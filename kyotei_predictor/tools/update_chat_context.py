"""
chat_context.md の Latest Experiment と Leaderboard Summary を、
experiments/leaderboard.md と experiments/logs/ から自動更新する。

使い方:
  python3 -m kyotei_predictor.tools.update_chat_context
  または
  PYTHONPATH=. python3 kyotei_predictor/tools/update_chat_context.py

実験ログ・leaderboard 更新後に実行し、commit 前に chat_context を同期する。
"""

import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parent.parent
_LEADERBOARD_PATH = _PROJECT_ROOT / "experiments" / "leaderboard.md"
_LOGS_DIR = _PROJECT_ROOT / "experiments" / "logs"
_CHAT_CONTEXT_PATH = _PROJECT_ROOT / "docs" / "ai_dev" / "chat_context.md"


def _parse_leaderboard_table(content: str) -> List[dict]:
    """leaderboard.md の ROI Leaderboard 表（Rank 付き）の行を最大3件パースする。"""
    lines = content.splitlines()
    in_table = False
    header = []
    rows = []
    for line in lines:
        if "| Rank |" in line and "Experiment ID |" in line and "overall_roi_selected |" in line:
            in_table = True
            header = [c.strip() for c in line.split("|")[1:-1]]
            continue
        if not in_table:
            continue
        if not line.strip().startswith("|"):
            break
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) < len(header):
            continue
        rank_cell = cells[0] if header else ""
        if not re.match(r"^\d+$", rank_cell):
            continue
        row = dict(zip(header, cells))
        rows.append(row)
        if len(rows) >= 3:
            break
    return rows


def _build_leaderboard_summary(leaderboard_path: Path) -> str:
    """Leaderboard Summary セクションの Markdown を組み立てる。"""
    text = leaderboard_path.read_text(encoding="utf-8")
    rows = _parse_leaderboard_table(text)
    if not rows:
        return "（leaderboard の表を取得できませんでした。手動で experiments/leaderboard.md を参照してください。）\n"
    header = "| Rank | Experiment ID | Parameters | overall_roi_selected | selected_bets | Notes |"
    sep = "|------|----------------|-----------|----------------------|----------------|-------|"
    lines = [
        "<!-- update_chat_context.py が自動更新 -->",
        "",
        header,
        sep,
    ]
    for r in rows:
        rank = r.get("Rank", "—")
        exp_id = r.get("Experiment ID", "—")
        params = r.get("Parameters", "—")
        roi = r.get("overall_roi_selected", "—")
        notes = r.get("Notes", "—")
        selected_bets = "—"  # 主表にはないため省略
        lines.append(f"| {rank} | {exp_id} | {params} | {roi} | {selected_bets} | {notes} |")
    lines.extend(["", "詳細は experiments/leaderboard.md 参照。", ""])
    return "\n".join(lines)


def _latest_exp_log(logs_dir: Path) -> Optional[Path]:
    """experiments/logs/ 内で最大の EXP-XXXX を持つ .md を返す。"""
    if not logs_dir.is_dir():
        return None
    candidates = []
    for p in logs_dir.glob("EXP-*.md"):
        m = re.match(r"EXP-(\d{4})", p.name, re.IGNORECASE)
        if m:
            candidates.append((int(m.group(1)), p))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def _parse_exp_log(path: Path) -> dict:
    """EXP ログの experiment id, purpose, summary を簡易パース。"""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    out = {"experiment_id": "", "purpose": "", "summary": ""}
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r"^##\s+experiment\s+id\s*$", line.strip(), re.IGNORECASE):
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            if i < len(lines) and re.match(r"^EXP-\d{4}", lines[i].strip(), re.IGNORECASE):
                out["experiment_id"] = lines[i].strip()
            i += 1
            continue
        if re.match(r"^##\s+purpose\s*$", line.strip(), re.IGNORECASE):
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            if i < len(lines) and not lines[i].strip().startswith("#"):
                out["purpose"] = lines[i].strip()[:250]
            i += 1
            continue
        if re.match(r"^##\s+summary\s*$", line.strip(), re.IGNORECASE):
            i += 1
            parts = []
            while i < len(lines) and (lines[i].strip().startswith("- ") or not lines[i].strip()):
                if lines[i].strip().startswith("- "):
                    parts.append(lines[i].strip()[:120])
                i += 1
                if len(parts) >= 3:
                    break
            out["summary"] = " ".join(parts)[:350] if parts else ""
            continue
        i += 1
    return out


def _build_latest_experiment(logs_dir: Path) -> str:
    """Latest Experiment セクションの Markdown を組み立てる。"""
    path = _latest_exp_log(logs_dir)
    if not path:
        return "<!-- update_chat_context.py が自動更新 -->\n\n（experiments/logs/ に EXP-*.md がありません。）\n"
    meta = _parse_exp_log(path)
    exp_id = meta["experiment_id"] or path.stem.replace("_", " ").upper()
    purpose = meta["purpose"] or "（概要はログを参照）"
    summary = meta["summary"] or "（結果は experiments/logs/ を参照）"
    rel_path = path.relative_to(_PROJECT_ROOT) if _PROJECT_ROOT in path.parents else path.name
    lines = [
        "<!-- update_chat_context.py が自動更新 -->",
        "",
        f"- **最新 EXP**: {exp_id}",
        f"- **概要**: {purpose}",
        f"- **結果**: {summary}",
        f"- **ログ**: {rel_path}",
        "",
    ]
    return "\n".join(lines)


def _replace_section(content: str, section_title: str, new_body: str) -> str:
    """# Section Title の直後から次の # の手前までを new_body に差し替える。"""
    pattern = rf"(^# {re.escape(section_title)}\s*\n)(.*?)(?=^# [^\s]|\Z)"
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if not match:
        return content
    return content[: match.start(2)] + new_body.rstrip() + "\n\n" + content[match.end(2) :]


def main() -> int:
    if not _LEADERBOARD_PATH.exists():
        print(f"Error: {_LEADERBOARD_PATH} not found", file=sys.stderr)
        return 1
    if not _CHAT_CONTEXT_PATH.exists():
        print(f"Error: {_CHAT_CONTEXT_PATH} not found", file=sys.stderr)
        return 1

    latest_body = _build_latest_experiment(_LOGS_DIR)
    leaderboard_body = _build_leaderboard_summary(_LEADERBOARD_PATH)

    content = _CHAT_CONTEXT_PATH.read_text(encoding="utf-8")
    content = _replace_section(content, "Latest Experiment", latest_body)
    content = _replace_section(content, "Leaderboard Summary", leaderboard_body)

    _CHAT_CONTEXT_PATH.write_text(content, encoding="utf-8")
    print(f"Updated {_CHAT_CONTEXT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
