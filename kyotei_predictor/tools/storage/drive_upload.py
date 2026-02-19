#!/usr/bin/env python3
"""
Google Drive API でローカルフォルダを Drive にアップロードするツール。

Cursor Web など、Drive がマウントされていない環境で取得したデータを
Google Drive に保存するときに使います。

依存（別途インストール）:
  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

準備:
  1. Google Cloud Console で Drive API を有効化し、OAuth 2.0 クライアント ID（デスクトップ）を作成
  2. ダウンロードした JSON を credentials.json としてプロジェクトルートに置く
  3. 初回: python -m kyotei_predictor.tools.storage.drive_upload --auth-only
  4. 以降: python -m kyotei_predictor.tools.storage.drive_upload --local-dir kyotei_predictor/data/raw --drive-folder-name "kyotei_prediction/data/raw"
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# プロジェクトルート（このファイルの 4 階層上）
STORAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = STORAGE_DIR.parent.parent.parent
CREDENTIALS_PATH = PROJECT_ROOT / "credentials.json"
TOKEN_PATH = PROJECT_ROOT / "token.json"

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def _ensure_deps():
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError as e:
        print("必要なパッケージをインストールしてください:", file=sys.stderr)
        print("  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib", file=sys.stderr)
        raise SystemExit(1) from e


def get_drive_service(credentials_path: Path | None = None, token_path: Path | None = None):
    """OAuth2 で認証し、Drive API のサービスオブジェクトを返す。"""
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    credentials_path = credentials_path or CREDENTIALS_PATH
    token_path = token_path or TOKEN_PATH

    if not credentials_path.exists():
        print(f"credentials.json が見つかりません: {credentials_path}", file=sys.stderr)
        print("Google Cloud Console で OAuth 2.0 クライアント ID を作成し、JSON をダウンロードしてこのパスに保存してください。", file=sys.stderr)
        raise SystemExit(1)

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as f:
            f.write(creds.to_json())
    return build("drive", "v3", credentials=creds)


def get_or_create_folder(service, name: str, parent_id: str | None = None):
    """指定名のフォルダの ID を返す。なければ作成。parent_id は Drive のフォルダ ID（None のときはマイドライブ直下）。"""
    parent_id = parent_id or "root"
    q = f"name='{name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=q, spaces="drive", fields="files(id, name)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]
    meta = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id != "root":
        meta["parents"] = [parent_id]
    folder = service.files().create(body=meta, fields="id").execute()
    return folder["id"]


def ensure_drive_path(service, folder_path: str) -> str:
    """例: 'kyotei_prediction/data/raw' → そのパスを作成し、最後のフォルダ ID を返す。"""
    parts = [p for p in folder_path.replace("\\", "/").split("/") if p]
    parent_id = None
    for name in parts:
        parent_id = get_or_create_folder(service, name, parent_id)
    return parent_id or "root"


def upload_file(service, local_path: Path, drive_folder_id: str, rel_name: str) -> bool:
    """1 ファイルを Drive の指定フォルダにアップロード。"""
    from googleapiclient.http import MediaFileUpload

    mime = "application/octet-stream"
    if local_path.suffix.lower() == ".json":
        mime = "application/json"
    media = MediaFileUpload(str(local_path), mimetype=mime, resumable=True)
    meta = {"name": rel_name, "parents": [drive_folder_id]}
    try:
        service.files().create(body=meta, media_body=media, fields="id").execute()
        return True
    except Exception as e:
        print(f"  [skip] {rel_name}: {e}", file=sys.stderr)
        return False


def upload_dir(service, local_dir: Path, drive_folder_id: str, base_dir: Path) -> tuple[int, int]:
    """再帰的にフォルダをアップロード。戻り値は (成功数, 失敗数)。"""
    ok, ng = 0, 0
    for item in sorted(local_dir.iterdir()):
        rel = item.relative_to(base_dir)
        rel_str = str(rel).replace("\\", "/")
        if item.is_file():
            if upload_file(service, item, drive_folder_id, item.name):
                ok += 1
                print(f"  uploaded: {rel_str}")
            else:
                ng += 1
        else:
            sub_id = get_or_create_folder(service, item.name, drive_folder_id)
            o, n = upload_dir(service, item, sub_id, base_dir)
            ok += o
            ng += n
    return ok, ng


def main() -> None:
    _ensure_deps()
    parser = argparse.ArgumentParser(description="ローカルフォルダを Google Drive にアップロード（Cursor Web 向け）")
    parser.add_argument("--auth-only", action="store_true", help="認証のみ行い token.json を保存して終了")
    parser.add_argument("--local-dir", type=str, default="kyotei_predictor/data/raw", help="アップロードするローカルフォルダ")
    parser.add_argument("--drive-folder-name", type=str, default="kyotei_prediction/data/raw", help="Drive のマイドライブ直下からのフォルダパス")
    parser.add_argument("--credentials", type=str, default=None, help="credentials.json のパス（未指定時はプロジェクトルート）")
    parser.add_argument("--token", type=str, default=None, help="token.json のパス（未指定時はプロジェクトルート）")
    args = parser.parse_args()

    if args.auth_only:
        get_drive_service(
            Path(args.credentials) if args.credentials else None,
            Path(args.token) if args.token else None,
        )
        print("認証が完了しました。token.json が保存されています。")
        return

    local_dir = Path(args.local_dir).resolve()
    if not local_dir.is_dir():
        print(f"ローカルフォルダが見つかりません: {local_dir}", file=sys.stderr)
        raise SystemExit(1)

    service = get_drive_service(
        Path(args.credentials) if args.credentials else None,
        Path(args.token) if args.token else None,
    )
    folder_id = ensure_drive_path(service, args.drive_folder_name)
    print(f"アップロード先: Drive の {args.drive_folder_name}")
    ok, ng = upload_dir(service, local_dir, folder_id, local_dir)
    print(f"完了: 成功 {ok} 件, 失敗 {ng} 件")


if __name__ == "__main__":
    main()
