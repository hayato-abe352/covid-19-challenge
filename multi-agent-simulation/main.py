"""
MASシミュレーションの実行コード
"""
from Simulator import Infection, Simulator

# シミュレーションパラメータ
SIMULATION_PARAMS = {
    "simulation_days": 150,
    "episode_num": 10,
    "env_size": 10,
    "population": 200,
    "init_infected_num": 3,
    "agent_moving": "freeze",
}

# 感染症パラメータ
INFECTION_PARAMS = {
    "infection_prob": 0.02,
    "recovery_prob": 1 / 20,
    "antibody_acquisition_prob": 1.0,
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
    simulator.output_line_charts()

    # 集計結果出力
    episode_num = SIMULATION_PARAMS["episode_num"]
    aa_prob = INFECTION_PARAMS["antibody_acquisition_prob"]
    simulator.output_aggregated_line_chart(
        title="TotalEpisode:{}, AAprob:{}".format(episode_num, aa_prob)
    )

    # アニメーション出力
    simulator.output_animation()


if __name__ == "__main__":
    main()
