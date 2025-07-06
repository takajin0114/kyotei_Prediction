#!/usr/bin/env python3
"""
大量データでの統計的検証ツール

1,555レースのデータで各アルゴリズムの性能を検証
的中率、順位分布、信頼区間を計算
"""

import sys
import os
import json
import time
import statistics
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
import numpy as np

# パス設定
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from kyotei_predictor.prediction_engine import PredictionEngine
from kyotei_predictor.data_integration import DataIntegration

class BulkPredictionValidator:
    """大量データでの予測検証クラス"""
    
    def __init__(self):
        """初期化"""
        self.engine = PredictionEngine()
        self.data_integration = DataIntegration()
        self.results = {}
        self.algorithms = ['basic', 'rating_weighted', 'equipment_focused', 'comprehensive', 'relative_strength']
        
    def load_race_data_files(self, data_dir: Optional[str] = None) -> List[str]:
        """レースデータファイルの一覧を取得"""
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
        if not isinstance(data_dir, str):
            return []
        race_files = []
        for file in os.listdir(data_dir):
            if file.startswith('race_data_') and file.endswith('.json'):
                race_files.append(os.path.join(data_dir, file))
        print(f"📁 検出されたレースデータ: {len(race_files)}ファイル")
        return sorted(race_files)
    
    def extract_actual_result(self, race_data: Dict[str, Any]) -> Optional[str]:
        """実際の結果を抽出"""
        try:
            # 実際の結果が含まれている場合
            if 'actual_result' in race_data:
                return race_data['actual_result']
            
            # race_recordsから実際の着順を抽出
            race_records = race_data.get('race_records', [])
            if not race_records:
                return None
            
            # arrival（着順）でソート
            sorted_records = sorted(race_records, key=lambda x: x.get('arrival', 999))
            
            # 上位3着の艇番号を取得
            top_3 = []
            for record in sorted_records:
                if record.get('arrival') is not None and record.get('arrival') <= 3:
                    top_3.append(str(record['pit_number']))
                    if len(top_3) == 3:
                        break
            
            if len(top_3) == 3:
                result = '-'.join(top_3)
                return result
            
            return None
            
        except Exception as e:
            print(f"⚠️ 実際の結果抽出エラー: {e}")
            return None
    
    def validate_single_race(self, race_file: str) -> Optional[Dict[str, Any]]:
        """単一レースの検証"""
        try:
            # データ読み込み
            with open(race_file, 'r', encoding='utf-8') as f:
                race_data = json.load(f)
            
            # 実際の結果を抽出
            actual_result = self.extract_actual_result(race_data)
            if not actual_result:
                return None
            
            # 1着艇を抽出
            actual_winner = int(actual_result.split('-')[0])
            
            # 各アルゴリズムで予測
            race_results = {
                'file': os.path.basename(race_file),
                'actual_result': actual_result,
                'actual_winner': actual_winner,
                'predictions': {}
            }
            
            for algorithm in self.algorithms:
                try:
                    # 予測実行
                    prediction_result = self.engine.predict(race_data, algorithm=algorithm)
                    predictions = prediction_result['predictions']
                    
                    # 予測順位をソート
                    predictions.sort(key=lambda x: x['prediction_score'], reverse=True)
                    
                    # 実際の1着艇の予測順位を検索
                    predicted_rank = None
                    predicted_probability = None
                    
                    for i, pred in enumerate(predictions, 1):
                        if pred['pit_number'] == actual_winner:
                            predicted_rank = i
                            predicted_probability = pred['win_probability']
                            break
                    
                    race_results['predictions'][algorithm] = {
                        'predicted_rank': predicted_rank,
                        'predicted_probability': predicted_probability,
                        'top_prediction': predictions[0]['pit_number'] if predictions else None,
                        'execution_time': prediction_result['execution_time']
                    }
                    
                except Exception as e:
                    print(f"⚠️ アルゴリズム {algorithm} エラー: {e}")
                    race_results['predictions'][algorithm] = {
                        'predicted_rank': None,
                        'predicted_probability': None,
                        'top_prediction': None,
                        'execution_time': None
                    }
            
            return race_results
            
        except Exception as e:
            print(f"❌ レース検証エラー {race_file}: {e}")
            return None
    
    def run_bulk_validation(self, max_races: Optional[int] = None) -> Dict[str, Any]:
        """大量データでの検証実行"""
        print("🚀 大量データでの統計的検証開始")
        print("=" * 60)
        race_files = self.load_race_data_files()
        if max_races is not None:
            race_files = race_files[:max_races]
            print(f"📊 検証対象: {len(race_files)}レース（最大{max_races}件）")
        else:
            print(f"📊 検証対象: {len(race_files)}レース（全件）")
        results = []
        start_time = time.time()
        for i, race_file in enumerate(race_files, 1):
            if i % 100 == 0:
                elapsed = time.time() - start_time
                print(f"📈 進捗: {i}/{len(race_files)} ({i/len(race_files)*100:.1f}%) - {elapsed:.1f}秒経過")
            result = self.validate_single_race(race_file)
            if result:
                results.append(result)
        total_time = time.time() - start_time
        print(f"✅ 検証完了: {len(results)}レース - {total_time:.1f}秒")
        analysis = self.analyze_results(results)
        return {
            'total_races': len(results),
            'execution_time': total_time,
            'results': results,
            'analysis': analysis
        }
    
    def analyze_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """結果の統計分析"""
        print("\n📊 統計分析実行中...")
        
        analysis = {}
        
        for algorithm in self.algorithms:
            print(f"🔍 {algorithm} アルゴリズム分析中...")
            
            # 有効な結果を抽出
            valid_results = []
            for result in results:
                if (algorithm in result['predictions'] and 
                    result['predictions'][algorithm]['predicted_rank'] is not None):
                    valid_results.append(result['predictions'][algorithm])
            
            if not valid_results:
                analysis[algorithm] = {'error': '有効なデータなし'}
                continue
            
            # 順位データ
            ranks = [r['predicted_rank'] for r in valid_results]
            probabilities = [r['predicted_probability'] for r in valid_results if r['predicted_probability'] is not None]
            
            # 基本統計
            analysis[algorithm] = {
                'total_races': len(valid_results),
                'hit_rates': {
                    '1st_place': len([r for r in ranks if r == 1]) / len(ranks) * 100,
                    'top_3': len([r for r in ranks if r <= 3]) / len(ranks) * 100,
                    'top_5': len([r for r in ranks if r <= 5]) / len(ranks) * 100,
                    'top_10': len([r for r in ranks if r <= 10]) / len(ranks) * 100
                },
                'rank_statistics': {
                    'mean': statistics.mean(ranks),
                    'median': statistics.median(ranks),
                    'std': statistics.stdev(ranks) if len(ranks) > 1 else 0,
                    'min': min(ranks),
                    'max': max(ranks)
                },
                'probability_statistics': {
                    'mean': statistics.mean(probabilities) if probabilities else 0,
                    'median': statistics.median(probabilities) if probabilities else 0,
                    'std': statistics.stdev(probabilities) if len(probabilities) > 1 else 0
                },
                'rank_distribution': self.calculate_rank_distribution(ranks),
                'confidence_intervals': self.calculate_confidence_intervals(ranks)
            }
        
        return analysis
    
    def calculate_rank_distribution(self, ranks: List[int]) -> Dict[str, int]:
        """順位分布の計算"""
        distribution = {}
        for rank in ranks:
            if rank <= 10:
                key = f"rank_{rank}"
            elif rank <= 20:
                key = "rank_11_20"
            elif rank <= 30:
                key = "rank_21_30"
            else:
                key = "rank_31+"
            
            distribution[key] = distribution.get(key, 0) + 1
        
        return distribution
    
    def calculate_confidence_intervals(self, ranks: List[int], confidence: float = 0.95) -> Dict[str, float]:
        """信頼区間の計算"""
        if len(ranks) < 2:
            return {'lower': 0, 'upper': 0, 'confidence': confidence}
        
        mean_rank = statistics.mean(ranks)
        std_error = statistics.stdev(ranks) / (len(ranks) ** 0.5)
        
        # 簡易的な信頼区間（正規分布仮定）
        z_score = 1.96  # 95%信頼区間
        margin_of_error = z_score * std_error
        
        return {
            'lower': max(1, mean_rank - margin_of_error),
            'upper': mean_rank + margin_of_error,
            'confidence': confidence
        }
    
    def generate_report(self, validation_result: Dict[str, Any]) -> str:
        """検証結果レポートの生成"""
        analysis = validation_result['analysis']
        
        report = []
        report.append("# 大量データ統計的検証レポート")
        report.append(f"**生成日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**検証レース数**: {validation_result['total_races']}")
        report.append(f"**実行時間**: {validation_result['execution_time']:.1f}秒")
        report.append("")
        
        # アルゴリズム別性能比較
        report.append("## 📊 アルゴリズム別性能比較")
        report.append("")
        
        # 的中率比較表
        report.append("### 的中率比較")
        report.append("| アルゴリズム | 1位的中率 | 上位3位 | 上位5位 | 上位10位 |")
        report.append("|-------------|-----------|---------|---------|----------|")
        
        for algorithm in self.algorithms:
            if algorithm in analysis and 'error' not in analysis[algorithm]:
                hit_rates = analysis[algorithm]['hit_rates']
                report.append(f"| {algorithm} | {hit_rates['1st_place']:.1f}% | {hit_rates['top_3']:.1f}% | {hit_rates['top_5']:.1f}% | {hit_rates['top_10']:.1f}% |")
        
        report.append("")
        
        # 順位統計比較
        report.append("### 順位統計比較")
        report.append("| アルゴリズム | 平均順位 | 中央値 | 標準偏差 | 信頼区間 |")
        report.append("|-------------|----------|--------|----------|----------|")
        
        for algorithm in self.algorithms:
            if algorithm in analysis and 'error' not in analysis[algorithm]:
                rank_stats = analysis[algorithm]['rank_statistics']
                conf_intervals = analysis[algorithm]['confidence_intervals']
                report.append(f"| {algorithm} | {rank_stats['mean']:.1f} | {rank_stats['median']:.1f} | {rank_stats['std']:.1f} | {conf_intervals['lower']:.1f}-{conf_intervals['upper']:.1f} |")
        
        report.append("")
        
        # 詳細分析
        report.append("## 🔍 詳細分析")
        report.append("")
        
        for algorithm in self.algorithms:
            if algorithm in analysis and 'error' not in analysis[algorithm]:
                report.append(f"### {algorithm} アルゴリズム")
                report.append("")
                
                # 順位分布
                report.append("#### 順位分布")
                rank_dist = analysis[algorithm]['rank_distribution']
                for rank_range, count in rank_dist.items():
                    percentage = count / analysis[algorithm]['total_races'] * 100
                    report.append(f"- {rank_range}: {count}件 ({percentage:.1f}%)")
                
                report.append("")
                
                # 確率統計
                prob_stats = analysis[algorithm]['probability_statistics']
                report.append(f"#### 予測確率統計")
                report.append(f"- 平均確率: {prob_stats['mean']:.2f}%")
                report.append(f"- 中央値確率: {prob_stats['median']:.2f}%")
                report.append(f"- 標準偏差: {prob_stats['std']:.2f}%")
                report.append("")
        
        return "\n".join(report)
    
    def save_results(self, validation_result: Dict[str, Any], output_dir: Optional[str] = None) -> Optional[Tuple[str, str]]:
        """結果の保存"""
        if not output_dir:
            output_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'outputs')
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # JSON結果保存
        json_file = os.path.join(output_dir, f'bulk_validation_results_{timestamp}.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(validation_result, f, ensure_ascii=False, indent=2)
        # レポート保存
        report = self.generate_report(validation_result)
        report_file = os.path.join(output_dir, f'bulk_validation_report_{timestamp}.md')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"💾 結果保存完了:")
        print(f"  - JSON: {json_file}")
        print(f"  - レポート: {report_file}")
        return json_file, report_file

def main():
    """メイン実行"""
    validator = BulkPredictionValidator()
    
    # 検証実行（最初の100レースでテスト）
    print("🧪 テスト実行: 最初の100レースで検証")
    result = validator.run_bulk_validation(max_races=100)
    
    # 結果保存
    validator.save_results(result)
    
    # レポート表示
    report = validator.generate_report(result)
    print("\n" + "="*60)
    print("📋 検証レポート")
    print("="*60)
    print(report)

if __name__ == "__main__":
    main() 