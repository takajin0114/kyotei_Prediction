#!/usr/bin/env python3
"""
メモリ使用量最適化モジュール
"""

import os
import sys
import gc
import psutil
import logging
from typing import Dict, Any, Optional, List, Callable
from functools import wraps
import time

logger = logging.getLogger(__name__)

class MemoryMonitor:
    """メモリ監視クラス"""
    
    def __init__(self):
        """初期化"""
        self.process = psutil.Process(os.getpid())
        self.initial_memory = self.get_memory_usage()
        
        logger.info(f"メモリ監視開始: {self.initial_memory:.2f}MB")
    
    def get_memory_usage(self) -> float:
        """
        現在のメモリ使用量を取得（MB）
        
        Returns:
            メモリ使用量（MB）
        """
        try:
            memory_info = self.process.memory_info()
            return memory_info.rss / 1024 / 1024  # bytes to MB
        except Exception as e:
            logger.error(f"メモリ使用量取得エラー: {e}")
            return 0.0
    
    def get_memory_percentage(self) -> float:
        """
        メモリ使用率を取得（%）
        
        Returns:
            メモリ使用率（%）
        """
        try:
            return self.process.memory_percent()
        except Exception as e:
            logger.error(f"メモリ使用率取得エラー: {e}")
            return 0.0
    
    def get_system_memory_info(self) -> Dict[str, Any]:
        """
        システムメモリ情報を取得
        
        Returns:
            システムメモリ情報
        """
        try:
            memory = psutil.virtual_memory()
            return {
                'total_mb': memory.total / 1024 / 1024,
                'available_mb': memory.available / 1024 / 1024,
                'used_mb': memory.used / 1024 / 1024,
                'percent': memory.percent
            }
        except Exception as e:
            logger.error(f"システムメモリ情報取得エラー: {e}")
            return {}
    
    def log_memory_usage(self, label: str = ""):
        """
        メモリ使用量をログに記録
        
        Args:
            label: ラベル
        """
        current_memory = self.get_memory_usage()
        memory_diff = current_memory - self.initial_memory
        
        logger.info(f"メモリ使用量 {label}: {current_memory:.2f}MB (差分: {memory_diff:+.2f}MB)")
    
    def check_memory_threshold(self, threshold_mb: float = 1000) -> bool:
        """
        メモリ使用量が閾値を超えているかチェック
        
        Args:
            threshold_mb: 閾値（MB）
        
        Returns:
            閾値を超えている場合True
        """
        current_memory = self.get_memory_usage()
        return current_memory > threshold_mb

