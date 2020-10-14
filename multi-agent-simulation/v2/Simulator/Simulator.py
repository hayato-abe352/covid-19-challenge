"""
MASシミュレーター
"""
import sys
import glob
import os
import itertools
from datetime import datetime

import pandas as pd
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

        # シミュレーションを実行
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

        # 結果出力
        self.output_results()

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

    def output_results(self):
        """ シミュレーションの結果出力 """
        self.output_simulation_result()
        self.output_infected_chart()
        self.output_population_chart()
        self.output_outflow_chart()

    def save_record(self, episode: int, day: int, env: Environment):
        """ Recorder にデータを記録 """
        city = env.name
        travelers = len(self.world.get_travelers(env.name))
        seir = self._get_seir_counts(env)
        self.recorder.add_record(episode, day, city, travelers, *seir)

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
        targets = [
            "output/*.csv",
            "output/animations/*.mp4",
            "output/images/*.png",
        ]
        for target in targets:
            for path in glob.glob(target):
                if os.path.isfile(path):
                    os.remove(path)
        logger.info("出力先ディレクトリをクリアしました。")

    def load_simulation_result(self, path: str):
        """ シミュレーション結果の CSV ファイルを読み込み """
        filename = os.path.basename(path)
        logger.info("シミュレーション結果 {} を読み込んでいます...".format(filename))
        data = pd.read_csv(path)
        self.recorder.set_dataframe(data)
        logger.info("シミュレーション結果 {} を読み込みました。".format(filename))

    def output_simulation_result(self):
        """ シミュレーション結果の CSV ファイルを出力 """
        data = self.recorder.get_dataframe()

        filename = "simulation_result_{}.csv".format(
            datetime.now().strftime("%Y%m%d_%H%M%S")
        )
        logger.info("シミュレーション結果 {} を出力しています...".format(filename))
        path = "output/{}".format(filename)
        data.to_csv(path, index=False)
        logger.info("シミュレーション結果 {} を出力しました。".format(filename))

    def output_world_graph(self):
        """ World のネットワーク図を出力 """
        pass

    def output_infected_chart(self):
        """ 感染者推移に関するグラフを出力 """
        data = self.recorder.get_dataframe()

        params = [True, False]
        for (
            exposed,
            total,
            percentage,
        ) in itertools.product(params, repeat=3):
            path = "output/images/infected{}{}{}.png".format(
                "_and_exposed" if exposed else "",
                "_total" if total else "",
                "_percentage" if percentage else "",
            )
            title = "infected{}{}{}".format(
                " + exposed" if exposed else "",
                " (all envs)" if total else "",
                " [%]" if percentage else "",
            )
            Visualizer.output_infected_chart(
                path, data, exposed, total, percentage, title
            )

    def output_population_chart(self):
        """ 各都市の滞在者人口グラフを出力 """
        data = self.recorder.get_dataframe()

        path = "output/images/population.png"
        title = "population"
        Visualizer.output_population_chart(path, data, title=title)

    def output_outflow_chart(self):
        """ 各都市の流出者推移グラフを出力 """
        data = self.recorder.get_dataframe()

        path = "output/images/outflow.png"
        title = "outflow"
        Visualizer.output_outflow_chart(path, data, title=title)

        path = "output/images/outflow_aggregated.png"
        title = "outflow (all environments)"
        Visualizer.output_outflow_chart(path, data, total=True, title=title)

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
