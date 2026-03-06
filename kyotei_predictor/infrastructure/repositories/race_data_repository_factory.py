"""
レースデータリポジトリのファクトリ。

data_source と data_dir / db_path から適切な実装を返す。
usecase は SQL を書かず、このファクトリで repository を取得して利用する。
"""

from pathlib import Path
from typing import Optional, Union

from kyotei_predictor.domain.repositories.race_data_repository import (
    RaceDataRepositoryProtocol,
)
from kyotei_predictor.infrastructure.repositories.json_race_data_repository import (
    JsonRaceDataRepository,
)
from kyotei_predictor.infrastructure.repositories.db_race_data_repository import (
    DbRaceDataRepository,
)


def get_race_data_repository(
    data_source: str,
    data_dir: Optional[Union[Path, str]] = None,
    db_path: Optional[str] = None,
) -> RaceDataRepositoryProtocol:
    """
    data_source に応じて JSON または DB のリポジトリを返す。

    Args:
        data_source: "json" または "db"
        data_dir: JSON 用の data_dir（data_source=json 時に必須）
        db_path: DB 用の SQLite パス（data_source=db 時に必須。None なら Settings から取得）

    Returns:
        RaceDataRepositoryProtocol を実装したインスタンス
    """
    data_source = (data_source or "json").strip().lower()
    if data_source == "db":
        if db_path is None:
            from kyotei_predictor.config.settings import Settings
            db_path = str(Path(Settings.PROJECT_ROOT) / Settings.DB_PATH)
        return DbRaceDataRepository(db_path)
    # 既定: json
    if data_dir is None:
        from kyotei_predictor.config.settings import Settings
        data_dir = Path(Settings.PROJECT_ROOT) / Settings.RAW_DATA_DIR
    return JsonRaceDataRepository(Path(data_dir))
