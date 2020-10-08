"""
環境定義
"""
import random
import pandas as pd
import networkx as nx
from typing import List

from loguru import logger

from Agent.Status import Status
from Agent.Agent import Agent


class Environment:
    def __init__(
        self,
        infection_model,
        id,
        name,
        population,
        city_type,
        attach,
        init_infection,
    ):
        self.id = id
        self.name = name
        self.type = city_type

        # エージェント数（人口）
        self.agent_num = population

        # 感染症モデル
        self.infection_model = infection_model
        # 初期感染者数
        self.init_infection = init_infection

        # 環境グラフ（各エージェントをつなぐバラバシ・アルバートグラフ）
        self.graph = nx.barabasi_albert_graph(n=self.agent_num, m=attach)

        # ノードのコードリスト
        self.code_list = []

        self.init_environment()
        self.update_code_list()

    def init_environment(self):
        """ 環境を初期化 """
        # 各ノードのエージェントを初期化
        for node in self.graph.nodes(data=True):
            idx, data = node
            data["agent"] = Agent(
                id=idx,
                hometown=self.name,
                status=Status.SUSCEPTABLE,
                infection_model=self.infection_model,
            )

        # 初期感染者を確定
        init_infected = random.sample(
            self.graph.nodes(data=True), self.init_infection
        )
        for node in init_infected:
            _, data = node
            data["agent"].status = Status.INFECTED

        logger.info(
            'Enviromnent "{}" を初期化しました。人口:{}, 初期感染者:{}'.format(
                self.name.upper(), self.agent_num, self.init_infection
            )
        )

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

    def outflow(self):
        """ 外部環境から来訪しているエージェントの流出処理 """
        # 滞在日数がゼロになった流入者を元の環境に戻す
        outflow_agents = [
            node
            for node in self.graph.nodes(data=True)
            if node[1]["agent"].is_stay_in(self.name)
            and node[1]["agent"].is_traveler
            and node[1]["agent"].stay_period == 0
        ]
        for idx, data in outflow_agents:
            data["agent"].go_back_hometown()

    def decide_agents_next_status(self):
        """ エージェントの次ステータスを決定 """
        for node in self.graph.nodes(data=True):
            idx, data = node
            if data["agent"].is_stay_in(self.name):
                neighbors = []
                for n in self.graph.neighbors(idx):
                    agent = self.graph.nodes[n]["agent"]
                    if agent.is_stay_in(self.name):
                        neighbors.append(agent)
                data["agent"].decide_next_status(neighbors)

    def update_agents_status(self):
        """ エージェントの状態を更新 """
        for node in self.graph.nodes(data=True):
            _, data = node
            if data["agent"].is_stay_in(self.name):
                data["agent"].update_status()

    def count_agent(self, status: Status) -> int:
        """ 該当ステータスのエージェント数をカウント """
        targets = [
            node
            for node in self.graph.nodes(data=True)
            if node[1]["agent"].status == status
            and node[1]["agent"].is_stay_in(self.name)
        ]
        return len(targets)

    def get_graph(self) -> nx.Graph:
        """ Environment グラフを取得 """
        return self.graph

    def get_agents(self) -> List[Agent]:
        """ Agent のリストを取得 """
        return [node[1]["agent"] for node in self.graph.nodes(data=True)]

    def get_snap_shot(self) -> pd.DataFrame:
        """ 現時点のスナップショットを取得 """
        pass
