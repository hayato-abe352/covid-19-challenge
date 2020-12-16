"""
MASシミュレーションの実行コード
"""
import argparse
import pathlib
import json

from Simulator.Simulator import Simulator

SIMULATION_SETTING = "./settings/simulation.json"
ENVIRONMENT_SETTING = "./settings/world.json"
AGENT_SETTING = "./settings/agent.json"
INFECTION_MODEL_SETTING = "./settings/infection-model.json"


def main(q_table_path=None, q_score_csv=None):
    simulation_setting = read_settings(SIMULATION_SETTING)
    world_setting = read_settings(ENVIRONMENT_SETTING)
    agent_setting = read_settings(AGENT_SETTING)
    infection_setting = read_settings(INFECTION_MODEL_SETTING)

    simulator = Simulator(
        simulation_setting,
        world_setting,
        agent_setting,
        infection_setting,
        q_table_path,
        q_score_csv,
    )
    simulator.run()


def read_settings(path: str) -> dict:
    """ 設定情報の読み込み """
    setting_path = pathlib.Path(path).resolve()
    with open(setting_path, mode="r") as f:
        settings = json.load(f)
        return settings


def get_options():
    """ 起動オプションを取得 """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--q-table-path",
        action="store",
        required=False,
        default=None,
        help="学習済みの Q-Table (.json) ファイルのパスを指定してください。",
    )
    parser.add_argument(
        "--q-score-csv",
        action="store",
        required=False,
        default=None,
        help="既存の Q-Score (.csv) ファイルのパスを指定してください。",
    )
    args = parser.parse_args()
    return vars(args)


if __name__ == "__main__":
    # 起動引数を取得
    options = get_options()

    main(options["q_table_path"], options["q_score_csv"])
