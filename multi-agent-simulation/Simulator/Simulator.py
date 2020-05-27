"""
MASシミュレーター
"""
import math
from collections import OrderedDict

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from tqdm import tqdm

from Agent import Status
from Environment import Environment


class Simulator:
    def __init__(
        self,
        infection_model,
        simulation_days,
        episode_num,
        env_size,
        population,
        init_infected_num,
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

        # グラフ描画用
        self.t_values = []
        self.s_values = []
        self.i_values = []
        self.r_values = []
        self.snap_shots = []
        self.i_values_in_all_episode = []

    def one_epoch(self, env):
        """ 1回のエピソードを実行 """
        # エージェントの次の位置・ステータスを決定
        for agent in env.agents:
            agent.neighbor_agents = env.get_neighbor_agents(agent)
            agent.decide_next_position(0, self.env_size, 0, self.env_size)
            agent.decide_next_status()

        # エージェントの位置・ステータスを更新
        for agent in env.agents:
            agent.update_position()
            agent.update_status()

    def run(self):
        """ シミュレーションを実行 """
        self.i_values_in_all_episode = []
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
            print(
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

                    pbar.set_description("[Episode {}]".format(episode))
                    pbar.set_postfix(
                        OrderedDict(
                            day=day + 1,
                            s=susceptable_num,
                            i=infected_num,
                            r=recovered_num,
                        )
                    )
                self.i_values_in_all_episode.append(self.i_values)

    def output_logs(self):
        """ シミュレーションログを出力 """
        for episode in range(self.episode_num):
            df = pd.DataFrame(
                columns=["Day", "Susceptable", "Infected", "Recovered"]
            )
            for t, s, i, r in tqdm(
                zip(
                    self.t_values, self.s_values, self.i_values, self.r_values
                ),
                total=len(self.t_values),
            ):
                record = pd.Series(index=df.columns, dtype="object")
                record["Day"] = t
                record["Susceptable"] = s
                record["Infected"] = i
                record["Recovered"] = r
                df = df.append(record, ignore_index=True)
            df.to_csv(
                "outputs/logs/episode-{}.csv".format(episode), index=False
            )
            print("episode-{}.csv を出力しました".format(episode))

    def output_line_charts(self):
        """ ラインチャートを出力 """
        for episode in range(self.episode_num):
            plt.clf()
            df = pd.DataFrame(columns=["Day", "Count", "Status"])

            for t, s, i, r in tqdm(
                zip(
                    self.t_values, self.s_values, self.i_values, self.r_values
                ),
                total=len(self.t_values),
            ):
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
            plt.savefig("output/images/episode-{}.png".format(episode))
            print("episode-{}.png を出力しました".format(episode))

    def output_aggregated_line_chart(self, estimator="mean"):
        """ 集計結果のラインチャートを出力
        
        Parameters
        ----------
        estimator : str, optional
            集計方法（デフォルトは平均値）
            Noneを指定した場合は、全エピソードの結果を重ねてプロット
        """
        plt.clf()
        df = pd.DataFrame(columns=["Episode", "Day", "Count"])
        for episode, i_values in enumerate(self.i_values_in_all_episode):
            for t, i in zip(self.t_values, i_values):
                i_record = pd.Series(index=df.columns, dtype="object")
                i_record["Episode"] = episode
                i_record["Day"] = t
                i_record["Count"] = i
                df = df.append(i_record, ignore_index=True)

        df["Episode"] = df["Episode"].astype(str)
        df["Day"] = df["Day"].astype(int)
        df["Count"] = df["Count"].astype(int)

        if estimator is None:
            sns.lineplot(
                x="Day",
                y="Count",
                units="Episode",
                estimator=estimator,
                data=df,
            )
        else:
            sns.lineplot(x="Day", y="Count", estimator=estimator, data=df)
        plt.savefig("output/images/aggrigated.png")
        print("aggrigated.png を出力しました")

    def output_animation(self, interval=200):
        """ シミュレーション結果の動画を出力
        
        Parameters
        ----------
        interval : int, optional
            フレーム切り替え時間[ms]（デフォルトは200ms）
        """
        for episode in range(self.episode_num):
            plt.clf()
            fig = plt.figure()

            margin = math.ceil(self.env_size * 0.05)
            plt.xlim(-margin, self.env_size + margin)
            plt.ylim(-margin, self.env_size + margin)

            artists = []
            for idx, df in enumerate(tqdm(self.snap_shots)):
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
                "output/animations/episode-{}.mp4".format(episode),
                write="ffmpeg",
            )
            print("episode-{}.mp4 を出力しました".format(episode))
