"""
エージェントの状態定義
"""
from enum import Enum


class Status(Enum):
    # 未感染
    SUSCEPTABLE = "Susceptable"
    # 感染（潜伏）
    EXPOSED = "Exposed"
    # 感染（発症）
    INFECTED = "Infected"
    # 回復
    RECOVERED = "Recovered"
