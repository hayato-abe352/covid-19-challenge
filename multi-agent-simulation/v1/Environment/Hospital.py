"""
Hospital (感染者の隔離・治療オブジェクト) の定義
"""
from Agent import Status


class Hospital:
    def __init__(self, capacity):
        # キャパシティ
        self.capacity = capacity

        # 格納中のエージェント
        self.patients = []

    def accommodate(self, agent):
        """ エージェントを病院に収容 """
        # 入院処理
        self.patients.append(agent)
        agent.is_in_hospital = True

    def is_accommodatable(self):
        """ 新たな患者を収容可能かどうか """
        return self.count_patients() < self.capacity

    def count_patients(self):
        """ 患者数をカウント """
        return len(self.patients)

    def has_patient(self, agent):
        """ agentが収容されているかどうか """
        return agent in self.patients

    def leave_patients(self):
        """ 回復した患者の解放(退院) """
        new_patients = []
        for agent in self.patients:
            if agent.status == Status.INFECTED:
                new_patients.append(agent)
            else:
                # 退院処理
                agent.is_in_hospital = False
        self.patients = new_patients
