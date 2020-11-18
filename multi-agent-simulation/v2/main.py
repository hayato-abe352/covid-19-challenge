"""
MASシミュレーションの実行コード
"""
import pathlib
import json

from Simulator.Simulator import Simulator

SIMULATION_SETTING = "./settings/simulation.json"
ENVIRONMENT_SETTING = "./settings/world.json"
AGENT_SETTING = "./settings/agent.json"
INFECTION_MODEL_SETTING = "./settings/infection-model.json"


def main():
    simulation_setting = read_settings(SIMULATION_SETTING)
    world_setting = read_settings(ENVIRONMENT_SETTING)
    agent_setting = read_settings(AGENT_SETTING)
    infection_setting = read_settings(INFECTION_MODEL_SETTING)

    simulator = Simulator(
        simulation_setting, world_setting, agent_setting, infection_setting
    )
    simulator.run()


def read_settings(path: str) -> dict:
    """ 設定情報の読み込み """
    setting_path = pathlib.Path(path).resolve()
    with open(setting_path, mode="r") as f:
        settings = json.load(f)
        return settings


if __name__ == "__main__":
    main()
