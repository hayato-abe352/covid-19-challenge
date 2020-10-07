"""
Worldクラス定義
    複数の Environment 間のエージェント移動を実現するためのクラス
"""
import networkx as nx
from typing import List, Tuple

from loguru import logger

from Environment.Environment import Environment


class World:
    def __init__(self, infection_model, setting):
        self.infection_model = infection_model
        self.flow_rate = setting["flow_rate"]
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
        """ Environment をリセット """
        self.all_agents = []
        for node in self.world_graph.nodes(data=True):
            _, data = node
            data["env"].init_environment()
            agents = data["env"].get_agents()
            self.all_agents.extend(agents)

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
