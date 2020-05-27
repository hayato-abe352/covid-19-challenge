"""
エージェントの状態定義
"""
from enum import Enum


# エージェントの状態定義
class Status(Enum):
    # 未感染
    SUSCEPTABLE = "Susceptable"
    # 感染
    INFECTED = "Infected"
    # 回復
    RECOVERED = "Recovered"
