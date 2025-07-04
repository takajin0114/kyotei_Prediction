"""
競艇予測エンジン - Phase 2: 中級アルゴリズム実装

このモジュールは競艇レースの予測を行うためのアルゴリズムを提供します。
段階的な実装により、基本的な勝率ベース予測から高度な分析まで対応します。

Phase 1: 基本アルゴリズム (完了)
- basic: シンプル勝率ベース
- rating_weighted: 級別重み付け

Phase 2: 中級アルゴリズム (実装中)
- equipment_focused: 機材重視アルゴリズム
- comprehensive: 総合評価アルゴリズム  
- relative_strength: 相対評価アルゴリズム

作成日: 2025-06-13
バージョン: 2.0 (Phase 2)
"""

import json
import time
from typing import Dict, List, Any, Optional, Tuple
import logging
from kyotei_predictor.pipelines.trifecta_probability import TrifectaProbabilityCalculator

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PredictionError(Exception):
    """予測エラーの基底クラス"""
    pass


class DataValidationError(PredictionError):
    """データ検証エラー"""
    pass


class AlgorithmError(PredictionError):
    """アルゴリズム実行エラー"""
    pass


class PredictionEngine:
    """
    競艇予測エンジンのメインクラス
    
    Phase 1では基本的なアルゴリズムを実装:
    - basic: シンプル勝率ベース
    - rating_weighted: 級別重み付け
    """
    
    def __init__(self):
        """予測エンジンの初期化"""
        self.algorithms = {
            'basic': self._basic_algorithm,
            'rating_weighted': self._rating_weighted_algorithm,
            'equipment_focused': self._equipment_focused_algorithm,
            'comprehensive': self._comprehensive_algorithm,
            'relative_strength': self._relative_strength_algorithm
        }
        
        # 級別係数の定義
        self.rating_coefficients = {
            'A1': 1.2,  # A1級（最上位）
            'A2': 1.1,  # A2級（上位）
            'B1': 1.0,  # B1級（標準）
            'B2': 0.9   # B2級（下位）
        }
        
        logger.info("🔧 PredictionEngine初期化完了")
        logger.info(f"   利用可能アルゴリズム: {list(self.algorithms.keys())}")
        logger.info(f"   級別係数: {self.rating_coefficients}")
    
    def predict(self, race_data: Dict[str, Any], algorithm: str = 'basic', 
                options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        予測実行のメインメソッド
        
        Args:
            race_data: レースデータ（DataIntegrationから取得）
            algorithm: 使用するアルゴリズム名
            options: アルゴリズム固有のオプション
        
        Returns:
            予測結果の辞書
        
        Raises:
            DataValidationError: データ検証エラー
            AlgorithmError: アルゴリズム実行エラー
        """
        start_time = time.time()
        
        try:
            # データ検証
            self._validate_race_data(race_data)
            
            # アルゴリズム存在確認
            if algorithm not in self.algorithms:
                raise AlgorithmError(f"未知のアルゴリズム: {algorithm}")
            
            # 予測実行
            logger.info(f"📊 予測開始: algorithm={algorithm}")
            predictions = self.algorithms[algorithm](race_data, options or {})
            
            # 結果の正規化と追加情報
            normalized_predictions = self._normalize_predictions(predictions)
            win_probabilities = self._calculate_win_probabilities(normalized_predictions)
            
            execution_time = time.time() - start_time
            
            # 結果の構築
            result = {
                'algorithm': algorithm,
                'execution_time': round(execution_time, 3),
                'race_info': self._extract_race_info(race_data),
                'predictions': self._format_predictions(normalized_predictions, win_probabilities),
                'summary': self._create_summary(normalized_predictions, win_probabilities),
                'validation': {
                    'data_quality': 'good',
                    'missing_fields': [],
                    'warnings': [],
                    'recommendation': '予測結果は信頼できます'
                },
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
            }
            
            logger.info(f"✅ 予測完了: {execution_time:.3f}秒")
            return result
            
        except Exception as e:
            logger.error(f"❌ 予測エラー: {str(e)}")
            raise
    
    def _validate_race_data(self, race_data: Dict[str, Any]) -> None:
        """
        レースデータの検証
        
        Args:
            race_data: 検証対象のレースデータ
        
        Raises:
            DataValidationError: データが不正な場合
        """
        required_fields = ['race_entries']
        
        for field in required_fields:
            if field not in race_data:
                raise DataValidationError(f"必須フィールドが不足: {field}")
        
        entries = race_data['race_entries']
        if not isinstance(entries, list) or len(entries) == 0:
            raise DataValidationError("race_entriesが空または不正な形式")
        
        # 各エントリーの検証
        for i, entry in enumerate(entries):
            required_entry_fields = ['pit_number', 'racer', 'performance']
            for field in required_entry_fields:
                if field not in entry:
                    raise DataValidationError(f"エントリー{i+1}に必須フィールドが不足: {field}")
            
            # 選手データの検証
            racer = entry['racer']
            if 'current_rating' not in racer:
                raise DataValidationError(f"エントリー{i+1}の選手に級別情報が不足")
            
            # 成績データの検証
            performance = entry['performance']
            required_perf_fields = ['rate_in_all_stadium', 'rate_in_event_going_stadium']
            for field in required_perf_fields:
                if field not in performance:
                    raise DataValidationError(f"エントリー{i+1}の成績に必須フィールドが不足: {field}")
        
        logger.info(f"✅ データ検証完了: {len(entries)}艇のデータが正常")
    
    def _basic_algorithm(self, race_data: Dict[str, Any], options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        基本アルゴリズム: シンプル勝率ベース
        
        計算式: 基本スコア = 全国勝率 × 0.6 + 当地勝率 × 0.4
        
        Args:
            race_data: レースデータ
            options: アルゴリズムオプション
        
        Returns:
            予測結果のリスト
        """
        predictions = []
        
        for entry in race_data['race_entries']:
            pit_number = entry['pit_number']
            racer = entry['racer']
            performance = entry['performance']
            
            # 勝率データの取得
            all_stadium_rate = performance['rate_in_all_stadium']
            local_rate = performance['rate_in_event_going_stadium']
            
            # 基本スコア計算
            basic_score = all_stadium_rate * 0.6 + local_rate * 0.4
            
            prediction = {
                'pit_number': pit_number,
                'racer_name': racer['name'],
                'rating': racer['current_rating'],
                'prediction_score': round(basic_score, 3),
                'details': {
                    'all_stadium_rate': all_stadium_rate,
                    'local_rate': local_rate,
                    'all_stadium_weight': 0.6,
                    'local_weight': 0.4,
                    'base_score': round(basic_score, 3)
                }
            }
            
            predictions.append(prediction)
        
        logger.info(f"📊 基本アルゴリズム完了: {len(predictions)}艇の予測")
        return predictions
    
    def _rating_weighted_algorithm(self, race_data: Dict[str, Any], options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        級別重み付けアルゴリズム
        
        計算式: 級別補正スコア = (全国勝率 × 0.6 + 当地勝率 × 0.4) × 級別係数
        
        Args:
            race_data: レースデータ
            options: アルゴリズムオプション
        
        Returns:
            予測結果のリスト
        """
        predictions = []
        
        for entry in race_data['race_entries']:
            pit_number = entry['pit_number']
            racer = entry['racer']
            performance = entry['performance']
            
            # 勝率データの取得
            all_stadium_rate = performance['rate_in_all_stadium']
            local_rate = performance['rate_in_event_going_stadium']
            rating = racer['current_rating']
            
            # 基本スコア計算
            basic_score = all_stadium_rate * 0.6 + local_rate * 0.4
            
            # 級別係数の適用
            rating_coefficient = self.rating_coefficients.get(rating, 1.0)
            final_score = basic_score * rating_coefficient
            
            prediction = {
                'pit_number': pit_number,
                'racer_name': racer['name'],
                'rating': rating,
                'prediction_score': round(final_score, 3),
                'details': {
                    'all_stadium_rate': all_stadium_rate,
                    'local_rate': local_rate,
                    'basic_score': round(basic_score, 3),
                    'rating_coefficient': rating_coefficient,
                    'final_score': round(final_score, 3)
                }
            }
            
            predictions.append(prediction)
        
        logger.info(f"📊 級別重み付けアルゴリズム完了: {len(predictions)}艇の予測")
        return predictions
    
    def _normalize_predictions(self, predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        予測結果の正規化（スコア順でソート）
        
        Args:
            predictions: 正規化前の予測結果
        
        Returns:
            正規化後の予測結果
        """
        # スコア順でソート（降順）
        sorted_predictions = sorted(predictions, key=lambda x: x['prediction_score'], reverse=True)
        
        # ランキング情報を追加
        for rank, prediction in enumerate(sorted_predictions, 1):
            prediction['predicted_rank'] = rank
        
        return sorted_predictions
    
    def _calculate_win_probabilities(self, predictions: List[Dict[str, Any]]) -> List[float]:
        """
        各艇の勝率を計算（ソフトマックス関数を使用）
        
        Args:
            predictions: 予測結果
        
        Returns:
            各艇の勝率リスト
        """
        import math
        
        scores = [pred['prediction_score'] for pred in predictions]
        
        # ソフトマックス関数で確率に変換
        exp_scores = [math.exp(score) for score in scores]
        sum_exp_scores = sum(exp_scores)
        probabilities = [exp_score / sum_exp_scores for exp_score in exp_scores]
        
        return [round(prob * 100, 1) for prob in probabilities]  # パーセント表示
    
    def _format_predictions(self, predictions: List[Dict[str, Any]], 
                          win_probabilities: List[float]) -> List[Dict[str, Any]]:
        """
        予測結果のフォーマット
        
        Args:
            predictions: 正規化済み予測結果
            win_probabilities: 勝率リスト
        
        Returns:
            フォーマット済み予測結果
        """
        formatted = []
        
        for i, prediction in enumerate(predictions):
            formatted_prediction = {
                'rank': prediction['predicted_rank'],
                'pit_number': prediction['pit_number'],
                'racer_name': prediction['racer_name'],
                'rating': prediction['rating'],
                'prediction_score': prediction['prediction_score'],
                'win_probability': win_probabilities[i],
                'confidence': self._calculate_confidence(prediction['prediction_score'], predictions),
                'details': prediction['details']
            }
            formatted.append(formatted_prediction)
        
        return formatted
    
    def _calculate_confidence(self, score: float, all_predictions: List[Dict[str, Any]]) -> str:
        """
        予測の信頼度を計算
        
        Args:
            score: 対象のスコア
            all_predictions: 全予測結果
        
        Returns:
            信頼度（'high', 'medium', 'low'）
        """
        scores = [pred['prediction_score'] for pred in all_predictions]
        max_score = max(scores)
        min_score = min(scores)
        
        if max_score == min_score:
            return 'medium'
        
        normalized_score = (score - min_score) / (max_score - min_score)
        
        if normalized_score >= 0.8:
            return 'high'
        elif normalized_score >= 0.5:
            return 'medium'
        else:
            return 'low'
    
    def _create_summary(self, predictions: List[Dict[str, Any]], 
                       win_probabilities: List[float]) -> Dict[str, Any]:
        """
        予測結果のサマリー作成
        
        Args:
            predictions: 予測結果
            win_probabilities: 勝率リスト
        
        Returns:
            サマリー情報
        """
        scores = [pred['prediction_score'] for pred in predictions]
        
        # 本命と穴馬の特定
        favorite = predictions[0]  # 1位予測
        dark_horse = None
        
        # B級で上位に来た選手を穴馬として特定
        for pred in predictions[:3]:  # 上位3位まで
            if pred['rating'].startswith('B') and pred['predicted_rank'] <= 3:
                dark_horse = pred
                break
        
        summary = {
            'favorite': {
                'pit_number': favorite['pit_number'],
                'racer_name': favorite['racer_name'],
                'rating': favorite['rating'],
                'win_probability': win_probabilities[0]
            },
            'score_distribution': {
                'max': round(max(scores), 3),
                'min': round(min(scores), 3),
                'average': round(sum(scores) / len(scores), 3),
                'range': round(max(scores) - min(scores), 3)
            },
            'confidence_level': self._overall_confidence(predictions)
        }
        
        if dark_horse:
            summary['dark_horse'] = {
                'pit_number': dark_horse['pit_number'],
                'racer_name': dark_horse['racer_name'],
                'rating': dark_horse['rating'],
                'predicted_rank': dark_horse['predicted_rank'],
                'win_probability': win_probabilities[dark_horse['predicted_rank'] - 1]
            }
        
        return summary
    
    def _overall_confidence(self, predictions: List[Dict[str, Any]]) -> str:
        """
        全体的な予測信頼度を計算
        
        Args:
            predictions: 予測結果
        
        Returns:
            全体信頼度
        """
        scores = [pred['prediction_score'] for pred in predictions]
        score_range = max(scores) - min(scores)
        
        # スコア差が大きいほど信頼度が高い
        if score_range >= 1.0:
            return 'high'
        elif score_range >= 0.5:
            return 'medium'
        else:
            return 'low'
    
    def _extract_race_info(self, race_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        レース情報の抽出
        
        Args:
            race_data: レースデータ
        
        Returns:
            レース情報
        """
        race_info = {
            'total_boats': len(race_data['race_entries'])
        }
        
        # race_infoが存在する場合は追加
        if 'race_info' in race_data:
            info = race_data['race_info']
            race_info.update({
                'date': info.get('date'),
                'stadium': info.get('stadium'),
                'race_number': info.get('race_number'),
                'title': info.get('title')
            })
        
        # 天候情報が存在する場合は追加
        if 'weather_condition' in race_data:
            weather = race_data['weather_condition']
            race_info.update({
                'weather': weather.get('weather'),
                'wind_velocity': weather.get('wind_velocity'),
                'air_temperature': weather.get('air_temperature')
            })
        
        return race_info

    # ========================================
    # Phase 2: 中級アルゴリズム実装
    # ========================================
    
    def _equipment_focused_algorithm(self, race_data: Dict[str, Any], options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        機材重視アルゴリズム
        
        ボート・モーターの成績を重視した予測
        選手の実力よりも機材の調子を重視
        
        Args:
            race_data: レースデータ
            options: アルゴリズムオプション
        
        Returns:
            予測結果リスト
        """
        predictions = []
        race_entries = race_data['race_entries']
        
        for entry in race_entries:
            pit_number = entry['pit_number']
            racer = entry['racer']
            performance = entry['performance']
            
            # 機材データの取得
            boat_rate = performance.get('boat_quinella_rate', 0) / 100  # パーセントを小数に変換
            motor_rate = performance.get('motor_quinella_rate', 0) / 100
            
            # 選手の基本データ
            all_stadium_rate = performance.get('rate_in_all_stadium', 0)
            local_rate = performance.get('rate_in_event_going_stadium', 0)
            rating = racer.get('current_rating', 'B2')
            
            # 機材重視スコア計算
            # 機材成績 70% + 選手成績 30%
            equipment_score = (boat_rate * 0.4 + motor_rate * 0.3)  # 機材70%
            racer_score = (all_stadium_rate * 0.15 + local_rate * 0.15) / 10  # 選手30% (10で割って正規化)
            
            # 級別ボーナス（軽微）
            rating_bonus = self.rating_coefficients.get(rating, 1.0) * 0.1
            
            # 総合スコア
            total_score = equipment_score + racer_score + rating_bonus
            
            prediction = {
                'pit_number': pit_number,
                'racer_name': racer['name'],
                'rating': rating,
                'prediction_score': total_score,
                'details': {
                    'equipment_score': round(equipment_score, 3),
                    'racer_score': round(racer_score, 3),
                    'rating_bonus': round(rating_bonus, 3),
                    'boat_rate': boat_rate,
                    'motor_rate': motor_rate,
                    'algorithm': 'equipment_focused'
                }
            }
            
            predictions.append(prediction)
        
        return predictions
    
    def _comprehensive_algorithm(self, race_data: Dict[str, Any], options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        総合評価アルゴリズム
        
        選手・機材・環境すべてを考慮した総合的な予測
        バランス重視のアプローチ
        
        Args:
            race_data: レースデータ
            options: アルゴリズムオプション
        
        Returns:
            予測結果リスト
        """
        predictions = []
        race_entries = race_data['race_entries']
        
        for entry in race_entries:
            pit_number = entry['pit_number']
            racer = entry['racer']
            performance = entry['performance']
            
            # 各要素のデータ取得
            all_stadium_rate = performance.get('rate_in_all_stadium', 0)
            local_rate = performance.get('rate_in_event_going_stadium', 0)
            boat_rate = performance.get('boat_quinella_rate', 0) / 100
            motor_rate = performance.get('motor_quinella_rate', 0) / 100
            rating = racer.get('current_rating', 'B2')
            
            # 各要素のスコア計算
            # 1. 選手成績スコア (40%)
            racer_score = (all_stadium_rate * 0.25 + local_rate * 0.15) / 10
            
            # 2. 機材成績スコア (35%)
            equipment_score = (boat_rate * 0.2 + motor_rate * 0.15)
            
            # 3. 級別スコア (25%)
            rating_coefficient = self.rating_coefficients.get(rating, 1.0)
            rating_score = (rating_coefficient - 0.9) * 0.25  # 0.9を基準として正規化
            
            # 総合スコア
            total_score = racer_score + equipment_score + rating_score
            
            prediction = {
                'pit_number': pit_number,
                'racer_name': racer['name'],
                'rating': rating,
                'prediction_score': total_score,
                'details': {
                    'racer_score': round(racer_score, 3),
                    'equipment_score': round(equipment_score, 3),
                    'rating_score': round(rating_score, 3),
                    'rating_coefficient': rating_coefficient,
                    'algorithm': 'comprehensive'
                }
            }
            
            predictions.append(prediction)
        
        return predictions
    
    def _relative_strength_algorithm(self, race_data: Dict[str, Any], options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        相対評価アルゴリズム
        
        各艇の他艇に対する相対的な強さを評価
        レース内での相対的な優位性を重視
        
        Args:
            race_data: レースデータ
            options: アルゴリズムオプション
        
        Returns:
            予測結果リスト
        """
        predictions = []
        race_entries = race_data['race_entries']
        
        # 全艇のデータを事前に収集
        all_entries_data = []
        for entry in race_entries:
            performance = entry['performance']
            data = {
                'pit_number': entry['pit_number'],
                'racer_name': entry['racer']['name'],
                'rating': entry['racer'].get('current_rating', 'B2'),
                'all_stadium_rate': performance.get('rate_in_all_stadium', 0),
                'local_rate': performance.get('rate_in_event_going_stadium', 0),
                'boat_rate': performance.get('boat_quinella_rate', 0) / 100,
                'motor_rate': performance.get('motor_quinella_rate', 0) / 100
            }
            all_entries_data.append(data)
        
        # 各艇の相対的強さを計算
        for target_data in all_entries_data:
            wins = 0
            total_comparisons = 0
            
            # 他の全艇と比較
            for other_data in all_entries_data:
                if target_data['pit_number'] != other_data['pit_number']:
                    # 各要素での比較
                    comparisons = [
                        target_data['all_stadium_rate'] > other_data['all_stadium_rate'],
                        target_data['local_rate'] > other_data['local_rate'],
                        target_data['boat_rate'] > other_data['boat_rate'],
                        target_data['motor_rate'] > other_data['motor_rate']
                    ]
                    
                    wins += sum(comparisons)
                    total_comparisons += len(comparisons)
            
            # 相対的強さの計算
            relative_strength = wins / total_comparisons if total_comparisons > 0 else 0
            
            # 級別ボーナス
            rating_coefficient = self.rating_coefficients.get(target_data['rating'], 1.0)
            rating_bonus = (rating_coefficient - 1.0) * 0.2
            
            # 総合スコア
            total_score = relative_strength + rating_bonus
            
            prediction = {
                'pit_number': target_data['pit_number'],
                'racer_name': target_data['racer_name'],
                'rating': target_data['rating'],
                'prediction_score': total_score,
                'details': {
                    'relative_strength': round(relative_strength, 3),
                    'wins': wins,
                    'total_comparisons': total_comparisons,
                    'win_rate_vs_others': round(relative_strength * 100, 1),
                    'rating_bonus': round(rating_bonus, 3),
                    'algorithm': 'relative_strength'
                }
            }
            
            predictions.append(prediction)
        
        return predictions

    # ========================================
    # Phase 2: 3連単確率計算機能
    # ========================================
    
    def calculate_trifecta_probabilities(self, predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        3連単の全組み合わせ確率を計算
        
        Args:
            predictions: 予測結果リスト
        
        Returns:
            3連単確率リスト（確率順）
        """
        calculator = TrifectaProbabilityCalculator()
        return calculator.calculate(predictions)
    
    def get_top_trifecta_recommendations(self, race_data: Dict[str, Any], 
                                       algorithm: str = 'comprehensive',
                                       top_n: int = 10) -> Dict[str, Any]:
        """
        上位3連単推奨組み合わせを取得
        
        Args:
            race_data: レースデータ
            algorithm: 使用するアルゴリズム
            top_n: 上位何位まで取得するか
        
        Returns:
            3連単推奨結果
        """
        # 予測実行
        prediction_result = self.predict(race_data, algorithm)
        
        # 3連単確率計算
        trifecta_probs = self.calculate_trifecta_probabilities(prediction_result['predictions'])
        
        # 上位N位を取得
        top_combinations = trifecta_probs[:top_n]
        
        return {
            'algorithm': algorithm,
            'race_info': prediction_result['race_info'],
            'top_combinations': top_combinations,
            'total_combinations': len(trifecta_probs),
            'summary': {
                'most_likely': top_combinations[0] if top_combinations else None,
                'total_probability': sum(combo['probability'] for combo in top_combinations),
                'average_odds': sum(combo['expected_odds'] for combo in top_combinations) / len(top_combinations) if top_combinations else 0
            }
        }


def test_prediction_engine():
    """
    予測エンジンのテスト関数 - Phase 2対応
    """
    print("🧪 PredictionEngine Phase 2 テスト開始")
    
    # テスト用のサンプルデータ（機材データ追加）
    sample_race_data = {
        'race_entries': [
            {
                'pit_number': 1,
                'racer': {
                    'name': '渡辺 史之',
                    'current_rating': 'B1'
                },
                'performance': {
                    'rate_in_all_stadium': 3.89,
                    'rate_in_event_going_stadium': 4.36,
                    'boat_quinella_rate': 34.2,
                    'motor_quinella_rate': 29.5
                }
            },
            {
                'pit_number': 2,
                'racer': {
                    'name': '横井 健太',
                    'current_rating': 'B1'
                },
                'performance': {
                    'rate_in_all_stadium': 3.95,
                    'rate_in_event_going_stadium': 3.00,
                    'boat_quinella_rate': 44.6,
                    'motor_quinella_rate': 38.3
                }
            },
            {
                'pit_number': 3,
                'racer': {
                    'name': '松尾 基成',
                    'current_rating': 'B1'
                },
                'performance': {
                    'rate_in_all_stadium': 4.07,
                    'rate_in_event_going_stadium': 4.22,
                    'boat_quinella_rate': 36.1,
                    'motor_quinella_rate': 40.0
                }
            },
            {
                'pit_number': 5,
                'racer': {
                    'name': '北川 太一',
                    'current_rating': 'A2'
                },
                'performance': {
                    'rate_in_all_stadium': 5.75,
                    'rate_in_event_going_stadium': 7.11,
                    'boat_quinella_rate': 29.8,
                    'motor_quinella_rate': 32.2
                }
            },
            {
                'pit_number': 6,
                'racer': {
                    'name': '上之 晃弘',
                    'current_rating': 'A2'
                },
                'performance': {
                    'rate_in_all_stadium': 4.89,
                    'rate_in_event_going_stadium': 5.20,
                    'boat_quinella_rate': 23.9,
                    'motor_quinella_rate': 28.1
                }
            }
        ]
    }
    
    try:
        engine = PredictionEngine()
        algorithms = ['basic', 'rating_weighted', 'equipment_focused', 'comprehensive', 'relative_strength']
        
        print("\n" + "="*60)
        print("🏁 Phase 2 アルゴリズム比較テスト")
        print("="*60)
        
        results = {}
        
        for algorithm in algorithms:
            print(f"\n📊 {algorithm.upper()} アルゴリズム")
            print("-" * 40)
            
            result = engine.predict(sample_race_data, algorithm)
            results[algorithm] = result
            
            print(f"⏱️  実行時間: {result['execution_time']}秒")
            print(f"🏆 本命: {result['summary']['favorite']['racer_name']} ({result['summary']['favorite']['win_probability']}%)")
            print(f"📈 信頼度: {result['summary']['confidence_level']}")
            
            # 上位3位表示
            print("🥇 予測順位:")
            for i, pred in enumerate(result['predictions'][:3], 1):
                print(f"   {i}位: {pred['pit_number']}号艇 {pred['racer_name']} ({pred['win_probability']}%)")
        
        # アルゴリズム比較サマリー
        print(f"\n" + "="*60)
        print("📊 アルゴリズム比較サマリー")
        print("="*60)
        
        for algorithm in algorithms:
            result = results[algorithm]
            favorite = result['summary']['favorite']
            print(f"{algorithm:15}: {favorite['pit_number']}号艇 {favorite['racer_name']} ({favorite['win_probability']}%)")
        
        print("\n✅ Phase 2 テスト完了")
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_prediction_engine()