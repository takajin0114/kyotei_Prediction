#!/usr/bin/env python3
"""
統合設定ファイル
"""
import os
from pathlib import Path
from typing import Dict, Any

def get_project_root() -> Path:
    """プロジェクトルートを動的に検出"""
    # 現在のファイルの場所から遡ってプロジェクトルートを検出
    current_file = Path(__file__)
    
    # kyotei_predictor/config/settings.py から kyotei_Prediction/ まで遡る
    project_root = current_file.parent.parent.parent
    
    # Google Colab環境の検出
    if str(project_root).startswith('/content/'):
        # Colab環境では /content/kyotei_Prediction を使用
        return Path('/content/kyotei_Prediction')
    
    return project_root

class Settings:
    """競艇予測システムの設定クラス"""
    
    # プロジェクトルートを動的に取得
    PROJECT_ROOT = get_project_root()
    
    # 基本設定
    PROJECT_NAME = "kyotei_Prediction"
    VERSION = "Phase 3"
    
    # データディレクトリ（相対パス）
    DATA_DIR = "kyotei_predictor/data"
    RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
    PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
    SAMPLE_DATA_DIR = os.path.join(DATA_DIR, "sample")
    BACKUP_DATA_DIR = os.path.join(DATA_DIR, "backup")
    
    # 出力ディレクトリ（相対パス）
    OUTPUT_DIR = "kyotei_predictor/outputs"
    LOGS_DIR = "kyotei_predictor/logs"
    
    # Optuna関連（相対パス）
    OPTUNA_STUDIES_DIR = "optuna_studies"
    OPTUNA_LOGS_DIR = "optuna_logs"
    OPTUNA_MODELS_DIR = "optuna_models"
    OPTUNA_RESULTS_DIR = "optuna_results"
    OPTUNA_TENSORBOARD_DIR = "optuna_tensorboard"
    
    # Webアプリ設定
    FLASK_HOST = "localhost"
    FLASK_PORT = 12000
    FLASK_DEBUG = True
    
    # データ取得設定
    MAX_RACES_PER_VENUE = 1000
    REQUEST_DELAY = 1.0  # 秒
    MAX_RETRIES = 3
    
    # 予測モデル設定
    TRIFECTA_COMBINATIONS = 120  # 6P3 = 120通り
    DEFAULT_TEMPERATURE = 1.0
    MIN_PROBABILITY = 0.001
    
    # 投資分析設定
    DEFAULT_EXPECTED_VALUE_THRESHOLD = 1.0
    CONSERVATIVE_THRESHOLD = 1.5
    BALANCED_THRESHOLD = 1.2
    AGGRESSIVE_THRESHOLD = 1.0
    
    # 検証設定
    DEFAULT_VALIDATION_RACES = 1000
    CONFIDENCE_LEVEL = 0.95
    
    # ログ設定
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def get_project_root_path(cls) -> Path:
        """プロジェクトルートのPathオブジェクトを取得"""
        return cls.PROJECT_ROOT
    
    @classmethod
    def get_absolute_path(cls, relative_path: str) -> Path:
        """相対パスを絶対パスに変換"""
        return cls.PROJECT_ROOT / relative_path
    
    @classmethod
    def get_data_paths(cls) -> Dict[str, str]:
        """データパスの辞書を取得（絶対パス）"""
        return {
            'data_dir': str(cls.get_absolute_path(cls.DATA_DIR)),
            'raw_dir': str(cls.get_absolute_path(cls.RAW_DATA_DIR)),
            'processed_dir': str(cls.get_absolute_path(cls.PROCESSED_DATA_DIR)),
            'sample_dir': str(cls.get_absolute_path(cls.SAMPLE_DATA_DIR)),
            'backup_dir': str(cls.get_absolute_path(cls.BACKUP_DATA_DIR)),
            'output_dir': str(cls.get_absolute_path(cls.OUTPUT_DIR)),
            'logs_dir': str(cls.get_absolute_path(cls.LOGS_DIR))
        }
    
    @classmethod
    def get_optuna_paths(cls) -> Dict[str, str]:
        """Optunaパスの辞書を取得（絶対パス）"""
        return {
            'studies_dir': str(cls.get_absolute_path(cls.OPTUNA_STUDIES_DIR)),
            'logs_dir': str(cls.get_absolute_path(cls.OPTUNA_LOGS_DIR)),
            'models_dir': str(cls.get_absolute_path(cls.OPTUNA_MODELS_DIR)),
            'results_dir': str(cls.get_absolute_path(cls.OPTUNA_RESULTS_DIR)),
            'tensorboard_dir': str(cls.get_absolute_path(cls.OPTUNA_TENSORBOARD_DIR))
        }
    
    @classmethod
    def get_web_config(cls) -> Dict[str, Any]:
        """Webアプリ設定を取得"""
        return {
            'host': cls.FLASK_HOST,
            'port': cls.FLASK_PORT,
            'debug': cls.FLASK_DEBUG
        }
    
    @classmethod
    def get_model_config(cls) -> Dict[str, Any]:
        """予測モデル設定を取得"""
        return {
            'trifecta_combinations': cls.TRIFECTA_COMBINATIONS,
            'default_temperature': cls.DEFAULT_TEMPERATURE,
            'min_probability': cls.MIN_PROBABILITY
        }
    
    @classmethod
    def get_investment_config(cls) -> Dict[str, float]:
        """投資分析設定を取得"""
        return {
            'default_threshold': cls.DEFAULT_EXPECTED_VALUE_THRESHOLD,
            'conservative': cls.CONSERVATIVE_THRESHOLD,
            'balanced': cls.BALANCED_THRESHOLD,
            'aggressive': cls.AGGRESSIVE_THRESHOLD
        }
    
    @classmethod
    def create_directories(cls):
        """必要なディレクトリを作成"""
        directories = [
            cls.DATA_DIR,
            cls.RAW_DATA_DIR,
            cls.PROCESSED_DATA_DIR,
            cls.SAMPLE_DATA_DIR,
            cls.BACKUP_DATA_DIR,
            cls.OUTPUT_DIR,
            cls.LOGS_DIR,
            cls.OPTUNA_STUDIES_DIR,
            cls.OPTUNA_LOGS_DIR,
            cls.OPTUNA_MODELS_DIR,
            cls.OPTUNA_RESULTS_DIR,
            cls.OPTUNA_TENSORBOARD_DIR
        ]
        
        for directory in directories:
            abs_path = cls.get_absolute_path(directory)
            abs_path.mkdir(parents=True, exist_ok=True)

# 環境変数による設定オーバーライド
def get_env_settings() -> Dict[str, Any]:
    """環境変数から設定を取得"""
    return {
        'FLASK_HOST': os.getenv('FLASK_HOST', Settings.FLASK_HOST),
        'FLASK_PORT': int(os.getenv('FLASK_PORT', str(Settings.FLASK_PORT))),
        'FLASK_DEBUG': os.getenv('FLASK_DEBUG', 'True').lower() == 'true',
        'LOG_LEVEL': os.getenv('LOG_LEVEL', Settings.LOG_LEVEL),
        'REQUEST_DELAY': float(os.getenv('REQUEST_DELAY', str(Settings.REQUEST_DELAY))),
        'MAX_RETRIES': int(os.getenv('MAX_RETRIES', str(Settings.MAX_RETRIES)))
    }

# 環境変数設定を取得
env_settings = get_env_settings()

# 便利なエイリアス
config = Settings 