"""
Worldクラス定義
    複数の Environment 間のエージェント移動を実現するためのクラス
"""
import random
import networkx as nx
from typing import List, Tuple

from loguru import logger

from Agent.Agent import Agent
from Agent.Status import Status
from Environment.Environment import Environment


class World:
    def __init__(self, infection_model, setting):
        self.infection_model = infection_model
        self.flow_rate = setting["flow_rate"]
        self.travel_days = setting["travel_days"]
        self.env_settings = setting["environments"]
        self.immigration_settings = setting["immigration"]

        # Worldグラフ（各地域をつなぐ完全グラフ）
        self.node_num = len(self.env_settings)
        self.world_graph = nx.complete_graph(self.node_num)
        self.init_world()

        # 全エージェント
        self.all_agents = 0

        # １日あたりの流出者リスト [(流出元の環境名, Agent), ...]
        #   - hometownからの流出者と、hometownへの帰還者の合計値
        #   - move_agent() を実行する度更新される
        self.travelers: List[Tuple[str, Agent]] = []

    def init_world(self):
        """ World の初期化 """
        # 各ノードの Environment を初期化
        self.all_agents = []
        for node in self.world_graph.nodes(data=True):
            idx, data = node
            env_setting = self.env_settings[idx]
            data["env"] = Environment(
                infection_model=self.infection_model, **env_setting
            )
            agents = data["env"].get_agents()
            self.all_agents.extend(agents)
        logger.info(
            "Worldクラスを初期化しました。ノード数:{}, 総人口:{}".format(
                self.node_num, len(self.all_agents)
            )
        )

    def reset_environments(self):
        """ Environment をリセット（各 Episode の最初に実行する想定） """
        self.all_agents = []
        for node in self.world_graph.nodes(data=True):
            _, data = node
            data["env"].init_environment()
            agents = data["env"].get_agents()
            self.all_agents.extend(agents)

    def forward_time(self):
        """ 時間を進める（滞在期間カウントのデクリメント処理） """
        for agent in self.all_agents:
            agent.stay_period = max(0, agent.stay_period - 1)

    def move_agent(self):
        """ エージェントの Environment 間移動 """
        self.travelers = []

        # 流出処理（滞在期間がゼロになったエージェントを帰還させる）
        for env in self.get_environments():
            # 滞在日数がゼロになった旅行者を抽出
            outflow_agents = [
                data["agent"]
                for _, data in env.graph.nodes(data=True)
                if data["agent"].is_stay_in(env.name)
                and data["agent"].is_traveler
                and data["agent"].stay_period == 0
            ]
            # 帰還可能かを判断（出国審査）
            outflow_agents = self.immigration(
                [(env.name, agent) for agent in outflow_agents]
            )
            # 流出処理（故郷への帰還処理）
            env.outflow(outflow_agents)
            self.travelers.extend(
                [(env.name, agent) for agent in outflow_agents]
            )

        # 全エージェントからランダムに移動者を決定
        travelers = [
            agent
            for agent in self.all_agents
            if not agent.is_traveler and random.random() <= self.flow_rate
        ]

        # 流出可能なエージェントのみを抽出（出国審査処理）
        travelers = self.immigration(
            [(agent.hometown, agent) for agent in travelers]
        )
        self.travelers.extend([(agent.hometown, agent) for agent in travelers])

        # 一度移動者の所在地をクリア
        for traveler in travelers:
            traveler.current_location = None

        # 移動を実行
        environments = self.get_environments()
        for traveler in travelers:
            # 行先を決定
            destination = random.choice(
                [env for env in environments if env.name != traveler.hometown]
            )

            # 滞在日数を決定
            stay_min = min(self.travel_days)
            stay_max = max(self.travel_days)
            stay_period = random.randint(stay_min, stay_max)

            # 環境移動を実行
            destination.inflow(traveler, stay_period)

        # 各環境のコードリストを更新
        for env in environments:
            env.update_code_list()

    def immigration(self, travelers: List[Tuple[str, Agent]]):
        """ 出国時のPCR検査を実施 """
        travelable_agents = []
        for env_name, agent in travelers:
            env = self.get_environment(env_name)
            e = env.count_agent(Status.EXPOSED)
            i = env.count_agent(Status.INFECTED)
            total = env.count_agent()

            # 検査カバー率に応じて、一定割合をスルーさせる
            if random.random() <= (1 - self.immigration_settings["cover"]):
                travelable_agents.append(agent)
                continue

            full_pcr_setting = self.immigration_settings["pcr_full_check"]
            infected_pcr_setting = self.immigration_settings[
                "pcr_infected_check"
            ]

            ei_rate = (e + i) / total
            i_rate = i / total

            if (
                full_pcr_setting["perform"]
                and ei_rate >= full_pcr_setting["active_rate"]
            ):
                # フルPCR実施条件を満たしている場合
                if self._take_pcr_test(agent, level="full"):
                    travelable_agents.append(agent)
            elif (
                infected_pcr_setting["perform"]
                and i_rate >= infected_pcr_setting["active_rate"]
            ):
                # 発症者限定PCR実施条件を満たしている場合
                if self._take_pcr_test(agent, level="infected"):
                    travelable_agents.append(agent)
            else:
                # いずれのPCR検査も実施していない場合
                travelable_agents.append(agent)

        return travelable_agents

    def _take_pcr_test(self, agent: Agent, level: str) -> bool:
        """ PCR検査を実施 """
        if random.random() <= (1 - self.immigration_settings["pcr_recall"]):
            # 偽陰性の場合
            return True

        if level == "full":
            return agent.status not in [Status.EXPOSED, Status.INFECTED]
        if level == "infected":
            return agent.status != Status.INFECTED

    def get_environments(self) -> List[Environment]:
        """ Environment のリストを取得 """
        return [node[1]["env"] for node in self.world_graph.nodes(data=True)]

    def get_environment(self, name: str) -> Environment:
        """ Environment を取得 """
        environments = self.get_environments()
        return [env for env in environments if env.name == name][0]

    def get_travelers(self, env_name: str) -> List[Agent]:
        """ env_name から流出するエージェントのリストを取得 """
        return [agent for env, agent in self.travelers if env == env_name]

    def get_world_graph(self) -> nx.Graph:
        """ World グラフを取得 """
        return self.world_graph

    def get_environment_graphs(self) -> List[Tuple[str, nx.Graph]]:
        """ Environment のグラフリスト [(name, graph), ... ] を取得 """
        graphs = []
        for node in self.world_graph.nodes(data=True):
            _, data = node
            record = (data["env"].name, data["env"].get_graph())
            graphs.append(record)
        return graphs
