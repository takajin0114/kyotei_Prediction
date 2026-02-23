#!/usr/bin/env bash
#
# バッチフェッチが「動いているように見えて実は止まっている」状態を検知するスクリプト。
# プロセスは生きているが、ログが一定時間更新されていない & CPU が増えていない → ハングとみなす。
#
# 使い方:
#   ./scripts/check_batch_fetch_stuck.sh              # チェックのみ（止まっていたら exit 1）
#   ./scripts/check_batch_fetch_stuck.sh --kill       # 止まっていたらプロセスを落とす
#   STALE_MINUTES=60 ./scripts/check_batch_fetch_stuck.sh
#
# 検知条件:
#   1. batch_fetch_all_venues を実行中のプロセスがいる
#   2. そのプロセスに紐づくログファイルの最終更新が STALE_MINUTES 分より古い
#   3. (オプション) Python 子プロセスの CPU 時間が 60 秒前後で増えていない
#
# 環境変数:
#   STALE_MINUTES  … ログがこの分数だけ更新されなければ「止まっている」とみなす（デフォルト: 30）
#   LOG_FILE       … ログファイルパス（未指定時はプロセスコマンドから自動検出）
#
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}/.."
cd "${PROJECT_ROOT}"

STALE_MINUTES="${STALE_MINUTES:-30}"
DO_KILL=false
[[ "${1:-}" == "--kill" ]] && DO_KILL=true

# batch_fetch_all_venues を実行しているプロセスを探す（tee を含むコマンドの親＝シェルの PID）
find_batch_pid() {
  local pids
  if [[ "$(uname -s)" == "Darwin" ]]; then
    pids="$(ps -eo pid,command 2>/dev/null | grep -E 'batch_fetch_all_venues' | grep -v check_batch_fetch_stuck | awk '{print $1}')"
  else
    pids="$(pgrep -f "batch_fetch_all_venues" 2>/dev/null)"
  fi
  [[ -z "$pids" ]] && return 0
  for pid in $pids; do
    local cmd
    cmd="$(ps -p "$pid" -o command= 2>/dev/null)"
    if echo "$cmd" | grep -q "tee -a"; then
      echo "$pid"
      return 0
    fi
  done
  # tee を含むプロセスがなければ最初の PID（Python の可能性）
  echo "$pids" | head -1
}

# そのプロセスのコマンド行から tee -a のログファイルを抽出
get_log_file_from_pid() {
  local pid="$1"
  [[ -z "$pid" ]] && return 1
  if [[ -n "${LOG_FILE}" ]]; then
    echo "${LOG_FILE}"
    return 0
  fi
  local cmd
  cmd="$(ps -p "$pid" -o command= 2>/dev/null)" || return 1
  local log
  log="$(echo "$cmd" | sed -n 's/.*tee -a \([^ ]*\).*/\1/p')"
  [[ -n "$log" ]] && echo "$log" && return 0
  # フォールバック: 日次ログ logs/batch_fetch_YYYY-MM-DD.log のうち最も新しいもの
  log="$(cd "${PROJECT_ROOT}" && ls -t logs/batch_fetch_*.log 2>/dev/null | head -1)"
  [[ -n "$log" ]] && echo "$log" && return 0
  # 旧形式: プロジェクト直下の batch_fetch_*.log
  (cd "${PROJECT_ROOT}" && ls -t batch_fetch_*.log 2>/dev/null | head -1)
}

# Python 子プロセスの PID（batch の子）
get_python_child_pid() {
  local parent_pid="$1"
  [[ -z "$parent_pid" ]] && return 1
  if [[ "$(uname -s)" == "Darwin" ]]; then
    ps -eo pid,ppid,comm 2>/dev/null | awk -v ppid="$parent_pid" '
      $2 == ppid && $3 ~ /Python|python/ { print $1; exit }
    '
  else
    pgrep -P "$parent_pid" 2>/dev/null | while read -r cid; do
      ps -p "$cid" -o comm= 2>/dev/null | grep -q -i python && echo "$cid" && break
    done
  fi
}

