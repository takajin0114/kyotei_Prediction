import os
import numpy as np
from kyotei_predictor.tools.optimization.optimize_graduated_reward import safe_savez

print("=== safe_savez テスト開始 ===")

# 1. 正常なパスでの保存
try:
    arr = np.arange(10)
    path = "outputs/test_safe_savez1.npz"
    safe_savez(path, arr=arr)
    print(f"✓ 正常保存成功: {path}")
except Exception as e:
    print(f"❌ 正常保存失敗: {e}")

# 2. 存在しないディレクトリでの保存
try:
    arr = np.arange(5)
    path = "outputs/test_dir2/test_safe_savez2.npz"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    safe_savez(path, arr=arr)
    print(f"✓ ディレクトリ自動作成＋保存成功: {path}")
except Exception as e:
    print(f"❌ ディレクトリ作成＋保存失敗: {e}")

# 3. 故意に失敗させる（ファイル名に不正文字を含める）
try:
    arr = np.arange(3)
    # Windowsで不正なファイル名
    path = "outputs/test_safe_savez3:invalid?.npz"
    safe_savez(path, arr=arr)
    print(f"❌ 失敗すべきケースで成功してしまった: {path}")
except Exception as e:
    print(f"✓ 失敗時の例外発生を確認: {e}")

print("=== safe_savez テスト終了 ===") 