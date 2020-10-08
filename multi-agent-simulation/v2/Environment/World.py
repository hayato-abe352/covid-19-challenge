"""
Worldクラス定義
    複数の Environment 間のエージェント移動を実現するためのクラス
"""
import random
import networkx as nx
from typing import List, Tuple

from loguru import logger

from Environment.Environment import Environment


class World:
    def __init__(self, infection_model, setting):
        self.infection_model = infection_model
        self.flow_rate = setting["flow_rate"]
        self.travel_days = setting["travel_days"]
        self.env_settings = setting["environments"]

        # Worldグラフ（各地域をつなぐ完全グラフ）
        self.node_num = len(self.env_settings)
        self.world_graph = nx.complete_graph(self.node_num)
        self.init_world()

        # 全エージェント
        self.all_agents = 0

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
        # 流出処理（滞在期間がゼロになったエージェントを帰還させる）
        for env in self.get_environments():
            env.outflow()

        # 全エージェントからランダムに移動者を決定
        traveler_num = int(len(self.all_agents) * self.flow_rate)
        travelers = random.sample(
            [agent for agent in self.all_agents if not agent.is_traveler],
            traveler_num,
        )

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

    def get_environments(self) -> List[Environment]:
        """ Environment のリストを取得 """
        return [node[1]["env"] for node in self.world_graph.nodes(data=True)]

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
