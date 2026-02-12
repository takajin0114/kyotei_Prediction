# PowerShell スクリプト

## 概要

最適化は **バッチ（.bat）** を推奨します。`scripts/run_optimization_config.bat` を利用してください。

PowerShell で実行する場合は、プロジェクトルートで以下と同等の操作をしてください。

```powershell
cd プロジェクトルート
.\venv\Scripts\Activate.ps1
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward --n-trials 20 --medium-mode --year-month 2024-02
```

## 実行ポリシー

スクリプトが実行できない場合:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 参照

- [batch_usage.md](batch_usage.md) - バッチの使い方
- [optimization_script.md](optimization_script.md) - 最適化の設定
