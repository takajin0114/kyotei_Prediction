"""
rolling validation の summary が標準キーを持つことを検証するテスト。
"""
import os
import sys
import unittest
from pathlib import Path

# プロジェクトルートを path に追加
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# 標準化された summary に含めるべきキー（タスク2で定義）
REQUIRED_SUMMARY_KEYS = {
    "model_type",
    "calibration",
    "feature_set",
    "strategy",
    "top_n",
    "ev_threshold",
    "seed",
    "n_windows",
    "overall_roi_selected",
    "mean_roi_selected",
    "median_roi_selected",
    "std_roi_selected",
    "total_selected_bets",
    "mean_log_loss",
    "mean_brier_score",
}


class TestRollingValidationSummary(unittest.TestCase):
    """rolling validation summary の標準キーを検証する"""

    def test_required_summary_keys_exist_in_rolling_roi_output(self):
        """run_rolling_validation_roi の返却 summary に必須キーが含まれること（DB がある場合のみ実行）"""
        from kyotei_predictor.data.race_db import DEFAULT_DB_PATH
        from kyotei_predictor.tools.rolling_validation_roi import run_rolling_validation_roi

        db_path = Path(DEFAULT_DB_PATH)
        if not db_path.exists():
            self.skipTest(f"DB not found: {db_path}")
        data_dir = _ROOT / "kyotei_predictor" / "data" / "raw"
        if not data_dir.is_dir():
            data_dir = _ROOT / "kyotei_predictor" / "data" / "raw"
        if not data_dir.is_dir():
            self.skipTest("data_dir not found")
        out_dir = _ROOT / "outputs" / "test_rolling_summary"
        out_dir.mkdir(parents=True, exist_ok=True)
        prev_fs = os.environ.get("KYOTEI_FEATURE_SET")
        try:
            os.environ["KYOTEI_FEATURE_SET"] = "extended_features"
            summary, _ = run_rolling_validation_roi(
                db_path=str(db_path),
                output_dir=out_dir,
                data_dir_raw=data_dir,
                train_days=30,
                test_days=7,
                step_days=7,
                n_windows=1,
                top_n=6,
                ev_threshold=1.20,
                calibration="sigmoid",
                seed=42,
            )
            missing = REQUIRED_SUMMARY_KEYS - set(summary.keys())
            self.assertEqual(missing, set(), msg=f"Missing keys in summary: {missing}")
        finally:
            if prev_fs is not None:
                os.environ["KYOTEI_FEATURE_SET"] = prev_fs
            elif "KYOTEI_FEATURE_SET" in os.environ:
                os.environ.pop("KYOTEI_FEATURE_SET")


if __name__ == "__main__":
    unittest.main()
