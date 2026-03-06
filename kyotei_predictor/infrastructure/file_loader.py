"""
JSON ファイルの読込（I/O 層）。

検証・予測のペイロード読込に利用。application 層から呼ばれる。
"""

import json
from pathlib import Path
from typing import Any, Union


def load_json(path: Union[Path, str]) -> Any:
    """JSON ファイルを読み、辞書またはリストで返す。"""
    with open(Path(path), "r", encoding="utf-8") as f:
        return json.load(f)
