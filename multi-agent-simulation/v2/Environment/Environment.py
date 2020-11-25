"""
環境定義
"""
import random
import math
from typing import List

import networkx as nx
import pandas as pd
from loguru import logger

from Agent.Agent import Agent
from Agent.Status import Status

POPULATION_PYRAMID_DATA = "settings/population-pyramid.csv"


class Environment:
    def __init__(
        self,
        infection_model,
        agent_setting,
        global_hospital_setting,
        id,
        name,
        population,
        city_type,
        attach,
        init_infection,
        hospital,
        hospital_bed_num,
        economy,
    ):
        self.id = id
        self.name = name
        self.type = city_type

        # エージェント数（人口）
        self.agent_num = population
        # 人口ピラミッド
        self.population_pyramid = pd.read_csv(POPULATION_PYRAMID_DATA)
        # エージェントの設定
        self.agent_setting = agent_setting

        # 感染症モデル
        self.infection_model = infection_model
        # 初期感染者数
        self.init_infection = init_infection

        # 環境グラフ（各エージェントをつなぐバラバシ・アルバートグラフ）
        self.attach = attach
        self.graph = nx.barabasi_albert_graph(n=self.agent_num, m=attach)

        # ノードのコードリスト
        self.code_list = []

        # 経済関連の設定情報
        self.economy_setting = economy
        # 経済力
        self.finance = economy["init_gdp"]
        # 税率
        self.tax_rate = economy["tax_rate"]
        # 一日の税収
        self.tmp_tax_revenue = 0

        # エージェント設定にこの環境における平均所得と所得幅を追加
        self.agent_setting["params"]["economical"]["income_avg"] = economy[
            "agent_avg_income"
        ]
        self.agent_setting["params"]["economical"]["income_range"] = economy[
            "agent_income_range"
        ]

        # 病院に隔離中のエージェント情報
        self.hospital = []
        # 病院機能を稼働させるかどうか
        self.can_hospitalized = hospital and global_hospital_setting
        # 病院の病床数
        self.hospital_bed_num = hospital_bed_num
        # 病院の稼働コスト (入院患者一人あたりでコストが発生)
        self.hospital_operating_cost = economy["hospital_operating_cost"]

        self.init_environment()
        self.update_code_list()

    def init_environment(self):
        """ 環境を初期化 """
        self.graph = nx.barabasi_albert_graph(n=self.agent_num, m=self.attach)
        for node in self.graph.nodes(data=True):
            idx, data = node
            age = self.get_agent_age()
            data["agent"] = Agent(
                agent_setting=self.agent_setting,
                id=idx,
                age=age,
                hometown=self.name,
                status=Status.SUSCEPTABLE,
                infection_model=self.infection_model,
            )

        # 公務員を確定
        cs_num = math.ceil(
            self.agent_num * self.economy_setting["civil_servants_rate"]
        )
        civil_servants = random.sample(self.graph.nodes(data=True), cs_num)
        for _, data in civil_servants:
            data["agent"].is_civil_servant = True

        # 初期感染者を確定
        init_infected = random.sample(
            self.graph.nodes(data=True), self.init_infection
        )
        for _, data in init_infected:
            data["agent"].status = Status.INFECTED

        # 経済パラメータを初期化
        self.finance = self.economy_setting["init_gdp"]
        self.tax_rate = self.economy_setting["tax_rate"]
        self.tmp_tax_revenue = 0

        # 病院を初期化
        self.hospital = []

        logger.info(
            'Enviromnent "{}" を初期化しました。人口:{}, 初期感染者:{}'.format(
                self.name.upper(), self.agent_num, self.init_infection
            )
        )

    def get_agent_age(self) -> int:
        """ エージェントの年齢を決定 """
        # 人口ピラミッドに従う確率で年齢を確定
        age_list = list(self.population_pyramid["age"])
        weight_list = list(self.population_pyramid["weight"])
        return random.choices(age_list, weight_list, k=1)[0]

    def update_code_list(self):
        """ コードリストを更新 """
        self.code_list = [
            node[1]["agent"].code for node in self.graph.nodes(data=True)
        ]

    def inflow(self, inflow_agent: Agent, stay_period: int):
        """ 外部環境からのエージェント流入処理 """
        # 流入者の情報を書き換え
        inflow_agent.current_location = self.name
        inflow_agent.stay_period = stay_period

        # 過去に流入したことがある場合はノードの新規作成をスキップ
        if inflow_agent.code in self.code_list:
            return

        # 過去に流入したことがない場合は新規ノードを追加
        self._add_new_node(inflow_agent)

    def _add_new_node(self, new_agent):
        """ グラフのランダムな位置に対して新規ノードを追加 """
        # ランダムなノードを選択
        connect_target = random.choice(
            [
                node[0]
                for node in self.graph.nodes(data=True)
                if node[1]["agent"].current_location == self.name
            ]
        )
        # 抽出ノードに接続されているノードを取得
        connect_neighbors = [
            node for node in self.graph.neighbors(connect_target)
        ]

        # 流入者の受け入れ
        new_idx = len(self.graph.nodes()) + 1
        self.graph.add_node(new_idx, agent=new_agent)
        for relevant_idx in [connect_target] + connect_neighbors:
            self.graph.add_edge(new_idx, relevant_idx)

    def outflow(self, outflow_agents: List[Agent]):
        """ 外部環境から来訪しているエージェントの流出処理 """
        # 滞在日数がゼロになった流入者を元の環境に戻す
        for agent in outflow_agents:
            agent.go_back_hometown()

    def update_agents_params(self):
        """ エージェントのパラメータ（体力・精神力）を更新 """
        for node in self.graph.nodes(data=True):
            _, data = node
            if data["agent"].is_stay_in(self.name):
                # 精神力を更新
                data["agent"].update_mental_strength()
                # 体力を更新
                data["agent"].update_physical_strength()

    def decide_agents_next_status(self):
        """ エージェントの次ステータスを決定 """
        for idx, data in self.graph.nodes(data=True):
            if data["agent"].is_stay_in(self.name):
                neighbors = []
                for n in self.graph.neighbors(idx):
                    agent = self.graph.nodes[n]["agent"]
                    if agent.is_stay_in(
                        self.name
                    ) and not agent.is_hospitalized(self.hospital):
                        neighbors.append(agent)
                data["agent"].decide_next_status(neighbors)

    def trade(self):
        """ エージェント間の経済的取引を実行 """
        for idx, data in self.graph.nodes(data=True):
            agent = data["agent"]
            if agent.is_stay_in(self.name) and agent.is_tradable:
                for n in self.graph.neighbors(idx):
                    partner = self.graph.nodes[n]["agent"]

                    # 取引相手が他環境に外出中 または 入院中 の場合は取引しない
                    if not partner.is_stay_in(
                        self.name
                    ) or partner.is_hospitalized(self.hospital):
                        continue

                    # Step-1. 取引アクションの決定
                    a_action = agent.decide_trade_action()
                    p_action = partner.decide_trade_action()

                    # Step-2. 取引成立判定
                    if a_action == p_action:
                        # [buy]-[buy], [sell]-[sell] は取引不成立
                        continue

                    # Step-3. sell 側が取引金額を決定
                    price = agent.get_trade_price()
                    if p_action == "sell":
                        price = partner.get_trade_price()

                    # Step-4. 取引実行 および 税収処理
                    tax = math.ceil(price * self.tax_rate)
                    if a_action == "sell":
                        # agent: 売り手、partner: 買い手
                        agent.trade(price, a_action)
                        partner.trade(price + tax, p_action)
                    else:
                        # agent: 買い手、partner: 売り手
                        agent.trade(price + tax, a_action)
                        partner.trade(price, p_action)
                    self.pay_tax(tax)

                    # Step-5. 取引実績の更新
                    agent.update_income()
                    partner.update_income()

    def update_agents_status(self):
        """ エージェントの状態を更新 """
        for _, data in self.graph.nodes(data=True):
            agent = data["agent"]
            if agent.is_stay_in(self.name):
                agent.update_status()

                # 発症者を病院に隔離する処理
                if agent.status == Status.INFECTED:
                    self.admit_to_hospital(agent.code)

                # 回復者を病院から退院させる処理
                if agent.status == Status.RECOVERED:
                    self.discharge_to_hospital(agent.code)

    def admit_to_hospital(self, agent_code):
        """ エージェントを病院に入院させる """
        patient_num = len(self.hospital)
        if not self.can_hospitalized or patient_num > self.hospital_bed_num:
            # 入院機能が off のとき または 病床が埋まっているとき
            return

        # 感染症と認知される閾値
        th = self.infection_model.thresh * self.agent_num
        # 発症者数が閾値以上の場合、病院による隔離を開始
        infected_agents = self.count_agent(Status.INFECTED)
        if infected_agents > th and agent_code not in self.hospital:
            self.hospital.append(agent_code)

    def discharge_to_hospital(self, agent_code):
        """ エージェントを病院から退院させる """
        if agent_code in self.hospital:
            self.hospital.remove(agent_code)

    def consume_hospital_operating_cost(self):
        """ 病院を稼働させる (入院患者数の運営費を消費させる) """
        patient_num = len(self.hospital)
        operating_cost = patient_num * self.hospital_operating_cost
        self.finance = self.finance - operating_cost

    def pay_tax(self, tax):
        """ 税金を納める """
        self.tmp_tax_revenue += tax

    def update_finance(self):
        """ 経済力パラメータの更新（税収を加算） """
        self.finance += self.tmp_tax_revenue
        self.tmp_tax_revenue = 0

    def pay_salary_to_public_officials(self):
        """ 公務員エージェントに給料を払う """
        civil_servants = [
            data["agent"]
            for _, data in self.graph.nodes(data=True)
            if data["agent"].is_civil_servant
            and data["agent"].belong_to(self.name)
        ]
        salary = self.economy_setting["civil_servants_salary"]
        for agent in civil_servants:
            agent.receive_salary(salary)
            self.finance -= salary

    def count_agent(self, status: Status = None) -> int:
        """ 該当ステータスのエージェント数をカウント """
        stay_agent = [
            data["agent"]
            for _, data in self.graph.nodes(data=True)
            if data["agent"].is_stay_in(self.name)
        ]
        if status is None:
            return len(stay_agent)

        targets = [agent for agent in stay_agent if agent.status == status]
        return len(targets)

    def count_patients(self) -> int:
        """ 患者数を取得 """
        return len(self.hospital)

    def get_average_mental_strength(self) -> float:
        """ 平均メンタル値を取得 """
        values = [
            data["agent"].mental_strength
            for _, data in self.graph.nodes(data=True)
            if data["agent"].is_stay_in(self.name)
        ]
        return sum(values) / len(values)

    def get_finance(self) -> float:
        """ 経済力を取得 """
        return self.finance

    def get_tax_revenue(self) -> float:
        """ 税収を取得 """
        return self.tmp_tax_revenue

    def get_average_income(self) -> float:
        """ 平均所得を取得 """
        values = [
            data["agent"].income
            for _, data in self.graph.nodes(data=True)
            if data["agent"].is_stay_in(self.name)
        ]
        return sum(values) / len(values)

    def get_graph(self) -> nx.Graph:
        """ Environment グラフを取得 """
        return self.graph

    def get_agents(self) -> List[Agent]:
        """ Agent のリストを取得 """
        return [node[1]["agent"] for node in self.graph.nodes(data=True)]

    def get_snap_shot(self) -> pd.DataFrame:
        """ 現時点のスナップショットを取得 """
        pass
