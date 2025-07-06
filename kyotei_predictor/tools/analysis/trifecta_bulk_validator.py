#!/usr/bin/env python3
"""
3連単予測の大量データ検証ツール

3連単の的中率を大量データで検証
"""

import sys
import os
import json
import time
import statistics
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np

# パス設定
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from kyotei_predictor.prediction_engine import PredictionEngine
from kyotei_predictor.data_integration import DataIntegration

class TrifectaBulkValidator:
    """3連単予測の大量データ検証クラス"""
    
    def __init__(self):
        """初期化"""
        self.engine = PredictionEngine()
        self.data_integration = DataIntegration()
        self.results = {}
        self.algorithms = ['basic', 'rating_weighted', 'equipment_focused', 'comprehensive', 'relative_strength']
    
    def extract_actual_trifecta(self, race_data: Dict[str, Any]) -> Optional[str]:
        """実際の3連単結果を抽出"""
        try:
            # 実際の結果が含まれている場合
            if 'actual_result' in race_data:
                return race_data['actual_result']
            
            # race_recordsから実際の着順を抽出
            race_records = race_data.get('race_records', [])
            if not race_records:
                return None
            
            # arrival（着順）でソート（Noneを除外）
            valid_records = [r for r in race_records if r.get('arrival') is not None]
            if not valid_records:
                return None
                
            sorted_records = sorted(valid_records, key=lambda x: x.get('arrival', 999))
            
            # 上位3着の艇番号を取得
            top_3 = []
            for record in sorted_records:
                if record.get('arrival') is not None and record.get('arrival') <= 3:
                    top_3.append(str(record['pit_number']))
            
            if len(top_3) >= 3:
                return '-'.join(top_3)
            return None
            
        except Exception as e:
            return None
    
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
    
    def validate_single_race(self, race_file: str) -> Optional[Dict[str, Any]]:
        """単一レースの3連単予測検証"""
        try:
            with open(race_file, 'r', encoding='utf-8') as f:
                race_data = json.load(f)
            
            # 実際の3連単結果を抽出
            actual_trifecta = self.extract_actual_trifecta(race_data)
            if not actual_trifecta:
                return None
            
            # 各アルゴリズムで3連単予測
            race_results = {
                'file': os.path.basename(race_file),
                'actual_trifecta': actual_trifecta,
                'predictions': {}
            }
            
            for algorithm in self.algorithms:
                try:
                    # 3連単推奨取得
                    trifecta_result = self.engine.get_top_trifecta_recommendations(
                        race_data, 
                        algorithm=algorithm, 
                        top_n=120  # 全組み合わせ
                    )
                    
                    # 実際の結果の順位を検索
                    actual_rank = None
                    actual_prob = None
                    for i, combo in enumerate(trifecta_result['top_combinations'], 1):
                        if combo['combination'] == actual_trifecta:
                            actual_rank = i
                            actual_prob = combo
                            break
                    
                    # 上位10位以内の的中判定
                    top_10_hit = actual_rank is not None and actual_rank <= 10
                    top_5_hit = actual_rank is not None and actual_rank <= 5
                    top_1_hit = actual_rank is not None and actual_rank == 1
                    
                    race_results['predictions'][algorithm] = {
                        'actual_rank': actual_rank,
                        'actual_probability': actual_prob['percentage'] if actual_prob else 0,
                        'top_1_hit': top_1_hit,
                        'top_5_hit': top_5_hit,
                        'top_10_hit': top_10_hit,
                        'most_likely': trifecta_result['summary']['most_likely']['combination'] if trifecta_result['summary']['most_likely'] else None,
                        'most_likely_probability': trifecta_result['summary']['most_likely']['percentage'] if trifecta_result['summary']['most_likely'] else 0
                    }
                    
                except Exception as e:
                    print(f"⚠️ {algorithm}アルゴリズムエラー: {str(e)}")
                    race_results['predictions'][algorithm] = {
                        'actual_rank': None,
                        'actual_probability': 0,
                        'top_1_hit': False,
                        'top_5_hit': False,
                        'top_10_hit': False,
                        'most_likely': None,
                        'most_likely_probability': 0
                    }
            
            return race_results
            
        except Exception as e:
            print(f"⚠️ レース処理エラー {race_file}: {str(e)}")
            return None
    
    def run_bulk_validation(self, max_races: Optional[int] = None) -> Dict[str, Any]:
        """大量データでの3連単予測検証実行"""
        print("🚀 3連単予測の大量データ検証開始")
        print("=" * 60)
        
        race_files = self.load_race_data_files()
        if max_races:
            race_files = race_files[:max_races]
        
        print(f"📊 検証対象: {len(race_files)}レース")
        print()
        
        # 進捗表示用
        total_races = len(race_files)
        start_time = time.time()
        
        # 各レースの検証
        valid_results = []
        for i, race_file in enumerate(race_files):
            result = self.validate_single_race(race_file)
            if result:
                valid_results.append(result)
            
            # 進捗表示
            if (i + 1) % 10 == 0:
                elapsed = time.time() - start_time
                progress = (i + 1) / total_races * 100
                print(f"📈 進捗: {i + 1}/{total_races} ({progress:.1f}%) - {elapsed:.1f}秒経過")
        
        execution_time = time.time() - start_time
        
        print("=" * 60)
        print(f"✅ 検証完了: {len(valid_results)}レース - {execution_time:.1f}秒")
        
        # 統計分析
        print("\n📊 統計分析実行中...")
        analysis_result = self.analyze_results(valid_results)
        
        # 結果保存
        validation_result = {
            'total_races': len(valid_results),
            'execution_time': execution_time,
            'results': valid_results,
            'analysis': analysis_result
        }
        
        return validation_result
    
    def analyze_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """結果の統計分析"""
        analysis = {}
        
        for algorithm in self.algorithms:
            print(f"🔍 {algorithm} アルゴリズム分析中...")
            
            # 各指標の計算
            total_races = len(results)
            top_1_hits = sum(1 for r in results if r['predictions'][algorithm]['top_1_hit'])
            top_5_hits = sum(1 for r in results if r['predictions'][algorithm]['top_5_hit'])
            top_10_hits = sum(1 for r in results if r['predictions'][algorithm]['top_10_hit'])
            
            # 順位データ
            ranks = [r['predictions'][algorithm]['actual_rank'] for r in results if r['predictions'][algorithm]['actual_rank'] is not None]
            probabilities = [r['predictions'][algorithm]['actual_probability'] for r in results if r['predictions'][algorithm]['actual_probability'] > 0]
            
            # 統計計算
            avg_rank = statistics.mean(ranks) if ranks else 0
            median_rank = statistics.median(ranks) if ranks else 0
            std_rank = statistics.stdev(ranks) if len(ranks) > 1 else 0
            
            # 信頼区間（95%）
            if ranks:
                confidence_interval = (
                    avg_rank - 1.96 * std_rank / (len(ranks) ** 0.5),
                    avg_rank + 1.96 * std_rank / (len(ranks) ** 0.5)
                )
            else:
                confidence_interval = (0, 0)
            
            analysis[algorithm] = {
                'total_races': total_races,
                'top_1_hit_rate': top_1_hits / total_races * 100 if total_races > 0 else 0,
                'top_5_hit_rate': top_5_hits / total_races * 100 if total_races > 0 else 0,
                'top_10_hit_rate': top_10_hits / total_races * 100 if total_races > 0 else 0,
                'average_rank': avg_rank,
                'median_rank': median_rank,
                'std_rank': std_rank,
                'confidence_interval': confidence_interval,
                'average_probability': statistics.mean(probabilities) if probabilities else 0,
                'median_probability': statistics.median(probabilities) if probabilities else 0,
                'std_probability': statistics.stdev(probabilities) if len(probabilities) > 1 else 0
            }
        
        return analysis
    
    def save_results(self, validation_result: Dict[str, Any], output_dir: Optional[str] = None) -> Optional[Tuple[str, str]]:
        """結果の保存"""
        if not output_dir:
            output_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'outputs')
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # JSON結果保存
        json_file = os.path.join(output_dir, f'trifecta_validation_results_{timestamp}.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(validation_result, f, ensure_ascii=False, indent=2)
        
        # レポート保存
        report = self.generate_report(validation_result)
        report_file = os.path.join(output_dir, f'trifecta_validation_report_{timestamp}.md')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"💾 結果保存完了:")
        print(f"  - JSON: {json_file}")
        print(f"  - レポート: {report_file}")
        
        return json_file, report_file
    
    def generate_report(self, validation_result: Dict[str, Any]) -> str:
        """レポート生成"""
        analysis = validation_result['analysis']
        
        report = f"""# 3連単予測大量データ統計的検証レポート
**生成日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**検証レース数**: {validation_result['total_races']}
**実行時間**: {validation_result['execution_time']:.2f}秒

## 📊 アルゴリズム別性能比較

### 的中率比較
| アルゴリズム | 1位的中率 | 上位5位 | 上位10位 |
|-------------|-----------|---------|----------|
"""
        
        for algo in self.algorithms:
            stats = analysis[algo]
            report += f"| {algo} | {stats['top_1_hit_rate']:.1f}% | {stats['top_5_hit_rate']:.1f}% | {stats['top_10_hit_rate']:.1f}% |\n"
        
        report += """
### 順位統計比較
| アルゴリズム | 平均順位 | 中央値 | 標準偏差 | 信頼区間 |
|-------------|----------|--------|----------|----------|
"""
        
        for algo in self.algorithms:
            stats = analysis[algo]
            ci = stats['confidence_interval']
            report += f"| {algo} | {stats['average_rank']:.1f} | {stats['median_rank']:.1f} | {stats['std_rank']:.1f} | {ci[0]:.1f}-{ci[1]:.1f} |\n"
        
        report += """
### 予測確率統計比較
| アルゴリズム | 平均確率 | 中央値確率 | 標準偏差 |
|-------------|----------|------------|----------|
"""
        
        for algo in self.algorithms:
            stats = analysis[algo]
            report += f"| {algo} | {stats['average_probability']:.1f}% | {stats['median_probability']:.1f}% | {stats['std_probability']:.1f}% |\n"
        
        report += """
## 🔍 詳細分析
"""
        
        for algo in self.algorithms:
            stats = analysis[algo]
            report += f"""
### {algo} アルゴリズム

#### 的中率
- 1位的中率: {stats['top_1_hit_rate']:.1f}%
- 上位5位的中率: {stats['top_5_hit_rate']:.1f}%
- 上位10位的中率: {stats['top_10_hit_rate']:.1f}%

#### 順位統計
- 平均順位: {stats['average_rank']:.1f}位
- 中央値: {stats['median_rank']:.1f}位
- 標準偏差: {stats['std_rank']:.1f}
- 95%信頼区間: {stats['confidence_interval'][0]:.1f}位 - {stats['confidence_interval'][1]:.1f}位

#### 予測確率統計
- 平均確率: {stats['average_probability']:.1f}%
- 中央値確率: {stats['median_probability']:.1f}%
- 標準偏差: {stats['std_probability']:.1f}%
"""
        
        return report

