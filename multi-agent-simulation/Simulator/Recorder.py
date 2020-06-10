"""
MASシミュレーションの結果記録オブジェクト
"""
import pandas as pd
from tqdm import tqdm


class Recorder:
    def __init__(self, days):
        # タイムスタンプ
        self.t_values = list(range(days + 1))

        # SIRのカウント記録
        self.s_values = []
        self.i_values = []
        self.r_values = []
        self.s_values_in_all_episode = []
        self.i_values_in_all_episode = []
        self.r_values_in_all_episode = []

        # 使用中の病床数記録
        self.patients_values = []
        self.patients_values_in_all_episode = []

        # スナップショット記録
        self.snap_shots = []
        self.snap_shots_in_all_episode = []

        # 環境の区画情報記録
        self.section_maps = []

    def clear_simulation_records(self):
        """ シミュレーション記録の削除 """
        self.s_values_in_all_episode = []
        self.i_values_in_all_episode = []
        self.r_values_in_all_episode = []
        self.patients_values_in_all_episode = []
        self.snap_shots_in_all_episode = []
        self.section_maps = []

    def clear_episode_record(self):
        """ エピソード記録の削除 """
        self.s_values = []
        self.i_values = []
        self.r_values = []
        self.patients_values = []
        self.snap_shots = []

    def update_simulation_records(self):
        """ シミュレーション記録を更新します """
        self.s_values_in_all_episode.append(self.s_values)
        self.i_values_in_all_episode.append(self.i_values)
        self.r_values_in_all_episode.append(self.r_values)
        self.patients_values_in_all_episode.append(self.patients_values)
        self.snap_shots_in_all_episode.append(self.snap_shots)

    def append_sirp(self, s_value, i_value, r_value, p_value):
        """ SIRの数値と病院患者数を記録 """
        self.s_values.append(s_value)
        self.i_values.append(i_value)
        self.r_values.append(r_value)
        self.patients_values.append(p_value)

    def append_snap_shot(self, snap_shot):
        """ スナップショットを記録 """
        self.snap_shots.append(snap_shot)

    def append_section_map(self, section_map):
        """ セクションマップを記録 """
        self.section_maps.append(section_map)

    def get_simulation_sir(self, episode=None):
        """ シミュレーション記録からSIRカウントを取得します """
        s = self.s_values_in_all_episode
        i = self.i_values_in_all_episode
        r = self.r_values_in_all_episode
        if episode is not None:
            s = s[episode]
            i = i[episode]
            r = r[episode]
        return s, i, r

    def get_simulation_patients(self, episode=None):
        """ シミュレーション記録から病床数を取得します """
        if episode is not None:
            return self.patients_values_in_all_episode[episode]
        return self.patients_values_in_all_episode

    def get_simulation_snap_shots(self, episode=None):
        """ シミュレーション記録からスナップショットを取得します """
        if episode is not None:
            return self.snap_shots_in_all_episode[episode]
        return self.snap_shots_in_all_episode
    
    def get_section_maps(self, episode=None):
        """ シミュレーション記録から区画情報を取得します """
        if episode is not None:
            return self.section_maps[episode]
        return self.section_maps

    def output_logs(self, episode, path):
        """ シミュレーションログを出力 """
        s_val, i_val, r_val = self.get_simulation_sir(episode)
        p_val = self.get_simulation_patients(episode)

        df = pd.DataFrame(
            columns=[
                "Day",
                "Susceptable",
                "Infected",
                "Recovered",
                "Patients",
            ]
        )
        with tqdm(
            zip(self.t_values, s_val, i_val, r_val, p_val),
            total=len(self.t_values),
        ) as pbar:
            for t, s, i, r, p in pbar:
                pbar.set_description("[LogOutput: Episode {}]".format(episode))
                record = pd.Series(index=df.columns, dtype="object")
                record["Day"] = t
                record["Susceptable"] = s
                record["Infected"] = i
                record["Recovered"] = r
                record["Patients"] = p
                df = df.append(record, ignore_index=True)
            df.to_csv(path, index=False)
