"""
区画定義
"""


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
