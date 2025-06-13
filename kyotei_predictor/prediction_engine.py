"""
競艇予測エンジン - Phase 1: 基本アルゴリズム実装

このモジュールは競艇レースの予測を行うためのアルゴリズムを提供します。
段階的な実装により、基本的な勝率ベース予測から高度な分析まで対応します。

作成日: 2025-06-13
バージョン: 1.0 (Phase 1)
"""

import json
import time
from typing import Dict, List, Any, Optional, Tuple
import logging

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
            'rating_weighted': self._rating_weighted_algorithm
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


def test_prediction_engine():
    """
    予測エンジンのテスト関数
    """
    print("🧪 PredictionEngine テスト開始")
    
    # テスト用のサンプルデータ
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
                    'rate_in_event_going_stadium': 4.36
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
                    'rate_in_event_going_stadium': 3.00
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
                    'rate_in_event_going_stadium': 7.11
                }
            }
        ]
    }
    
    try:
        engine = PredictionEngine()
        
        # 基本アルゴリズムのテスト
        print("\n📊 基本アルゴリズムテスト")
        result_basic = engine.predict(sample_race_data, 'basic')
        print(f"実行時間: {result_basic['execution_time']}秒")
        print(f"本命: {result_basic['summary']['favorite']['racer_name']} ({result_basic['summary']['favorite']['win_probability']}%)")
        
        # 級別重み付けアルゴリズムのテスト
        print("\n📊 級別重み付けアルゴリズムテスト")
        result_rating = engine.predict(sample_race_data, 'rating_weighted')
        print(f"実行時間: {result_rating['execution_time']}秒")
        print(f"本命: {result_rating['summary']['favorite']['racer_name']} ({result_rating['summary']['favorite']['win_probability']}%)")
        
        print("\n✅ テスト完了")
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {str(e)}")
        return False


if __name__ == "__main__":
    test_prediction_engine()