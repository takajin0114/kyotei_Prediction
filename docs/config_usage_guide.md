# 設定ファイル使用ガイド

## 概要

3連単的中率改善策の各種パラメータを設定ファイルで管理することで、ソースコードを変更することなくパラメータ調整が可能になります。

## 📁 設定ファイル構成

### メイン設定ファイル
- **`kyotei_predictor/config/improvement_config.json`**: 改善策の全パラメータ
- **`kyotei_predictor/config/config.json`**: 基本設定（データパス・API・**ログ**・予測・バッチ等）
- **`kyotei_predictor/config/optuna_config.json`**: Optuna最適化設定
- **`kyotei_predictor/config/alert_config.json.sample`**: アラート（メール）通知のサンプル。コピーして `alert_config.json` として編集すると、scheduled_data_maintenance で利用される。無い場合はメール無効。

### プロジェクトルート・データパス（settings.py で一元管理）
- **`kyotei_predictor/config/settings.py`**: `Settings.PROJECT_ROOT`, `Settings.RAW_DATA_DIR`, `get_raw_data_dir()` 等を定義。ツール類はここから import してパスを揃える。
- 環境変数 `KYOTEI_RAW_DATA_DIR` で raw データディレクトリを上書き可能。

### ログの日時形式（config.json で一律管理）
`config.json` の `logging` に `format` と **`datefmt`** を指定すると、学習・バッチ・予測などの実行ログに共通で反映されます。

- **`datefmt`**: `"%Y-%m-%d %H:%M:%S"`（日時分秒）。変更すると `kyotei_predictor/utils/logger.py` 経由で全ログに適用されます。
- **`format`**: 例 `"%(asctime)s [%(levelname)s] %(name)s: %(message)s"`（`%(asctime)s` が datefmt でフォーマットされます）。

### 設定管理クラス
- **`kyotei_predictor/config/improvement_config_manager.py`**: 改善策設定の管理クラス

## 🚀 設定ファイルの使用方法

### 1. 設定管理クラスの基本使用

```python
from kyotei_predictor.config.improvement_config_manager import ImprovementConfigManager

# 設定管理クラスのインスタンスを作成
config_manager = ImprovementConfigManager()

# 報酬設計パラメータを取得
reward_params = config_manager.get_reward_params("phase1")
print(f"的中報酬倍率: {reward_params['win_multiplier']}")

# 学習パラメータを取得
learning_params = config_manager.get_learning_params("phase2", "normal")
print(f"学習ステップ数: {learning_params['total_timesteps']}")

# ハイパーパラメータ範囲を取得
hyperparams = config_manager.get_hyperparameters("phase2")
print(f"学習率範囲: {hyperparams['learning_rate']}")
```

### 2. 設定の動的変更

```python
# 設定を更新
updates = {
    "reward_design": {
        "phase1": {
            "win_multiplier": 1.7,  # 的中報酬を1.7倍に変更
            "partial_second_hit_reward": 15  # 2着的中報酬を15に変更
        }
    }
}

config_manager.update_config(updates)

# 更新後のパラメータを確認
updated_params = config_manager.get_reward_params("phase1")
print(f"更新後の的中報酬倍率: {updated_params['win_multiplier']}")
```

### 3. 設定の検証

```python
# 設定の妥当性を検証
is_valid = config_manager.validate_config()
if is_valid:
    print("設定が妥当です")
else:
    print("設定に問題があります")
```

## 📊 設定項目の詳細

### 1. 報酬設計パラメータ (`reward_design`)

```json
{
  "reward_design": {
    "phase1": {
      "win_multiplier": 1.5,              // 的中時の報酬倍率
      "partial_second_hit_reward": 10,    // 2着的中の報酬
      "partial_first_hit_penalty": -10,   // 1着的中のペナルティ
      "no_hit_penalty": -80               // 不的中のペナルティ
    },
    "original": {
      "win_multiplier": 1.2,              // 元の的中報酬倍率
      "partial_second_hit_reward": 0,     // 元の2着的中報酬
      "partial_first_hit_penalty": -20,   // 元の1着的中ペナルティ
      "no_hit_penalty": -100              // 元の不的中ペナルティ
    }
  }
}
```

### 2. 学習パラメータ (`learning_parameters`)

```json
{
  "learning_parameters": {
    "phase2": {
      "total_timesteps": 200000,          // 通常モードの学習ステップ数
      "n_eval_episodes": 5000,            // 通常モードの評価エピソード数
      "test_mode": {
        "total_timesteps": 20000,         // テストモードの学習ステップ数
        "n_eval_episodes": 200            // テストモードの評価エピソード数
      },
      "minimal_mode": {
        "total_timesteps": 5000,          // 最小限モードの学習ステップ数
        "n_eval_episodes": 50             // 最小限モードの評価エピソード数
      }
    }
  }
}
```

