import subprocess

if __name__ == "__main__":
    # 2024年3月分のデータディレクトリを指定
    data_dir = "kyotei_predictor/data/raw/2024-03"
    n_trials = 30  # 2024年3月データでの最適化用に試行回数を増加
    cmd = [
        "python", "-m", "kyotei_predictor.tools.optimization.optimize_graduated_reward",
        "--n-trials", str(n_trials),
        "--data-dir", data_dir
    ]
    print(f"実行コマンド: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    print(f"バッチ実行終了: returncode={result.returncode}") 