#!/usr/bin/env python3
"""
Google Colab向け 学習→予測 実行ラッパー。

想定:
  1) Colabでこのリポジトリをclone
  2) Google Driveを /content/drive にマウント
  3) 本スクリプトを実行して Drive 上データで学習/予測し、成果物を Drive 側へ同期
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from kyotei_predictor.tools.storage.drive_data_sync import sync_directories


def run_cmd(cmd: list[str]) -> None:
    print("[run]", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="ColabでDriveデータを使って学習/予測を実行")
    parser.add_argument(
        "--drive-root",
        type=str,
        default="/content/drive/MyDrive/kyotei_prediction",
        help="Google Drive上のプロジェクト保存先ルート",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="学習/予測用データディレクトリ（未指定時: <drive-root>/data/raw）",
    )
    parser.add_argument("--year-month", type=str, default=None, help="学習データ年月フィルタ（例: 2026-02）")
    parser.add_argument("--n-trials", type=int, default=1, help="Optuna試行回数")
    parser.add_argument("--minimal", action="store_true", help="最小モード（短時間）")
    parser.add_argument("--predict-date", type=str, default=None, help="予測対象日（指定時のみ予測実行）")
    parser.add_argument("--skip-prediction", action="store_true", help="予測をスキップ")
    parser.add_argument("--python-bin", type=str, default=sys.executable, help="使用するPython実行ファイル")
    parser.add_argument("--skip-push-artifacts", action="store_true", help="学習/予測成果物のDrive同期をスキップ")
    args = parser.parse_args()

    drive_root = Path(args.drive_root).expanduser().resolve()
    data_dir = Path(args.data_dir).expanduser().resolve() if args.data_dir else (drive_root / "data" / "raw")

    if not drive_root.exists():
        raise FileNotFoundError(f"drive root not found: {drive_root}")
    if not data_dir.exists():
        raise FileNotFoundError(f"data dir not found: {data_dir}")

    # 学習
    train_cmd = [
        args.python_bin,
        "-m",
        "kyotei_predictor.tools.optimization.optimize_graduated_reward",
        "--data-dir",
        str(data_dir),
        "--n-trials",
        str(args.n_trials),
    ]
    if args.year_month:
        train_cmd += ["--year-month", args.year_month]
    if args.minimal:
        train_cmd += ["--minimal"]
    run_cmd(train_cmd)

    # 予測
    if not args.skip_prediction and args.predict_date:
        pred_cmd = [
            args.python_bin,
            "-m",
            "kyotei_predictor.tools.prediction_tool",
            "--predict-date",
            args.predict_date,
            "--data-dir",
            str(data_dir),
        ]
        run_cmd(pred_cmd)

    # 成果物をDriveへ同期
    if not args.skip_push_artifacts:
        artifact_dirs = ["optuna_models", "optuna_results", "optuna_logs", "outputs"]
        for rel in artifact_dirs:
            local_dir = Path(rel).resolve()
            if not local_dir.exists():
                continue
            dst_dir = drive_root / rel
            stats = sync_directories(local_dir, dst_dir)
            print(
                f"[sync] {rel} -> {dst_dir} "
                f"(copied={stats.copied_files}, skipped={stats.skipped_files})",
                flush=True,
            )

    print("[done] colab learning cycle completed", flush=True)


if __name__ == "__main__":
    main()
