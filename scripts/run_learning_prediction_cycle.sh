#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

DATA_DIR="${DATA_DIR:-kyotei_predictor/data/test_raw}"
DATA_SOURCE="${DATA_SOURCE:-file}"
YEAR_MONTH="${YEAR_MONTH:-2024-05}"
PREDICT_DATE="${PREDICT_DATE:-2024-05-01}"
VENV_PATH="${VENV_PATH:-.venv}"
# DATA_SOURCE=db のときはレースデータを SQLite から取得（未指定時は file=test_raw 用）

echo "========================================"
echo "Learning -> Prediction Cycle (test_raw)"
echo "========================================"
echo

if [[ -f "${VENV_PATH}/bin/activate" ]]; then
    echo "Activating venv: ${VENV_PATH}"
    # shellcheck disable=SC1090
    source "${VENV_PATH}/bin/activate"
    PYTHON_BIN="python"
else
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_BIN="python3"
    elif command -v python >/dev/null 2>&1; then
        PYTHON_BIN="python"
    else
        echo "Python is not available."
        exit 1
    fi
    echo "No venv found at ${VENV_PATH}. Using ${PYTHON_BIN}."
fi

if [[ "${DATA_SOURCE}" = "file" ]] && [[ ! -d "${DATA_DIR}" ]]; then
    echo "Data directory not found: ${DATA_DIR}"
    exit 1
fi

echo
echo "[1/3] Learning (minimal, 1 trial, data_source=${DATA_SOURCE})..."
LEARN_OPTS=(--year-month "${YEAR_MONTH}" --minimal --n-trials 1)
if [[ "${DATA_SOURCE}" = "db" ]]; then
    LEARN_OPTS+=(--data-source db)
else
    LEARN_OPTS+=(--data-source file --data-dir "${DATA_DIR}")
fi
"${PYTHON_BIN}" -m kyotei_predictor.tools.optimization.optimize_graduated_reward "${LEARN_OPTS[@]}"

echo
echo "[2/3] Prediction (${PREDICT_DATE}, data_source=${DATA_SOURCE})..."
PRED_OPTS=(--predict-date "${PREDICT_DATE}")
if [[ "${DATA_SOURCE}" = "db" ]]; then
    PRED_OPTS+=(--data-source db)
else
    PRED_OPTS+=(--data-source file --data-dir "${DATA_DIR}")
fi
"${PYTHON_BIN}" -m kyotei_predictor.tools.prediction_tool "${PRED_OPTS[@]}"

PREDICTION_JSON="${PROJECT_ROOT}/outputs/predictions_${PREDICT_DATE}.json"
VERIFY_LOG="${PROJECT_ROOT}/logs/verification_${PREDICT_DATE}_$(date +%Y%m%d_%H%M%S).txt"
mkdir -p "${PROJECT_ROOT}/logs"
echo
echo "[3/3] Verification (predictions vs actuals)..."
if [[ -f "${PREDICTION_JSON}" ]]; then
    "${PYTHON_BIN}" -m kyotei_predictor.tools.verify_predictions \
        --prediction "${PREDICTION_JSON}" \
        --data-dir "${DATA_DIR}" 2>&1 | tee "${VERIFY_LOG}"
else
    echo "Skip verification: ${PREDICTION_JSON} not found."
fi

echo
echo "========================================"
echo "Cycle completed. Check outputs/predictions_${PREDICT_DATE}.json"
echo "Verification log: ${VERIFY_LOG}"
echo "========================================"
