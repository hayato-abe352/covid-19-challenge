"""
エージェント定義
"""
from __future__ import annotations

import random
from typing import List

from Agent.Status import Status
from Simulator.InfectionModel import InfectionModel


class Agent:
    def __init__(
        self,
        id: int,
        hometown: str,
        status: Status,
        infection_model: InfectionModel,
    ):
        # 個体識別コード（Worldでユニーク）
        self.code = "{}_{}".format(hometown, id)

        # 個体識別番号（Environmentでユニーク）
        self.id = id

        # 故郷と現在地
        self.hometown = hometown
        self.current_location = None

        # ステータス
        self.status: Status = status
        self.next_status: Status = None

        # 感染症モデル
        self.infection_model = infection_model

        # 潜伏日数（発症までの残り日数）
        self.incubation_count = 0

    def decide_next_status(self, neighbors: List[Agent]):
        """ エージェントの次ステータスを決定 """
        # エージェントの状態変化ルール
        #  [現在の状態]  [状態変化ルール]
        #  SUSCEPTABLE  neighbors に含まれる EXPOSED / INFECTED の人数に応じて EXPOSED に推移
        #  EXPOSED      一定時間経過後 INFECTED に推移
        #  INFECTED     一定確率で RECOVERED に推移
        #  RECOVERED    RECOVERED のまま変化なし

        self.next_status = self.status

        # SUSCEPTABLE
        if self.status == Status.SUSCEPTABLE:
            infecteds = [
                agent
                for agent in neighbors
                if agent.status in [Status.EXPOSED, Status.INFECTED]
            ]
            prob = 1 - (
                (1 - self.infection_model.infection_prob) ** len(infecteds)
            )
            if random.random() <= prob:
                self.next_status = Status.EXPOSED
                self.incubation_count = self.infection_model.incubation_period

        # EXPOSED
        if self.status == Status.EXPOSED:
            count = self.incubation_count - 1
            if count == 0:
                self.next_status = Status.INFECTED
            self.incubation_count = count

        # INFECTED
        if self.status == Status.INFECTED:
            if random.random() <= self.infection_model.recovery_prob:
                self.next_status = Status.RECOVERED

    def update_status(self):
        """ エージェントのステータスを更新 """
        self.status = self.next_status
        self.next_status = None
