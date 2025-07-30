#!/usr/bin/env python3
"""
データ品質チェッカー
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

# プロジェクトルートを動的に取得
def get_project_root() -> Path:
    """プロジェクトルートを動的に検出"""
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent
    
    # Google Colab環境の検出
    if str(project_root).startswith('/content/'):
        return Path('/content/kyotei_Prediction')
    
    return project_root

PROJECT_ROOT = get_project_root()

# プロジェクトルートをパスに追加
sys.path.append(str(PROJECT_ROOT))

class DataQualityChecker:
    """データ品質チェッカークラス"""
    
    def __init__(self):
        """初期化"""
        self.project_root = PROJECT_ROOT
        self.log_dir = self.project_root / "kyotei_predictor" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # ログ設定
        log_file = self.log_dir / "data_quality_checker.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("DataQualityChecker初期化完了")
    
    def check_data_quality(self, target_date: str = None) -> Dict:
        """
        データ品質をチェック
        
        Args:
            target_date: チェック対象日
            
        Returns:
            品質チェック結果
        """
        try:
            if not target_date:
                target_date = datetime.now().strftime('%Y-%m-%d')
            
            self.logger.info(f"データ品質チェック開始: {target_date}")
            
            # データディレクトリ
            data_dir = self.project_root / "kyotei_predictor" / "data" / "raw"
            
            # チェック結果
            results = {
                'target_date': target_date,
                'timestamp': datetime.now().isoformat(),
                'total_files': 0,
                'valid_files': 0,
                'invalid_files': 0,
                'missing_files': 0,
                'quality_score': 0.0,
                'issues': []
            }
            
            # ファイルチェック
            self.check_files(data_dir, target_date, results)
            
            # データ内容チェック
            self.check_data_content(data_dir, target_date, results)
            
            # 品質スコア計算
            self.calculate_quality_score(results)
            
            self.logger.info(f"データ品質チェック完了: スコア {results['quality_score']:.2f}")
            return results
            
        except Exception as e:
            self.logger.error(f"データ品質チェックエラー: {e}")
            return {
                'target_date': target_date,
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'quality_score': 0.0
            }
    
    def check_files(self, data_dir: Path, target_date: str, results: Dict):
        """ファイル存在チェック"""
        try:
            # 期待されるファイルパターン
            expected_patterns = [
                f"race_data_{target_date}_*_R*.json",
                f"odds_data_{target_date}_*_R*.json"
            ]
            
            found_files = []
            for pattern in expected_patterns:
                files = list(data_dir.glob(pattern))
                found_files.extend(files)
            
            results['total_files'] = len(found_files)
            
            # ファイルの妥当性チェック
            for file_path in found_files:
                if self.is_valid_file(file_path):
                    results['valid_files'] += 1
                else:
                    results['invalid_files'] += 1
                    results['issues'].append(f"無効なファイル: {file_path.name}")
            
            # 不足ファイルの検出
            expected_count = self.get_expected_file_count(target_date)
            if results['valid_files'] < expected_count:
                results['missing_files'] = expected_count - results['valid_files']
                results['issues'].append(f"不足ファイル数: {results['missing_files']}")
                
        except Exception as e:
            self.logger.error(f"ファイルチェックエラー: {e}")
            results['issues'].append(f"ファイルチェックエラー: {e}")
    
    def check_data_content(self, data_dir: Path, target_date: str, results: Dict):
        """データ内容のチェック"""
        try:
            # レースデータファイルを取得
            race_files = list(data_dir.glob(f"race_data_{target_date}_*_R*.json"))
            
            for race_file in race_files:
                try:
                    with open(race_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # データ構造チェック
                    if not self.check_race_data_structure(data):
                        results['issues'].append(f"データ構造エラー: {race_file.name}")
                    
                    # データ内容チェック
                    content_issues = self.check_race_data_content(data)
                    results['issues'].extend([f"{race_file.name}: {issue}" for issue in content_issues])
                    
                except Exception as e:
                    results['issues'].append(f"ファイル読み込みエラー {race_file.name}: {e}")
            
            # オッズデータファイルを取得
            odds_files = list(data_dir.glob(f"odds_data_{target_date}_*_R*.json"))
            
            for odds_file in odds_files:
                try:
                    with open(odds_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # オッズデータ構造チェック
                    if not self.check_odds_data_structure(data):
                        results['issues'].append(f"オッズデータ構造エラー: {odds_file.name}")
                    
                except Exception as e:
                    results['issues'].append(f"オッズファイル読み込みエラー {odds_file.name}: {e}")
                    
        except Exception as e:
            self.logger.error(f"データ内容チェックエラー: {e}")
            results['issues'].append(f"データ内容チェックエラー: {e}")
    
    def is_valid_file(self, file_path: Path) -> bool:
        """ファイルの妥当性をチェック"""
        try:
            # ファイルサイズチェック
            if file_path.stat().st_size == 0:
                return False
            
            # JSON形式チェック
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            
            return True
            
        except Exception:
            return False
    
    def get_expected_file_count(self, target_date: str) -> int:
        """期待されるファイル数を取得"""
        # 簡易的な計算（実際の実装ではより詳細に）
        return 24  # 24会場 × 1日分
    
    def check_race_data_structure(self, data: Dict) -> bool:
        """レースデータの構造をチェック"""
        required_keys = ['race_info', 'race_entries']
        
        for key in required_keys:
            if key not in data:
                return False
        
        # race_entriesの構造チェック
        entries = data.get('race_entries', [])
        if not isinstance(entries, list) or len(entries) != 6:
            return False
        
        return True
    
    def check_race_data_content(self, data: Dict) -> List[str]:
        """レースデータの内容をチェック"""
        issues = []
        
        try:
            entries = data.get('race_entries', [])
            
            for i, entry in enumerate(entries):
                # 必須フィールドチェック
                required_fields = ['pit_number', 'racer', 'boat', 'motor', 'performance']
                
                for field in required_fields:
                    if field not in entry:
                        issues.append(f"艇{i+1}: {field}フィールドが不足")
                
                # データ型チェック
                if not isinstance(entry.get('pit_number'), int):
                    issues.append(f"艇{i+1}: pit_numberが整数ではありません")
                
                # 値の範囲チェック
                pit_number = entry.get('pit_number', 0)
                if pit_number < 1 or pit_number > 6:
                    issues.append(f"艇{i+1}: pit_numberが範囲外: {pit_number}")
            
        except Exception as e:
            issues.append(f"データ内容チェックエラー: {e}")
        
        return issues
    
    def check_odds_data_structure(self, data: Dict) -> bool:
        """オッズデータの構造をチェック"""
        if 'odds_data' not in data:
            return False
        
        odds_data = data.get('odds_data', [])
        if not isinstance(odds_data, list):
            return False
        
        return True
    
    def calculate_quality_score(self, results: Dict):
        """品質スコアを計算"""
        try:
            total_issues = len(results['issues'])
            valid_files = results['valid_files']
            total_files = results['total_files']
            
            if total_files == 0:
                results['quality_score'] = 0.0
                return
            
            # ファイル存在率
            file_score = valid_files / total_files if total_files > 0 else 0
            
            # エラー率
            error_penalty = min(total_issues * 0.1, 1.0)  # 最大1.0のペナルティ
            
            # 品質スコア計算
            quality_score = max(0.0, file_score - error_penalty)
            results['quality_score'] = round(quality_score * 100, 2)
            
        except Exception as e:
            self.logger.error(f"品質スコア計算エラー: {e}")
            results['quality_score'] = 0.0
    
    def save_quality_report(self, results: Dict) -> Optional[Path]:
        """品質レポートを保存"""
        try:
            # 出力ディレクトリ
            output_dir = self.project_root / "outputs" / "quality_reports"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # ファイル名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"quality_report_{results['target_date']}_{timestamp}.json"
            output_path = output_dir / filename
            
            # 保存
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"品質レポートを保存: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"品質レポート保存エラー: {e}")
            return None

def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='データ品質チェッカー')
    parser.add_argument('--date', type=str, help='チェック対象日 (YYYY-MM-DD)')
    parser.add_argument('--save-report', action='store_true', help='レポートを保存')
    
    args = parser.parse_args()
    
    checker = DataQualityChecker()
    
    # 品質チェック実行
    results = checker.check_data_quality(args.date)
    
    # 結果表示
    print(f"=== データ品質チェック結果 ===")
    print(f"対象日: {results['target_date']}")
    print(f"品質スコア: {results['quality_score']}")
    print(f"総ファイル数: {results['total_files']}")
    print(f"有効ファイル数: {results['valid_files']}")
    print(f"無効ファイル数: {results['invalid_files']}")
    print(f"不足ファイル数: {results['missing_files']}")
    
    if results['issues']:
        print(f"\n=== 問題点 ===")
        for issue in results['issues']:
            print(f"- {issue}")
    
    # レポート保存
    if args.save_report:
        output_path = checker.save_quality_report(results)
        if output_path:
            print(f"\nレポート保存: {output_path}")

if __name__ == "__main__":
    main() 