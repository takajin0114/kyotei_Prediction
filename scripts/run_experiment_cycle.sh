#!/bin/bash
# 実験サイクル: validation → ROI → experiment log → leaderboard を1コマンドで実行。
# リポジトリルートで実行すること。DB パスは KYOTEI_DB_PATH で指定（未設定時は data/races.db）。

set -e
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
DB_PATH="${KYOTEI_DB_PATH:-data/races.db}"
OUTPUT_DIR="${ROOT}/outputs"
SUMMARY_JSON="${OUTPUT_DIR}/rolling_validation_summary.json"

echo "=== 1. Validation ==="
# 例: python3 -m kyotei_predictor.validation
# 現状は rolling_validation_roi で検証（要 --db-path）
python3 -m kyotei_predictor.tools.rolling_validation_roi \
  --db-path "$DB_PATH" \
  --output-dir "$OUTPUT_DIR"

echo "=== 2. ROI 結果取得（上記出力を利用） ==="
# summary JSON は既に outputs/ に出力済み

echo "=== 3. Experiment log 生成 ==="
CREATE_OUT=$(python3 scripts/experiments/create_experiment_log.py --summary-json "$SUMMARY_JSON")
echo "$CREATE_OUT"
EXP_ID=$(echo "$CREATE_OUT" | grep -o 'EXP_ID=EXP-[0-9]*' | sed 's/EXP_ID=//')

echo "=== 4. Leaderboard 更新 ==="
if [ -f "$SUMMARY_JSON" ]; then
  ROI=$(python3 -c "
import json
try:
    d = json.load(open('$SUMMARY_JSON'))
    if isinstance(d, list):
        d = d[0] if d else {}
    print(d.get('overall_roi_selected', ''))
except Exception:
    print('')
")
  python3 scripts/experiments/update_leaderboard.py \
    --experiment "$EXP_ID" \
    --roi "$ROI" \
    --notes "run_experiment_cycle"
else
  echo "Skip leaderboard (no summary JSON); EXP_ID=$EXP_ID"
fi

echo "=== Done ==="
