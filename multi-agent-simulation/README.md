# マルチエージェント感染症シミュレーター

マルチエージェントシミュレーション（MAS）を用いて、感染症をシミュレートする。

## セットアップ

```
pip install -r requirements.txt
```

シミュレーション結果をアニメーション（ `.mp4` ）で出力する場合、 `ffmpeg` もインストールする必要がある。Anaconda の場合、下記コマンドでインストール可能。

```
conda install -c conda-forge ffmpeg
```

## 実行方法

1. `main.py` にシミュレーションのパラメータを設定
1. `python main.py` を実行

## クラス構成

SIR モデルを基本構造として、適宜マルチエージェントシミュレーションの機能を高度化していく。

### Agent

- 環境内における行動主体オブジェクト
- Agent は以下の状態を持つ
  - Susceptable（未感染者）
  - Infected（感染者）
  - Recovered（回復者）
- Agent は以下のパターンで状態を変化させる
  - S-S, S-R, I-I, I-R, R-R の組み合わせで接触が起きた場合では、状態変化は起こらないとする。
  - S と I が接触した場合、一定の確率で S が I に変化する。この確率は、S の周囲に存在する I の人数に応じて高くなる。
  - I は一定の確率で R に変化する。このとき、さらに一定確率で R から S に変化する。つまり、感染症から回復した際、必ずしも抗体を獲得できるとは限らない。
- Agent が状態 I に変化した時、一定確率で「自覚症状」が付与される。
- 状態が S の Agent は、単位時間当たりに一定距離だけランダムウォークする。このとき、周囲に存在する I との合計距離が小さくなる場合（つまり、感染者に接近する移動の場合）、移動せずその場に留まる。

### Environment

- 複数の Agent が存在する環境オブジェクト
- 正方形の均一空間を想定（空間内の位置によって、Agent の特性に変化を与えない想定）
- Environment は隔離機能 Hospital を持つ。

#### Hospital
 
- Environment が保持する感染者の隔離機能
- Hospital に収容された Agent は、Environment 空間から隔離された状態になる（周囲から認知されず、かつ周囲に感染症を拡散しない）。
- Hospital に収容されている Agent の状態が I 以外に変化した場合、Hospital から退院する（収容される直前の座標に戻る）
- Hospital は capacity を持つ。capacity 以上の感染者は収容できない。

### Simulator

- マルチエージェントシミュレーションのロジックオブジェクト
- 以下の手順でシミュレーションの実行と結果出力が可能

  1. シミュレーションパラメータを渡しつつ、インスタンスを作成

     ```python
     infection_model = Infection(**INFECTION_PARAMS)
     simulator = Simulator(infection_model=infection_model, **SIMULATION_PARAMS)
     ```

  1. `run()` メソッドでシミュレーションを実行

     ```python
     simulator.run()
     ```

  1. シミュレーション完了後、結果の出力が可能

     ```python
     # ログ出力
     simulator.output_logs()

     # ラインチャート出力
     simulator.output_line_charts()

     # 集計結果出力
     simulator.output_aggregated_line_chart()

     # アニメーション出力
     simulator.output_animation()
     ```
