"""
継続学習管理システム

このモジュールは、競艇予測システムの継続学習を自動化し、
学習履歴を管理するための機能を提供します。
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContinuousLearningManager:
    """継続学習管理クラス"""
    
    def __init__(self, model_dir: str = "optuna_models", history_file: str = "training_history.json"):
        """
        初期化
        
        Args:
            model_dir: モデル保存ディレクトリ
            history_file: 学習履歴ファイル
        """
        self.model_dir = Path(model_dir)
        self.history_file = Path(history_file)
        self.performance_threshold = 0.01  # 性能改善の閾値
        
        # ディレクトリが存在しない場合は作成
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"ContinuousLearningManager initialized: model_dir={self.model_dir}, history_file={self.history_file}")
    
    def find_latest_model(self) -> Optional[Path]:
        """
        最新の学習済みモデルを検出
        
        Returns:
            最新モデルのパス、見つからない場合はNone
        """
        try:
            # モデルファイルを検索（.zipファイル）
            model_files = list(self.model_dir.glob("**/*.zip"))
            
            if not model_files:
                logger.debug("モデルファイルが見つかりません")
                return None
            
            # 最新のファイルを選択
            latest_model = max(model_files, key=lambda x: x.stat().st_mtime)
            logger.debug(f"最新モデルを検出: {latest_model}")
            return latest_model
            
        except Exception as e:
            logger.error(f"モデル検索中にエラーが発生: {e}")
            return None
    
    def get_model_info(self, model_path: Path) -> Dict[str, Any]:
        """
        モデルファイルの情報を取得
        
        Args:
            model_path: モデルファイルのパス
            
        Returns:
            モデル情報の辞書
        """
        try:
            stat = model_path.stat()
            return {
                'path': str(model_path),
                'size': stat.st_size,
                'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'created_time': datetime.fromtimestamp(stat.st_ctime).isoformat()
            }
        except Exception as e:
            logger.error(f"モデル情報取得中にエラーが発生: {e}")
            return {}
    
    def record_training_history(self, model_path: str, performance_metrics: Dict[str, Any]) -> bool:
        """
        学習履歴を記録
        
        Args:
            model_path: モデルパス
            performance_metrics: 性能指標
            
        Returns:
            記録成功時True
        """
        try:
            history_entry = {
                'model_path': model_path,
                'timestamp': datetime.now().isoformat(),
                'performance': performance_metrics,
                'parent_model': self._get_parent_model(),
                'training_parameters': self._get_training_parameters(),
                'data_version': self._get_data_version()
            }
            
            self._save_history(history_entry)
            logger.info(f"学習履歴を記録: {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"学習履歴記録中にエラーが発生: {e}")
            return False
    
    def should_continue_training(self, performance_metrics: Dict[str, Any]) -> bool:
        """
        継続学習すべきか判定
        
        Args:
            performance_metrics: 現在の性能指標
            
        Returns:
            継続学習すべき場合True
        """
        try:
            if not self.history_file.exists():
                logger.info("履歴ファイルが存在しないため、継続学習を推奨")
                return True
            
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            if not history:
                logger.info("履歴が空のため、継続学習を推奨")
                return True
            
            latest_performance = history[-1]['performance']
            current_performance = performance_metrics
            
            # 性能改善の判定
            improvement = (
                current_performance.get('mean_reward', 0) - 
                latest_performance.get('mean_reward', 0)
            )
            
            should_continue = improvement > self.performance_threshold
            logger.info(f"性能改善: {improvement:.4f}, 閾値: {self.performance_threshold}, 継続学習: {should_continue}")
            
            return should_continue
            
        except Exception as e:
            logger.error(f"継続学習判定中にエラーが発生: {e}")
            return True
    
    def get_training_lineage(self) -> List[Dict[str, Any]]:
        """
        学習系譜を取得
        
        Returns:
            学習履歴のリスト
        """
        try:
            if not self.history_file.exists():
                logger.debug("学習履歴ファイルが存在しません")
                return []
            
            with open(self.history_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
            if not content:
                logger.debug("学習履歴ファイルが空です")
                return []
                
            history = json.loads(content)
            logger.debug(f"学習履歴を読み込みました: {len(history)}件")
            return history
            
        except json.JSONDecodeError as e:
            logger.warning(f"学習履歴ファイルが破損しています: {e}")
            # 破損したファイルをバックアップして新規作成
            try:
                backup_file = self.history_file.with_suffix('.json.bak')
                if self.history_file.exists():
                    import shutil
                    shutil.copy2(self.history_file, backup_file)
                    logger.info(f"破損したファイルをバックアップしました: {backup_file}")
                
                # 新規ファイルを作成
                with open(self.history_file, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
                logger.info("新しい学習履歴ファイルを作成しました")
                return []
                
            except Exception as backup_error:
                logger.error(f"ファイル修復中にエラーが発生: {backup_error}")
                return []
                
        except Exception as e:
            logger.error(f"学習履歴読み込み中にエラーが発生: {e}")
            return []
    
    def get_training_history(self) -> List[Dict[str, Any]]:
        """
        学習履歴を取得（get_training_lineageのエイリアス）
        
        Returns:
            学習履歴のリスト
        """
        return self.get_training_lineage()
    
    def _get_parent_model(self) -> Optional[str]:
        """親モデルのパスを取得"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    if history:
                        return history[-1]['model_path']
            return None
        except Exception as e:
            logger.error(f"親モデル取得中にエラーが発生: {e}")
            return None
    
    def _get_training_parameters(self) -> Dict[str, Any]:
        """現在の学習パラメータを取得"""
        return {
            'learning_rate': 3e-4,
            'n_steps': 2048,
            'batch_size': 64,
            'n_epochs': 10,
            'gamma': 0.99,
            'gae_lambda': 0.95,
            'clip_range': 0.2,
            'ent_coef': 0.01,
            'vf_coef': 0.5,
            'max_grad_norm': 0.5
        }
    
    def _get_data_version(self) -> str:
        """データバージョンを取得"""
        return datetime.now().strftime("%Y%m")
    
    def _save_history(self, entry: Dict[str, Any]) -> None:
        """履歴を保存"""
        try:
            history = []
            if self.history_file.exists():
                try:
                    with open(self.history_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            history = json.loads(content)
                except (json.JSONDecodeError, Exception) as e:
                    logger.warning(f"既存の履歴ファイルを読み込めませんでした: {e}")
                    history = []
            
            history.append(entry)
            
            # ディレクトリが存在しない場合は作成
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
                
            logger.debug(f"学習履歴を保存しました: {len(history)}件")
                
        except Exception as e:
            logger.error(f"履歴保存中にエラーが発生: {e}")
            raise 