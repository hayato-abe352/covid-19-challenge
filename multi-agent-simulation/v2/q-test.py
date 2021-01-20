"""
Q-Learning のモデルを適用したシミュレーションの実行コード
"""
import argparse
import pathlib
import glob
import shutil
import os
import json
import datetime

from Simulator.Simulator import Simulator

SIMULATION_SETTING = "./settings/simulation.json"
ENVIRONMENT_SETTING = "./settings/world.json"
AGENT_SETTING = "./settings/agent.json"
INFECTION_MODEL_SETTING = "./settings/infection-model.json"


def main(q_table_path=None):
    now = datetime.datetime.now()
    result_dir = now.strftime("%Y%m%d-%H%M%S")

    simulation_setting = read_settings(SIMULATION_SETTING)
    world_setting = read_settings(ENVIRONMENT_SETTING)
    agent_setting = read_settings(AGENT_SETTING)
    infection_setting = read_settings(INFECTION_MODEL_SETTING)

    # モデルなし・モデルありの両パターンで試行回数を共通化する
    simulation_setting["episode"] = 10

    # Q-Learning のモデルなしでシミュレート
    print("[Step-1/4] Q-Learning モデルを適用しないシミュレーション")
    simulation_setting["simulation_recording"] = True
    simulation_setting["q_learning"] = False
    simulator = Simulator(
        simulation_setting,
        world_setting,
        agent_setting,
        infection_setting,
    )
    simulator.run()
    simulator.output_q_state_csv()

    # シミュレーション結果を移動
    print("[Step-2/4] 出力ディレクトリに結果を格納")
    move_simulation_result(
        "output/q-test-result/{}/01_natural".format(result_dir)
    )

    # Q-Learning のモデルありでシミュレート
    print("[Step-3/4] Q-Learning モデルを適用したシミュレーション")
    simulation_setting["simulation_recording"] = True
    simulation_setting["q_learning"] = True
    simulator = Simulator(
        simulation_setting,
        world_setting,
        agent_setting,
        infection_setting,
        q_table_path,
    )
    simulator.run_with_q_model()
    simulator.output_q_state_csv()
    simulator.output_q_action_csv()
    simulator.output_q_state_graph()

    # シミュレーション結果を移動
    print("[Step-4/4] 出力ディレクトリに結果を格納")
    move_simulation_result(
        "output/q-test-result/{}/02_artificial".format(result_dir)
    )


def read_settings(path: str) -> dict:
    """ 設定情報の読み込み """
    setting_path = pathlib.Path(path).resolve()
    with open(setting_path, mode="r") as f:
        settings = json.load(f)
        return settings


def move_simulation_result(dir_path: str):
    """ シミュレーションの結果ファイルを移動します """
    os.makedirs(dir_path, exist_ok=True)

    targets = ["output/*.csv", "output/images/*.png"]
    for target in targets:
        for t_path in glob.glob(target):
            if os.path.isfile(t_path):
                shutil.move(t_path, dir_path)


def get_options():
    """ 起動引数を取得 """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--q-table-path",
        action="store",
        required=True,
        help="学習済み Q-Table (.json) ファイルのパスを指定してください。",
    )
    args = parser.parse_args()
    return vars(args)


if __name__ == "__main__":
    # 起動引数を取得
    options = get_options()

    main(options["q_table_path"])
