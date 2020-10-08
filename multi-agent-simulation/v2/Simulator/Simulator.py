"""
MASシミュレーター
"""
import sys
import glob
import os

from loguru import logger
from tqdm import tqdm

from Agent.Status import Status
from Environment.World import World
from Simulator.InfectionModel import InfectionModel

logger.remove()
logger.add(sys.stdout, colorize=True, backtrace=False, diagnose=False)


class Simulator:
    def __init__(
        self,
        simulation_setting: dict,
        world_setting: dict,
        infection_setting: dict,
    ):
        self.setting = simulation_setting
        self.world = World(InfectionModel(**infection_setting), world_setting)

    def run(self):
        """ シミュレーションを実行 """
        self.clear_output_dirs()

        for episode in range(self.setting["episode"]):
            logger.info("Episode {} を開始します。".format(episode))
            self.world.reset_environments()
            for day in tqdm(range(self.setting["days"])):
                self.one_epoch()
            self.print_agent_status_count()
        pass

    def one_epoch(self):
        """ 1回のエポックを実行 """
        # 全環境の時間経過処理
        self.world.forward_time()

        # エージェントの環境間移動
        self.world.move_agent()

        # 感染シミュレート
        environments = self.world.get_environments()
        for env in environments:
            # エージェントの次ステータスを決定
            env.decide_agents_next_status()
            # エージェントの状態を更新
            env.update_agents_status()

    def print_agent_status_count(self):
        """ 各 Environment の状態別エージェント数をログに出力 """
        environments = self.world.get_environments()
        for env in environments:
            s = env.count_agent(Status.SUSCEPTABLE)
            e = env.count_agent(Status.EXPOSED)
            i = env.count_agent(Status.INFECTED)
            r = env.count_agent(Status.RECOVERED)
            total = s + e + i + r
            logger.info(
                "{}:\tS:{}\tE:{}\tI:{}\tR:{}\tTOTAL:{}".format(
                    "%12s" % env.name.upper(), s, e, i, r, total
                )
            )

    def clear_output_dirs(self):
        """ 出力ディレクトリをクリア """
        targets = ["outputs/animations/*.mp4", "outputs/images/*mp4"]
        for target in targets:
            for path in glob.glob(target):
                if os.path.isfile(path):
                    os.remove(path)
        logger.info("出力先ディレクトリをクリアしました。")

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
