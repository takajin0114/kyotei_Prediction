import os
import sys
import signal
import subprocess

PID_FILE = os.path.join(os.path.dirname(__file__), "test_server.pid")

def stop_server():
    if not os.path.exists(PID_FILE):
        print("[INFO] test_server.pid が見つかりません。サーバーは既に停止している可能性があります。")
        return
    with open(PID_FILE, "r") as f:
        pid_str = f.read().strip()
    try:
        pid = int(pid_str)
    except ValueError:
        print(f"[ERROR] PIDの読み取りに失敗: {pid_str}")
        return
    print(f"[INFO] 停止対象のテストサーバーPID: {pid}")
    # WindowsとUNIXで分岐
    if os.name == "nt":
        # Windows: taskkill
        try:
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], check=True)
            print(f"[OK] サーバープロセス(PID={pid})を停止しました。")
        except Exception as e:
            print(f"[ERROR] サーバープロセスの停止に失敗: {e}")
    else:
        # UNIX: os.kill
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"[OK] サーバープロセス(PID={pid})にSIGTERMを送信しました。")
        except Exception as e:
            print(f"[ERROR] サーバープロセスの停止に失敗: {e}")
    # PIDファイル削除
    try:
        os.remove(PID_FILE)
    except Exception:
        pass

if __name__ == "__main__":
    stop_server() 