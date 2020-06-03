"""
MASシミュレーター
"""
import glob
import math
import os
import sys
from collections import OrderedDict

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from loguru import logger
from tqdm import tqdm

from Agent import Status
from Environment import Environment

logger.remove()
logger.add(sys.stdout, colorize=True, backtrace=False, diagnose=False)


class Simulator:
    def __init__(
        self,
        infection_model,
        simulation_days,
        episode_num,
        env_size,
        population,
        init_infected_num,
        hospital_capacity,
        observation_period,
        agent_moving,
    ):
        # シミュレートする感染症モデル
        self.infection_model = infection_model

        # シミュレーション日数
        self.simulation_days = simulation_days
        # エピソード数
        self.episode_num = episode_num

        # 環境サイズ
        self.env_size = env_size
        # エージェント数（人口）
        self.population = population
        # 初期感染者数
        self.init_infected_num = init_infected_num
        # Hospital キャパシティ
        self.hospital_capacity = hospital_capacity
        # 観察期間
        self.observation_period = observation_period

        # エージェントの移動パターン
        self.agent_moving = agent_moving

        # グラフ描画用
        self.t_values = []
        self.s_values = []
        self.i_values = []
        self.r_values = []
        self.patients_values = []
        self.snap_shots = []
        self.s_values_in_all_episode = []
        self.i_values_in_all_episode = []
        self.r_values_in_all_episode = []
        self.patients_values_in_all_episode = []
        self.snap_shots_in_all_episode = []

    def one_epoch(self, env, day):
        """ 1回のepochを実行 (1-epoch = 1-day) """
        public_sections = [
            sec for sec in env.sections if sec["attribute"] == "public"
        ]

        # 1時間ごとに Agent を行動させる
        snap_shots = []
        with tqdm(range(24)) as pbar:
            for hour in pbar:
                pbar.set_description("[Day:{} Hour:{}]".format(day, hour))
                snap_shots.append(env.get_snap_shot_df())

                # エージェントの次の位置を決定
                for agent in env.agents:
                    # 同じ区画に属している Agent を記録
                    agent.neighbor_agents.extend(
                        env.get_neighbor_agents(agent)
                    )
                    agent.decide_action(
                        0,
                        self.env_size,
                        0,
                        self.env_size,
                        public_sections,
                        self.agent_moving,
                        hour,
                    )
                # エージェントの位置を更新
                for agent in env.agents:
                    agent.do_action()

        # 1日が終了したら、Agent の状態を更新
        for agent in env.agents:
            agent.decide_next_status()
        for agent in env.agents:
            agent.update_status()

        # 病院への収容・病院からの退院を実行
        #   - 入院処理 => 退院処理の順に実行
        #     (空いた病床に新たな患者が入るのは早くても翌日になる)
        env.accommodate_to_hospital()
        env.leave_from_hospital()

        return snap_shots

    def run(self):
        """ シミュレーションを実行 """
        self.clear_output_dirs()

        self.s_values_in_all_episode = []
        self.i_values_in_all_episode = []
        self.r_values_in_all_episode = []
        self.patients_values_in_all_episode = []
        self.snap_shots_in_all_episode = []
        logger.info(
            "シミュレーション開始 Episode: {} (Day: {})".format(
                self.episode_num, self.simulation_days
            )
        )
        for episode in range(self.episode_num):
            # 環境を生成し、エージェントを初期化
            env = Environment(
                self.env_size,
                self.population,
                self.infection_model,
                self.hospital_capacity,
                self.observation_period,
            )
            env.init_agents(self.init_infected_num)

            # 初期状態を記録
            susceptable_num = env.count_susceptable()
            infected_num = env.count_infected()
            recovered_num = env.count_recovered()
            patients_num = env.count_hospital_parients()
            logger.info(
                "Population density: {} [members/square]".format(
                    self.population / (self.env_size ** 2)
                )
            )

            self.t_values = [0]
            self.s_values = [susceptable_num]
            self.i_values = [infected_num]
            self.r_values = [recovered_num]
            self.patients_values = [patients_num]
            self.snap_shots = []

            with tqdm(range(self.simulation_days)) as pbar:
                for day in pbar:
                    snap_shots = self.one_epoch(env, day + 1)

                    susceptable_num = env.count_susceptable()
                    infected_num = env.count_infected()
                    recovered_num = env.count_recovered()
                    patients_num = env.count_hospital_parients()

                    self.t_values.append(day + 1)
                    self.s_values.append(susceptable_num)
                    self.i_values.append(infected_num)
                    self.r_values.append(recovered_num)
                    self.patients_values.append(patients_num)
                    self.snap_shots.append(snap_shots)

                    pbar.set_description("[Run: Episode {}]".format(episode))
                    pbar.set_postfix(
                        OrderedDict(
                            day=day + 1,
                            s=susceptable_num,
                            i=infected_num,
                            r=recovered_num,
                            p=patients_num,
                        )
                    )
            self.s_values_in_all_episode.append(self.s_values)
            self.i_values_in_all_episode.append(self.i_values)
            self.r_values_in_all_episode.append(self.r_values)
            self.patients_values_in_all_episode.append(self.patients_values)
            self.snap_shots_in_all_episode.append(self.snap_shots)
        logger.info("シミュレーション終了")

    def clear_output_dirs(self):
        """ 出力ディレクトリの中身をクリア """
        target_dirs = [
            "outputs/animations/*.mp4",
            "outputs/images/*.png",
            "outputs/logs/*.csv",
        ]
        logger.info("出力ディレクトリの中身をクリアします")
        for target_dir in target_dirs:
            for path in glob.glob(target_dir):
                if os.path.isfile(path):
                    os.remove(path)
        logger.info("出力ディレクトリの中身をクリアしました")

    def output_logs(self):
        """ シミュレーションログを出力 """
        logger.info("ログ出力を開始します")
        for episode in range(self.episode_num):
            s_values = self.s_values_in_all_episode[episode]
            i_values = self.i_values_in_all_episode[episode]
            r_values = self.r_values_in_all_episode[episode]
            p_values = self.patients_values_in_all_episode[episode]
            df = pd.DataFrame(
                columns=[
                    "Day",
                    "Susceptable",
                    "Infected",
                    "Recovered",
                    "Patients",
                ]
            )
            with tqdm(
                zip(self.t_values, s_values, i_values, r_values, p_values),
                total=len(self.t_values),
            ) as pbar:
                for t, s, i, r, p in pbar:
                    pbar.set_description(
                        "[LogOutput: Episode {}]".format(episode)
                    )
                    record = pd.Series(index=df.columns, dtype="object")
                    record["Day"] = t
                    record["Susceptable"] = s
                    record["Infected"] = i
                    record["Recovered"] = r
                    record["Patients"] = p
                    df = df.append(record, ignore_index=True)
                df.to_csv(
                    "outputs/logs/episode-{}.csv".format(episode), index=False
                )
                logger.info("episode-{}.csv を出力しました".format(episode))

    def output_sir_charts(self):
        """ SIRチャートを出力 """
        logger.info("ラインチャート出力を開始します")
        for episode in range(self.episode_num):
            plt.clf()

            s_values = self.s_values_in_all_episode[episode]
            i_values = self.i_values_in_all_episode[episode]
            r_values = self.r_values_in_all_episode[episode]
            df = pd.DataFrame(columns=["Day", "Count", "Status"])
            with tqdm(
                zip(self.t_values, s_values, i_values, r_values),
                total=len(self.t_values),
            ) as pbar:
                for t, s, i, r in pbar:
                    pbar.set_description(
                        "[LineChartOutput: Episode {}]".format(episode)
                    )

                    s_record = pd.Series(index=df.columns, dtype="object")
                    s_record["Day"] = t
                    s_record["Count"] = s
                    s_record["Status"] = Status.SUSCEPTABLE.value
                    df = df.append(s_record, ignore_index=True)

                    i_record = pd.Series(index=df.columns, dtype="object")
                    i_record["Day"] = t
                    i_record["Count"] = i
                    i_record["Status"] = Status.INFECTED.value
                    df = df.append(i_record, ignore_index=True)

                    r_record = pd.Series(index=df.columns, dtype="object")
                    r_record["Day"] = t
                    r_record["Count"] = r
                    r_record["Status"] = Status.RECOVERED.value
                    df = df.append(r_record, ignore_index=True)

            df["Day"] = df["Day"].astype(int)
            df["Count"] = df["Count"].astype(int)

            sns.lineplot(x="Day", y="Count", hue="Status", data=df)
            plt.savefig("outputs/images/episode-{}.png".format(episode))
            logger.info("episode-{}.png を出力しました".format(episode))

    def output_aggregated_sir_chart(self, title=None, estimator="mean"):
        """ 集計結果のSIRチャートを出力
        
        Parameters
        ----------
        title : str, optional
            タイトル
        estimator : str, optional
            集計方法（デフォルトは平均値）
            Noneを指定した場合は、全エピソードの結果を重ねてプロット
        """
        logger.info("集計結果ラインチャートの出力を開始します estimator:{}".format(estimator))
        plt.clf()
        df = pd.DataFrame(columns=["Episode", "Day", "Count", "Status"])
        for episode in tqdm(range(self.episode_num)):
            s_values = self.s_values_in_all_episode[episode]
            i_values = self.i_values_in_all_episode[episode]
            r_values = self.r_values_in_all_episode[episode]
            for t, s, i, r in zip(self.t_values, s_values, i_values, r_values):
                s_record = pd.Series(index=df.columns, dtype="object")
                s_record["Episode"] = episode
                s_record["Day"] = t
                s_record["Count"] = s
                s_record["Status"] = Status.SUSCEPTABLE.value
                df = df.append(s_record, ignore_index=True)

                i_record = pd.Series(index=df.columns, dtype="object")
                i_record["Episode"] = episode
                i_record["Day"] = t
                i_record["Count"] = i
                i_record["Status"] = Status.INFECTED.value
                df = df.append(i_record, ignore_index=True)

                r_record = pd.Series(index=df.columns, dtype="object")
                r_record["Episode"] = episode
                r_record["Day"] = t
                r_record["Count"] = r
                r_record["Status"] = Status.RECOVERED.value
                df = df.append(r_record, ignore_index=True)

        df["Episode"] = df["Episode"].astype(str)
        df["Day"] = df["Day"].astype(int)
        df["Count"] = df["Count"].astype(int)
        df["Status"] = df["Status"].astype(str)

        if title is not None:
            plt.title(title)

        if estimator is None:
            sns.lineplot(
                x="Day",
                y="Count",
                hue="Status",
                units="Episode",
                estimator=estimator,
                data=df,
            )
            output_path = "outputs/images/aggrigated-all.png"
        else:
            sns.lineplot(
                x="Day", y="Count", hue="Status", estimator=estimator, data=df
            )
            output_path = "outputs/images/aggrigated-{}.png".format(estimator)
        plt.savefig(output_path)
        logger.info("集計結果ラインチャートを出力しました")

    def output_hospital_patients_charts(self, capacity):
        """ 病院の患者数遷移ラインチャートを出力 """
        logger.info("病院の患者数遷移グラフの出力を開始します")
        for episode in range(self.episode_num):
            plt.clf()
            plt.xlim(0, capacity)

            p_values = self.patients_values_in_all_episode[episode]
            df = pd.DataFrame(columns=["Day", "Count"])
            with tqdm(zip(self.t_values, p_values)) as pbar:
                for t, p in pbar:
                    pbar.set_description(
                        "[PatientsChartOutput: Episode {}]".format(episode)
                    )

                    record = pd.Series(index=df.columns, dtype="object")
                    record["Day"] = t
                    record["Count"] = p
                    df = df.append(record, ignore_index=True)

            df["Day"] = df["Day"].astype(int)
            df["Count"] = df["Count"].astype(int)

            sns.lineplot(x="Day", y="Count", data=df)
            plt.savefig(
                "outputs/images/patients-episode-{}.png".format(episode)
            )
            logger.info("patients-episode-{}.png を出力しました".format(episode))

    def output_hospital_patients_aggregated_chart(
        self, capacity, title=None, estimator="mean"
    ):
        """ 病院の患者数集計ラインチャートを出力

        Parameters
        ----------
        title : str, optional
            タイトル
        estimator : str, optional
            集計方法（デフォルトは平均値）
            Noneを指定した場合は、全エピソードの結果を重ねてプロット
        """
        logger.info("病院の患者数集計グラフの出力を開始します")
        plt.clf()
        plt.xlim(0, capacity)
        df = pd.DataFrame(columns=["Episode", "Day", "Count"])
        for episode in tqdm(range(self.episode_num)):
            p_values = self.patients_values_in_all_episode[episode]
            for t, p in zip(self.t_values, p_values):
                record = pd.Series(index=df.columns, dtype="object")
                record["Episode"] = episode
                record["Day"] = t
                record["Count"] = p
                df = df.append(record, ignore_index=True)

        df["Episode"] = df["Episode"].astype(str)
        df["Day"] = df["Day"].astype(int)
        df["Count"] = df["Count"].astype(int)

        if title is not None:
            plt.title(title)

        if estimator is None:
            sns.lineplot(
                x="Day",
                y="Count",
                units="Episode",
                estimator=estimator,
                data=df,
            )
            output_path = "outputs/images/patients-aggrigated-all.png"
        else:
            sns.lineplot(x="Day", y="Count", estimator=estimator, data=df)
            output_path = "outputs/images/patients-aggrigated-{}.png".format(
                estimator
            )
        plt.savefig(output_path)
        logger.info("病院の患者数集計グラフを出力しました")

    def output_animation(self, interval=100):
        """ シミュレーション結果の動画を出力

        Parameters
        ----------
        interval : int, optional
            フレーム切り替え時間[ms]（デフォルトは200ms）
        """
        logger.info("アニメーションの出力を開始します")
        for episode in range(self.episode_num):
            plt.clf()
            fig = plt.figure(figsize=(5, 5))

            margin = math.ceil(self.env_size * 0.05)
            plt.xlim(-margin, self.env_size + margin)
            plt.ylim(-margin, self.env_size + margin)

            artists = []
            snap_shots_in_days = self.snap_shots_in_all_episode[episode]
            with tqdm(snap_shots_in_days) as pbar:
                for d_idx, snap_shots_in_hours in enumerate(pbar):
                    pbar.set_description(
                        "[AnimationOutput: Episode {}]".format(episode)
                    )

                    for h_idx, df in enumerate(snap_shots_in_hours):
                        df.loc[
                            df["status"] == Status.SUSCEPTABLE, "color"
                        ] = "lightskyblue"
                        df.loc[
                            (df["status"] == Status.INFECTED)
                            & ~(df["is_patient"]),
                            "color",
                        ] = "red"
                        df.loc[
                            (df["status"] == Status.INFECTED)
                            & (df["is_patient"]),
                            "color",
                        ] = "darkgrey"
                        df.loc[
                            df["status"] == Status.RECOVERED, "color"
                        ] = "lightgreen"

                        artist = plt.scatter(df["x"], df["y"], c=df["color"])
                        title = plt.text(
                            -margin,
                            -margin,
                            "Day:{} Hour:{}".format(d_idx + 1, h_idx),
                            fontsize="small",
                        )
                        artists.append([artist, title])

            anim = animation.ArtistAnimation(fig, artists, interval=interval)
            anim.save(
                "outputs/animations/episode-{}.mp4".format(episode),
                writer="ffmpeg",
            )
            logger.info("episode-{}.mp4 を出力しました".format(episode))
