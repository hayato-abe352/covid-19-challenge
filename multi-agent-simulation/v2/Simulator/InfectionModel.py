"""
感染症モデル
"""


class InfectionModel:
    def __init__(
        self, name, infection_prob, recovery_prob, incubation_period, impact
    ):
        # 感染症名
        self.name = name
        # 感染確率
        self.infection_prob = infection_prob
        # 回復確率
        self.recovery_prob = recovery_prob
        # 潜伏期間
        self.incubation_period = incubation_period
        # ダメージ
        self.impact = impact
