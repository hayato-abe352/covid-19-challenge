"""
MASシミュレーター
"""
import glob
import os
import sys
from collections import OrderedDict

from loguru import logger
from tqdm import tqdm

from Environment import Environment
from Simulator import Recorder
from Simulator.Visualizer import Visualizer

logger.remove()
logger.add(sys.stdout, colorize=True, backtrace=False, diagnose=False)


class Simulator:
    def __init__(
        self,
        infection_model,
        simulation_days,
        episode_num,
        env_size,
        population,
        init_infected_num,
        hospital_capacity,
        observation_period,
    ):
        # シミュレートする感染症モデル
        self.infection_model = infection_model

        # シミュレーション日数
        self.simulation_days = simulation_days
        # エピソード数
        self.episode_num = episode_num

        # 環境サイズ
        self.env_size = env_size
        # エージェント数（人口）
        self.population = population
        # 初期感染者数
        self.init_infected_num = init_infected_num
        # Hospital キャパシティ
        self.hospital_capacity = hospital_capacity
        # 観察期間
        self.observation_period = observation_period

        # データ記録
        self.recorder = Recorder(simulation_days)

    def one_epoch(self, env, day):
        """ 1回のepochを実行 (1-epoch = 1-day) """
        public_sections = [
            sec for sec in env.sections if sec.attribute == "public"
        ]

        # 1時間ごとに Agent を行動させる
        snap_shots = []
        for hour in env.active_time:
            snap_shots.append(env.get_snap_shot_df())

            # エージェントの次の位置を決定
            for agent in env.agents:
                # 同じ区画に属している Agent を記録
                agent.neighbor_agents.extend(env.get_neighbor_agents(agent))
                agent.decide_action(
                    0, self.env_size, 0, self.env_size, public_sections, hour
                )
            # エージェントの位置を更新
            for agent in env.agents:
                agent.do_action()

        # 1日が終了したら、Agent の状態を更新
        inactive_time = 24 - len(env.active_time)
        for agent in env.agents:
            # 外出中のエージェントを自宅に帰す
            agent.go_back_home()
            # familyと同居する影響を付与 (非アクティブ時間はfamilyと接触する)
            agent.neighbor_agents.extend(agent.family * inactive_time)
            agent.decide_next_status()
        for agent in env.agents:
            agent.update_status()

        # 病院への収容・病院からの退院を実行
        #   - 入院処理 => 退院処理の順に実行
        #     (空いた病床に新たな患者が入るのは早くても翌日になる)
        env.accommodate_to_hospital()
        env.leave_from_hospital()

        # 非常事態宣言の発動判定
        env.update_goverment()
        env.apply_policy()

        return snap_shots

    def run(self):
        """ シミュレーションを実行 """
        self.clear_output_dirs()

        self.recorder.clear_simulation_records()
        logger.info(
            "シミュレーション開始 Episode: {} (Day: {})".format(
                self.episode_num, self.simulation_days
            )
        )
        for episode in range(self.episode_num):
            # 環境を生成し、エージェントを初期化
            env = Environment(
                self.env_size,
                self.population,
                self.infection_model,
                self.hospital_capacity,
                self.observation_period,
            )
            env.init_agents(self.init_infected_num)
            self.recorder.append_section_map(env.get_sections())

            # 初期状態を記録
            susceptable_num = env.count_susceptable()
            exposed_num = env.count_exposed()
            infected_num = env.count_infected()
            recovered_num = env.count_recovered()
            patients_num = env.count_hospital_parients()
            logger.info(
                "Population density: {} [members/square]".format(
                    self.population / (self.env_size ** 2)
                )
            )

            self.recorder.clear_episode_record()
            self.recorder.append_seirp(
                susceptable_num,
                exposed_num,
                infected_num,
                recovered_num,
                patients_num,
            )

            with tqdm(range(self.simulation_days)) as pbar:
                emergency = False
                for day in pbar:
                    snap_shots = self.one_epoch(env, day + 1)

                    susceptable_num = env.count_susceptable()
                    exposed_num = env.count_exposed()
                    infected_num = env.count_infected()
                    recovered_num = env.count_recovered()
                    patients_num = env.count_hospital_parients()

                    self.recorder.append_seirp(
                        susceptable_num,
                        exposed_num,
                        infected_num,
                        recovered_num,
                        patients_num,
                    )
                    self.recorder.append_snap_shot(snap_shots)

                    if env.is_emergency - emergency == 1:
                        # 非常事態宣言が発令された場合
                        self.recorder.append_start_emergency(day + 1)
                    elif env.is_emergency - emergency == -1:
                        # 非常事態宣言か解除された場合
                        self.recorder.append_end_emergency(day + 1)
                    emergency = env.is_emergency

                    pbar.set_description("[Run: Episode {}]".format(episode))
                    pbar.set_postfix(
                        OrderedDict(
                            day=day + 1,
                            s=susceptable_num,
                            e=exposed_num,
                            i="{}({})".format(
                                infected_num,
                                env.count_infected_with_symptoms(),
                            ),
                            r=recovered_num,
                            p=patients_num,
                            EMG="Active" if env.is_emergency else "None",
                        )
                    )
            self.recorder.update_simulation_records()
        logger.info("シミュレーション終了")

    def clear_output_dirs(self):
        """ 出力ディレクトリの中身をクリア """
        target_dirs = [
            "outputs/animations/*.mp4",
            "outputs/images/*.png",
            "outputs/logs/*.csv",
        ]
        logger.info("出力ディレクトリの中身をクリアします")
        for target_dir in target_dirs:
            for path in glob.glob(target_dir):
                if os.path.isfile(path):
                    os.remove(path)
        logger.info("出力ディレクトリの中身をクリアしました")

    def output_logs(self):
        """ シミュレーションログを出力 """
        logger.info("ログ出力を開始します")
        output_logs = self.recorder.output_logs
        for episode in range(self.episode_num):
            path = "outputs/logs/episode-{}.csv".format(episode)
            output_logs(episode, path)
            logger.info("episode-{}.csv を出力しました".format(episode))

    def output_environment_section_map(self):
        """ Environment の区画マップを出力 """
        logger.info("区画マップ出力を開始します")
        section_maps = self.recorder.get_section_maps()
        output_section_map = Visualizer.output_section_map
        for episode, section_map in tqdm(enumerate(section_maps)):
            path = "outputs/images/section-map-episode-{}.png".format(episode)
            output_section_map(section_map, self.env_size, path)
        logger.info("区画マップを出力しました")

    def output_seir_charts(self):
        """ SEIRチャートを出力 """
        logger.info("ラインチャート出力を開始します")
        output_seir_chart = Visualizer.output_seir_chart
        for episode in range(self.episode_num):
            s, e, i, r = self.recorder.get_simulation_seir(episode)
            se, ee = self.recorder.get_emergency_date(episode)
            path = "outputs/images/episode-{}.png".format(episode)
            output_seir_chart(episode, s, e, i, r, se, ee, path)
            logger.info("episode-{}.png を出力しました".format(episode))

    def output_aggregated_seir_chart(self, title=None, estimator="mean"):
        """ 集計結果のSEIRチャートを出力
        
        Parameters
        ----------
        title : str, optional
            タイトル
        estimator : str, optional
            集計方法（デフォルトは平均値）
            Noneを指定した場合は、全エピソードの結果を重ねてプロット
        """
        logger.info("集計結果ラインチャートの出力を開始します estimator:{}".format(estimator))
        s, e, i, r = self.recorder.get_simulation_seir()
        se, ee = self.recorder.get_emergency_date()
        path = "outputs/images/aggrigated-all.png"
        if estimator is not None:
            path = "outputs/images/aggrigated-{}.png".format(estimator)
        Visualizer.output_aggregated_seir_chart(
            self.episode_num, s, e, i, r, se, ee, path, title, estimator
        )
        logger.info("集計結果ラインチャートを出力しました")

    def output_hospital_patients_charts(self):
        """ 病院の患者数遷移ラインチャートを出力 """
        logger.info("病院の患者数遷移グラフの出力を開始します")
        output_hospital_patients_chart = (
            Visualizer.output_hospital_patients_chart
        )
        for episode in range(self.episode_num):
            p = self.recorder.get_simulation_patients(episode)
            path = "outputs/images/patients-episode-{}.png".format(episode)
            output_hospital_patients_chart(
                episode, self.hospital_capacity, p, path
            )
            logger.info("patients-episode-{}.png を出力しました".format(episode))

    def output_hospital_patients_aggregated_chart(
        self, title=None, estimator="mean"
    ):
        """ 病院の患者数集計ラインチャートを出力

        Parameters
        ----------
        title : str, optional
            タイトル
        estimator : str, optional
            集計方法（デフォルトは平均値）
            Noneを指定した場合は、全エピソードの結果を重ねてプロット
        """
        logger.info("病院の患者数集計グラフの出力を開始します")
        p = self.recorder.get_simulation_patients()
        path = "outputs/images/patients-aggrigated-all.png"
        if estimator is not None:
            path = "outputs/images/patients-aggrigated-{}.png".format(
                estimator
            )
        Visualizer.output_hospital_patients_aggregated_chart(
            self.episode_num, self.hospital_capacity, p, path, title, estimator
        )
        logger.info("病院の患者数集計グラフを出力しました")

    def output_animation(self, interval=200):
        """ シミュレーション結果の動画を出力

        Parameters
        ----------
        interval : int, optional
            フレーム切り替え時間[ms]（デフォルトは200ms）
        """
        logger.info("アニメーションの出力を開始します")
        output_animation = Visualizer.output_animation
        for episode in range(self.episode_num):
            snap_shots = self.recorder.get_simulation_snap_shots(episode)
            section_map = self.recorder.get_section_maps(episode)
            path = "outputs/animations/episode-{}.mp4".format(episode)
            output_animation(
                episode, snap_shots, section_map, self.env_size, path, interval
            )
            logger.info("episode-{}.mp4 を出力しました".format(episode))
