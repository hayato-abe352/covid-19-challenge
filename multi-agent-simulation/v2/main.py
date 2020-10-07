"""
MASシミュレーションの実行コード
"""
import pathlib
import os
import json

from Simulator.Simulator import Simulator

ENVIRONMENT_SETTING = "./settings/world.json"
INFECTION_MODEL_SETTING = "./settings/infection-model.json"


def main():
    world_setting = read_settings(ENVIRONMENT_SETTING)
    infection_setting = read_settings(INFECTION_MODEL_SETTING)
    simulator = Simulator(world_setting, infection_setting)


def read_settings(path: str) -> dict:
    """ 設定情報の読み込み """
    setting_path = pathlib.Path(path).resolve()
    with open(setting_path, mode="r") as f:
        settings = json.load(f)
        return settings


if __name__ == "__main__":
    main()
