"""
EXP-0072b: race difficulty filter recheck.

EXP-0072 の baseline を EXP-0070 CASE2 と一致させたうえで、
difficulty filter 実験を再実行する。ref_profit は EXP-0070 と同様 CASE0 (4.30, 4.75, 0.05) で算出。
出力: outputs/race_difficulty/exp0072b_race_difficulty.json
"""

import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _THIS_DIR.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def main() -> int:
    # run_exp0072 を ref 修正済みで呼び出し、EXP-0072b として出力
    from kyotei_predictor.tools.run_exp0072_race_difficulty_filter import main as run_0072
    sys.argv = [sys.argv[0], "--n-windows", "36", "--exp-id", "EXP-0072b", "--output-name", "exp0072b_race_difficulty.json"]
    return run_0072()


if __name__ == "__main__":
    sys.exit(main())
