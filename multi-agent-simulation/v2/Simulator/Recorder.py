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
                "susceptable",
                "exposed",
                "infected",
                "recovered",
            ]
        )
        self.dataframe = self.dataframe.astype(
            {
                "episode": int,
                "day": int,
                "city": str,
                "susceptable": int,
                "exposed": int,
                "infected": int,
                "recovered": int,
            }
        )

    def add_record(
        self, episode: int, day: int, city: str, s: int, e: int, i: int, r: int
    ):
        """ レコードを追加します """
        data = {
            "episode": episode,
            "day": day,
            "city": city,
            "susceptable": s,
            "exposed": e,
            "infected": i,
            "recovered": r,
        }
        self.dataframe = self.dataframe.append(data, ignore_index=True)

    def get_dataframe(self) -> pd.DataFrame:
        """ データフレームを取得します """
        return self.dataframe
