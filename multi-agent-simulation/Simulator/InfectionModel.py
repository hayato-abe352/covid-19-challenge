"""
感染症モデル
"""


class Infection:
    def __init__(self, infection_prob, recovery_prob, influence_range):
        # 感染確率( S => I の確率)
        self.infection_prob = infection_prob
        # 回復確率( I => R の確率)
        self.recovery_prob = recovery_prob
        # 感染範囲(濃厚接触範囲)
        self.influence_range = influence_range
