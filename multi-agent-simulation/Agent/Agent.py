"""
エージェント定義
"""
import random

from Agent.Status import Status


class Agent:
    def __init__(self, id, x, y, home, status, infection_model):
        # 個体識別番号
        self.id = id

        # エージェントの位置
        self.x = x
        self.y = y
        self.next_x = None
        self.next_y = None

        # エージェントのホーム区画
        self.home_section = home
        # エージェントの現在の区画
        self.current_section = home
        self.next_section = None

        # エージェントの家族 (同じhomeを持つAgent)
        self.family = []

        # エージェントの感染確率( S => I の確率)
        self.infection_prob = infection_model.infection_prob
        # エージェントの回復確率( I => R の確率)
        self.recovery_prob = infection_model.recovery_prob
        # エージェントの抗体獲得確率( I => R 後に R => S が起きる確率)
        self.antibody_acquisition_prob = (
            infection_model.antibody_acquisition_prob
        )
        # 自覚症状が生じる確率
        self.subjective_symptoms_prob = (
            infection_model.subjective_symptoms_prob
        )

        # エージェントの状態
        self.status = status
        self.next_status = None

        # 自覚症状の有無
        self.has_subjective_symptoms = False

        # 感染してからの経過日数
        self.infection_duration = 0
        # 病院の収容状況
        self.is_in_hospital = False

        # 自身の周囲に存在するエージェント
        self.neighbor_agents = []

    def decide_action(
        self, x_min, x_max, y_min, y_max, public_sections, pattern, hour
    ):
        """ 次のエージェント位置を決定 """
        if pattern == "freeze":
            self._stay_here()
            return

        if self.status == Status.INFECTED and self.has_subjective_symptoms:
            # 自覚症状ありの感染者の場合、自宅に留まる
            self._stay_home()
            return

        if self.is_in_hospital:
            # Hospitalに収容されている場合、自宅に留まる
            self._stay_home()
            return

        # [その場に留まる]/[別の公共区画に移動する] をランダムに選択
        action = random.choice(["stay", "move"])
        if action == "home":
            self._stay_home()
        elif action == "stay":
            self._stay_here()
        else:
            self._move_other_section(public_sections)
    
    def go_back_home(self):
        """ エージェントを自宅に帰す """
        self._stay_home()
        self.do_action()

    def _stay_home(self):
        """ [行動定義関数] ステイホーム """
        home = self.home_section
        self.next_x, self.next_y = self._get_position_in_section(home)
        self.next_section = self.home_section

    def _stay_here(self):
        """ [行動定義関数] その区画に留まる """
        current_sec = self.current_section
        self.next_x, self.next_y = self._get_position_in_section(current_sec)
        self.next_section = self.current_section

    def _move_other_section(self, public_sections):
        """ [行動定義関数] 別の区画に移動する """
        # 公共区画の中からランダムに１つ選択 (現在の区画は除外)
        next_sec = random.choice(
            [sec for sec in public_sections if sec != self.current_section]
        )
        self.next_x, self.next_y = self._get_position_in_section(next_sec)
        self.next_section = next_sec

    def _get_position_in_section(self, section):
        """ [補助関数] セクション内のランダムな位置を取得 """
        x = random.uniform(section["x_min"], section["x_max"])
        y = random.uniform(section["y_min"], section["y_max"])
        return x, y

    def do_action(self):
        """ エージェントの位置を更新 """
        self.x = self.next_x
        self.y = self.next_y
        self.current_section = self.next_section

    def decide_next_status(self):
        """ 次のエージェント状態を決定 """
        if self.status == Status.RECOVERED:
            # 回復者は再感染しない想定
            self.next_status = Status.RECOVERED

        elif self.status == Status.INFECTED:
            # 感染者は一定確率で回復する想定
            if random.random() <= self.recovery_prob:
                if random.random() <= self.antibody_acquisition_prob:
                    # 抗体獲得に成功した場合
                    self.next_status = Status.RECOVERED
                else:
                    # 抗体獲得に失敗した場合
                    self.next_status = Status.SUSCEPTABLE
            else:
                self.next_status = Status.INFECTED

        elif self.status == Status.SUSCEPTABLE:
            # 1日に接触した感染者に比例する確率で感染状態に移行
            # (Hospitalに収容されている感染者は除外)
            infected_agents = [
                agent
                for agent in self.neighbor_agents
                if agent.status == Status.INFECTED and not agent.is_in_hospital
            ]

            # len(infected_agents)人の感染者と接触したとき、一度でも感染する確率
            infection_prob = 1 - (
                (1 - self.infection_prob) ** len(infected_agents)
            )

            if random.random() <= infection_prob:
                self.next_status = Status.INFECTED
            else:
                self.next_status = Status.SUSCEPTABLE

            self.neighbor_agents = []

    def update_status(self):
        """ エージェントの状態を更新 """
        # 感染時の自覚症状発生判定
        if (
            self.status == Status.SUSCEPTABLE
            and self.next_status == Status.INFECTED
        ):
            # 感染状態に移行するとき、一定確率で自覚症状を付与
            if random.random() <= self.subjective_symptoms_prob:
                self.has_subjective_symptoms = True
            else:
                self.has_subjective_symptoms = False
        elif self.status == Status.RECOVERED:
            self.has_subjective_symptoms = False

        # 感染中の経過日数インクリメント
        if (
            self.status == Status.INFECTED
            and self.next_status == Status.INFECTED
        ):
            self.infection_duration += 1

        # 状態変化を実行
        self.status = self.next_status