def main():
    """メイン処理"""
    import argparse
    
    parser = argparse.ArgumentParser(description='3連単予測の大量データ検証')
    parser.add_argument('--max_races', type=int, help='最大検証レース数')
    args = parser.parse_args()
    
    validator = TrifectaBulkValidator()
    validation_result = validator.run_bulk_validation(args.max_races)
    
    # 結果保存
    validator.save_results(validation_result)
    
    # 結果表示
    print("\n" + "=" * 60)
    print("📋 検証レポート")
    print("=" * 60)
    
    analysis = validation_result['analysis']
    
    print("### 的中率比較")
    print("| アルゴリズム | 1位的中率 | 上位5位 | 上位10位 |")
    print("|-------------|-----------|---------|----------|")
    
    for algo in ['basic', 'rating_weighted', 'equipment_focused', 'comprehensive', 'relative_strength']:
        stats = analysis[algo]
        print(f"| {algo} | {stats['top_1_hit_rate']:.1f}% | {stats['top_5_hit_rate']:.1f}% | {stats['top_10_hit_rate']:.1f}% |")
    
    print("\n### 順位統計比較")
    print("| アルゴリズム | 平均順位 | 中央値 | 標準偏差 |")
    print("|-------------|----------|--------|----------|")
    
    for algo in ['basic', 'rating_weighted', 'equipment_focused', 'comprehensive', 'relative_strength']:
        stats = analysis[algo]
        print(f"| {algo} | {stats['average_rank']:.1f} | {stats['median_rank']:.1f} | {stats['std_rank']:.1f} |")

if __name__ == "__main__":
    main() 