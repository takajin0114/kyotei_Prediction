#!/usr/bin/env python3
"""
共通ユーティリティ関数。

Windows では標準出力の UTF-8 化を ensure_windows_utf8_stdio() で行う。
他モジュールではこのモジュールを最優先で import するか、ensure_windows_utf8_stdio() を呼ぶこと。
"""
import os
import json
import logging
import sys
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import numpy as np
import pandas as pd


def ensure_windows_utf8_stdio() -> None:
    """Windows で標準入出力を UTF-8 に設定（PowerShell 等の文字化け対策）。他プラットフォームでは no-op。"""
    if not sys.platform.startswith('win'):
        return
    import codecs
    try:
        os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
        os.environ.setdefault('PYTHONLEGACYWINDOWSSTDIO', 'utf-8')
        if hasattr(sys.stdout, 'detach'):
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
    except Exception:
        os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
        os.environ.setdefault('PYTHONLEGACYWINDOWSSTDIO', 'utf-8')


# このモジュールが import された時点で Windows の場合は UTF-8 化を適用
ensure_windows_utf8_stdio()

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KyoteiUtils:
    """競艇予測システムの共通ユーティリティクラス"""
    
    @staticmethod
    def load_json_file(file_path: str) -> Dict[str, Any]:
        """JSONファイルを読み込み"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"JSONファイル読み込みエラー: {file_path}, {e}")
            return {}
    
    @staticmethod
    def save_json_file(data: Dict[str, Any], file_path: str) -> bool:
        """JSONファイルに保存"""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"JSONファイル保存エラー: {file_path}, {e}")
            return False
    
    @staticmethod
    def safe_print(message: str) -> None:
        """文字化け対策付きprint関数"""
        try:
            # まず通常のprintを試行
            print(message)
        except UnicodeEncodeError:
            try:
                # UTF-8でエンコードして出力
                print(message.encode('utf-8').decode('utf-8'))
            except:
                # 最後の手段: ASCII文字のみ出力
                print(message.encode('ascii', 'ignore').decode('ascii'))
        except Exception as e:
            # その他のエラーの場合はASCII文字のみ出力
            try:
                print(message.encode('ascii', 'ignore').decode('ascii'))
            except:
                print("文字化けエラー: メッセージを表示できません")
    
    @staticmethod
    def extract_race_result(race_data: Dict[str, Any]) -> Optional[Tuple[int, int, int]]:
        """レース結果（1着、2着、3着）を抽出"""
        try:
            boats = race_data.get('boats', [])
            if not boats:
                return None
            
            # 着順でソート
            sorted_boats = sorted(boats, key=lambda x: x.get('arrival', 999))
            
            # 1着、2着、3着を取得
            first = sorted_boats[0].get('boat_number', 0)
            second = sorted_boats[1].get('boat_number', 0) if len(sorted_boats) > 1 else 0
            third = sorted_boats[2].get('boat_number', 0) if len(sorted_boats) > 2 else 0
            
            return (first, second, third)
        except Exception as e:
            logger.error(f"レース結果抽出エラー: {e}")
            return None
    
    @staticmethod
    def calculate_expected_value(probability: float, odds: float) -> float:
        """期待値を計算"""
        return probability * odds
    
    @staticmethod
    def is_profitable(expected_value: float, threshold: float = 1.0) -> bool:
        """投資価値があるか判定"""
        return expected_value >= threshold
    
    @staticmethod
    def normalize_probabilities(probabilities: List[float]) -> List[float]:
        """確率を正規化（合計=1.0）"""
        total = sum(probabilities)
        if total == 0:
            return [1.0 / len(probabilities)] * len(probabilities)
        return [p / total for p in probabilities]
    
    @staticmethod
    def softmax(x: List[float], temperature: float = 1.0) -> List[float]:
        """ソフトマックス関数"""
        if temperature == 0:
            return [1.0 if i == np.argmax(x) else 0.0 for i in range(len(x))]
        
        exp_x = np.exp(np.array(x) / temperature)
        return (exp_x / exp_x.sum()).tolist()
    
    @staticmethod
    def get_ranking_distribution(predictions: List[Dict[str, Any]], 
                               actual_result: Tuple[int, int, int]) -> Dict[str, Any]:
        """予測結果の順位分布を計算"""
        if not actual_result:
            return {}
        
        actual_str = f"{actual_result[0]}-{actual_result[1]}-{actual_result[2]}"
        
        # 実際の結果の順位を検索
        for i, pred in enumerate(predictions):
            if pred['combination'] == actual_str:
                return {
                    'rank': i + 1,
                    'total_combinations': len(predictions),
                    'probability': pred['probability']
                }
        
        return {'rank': len(predictions), 'total_combinations': len(predictions), 'probability': 0.0}
    
    @staticmethod
    def calculate_hit_rates(results: List[Dict[str, Any]]) -> Dict[str, float]:
        """的中率を計算"""
        if not results:
            return {}
        
        total_races = len(results)
        hit_counts = {
            '1st': 0,
            'top3': 0,
            'top5': 0,
            'top10': 0
        }
        
        for result in results:
            rank = result.get('rank', 999)
            if rank == 1:
                hit_counts['1st'] += 1
            if rank <= 3:
                hit_counts['top3'] += 1
            if rank <= 5:
                hit_counts['top5'] += 1
            if rank <= 10:
                hit_counts['top10'] += 1
        
        return {
            '1st_hit_rate': hit_counts['1st'] / total_races * 100,
            'top3_hit_rate': hit_counts['top3'] / total_races * 100,
            'top5_hit_rate': hit_counts['top5'] / total_races * 100,
            'top10_hit_rate': hit_counts['top10'] / total_races * 100,
            'total_races': total_races
        }
    
    @staticmethod
    def generate_timestamp() -> str:
        """タイムスタンプを生成"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    @staticmethod
    def create_output_filename(prefix: str, extension: str = 'json') -> str:
        """出力ファイル名を生成"""
        timestamp = KyoteiUtils.generate_timestamp()
        return f"{prefix}_{timestamp}.{extension}"
    
    @staticmethod
    def validate_race_data(race_data: Dict[str, Any]) -> bool:
        """レースデータの妥当性を検証"""
        try:
            # 必須フィールドの確認
            required_fields = ['race_id', 'boats']
            for field in required_fields:
                if field not in race_data:
                    logger.warning(f"必須フィールドが不足: {field}")
                    return False
            
            # ボートデータの確認
            boats = race_data.get('boats', [])
            if len(boats) < 6:
                logger.warning(f"ボート数が不足: {len(boats)}")
                return False
            
            # 着順データの確認
            for boat in boats:
                if 'arrival' not in boat or boat['arrival'] is None:
                    logger.warning(f"着順データが不足: {boat}")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"データ検証エラー: {e}")
            return False
    
    @staticmethod
    def get_boat_features(boat_data: Dict[str, Any]) -> Dict[str, float]:
        """ボートの特徴量を抽出"""
        features = {}
        
        # 基本情報
        features['boat_number'] = float(boat_data.get('boat_number', 0))
        features['course'] = float(boat_data.get('course', 0))
        
        # 選手情報
        features['age'] = float(boat_data.get('age', 0))
        features['weight'] = float(boat_data.get('weight', 0))
        features['height'] = float(boat_data.get('height', 0))
        
        # 成績情報
        features['win_rate'] = float(boat_data.get('win_rate', 0))
        features['place_rate'] = float(boat_data.get('place_rate', 0))
        features['avg_start_time'] = float(boat_data.get('avg_start_time', 0))
        
        # 設備情報
        features['motor_number'] = float(boat_data.get('motor_number', 0))
        features['boat_number_equipment'] = float(boat_data.get('boat_number_equipment', 0))
        
        return features
    
    @staticmethod
    def calculate_boat_similarity(boat1: Dict[str, float], boat2: Dict[str, float]) -> float:
        """ボート間の類似度を計算"""
        # ユークリッド距離の逆数
        distance = 0.0
        for key in boat1:
            if key in boat2:
                distance += (boat1[key] - boat2[key]) ** 2
        
        if distance == 0:
            return 1.0
        
        return 1.0 / (1.0 + np.sqrt(distance))
    
    @staticmethod
    def log_progress(current: int, total: int, message: str = "処理中"):
        """進捗をログ出力"""
        percentage = (current / total) * 100
        logger.info(f"{message}: {current}/{total} ({percentage:.1f}%)")

# 便利な関数のエイリアス
load_json = KyoteiUtils.load_json_file
save_json = KyoteiUtils.save_json_file
extract_result = KyoteiUtils.extract_race_result
calc_expected_value = KyoteiUtils.calculate_expected_value
is_profitable = KyoteiUtils.is_profitable
normalize_probs = KyoteiUtils.normalize_probabilities
softmax = KyoteiUtils.softmax
get_ranking = KyoteiUtils.get_ranking_distribution
calc_hit_rates = KyoteiUtils.calculate_hit_rates
get_timestamp = KyoteiUtils.generate_timestamp
create_filename = KyoteiUtils.create_output_filename
validate_data = KyoteiUtils.validate_race_data
get_features = KyoteiUtils.get_boat_features
calc_similarity = KyoteiUtils.calculate_boat_similarity
log_progress = KyoteiUtils.log_progress 