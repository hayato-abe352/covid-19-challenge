"""
エージェント定義
"""
import math
import random

from Agent.Status import Status


class Agent:
    def __init__(self, id, x, y, status, infection_model):
        # 個体識別番号
        self.id = id

        # エージェントの位置
        self.x = x
        self.y = y
        self.next_x = None
        self.next_y = None

        # エージェントの感染確率( S => I の確率)
        self.infection_prob = infection_model.infection_prob
        # エージェントの回復確率( I => R の確率)
        self.recovery_prob = infection_model.recovery_prob
        # エージェントの抗体獲得確率( I => R 後に R => S が起きる確率)
        self.antibody_acquisition_prob = (
            infection_model.antibody_acquisition_prob
        )
        # 自覚症状が生じる確率
        self.subjective_symptoms_prob = (
            infection_model.subjective_symptoms_prob
        )

        # エージェントの状態
        self.status = status
        self.next_status = None

        # 自覚症状の有無
        self.has_subjective_symptoms = False

        # 感染してからの経過日数
        self.infection_duration = 0

        # 自身の周囲に存在するエージェント
        self.neighbor_agents = []

    def decide_next_position(self, x_min, x_max, y_min, y_max, pattern):
        """ 次のエージェント位置を決定 """
        # TODO: 行動に関する意思決定機能を追加

        if pattern == "freeze":
            self.next_x = self.x
            self.next_y = self.y
            return

        if self.status == Status.INFECTED and self.has_subjective_symptoms:
            # 自覚症状ありの感染者の場合、その場に留まる
            self.next_x = self.x
            self.next_y = self.y
            return

        # 自身の周囲に存在する感染者(自覚症状がある者のみ)との距離の和を計算
        neighbor_infected = [
            n
            for n in self.neighbor_agents
            if n.status == Status.INFECTED and n.has_subjective_symptoms
        ]
        current_sum_dist = self._get_sum_distance_to_infected(
            self.x, self.y, neighbor_infected
        )

        # 移動距離
        distance = 0.5
        while True:
            direction = random.random() * 2.0 * math.pi
            next_x = self.x + distance * math.cos(direction)
            next_y = self.y + distance * math.sin(direction)
            next_sum_dist = self._get_sum_distance_to_infected(
                next_x, next_y, neighbor_infected
            )

            if current_sum_dist >= next_sum_dist:
                # 感染者に近づいてしまう場合は、その場に留まる
                next_x = self.x
                next_y = self.y

            if (x_min <= next_x <= x_max) and (y_min <= next_y <= y_max):
                break

        self.next_x = next_x
        self.next_y = next_y

    def _get_sum_distance_to_infected(self, x, y, neighbor_infected):
        """ 周囲に存在する感染者との距離の和を算出 """
        sum_distance = 0.0
        for neighbor in neighbor_infected:
            sum_distance += math.sqrt(
                ((x - neighbor.x) ** 2) + ((y - neighbor.y) ** 2)
            )
        return sum_distance

    def update_position(self):
        """ エージェントの位置を更新 """
        self.x = self.next_x
        self.y = self.next_y

    def decide_next_status(self):
        """ 次のエージェント状態を決定 """
        if self.status == Status.RECOVERED:
            # 回復者は再感染しない想定
            self.next_status = Status.RECOVERED

        elif self.status == Status.INFECTED:
            # 感染者は一定確率で回復する想定
            if random.random() <= self.recovery_prob:
                if random.random() <= self.antibody_acquisition_prob:
                    # 抗体獲得に成功した場合
                    self.next_status = Status.RECOVERED
                else:
                    # 抗体獲得に失敗した場合
                    self.next_status = Status.SUSCEPTABLE
            else:
                self.next_status = Status.INFECTED

        elif self.status == Status.SUSCEPTABLE:
            # 未感染者は周囲の感染者に比例する確率で感染状態に移行
            infected_agents = [
                agent
                for agent in self.neighbor_agents
                if agent.status == Status.INFECTED
            ]

            # len(infected_agents)人の感染者と接触したとき、一度でも感染する確率
            infection_prob = 1 - (
                (1 - self.infection_prob) ** len(infected_agents)
            )

            if random.random() <= infection_prob:
                self.next_status = Status.INFECTED
            else:
                self.next_status = Status.SUSCEPTABLE

    def update_status(self):
        """ エージェントの状態を更新 """
        # 感染時の自覚症状発生判定
        if (
            self.status == Status.SUSCEPTABLE
            and self.next_status == Status.INFECTED
        ):
            # 感染状態に移行するとき、一定確率で自覚症状を付与
            if random.random() <= self.subjective_symptoms_prob:
                self.has_subjective_symptoms = True
            else:
                self.has_subjective_symptoms = False
        elif self.status == Status.RECOVERED:
            self.has_subjective_symptoms = False

        # 感染中の経過日数インクリメント
        if (
            self.status == Status.INFECTED
            and self.next_status == Status.INFECTED
        ):
            self.infection_duration += 1

        # 状態変化を実行
        self.status = self.next_status
