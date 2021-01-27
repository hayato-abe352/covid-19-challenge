"""
シミュレーションデータの記録クラス
"""
import pandas as pd

from Environment.Government import (
    QLearningAction,
    QLearningInfectionStatus,
    QLearningHospitalStatus,
    QLearningEconomyStatus,
    QLearningMaskDistributionStatus,
)


class Recorder:
    def __init__(self):
        # シミュレーションのデータ記録
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

        # Q-Learning の学習状況記録
        self.q_score = pd.DataFrame(columns=["episode", "avg_score"])
        self.q_score = self.q_score.astype(
            {"episode": int, "avg_score": float}
        )

        # Q-Learning の状態を記録
        self.q_state = pd.DataFrame(columns=["episode", "day", "state"])
        self.q_state = self.q_state.astype(
            {"episode": int, "day": int, "state": str}
        )

        # Q-Learning のアクションを記録
        self.actions = {a.value: a.name for a in QLearningAction}
        self.q_action = pd.DataFrame(columns=["episode", "day", "action"])
        self.q_action = self.q_action.astype(
            {"episode": int, "day": int, "action": str}
        )

        # Q-Learning の状態遷移を記録
        self.q_history = pd.DataFrame(
            columns=["prev_state", "next_state", "action"]
        )
        self.q_history = self.q_history.astype(
            {"prev_state": str, "next_state": str, "action": str}
        )

        # 状態の略式コード定義
        self._infection_state = {
            QLearningInfectionStatus.BEFORE_PANDEMIC.name: "BP",
            QLearningInfectionStatus.SPREAD.name: "SP",
            QLearningInfectionStatus.EPIDEMIC.name: "EP",
            QLearningInfectionStatus.CONVERGENCE.name: "CV",
            QLearningInfectionStatus.AFTER_PANDEMIC.name: "AP",
        }
        self._hospital_state = {
            QLearningHospitalStatus.NORMAL.name: "N",
            QLearningHospitalStatus.TIGHT.name: "T",
            QLearningHospitalStatus.VERY_TIGHT.name: "VT",
        }
        self._economy_state = {
            QLearningEconomyStatus.NORMAL.name: "N",
            QLearningEconomyStatus.RECESSION.name: "R",
            QLearningEconomyStatus.CRISIS.name: "C",
        }
        self._mask_state = {
            QLearningMaskDistributionStatus.DISTRIBUTED.name: "D",
            QLearningMaskDistributionStatus.UNDISTRIBUTED.name: "UD",
        }
        self._action = ["NOP", "UPH", "DWH", "MSK"]

    def load_q_score_csv(self, path):
        """ Q-Score を記録した csv ファイルを読み込む """
        self.q_score = pd.read_csv(path)

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
            "patients": patients,
        }
        self.dataframe = self.dataframe.append(data, ignore_index=True)

    def save_q_score(self, episode, score):
        """ Q-スコアを記録します """
        data = {"episode": episode, "avg_score": score}
        self.q_score = self.q_score.append(data, ignore_index=True)

    def save_q_state(self, episode, day, state):
        """ Q-Learning の状態を記録します """
        s = ".".join([s.name for s in state])
        data = {"episode": episode, "day": day, "state": s}
        self.q_state = self.q_state.append(data, ignore_index=True)

    def save_q_action(self, episode, day, action):
        """ Q-Leanring のアクションを記録します """
        a = self.actions[action]
        data = {"episode": episode, "day": day, "action": a}
        self.q_action = self.q_action.append(data, ignore_index=True)

    def save_q_history(self, prev_s, next_s, a_val):
        """ Q-Learning の状態変化履歴を記録します """
        prev_s = self._get_state_code(prev_s)
        next_s = self._get_state_code(next_s) if next_s != "end" else "end"
        action = self._action[a_val] if a_val is not None else "*"
        data = {
            "prev_state": prev_s,
            "next_state": next_s,
            "action": action,
        }
        self.q_history = self.q_history.append(data, ignore_index=True)

    def _get_state_code(self, state):
        """ 状態を示す略式コードを取得 """
        if state is None:
            return "start"

        inf_s = state[0].name
        inf_cd = self._infection_state[inf_s]

        hsp_s = state[1].name
        hsp_cd = self._hospital_state[hsp_s]

        eco_s = state[2].name
        eco_cd = self._economy_state[eco_s]

        msk_s = state[3].name
        msk_cd = self._mask_state[msk_s]

        return ".".join([inf_cd, hsp_cd, eco_cd, msk_cd])

    def get_dataframe(self) -> pd.DataFrame:
        """ データフレームを取得します """
        return self.dataframe

    def get_q_score(self) -> pd.DataFrame:
        """ Q-スコアのデータフレームを取得します """
        return self.q_score

    def get_q_state(self) -> pd.DataFrame:
        """ Q-Learning の状態に関するデータフレームを取得します """
        return self.q_state

    def get_q_action(self) -> pd.DataFrame:
        """ Q-Learning のアクションに関するデータフレームを取得します """
        return self.q_action

    def get_q_history(self) -> pd.DataFrame:
        """ Q-Learning の状態変化履歴を取得します """
        dataframe = self.q_history.copy()
        grouped = (
            dataframe.groupby(["prev_state", "next_state", "action"])
            .size()
            .reset_index()
        )
        grouped = grouped.rename(columns={0: "count"})
        state_count = dataframe.groupby("prev_state").size().reset_index()
        state_count = state_count.rename(columns={0: "s_count"})
        result = pd.merge(grouped, state_count, on="prev_state")
        result["transition_prob"] = result["count"] / result["s_count"]
        return result[
            ["prev_state", "next_state", "action", "transition_prob"]
        ]

    def set_dataframe(self, df: pd.DataFrame):
        """ データフレームをセットします """
        self.dataframe = df
