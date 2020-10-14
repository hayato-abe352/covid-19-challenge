"""
シミュレーション結果の可視化クラス
"""
import os

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from loguru import logger


class Visualizer:
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
        pass
