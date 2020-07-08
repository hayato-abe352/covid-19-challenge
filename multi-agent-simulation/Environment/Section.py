"""
区画定義
"""
from enum import Enum


class SeverityLevel(Enum):
    # 必須 (非常事態宣言下でもopen)
    HIGH = 0
    # 非必須 (非常事態宣言下ではclose)
    LOW = 1


class Section:
    def __init__(self, address, x_min, x_max, y_min, y_max, attribute):
        # 住所情報
        self.address = address
        # x座標の最低値
        self.x_min = x_min
        # x座標の最大値
        self.x_max = x_max
        # y座標の最低値
        self.y_min = y_min
        # y座標の最大値
        self.y_max = y_max
        # 属性値
        self.attribute = attribute
        # 重要度(attributeがpublicの場合、この区画が社会にとってどれだけ重要かを示す値)
        self.severity = None
        # Agent が区画に入れるかどうか
        self.is_open = True
