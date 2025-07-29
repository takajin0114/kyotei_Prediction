#!/usr/bin/env python3
"""
キャッシュ機能モジュール
"""

import os
import json
import time
import hashlib
from typing import Dict, Any, Optional, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """キャッシュ管理クラス"""
    
    def __init__(self, cache_dir: str = "cache", max_size_mb: int = 100):
        """
        初期化
        
        Args:
            cache_dir: キャッシュディレクトリ
            max_size_mb: 最大キャッシュサイズ（MB）
        """
        self.cache_dir = Path(cache_dir)
        self.max_size_mb = max_size_mb
        self.cache_dir.mkdir(exist_ok=True)
        
        # メモリキャッシュ
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"キャッシュマネージャー初期化: {cache_dir}")
    
    def _generate_cache_key(self, data: Any) -> str:
        """キャッシュキーを生成"""
        if isinstance(data, str):
            content = data
        else:
            content = json.dumps(data, sort_keys=True, ensure_ascii=False)
        
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def get(self, key: str, max_age_seconds: int = 3600) -> Optional[Any]:
        """
        キャッシュからデータを取得
        
        Args:
            key: キャッシュキー
            max_age_seconds: 最大有効期間（秒）
        
        Returns:
            キャッシュされたデータ、またはNone
        """
        try:
            # メモリキャッシュをチェック
            if key in self.memory_cache:
                cache_data = self.memory_cache[key]
                if time.time() - cache_data['timestamp'] < max_age_seconds:
                    logger.debug(f"メモリキャッシュヒット: {key}")
                    return cache_data['data']
                else:
                    del self.memory_cache[key]
            
            # ファイルキャッシュをチェック
            cache_file = self.cache_dir / f"{key}.json"
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                if time.time() - cache_data['timestamp'] < max_age_seconds:
                    # メモリキャッシュに追加
                    self.memory_cache[key] = cache_data
                    logger.debug(f"ファイルキャッシュヒット: {key}")
                    return cache_data['data']
                else:
                    # 期限切れキャッシュを削除
                    cache_file.unlink()
            
            return None
            
        except Exception as e:
            logger.error(f"キャッシュ取得エラー: {e}")
            return None
    
    def set(self, key: str, data: Any, max_age_seconds: int = 3600) -> bool:
        """
        データをキャッシュに保存
        
        Args:
            key: キャッシュキー
            data: 保存するデータ
            max_age_seconds: 有効期間（秒）
        
        Returns:
            保存成功時True
        """
        try:
            cache_data = {
                'data': data,
                'timestamp': time.time(),
                'max_age': max_age_seconds
            }
            
            # メモリキャッシュに保存
            self.memory_cache[key] = cache_data
            
            # ファイルキャッシュに保存
            cache_file = self.cache_dir / f"{key}.json"
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            # キャッシュサイズチェック
            self._cleanup_cache()
            
            logger.debug(f"キャッシュ保存: {key}")
            return True
            
        except Exception as e:
            logger.error(f"キャッシュ保存エラー: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        キャッシュを削除
        
        Args:
            key: キャッシュキー
        
        Returns:
            削除成功時True
        """
        try:
            # メモリキャッシュから削除
            if key in self.memory_cache:
                del self.memory_cache[key]
            
            # ファイルキャッシュから削除
            cache_file = self.cache_dir / f"{key}.json"
            if cache_file.exists():
                cache_file.unlink()
            
            logger.debug(f"キャッシュ削除: {key}")
            return True
            
        except Exception as e:
            logger.error(f"キャッシュ削除エラー: {e}")
            return False
    
    def clear(self) -> bool:
        """
        全キャッシュをクリア
        
        Returns:
            クリア成功時True
        """
        try:
            # メモリキャッシュをクリア
            self.memory_cache.clear()
            
            # ファイルキャッシュをクリア
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            
            logger.info("全キャッシュをクリアしました")
            return True
            
        except Exception as e:
            logger.error(f"キャッシュクリアエラー: {e}")
            return False
    
    def _cleanup_cache(self):
        """キャッシュサイズをチェックしてクリーンアップ"""
        try:
            total_size = 0
            cache_files = []
            
            # ファイルサイズを計算
            for cache_file in self.cache_dir.glob("*.json"):
                size = cache_file.stat().st_size
                total_size += size
                cache_files.append((cache_file, size))
            
            # MBに変換
            total_size_mb = total_size / (1024 * 1024)
            
            if total_size_mb > self.max_size_mb:
                # 古いファイルから削除
                cache_files.sort(key=lambda x: x[0].stat().st_mtime)
                
                for cache_file, size in cache_files:
                    cache_file.unlink()
                    total_size_mb -= size / (1024 * 1024)
                    
                    if total_size_mb <= self.max_size_mb:
                        break
                
                logger.info(f"キャッシュクリーンアップ完了: {total_size_mb:.2f}MB")
                
        except Exception as e:
            logger.error(f"キャッシュクリーンアップエラー: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        キャッシュ統計を取得
        
        Returns:
            キャッシュ統計情報
        """
        try:
            memory_count = len(self.memory_cache)
            file_count = len(list(self.cache_dir.glob("*.json")))
            
            total_size = 0
            for cache_file in self.cache_dir.glob("*.json"):
                total_size += cache_file.stat().st_size
            
            return {
                'memory_cache_count': memory_count,
                'file_cache_count': file_count,
                'total_size_mb': total_size / (1024 * 1024),
                'max_size_mb': self.max_size_mb
            }
            
        except Exception as e:
            logger.error(f"キャッシュ統計取得エラー: {e}")
            return {}

# グローバルキャッシュマネージャー
_cache_manager: Optional[CacheManager] = None

def get_cache_manager() -> CacheManager:
    """グローバルキャッシュマネージャーを取得"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager

def cache_result(max_age_seconds: int = 3600):
    """
    関数結果をキャッシュするデコレータ
    
    Args:
        max_age_seconds: キャッシュ有効期間（秒）
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()
            
            # キャッシュキーを生成
            cache_key = f"{func.__name__}_{cache_manager._generate_cache_key((args, kwargs))}"
            
            # キャッシュから取得を試行
            cached_result = cache_manager.get(cache_key, max_age_seconds)
            if cached_result is not None:
                return cached_result
            
            # 関数を実行
            result = func(*args, **kwargs)
            
            # 結果をキャッシュに保存
            cache_manager.set(cache_key, result, max_age_seconds)
            
            return result
        return wrapper
    return decorator