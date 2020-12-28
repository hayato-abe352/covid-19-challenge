"""
政府クラス
（ Q-Learning アルゴリズムによる意思決定クラス）
"""
from __future__ import annotations

import copy
import json
import os
import uuid
from enum import Enum

import numpy as np
from loguru import logger

MODEL_OUTPUT_PATH = "output/models/ql-model-{model_id}-{episode}.json"


class Government:
    def __init__(self, env):
        # Environment
        self.env = env

        # 現在の状態を判定するためのデータ
        self.current_data = []
        # 過去の状態を判定するためのデータ
        self.past_data = []
        # 死亡者数
        self.death_data = []
        # 観測周期
        self.period = 5

        # 感染拡大アラート (一度感染が広がると True になるフラグ)
        self.alert = False

        # アクションの実行可能判定用
        self.execution_status = None
        self.init_execution_status()

        # 状態判定の閾値
        self.explosion_thresh = 1.2
        self.spread_thresh = 1.05
        self.convergence_thresh = 0.95

        # スコア基準値
        self.impossible_action_score = -99999
        self.infected_score = -100
        self.death_score = -1000
        self.economy_score = {
            "normal": 0,
            "recession": -1000,
            "crisis": -10000,
        }

    def reset_government(self):
        """ Government クラスの管理状態を初期化 """
        self.current_data = []
        self.past_data = []
        self.death_data = []
        self.init_execution_status()
        self.alert = False
        logger.info("Government クラスを初期化しました。")

    def init_execution_status(self):
        """ アクション実行状況の初期値を取得 """
        init_exe_status = {"abe_no_mask": False}
        self.execution_status = init_exe_status

    def save_data(self, infected_num, death_num):
        """ 感染者数を記録 """
        self.current_data.append(infected_num)
        if len(self.current_data) > self.period:
            self.past_data.append(self.current_data[0])
            self.current_data.pop(0)
        if len(self.past_data) > self.period:
            self.past_data.pop(0)

        self.death_data.append(death_num)
        if len(self.death_data) > self.period:
            self.death_data.pop(0)

    def determine_state(self):
        """ 現在の状態を観測 """
        infection_s = self._decide_infection_status()
        hospital_s = self._decide_hospital_status()
        economy_s = self._decide_economy_status()
        mask_dist_s = self._decide_mask_distribution_status()
        return (infection_s, hospital_s, economy_s, mask_dist_s)

    def _decide_infection_status(self):
        """ 感染拡大のステータスを決定 """
        if not self.past_data or not self.current_data:
            return QLearningInfectionStatus.BEFORE_PANDEMIC

        past_avg = sum(self.past_data) / len(self.past_data)
        current_avg = sum(self.current_data) / len(self.current_data)

        # 感染症と認知される閾値を算出
        population = self.env.agent_num
        rate = self.env.infection_model.thresh
        thresh = int(population * rate)

        # 昨日・今日ともに感染症と認知されていない場合
        if past_avg < thresh and current_avg < thresh:
            if not self.alert:
                # 感染拡大前の平常状態
                return QLearningInfectionStatus.BEFORE_PANDEMIC
            else:
                # 感染拡大後の平常状態
                return QLearningInfectionStatus.AFTER_PANDEMIC
        self.alert = True

        increase_rate = current_avg / past_avg

        # 感染者が急激に増加傾向の場合 => 感染爆発
        if self.explosion_thresh < increase_rate:
            return QLearningInfectionStatus.EXPLOSION

        # 感染者が増加傾向の場合 => 感染拡大
        if self.spread_thresh < increase_rate:
            return QLearningInfectionStatus.SPREAD

        # 感染者が減少傾向の場合 => 感染収束
        if increase_rate < self.convergence_thresh:
            return QLearningInfectionStatus.CONVERGENCE

        # 感染者の増加傾向が緩やかな場合 => 蔓延
        return QLearningInfectionStatus.PANDEMIC

    def _decide_hospital_status(self):
        """ 病院ステータスを決定 """
        hospital_occupancy = self.env.get_hospital_occupancy()
        if hospital_occupancy >= 0.8:
            return QLearningHospitalStatus.TIGHT
        return QLearningHospitalStatus.NORMAL

    def _decide_economy_status(self):
        """ 経済ステータスを決定 """
        finance = self.env.get_finance()
        baseline = self.env.get_finance_baseline()
        rate = finance / baseline

        if rate > 0.75:
            return QLearningEconomyStatus.NORMAL

        if rate > 0.5:
            return QLearningEconomyStatus.RECESSION

        return QLearningEconomyStatus.CRISIS

    def _decide_mask_distribution_status(self):
        """ マスクの配布状態を決定 """
        executed = self.execution_status["abe_no_mask"]
        if executed:
            return QLearningMaskDistributionStatus.DISTRIBUTED
        return QLearningMaskDistributionStatus.UNDISTRIBUTED

    def apply_action(self, action: int):
        """ 政策 (アクション) を適用 """
        if action == QLearningAction.NOP.value:
            # 何もしない
            return

        if action == QLearningAction.UP_HOSPITAL_CAPACITY.value:
            # 病院のキャパシティを +10
            self.env.change_hospital_capacity(+10)

        if action == QLearningAction.DOWN_HOSPITAL_CAPACITY.value:
            # 病院のキャパシティを -10
            self.env.change_hospital_capacity(-10)

        if action == QLearningAction.ABE_NO_MASK.value:
            # 感染確率を半減
            for agent in self.env.get_agents():
                agent.set_mask_effect(0.5)
            # 実施状況を記録（アベノマスク政策は episode 中に１回のみ発動可能）
            self.execution_status["abe_no_mask"] = True

    def is_possible_action(self, action: int):
        """ 政策 (アクション) が実行可能かを判定 """
        if action == QLearningAction.ABE_NO_MASK.value:
            # 未実行であれば実行可能
            executed = self.execution_status["abe_no_mask"]
            return not executed
        return True

    def compute_reward(self):
        """ 報酬を計算 """
        if not self.current_data or not self.death_data:
            return 0

        # 感染者数によるスコア計算
        avg_infected = sum(self.current_data) / len(self.current_data)
        i_score = avg_infected * self.infected_score

        # 死亡者数によるスコア計算
        avg_death = sum(self.death_data) / len(self.death_data)
        d_score = avg_death * self.death_score

        # 経済状態によるスコア計算
        economy_status = self._decide_economy_status()
        ec_score = self.economy_score["normal"]
        if economy_status == QLearningEconomyStatus.RECESSION:
            ec_score = self.economy_score["recession"]
        elif economy_status == QLearningEconomyStatus.CRISIS:
            ec_score = self.economy_score["crisis"]

        score = i_score + d_score + ec_score
        return score

    def get_executable_acts(self):
        """ 実行可能なアクションの一覧を取得 """
        results = []
        for act in QLearningAction:
            if self.is_possible_action(act.value):
                results.append(act.value)
        return results

    def get_impossible_score(self):
        """ アクションが実行付加だった場合のスコアを取得 """
        return self.impossible_action_score


