#!/usr/bin/env python3
"""
AI レビュー用 chat_context.md を生成する。

experiments/leaderboard.md と experiments/logs/ を読み、
以下を自動生成して docs/ai_dev/chat_context.md を出力する。

- Leaderboard Summary（上位5件）
- Latest Experiment（最新 EXP の内容・結果・結論）

使い方（リポジトリルートで）:
  python3 scripts/generate_chat_context.py
"""

import re
from pathlib import Path
from typing import List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
LEADERBOARD_PATH = ROOT / "experiments" / "leaderboard.md"
LOGS_DIR = ROOT / "experiments" / "logs"
OUT_PATH = ROOT / "docs" / "ai_dev" / "chat_context.md"


def _parse_leaderboard_table(content: str, max_rows: int = 5) -> List[dict]:
    """leaderboard.md の ROI Leaderboard 表の行をパースする。"""
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
        if len(rows) >= max_rows:
            break
    return rows


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
    """EXP ログから experiment id, purpose, summary, conclusion をパース。"""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    out = {"experiment_id": "", "purpose": "", "summary": "", "conclusion": ""}
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
                out["purpose"] = lines[i].strip()[:280]
            i += 1
            continue
        if re.match(r"^##\s+summary\s*$", line.strip(), re.IGNORECASE):
            i += 1
            parts = []
            while i < len(lines):
                l = lines[i]
                if l.strip().startswith("- **"):
                    parts.append(l.strip()[:150])
                i += 1
                if len(parts) >= 4:
                    break
                if l.strip().startswith("##") or (l.strip() and not l.strip().startswith("-")):
                    break
            out["summary"] = " ".join(parts)[:400] if parts else ""
            continue
        if re.match(r"^##\s+conclusion\s*$", line.strip(), re.IGNORECASE):
            i += 1
            parts = []
            while i < len(lines) and not lines[i].strip().startswith("##"):
                if lines[i].strip():
                    parts.append(lines[i].strip()[:120])
                i += 1
                if len(parts) >= 3:
                    break
            out["conclusion"] = " ".join(parts)[:300] if parts else ""
            continue
        i += 1
    if not out["conclusion"]:
        for j, l in enumerate(lines):
            if "**結論**" in l:
                rest = l.split("**結論**")[-1].strip().strip(":").strip()
                if rest:
                    out["conclusion"] = rest[:200]
                elif j + 1 < len(lines) and lines[j + 1].strip():
                    out["conclusion"] = lines[j + 1].strip()[:200]
                break
        if not out["conclusion"] and out["summary"]:
            out["conclusion"] = out["summary"][:200]
    return out


def _build_leaderboard_summary(rows: List[dict]) -> str:
    """Leaderboard Summary セクションの Markdown。"""
    if not rows:
        return "（leaderboard の表を取得できませんでした。experiments/leaderboard.md を参照。）\n"
    lines = [
        "| EXP | strategy | ROI | bets |",
        "|-----|----------|-----|------|",
    ]
    for r in rows:
        exp_id = r.get("Experiment ID", "—")
        params = r.get("Parameters", "—")
        roi = r.get("overall_roi_selected", "—")
        lines.append(f"| {exp_id} | {params} | {roi} | — |")
    lines.append("")
    lines.append("詳細は experiments/leaderboard.md 参照。")
    return "\n".join(lines)


def _build_latest_experiment(log_path: Optional[Path]) -> str:
    """Latest Experiment セクションの Markdown。"""
    if not log_path or not log_path.exists():
        return "（experiments/logs/ に EXP-*.md がありません。）\n"
    meta = _parse_exp_log(log_path)
    exp_id = meta["experiment_id"] or log_path.stem.replace("_", " ").upper()
    purpose = meta["purpose"] or "（ログ参照）"
    summary = meta["summary"] or "（ログ参照）"
    conclusion = meta["conclusion"] or "（ログ参照）"
    rel = log_path.relative_to(ROOT) if ROOT in log_path.parents else log_path.name
    return "\n".join([
        f"**{exp_id}**",
        "",
        "実験内容",
        purpose,
        "",
        "結果",
        summary,
        "",
        "結論",
        conclusion,
        "",
        f"ログ: {rel}",
        "",
    ])


def _build_best_historical(rows: List[dict]) -> tuple:
    """Leaderboard #1 から strategy, ROI, windows を返す。(str, str, str)"""
    if not rows:
        return "—", "—", "—"
    r = rows[0]
    params = r.get("Parameters", "—")
    roi = r.get("overall_roi_selected", "—")
    return params, roi, "12"


def main() -> int:
    leaderboard_text = LEADERBOARD_PATH.read_text(encoding="utf-8") if LEADERBOARD_PATH.exists() else ""
    top5 = _parse_leaderboard_table(leaderboard_text, max_rows=5)
    best_strategy, best_roi, best_windows = _build_best_historical(top5)

    latest_path = _latest_exp_log(LOGS_DIR)
    latest_md = _build_latest_experiment(latest_path)
    summary_md = _build_leaderboard_summary(top5)

    # Current Production Strategy = 採用戦略（leaderboard #1 ベース）
    production_top_n = "3"
    production_ev = "1.18"
    if top5:
        p = top5[0].get("Parameters", "")
        mn = re.search(r"top_n=(\d+)", p, re.IGNORECASE)
        evn = re.search(r"ev=(\d+\.?\d*)", p, re.IGNORECASE)
        if mn:
            production_top_n = mn.group(1)
        if evn:
            production_ev = evn.group(1)

    body = f"""# Chat Context

AI レビュー用。実験・leaderboard 更新後に `python3 scripts/generate_chat_context.py` で再生成すること。

---

# Project Goal

競艇予測AIのROI最大化（rolling validation n_w=12 における overall_roi_selected の改善）。

---

# Current Production Strategy

現在採用している戦略（leaderboard #1 に基づく）。

- model: xgboost
- calibration: sigmoid
- strategy: top_n_ev
- top_n: {production_top_n}
- ev_threshold: {production_ev}
- seed: 42
- features: extended_features
- validation windows: 12

---

# Best Historical Result (Leaderboard #1)

leaderboard の 1 位。

- strategy: {best_strategy}
- ROI: {best_roi}
- selected_bets: —（experiments/leaderboard.md の Bet Sizing 表参照）
- validation windows: {best_windows}

---

# Latest Experiment

{latest_md}

---

# Leaderboard Summary

{summary_md}

---

# Current Findings

- EV threshold を下げると bet 数が増える。ev=1.18 が 1 位（-14.54%）、ev=1.20 が 2 位（-14.88%）。
- top_n が大きいと ROI が悪化する傾向（top_n=3 が最良、top_n=6 で -18.78%）。
- bet sizing は fixed が最良。Kelly 系は資金制約で破綻リスクあり。
- calibration は sigmoid が none より有利（-14.88% vs -15.80%）。
- xgboost が lightgbm より ROI 良好（-14.88% vs -20.90%）。

---

# Open Questions

- EXP-0008 Task3: ensemble（確率平均）で bet_count=0 となる不具合。予測マージ／パス参照の修正が必要。
- 暫定 best（n_w=4）top_n=3, ev=1.25 は n_w=12 再評価が未実施。

---

# Next Experiments

- ensemble 不具合修正後の再評価。
- top_n / EV threshold の追加 sweep（必要に応じて）。
- probability calibration の詳細比較（必要に応じて）。
"""

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(body.strip() + "\n", encoding="utf-8")
    print(f"Generated {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
