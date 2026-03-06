"""
検証・予測結果の保存（I/O 層）。

JSON で検証ペイロードを保存する。application 層から呼ばれる。
"""

import json
from pathlib import Path
from typing import Any, Dict, List


def save_verification_result(path: Path, summary: Dict[str, Any], details: List[Dict[str, Any]]) -> None:
    """検証結果（summary + details）を JSON で保存する。"""
    payload = {
        "evaluation_mode": summary.get("evaluation_mode", "first_only"),
        "summary": summary,
        "details": details,
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
