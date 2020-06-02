"""
MASシミュレーションの実行コード
"""
from Simulator import Infection, Simulator

# シミュレーションパラメータ
SIMULATION_PARAMS = {
    # シミュレーション日数
    "simulation_days": 150,
    # シミュレーションの繰り返し数
    "episode_num": 2,
    # 環境サイズ
    "env_size": 10,
    # 総人口
    "population": 200,
    # 初期感染者数
    "init_infected_num": 3,
    # Hospitalキャパシティ
    "hospital_capacity": 15,
    # 病院収容までの観察期間
    "observation_period": 3,
    # エージェントの動きパターン (moving/freeze)
    "agent_moving": "moving",
}

# 感染症パラメータ
INFECTION_PARAMS = {
    # 感染確率
    "infection_prob": 0.02,
    # 回復確率
    "recovery_prob": 1 / 20,
    # 抗体獲得率
    "antibody_acquisition_prob": 1.0,
    # 自覚症状の発生確率
    "subjective_symptoms_prob": 0.8,
    # 濃厚接触半径
    "influence_range": 2,
}


def main():
    infection_model = Infection(**INFECTION_PARAMS)
    simulator = Simulator(infection_model=infection_model, **SIMULATION_PARAMS)

    # シミュレーション実行
    simulator.run()

    # ログ出力
    simulator.output_logs()

    # ラインチャート出力
    simulator.output_sir_charts()

    # 集計結果出力
    episode_num = SIMULATION_PARAMS["episode_num"]
    title = "TotalEpisode:{}".format(episode_num)
    simulator.output_aggregated_sir_chart(title=title)
    simulator.output_aggregated_sir_chart(
        title=title, estimator=None,
    )

    # 病院の患者数推移を出力
    simulator.output_hospital_patients_charts()

    # 病院の患者数集計結果を出力
    simulator.output_hospital_patients_aggregated_chart(title=title)

    # アニメーション出力
    simulator.output_animation()


if __name__ == "__main__":
    main()
