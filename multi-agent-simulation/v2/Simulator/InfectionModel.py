"""
感染症モデル
"""


class InfectionModel:
    def __init__(
        self,
        name,
        thresh,
        infection_prob,
        recovery_prob,
        recovery_prob_in_hospital,
        incubation_period,
        impact,
    ):
        # 感染症名
        self.name = name
        # 感染症と認知される閾値
        self.thresh = thresh
        # 感染確率
        self.infection_prob = infection_prob
        # 回復確率（入院していない場合）
        self.recovery_prob = recovery_prob
        # 回復確率（入院している場合）
        self.recovery_prob_in_hospital = recovery_prob_in_hospital
        # 潜伏期間
        self.incubation_period = incubation_period
        # ダメージ
        self.impact = impact
