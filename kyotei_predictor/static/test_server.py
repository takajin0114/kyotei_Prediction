#!/usr/bin/env python3
"""
Web表示機能テスト用HTTPサーバー
予測結果のJSONファイルを静的ファイルとして提供
"""

import http.server
import socketserver
import os
import sys
import signal
from pathlib import Path

# プロジェクトルートの設定
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """カスタムHTTPリクエストハンドラー"""
    
    def __init__(self, *args, **kwargs):
        # 静的ファイルのルートディレクトリを設定
        super().__init__(*args, directory=str(PROJECT_ROOT), **kwargs)
    
    def end_headers(self):
        # CORSヘッダーを追加
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def log_message(self, format, *args):
        # ログメッセージをカスタマイズ
        print(f"[{self.log_date_time_string()}] {format % args}")

def main():
    """メイン関数"""
    PORT = 8000
    
    # 出力ディレクトリの存在確認
    outputs_dir = PROJECT_ROOT / "outputs"
    if not outputs_dir.exists():
        print(f"エラー: outputsディレクトリが見つかりません: {outputs_dir}")
        return
    
    # 予測結果ファイルの存在確認
    predictions_file = outputs_dir / "predictions_latest.json"
    if not predictions_file.exists():
        print(f"警告: 予測結果ファイルが見つかりません: {predictions_file}")
        print("予測ツールを実行してからWeb表示をテストしてください。")
    
    print(f"Web表示機能テストサーバーを起動中...")
    print(f"プロジェクトルート: {PROJECT_ROOT}")
    print(f"ポート: {PORT}")
    print(f"URL: http://localhost:{PORT}/kyotei_predictor/templates/predictions.html")
    print("終了するには Ctrl+C を押してください。")
    print("-" * 50)
    
    # PIDファイルの作成
    pid_file = os.path.join(os.path.dirname(__file__), "test_server.pid")
    with open(pid_file, "w") as f:
        f.write(str(os.getpid()))

    def cleanup(*args):
        if os.path.exists(pid_file):
            os.remove(pid_file)
        sys.exit(0)

    # Windows/UNIX両対応のためのシグナルハンドラ
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
            print(f"サーバーが起動しました: http://localhost:{PORT}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nサーバーを停止しました。")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"エラー: ポート {PORT} は既に使用されています。")
            print("他のプロセスを終了するか、別のポートを使用してください。")
        else:
            print(f"エラー: {e}")
    finally:
        cleanup()

if __name__ == "__main__":
    main() 