class MemoryOptimizer:
    """メモリ最適化クラス"""
    
    def __init__(self):
        """初期化"""
        self.monitor = MemoryMonitor()
    
    def optimize_memory(self, force_gc: bool = True) -> Dict[str, Any]:
        """
        メモリ最適化を実行
        
        Args:
            force_gc: 強制ガベージコレクションを実行するか
        
        Returns:
            最適化結果
        """
        before_memory = self.monitor.get_memory_usage()
        
        if force_gc:
            # ガベージコレクションを実行
            collected = gc.collect()
            logger.info(f"ガベージコレクション実行: {collected}オブジェクト回収")
        
        after_memory = self.monitor.get_memory_usage()
        memory_saved = before_memory - after_memory
        
        logger.info(f"メモリ最適化完了: {memory_saved:.2f}MB節約")
        
        return {
            'before_memory_mb': before_memory,
            'after_memory_mb': after_memory,
            'memory_saved_mb': memory_saved,
            'objects_collected': collected if force_gc else 0
        }
    
    def monitor_function(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """
        関数のメモリ使用量を監視
        
        Args:
            func: 監視対象の関数
            *args, **kwargs: 関数の引数
        
        Returns:
            監視結果
        """
        before_memory = self.monitor.get_memory_usage()
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            result = None
            success = False
            logger.error(f"関数実行エラー: {e}")
        
        after_memory = self.monitor.get_memory_usage()
        execution_time = time.time() - start_time
        memory_used = after_memory - before_memory
        
        logger.info(f"関数 {func.__name__} 監視結果:")
        logger.info(f"  実行時間: {execution_time:.3f}秒")
        logger.info(f"  メモリ使用量: {memory_used:.2f}MB")
        logger.info(f"  成功: {success}")
        
        return {
            'function_name': func.__name__,
            'success': success,
            'execution_time': execution_time,
            'memory_used_mb': memory_used,
            'before_memory_mb': before_memory,
            'after_memory_mb': after_memory,
            'result': result
        }

def memory_efficient(max_memory_mb: float = 1000):
    """
    メモリ効率的な関数実行デコレータ
    
    Args:
        max_memory_mb: 最大メモリ使用量（MB）
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            optimizer = MemoryOptimizer()
            
            # 実行前のメモリチェック
            if optimizer.monitor.check_memory_threshold(max_memory_mb):
                logger.warning(f"メモリ使用量が閾値を超えています: {optimizer.monitor.get_memory_usage():.2f}MB")
                optimizer.optimize_memory()
            
            # 関数実行
            result = optimizer.monitor_function(func, *args, **kwargs)
            
            # 実行後のメモリ最適化
            if result['memory_used_mb'] > max_memory_mb * 0.5:
                optimizer.optimize_memory()
            
            return result['result']
        return wrapper
    return decorator

def chunk_processing(items: List[Any], func: Callable, chunk_size: int = 100,
                    max_memory_mb: float = 1000) -> List[Any]:
    """
    メモリ効率的なチャンク処理
    
    Args:
        items: 処理対象のリスト
        func: 処理関数
        chunk_size: チャンクサイズ
        max_memory_mb: 最大メモリ使用量（MB）
    
    Returns:
        処理結果のリスト
    """
    optimizer = MemoryOptimizer()
    results = []
    
    for i in range(0, len(items), chunk_size):
        chunk = items[i:i + chunk_size]
        
        # チャンク処理
        chunk_results = [func(item) for item in chunk]
        results.extend(chunk_results)
        
        # メモリ最適化
        if optimizer.monitor.check_memory_threshold(max_memory_mb):
            optimizer.optimize_memory()
        
        logger.info(f"チャンク処理進捗: {min(i + chunk_size, len(items))}/{len(items)}")
    
    return results

def get_memory_info() -> Dict[str, Any]:
    """
    詳細なメモリ情報を取得
    
    Returns:
        メモリ情報
    """
    optimizer = MemoryOptimizer()
    
    return {
        'process_memory_mb': optimizer.monitor.get_memory_usage(),
        'process_memory_percent': optimizer.monitor.get_memory_percentage(),
        'system_memory': optimizer.monitor.get_system_memory_info(),
        'gc_stats': {
            'counts': gc.get_count(),
            'objects': len(gc.get_objects())
        }
    }

def optimize_large_data_structures(data: Any, max_size_mb: float = 100) -> Any:
    """
    大きなデータ構造の最適化
    
    Args:
        data: 最適化対象のデータ
        max_size_mb: 最大サイズ（MB）
    
    Returns:
        最適化されたデータ
    """
    optimizer = MemoryOptimizer()
    
    # データサイズを推定（簡易版）
    data_size = sys.getsizeof(data)
    
    if data_size > max_size_mb * 1024 * 1024:
        logger.warning(f"データサイズが大きすぎます: {data_size / 1024 / 1024:.2f}MB")
        
        # メモリ最適化を実行
        optimizer.optimize_memory()
        
        # データの簡略化を試行
        if isinstance(data, list) and len(data) > 1000:
            logger.info("リストサイズを削減します")
            data = data[:1000]  # 最初の1000要素のみ保持
        
        elif isinstance(data, dict) and len(data) > 1000:
            logger.info("辞書サイズを削減します")
            # 最初の1000キーのみ保持
            keys = list(data.keys())[:1000]
            data = {k: data[k] for k in keys}
    
    return data