"""
感染症モデル
"""


class Infection:
    def __init__(
        self,
        infection_prob,
        recovery_prob,
        antibody_acquisition_prob,
        influence_range,
    ):
        # 感染確率( S => I の確率)
        self.infection_prob = infection_prob
        # 回復確率( I => R の確率)
        self.recovery_prob = recovery_prob
        # 抗体獲得確率( I => R に遷移した際、さらに R => S に変化する確率)
        self.antibody_acquisition_prob = antibody_acquisition_prob
        # 感染範囲(濃厚接触範囲)
        self.influence_range = influence_range
