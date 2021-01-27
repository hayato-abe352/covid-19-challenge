"""
シミュレーション結果の可視化クラス
"""
import os

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from loguru import logger
from graphviz import Digraph


class Visualizer:
    @classmethod
    def output_seir_chart(
        cls,
        path: str,
        dataframe: pd.DataFrame,
        env_name: str = None,
        title: str = None,
    ):
        """ SEIR グラフを出力 """
        filename = os.path.basename(path)
        logger.info("SEIRグラフ {} を出力しています...".format(filename))

        data = dataframe.copy()
        if env_name is not None:
            data = data[data["city"] == env_name]

        seir_data = pd.DataFrame(columns=["day", "count", "type"])
        for status_type in [
            "susceptable",
            "exposed",
            "infected",
            "recovered",
            "death",
        ]:
            record = pd.DataFrame(columns=["day", "count", "type"])
            record["day"] = data["day"]
            record["count"] = data[status_type]
            record["type"] = status_type
            seir_data = pd.concat([seir_data, record], ignore_index=True)

        seir_data = seir_data.astype({"day": int, "count": int, "type": str})
        sns.lineplot(data=seir_data, x="day", y="count", hue="type")

        if title is not None:
            plt.title(title)
        plt.savefig(path)
        plt.clf()

        logger.info("SEIRグラフ {} を出力しました".format(filename))

    @classmethod
    def output_infected_chart(
        cls,
        path: str,
        dataframe: pd.DataFrame,
        exposed=False,
        total=False,
        percentage=False,
        title: str = None,
    ):
        """ 感染者の推移に関するグラフを出力 """
        filename = os.path.basename(path)
        logger.info("感染者推移グラフ {} を出力しています...".format(filename))

        data = dataframe.copy()
        if exposed:
            data = cls._sum_exposed_to_infected(data)
        if total:
            data = cls._aggregate_infected(data)
        if percentage:
            data = cls._percentage(data)
            plt.ylim([0.0, 1.0])

        if total:
            sns.lineplot(data=data, x="day", y="infected")
        else:
            sns.lineplot(data=data, x="day", y="infected", hue="city", ci=None)

        if title is not None:
            plt.title(title)
        plt.savefig(path)
        plt.clf()
        logger.info("感染者推移グラフ {} を出力しました。".format(filename))

    @classmethod
    def output_patients_chart(
        cls,
        path: str,
        dataframe: pd.DataFrame,
        title: str = None,
    ):
        """ 患者数の推移に関するグラフを出力 """
        filename = os.path.basename(path)
        logger.info("患者数推移グラフ {} を出力しています...".format(filename))

        sns.lineplot(
            data=dataframe, x="day", y="patients", hue="city", ci=None
        )

        if title is not None:
            plt.title(title)
        plt.savefig(path)
        plt.clf()

        logger.info("患者数推移グラフ {} を出力しました。".format(filename))

    @classmethod
    def _sum_exposed_to_infected(cls, data: pd.DataFrame) -> pd.DataFrame:
        """ 潜伏者を発症者数に合算 """
        data["infected"] = data["infected"] + data["exposed"]
        return data

    @classmethod
    def _aggregate_infected(cls, data: pd.DataFrame) -> pd.DataFrame:
        """ 感染者数を合計します """
        grouped = data.groupby(["episode", "day"]).sum().reset_index()
        return grouped

    @classmethod
    def _percentage(cls, data: pd.DataFrame) -> pd.DataFrame:
        """ infected 数をパーセンテージに切り替えます """
        data["infected"] = data["infected"] / data["total"]
        return data

    @classmethod
    def output_population_chart(
        cls,
        path: str,
        dataframe: pd.DataFrame,
        mode: str = "total",
        title: str = None,
    ):
        """ 各都市の滞在者人口グラフを出力 """
        filename = os.path.basename(path)
        logger.info("人口推移グラフ {} を出力しています...".format(filename))

        data = dataframe.copy()
        data["population"] = data["total"]
        if mode == "living":
            data["population"] = data["living"]
        if mode == "death":
            data["population"] = data["death"]

        sns.lineplot(data=data, x="day", y="population", hue="city", ci=None)
        if title is not None:
            plt.title(title)
        plt.savefig(path)
        plt.clf()

        logger.info("人口推移グラフ {} を出力しました。".format(filename))

    @classmethod
    def output_outflow_chart(
        cls,
        path: str,
        dataframe: pd.DataFrame,
        total=False,
        title: str = None,
    ):
        """ 流出者グラフを出力 """
        filename = os.path.basename(path)
        logger.info("流出者推移グラフ {} を出力しています...".format(filename))

        data = dataframe.copy()
        if total:
            grouped = data.groupby(["episode", "day"]).sum().reset_index()
            sns.lineplot(data=grouped, x="day", y="outflow")
        else:
            sns.lineplot(data=data, x="day", y="outflow", hue="city", ci=None)

        if title is not None:
            plt.title(title)
        plt.savefig(path)
        plt.clf()

        logger.info("流出者推移グラフ {} を出力しました。".format(filename))

    @classmethod
    def output_mental_strength_chart(
        cls, path: str, dataframe: pd.DataFrame, title: str = None
    ):
        """ メンタル値の変化をプロット """
        filename = os.path.basename(path)
        logger.info("平均メンタル値の推移グラフ {} を出力しています...".format(filename))

        sns.lineplot(
            data=dataframe, x="day", y="avg_mental", hue="city", ci=None
        )
        plt.ylim(-1.0, 1.0)

        if title is not None:
            plt.title(title)
        plt.savefig(path)
        plt.clf()

        logger.info("平均メンタル値の推移グラフ {} を出力しました".format(filename))

    @classmethod
    def output_finance_chart(
        cls, path: str, dataframe: pd.DataFrame, title: str = None
    ):
        """ 各 env の経済力の変化をプロット """
        filename = os.path.basename(path)
        logger.info("経済力の推移グラフ {} を出力しています...".format(filename))

        sns.lineplot(data=dataframe, x="day", y="finance", hue="city", ci=None)

        if title is not None:
            plt.title(title)
        plt.savefig(path)
        plt.clf()

        logger.info("経済力の推移グラフ {} を出力しました".format(filename))

    @classmethod
    def output_tax_revenue_chart(
        cls, path: str, dataframe: pd.DataFrame, title: str = None
    ):
        """ 各 env の税収をプロット """
        filename = os.path.basename(path)
        logger.info("税収の推移グラフ {} を出力しています...".format(filename))

        sns.lineplot(
            data=dataframe, x="day", y="tax_revenue", hue="city", ci=None
        )

        if title is not None:
            plt.title(title)
        plt.savefig(path)
        plt.clf()

        logger.info("税収の推移グラフ {} を出力しました".format(filename))

    @classmethod
    def output_income_chart(
        cls, path: str, dataframe: pd.DataFrame, title: str = None
    ):
        """ 平均所得の変化をプロット """
        filename = os.path.basename(path)
        logger.info("平均所得の推移グラフ {} を出力しています...".format(filename))

        sns.lineplot(
            data=dataframe, x="day", y="avg_income", hue="city", ci=None
        )

        if title is not None:
            plt.title(title)
        plt.savefig(path)
        plt.clf()

        logger.info("平均所得の推移グラフ {} を出力しました".format(filename))

    @classmethod
    def output_q_score(cls, path: str, dataframe: pd.DataFrame):
        """ Q-スコアを出力 """
        filename = os.path.basename(path)
        logger.info("Q-スコアの推移グラフ {} を出力しています...".format(filename))

        sns.lineplot(data=dataframe, x="episode", y="avg_score")
        plt.title("Q-Score")
        plt.savefig(path)
        plt.clf()

        logger.info("Q-スコアの推移グラフ {} を出力しました。".format(filename))

    @classmethod
    def output_q_history(cls, path: str, dataframe: pd.DataFrame):
        """ 状態変化図を出力 """
        output_path, ext = os.path.splitext(path)
        G = Digraph(format=ext.replace(".", ""))
        G.attr("node", shape="square", style="filled")
        for _, row in dataframe.iterrows():
            before = row["prev_state"]
            after = row["next_state"]
            label = "{}/{:.1%}".format(row["action"], row["transition_prob"])
            G.edge(before, after, label=label)
        G.node("start", shape="circle", color="pink")
        G.node("end", shape="circle", color="pink")
        G.render(output_path)
