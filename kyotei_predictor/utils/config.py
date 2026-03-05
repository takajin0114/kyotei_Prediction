#!/usr/bin/env python3
"""
統合設定管理クラス
"""
import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

class Config:
    """競艇予測システムの統合設定管理クラス"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Args:
            config_file: 設定ファイルのパス（未指定時はデフォルト）
        """
        self.config_file = config_file or self._get_default_config_path()
        self._config = self._load_config()
        self._env_overrides = self._load_env_overrides()
    
    def _get_default_config_path(self) -> str:
        """デフォルト設定ファイルのパスを取得"""
        base_dir = Path(__file__).parent.parent
        return str(base_dir / "config" / "config.json")
    
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self._get_default_config()
        except Exception as e:
            print(f"⚠️ 設定ファイル読み込みエラー: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """デフォルト設定を返す"""
        return {
            "data": {
                "raw_dir": "data/raw",
                "processed_dir": "data/processed",
                "output_dir": "outputs",
                "backup_dir": "data/backup"
            },
            "api": {
                "timeout": 30,
                "retry_count": 3,
                "retry_delay": 2
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "logs/kyotei_predictor.log"
            },
            "prediction": {
                "model_dir": "optuna_models",
                "results_dir": "optuna_results",
                "top_predictions": 20
            }
        }
    
    def _load_env_overrides(self) -> Dict[str, str]:
        """環境変数オーバーライドを読み込み"""
        overrides = {}
        env_prefix = "KYOTEI_"
        
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix):].lower()
                overrides[config_key] = value
        
        return overrides
    
    def get(self, key: str, default: Any = None) -> Any:
        """設定値を取得（ドット記法対応）。環境変数は KYOTEI_DATA_RAW_DIR のようにアンダースコアで格納されるため、両形式を参照する。"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                env_val = self._env_overrides.get(key) or self._env_overrides.get(key.replace(".", "_"))
                return env_val if env_val is not None else default
        
        env_val = self._env_overrides.get(key) or self._env_overrides.get(key.replace(".", "_"))
        return env_val if env_val is not None else value
    
    def get_data_dir(self) -> str:
        """データディレクトリを取得"""
        return self.get("data.raw_dir", "data/raw")
    
    def get_output_dir(self) -> str:
        """出力ディレクトリを取得"""
        return self.get("data.output_dir", "outputs")
    
    def get_log_level(self) -> str:
        """ログレベルを取得"""
        return self.get("logging.level", "INFO")
    
    def get_api_timeout(self) -> int:
        """APIタイムアウトを取得"""
        return int(self.get("api.timeout", 30))
    
    def get_retry_count(self) -> int:
        """リトライ回数を取得"""
        return int(self.get("api.retry_count", 3))
    
    def get_top_predictions(self) -> int:
        """上位予測数を取得"""
        return int(self.get("prediction.top_predictions", 20))
    
    def save_config(self) -> bool:
        """設定を保存"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"⚠️ 設定保存エラー: {e}")
            return False
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """設定を更新"""
        try:
            for key, value in updates.items():
                keys = key.split('.')
                config = self._config
                
                for k in keys[:-1]:
                    if k not in config:
                        config[k] = {}
                    config = config[k]
                
                config[keys[-1]] = value
            
            return self.save_config()
        except Exception as e:
            print(f"⚠️ 設定更新エラー: {e}")
            return False 