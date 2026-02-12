#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

DATA_DIR="${DATA_DIR:-kyotei_predictor/data/test_raw}"
YEAR_MONTH="${YEAR_MONTH:-2024-05}"
PREDICT_DATE="${PREDICT_DATE:-2024-05-01}"
VENV_PATH="${VENV_PATH:-.venv}"

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

if [[ ! -d "${DATA_DIR}" ]]; then
    echo "Data directory not found: ${DATA_DIR}"
    exit 1
fi

echo
echo "[1/2] Learning (minimal, 1 trial, test_raw)..."
"${PYTHON_BIN}" -m kyotei_predictor.tools.optimization.optimize_graduated_reward \
    --data-dir "${DATA_DIR}" \
    --year-month "${YEAR_MONTH}" \
    --minimal \
    --n-trials 1

echo
echo "[2/2] Prediction (${PREDICT_DATE}, test_raw)..."
"${PYTHON_BIN}" -m kyotei_predictor.tools.prediction_tool \
    --predict-date "${PREDICT_DATE}" \
    --data-dir "${DATA_DIR}"

echo
echo "========================================"
echo "Cycle completed. Check outputs/predictions_${PREDICT_DATE}.json"
echo "========================================"
