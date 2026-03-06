"""
JSON ベースのレースデータリポジトリ実装。

既存の race_data_*.json を data_dir 以下（サブディレクトリ含む）で検索し、
従来の学習・検証フローと互換の形で返す。raw 保管用 JSON をそのまま読む用途。
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from kyotei_predictor.infrastructure.file_loader import load_json

# race_data_YYYY-MM-DD_VENUE_Rn.json から (date, venue, n) を抽出
RACE_FILENAME_PATTERN = re.compile(
    r"race_data_(\d{4}-\d{2}-\d{2})_([A-Z0-9]+)_R(\d{1,2})\.json"
)


def _parse_race_path(path: Path) -> Optional[Tuple[str, str, int]]:
    """ファイルパスから (race_date, venue, race_number) を返す。マッチしなければ None。"""
    m = RACE_FILENAME_PATTERN.match(path.name)
    if not m:
        return None
    date_s, venue, num_s = m.groups()
    return (date_s, venue, int(num_s))


class JsonRaceDataRepository:
    """data_dir 配下の race_data_*.json を読むリポジトリ。既存互換用。"""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir)

    def load_race(
        self,
        race_date: str,
        venue: str,
        race_number: int,
    ) -> Optional[Dict[str, Any]]:
        """1 レース分をファイル名で検索して読み、辞書で返す。"""
        for path in self.data_dir.rglob("race_data_*.json"):
            parsed = _parse_race_path(path)
            if not parsed:
                continue
            d, v, n = parsed
            if d == race_date and v == venue and n == race_number:
                try:
                    return load_json(path)
                except Exception:
                    return None
        return None

    def load_races_between(
        self,
        start_date: str,
        end_date: str,
        max_samples: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """期間内の race_data_*.json を日付でフィルタして読み、リストで返す。"""
        race_files = sorted(self.data_dir.rglob("race_data_*.json"))
        result: List[Dict[str, Any]] = []
        for path in race_files:
            parsed = _parse_race_path(path)
            if not parsed:
                continue
            date_str, _, _ = parsed
            if date_str < start_date or date_str > end_date:
                continue
            if max_samples is not None and len(result) >= max_samples:
                break
            try:
                data = load_json(path)
                result.append(data)
            except Exception:
                continue
        return result

    def load_races_by_date(
        self,
        race_date: str,
        venues: Optional[List[str]] = None,
    ) -> List[Tuple[Dict[str, Any], str, int]]:
        """指定日のレース一覧を (race_data, venue, race_number) のリストで返す。"""
        prefix = f"race_data_{race_date}_"
        race_files = sorted(self.data_dir.rglob("race_data_*.json"))
        result: List[Tuple[Dict[str, Any], str, int]] = []
        for path in race_files:
            if not path.name.startswith(prefix):
                continue
            parsed = _parse_race_path(path)
            if not parsed:
                continue
            _, venue, race_number = parsed
            if venues is not None and venue not in venues:
                continue
            try:
                data = load_json(path)
                result.append((data, venue, race_number))
            except Exception:
                continue
        return result
