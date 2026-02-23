#!/usr/bin/env bash
# 1ヶ月分データ取得ランチャー（プロジェクトルートで実行）
# venv を自動で使うため、activate し忘れても動く
#
# 例: ./scripts/run_batch_fetch_1month.sh
#      ./scripts/run_batch_fetch_1month.sh 2026-03
#      RATE_LIMIT=1 RACE_WORKERS=8 ./scripts/run_batch_fetch_1month.sh 2026-02

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/.."

VENV_PATH="${VENV_PATH:-.venv}"
if [[ -x "${VENV_PATH}/bin/python" ]]; then
  PYTHON="${VENV_PATH}/bin/python"
else
  PYTHON="$(command -v python3 || command -v python)"
fi

YEAR_MONTH="${1:-${YEAR_MONTH:-$(date +%Y-%m)}}"
START_DATE="${START_DATE:-${YEAR_MONTH}-01}"
if [[ -n "${END_DATE:-}" ]]; then
  :
elif [[ "${YEAR_MONTH}" =~ ^[0-9]{4}-[0-9]{2}$ ]]; then
  case "${YEAR_MONTH}" in
    *-01) END_DATE="${YEAR_MONTH%-*}-01-31" ;;
    *-02) END_DATE="${YEAR_MONTH%-*}-02-28" ;;
    *-03) END_DATE="${YEAR_MONTH%-*}-03-31" ;;
    *-04) END_DATE="${YEAR_MONTH%-*}-04-30" ;;
    *-05) END_DATE="${YEAR_MONTH%-*}-05-31" ;;
    *-06) END_DATE="${YEAR_MONTH%-*}-06-30" ;;
    *-07) END_DATE="${YEAR_MONTH%-*}-07-31" ;;
    *-08) END_DATE="${YEAR_MONTH%-*}-08-31" ;;
    *-09) END_DATE="${YEAR_MONTH%-*}-09-30" ;;
    *-10) END_DATE="${YEAR_MONTH%-*}-10-31" ;;
    *-11) END_DATE="${YEAR_MONTH%-*}-11-30" ;;
    *-12) END_DATE="${YEAR_MONTH%-*}-12-31" ;;
    *) END_DATE="${YEAR_MONTH}-28" ;;
  esac
else
  END_DATE="${YEAR_MONTH}-28"
fi

RATE_LIMIT="${RATE_LIMIT:-1}"
RACE_WORKERS="${RACE_WORKERS:-8}"
OUTPUT_DIR="${OUTPUT_DATA_DIR:-kyotei_predictor/data/raw}"

rm -f batch_fetch_all_venues.lock 2>/dev/null

echo "1ヶ月分取得: ${START_DATE} 〜 ${END_DATE} (並列${RACE_WORKERS}, rate-limit ${RATE_LIMIT}s)"
exec "$PYTHON" -m kyotei_predictor.tools.batch.batch_fetch_all_venues \
  --start-date "${START_DATE}" \
  --end-date "${END_DATE}" \
  --stadiums ALL \
  --output-data-dir "${OUTPUT_DIR}" \
  --rate-limit "${RATE_LIMIT}" \
  --race-workers "${RACE_WORKERS}" \
  --quiet
