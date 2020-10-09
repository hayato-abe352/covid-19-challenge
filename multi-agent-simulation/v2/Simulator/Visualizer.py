"""
シミュレーション結果の可視化クラス
"""
import pandas as pd
from loguru import logger
import os

import matplotlib.pyplot as plt
import seaborn as sns


class Visualizer:
    @classmethod
    def output_infected_chart(
        cls,
        path: str,
        dataframe: pd.DataFrame,
        exposed=False,
        percentage=False,
        title: str = None,
    ):
        """ 感染者の推移に関するグラフを出力 """
        filename = os.path.basename(path)
        logger.info("感染者推移グラフ {} を出力しています...".format(filename))

        data = dataframe.copy()
        if exposed:
            data = cls._sum_exposed_to_infected(data)
        if percentage:
            data = cls._percentage(data)
            plt.ylim([0.0, 1.0])

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
    def _percentage(cls, data: pd.DataFrame) -> pd.DataFrame:
        """ infected 数をパーセンテージに切り替えます """
        data["total"] = (
            data["susceptable"]
            + data["exposed"]
            + data["infected"]
            + data["recovered"]
        )
        data["infected"] = data["infected"] / data["total"]
        return data

    @classmethod
    def output_population_chart(
        cls, path: str, dataframe: pd.DataFrame, title: str = None
    ):
        """ 各都市の滞在者人口グラフを出力 """
        filename = os.path.basename(path)
        logger.info("滞在者人口推移グラフ {} を出力しています...".format(filename))

        data = dataframe.copy()
        data["population"] = (
            data["susceptable"]
            + data["exposed"]
            + data["infected"]
            + data["recovered"]
        )

        sns.lineplot(data=data, x="day", y="population", hue="city", ci=None)
        if title is not None:
            plt.title(title)
        plt.savefig(path)
        plt.clf()

        logger.info("滞在者人口推移グラフ {} を出力しました。".format(filename))

    @classmethod
    def output_outflow_chart(
        cls, path: str, dataframe: pd.DataFrame, title: str = None
    ):
        """ 流出者グラフを出力 """
        filename = os.path.basename(path)
        logger.info("流出者推移グラフ {} を出力しています...".format(filename))

        sns.lineplot(data=dataframe, x="day", y="outflow", hue="city", ci=None)
        if title is not None:
            plt.title(title)
        plt.savefig(path)
        plt.clf()

        logger.info("流出者推移グラフ {} を出力しました。".format(filename))
        pass
