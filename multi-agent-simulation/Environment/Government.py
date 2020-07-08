"""
政府クラス
"""


class Government:
    def __init__(self, agent_num):
        # 国民の総人口
        self.agent_num = agent_num

        # 政策を決定するための参考値として、過去の感染者の推移を記録する
        self.infected_history = []

    def add_history(self, i_num):
        self.infected_history.append(i_num)

    def decide_issue_emergency(self):
        """ 非常事態宣言の発令を判断 """
        if len(self.infected_history) < 2:
            return False

        today = self.infected_history[-1]
        yesterday = self.infected_history[-2]

        thresh = self.agent_num * 0.10
        if today >= thresh and yesterday >= thresh:
            # 以下の条件のとき、非常事態を宣言
            #   - 1. 2日連続で感染者(発症者)が国民の総人口の 10% 以上に達したとき
            return True
        else:
            # 非常事態宣言の発令は見送り
            return False

    def decide_cancel_emergency(self):
        """ 非常事態宣言の解除を判断 """
        if len(self.infected_history) < 3:
            return False

        # 非常事態宣言を発令中 => 継続するかを判断
        thresh = self.agent_num * 0.10
        if (
            self.infected_history[-1] <= thresh
            and self.infected_history[-2] <= thresh
            and self.infected_history[-3] <= thresh
        ):
            # 以下の条件のとき、非常事態宣言を解除
            #   - 1. 3日連続で感染者(発症者)が国民の総人口の 10% 以下まで低下したとき
            return True
        else:
            # 非常事態宣言は継続
            return False