class QLearningAction(Enum):
    """
    Q-Learning Actions
    """

    # 実行不可能なアクション
    IMPOSSIBLE = -1
    # 何もしない
    NOP = 0
    # 病院のキャパを +10
    UP_HOSPITAL_CAPACITY = 1
    # 病院のキャパを -10
    DOWN_HOSPITAL_CAPACITY = 2
    # マスクを配布 (感染確率を半減)
    ABE_NO_MASK = 3


class QLearningInfectionStatus(Enum):
    """
    Q-Learning Infection Status
    """

    # 感染拡大前
    BEFORE_PANDEMIC = 0
    # 感染拡大
    SPREAD = 1
    # 感染爆発
    EXPLOSION = 2
    # 蔓延
    PANDEMIC = 3
    # 感染収束
    CONVERGENCE = 4
    # 感染拡大後
    AFTER_PANDEMIC = 5


class QLearningHospitalStatus(Enum):
    """
    Q-Learning Hospital Status
    """

    # 通常時
    NORMAL = 0
    # 病床逼迫
    TIGHT = 1


class QLearningEconomyStatus(Enum):
    """
    Q-Learning Economy Status
    """

    # 通常時
    NORMAL = 0
    # 不況
    RECESSION = 1
    # 経済危機
    CRISIS = 2


class QLearningMaskDistributionStatus(Enum):
    """
    Q-Learning Mask Distribution Status
    """

    # 未配布
    UNDISTRIBUTED = 0
    # 配布済み
    DISTRIBUTED = 1


