#!/usr/bin/env python3
"""
Google Drive（マウント済みディレクトリ）とのデータ同期ツール。

前提:
  - Colab 等で Google Drive がローカルパスとしてマウントされていること
  - 例: /content/drive/MyDrive/kyotei_prediction

利用例:
  # 取得データをDriveへ反映（push）
  python -m kyotei_predictor.tools.storage.drive_data_sync \
    --direction push \
    --local-dir kyotei_predictor/data/raw \
    --drive-dir /content/drive/MyDrive/kyotei_prediction/data/raw

  # Driveからローカルへ反映（pull）
  python -m kyotei_predictor.tools.storage.drive_data_sync \
    --direction pull \
    --local-dir kyotei_predictor/data/raw \
    --drive-dir /content/drive/MyDrive/kyotei_prediction/data/raw
"""

from __future__ import annotations

import argparse
import os
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SyncStats:
    scanned_files: int = 0
    copied_files: int = 0
    skipped_files: int = 0
    copied_bytes: int = 0


def _is_same_file(src: Path, dst: Path) -> bool:
    """サイズと更新時刻（秒）で同一判定"""
    if not dst.exists() or not dst.is_file():
        return False
    s_stat = src.stat()
    d_stat = dst.stat()
    if s_stat.st_size != d_stat.st_size:
        return False
    return int(s_stat.st_mtime) == int(d_stat.st_mtime)


def _iter_files(base_dir: Path):
    for p in base_dir.rglob("*"):
        if p.is_file():
            yield p


def sync_directories(src_dir: Path, dst_dir: Path) -> SyncStats:
    """
    src_dir -> dst_dir へ一方向同期（存在しない/更新されたファイルのみコピー）
    """
    stats = SyncStats()
    dst_dir.mkdir(parents=True, exist_ok=True)

    for src_file in _iter_files(src_dir):
        stats.scanned_files += 1
        rel = src_file.relative_to(src_dir)
        dst_file = dst_dir / rel
        dst_file.parent.mkdir(parents=True, exist_ok=True)

        if _is_same_file(src_file, dst_file):
            stats.skipped_files += 1
            continue

        shutil.copy2(src_file, dst_file)
        stats.copied_files += 1
        stats.copied_bytes += src_file.stat().st_size

    return stats


def _fmt_bytes(size: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size)
    unit_idx = 0
    while value >= 1024 and unit_idx < len(units) - 1:
        value /= 1024
        unit_idx += 1
    return f"{value:.2f}{units[unit_idx]}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Google Drive（マウント済み）同期ツール")
    parser.add_argument("--direction", choices=["push", "pull"], required=True, help="push: local->drive, pull: drive->local")
    parser.add_argument("--local-dir", required=True, help="ローカル側ディレクトリ")
    parser.add_argument("--drive-dir", required=True, help="Google Drive側ディレクトリ（マウント済みパス）")
    args = parser.parse_args()

    local_dir = Path(args.local_dir).expanduser().resolve()
    drive_dir = Path(args.drive_dir).expanduser().resolve()

    if args.direction == "push":
        src_dir, dst_dir = local_dir, drive_dir
    else:
        src_dir, dst_dir = drive_dir, local_dir

    if not src_dir.exists() or not src_dir.is_dir():
        raise FileNotFoundError(f"source directory not found: {src_dir}")

    print(f"[sync] direction={args.direction}")
    print(f"[sync] source={src_dir}")
    print(f"[sync] destination={dst_dir}")

    stats = sync_directories(src_dir, dst_dir)

    print("[sync] completed")
    print(f"  scanned_files: {stats.scanned_files}")
    print(f"  copied_files : {stats.copied_files}")
    print(f"  skipped_files: {stats.skipped_files}")
    print(f"  copied_size  : {_fmt_bytes(stats.copied_bytes)}")


if __name__ == "__main__":
    main()
