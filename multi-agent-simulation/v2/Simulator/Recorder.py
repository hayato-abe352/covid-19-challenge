"""
シミュレーションデータの記録クラス
"""
import pandas as pd


class Recorder:
    def __init__(self):
        self.dataframe = pd.DataFrame(
            columns=[
                "episode",
                "day",
                "city",
                "outflow",
                "susceptable",
                "exposed",
                "infected",
                "recovered",
                "total",
            ]
        )
        self.dataframe = self.dataframe.astype(
            {
                "episode": int,
                "day": int,
                "city": str,
                "outflow": int,
                "susceptable": int,
                "exposed": int,
                "infected": int,
                "recovered": int,
                "total": int,
            }
        )

    def add_record(
        self,
        episode: int,
        day: int,
        city: str,
        outflow: int,
        s: int,
        e: int,
        i: int,
        r: int,
    ):
        """ レコードを追加します """
        data = {
            "episode": episode,
            "day": day,
            "city": city,
            "outflow": outflow,
            "susceptable": s,
            "exposed": e,
            "infected": i,
            "recovered": r,
            "total": s + e + i + r,
        }
        self.dataframe = self.dataframe.append(data, ignore_index=True)

    def get_dataframe(self) -> pd.DataFrame:
        """ データフレームを取得します """
        return self.dataframe
