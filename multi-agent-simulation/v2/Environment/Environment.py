"""
環境定義
"""
import pandas as pd

from Agent.Status import Status


class Environment:
    def __init__(self):
        pass

    def init_environment(self):
        """ 環境を初期化 """
        pass

    def init_agents(selg):
        """ エージェントを初期化 """
        pass

    def count_agent(self, status: Status) -> int:
        """ 該当ステータスのエージェント数をカウント """
        pass

    def get_snap_shot(self) -> pd.DataFrame:
        """ 現時点のスナップショットを取得 """
        pass
