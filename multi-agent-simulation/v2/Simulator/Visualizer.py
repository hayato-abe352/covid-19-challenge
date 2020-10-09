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
        accumulate=False,
        exposed=False,
        title: str = None,
    ):
        """ 感染者の推移に関するグラフを出力 """
        filename = os.path.basename(path)
        logger.info("感染者推移グラフ {} を出力しています...".format(filename))

        data = dataframe.copy()
        if exposed:
            data = cls._sum_exposed_to_infected(data)
        if accumulate:
            data = cls._accumulate(data)

        sns.lineplot(data=data, x="day", y="infected", hue="city")
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
    def _accumulate(cls, data: pd.DataFrame) -> pd.DataFrame:
        """ 感染者数を累積値に変更 """
        result = pd.DataFrame()
        for (city, episode), group in data.groupby(["city", "episode"]):
            group = group.sort_values("day")
            infected = group["infected"]
            accumulated = infected.cumsum()
            group["infected"] = accumulated
            result = pd.concat([result, group], ignore_index=True)
        return result
