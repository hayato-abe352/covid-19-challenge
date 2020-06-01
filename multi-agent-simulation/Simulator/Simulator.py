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

        # エージェントの移動パターン
        self.agent_moving = agent_moving

        # グラフ描画用
        self.t_values = []
        self.s_values = []
        self.i_values = []
        self.r_values = []
        self.snap_shots = []
        self.s_values_in_all_episode = []
        self.i_values_in_all_episode = []
        self.r_values_in_all_episode = []
        self.snap_shots_in_all_episode = []

    def one_epoch(self, env):
        """ 1回のエピソードを実行 """
        # エージェントの次の位置・ステータスを決定
        for agent in env.agents:
            agent.neighbor_agents = env.get_neighbor_agents(agent)
            agent.decide_next_position(
                0, self.env_size, 0, self.env_size, self.agent_moving
            )
            agent.decide_next_status()

        # エージェントの位置・ステータスを更新
        for agent in env.agents:
            agent.update_position()
            agent.update_status()

    def run(self):
        """ シミュレーションを実行 """
        self.clear_output_dirs()

        self.s_values_in_all_episode = []
        self.i_values_in_all_episode = []
        self.r_values_in_all_episode = []
        self.snap_shots_in_all_episode = []
        logger.info(
            "シミュレーション開始 Episode: {} (Day: {})".format(
                self.episode_num, self.simulation_days
            )
        )
        for episode in range(self.episode_num):
            # 環境を生成し、エージェントを初期化
            env = Environment(
                self.env_size, self.population, self.infection_model
            )
            env.init_agents(self.init_infected_num)

            # 初期状態を記録
            susceptable_num = env.count_susceptable()
            infected_num = env.count_infected()
            recovered_num = env.count_recovered()
            logger.info(
                "Population density: {} [members/square]".format(
                    self.population / (self.env_size ** 2)
                )
            )

            self.t_values = [0]
            self.s_values = [susceptable_num]
            self.i_values = [infected_num]
            self.r_values = [recovered_num]
            self.snap_shots = []

            with tqdm(range(self.simulation_days)) as pbar:
                for day in pbar:
                    self.one_epoch(env)

                    susceptable_num = env.count_susceptable()
                    infected_num = env.count_infected()
                    recovered_num = env.count_recovered()

                    self.t_values.append(day + 1)
                    self.s_values.append(susceptable_num)
                    self.i_values.append(infected_num)
                    self.r_values.append(recovered_num)
                    self.snap_shots.append(env.get_snap_shot_df())

                    pbar.set_description("[Run: Episode {}]".format(episode))
                    pbar.set_postfix(
                        OrderedDict(
                            day=day + 1,
                            s=susceptable_num,
                            i=infected_num,
                            r=recovered_num,
                        )
                    )
                self.s_values_in_all_episode.append(self.s_values)
                self.i_values_in_all_episode.append(self.i_values)
                self.r_values_in_all_episode.append(self.r_values)
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
            df = pd.DataFrame(
                columns=["Day", "Susceptable", "Infected", "Recovered"]
            )
            with tqdm(
                zip(self.t_values, s_values, i_values, r_values),
                total=len(self.t_values),
            ) as pbar:
                for t, s, i, r in pbar:
                    pbar.set_description(
                        "[LogOutput: Episode {}]".format(episode)
                    )
                    record = pd.Series(index=df.columns, dtype="object")
                    record["Day"] = t
                    record["Susceptable"] = s
                    record["Infected"] = i
                    record["Recovered"] = r
                    df = df.append(record, ignore_index=True)
                df.to_csv(
                    "outputs/logs/episode-{}.csv".format(episode), index=False
                )
                logger.info("episode-{}.csv を出力しました".format(episode))

    def output_line_charts(self):
        """ ラインチャートを出力 """
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

    def output_aggregated_line_chart(self, title=None, estimator="mean"):
        """ 集計結果のラインチャートを出力
        
        Parameters
        ----------
        estimator : str, optional
            集計方法（デフォルトは平均値）
            Noneを指定した場合は、全エピソードの結果を重ねてプロット
        """
        logger.info("集計結果ラインチャートの出力を開始します")
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
        else:
            sns.lineplot(
                x="Day", y="Count", hue="Status", estimator=estimator, data=df
            )
        plt.savefig("outputs/images/aggrigated.png")
        logger.info("aggrigated.png を出力しました")

    def output_animation(self, interval=500):
        """ シミュレーション結果の動画を出力

        Parameters
        ----------
        interval : int, optional
            フレーム切り替え時間[ms]（デフォルトは200ms）
        """
        logger.info("アニメーションの出力を開始します")
        for episode in range(self.episode_num):
            plt.clf()
            fig = plt.figure()

            margin = math.ceil(self.env_size * 0.05)
            plt.xlim(-margin, self.env_size + margin)
            plt.ylim(-margin, self.env_size + margin)

            artists = []
            snap_shots = self.snap_shots_in_all_episode[episode]
            with tqdm(snap_shots) as pbar:
                for idx, df in enumerate(pbar):
                    pbar.set_description(
                        "[AnimationOutput: Episode {}]".format(episode)
                    )

                    df.loc[
                        df["status"] == Status.SUSCEPTABLE, "color"
                    ] = "lightskyblue"
                    df.loc[df["status"] == Status.INFECTED, "color"] = "red"
                    df.loc[
                        df["status"] == Status.RECOVERED, "color"
                    ] = "lightgreen"

                    artist = plt.scatter(df["x"], df["y"], c=df["color"])
                    title = plt.text(
                        -margin,
                        -margin,
                        "Day:{}".format(idx + 1),
                        fontsize="small",
                    )
                    artists.append([artist, title])

            anim = animation.ArtistAnimation(fig, artists, interval=interval)
            anim.save(
                "outputs/animations/episode-{}.mp4".format(episode),
                writer="ffmpeg",
            )
            logger.info("episode-{}.mp4 を出力しました".format(episode))
