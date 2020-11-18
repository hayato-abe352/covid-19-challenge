"""
エージェント定義
"""
from __future__ import annotations

import random
from typing import List

import numpy as np

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
        physical_settings = agent_setting["params"]["physical"]
        self.physical_strength = physical_settings["default_strength"]
        # 免疫力
        self.immunity = self._get_immunity_value()

        # メンタル
        mental_settings = agent_setting["params"]["mental"]
        msp = self._get_mental_stabilize_point(
            mental_settings["default_stabilize_point_distribution"]
        )
        self.mental_stabilize_point = msp
        self.mental_strength = msp
        self.stabilize_scale = mental_settings["stabilize_scale"]
        self.emotional_instability_setting = mental_settings[
            "emotional_instability"
        ]

        # 経済力
        economy_setting = agent_setting["params"]["economical"]
        isp = self._get_income_stabilize_point(
            economy_setting["income_avg"], economy_setting["income_range"]
        )
        self.income_stabilize_point = isp
        self.income = isp
        self.trade_price = 0

        # 公務員かどうか（公務員の場合 env から収入を得られる）
        self.is_civil_servant = False

    @property
    def is_living(self):
        """ 生存しているかどうか """
        return self.status != Status.DEATH

    @property
    def is_traveler(self):
        """ 外部環境に旅行中かどうか """
        return self.hometown != self.current_location

    @property
    def is_tradable(self):
        """ 取引可能かどうか """
        return self.status not in [Status.INFECTED, Status.DEATH]

    def is_stay_in(self, env_name) -> bool:
        """ このエージェントの所在が env_name の環境かどうか """
        return env_name == self.current_location

    def belong_to(self, env_name) -> bool:
        """　このエージェントが env_name に所属しているかどうか　(公務員の所属確認) """
        return env_name == self.hometown

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

    def trade(self, price, action):
        """ 取引額の変化を記録 """
        if action == "buy":
            # 買い手の場合 => 所得は減少
            self.trade_price = -price
        elif action == "sell":
            # 売り手の場合 => 所得は増加
            self.trade_price = +price

    def get_trade_price(self) -> int:
        """ 取引額を決定 """
        base_line = abs(self.income_stabilize_point - self.income)
        scale = base_line * 0.5
        price = np.random.normal(loc=base_line, scale=scale)
        price = min(price, self.income)

        min_price = self.agent_setting["params"]["economical"][
            "min_trade_price"
        ]
        max_price = self.agent_setting["params"]["economical"][
            "max_trade_price"
        ]
        price = min(price, max_price)
        price = max(price, min_price)
        return int(price)

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

    def decide_trade_action(self) -> str:
        """ 取引アクションを決定 """
        # 取引アクションの種類:
        #     sell (売り手): 自身の所得を増加させる取引
        #     buy  (買い手): 自身の所得を低下させる取引
        # 取引アクションの選択確率：
        #     isp > income : seller が発生しやすい
        #     isp < income : buyer が発生しやすい
        # 取引の成立条件:
        #     自身と相手のアクションが [s]-[b] または [b]-[s] の組み合わせの場合のみ成立
        #     [s]-[s] や [b]-[b] の場合は取引が成立しない

        # 所得が最低取引額以下の場合、sell のみ
        min_price = self.agent_setting["params"]["economical"][
            "min_trade_price"
        ]
        if self.income < min_price:
            return "sell"

        # isp と income の差から sell と buy の比重を算出
        max_val = self.income_stabilize_point * 2
        buy_w = min(self.income / max_val, 1)
        sell_w = 1 - buy_w

        # 取引アクションを確率で決定
        action = random.choices(["buy", "sell"], weights=[buy_w, sell_w])[0]
        return action

    def receive_salary(self, salary):
        """ 給料を受け取る """
        self.income += salary

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
        mf = self.infection_model.impact["mental_fluctuation"]
        damage = self._get_physical_damage_from_infection(
            vd_max, vd_min, mf, self.mental_strength, self.immunity
        )

        # 体力値を更新（ダメージ量分を減算）
        self.physical_strength = max(self.physical_strength - damage, 0)

    def update_mental_strength(self):
        """ 精神力を更新 """
        # メンタルの更新方向を決定（positive/negative)
        vec = np.random.normal(
            loc=self.mental_stabilize_point, scale=self.stabilize_scale
        )
        pn = 1 if vec > self.mental_stabilize_point else -1

        # メンタルの更新量を決定（カイ二乗分布で移動量を決定）
        df = self.emotional_instability_setting["degree_of_freedom"]
        cor = self.emotional_instability_setting["correction"]
        amount = cor * np.random.chisquare(df=df)

        # メンタル値の更新
        new_strength = self.mental_strength + (pn * amount)
        new_strength = min(max(new_strength, -1), 1)
        self.mental_strength = new_strength

    def update_income(self):
        """ 取引額に応じて所得を変化 """
        self.income = self.income + self.trade_price
        self.trade_price = 0

    def _get_mental_stabilize_point(self, setting):
        """ 精神力のスタビライズポイントを決定 """
        loc = setting["loc"]
        scale = setting["scale"]
        val = np.random.normal(loc=loc, scale=scale)
        return min(max(val, -1), 1)

    def _get_income_stabilize_point(self, avg, scale_rate):
        """ 所得のスタビライズポイントを決定 """
        loc = avg
        scale = avg * scale_rate
        val = np.random.normal(loc=loc, scale=scale)
        return val

    def _get_physical_damage_from_infection(
        self,
        vd_max: float,
        vd_min: float,
        mf: float,
        mental: float,
        immunity: float,
    ):
        """ 感染症による身体的ダメージを取得 """
        mental_effect = mf * mental
        return -(vd_max - vd_min + mental_effect) * immunity + vd_max
