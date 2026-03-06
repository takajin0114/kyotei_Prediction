"""
optimization_config.ini を読み、CLI 用の辞書を返す。
セクションなしの KEY=VALUE 形式に対応。コメント行（#）は無視する。
"""
from pathlib import Path
from typing import Any, Dict, Optional


def load_optimization_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    optimization_config.ini を読み KEY=VALUE の辞書で返す。
    存在しない場合はデフォルト値の辞書を返す。

    Args:
        config_path: ini のパス。None の場合はプロジェクトルートの optimization_config.ini を探す。

    Returns:
        MODE, TRIALS, YEAR_MONTH, EVALUATION_MODE, VENV_PATH, LOG_DIR, CLEANUP_DAYS 等の辞書。
    """
    defaults = {
        "MODE": "fast",
        "TRIALS": "20",
        "YEAR_MONTH": "",
        "EVALUATION_MODE": "first_only",
        "VENV_PATH": "venv",
        "LOG_DIR": "logs",
        "CLEANUP_DAYS": "7",
    }
    if config_path is None:
        # 呼び出し元がプロジェクトルートで実行していることを想定
        config_path = Path("optimization_config.ini")
    path = Path(config_path)
    if not path.is_file():
        return defaults
    out = dict(defaults)
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.split("#")[0].strip()
            if "=" in line:
                key, value = line.split("=", 1)
                out[key.strip()] = value.strip()
    return out
