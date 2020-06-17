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

    def decide_emergency_declaration(self, is_emergency):
        """ 非常事態宣言の発令・継続を判断 """
        if len(self.infected_history) < 2:
            return False
        
        today = self.infected_history[0]
        yesterday = self.infected_history[1]

        if is_emergency:
            # 非常事態宣言を発令中 => 継続するかを判断
            if (today - yesterday) / yesterday <= -0.05:
                # 以下の条件のとき、非常事態宣言を解除
                #   - 1. 新規感染者の(発症者)の前日比が -5% 以下の時
                return False
            else:
                # 非常事態宣言は継続
                return True
        else:
            # 非常事態宣言外 => 発令するかを判断
            if (
                self.infected_history >= (self.agent_num * 0.05)
                or (today - yesterday) / yesterday >= 0.02
            ):
                # 以下の条件のとき、非常事態を宣言
                #   - 1. 感染者(発症者)が国民の総人口の 5% 以上に達したとき
                #   - 2. 新規感染者(発症者)の前日比が 2% 以上のとき
                return True
            else:
                # 非常事態宣言の発令は見送り
                return False

