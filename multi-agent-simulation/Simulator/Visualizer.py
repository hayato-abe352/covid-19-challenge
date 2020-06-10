"""
可視化 (グラフ出力) 関連の関数定義
"""
import math

import matplotlib.animation as animation
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from tqdm import tqdm

from Agent import Status


class Visualizer:
    @classmethod
    def output_section_map(cls, section_map, env_size, path):
        """ Environment の区画マップを出力します """
        plt.clf()
        plt.figure()
        ax = plt.axes()

        margin = math.ceil(env_size * 0.05)
        plt.xlim(-margin, env_size + margin)
        plt.ylim(-margin, env_size + margin)

        for section in section_map:
            fill_color = (
                "#FFFCCC" if section["attribute"] == "public" else "#CCFFFC"
            )

            rect = patches.Rectangle(
                xy=(section["x_min"], section["y_min"]),
                width=section["x_max"] - section["x_min"],
                height=section["y_max"] - section["y_min"],
                ec="white",
                fc=fill_color,
            )
            ax.add_patch(rect)

        plt.axis("scaled")
        ax.set_aspect("equal")
        plt.savefig(path)

    @classmethod
    def output_sir_chart(cls, episode, s_values, i_values, r_values, path):
        """ SIRチャートを出力 """
        plt.clf()

        df = pd.DataFrame(columns=["Day", "Count", "Status"])
        with tqdm(
            zip(list(range(len(s_values))), s_values, i_values, r_values),
            total=len(s_values),
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
        plt.savefig(path)

    @classmethod
    def output_aggregated_sir_chart(
        cls,
        episode_num,
        s_values,
        i_values,
        r_values,
        path,
        title=None,
        estimator="mean",
    ):
        """ 集計SIRチャートを出力 """
        plt.clf()

        df = pd.DataFrame(columns=["Episode", "Day", "Count", "Status"])
        for episode in tqdm(range(episode_num)):
            s_val = s_values[episode]
            i_val = i_values[episode]
            r_val = r_values[episode]
            t_val = list(range(len(s_val)))
            for t, s, i, r in zip(t_val, s_val, i_val, r_val):
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

        plt.savefig(path)

    @classmethod
    def output_hospital_patients_chart(cls, episode, capacity, p_values, path):
        """ 病院の患者数遷移チャートを出力 """
        plt.clf()
        plt.ylim(0, capacity)

        df = pd.DataFrame(columns=["Day", "Count"])
        with tqdm(p_values) as pbar:
            for t, p in enumerate(pbar):
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
        plt.savefig(path)

    @classmethod
    def output_hospital_patients_aggregated_chart(
        cls,
        episode_num,
        capacity,
        p_values,
        path,
        title=None,
        estimator="mean",
    ):
        """ 病院の患者数推移の集計チャートを出力 """
        plt.clf()
        plt.ylim(0, capacity)

        df = pd.DataFrame(columns=["Episode", "Day", "Count"])
        for episode in tqdm(range(episode_num)):
            p_val = p_values[episode]
            for t, p in enumerate(p_val):
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
        else:
            sns.lineplot(x="Day", y="Count", estimator=estimator, data=df)
        plt.savefig(path)

    @classmethod
    def output_animation(
        cls, episode, snap_shots, section_map, env_size, path, interval=200
    ):
        """ シミュレーション結果のアニメーション出力 """
        plt.clf()
        fig = plt.figure()
        ax = plt.axes()

        margin = math.ceil(env_size * 0.05)
        plt.xlim(-margin, env_size + margin)
        plt.ylim(-margin, env_size + margin)

        artists = []
        for section in section_map:
            fill_color = (
                "#FFFCCC" if section["attribute"] == "public" else "#CCFFFC"
            )

            rect = patches.Rectangle(
                xy=(section["x_min"], section["y_min"]),
                width=section["x_max"] - section["x_min"],
                height=section["y_max"] - section["y_min"],
                ec="lightgrey",
                fc=fill_color,
                alpha=0.3,
            )
            ax.add_patch(rect)

        plt.axis("scaled")
        ax.set_aspect("equal")

        with tqdm(snap_shots) as pbar:
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
                        (df["status"] == Status.INFECTED) & (df["is_patient"]),
                        "color",
                    ] = "darkgrey"
                    df.loc[
                        df["status"] == Status.RECOVERED, "color"
                    ] = "lightgreen"

                    artist = ax.scatter(df["x"], df["y"], s=10, c=df["color"])
                    title = ax.text(
                        -margin,
                        -margin,
                        "Day:{} Hour:{}".format(d_idx + 1, h_idx + 7),
                        fontsize="small",
                    )
                    artists.append([artist, title])

        anim = animation.ArtistAnimation(fig, artists, interval=interval)
        anim.save(path, writer="ffmpeg")
