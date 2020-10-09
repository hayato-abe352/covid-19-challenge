"""
MASシミュレーター
"""
import sys
import glob
import os

from loguru import logger
from tqdm import tqdm
from typing import Tuple

from Agent.Status import Status
from Environment.World import World
from Environment.Environment import Environment
from Simulator.InfectionModel import InfectionModel
from Simulator.Recorder import Recorder
from Simulator.Visualizer import Visualizer

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

        self.recorder = Recorder()

    def run(self):
        """ シミュレーションを実行 """
        self.clear_output_dirs()

        for episode in range(self.setting["episode"]):
            logger.info("Episode {} を開始します。".format(episode))
            self.world.reset_environments()
            for day in tqdm(range(self.setting["days"])):
                # エポック実行
                self.one_epoch()
                # データを記録
                for env in self.world.get_environments():
                    self.save_record(episode, day + 1, env)
            self.print_agent_status_count()

        self.output_infected_chart()
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

    def save_record(self, episode: int, day: int, env: Environment):
        """ Recorder にデータを記録 """
        city = env.name
        seir = self._get_seir_counts(env)
        self.recorder.add_record(episode, day, city, *seir)

    def print_agent_status_count(self):
        """ 各 Environment の状態別エージェント数をログに出力 """
        environments = self.world.get_environments()
        for env in environments:
            s, e, i, r = self._get_seir_counts(env)
            total = s + e + i + r
            logger.info(
                "{}:\tS:{}\tE:{}\tI:{}\tR:{}\tTOTAL:{}".format(
                    "%12s" % env.name.upper(), s, e, i, r, total
                )
            )

    def _get_seir_counts(self, env: Environment) -> Tuple[int, int, int, int]:
        """ env の s, e, i, r のカウント結果を取得 """
        s = env.count_agent(Status.SUSCEPTABLE)
        e = env.count_agent(Status.EXPOSED)
        i = env.count_agent(Status.INFECTED)
        r = env.count_agent(Status.RECOVERED)
        return s, e, i, r

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

    def output_infected_chart(self):
        """ 感染者推移に関するグラフを出力 """
        data = self.recorder.get_dataframe()

        path = "output/images/infected.png"
        title = "infected"
        Visualizer.output_infected_chart(path, data, title=title)

        path = "output/images/infected_and_exposed.png"
        title = "infected & exposed"
        Visualizer.output_infected_chart(path, data, exposed=True, title=title)

        path = "output/images/accumulated_infected.png"
        title = "accumulated infected"
        Visualizer.output_infected_chart(
            path, data, accumulate=True, title=title
        )

        path = "output/images/accumulated_infected_and_exposed.png"
        title = "accumulated infected & exposed"
        Visualizer.output_infected_chart(
            path, data, accumulate=True, exposed=True, title=title
        )

    def output_seir_charts_each_city(self):
        """ 各都市におけるSEIRチャートを出力 """
        pass

    def output_aggregated_seir_chart_each_city(
        self, title: str = None, method: str = "mean"
    ):
        """ 各都市における集計SEIRチャートを出力 """
        pass

    def output_animation(self):
        """ アニメーションを出力 """
        pass
