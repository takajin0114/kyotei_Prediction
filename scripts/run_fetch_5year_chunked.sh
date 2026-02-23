#!/usr/bin/env bash
# 5年分データを数回に分けて取得するランチャー（プロジェクトルートで実行）
# 例: ./scripts/run_fetch_5year_chunked.sh check
#      ./scripts/run_fetch_5year_chunked.sh next 1
#      ./scripts/run_fetch_5year_chunked.sh next 3

set -e
cd "$(dirname "$0")/.."
# venv を自動で使う（activate し忘れても動く）
if [[ -x "./.venv/bin/python" ]]; then
  PYTHON="${VENV_PYTHON:-./.venv/bin/python}"
else
  PYTHON="${VENV_PYTHON:-$(command -v python3 2>/dev/null || command -v python)}"
fi

case "${1:-}" in
  check)
    exec "$PYTHON" -m kyotei_predictor.tools.batch.fetch_5year_chunked --check
    ;;
  list)
    exec "$PYTHON" -m kyotei_predictor.tools.batch.fetch_5year_chunked --list
    ;;
  next)
    N="${2:-1}"
    exec "$PYTHON" -m kyotei_predictor.tools.batch.fetch_5year_chunked --next "$N" --rate-limit "${RATE_LIMIT:-1}" --race-workers "${RACE_WORKERS:-6}"
    ;;
  range)
    if [ -z "${2:-}" ] || [ -z "${3:-}" ]; then
      echo "Usage: $0 range START_DATE END_DATE   # 例: $0 range 2023-01-01 2023-12-31"
      exit 1
    fi
    exec "$PYTHON" -m kyotei_predictor.tools.batch.fetch_5year_chunked --range "$2" "$3" --rate-limit "${RATE_LIMIT:-1}" --race-workers "${RACE_WORKERS:-6}"
    ;;
  *)
    echo "Usage: $0 {check|list|next [N]|range START END}"
    echo "  check       進捗確認（取得済み・未取得・次に取る範囲）"
    echo "  list        全計画月の一覧と取得状況"
    echo "  next [N]    未取得の次の N ヶ月分を取得（省略時 1）"
    echo "  range S E   指定期間を取得（既存はスキップ）"
    exit 1
    ;;
esac
