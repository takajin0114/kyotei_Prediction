#!/usr/bin/env python3
"""
データ圧縮・保存ユーティリティ
"""
import json
import os
from typing import Any, Dict, List


class DataCompressor:
    """JSONの保存（圧縮形式対応）を行うユーティリティ"""

    def save_compressed_json(self, data: Any, file_path: str) -> bool:
        """
        データをJSONファイルに保存する（インデントなしで容量節約）

        Args:
            data: 保存するデータ（dict/list等、JSONシリアライズ可能なもの）
            file_path: 出力ファイルパス

        Returns:
            成功した場合True
        """
        try:
            os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            return True
        except Exception:
            return False

    def load_compressed_json(self, file_path: str) -> Any:
        """
        JSONファイルを読み込む

        Args:
            file_path: 入力ファイルパス

        Returns:
            読み込んだデータ。失敗時はNone
        """
        try:
            if not os.path.exists(file_path):
                return None
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
