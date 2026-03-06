# domain.repositories: データ読込のインターフェース（I/O は infrastructure で実装）

from kyotei_predictor.domain.repositories.race_data_repository import (
    RaceDataRepositoryProtocol,
)

__all__ = ["RaceDataRepositoryProtocol"]
