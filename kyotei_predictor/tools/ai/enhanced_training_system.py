"""
拡張学習システム

継続学習と段階的学習を統合した高度な学習システムを提供します。
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import time

from .continuous_learning_manager import ContinuousLearningManager
from .training_history_visualizer import TrainingHistoryVisualizer
from .curriculum_learning import CurriculumLearning, CurriculumStage


class EnhancedTrainingSystem:
    """拡張学習システム"""
    
    def __init__(self, 
                 model_dir: str = "optuna_models",
                 history_file: str = "training_history.json",
                 curriculum_file: str = "curriculum_config.json"):
        self.continuous_manager = ContinuousLearningManager(model_dir, history_file)
        self.visualizer = TrainingHistoryVisualizer(history_file)
        self.curriculum = CurriculumLearning(curriculum_file)
        self._latest_model_cache = None
        self._history_cache = None
        self._cache_timestamp = None
        logging.info("EnhancedTrainingSystem initialized")
    
    def _get_cached_latest_model(self):
        """キャッシュされた最新モデルを取得"""
        current_time = time.time()
        if (self._latest_model_cache is None or 
            self._cache_timestamp is None or 
            current_time - self._cache_timestamp > 60):  # 1分間キャッシュ
            self._latest_model_cache = self.continuous_manager.find_latest_model()
            self._cache_timestamp = current_time
        return self._latest_model_cache
    
    def _get_cached_history(self):
        """キャッシュされた履歴を取得"""
        current_time = time.time()
        if (self._history_cache is None or 
            self._cache_timestamp is None or 
            current_time - self._cache_timestamp > 60):  # 1分間キャッシュ
            self._history_cache = self.continuous_manager.get_training_history()
            self._cache_timestamp = current_time
        return self._history_cache
    
    def auto_continue_training(self, training_function: Callable, 
                              performance_evaluator: Optional[Callable] = None) -> bool:
        """自動継続学習の実行"""
        try:
            # 最新のモデルを検出
            latest_model = self._get_cached_latest_model()
            
            if latest_model:
                logging.info(f"Found latest model: {latest_model}")
                
                # 段階的学習の現在の段階を取得
                current_stage = self.curriculum.get_current_stage()
                if current_stage:
                    logging.info(f"Current curriculum stage: {current_stage.name}")
                    
                    # 段階固有のパラメータを取得
                    stage_params = self.curriculum.get_stage_parameters()
                    logging.info(f"Stage parameters: {stage_params}")
                
                # 学習を実行
                result = training_function()
                
                if result and performance_evaluator:
                    # 性能評価を実行
                    performance_metrics = performance_evaluator()
                    
                    # 継続学習の判定
                    should_continue = self.continuous_manager.should_continue_training(performance_metrics)
                    
                    # 段階的学習の完了判定
                    if self.curriculum.check_completion_criteria(performance_metrics):
                        self.curriculum.complete_current_stage(performance_metrics)
                        logging.info(f"Completed curriculum stage: {current_stage.name}")
                    
                    # 履歴を記録
                    self.continuous_manager.record_training_history(str(latest_model), performance_metrics)
                    
                    return should_continue
                
                return True
            else:
                logging.info("No existing model found, starting fresh training")
                return training_function()
                
        except Exception as e:
            logging.error(f"Error in auto_continue_training: {e}")
            return False
    
    def get_training_status(self) -> Dict[str, Any]:
        """学習状況を取得"""
        try:
            # 継続学習の状況
            latest_model = self._get_cached_latest_model()
            history = self._get_cached_history()
            
            continuous_learning_status = {
                'latest_model': str(latest_model) if latest_model else None,
                'history_count': len(history)
            }
            
            # 段階的学習の状況
            try:
                curriculum_summary = self.curriculum.get_curriculum_summary()
                current_stage = self.curriculum.get_current_stage()
                
                curriculum_learning_status = {
                    'total_stages': curriculum_summary.get('total_stages', 0),
                    'completed_stages': curriculum_summary.get('completed_stages', 0),
                    'current_stage_index': curriculum_summary.get('current_stage_index', 0),
                    'progress_percentage': curriculum_summary.get('progress_percentage', 0.0),
                    'current_stage': current_stage.name if current_stage else None,
                    'is_completed': current_stage.is_completed if current_stage else False
                }
            except Exception as e:
                logging.warning(f"段階的学習状況取得エラー: {e}")
                curriculum_learning_status = {
                    'total_stages': 0,
                    'completed_stages': 0,
                    'current_stage_index': 0,
                    'progress_percentage': 0.0,
                    'current_stage': None,
                    'is_completed': False
                }
            
            # 全体的な進捗
            try:
                overall_progress = self._calculate_overall_progress()
            except Exception as e:
                logging.warning(f"全体進捗計算エラー: {e}")
                overall_progress = {
                    'total_training_sessions': 0,
                    'completed_curriculum_stages': 0,
                    'total_curriculum_stages': 0,
                    'curriculum_completion_rate': 0.0
                }
            
            return {
                'continuous_learning': continuous_learning_status,
                'curriculum_learning': curriculum_learning_status,
                'overall_progress': overall_progress
            }
            
        except Exception as e:
            logging.error(f"学習状況取得中にエラーが発生: {e}")
            return {
                'continuous_learning': {'latest_model': None, 'history_count': 0},
                'curriculum_learning': {
                    'total_stages': 0, 'completed_stages': 0, 'current_stage_index': 0,
                    'progress_percentage': 0.0, 'current_stage': None, 'is_completed': False
                },
                'overall_progress': {
                    'total_training_sessions': 0, 'completed_curriculum_stages': 0,
                    'total_curriculum_stages': 0, 'curriculum_completion_rate': 0.0
                }
            }
    
    def _calculate_overall_progress(self) -> Dict[str, Any]:
        """全体の進捗を計算"""
        try:
            curriculum_progress = self.curriculum.get_progress()
            continuous_history = self._get_cached_history()
            
            total_sessions = len(continuous_history)
            completed_stages = curriculum_progress.get('completed_stages', 0)
            total_stages = curriculum_progress.get('total_stages', 0)
            
            return {
                'total_training_sessions': total_sessions,
                'completed_curriculum_stages': completed_stages,
                'total_curriculum_stages': total_stages,
                'curriculum_completion_rate': (completed_stages / total_stages * 100) if total_stages > 0 else 0
            }
        except Exception as e:
            logging.warning(f"全体進捗計算エラー: {e}")
            return {
                'total_training_sessions': 0,
                'completed_curriculum_stages': 0,
                'total_curriculum_stages': 0,
                'curriculum_completion_rate': 0.0
            }
    
    def visualize_training_progress(self, save_path: Optional[str] = None) -> bool:
        """学習進捗の可視化"""
        try:
            # 継続学習の可視化
            continuous_result = self.visualizer.plot_performance_trend(save_path)
            
            # 段階的学習の可視化
            curriculum_summary = self.curriculum.get_curriculum_summary()
            
            # 統合された可視化を作成
            if save_path:
                self._create_integrated_visualization(curriculum_summary, save_path)
            
            return continuous_result
        except Exception as e:
            logging.error(f"Error in visualize_training_progress: {e}")
            return False
    
    def _create_integrated_visualization(self, curriculum_summary: Dict[str, Any], save_path: str):
        """統合された可視化を作成"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib.patches as patches
            import warnings
            
            # フォント警告を完全に抑制
            warnings.filterwarnings('ignore', category=UserWarning)
            
            # matplotlibの設定でフォント警告を無効化
            plt.rcParams['font.family'] = 'DejaVu Sans'
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
            
            # 段階的学習の進捗
            stages = curriculum_summary['stages']
            stage_names = [stage['name'] for stage in stages]
            difficulty_levels = [stage['difficulty_level'] for stage in stages]
            is_completed = [stage['is_completed'] for stage in stages]
            
            colors = ['green' if completed else 'lightblue' for completed in is_completed]
            
            bars = ax1.bar(range(len(stages)), difficulty_levels, color=colors)
            ax1.set_title('Curriculum Learning Progress', fontsize=14)
            ax1.set_xlabel('Learning Stage')
            ax1.set_ylabel('Difficulty Level')
            ax1.set_xticks(range(len(stages)))
            ax1.set_xticklabels(stage_names, rotation=45)
            
            # 完了した段階にチェックマークを追加
            for i, completed in enumerate(is_completed):
                if completed:
                    ax1.text(i, difficulty_levels[i] + 0.05, '✓', 
                            ha='center', va='bottom', fontsize=16, color='green')
            
            # 全体の進捗
            progress = curriculum_summary['progress']
            progress_data = [
                progress['completed_stages'],
                progress['total_stages'] - progress['completed_stages']
            ]
            labels = ['Completed', 'Incomplete']
            colors = ['lightgreen', 'lightcoral']
            
            ax2.pie(progress_data, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax2.set_title('Curriculum Completion Rate', fontsize=14)
            
            plt.tight_layout()
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logging.info(f"Integrated visualization saved to {save_path}")
            
        except Exception as e:
            logging.error(f"Error creating integrated visualization: {e}")
    
    def export_training_data(self, export_path: str) -> bool:
        """学習データのエクスポート"""
        try:
            import json
            
            # 一度だけfind_latest_modelを呼び出し
            latest_model = self._get_cached_latest_model()
            
            # 学習状況を一度だけ取得
            training_status = self.get_training_status()
            
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'continuous_learning': {
                    'history': self._get_cached_history(),
                    'latest_model': str(latest_model) if latest_model else None
                },
                'curriculum_learning': self.curriculum.get_curriculum_summary(),
                'training_status': training_status
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logging.info(f"Training data exported to {export_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error exporting training data: {e}")
            return False
    
    def get_training_recommendations(self) -> List[str]:
        """学習の推奨事項を取得"""
        recommendations = []
        
        try:
            # 継続学習の推奨事項
            latest_model = self._get_cached_latest_model()
            if not latest_model:
                recommendations.append("Start new model training")
            
            # 段階的学習の推奨事項
            current_stage = self.curriculum.get_current_stage()
            if current_stage:
                if not current_stage.is_completed:
                    recommendations.append(f"Complete current stage \"{current_stage.name}\"")
                else:
                    next_stage = self.curriculum.get_next_stage()
                    if next_stage:
                        recommendations.append(f"Advance to next stage \"{next_stage.name}\"")
            
            # 全体的な推奨事項
            progress = self.curriculum.get_progress()
            progress_percentage = progress.get('progress_percentage', 0)
            if progress_percentage < 25:
                recommendations.append("Start curriculum learning to learn from basic to advanced stages")
            elif progress_percentage < 75:
                recommendations.append("Continue intermediate stage learning to aim for a more advanced model")
            else:
                recommendations.append("Continue advanced stage learning to aim for the optimal model")
                
        except Exception as e:
            logging.warning(f"Error getting training recommendations: {e}")
            recommendations.append("Check the initialization of the learning system")
        
        return recommendations
    
    def reset_training_system(self) -> bool:
        """学習システムのリセット"""
        try:
            # 段階的学習のリセット
            curriculum_reset = self.curriculum.reset_curriculum()
            
            # 継続学習の履歴クリア（オプション）
            # 注意: 実際のモデルファイルは削除されません
            
            logging.info("Training system reset completed")
            return curriculum_reset
            
        except Exception as e:
            logging.error(f"Error resetting training system: {e}")
            return False
    
    def get_adaptive_training_parameters(self, base_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """適応的学習パラメータを取得"""
        # 段階的学習のパラメータを取得
        curriculum_params = self.curriculum.get_adaptive_parameters(base_parameters)
        
        # 継続学習の状況に基づく調整
        latest_model = self._get_cached_latest_model()
        if latest_model:
            # 既存モデルがある場合、より慎重なパラメータを使用
            curriculum_params['learning_rate'] *= 0.8  # 学習率を下げる
            curriculum_params['batch_size'] = max(16, curriculum_params['batch_size'] // 2)  # バッチサイズを下げる
        
        return curriculum_params
    
    def create_custom_curriculum_stage(self, stage_config: Dict[str, Any]) -> bool:
        """カスタム段階を作成"""
        try:
            stage = CurriculumStage(
                stage_id=stage_config.get('stage_id', len(self.curriculum.stages) + 1),
                name=stage_config['name'],
                description=stage_config.get('description', ''),
                difficulty_level=stage_config.get('difficulty_level', 0.5),
                parameters=stage_config.get('parameters', {}),
                completion_criteria=stage_config.get('completion_criteria', {})
            )
            
            return self.curriculum.add_custom_stage(stage)
            
        except Exception as e:
            logging.error(f"Error creating custom curriculum stage: {e}")
            return False


def create_enhanced_training_system(model_dir: str = "optuna_models",
                                   history_file: str = "training_history.json",
                                   curriculum_file: str = "curriculum_config.json") -> EnhancedTrainingSystem:
    """拡張学習システムのファクトリ関数"""
    return EnhancedTrainingSystem(model_dir, history_file, curriculum_file) 