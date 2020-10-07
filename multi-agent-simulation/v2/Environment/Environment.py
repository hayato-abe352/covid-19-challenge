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
        self.init_environment()

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

    def decide_agents_next_status(self):
        """ エージェントの次ステータスを決定 """
        for node in self.graph.nodes(data=True):
            idx, data = node
            neighbors = [
                self.graph.nodes[n]["agent"] for n in self.graph.neighbors(idx)
            ]
            data["agent"].decide_next_status(neighbors)

    def update_agents_status(self):
        """ エージェントの状態を更新 """
        for node in self.graph.nodes(data=True):
            _, data = node
            data["agent"].update_status()

    def count_agent(self, status: Status) -> int:
        """ 該当ステータスのエージェント数をカウント """
        targets = [
            node
            for node in self.graph.nodes(data=True)
            if node[1]["agent"].status == status
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
