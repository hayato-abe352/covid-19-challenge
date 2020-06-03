"""
環境定義
"""
import random

import pandas as pd
from scipy.spatial.distance import cdist

from Environment.Hospital import Hospital
from Agent import Agent, Status


class Environment:
    def __init__(
        self,
        env_size,
        agent_num,
        infection_model,
        hospital_capacity,
        observation_period,
    ):
        # 環境サイズ（env_size x env_size の空間を想定）
        self.env_size = env_size
        # エージェント数（総人口）
        self.agent_num = agent_num
        # 感染症モデル
        self.infection_model = infection_model

        # Hospitalオブジェクト
        self.hospital = Hospital(hospital_capacity)
        # 病院収容までの観察期間(観察期間分の日数が経過した感染者は病院に収容)
        self.observation_period = observation_period

        # エージェント
        self.agents = []

    def init_agents(self, infected_agents_num):
        """ 環境内に存在するエージェントを初期化 """
        for id in range(self.agent_num):
            x = random.random() * self.env_size
            y = random.random() * self.env_size
            status = Status.SUSCEPTABLE
            agent = Agent(id, x, y, status, self.infection_model)
            self.agents.append(agent)

        # 生成したエージェントの中から、指定人数に感染症を付与
        # (初期感染者は必ず自覚症状を持つ)
        infected_ids = random.sample(
            range(self.agent_num), k=infected_agents_num
        )
        for target_id in infected_ids:
            self.agents[target_id].status = Status.INFECTED
            self.agents[target_id].has_subjective_symptoms = True

    def get_neighbor_agents(self, agent):
        """ 対象エージェントの周囲に存在するエージェントのリストを取得 """
        base = [(agent.x, agent.y)]
        targets = [(a.x, a.y) for a in self.agents]
        dist = cdist(base, targets)[0].tolist()
        neighbors = [
            t
            for i, t in enumerate(self.agents)
            if dist[i] <= self.infection_model.influence_range
        ]
        return neighbors

    def accommodate_to_hospital(self):
        """ 観察期間終了後の感染者(自覚症状あり)を病院に収容 """
        for agent in self.agents:
            if (
                agent.status == Status.INFECTED
                and agent.has_subjective_symptoms
                and agent.infection_duration >= self.observation_period
                and self.hospital.is_accommodatable()
                and not agent.is_in_hospital
            ):
                self.hospital.accommodate(agent)

    def leave_from_hospital(self):
        """ 回復患者を病院から解放(退院) """
        self.hospital.leave_patients()

    def count_susceptable(self):
        """ 未感染者数をカウント """
        susceptables = [
            agent
            for agent in self.agents
            if agent.status == Status.SUSCEPTABLE
        ]
        return len(susceptables)

    def count_infected(self):
        """ 感染者数をカウント """
        infecteds = [
            agent for agent in self.agents if agent.status == Status.INFECTED
        ]
        return len(infecteds)

    def count_recovered(self):
        """ 回復者数をカウント """
        recovereds = [
            agent for agent in self.agents if agent.status == Status.RECOVERED
        ]
        return len(recovereds)

    def count_hospital_parients(self):
        """ 病院の患者数をカウント """
        return self.hospital.count_patients()

    def get_snap_shot_df(self):
        """ 現時点のスナップショット(Pandas.DataFrame)を取得 """
        df = pd.DataFrame(columns=["id", "x", "y", "status", "is_patient"])
        for agent in self.agents:
            record = pd.Series(index=df.columns, dtype="object")
            record["id"] = agent.id
            record["x"] = agent.x
            record["y"] = agent.y
            record["status"] = agent.status
            record["is_patient"] = agent.is_in_hospital
            df = df.append(record, ignore_index=True)
        return df
