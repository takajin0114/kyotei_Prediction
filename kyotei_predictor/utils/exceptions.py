#!/usr/bin/env python3
"""
統合エラーハンドリングクラス
"""
from typing import Dict, Any, Optional
import traceback
import sys

class KyoteiError(Exception):
    """競艇予測システムの基本例外クラス"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """エラー情報を辞書形式で返す"""
        return {
            'error': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code,
            'details': self.details
        }

class DataError(KyoteiError):
    """データ関連エラー"""
    pass

class APIError(KyoteiError):
    """API関連エラー"""
    pass

class ValidationError(KyoteiError):
    """バリデーションエラー"""
    pass

class ConfigError(KyoteiError):
    """設定関連エラー"""
    pass

class PredictionError(KyoteiError):
    """予測関連エラー"""
    pass

def handle_exception(func):
    """例外処理デコレータ"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KyoteiError as e:
            print(f"⚠️ {e.__class__.__name__}: {e.message}")
            if e.details:
                print(f"   詳細: {e.details}")
            return None
        except Exception as e:
            print(f"❌ 予期しないエラー: {e}")
            print(f"   トレースバック: {traceback.format_exc()}")
            return None
    return wrapper

def safe_execute(func, *args, **kwargs):
    """安全な関数実行"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"⚠️ 実行エラー: {e}")
        return None

class ErrorHandler:
    """エラーハンドリング管理クラス"""
    
    def __init__(self):
        self.error_count = 0
        self.error_log = []
    
    def log_error(self, error: Exception, context: Optional[str] = None):
        """エラーをログに記録"""
        error_info = {
            'type': type(error).__name__,
            'message': str(error),
            'context': context,
            'traceback': traceback.format_exc()
        }
        self.error_log.append(error_info)
        self.error_count += 1
    
    def get_error_summary(self) -> Dict[str, Any]:
        """エラーサマリーを取得"""
        return {
            'total_errors': self.error_count,
            'recent_errors': self.error_log[-10:] if self.error_log else []
        }
    
    def clear_errors(self):
        """エラーログをクリア"""
        self.error_count = 0
        self.error_log.clear()
    
    def raise_if_too_many_errors(self, max_errors: int = 10):
        """エラー数が上限を超えた場合に例外を発生"""
        if self.error_count >= max_errors:
            raise KyoteiError(
                f"エラー数が上限({max_errors})を超えました",
                error_code="TOO_MANY_ERRORS",
                details={'error_count': self.error_count}
            )

# グローバルエラーハンドラー
global_error_handler = ErrorHandler()

def get_error_handler() -> ErrorHandler:
    """グローバルエラーハンドラーを取得"""
    return global_error_handler 