### 3. ハイパーパラメータ範囲 (`hyperparameters`)

```json
{
  "hyperparameters": {
    "phase2": {
      "learning_rate": {
        "min": 5e-6,                      // 学習率の最小値
        "max": 5e-3,                      // 学習率の最大値
        "log": true                       // 対数スケール
      },
      "batch_size": [64, 128, 256],       // バッチサイズの候補
      "n_steps": [2048, 4096, 8192],     // ステップ数の候補
      "gamma": {
        "min": 0.95,                      // 割引率の最小値
        "max": 0.999                      // 割引率の最大値
      }
    }
  }
}
```

### 4. アンサンブル学習パラメータ (`ensemble`)

```json
{
  "ensemble": {
    "phase3": {
      "n_models": 3,                      // アンサンブルするモデル数
      "weight_strategy": "performance_based", // 重み付け戦略
      "min_performance_threshold": 0.1    // 最小性能閾値
    }
  }
}
```

### 5. 継続的学習パラメータ (`continuous_learning`)

```json
{
  "continuous_learning": {
    "phase4": {
      "update_interval_hours": 24,        // 更新間隔（時間）
      "additional_steps": 50000,          // 追加学習ステップ数
      "backup_enabled": true,             // バックアップ有効
      "performance_threshold": 0.05        // 性能閾値
    }
  }
}
```

### 6. 性能監視パラメータ (`monitoring`)

```json
{
  "monitoring": {
    "targets": {
      "hit_rate": 4.0,                   // 的中率目標
      "reward_stability": 80.0,           // 報酬安定性目標
      "mean_reward": 30.0,               // 平均報酬目標
      "learning_efficiency": 25.0         // 学習効率目標
    },
    "alert_thresholds": {
      "hit_rate_drop": 0.5,              // 的中率低下アラート閾値
      "reward_instability": 20.0          // 報酬不安定性アラート閾値
    }
  }
}
```

## 🔧 実際の使用例

### 1. 報酬設計の調整

的中率を向上させるために報酬設計を調整する場合：

```python
# 設定ファイルを編集
updates = {
    "reward_design": {
        "phase1": {
            "win_multiplier": 1.8,        # 的中報酬を1.8倍に強化
            "partial_second_hit_reward": 20,  # 2着的中報酬を20に増加
            "partial_first_hit_penalty": -5,  # 1着的中ペナルティを-5に緩和
            "no_hit_penalty": -60         # 不的中ペナルティを-60に緩和
        }
    }
}

config_manager.update_config(updates)
```

### 2. 学習時間の調整

より深い学習を行うために学習時間を延長する場合：

```python
updates = {
    "learning_parameters": {
        "phase2": {
            "total_timesteps": 300000,    # 学習ステップ数を30万に延長
            "n_eval_episodes": 8000       # 評価エピソード数を8000に延長
        }
    }
}

config_manager.update_config(updates)
```

### 3. ハイパーパラメータ範囲の調整

より細かい調整を行うためにハイパーパラメータ範囲を調整する場合：

```python
updates = {
    "hyperparameters": {
        "phase2": {
            "learning_rate": {
                "min": 1e-6,              # 学習率の最小値を1e-6に調整
                "max": 1e-2,              # 学習率の最大値を1e-2に調整
                "log": true
            },
            "batch_size": [128, 256, 512], # バッチサイズの候補を調整
            "n_steps": [4096, 8192, 16384] # ステップ数の候補を調整
        }
    }
}

config_manager.update_config(updates)
```

## 🧪 テスト実行

### 設定ファイルの動作確認
```bash
cd tests/improvement_tests
python test_config_manager.py
```

### バッチファイルでの実行
```bash
# 基本パイプライン実行
.\run_learning_pipeline.bat --test

# 高度パイプライン実行
.\run_advanced_learning.bat --minimal --phase 1 --cleanup

# 本番実行
.\run_advanced_learning.bat --production --phase all
```

## ⚠️ 注意事項

1. **設定ファイルのバックアップ**: 重要な変更を行う前に設定ファイルをバックアップしてください
2. **設定の検証**: 変更後は必ず設定の妥当性を検証してください
3. **段階的な調整**: 一度に大幅な変更を行うのではなく、段階的に調整してください
4. **テスト実行**: 本格的な学習前に必ずテストモードで動作確認してください

## 📚 関連ドキュメント

- [改善戦略](trifecta_improvement_strategy.md)
- [実装状況](improvement_implementation_summary.md)
- [テスト結果](test_results_summary.md)

---

*最終更新: 2025年1月27日* 