"""
MASシミュレーター
"""
import sys

from loguru import logger

from Environment.World import World
from Simulator.InfectionModel import InfectionModel

logger.remove()
logger.add(sys.stdout, colorize=True, backtrace=False, diagnose=False)


class Simulator:
    def __init__(self, world_setting: dict, infection_setting: dict):
        self.world = World(InfectionModel(**infection_setting), world_setting)

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
