"""
段階的学習システム

学習の難易度を段階的に上げていく機能を提供します。
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import numpy as np


@dataclass
class CurriculumStage:
    """段階的学習の各段階を表すデータクラス"""
    stage_id: int
    name: str
    description: str
    difficulty_level: float  # 0.0-1.0
    parameters: Dict[str, Any]  # 段階固有のパラメータ
    completion_criteria: Dict[str, Any]  # 完了条件
    is_completed: bool = False
    completed_at: Optional[str] = None
    performance_metrics: Optional[Dict[str, Any]] = None


class CurriculumLearning:
    """段階的学習システム"""
    
    def __init__(self, curriculum_file: str = "curriculum_config.json"):
        self.curriculum_file = Path(curriculum_file)
        self.stages: List[CurriculumStage] = []
        self.current_stage_index: int = 0
        self.curriculum_history: List[Dict[str, Any]] = []
        
        logging.info(f"CurriculumLearning initialized: curriculum_file={self.curriculum_file}")
        self._load_curriculum()
    
    def _load_curriculum(self) -> bool:
        """カリキュラム設定を読み込み"""
        try:
            if self.curriculum_file.exists():
                with open(self.curriculum_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.stages = []
                for stage_data in data.get('stages', []):
                    stage = CurriculumStage(**stage_data)
                    self.stages.append(stage)
                
                self.current_stage_index = data.get('current_stage_index', 0)
                self.curriculum_history = data.get('curriculum_history', [])
                
                logging.info(f"Loaded curriculum with {len(self.stages)} stages")
                return True
            else:
                logging.warning(f"Curriculum file not found: {self.curriculum_file}")
                return False
        except Exception as e:
            logging.error(f"Error loading curriculum: {e}")
            return False
    
    def _save_curriculum(self) -> bool:
        """カリキュラム設定を保存"""
        try:
            data = {
                'stages': [asdict(stage) for stage in self.stages],
                'current_stage_index': self.current_stage_index,
                'curriculum_history': self.curriculum_history
            }
            
            with open(self.curriculum_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logging.info(f"Saved curriculum to {self.curriculum_file}")
            return True
        except Exception as e:
            logging.error(f"Error saving curriculum: {e}")
            return False
    
    def create_default_curriculum(self) -> bool:
        """デフォルトのカリキュラムを作成"""
        self.stages = [
            CurriculumStage(
                stage_id=1,
                name="基礎学習",
                description="基本的な予測モデルの学習",
                difficulty_level=0.2,
                parameters={
                    "learning_rate": 0.001,
                    "batch_size": 32,
                    "epochs": 100,
                    "data_ratio": 0.3
                },
                completion_criteria={
                    "min_accuracy": 0.6,
                    "max_loss": 0.5,
                    "min_epochs": 50
                }
            ),
            CurriculumStage(
                stage_id=2,
                name="中級学習",
                description="より複雑な特徴量を使用した学習",
                difficulty_level=0.5,
                parameters={
                    "learning_rate": 0.0005,
                    "batch_size": 64,
                    "epochs": 200,
                    "data_ratio": 0.6
                },
                completion_criteria={
                    "min_accuracy": 0.7,
                    "max_loss": 0.4,
                    "min_epochs": 100
                }
            ),
            CurriculumStage(
                stage_id=3,
                name="上級学習",
                description="全データを使用した高度な学習",
                difficulty_level=0.8,
                parameters={
                    "learning_rate": 0.0001,
                    "batch_size": 128,
                    "epochs": 300,
                    "data_ratio": 1.0
                },
                completion_criteria={
                    "min_accuracy": 0.8,
                    "max_loss": 0.3,
                    "min_epochs": 150
                }
            ),
            CurriculumStage(
                stage_id=4,
                name="最適化学習",
                description="ハイパーパラメータ最適化による学習",
                difficulty_level=1.0,
                parameters={
                    "learning_rate": 0.00005,
                    "batch_size": 256,
                    "epochs": 500,
                    "data_ratio": 1.0,
                    "use_optimization": True
                },
                completion_criteria={
                    "min_accuracy": 0.85,
                    "max_loss": 0.25,
                    "min_epochs": 200
                }
            )
        ]
        
        self.current_stage_index = 0
        self.curriculum_history = []
        
        return self._save_curriculum()
    
    def get_current_stage(self) -> Optional[CurriculumStage]:
        """現在の段階を取得"""
        if 0 <= self.current_stage_index < len(self.stages):
            return self.stages[self.current_stage_index]
        return None
    
    def get_next_stage(self) -> Optional[CurriculumStage]:
        """次の段階を取得"""
        next_index = self.current_stage_index + 1
        if 0 <= next_index < len(self.stages):
            return self.stages[next_index]
        return None
    
    def get_stage_parameters(self) -> Dict[str, Any]:
        """現在の段階のパラメータを取得"""
        current_stage = self.get_current_stage()
        if current_stage:
            return current_stage.parameters.copy()
        return {}
    
    def check_completion_criteria(self, performance_metrics: Dict[str, Any]) -> bool:
        """完了条件をチェック"""
        current_stage = self.get_current_stage()
        if not current_stage:
            return False
        
        criteria = current_stage.completion_criteria
        
        # 精度チェック
        if 'min_accuracy' in criteria:
            accuracy = performance_metrics.get('accuracy', 0)
            if accuracy < criteria['min_accuracy']:
                return False
        
        # 損失チェック
        if 'max_loss' in criteria:
            loss = performance_metrics.get('loss', float('inf'))
            if loss > criteria['max_loss']:
                return False
        
        # エポック数チェック
        if 'min_epochs' in criteria:
            epochs = performance_metrics.get('epochs', 0)
            if epochs < criteria['min_epochs']:
                return False
        
        return True
    
    def complete_current_stage(self, performance_metrics: Dict[str, Any]) -> bool:
        """現在の段階を完了"""
        current_stage = self.get_current_stage()
        if not current_stage:
            return False
        
        # 完了条件をチェック
        if not self.check_completion_criteria(performance_metrics):
            logging.warning(f"Stage {current_stage.name} does not meet completion criteria")
            return False
        
        # 段階を完了としてマーク
        current_stage.is_completed = True
        current_stage.completed_at = datetime.now().isoformat()
        current_stage.performance_metrics = performance_metrics.copy()
        
        # 履歴に記録
        history_entry = {
            'stage_id': current_stage.stage_id,
            'stage_name': current_stage.name,
            'completed_at': current_stage.completed_at,
            'performance_metrics': performance_metrics.copy(),
            'difficulty_level': current_stage.difficulty_level
        }
        self.curriculum_history.append(history_entry)
        
        # 次の段階に進む
        self.current_stage_index += 1
        
        logging.info(f"Completed stage: {current_stage.name}")
        return self._save_curriculum()
    
    def is_curriculum_completed(self) -> bool:
        """カリキュラムが完了したかチェック"""
        return self.current_stage_index >= len(self.stages)
    
    def get_progress(self) -> Dict[str, Any]:
        """学習進捗を取得"""
        total_stages = len(self.stages)
        completed_stages = sum(1 for stage in self.stages if stage.is_completed)
        current_stage = self.get_current_stage()
        
        return {
            'total_stages': total_stages,
            'completed_stages': completed_stages,
            'current_stage_index': self.current_stage_index,
            'progress_percentage': (completed_stages / total_stages * 100) if total_stages > 0 else 0,
            'current_stage': current_stage.name if current_stage else None,
            'is_completed': self.is_curriculum_completed()
        }
    
    def get_curriculum_summary(self) -> Dict[str, Any]:
        """カリキュラムの概要を取得"""
        progress = self.get_progress()
        
        return {
            'progress': progress,
            'stages': [
                {
                    'id': stage.stage_id,
                    'name': stage.name,
                    'description': stage.description,
                    'difficulty_level': stage.difficulty_level,
                    'is_completed': stage.is_completed,
                    'completed_at': stage.completed_at,
                    'performance_metrics': stage.performance_metrics
                }
                for stage in self.stages
            ],
            'history': self.curriculum_history
        }
    
    def reset_curriculum(self) -> bool:
        """カリキュラムをリセット"""
        for stage in self.stages:
            stage.is_completed = False
            stage.completed_at = None
            stage.performance_metrics = None
        
        self.current_stage_index = 0
        self.curriculum_history = []
        
        logging.info("Curriculum reset")
        return self._save_curriculum()
    
    def add_custom_stage(self, stage: CurriculumStage) -> bool:
        """カスタム段階を追加"""
        self.stages.append(stage)
        logging.info(f"Added custom stage: {stage.name}")
        return self._save_curriculum()
    
    def get_adaptive_parameters(self, base_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """適応的パラメータを取得"""
        current_stage = self.get_current_stage()
        if not current_stage:
            return base_parameters
        
        # 段階の難易度に基づいてパラメータを調整
        difficulty = current_stage.difficulty_level
        
        adaptive_params = base_parameters.copy()
        
        # 学習率の調整
        if 'learning_rate' in adaptive_params:
            adaptive_params['learning_rate'] *= (1 - difficulty * 0.5)
        
        # バッチサイズの調整
        if 'batch_size' in adaptive_params:
            adaptive_params['batch_size'] = int(adaptive_params['batch_size'] * (1 + difficulty))
        
        # エポック数の調整
        if 'epochs' in adaptive_params:
            adaptive_params['epochs'] = int(adaptive_params['epochs'] * (1 + difficulty * 0.5))
        
        return adaptive_params 