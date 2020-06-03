"""
環境定義
"""
import math
import random

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import pandas as pd

from Agent import Agent, Status
from Environment.Hospital import Hospital


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

        # 区画分割数
        self.section_div_num = 10
        # 区画定義
        self.sections = []
        self.init_sections()

        # エージェント
        self.agents = []

    def init_sections(self):
        """ 環境を初期化 (区画分割と属性付与) """
        section_size = self.env_size / self.section_div_num
        sections = []
        for x in range(self.section_div_num):
            for y in range(self.section_div_num):
                x_min = x * section_size
                x_max = x_min + section_size
                y_min = y * section_size
                y_max = y_min + section_size

                attribute = random.choices(
                    ["public", "private"], weights=[1, 3]
                )[0]

                cell = {
                    "address": (x, y),
                    "x_min": x_min,
                    "x_max": x_max,
                    "y_min": y_min,
                    "y_max": y_max,
                    "attribute": attribute,
                }
                sections.append(cell)
        self.sections = sections

    def get_sections(self):
        """ 区画情報を取得 """
        return self.sections

    def set_sections(self, sections):
        """ 区画情報を設定 """
        self.sections = sections

    def output_section_map(self, path):
        """ 区画マップを画像出力 """
        plt.clf()
        plt.title("Environment Section Map")
        plt.figure()
        ax = plt.axes()

        margin = math.ceil(self.env_size * 0.05)
        plt.xlim(-margin, self.env_size + margin)
        plt.ylim(-margin, self.env_size + margin)

        for section in self.sections:
            fill_color = "#FFFCCC"
            if section["attribute"] == "private":
                fill_color = "#CCFFFC"

            rect = patches.Rectangle(
                xy=(section["x_min"], section["y_min"]),
                width=section["x_max"] - section["x_min"],
                height=section["y_max"] - section["y_min"],
                ec="white",
                fc=fill_color,
            )
            ax.add_patch(rect)

        plt.axis("scaled")
        ax.set_aspect("equal")
        plt.savefig(path)

    def init_agents(self, infected_agents_num):
        """ 環境内に存在するエージェントを初期化 """
        for id in range(self.agent_num):
            # private 区画から１つをランダム抽出して home に設定
            home = random.choice(
                [sec for sec in self.sections if sec["attribute"] == "private"]
            )

            # home の座標空間内でランダムな位置を設定
            x = random.uniform(home["x_min"], home["x_max"])
            y = random.uniform(home["y_min"], home["y_max"])

            # 初期ステータスを設定
            status = Status.SUSCEPTABLE

            agent = Agent(id, x, y, home, status, self.infection_model)
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
        """ 対象エージェントと同じ区画に属するエージェントのリストを取得 """
        neighbors = [
            a
            for a in self.agents
            if a.current_section["address"] == agent.current_section["address"]
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
