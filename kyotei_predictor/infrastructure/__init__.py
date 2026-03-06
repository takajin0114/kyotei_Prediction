# infrastructure: I/O ・環境依存処理（config 読込、ファイル保存、パス解決）
# domain / application から利用される。CLI は含めない。

from kyotei_predictor.infrastructure.file_loader import load_json

__all__ = ["load_json"]