# ログの最終更新からの経過分数
log_age_minutes() {
  local log_path="$1"
  [[ -z "$log_path" ]] && echo "0" && return 0
  [[ -f "$log_path" ]] || { echo "0"; return 0; }
  local mtime_sec
  if [[ "$(uname -s)" == "Darwin" ]]; then
    mtime_sec="$(stat -f %m "$log_path")"
  else
    mtime_sec="$(stat -c %Y "$log_path")"
  fi
  local now_sec
  now_sec="$(date +%s)"
  echo "$(( (now_sec - mtime_sec) / 60 ))"
}

# プロセスの CPU 時間（秒、整数）。macOS の ps は秒に 54.27 のような小数点が出ることがある
get_cpu_time_seconds() {
  local pid="$1"
  [[ -z "$pid" ]] && echo "0" && return 0
  local etime
  etime="$(ps -p "$pid" -o time= 2>/dev/null | tr -d ' ')" || { echo "0"; return 0; }
  # time 形式は MM:SS または HH:MM:SS。秒は整数に丸める
  local t=0 a b c
  IFS=: read -r a b c <<< "$etime"
  a="${a:-0}"; b="${b:-0}"; c="${c:-0}"
  a="${a%%.*}"; b="${b%%.*}"; c="${c%%.*}"
  if [[ -n "$c" ]]; then
    t=$(( 3600 * 10#${a} + 60 * 10#${b} + 10#${c} ))
  elif [[ -n "$b" ]]; then
    t=$(( 60 * 10#${a} + 10#${b} ))
  else
    t=$(( 10#${a} ))
  fi
  echo "$t"
}

main() {
  local batch_pid
  batch_pid="$(find_batch_pid)"
  if [[ -z "$batch_pid" ]]; then
    echo "[OK] batch_fetch_all_venues は実行されていません。"
    exit 0
  fi

  local log_file
  log_file="$(get_log_file_from_pid "$batch_pid")"
  if [[ -z "$log_file" ]]; then
    echo "[?] ログファイルを特定できませんでした (PID=$batch_pid)。LOG_FILE を指定してください。"
    exit 0
  fi
  # 相対パスの場合はプロジェクトルート基準
  [[ "$log_file" != /* ]] && log_file="${PROJECT_ROOT}/${log_file}"

  local age
  age="$(log_age_minutes "$log_file")"
  if [[ "$age" -lt "$STALE_MINUTES" ]]; then
    echo "[OK] バッチ実行中 (PID=$batch_pid)。ログ ${log_file} は ${age} 分前に更新されています。"
    exit 0
  fi

  # ログが古い → CPU が増えているか確認
  local python_pid
  python_pid="$(get_python_child_pid "$batch_pid")"
  local cpu_before cpu_after
  cpu_before="$(get_cpu_time_seconds "$python_pid")"
  sleep 5
  cpu_after="$(get_cpu_time_seconds "$python_pid")"
  if [[ -n "$python_pid" ]] && [[ "$cpu_after" -gt "$cpu_before" ]]; then
    echo "[OK] バッチ実行中 (PID=$batch_pid)。ログは ${age} 分前の更新ですが、CPU は増加しています（${cpu_before}s → ${cpu_after}s）。"
    exit 0
  fi

  # 止まっていると判断
  echo "[STUCK] バッチプロセスは生きていますが、ログが ${age} 分間更新されておらず、CPU も増えていません。ハングの可能性があります。"
  echo "  PID: $batch_pid"
  echo "  ログ: $log_file"
  echo "  ログ最終更新: ${age} 分前"

  if [[ "$DO_KILL" == true ]]; then
    echo "  → プロセスを終了します (kill $batch_pid)"
    kill "$batch_pid" 2>/dev/null || true
    exit 1
  fi

  echo "  再実行でプロセスを落とす: $0 --kill"
  exit 1
}

main
