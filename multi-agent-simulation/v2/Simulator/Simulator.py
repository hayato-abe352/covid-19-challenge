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
from Environment.Government import Government, QLearningAgent, QLearningAction
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
        q_table_path: str = None,
        q_score_csv: str = None,
    ):
        self.setting = simulation_setting
        self.world = World(
            InfectionModel(**infection_setting),
            world_setting,
            agent_setting,
            simulation_setting["global_hospital_opetaring_setting"],
        )

        self.recorder = Recorder()

        # 感染シミュレーション用のデータを記録するか
        self.simulation_recording = self.setting["simulation_recording"]
        # 機械学習を行うか
        self.q_learning = self.setting["q_learning"]

        # Q-Learning Operation クラス
        tokyo = self.world.get_environment("tokyo")
        self.government = Government(tokyo)
        # Q-Learning Agent クラス
        init_status = self.government.determine_state()
        self.ql_agent = QLearningAgent(
            init_q_table_path=q_table_path,
            observation=".".join([s.name for s in init_status]),
        )

        # Q-Score 記録用 csv を指定された場合は、csv ファイルをロード
        self.q_score_csv = q_score_csv
        if q_score_csv is not None:
            self.recorder.load_q_score_csv(q_score_csv)

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
            self.government.reset_government()

            # Government クラスが意思決定・政策実行を行う周期
            period = self.government.period

            # 初期の観測状態をセット
            init_status = self.government.determine_state()
            self.ql_agent.observe(init_status)

            days = self.setting["days"] + self.setting["wake_up"]
            tokyo = self.world.get_environment("tokyo")
            ql_status = None
            ql_action = None
            ql_rewards = []
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
                    if self.simulation_recording and (
                        self.setting["wake_up_visualize"] or (not is_waking_up)
                    ):
                        record_day = (day - self.setting["wake_up"]) + 1
                        for env in self.world.get_environments():
                            self.save_record(episode, record_day, env)

                    # ウェイクアップ中 または Q学習を行わない場合
                    if is_waking_up or not self.q_learning:
                        continue

                    # 感染シミュレート開始時点の経済力を判定基準値に設定
                    if day == self.setting["wake_up"]:
                        for env in self.world.get_environments():
                            env.set_finance_baseline()

                    # Government クラスへの状況報告
                    infected = tokyo.count_agent(Status.INFECTED)
                    death = tokyo.count_agent(Status.DEATH)
                    self.government.save_data(infected, death)

                    # Government クラスによる意思決定
                    if day % period == 0:
                        # 現在の状況把握
                        env_status = self.government.determine_state()

                        # 過去に実行した政策に対して、現在の状態を踏まえて評価する
                        if ql_action is not None and ql_status is not None:
                            # 報酬を計算
                            if ql_action == QLearningAction.IMPOSSIBLE.value:
                                reward = self.government.get_impossible_score()
                            else:
                                reward = self.government.compute_reward()
                            ql_rewards.append(reward)
                            # Q-Learning Agent の観測と学習
                            self.ql_agent.observe(env_status, reward)

                        # 実行可能なアクションの一覧を取得
                        executable_acts = self.government.get_executable_acts()

                        # アクションを決定
                        action = self.ql_agent.act(executable_acts)
                        if self.government.is_possible_action(action):
                            # アクションが実行可能な場合 => 政策実行
                            self.government.apply_action(action)
                        else:
                            # アクションが実行不可能の場合
                            action = QLearningAction.IMPOSSIBLE.value

                        ql_status = env_status
                        ql_action = action

            if self.q_learning:
                # Q-Leaning モデルの経験済みエピソード数を +1
                self.ql_agent.count_up_episode()

                # Q-スコアの平均値を記録
                ql_episode = self.ql_agent.get_episode_count()
                avg_q_score = sum(ql_rewards) / len(ql_rewards)
                self.recorder.save_q_score(ql_episode, avg_q_score)

                # Q-Learning モデルの記録
                iteration = self.setting["q_table_auto_save_iteration"]
                if iteration != 0 and (episode + 1) % iteration == 0:
                    self.ql_agent.output_q_table()
                    self.output_q_score_csv()
                    self.output_q_score_chart()

                # この episode での Q-Learning 報酬数を出力
                self.print_ql_reward(ql_rewards)

            # この episode での最終 SEIRD 数を出力
            self.print_agent_status_count()

        # Q-Learning 結果出力
        if self.q_learning:
            self.ql_agent.output_q_table()
            self.output_q_score_csv()
            self.output_q_score_chart()

        # シミュレーター結果出力
        if self.simulation_recording:
            self.output_results()

    def one_epoch(self, is_waking_up=False):
        """ 1回のエポックを実行 """
        # 全環境の時間経過処理
        self.world.forward_time()

        # エージェントの環境間移動
        self.world.move_agent()

        # 経済活動・感染シミュレート
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
            # エージェントの状態を更新 + 入院/退院処理
            env.update_agents_status()

            # 患者数に応じて病院稼働コストを消費
            env.consume_hospital_operating_cost()

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
        self.output_patients_chart()
        self.output_seir_charts()

    def save_record(self, episode: int, day: int, env: Environment):
        """ Recorder にデータを記録 """
        city = env.name
        travelers = len(self.world.get_travelers(env.name))
        average_ms = self._get_average_mental_strength(env)
        finance = self._get_finance(env)
        tax_revenue = self._get_tax_revenue(env)
        average_income = self._get_average_income(env)
        patients = self._get_patients_count(env)
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
            patients,
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

    def print_ql_reward(self, ql_reward):
        """ Q-Learning の報酬情報をログに出力 """
        logger.info(
            "Q-LEARNING REWARDS: total={:.2f}, avg={:.2f}".format(
                sum(ql_reward), sum(ql_reward) / len(ql_reward)
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

    def _get_patients_count(self, env: Environment) -> int:
        """ 患者数を取得 """
        return env.count_patients()

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

    def output_q_score_csv(self):
        """ Q-Score (.csv) ファイルを出力 """
        data = self.recorder.get_q_score()

        output_path = self.q_score_csv
        if output_path is None:
            model_id = self.ql_agent.model_id
            output_path = "output/models/q-score-{}.csv".format(model_id)

        filename = os.path.basename(output_path)
        logger.info("Q-Score {} を出力しています...".format(filename))
        data.to_csv(output_path, index=False)
        logger.info("Q-Score {} を出力しました。".format(filename))

        pass

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

    def output_patients_chart(self):
        """ 患者数の推移グラフを出力 """
        data = self.recorder.get_dataframe()

        path = "output/images/patients.png"
        title = "patitens count"
        Visualizer.output_patients_chart(path, data, title=title)

    def output_seir_charts(self):
        """ 各都市におけるSEIRチャートを出力 """
        data = self.recorder.get_dataframe()
        envs = [e.name for e in self.world.get_environments()] + [None]
        for env in envs:
            path = "output/images/seir_{}.png".format(
                env if env is not None else "all"
            )
            title = "SEIR-chart in {}".format(
                env if env is not None else "total"
            )
            Visualizer.output_seir_chart(path, data, env_name=env, title=title)

    def output_aggregated_seir_chart_each_city(
        self, title: str = None, method: str = "mean"
    ):
        """ 各都市における集計SEIRチャートを出力 """
        pass

    def output_animation(self):
        """ アニメーションを出力 """
        pass

    def output_q_score_chart(self):
        """ Q-スコアの推移を出力 """
        data = self.recorder.get_q_score()
        path = "output/images/q-score.png"
        Visualizer.output_q_score(path, data)
