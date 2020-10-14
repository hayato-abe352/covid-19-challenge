"""
エージェント定義
"""
from __future__ import annotations

import random
from typing import List

from Simulator.InfectionModel import InfectionModel
from Agent.Status import Status


class Agent:
    def __init__(
        self,
        agent_setting: dict,
        id: int,
        age: int,
        hometown: str,
        status: Status,
        infection_model: InfectionModel,
    ):
        # エージェントの設定
        self.agent_setting = agent_setting

        # 個体識別コード（Worldでユニーク）
        self.code = "{}_{}".format(hometown, id)
        # 個体識別番号（Environmentでユニーク）
        self.id = id

        # 年齢
        self.age = age

        # 故郷と現在地
        self.hometown = hometown
        self.current_location = hometown

        # 滞在期間
        self.stay_period = 0

        # ステータス
        self.status: Status = status
        self.next_status: Status = None

        # 感染症モデル
        self.infection_model = infection_model

        # 潜伏日数（発症までの残り日数）
        self.incubation_count = 0

        # 体力
        self.physical_strength = agent_setting["params"]["physical"][
            "default_strength"
        ]
        # 免疫力
        self.immunity = self._get_immunity_value()

    @property
    def is_living(self):
        """ 生存しているかどうか """
        return self.status != Status.DEATH

    @property
    def is_traveler(self):
        """ 外部環境に旅行中かどうか """
        return self.hometown != self.current_location

    def is_stay_in(self, env_name):
        """ このエージェントの所在が env_name の環境かどうか """
        return env_name == self.current_location

    def go_back_hometown(self):
        """ エージェントの所在地を故郷に戻す """
        self.current_location = self.hometown
        self.stay_period = 0

    def _get_immunity_value(self) -> float:
        """ 免疫力の値を取得 """
        immunity_setting = [
            s
            for s in self.agent_setting["params"]["physical"][
                "default_immunity"
            ]
            if min(s["age_range"]) <= self.age <= max(s["age_range"])
        ][0]
        return immunity_setting["value"]

    def decide_next_status(self, neighbors: List[Agent]):
        """ エージェントの次ステータスを決定 """
        # エージェントの状態変化ルール
        #  [現在の状態]  [状態変化ルール]
        #  (ALL)        体力がゼロになった場合 DEATH に推移
        #  SUSCEPTABLE  neighbors に含まれる EXPOSED / INFECTED の人数に応じて EXPOSED に推移
        #  EXPOSED      一定時間経過後 INFECTED に推移
        #  INFECTED     一定確率で RECOVERED に推移
        #  RECOVERED    RECOVERED のまま変化なし
        #  DEATH        変化しない

        self.next_status = self.status

        # ALL
        if self.physical_strength == 0:
            self.next_status = Status.DEATH
            return

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

    def update_physical_strength(self):
        """ 体力値を更新 """
        # 発症状態のみ体力が減少する
        if self.status != Status.INFECTED:
            return

        # 1日に受ける身体的ダメージを計算
        vd_max = self.infection_model.impact["max_damage"]
        vd_min = self.infection_model.impact["min_damage"]
        damage = self._get_physical_damage_from_infection(
            vd_max, vd_min, self.immunity
        )

        # 体力値を更新（ダメージ量分を減算）
        self.physical_strength = max(self.physical_strength - damage, 0)

    def _get_physical_damage_from_infection(
        self, vd_max: float, vd_min: float, immunity: float
    ):
        """ 感染症による身体的ダメージを取得 """
        return -(vd_max - vd_min) * immunity + vd_max
