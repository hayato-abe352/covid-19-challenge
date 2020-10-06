"""
MASシミュレーター
"""
import json

from Simulator.InfectionModel import InfectionModel

INFECTION_MODEL_SETTING = "../settings/infection-model.json"


class Simulator:
    def __init__(self):
        # 感染症モデル
        infection_settings = self._read_settings(INFECTION_MODEL_SETTING)
        self.infection_model = InfectionModel(**infection_settings)
        pass

    def run(self):
        """ シミュレーションを実行 """
        pass

    def one_epoch(self):
        """ 1回のエポックを実行 """
        pass

    def _read_settings(self, path: str) -> dict:
        """ 設定情報の読み込み """
        with open(path, mode="r") as f:
            settings = json.load(f)
            return settings

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
