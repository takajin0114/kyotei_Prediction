#!/usr/bin/env python3
"""
予想ツール - 3連単予測・購入方法提案機能

機能:
1. レース前データ取得
2. 3連単予測実行（上位20組）
3. 購入方法の提案生成
4. JSON形式での結果保存
5. Web表示用データ生成

使用方法:
    python -m kyotei_predictor.tools.prediction_tool --predict-date 2024-07-12
    python -m kyotei_predictor.tools.prediction_tool --predict-date 2024-07-12 --venues KIRYU,TODA
"""

import os
import sys
import json
import argparse
import logging
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from itertools import permutations
import torch

# プロジェクトルートの設定
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from stable_baselines3 import PPO
from kyotei_predictor.pipelines.kyotei_env import vectorize_race_state, action_to_trifecta

class PredictionTool:
    """予想ツールのメインクラス"""
    
    def __init__(self, log_level=logging.INFO):
        self.setup_logging(log_level)
        self.model = None
        self.model_info = {}
        
    def setup_logging(self, log_level):
        """ログ設定"""
        log_file = PROJECT_ROOT / "kyotei_predictor" / "logs" / f"prediction_tool_{datetime.now().strftime('%Y%m%d')}.log"
        log_file.parent.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_model(self, model_path: str = None) -> bool:
        """学習済みモデルの読み込み"""
        try:
            if not model_path:
                # デフォルトで最新のベストモデルを使用
                model_dir = PROJECT_ROOT / "optuna_models" / "graduated_reward_best"
                model_path = model_dir / "best_model.zip"
                
                if not model_path.exists():
                    # フォールバック: 最新のチェックポイント
                    checkpoint_dir = PROJECT_ROOT / "optuna_models" / "graduated_reward_checkpoints"
                    if checkpoint_dir.exists():
                        checkpoints = list(checkpoint_dir.glob("*.zip"))
                        if checkpoints:
                            model_path = max(checkpoints, key=lambda x: x.stat().st_mtime)
            
            if not model_path.exists():
                self.logger.error(f"モデルファイルが見つかりません: {model_path}")
                return False
            
            self.logger.info(f"モデルを読み込み中: {model_path}")
            self.model = PPO.load(str(model_path))
            
            # モデル情報を記録
            self.model_info = {
                'model_path': str(model_path),
                'model_name': model_path.stem,
                'version': datetime.fromtimestamp(model_path.stat().st_mtime).strftime('%Y-%m-%d'),
                'training_data_until': self.get_training_data_date()
            }
            
            self.logger.info("モデルの読み込みが完了しました")
            return True
            
        except Exception as e:
            self.logger.error(f"モデル読み込みエラー: {e}")
            return False
    
    def get_training_data_date(self) -> str:
        """学習データの最終日を推定"""
        # 実際の実装では、学習時に使用したデータの最終日を記録する
        # ここでは簡易的に前日を返す
        yesterday = datetime.now() - timedelta(days=1)
        return yesterday.strftime('%Y-%m-%d')
    
    def get_race_data_paths(self, predict_date: str, venues: List[str] = None) -> List[Tuple[str, str, str]]:
        """予測対象のレースデータパスを取得"""
        race_data_dir = PROJECT_ROOT / "kyotei_predictor" / "data" / "raw"
        
        race_paths = []
        
        # 指定された会場または全会場
        if not venues:
            venues = ["KIRYU", "TODA", "EDOGAWA", "KORAKUEN", "HEIWAJIMA", "KAWASAKI", 
                     "FUNEBASHI", "KASAMATSU", "HAMANAKO", "MIKUNIHARA", "TOKONAME", 
                     "GAMAGORI", "TAMANO", "MIHARA", "YAMAGUCHI", "WAKAYAMA", 
                     "AMAGASAKI", "NARUTO", "MARUGAME", "KOCHI", "TOKUSHIMA", 
                     "IMABARI", "OGATA", "MIYAZAKI"]
        
        for venue in venues:
            # レースデータファイルを検索
            race_pattern = f"race_data_{predict_date}_{venue}_R*.json"
            odds_pattern = f"odds_data_{predict_date}_{venue}_R*.json"
            
            race_files = list(race_data_dir.glob(race_pattern))
            odds_files = list(race_data_dir.glob(odds_pattern))
            
            # レース番号でマッチング
            for race_file in race_files:
                # ファイル名からレース番号を抽出
                filename = race_file.name
                if "_R" in filename:
                    race_number = filename.split("_R")[-1].replace(".json", "")
                    
                    # 対応するオッズファイルを検索
                    odds_file = race_data_dir / f"odds_data_{predict_date}_{venue}_R{race_number}.json"
                    
                    if odds_file.exists():
                        race_paths.append((venue, race_number, str(race_file), str(odds_file)))
        
        self.logger.info(f"予測対象レース数: {len(race_paths)}")
        return race_paths
    
    def predict_trifecta_probabilities(self, race_data_path: str, odds_data_path: str) -> List[Dict]:
        """3連単の予測確率を計算（上位20組）"""
        try:
            # 状態ベクトルを生成
            state = vectorize_race_state(race_data_path, odds_data_path)
            # torch.Tensorに変換
            state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0)  # shape: (1, n_features)
            # モデルで予測
            action_probs = self.model.policy.get_distribution(state_tensor).distribution.probs.detach().cpu().numpy()[0]
            
            # 3連単の組み合わせリスト（120通り）
            trifecta_list = list(permutations(range(1, 7), 3))
            
            # 確率と組み合わせをペアにしてソート
            probability_combinations = []
            for i, prob in enumerate(action_probs):
                trifecta = trifecta_list[i]
                combination_str = f"{trifecta[0]}-{trifecta[1]}-{trifecta[2]}"
                probability_combinations.append({
                    'combination': combination_str,
                    'probability': float(prob),
                    'expected_value': self.calculate_expected_value(trifecta, odds_data_path),
                    'rank': 0
                })
            
            # 確率でソート（降順）
            probability_combinations.sort(key=lambda x: x['probability'], reverse=True)
            
            # 上位20組を取得し、ランクを設定
            top_20 = probability_combinations[:20]
            for i, item in enumerate(top_20):
                item['rank'] = i + 1
            
            return top_20
            
        except Exception as e:
            self.logger.error(f"予測エラー: {e}")
            return []
    
    def calculate_expected_value(self, trifecta: Tuple[int, int, int], odds_data_path: str) -> float:
        """期待値を計算"""
        try:
            with open(odds_data_path, 'r', encoding='utf-8') as f:
                odds_data = json.load(f)
            
            odds_map = {tuple(o['betting_numbers']): o['ratio'] for o in odds_data['odds_data']}
            odds = odds_map.get(trifecta, 0)
            
            # 期待値 = 確率 × オッズ - 1
            # 確率は上位20組の確率を使用するため、ここでは簡易計算
            return odds * 0.05 - 1  # 仮の確率0.05を使用
            
        except Exception as e:
            self.logger.warning(f"期待値計算エラー: {e}")
            return 0.0
    
    def generate_purchase_suggestions(self, top_20_combinations: List[Dict]) -> List[Dict]:
        """購入方法の提案を生成"""
        suggestions = []
        
        # 1. 流し買い（Nagashi）の提案
        nagashi_suggestions = self.generate_nagashi_suggestions(top_20_combinations)
        suggestions.extend(nagashi_suggestions)
        
        # 2. 流し買い（Wheel）の提案
        wheel_suggestions = self.generate_wheel_suggestions(top_20_combinations)
        suggestions.extend(wheel_suggestions)
        
        # 3. ボックス買いの提案
        box_suggestions = self.generate_box_suggestions(top_20_combinations)
        suggestions.extend(box_suggestions)
        
        # 期待値でソート
        suggestions.sort(key=lambda x: x['expected_return'], reverse=True)
        
        return suggestions[:5]  # 上位5件を返す
    
    def generate_nagashi_suggestions(self, combinations: List[Dict]) -> List[Dict]:
        """流し買い（同じ1-2着で3着を流す）の提案"""
        suggestions = []
        
        # 1-2着の組み合わせをグループ化
        first_second_groups = {}
        for combo in combinations:
            first, second, third = combo['combination'].split('-')
            key = f"{first}-{second}"
            if key not in first_second_groups:
                first_second_groups[key] = []
            first_second_groups[key].append(combo)
        
        # 上位の1-2着組み合わせで流し買いを提案
        for key, group in first_second_groups.items():
            if len(group) >= 3:  # 3つ以上の組み合わせがある場合
                total_prob = sum(c['probability'] for c in group[:4])  # 上位4つ
                total_cost = 400  # 流し買いのコスト
                expected_return = total_prob * 1000  # 仮の計算
                
                suggestions.append({
                    'type': 'nagashi',
                    'description': f"{key}-流し",
                    'combinations': [c['combination'] for c in group[:4]],
                    'total_probability': total_prob,
                    'total_cost': total_cost,
                    'expected_return': expected_return
                })
        
        return suggestions
    
    def generate_wheel_suggestions(self, combinations: List[Dict]) -> List[Dict]:
        """流し買い（同じ1着で2-3着を流す）の提案"""
        suggestions = []
        
        # 1着でグループ化
        first_groups = {}
        for combo in combinations:
            first, second, third = combo['combination'].split('-')
            if first not in first_groups:
                first_groups[first] = []
            first_groups[first].append(combo)
        
        # 上位の1着で流し買いを提案
        for first, group in first_groups.items():
            if len(group) >= 3:  # 3つ以上の組み合わせがある場合
                total_prob = sum(c['probability'] for c in group[:4])  # 上位4つ
                total_cost = 400  # 流し買いのコスト
                expected_return = total_prob * 1000  # 仮の計算
                
                suggestions.append({
                    'type': 'wheel',
                    'description': f"{first}-流し",
                    'combinations': [c['combination'] for c in group[:4]],
                    'total_probability': total_prob,
                    'total_cost': total_cost,
                    'expected_return': expected_return
                })
        
        return suggestions
    
    def generate_box_suggestions(self, combinations: List[Dict]) -> List[Dict]:
        """ボックス買いの提案"""
        suggestions = []
        
        # 上位の組み合わせでボックス買いを提案
        for i, combo in enumerate(combinations[:3]):  # 上位3つ
            first, second, third = combo['combination'].split('-')
            
            # 順列を生成
            permutations_list = list(permutations([int(first), int(second), int(third)], 3))
            box_combinations = [f"{p[0]}-{p[1]}-{p[2]}" for p in permutations_list]
            
            # 上位20組から該当する組み合わせを抽出
            box_prob_combinations = [c for c in combinations if c['combination'] in box_combinations]
            
            if len(box_prob_combinations) >= 3:
                total_prob = sum(c['probability'] for c in box_prob_combinations)
                total_cost = 1200  # ボックス買いのコスト（6通り）
                expected_return = total_prob * 1000  # 仮の計算
                
                suggestions.append({
                    'type': 'box',
                    'description': f"{combo['combination']} ボックス",
                    'combinations': [c['combination'] for c in box_prob_combinations],
                    'total_probability': total_prob,
                    'total_cost': total_cost,
                    'expected_return': expected_return
                })
        
        return suggestions
    
    def predict_races(self, predict_date: str, venues: List[str] = None) -> Dict:
        """全会場・全レースの予測を実行"""
        try:
            self.logger.info(f"予測開始: {predict_date}")
            start_time = datetime.now()
            
            # モデル読み込み
            if not self.load_model():
                return None
            
            # レースデータパスを取得
            race_paths = self.get_race_data_paths(predict_date, venues)
            
            if not race_paths:
                self.logger.warning(f"予測対象のレースデータが見つかりません: {predict_date}")
                return None
            
            # 各レースの予測を実行
            predictions = []
            successful_predictions = 0
            
            for venue, race_number, race_path, odds_path in race_paths:
                try:
                    self.logger.info(f"予測中: {venue} {race_number}")
                    
                    # 3連単予測
                    top_20_combinations = self.predict_trifecta_probabilities(race_path, odds_path)
                    
                    if top_20_combinations:
                        # 購入方法の提案
                        purchase_suggestions = self.generate_purchase_suggestions(top_20_combinations)
                        
                        # 合計確率
                        total_probability = sum(c['probability'] for c in top_20_combinations)
                        
                        # レース情報を取得
                        with open(race_path, 'r', encoding='utf-8') as f:
                            race_data = json.load(f)
                        
                        race_info = race_data.get('race_info', {})
                        race_time = race_info.get('race_time', '09:00')
                        
                        prediction = {
                            'venue': venue,
                            'venue_code': self.get_venue_code(venue),
                            'race_number': int(race_number),
                            'race_time': race_time,
                            'top_20_combinations': top_20_combinations,
                            'total_probability': total_probability,
                            'purchase_suggestions': purchase_suggestions,
                            'risk_level': self.calculate_risk_level(total_probability)
                        }
                        
                        predictions.append(prediction)
                        successful_predictions += 1
                    
                except Exception as e:
                    self.logger.error(f"レース予測エラー {venue} {race_number}: {e}")
            
            # 会場別サマリー
            venue_summaries = self.generate_venue_summaries(predictions)
            
            # 実行結果
            execution_time = (datetime.now() - start_time).total_seconds() / 60
            
            result = {
                'prediction_date': predict_date,
                'generated_at': datetime.now().isoformat(),
                'model_info': self.model_info,
                'execution_summary': {
                    'total_venues': len(set(p['venue'] for p in predictions)),
                    'total_races': len(predictions),
                    'successful_predictions': successful_predictions,
                    'execution_time_minutes': execution_time
                },
                'predictions': predictions,
                'venue_summaries': venue_summaries
            }
            
            self.logger.info(f"予測完了: {successful_predictions}レース, {execution_time:.1f}分")
            return result
            
        except Exception as e:
            self.logger.error(f"予測実行エラー: {e}")
            return None
    
    def get_venue_code(self, venue: str) -> str:
        """会場コードを取得"""
        venue_codes = {
            'KIRYU': '01', 'TODA': '02', 'EDOGAWA': '03', 'KORAKUEN': '04',
            'HEIWAJIMA': '05', 'KAWASAKI': '06', 'FUNEBASHI': '07', 'KASAMATSU': '08',
            'HAMANAKO': '09', 'MIKUNIHARA': '10', 'TOKONAME': '11', 'GAMAGORI': '12',
            'TAMANO': '13', 'MIHARA': '14', 'YAMAGUCHI': '15', 'WAKAYAMA': '16',
            'AMAGASAKI': '17', 'NARUTO': '18', 'MARUGAME': '19', 'KOCHI': '20',
            'TOKUSHIMA': '21', 'IMABARI': '22', 'OGATA': '23', 'MIYAZAKI': '24'
        }
        return venue_codes.get(venue, '00')
    
    def calculate_risk_level(self, total_probability: float) -> str:
        """リスクレベルを計算"""
        if total_probability >= 0.8:
            return 'low'
        elif total_probability >= 0.6:
            return 'medium'
        else:
            return 'high'
    
    def generate_venue_summaries(self, predictions: List[Dict]) -> List[Dict]:
        """会場別サマリーを生成"""
        venue_stats = {}
        
        for pred in predictions:
            venue = pred['venue']
            if venue not in venue_stats:
                venue_stats[venue] = {
                    'total_races': 0,
                    'high_confidence_races': 0,
                    'total_probability': 0,
                    'total_expected_value': 0
                }
            
            venue_stats[venue]['total_races'] += 1
            venue_stats[venue]['total_probability'] += pred['total_probability']
            
            # 高信頼度レース（上位確率が0.08以上）
            top_prob = pred['top_20_combinations'][0]['probability'] if pred['top_20_combinations'] else 0
            if top_prob >= 0.08:
                venue_stats[venue]['high_confidence_races'] += 1
            
            # 平均期待値
            avg_expected_value = sum(c['expected_value'] for c in pred['top_20_combinations'][:5]) / 5
            venue_stats[venue]['total_expected_value'] += avg_expected_value
        
        # サマリーを生成
        summaries = []
        for venue, stats in venue_stats.items():
            summaries.append({
                'venue': venue,
                'total_races': stats['total_races'],
                'high_confidence_races': stats['high_confidence_races'],
                'average_top_probability': stats['total_probability'] / stats['total_races'],
                'average_expected_value': stats['total_expected_value'] / stats['total_races']
            })
        
        return summaries
    
    def save_prediction_result(self, result: Dict, output_dir: str = None) -> str:
        """予測結果をJSONファイルに保存"""
        try:
            if not output_dir:
                output_dir = PROJECT_ROOT / "outputs"
            
            output_dir = Path(output_dir)
            output_dir.mkdir(exist_ok=True)
            
            # 日付別ファイル
            date_str = result['prediction_date'].replace('-', '')
            filename = f"predictions_{result['prediction_date']}.json"
            filepath = output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            # 最新ファイルへのシンボリックリンク（Windowsではコピー）
            latest_file = output_dir / "predictions_latest.json"
            if latest_file.exists():
                latest_file.unlink()
            
            # Windowsではシンボリックリンクの代わりにコピー
            import shutil
            shutil.copy2(filepath, latest_file)
            
            self.logger.info(f"予測結果を保存しました: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"予測結果保存エラー: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(description='予想ツール - 3連単予測・購入方法提案')
    parser.add_argument('--predict-date', type=str, required=True, help='予測対象日 (YYYY-MM-DD)')
    parser.add_argument('--venues', type=str, help='対象会場 (カンマ区切り)')
    parser.add_argument('--model-path', type=str, help='モデルファイルパス')
    parser.add_argument('--output-dir', type=str, help='出力ディレクトリ')
    parser.add_argument('--verbose', action='store_true', help='詳細ログ出力')
    
    args = parser.parse_args()
    
    # ログレベル設定
    log_level = logging.DEBUG if args.verbose else logging.INFO
    
    # 予想ツール初期化
    tool = PredictionTool(log_level)
    
    # 会場リスト
    venues = None
    if args.venues:
        venues = [v.strip() for v in args.venues.split(',')]
    
    # 予測実行
    result = tool.predict_races(args.predict_date, venues)
    
    if result:
        # 結果保存
        output_path = tool.save_prediction_result(result, args.output_dir)
        
        if output_path:
            print(f"\n=== 予測完了 ===")
            print(f"予測日: {result['prediction_date']}")
            print(f"対象レース数: {result['execution_summary']['total_races']}")
            print(f"成功レース数: {result['execution_summary']['successful_predictions']}")
            print(f"実行時間: {result['execution_summary']['execution_time_minutes']:.1f}分")
            print(f"結果ファイル: {output_path}")
        else:
            print("予測結果の保存に失敗しました")
    else:
        print("予測の実行に失敗しました")

if __name__ == "__main__":
    main() 