"""
Worldクラス定義
    複数の Environment 間のエージェント移動を実現するためのクラス
"""
import networkx as nx
import matplotlib.pyplot as plt
from typing import List, Tuple

from loguru import logger

from Agent.Agent import Agent
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
        self.all_agents = self.get_all_agents()

    def init_world(self):
        """ World の初期化 """
        # 各ノードの Environment を初期化
        for node in self.world_graph.nodes(data=True):
            idx, data = node
            env_setting = self.env_settings[idx]
            data["env"] = Environment(
                infection_model=self.infection_model, **env_setting
            )
        logger.info("Worldクラスを初期化しました。ノード数:{}".format(self.node_num))

    def get_all_agents(self) -> List[Agent]:
        """ 全エージェントのリストを取得 """
        all_agents = []
        for node in self.world_graph.nodes(data=True):
            _, data = node
            agents = data["env"].get_agents()
            all_agents.extend(agents)
        logger.info(
            "全エージェントを World 配下に格納しました。エージェント数:{}".format(len(all_agents))
        )
        return all_agents

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
