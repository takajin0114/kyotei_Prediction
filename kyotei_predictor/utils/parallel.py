#!/usr/bin/env python3
"""
並列処理最適化モジュール
"""

import os
import time
import logging
from typing import List, Callable, Any, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from functools import wraps
import multiprocessing

logger = logging.getLogger(__name__)

class ParallelProcessor:
    """並列処理管理クラス"""
    
    def __init__(self, max_workers: Optional[int] = None, use_processes: bool = False):
        """
        初期化
        
        Args:
            max_workers: 最大ワーカー数（Noneの場合は自動設定）
            use_processes: プロセスプールを使用するか（デフォルトはスレッドプール）
        """
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self.use_processes = use_processes
        
        logger.info(f"並列処理初期化: {self.max_workers}ワーカー, {'プロセス' if use_processes else 'スレッド'}プール")
    
    def process_list(self, items: List[Any], func: Callable, 
                    chunk_size: int = 1, show_progress: bool = True) -> List[Any]:
        """
        リストの並列処理
        
        Args:
            items: 処理対象のリスト
            func: 処理関数
            chunk_size: チャンクサイズ
            show_progress: 進捗表示するか
        
        Returns:
            処理結果のリスト
        """
        if not items:
            return []
        
        executor_class = ProcessPoolExecutor if self.use_processes else ThreadPoolExecutor
        
        with executor_class(max_workers=self.max_workers) as executor:
            # タスクを分割
            if chunk_size > 1:
                chunks = [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]
                futures = [executor.submit(self._process_chunk, chunk, func) for chunk in chunks]
            else:
                futures = [executor.submit(func, item) for item in items]
            
            # 結果を収集
            results = []
            total = len(futures)
            
            for i, future in enumerate(as_completed(futures)):
                try:
                    result = future.result()
                    if chunk_size > 1:
                        results.extend(result)
                    else:
                        results.append(result)
                    
                    if show_progress:
                        progress = (i + 1) / total * 100
                        logger.info(f"並列処理進捗: {progress:.1f}% ({i + 1}/{total})")
                        
                except Exception as e:
                    logger.error(f"並列処理エラー: {e}")
                    if chunk_size > 1:
                        results.extend([None] * chunk_size)
                    else:
                        results.append(None)
            
            return results
    
    def _process_chunk(self, chunk: List[Any], func: Callable) -> List[Any]:
        """チャンク処理"""
        return [func(item) for item in chunk]
    
    def process_dict(self, data_dict: Dict[str, Any], func: Callable,
                    show_progress: bool = True) -> Dict[str, Any]:
        """
        辞書の並列処理
        
        Args:
            data_dict: 処理対象の辞書
            func: 処理関数
            show_progress: 進捗表示するか
        
        Returns:
            処理結果の辞書
        """
        if not data_dict:
            return {}
        
        keys = list(data_dict.keys())
        values = list(data_dict.values())
        
        executor_class = ProcessPoolExecutor if self.use_processes else ThreadPoolExecutor
        
        with executor_class(max_workers=self.max_workers) as executor:
            futures = {executor.submit(func, key, value): key for key, value in data_dict.items()}
            
            results = {}
            total = len(futures)
            
            for i, future in enumerate(as_completed(futures)):
                key = futures[future]
                try:
                    result = future.result()
                    results[key] = result
                    
                    if show_progress:
                        progress = (i + 1) / total * 100
                        logger.info(f"並列処理進捗: {progress:.1f}% ({i + 1}/{total})")
                        
                except Exception as e:
                    logger.error(f"並列処理エラー (キー: {key}): {e}")
                    results[key] = None
            
            return results

def parallelize(max_workers: Optional[int] = None, use_processes: bool = False):
    """
    関数を並列化するデコレータ
    
    Args:
        max_workers: 最大ワーカー数
        use_processes: プロセスプールを使用するか
    """
    def decorator(func):
        @wraps(func)
        def wrapper(items, *args, **kwargs):
            processor = ParallelProcessor(max_workers, use_processes)
            return processor.process_list(items, lambda item: func(item, *args, **kwargs))
        return wrapper
    return decorator

def batch_process(items: List[Any], func: Callable, batch_size: int = 10,
                  max_workers: Optional[int] = None, use_processes: bool = False) -> List[Any]:
    """
    バッチ処理
    
    Args:
        items: 処理対象のリスト
        func: 処理関数
        batch_size: バッチサイズ
        max_workers: 最大ワーカー数
        use_processes: プロセスプールを使用するか
    
    Returns:
        処理結果のリスト
    """
    processor = ParallelProcessor(max_workers, use_processes)
    return processor.process_list(items, func, chunk_size=batch_size)

def get_optimal_workers(cpu_intensive: bool = False) -> int:
    """
    最適なワーカー数を取得
    
    Args:
        cpu_intensive: CPU集約的な処理か
    
    Returns:
        最適なワーカー数
    """
    cpu_count = os.cpu_count() or 1
    
    if cpu_intensive:
        # CPU集約的な処理の場合はCPU数に基づく
        return cpu_count
    else:
        # I/O集約的な処理の場合はCPU数の2倍程度
        return min(32, cpu_count * 2)

def measure_performance(func: Callable, *args, **kwargs) -> Tuple[Any, float]:
    """
    関数の実行時間を測定
    
    Args:
        func: 測定対象の関数
        *args, **kwargs: 関数の引数
    
    Returns:
        (結果, 実行時間（秒）)のタプル
    """
    start_time = time.time()
    result = func(*args, **kwargs)
    execution_time = time.time() - start_time
    
    logger.info(f"関数 {func.__name__} の実行時間: {execution_time:.3f}秒")
    
    return result, execution_time

def optimize_parallel_processing(func: Callable, test_data: List[Any],
                               max_workers_range: Tuple[int, int] = (1, 16)) -> Dict[str, Any]:
    """
    並列処理の最適化
    
    Args:
        func: 最適化対象の関数
        test_data: テストデータ
        max_workers_range: テストするワーカー数の範囲
    
    Returns:
        最適化結果
    """
    results = {}
    
    for workers in range(max_workers_range[0], max_workers_range[1] + 1):
        processor = ParallelProcessor(max_workers=workers)
        
        start_time = time.time()
        processor.process_list(test_data, func, show_progress=False)
        execution_time = time.time() - start_time
        
        results[workers] = execution_time
        logger.info(f"ワーカー数 {workers}: {execution_time:.3f}秒")
    
    # 最適なワーカー数を特定
    optimal_workers = min(results, key=results.get)
    optimal_time = results[optimal_workers]
    
    return {
        'optimal_workers': optimal_workers,
        'optimal_time': optimal_time,
        'all_results': results
    }