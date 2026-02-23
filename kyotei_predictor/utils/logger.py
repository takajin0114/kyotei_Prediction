#!/usr/bin/env python3
"""
統合ログ設定クラス
"""
import logging
import os
from datetime import datetime
from typing import Optional
from pathlib import Path

def setup_logger(
    name: str = "kyotei_predictor",
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    ログ設定をセットアップ
    
    Args:
        name: ロガー名
        level: ログレベル
        log_file: ログファイルパス（未指定時はコンソールのみ）
        format_string: ログフォーマット（未指定時はデフォルト）
    
    Returns:
        logging.Logger: 設定済みロガー
    """
    # ロガーを取得
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 既存のハンドラーをクリア
    logger.handlers.clear()
    
    # フォーマッターを設定
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    formatter = logging.Formatter(format_string)
    
    # コンソールハンドラーを追加
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # ファイルハンドラーを追加（指定された場合）
    if log_file:
        try:
            # ログディレクトリを作成
            log_dir = os.path.dirname(log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            logger.info(f"ログファイル設定完了: {log_file}")
        except Exception as e:
            logger.warning(f"ログファイル設定エラー: {e}")
    
    return logger

def create_timestamped_logger(
    base_name: str = "kyotei_predictor",
    log_dir: str = "logs"
) -> logging.Logger:
    """
    タイムスタンプ付きログファイルを作成
    
    Args:
        base_name: ログファイルのベース名
        log_dir: ログディレクトリ
    
    Returns:
        logging.Logger: 設定済みロガー
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"{base_name}_{timestamp}.log")
    
    return setup_logger(
        name=base_name,
        log_file=log_file
    )

# ログ出力先の既定ディレクトリ（プロジェクトルートの logs/ を想定）
DEFAULT_LOG_DIR = "logs"


def format_timestamp() -> str:
    """現在時刻を YYYY-MM-DD HH:MM:SS で返す（ログ用）"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def format_log_line(message: str) -> str:
    """1行ログを [日付 時:分:秒] 付きで返す。バッチ等の標準出力ログで共通利用。"""
    return f"[{format_timestamp()}] {message}"


def get_daily_log_path(prefix: str, log_dir: Optional[str] = None) -> str:
    """
    1日ごとのログファイルパスを返す。ディレクトリが無ければ作成する。
    例: prefix="batch_fetch" -> "logs/batch_fetch_2026-02-24.log"

    Args:
        prefix: ファイル名のプレフィックス（例: batch_fetch, retry_missing）
        log_dir: ログディレクトリ（未指定時は DEFAULT_LOG_DIR）

    Returns:
        絶対パスまたはカレント基準のログファイルパス
    """
    directory = log_dir if log_dir is not None else DEFAULT_LOG_DIR
    os.makedirs(directory, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(directory, f"{prefix}_{date_str}.log")


def get_logger(name: str = "kyotei_predictor") -> logging.Logger:
    """
    既存のロガーを取得（設定されていない場合はデフォルト設定）
    
    Args:
        name: ロガー名
    
    Returns:
        logging.Logger: ロガー
    """
    logger = logging.getLogger(name)
    
    # ハンドラーが設定されていない場合はデフォルト設定
    if not logger.handlers:
        setup_logger(name)
    
    return logger

class LoggerMixin:
    """ログ機能を提供するMixinクラス"""
    
    @property
    def logger(self) -> logging.Logger:
        """ロガーを取得"""
        return get_logger(self.__class__.__name__)
    
    def log_info(self, message: str):
        """情報ログを出力"""
        self.logger.info(message)
    
    def log_warning(self, message: str):
        """警告ログを出力"""
        self.logger.warning(message)
    
    def log_error(self, message: str):
        """エラーログを出力"""
        self.logger.error(message)
    
    def log_debug(self, message: str):
        """デバッグログを出力"""
        self.logger.debug(message) 