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
                "avg_mental",
                "finance",
                "tax_revenue",
                "avg_income",
                "susceptable",
                "exposed",
                "infected",
                "recovered",
                "death",
                "total",
                "patients",
            ]
        )
        self.dataframe = self.dataframe.astype(
            {
                "episode": int,
                "day": int,
                "city": str,
                "outflow": int,
                "avg_mental": float,
                "finance": float,
                "tax_revenue": float,
                "avg_income": float,
                "susceptable": int,
                "exposed": int,
                "infected": int,
                "recovered": int,
                "death": int,
                "total": int,
                "patients": int,
            }
        )

    def add_record(
        self,
        episode: int,
        day: int,
        city: str,
        outflow: int,
        avg_mental: float,
        finance: float,
        tax_revenue: float,
        avg_income: float,
        patients: int,
        s: int,
        e: int,
        i: int,
        r: int,
        d: int,
    ):
        """ レコードを追加します """
        data = {
            "episode": episode,
            "day": day,
            "city": city,
            "outflow": outflow,
            "avg_mental": avg_mental,
            "finance": finance,
            "tax_revenue": tax_revenue,
            "avg_income": avg_income,
            "susceptable": s,
            "exposed": e,
            "infected": i,
            "recovered": r,
            "death": d,
            "living": s + e + i + r,
            "total": s + e + i + r + d,
            "patients": patients
        }
        self.dataframe = self.dataframe.append(data, ignore_index=True)

    def get_dataframe(self) -> pd.DataFrame:
        """ データフレームを取得します """
        return self.dataframe

    def set_dataframe(self, df: pd.DataFrame):
        """ データフレームをセットします """
        self.dataframe = df