class QLearningAgent:
    """
    Q-Learning Agent class
    """

    def __init__(
        self,
        init_q_table_path=None,
        alpha=0.2,
        ganma=0.99,
        epsilon=0.1,
        observation=None,
    ):
        # 学習率 (0.0 ~ 1.0)
        self.alpha = alpha
        # 割引率 (0.0 ~ 1.0)
        self.ganma = ganma
        # ε-greedy 法のパラメータ
        self.epsilon = epsilon

        # アクション定義リスト
        self.actions = [
            a.value for a in QLearningAction if a != QLearningAction.IMPOSSIBLE
        ]

        # 観測状態
        self.observation = observation
        if self.observation is None:
            self.observation = QLearningInfectionStatus.BEFORE_PANDEMIC

        self.reward_history = []
        self.state = str(observation)
        self.init_state = str(observation)
        self.previous_state = None
        self.previous_action = None

        # Q-Table
        if init_q_table_path is None:
            model_id = uuid.uuid4().hex
            self.q_values = self._init_q_values(model_id)
        else:
            self.q_values = self._load_q_values(init_q_table_path)
        self.model_id = self.q_values["model_id"]

        logger.info(
            "Q-Learning Agent クラスを初期化しました。"
            "model={}, alpha={}, ganma={}, epsilon={}".format(
                self.model_id,
                self.alpha,
                self.ganma,
                self.epsilon,
            )
        )

    def _init_q_values(self, model_id):
        """ Q-Table の初期化 """
        q_values = {}
        q_values["generation"] = 0
        q_values["episode_count"] = 0
        q_values["model_id"] = model_id
        q_values[self.state] = np.repeat(0.0, len(self.actions)).tolist()
        return q_values

    def _load_q_values(self, path):
        """ 既存の Q-Table を読込 """
        with open(path, mode="r") as f:
            q_values = json.load(f)
            return q_values

    def act(self, executables, order=1) -> int:
        """ 行動を決定 """
        act_list = self.q_values[self.state]
        if order > len(act_list):
            # 全てのアクションが実行不可能な場合 => ランダムなアクションを返す
            return np.random.randint(0, len(act_list))

        # ε-greedy
        if np.random.uniform() < self.epsilon:
            # random
            action = np.random.randint(0, len(act_list))
        else:
            # greedy
            action = int(np.where(act_list == np.sort(act_list)[-order])[0][0])

        # 実行不可能なアクションを選択した場合 => Q値が次点で高いアクションを再帰的に選択
        if action not in executables:
            next_order = order + 1
            action = self.act(executables, next_order)

        self.previous_action = action
        return action

    def observe(self, next_state, reward=None):
        """ 次の状態と報酬の観測 """
        next_state = ".".join([s.name for s in next_state])
        if next_state not in self.q_values:
            # 初めて観測する状態のとき
            self.q_values[next_state] = np.repeat(
                0.0, len(self.actions)
            ).tolist()

        self.previous_state = copy.deepcopy(self.state)
        self.state = next_state

        if reward is not None:
            self.reward_history.append(reward)
            self.learn(reward)

    def count_up_episode(self):
        """ モデル内に記録している経験済みエピソード数カウントを +1 する """
        self.q_values["episode_count"] += 1

    def get_episode_count(self):
        """ モデル内に記録している経験済みエピソード数を取得 """
        return self.q_values["episode_count"]

    def learn(self, reward):
        """ Q-value の更新 """
        # Q(s,a)
        q = self.q_values[self.previous_state][self.previous_action]
        # maxQ(s')
        # FIXME: （バグ）マスク配布不可能な場合で必ず 0.0 になる問題
        max_q = max(self.q_values[self.state])
        # Q(s,a) <- Q(s,a) + alpha * (r + ganma * maxQ(s') - Q(s,a))
        self.q_values[self.previous_state][self.previous_action] = q + (
            self.alpha * (reward + (self.ganma * max_q) - q)
        )

        # 世代情報の更新
        self.q_values["generation"] += 1

    def output_q_table(self):
        """ Q-Table の json 出力 """
        episode = self.q_values["episode_count"]
        path = MODEL_OUTPUT_PATH.format(
            model_id=self.model_id, episode=episode
        )
        filename = os.path.basename(path)

        logger.info("Q-Table {} を出力しています...".format(filename))
        with open(path, mode="w") as f:
            json.dump(self.q_values, f, indent=4)
        logger.info("Q-Table {} を出力しました。".format(filename))
