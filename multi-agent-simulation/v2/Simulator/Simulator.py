"""
MASシミュレーター
"""
import sys
import glob
import os
import itertools
from typing import Tuple
from datetime import datetime

import pandas as pd
from loguru import logger
from tqdm import tqdm

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
        agent_setting: dict,
        infection_setting: dict,
    ):
        self.setting = simulation_setting
        self.world = World(
            InfectionModel(**infection_setting), world_setting, agent_setting
        )

        self.recorder = Recorder()

    def run(self):
        """ シミュレーションを実行 """
        self.clear_output_dirs()

        # シミュレーションを実行
        for episode in range(self.setting["episode"]):
            logger.info(
                "Episode {} を開始します。days={} (+ wake up {})".format(
                    episode,
                    self.setting["days"],
                    self.setting["wake_up"],
                )
            )
            self.world.reset_environments()

            days = self.setting["days"] + self.setting["wake_up"]
            with tqdm(range(days)) as pbar:
                for day in pbar:
                    is_waking_up = day < self.setting["wake_up"]
                    if is_waking_up:
                        # ウェイクアップ期間中
                        pbar.colour = "yellow"
                    else:
                        pbar.colour = "white"

                    # エポック実行
                    self.one_epoch(is_waking_up=is_waking_up)

                    # データを記録
                    if self.setting["wake_up_visualize"] or (not is_waking_up):
                        record_day = (day - self.setting["wake_up"]) + 1
                        for env in self.world.get_environments():
                            self.save_record(episode, record_day, env)
            self.print_agent_status_count()

        # 結果出力
        self.output_results()

    def one_epoch(self, is_waking_up=False):
        """ 1回のエポックを実行 """
        # 全環境の時間経過処理
        self.world.forward_time()

        # エージェントの環境間移動
        self.world.move_agent()

        # 感染シミュレート
        environments = self.world.get_environments()
        for env in environments:
            # 公務員エージェントに給料を支給
            env.pay_salary_to_public_officials()
            # 前日の税収を env の経済力に反映
            env.update_finance()
            # エージェント間の経済取引を実行
            env.trade()

            # ウェイクアップ時は感染拡大をシミュレートしない
            if is_waking_up:
                continue

            # エージェントの体力値を更新
            env.update_agents_params()
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
        self.output_mental_strength_chart()
        self.output_finance_chart()
        self.output_tax_revenue_chart()
        self.output_income_chart()

    def save_record(self, episode: int, day: int, env: Environment):
        """ Recorder にデータを記録 """
        city = env.name
        travelers = len(self.world.get_travelers(env.name))
        average_ms = self._get_average_mental_strength(env)
        finance = self._get_finance(env)
        tax_revenue = self._get_tax_revenue(env)
        average_income = self._get_average_income(env)
        seird = self._get_seird_counts(env)
        self.recorder.add_record(
            episode,
            day,
            city,
            travelers,
            average_ms,
            finance,
            tax_revenue,
            average_income,
            *seird,
        )

    def print_agent_status_count(self):
        """ 各 Environment の状態別エージェント数をログに出力 """
        environments = self.world.get_environments()
        for env in environments:
            s, e, i, r, d = self._get_seird_counts(env)
            total = s + e + i + r + d
            living = s + e + i + r
            logger.info(
                "{}:\tS:{}\tE:{}\tI:{}\tR:{}\tD:{}\t"
                "TOTAL:{} (living:{}, {:.1f}%)".format(
                    "%12s" % env.name.upper(),
                    s,
                    e,
                    i,
                    r,
                    d,
                    total,
                    living,
                    (living / total) * 100,
                )
            )

    def _get_seird_counts(
        self, env: Environment
    ) -> Tuple[int, int, int, int, int]:
        """ env の s, e, i, r, d のカウント結果を取得 """
        s = env.count_agent(Status.SUSCEPTABLE)
        e = env.count_agent(Status.EXPOSED)
        i = env.count_agent(Status.INFECTED)
        r = env.count_agent(Status.RECOVERED)
        d = env.count_agent(Status.DEATH)
        return s, e, i, r, d

    def _get_average_mental_strength(self, env: Environment) -> float:
        """ 平均メンタル値を取得 """
        return env.get_average_mental_strength()

    def _get_finance(self, env: Environment) -> float:
        """ Environment の経済力を取得 """
        return env.get_finance()

    def _get_tax_revenue(self, env: Environment) -> float:
        """ Environment の税収を取得 """
        return env.get_tax_revenue()

    def _get_average_income(self, env: Environment) -> float:
        """ 平均所得を取得 """
        return env.get_average_income()

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
        mode_list = ["total", "living", "death"]

        for mode in mode_list:
            path = "output/images/population_{}.png".format(mode)
            title = "population ({})".format(mode)
            Visualizer.output_population_chart(
                path, data, mode=mode, title=title
            )

    def output_outflow_chart(self):
        """ 各都市の流出者推移グラフを出力 """
        data = self.recorder.get_dataframe()

        path = "output/images/outflow.png"
        title = "outflow"
        Visualizer.output_outflow_chart(path, data, title=title)

        path = "output/images/outflow_aggregated.png"
        title = "outflow (all environments)"
        Visualizer.output_outflow_chart(path, data, total=True, title=title)

    def output_mental_strength_chart(self):
        """ 各都市ごとの平均メンタル値推移グラフを出力 """
        data = self.recorder.get_dataframe()

        path = "output/images/avg_mental_strength.png"
        title = "average of mental strength"
        Visualizer.output_mental_strength_chart(path, data, title=title)

    def output_finance_chart(self):
        """ 各都市の経済力推移グラフを出力 """
        data = self.recorder.get_dataframe()

        path = "output/images/finance.png"
        title = "finance"
        Visualizer.output_finance_chart(path, data, title=title)

    def output_tax_revenue_chart(self):
        """ 各都市の税収グラフを出力 """
        data = self.recorder.get_dataframe()

        path = "output/images/tax_revenue.png"
        title = "tax revenue"
        Visualizer.output_tax_revenue_chart(path, data, title=title)

    def output_income_chart(self):
        """ 各都市誤との平均所得推移グラフを出力 """
        data = self.recorder.get_dataframe()

        path = "output/images/avg_income.png"
        title = "average of income"
        Visualizer.output_income_chart(path, data, title=title)

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
