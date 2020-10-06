"""
エージェント定義
"""
import random

from Agent.Status import Status


class Agent:
    def __init__(self, id, hometown, status: Status, infection_model):
        # 個体識別番号
        self.id = id

        # 故郷と現在地
        self.hometown = hometown
        self.current_location = None

        # ステータス
        self.status: Status = status
        self.next_status: Status = None

        # 感染症モデル
        self.infection_model = infection_model

    def decide_next_status(self):
        """ エージェントの次ステータスを決定 """
        pass

    def update_status(self):
        """ エージェントのステータスを更新 """
        pass
