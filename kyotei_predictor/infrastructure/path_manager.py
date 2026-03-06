"""
出力パス・プロジェクトルートの解決（I/O ・環境依存）。

相対パスをプロジェクトルート基準で解決する。
TODO: 設定ファイルでルートを上書き可能にする。
"""

from pathlib import Path

# パッケージルート（kyotei_predictor）の親をプロジェクトルートとする
_INFRA_DIR = Path(__file__).resolve().parent
_PACKAGE_ROOT = _INFRA_DIR.parent
PROJECT_ROOT = _PACKAGE_ROOT.parent


def resolve_path(path: Path, base: Path = PROJECT_ROOT) -> Path:
    """相対パスなら base 基準で絶対パスにし、絶対パスはそのまま返す。"""
    p = Path(path)
    if not p.is_absolute():
        return base / p
    return p
