#!/usr/bin/env python3
"""
簡易ダッシュボード（3.3.2）: 検証ログを集約して一覧表示する。

logs/ 配下の verification_*.txt および outputs/predictions_*.json を走査し、
的中率・回収率などのサマリを標準出力（Markdown 表）または JSON で出力する。
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from datetime import datetime


def find_verification_logs(logs_dir: Path) -> list[Path]:
    """logs 配下の verification_*.txt を返す。"""
    if not logs_dir.is_dir():
        return []
    return sorted(logs_dir.glob("verification_*.txt"))


def parse_verification_log(path: Path) -> dict:
    """1 ファイルから日付・的中率・回収率らしき数値を抽出する（簡易）。"""
    out = {"file": path.name, "path": str(path), "date": None, "metrics": {}}
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        # 日付: verification_2025-06-15_20260301_120000.txt → 2025-06-15
        m = re.search(r"verification_(\d{4}-\d{2}-\d{2})", path.name)
        if m:
            out["date"] = m.group(1)
        # 1位的中率 / Top3 / 回収率 などのパターン（verify_predictions の出力に依存）
        for pattern, key in [
            (r"1[位]?[の]?的中率[:\s]*([\d.]+)%?", "hit_rate_1"),
            (r"Top3[の]?的中率[:\s]*([\d.]+)%?", "hit_rate_top3"),
            (r"回収率[:\s]*([\d.]+)%?", "recovery_rate"),
        ]:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                try:
                    out["metrics"][key] = float(m.group(1).replace(",", ""))
                except ValueError:
                    pass
    except Exception:
        pass
    return out


def find_prediction_jsons(outputs_dir: Path) -> list[Path]:
    """outputs 配下の predictions_*.json を返す。"""
    if not outputs_dir.is_dir():
        return []
    return sorted(outputs_dir.glob("predictions_*.json"))


def summarize_predictions(path: Path) -> dict:
    """1 ファイルから予測日・レース数・EV採用ログ（ev_selection）を取得。"""
    out = {
        "file": path.name,
        "path": str(path),
        "prediction_date": None,
        "total_races": 0,
        "ev_selection": None,
    }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        out["prediction_date"] = data.get("prediction_date")
        out["total_races"] = len(data.get("predictions", []))
        es = data.get("execution_summary") or {}
        ev_sel = es.get("ev_selection")
        if ev_sel:
            out["ev_selection"] = {
                "ev_threshold": ev_sel.get("ev_threshold"),
                "fallback_used_count": ev_sel.get("fallback_used_count"),
                "final_selected_count_total": ev_sel.get("final_selected_count_total"),
            }
    except Exception:
        pass
    return out


def run(project_root: Path, format: str) -> None:
    logs_dir = project_root / "logs"
    outputs_dir = project_root / "outputs"

    verification = [parse_verification_log(p) for p in find_verification_logs(logs_dir)]
    predictions = [summarize_predictions(p) for p in find_prediction_jsons(outputs_dir)]

    if format == "json":
        print(json.dumps({"verification": verification, "predictions": predictions}, ensure_ascii=False, indent=2))
        return

    # Markdown
    print("# 簡易ダッシュボード（検証・予測サマリ）")
    print()
    print(f"取得日時: {datetime.now().isoformat()}")
    print()

    if verification:
        print("## 検証ログ")
        print("| 日付 | 1位的中率 | Top3的中率 | 回収率 | ファイル |")
        print("|------|-----------|------------|--------|----------|")
        for v in verification:
            m = v.get("metrics", {})
            print(f"| {v.get('date') or '-'} | {m.get('hit_rate_1', '-')} | {m.get('hit_rate_top3', '-')} | {m.get('recovery_rate', '-')} | {v['file']} |")
    else:
        print("## 検証ログ")
        print("（`logs/verification_*.txt` がありません）")
    print()

    if predictions:
        print("## 予測結果一覧")
        print("| 予測日 | レース数 | ファイル |")
        print("|--------|----------|----------|")
        for p in predictions:
            print(f"| {p.get('prediction_date') or '-'} | {p.get('total_races', 0)} | {p['file']} |")
        ev_predictions = [p for p in predictions if p.get("ev_selection")]
        if ev_predictions:
            print()
            print("## EV 採用ログ（strategy=ev の予測）")
            print("ROI 解釈時は ev_selection を確認すること。")
            print("| ファイル | ev_threshold | fallback_used_count | final_selected_count_total |")
            print("|----------|--------------|---------------------|---------------------------|")
            for p in ev_predictions:
                es = p["ev_selection"]
                print(f"| {p['file']} | {es.get('ev_threshold', '-')} | {es.get('fallback_used_count', '-')} | {es.get('final_selected_count_total', '-')} |")
    else:
        print("## 予測結果一覧")
        print("（`outputs/predictions_*.json` がありません）")


def main() -> None:
    parser = argparse.ArgumentParser(description="検証ログ・予測結果の簡易サマリ（3.3.2 簡易ダッシュボード）")
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parent.parent, help="プロジェクトルート")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown", help="出力形式")
    args = parser.parse_args()
    run(args.project_root, args.format)


if __name__ == "__main__":
    main()
