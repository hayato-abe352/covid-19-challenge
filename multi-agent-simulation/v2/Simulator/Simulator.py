"""
MASシミュレーター
"""


class Simulator:
    def __init__(self):
        pass

    def run(self):
        """ シミュレーションを実行 """
        pass

    def one_epoch(self):
        """ 1回のエポックを実行 """
        pass

    def output_world_graph(self):
        """ World のネットワーク図を出力 """
        pass

    def output_seir_charts(self):
        """ SEIRチャートを出力 """
        pass

    def output_aggregated_seir_chart(
        self, title: str = None, method: str = "mean"
    ):
        """ 集計SEIRチャートを出力 """
        pass

    def output_animation(self):
        """ アニメーションを出力 """
        pass
