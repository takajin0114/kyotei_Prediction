#!/usr/bin/env python3
"""
選手名取得エラー分析ツール
選手名解析エラーの詳細分析と修正提案を行う
"""

import os
import json
import argparse
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Any
import glob

def load_racer_error_logs(log_dir: str) -> List[Dict[str, Any]]:
    """選手名取得エラーログを読み込み"""
    errors = []
    log_pattern = os.path.join(log_dir, "racer_errors_*.jsonl")
    
    for log_file in glob.glob(log_pattern):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        errors.append(json.loads(line))
        except Exception as e:
            print(f"⚠️  ログファイル読み込みエラー {log_file}: {e}")
    
    return errors

def analyze_racer_errors(errors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """選手名取得エラーを分析"""
    if not errors:
        return {"message": "エラーログが見つかりません"}
    
    # 基本統計
    total_errors = len(errors)
    error_types = Counter(error.get('error_type', 'unknown') for error in errors)
    
    # 会場別統計
    stadium_stats = defaultdict(int)
    for error in errors:
        stadium_stats[error.get('stadium', 'unknown')] += 1
    
    # 日付別統計
    date_stats = defaultdict(int)
    for error in errors:
        date = error.get('date', 'unknown')
        date_stats[date] += 1
    
    # エラーメッセージの分析
    error_messages = []
    for error in errors:
        msg = error.get('error_message', '')
        if msg:
            error_messages.append(msg)
    
    # 問題の文字列パターン分析
    problem_strings = []
    for error in errors:
        details = error.get('error_details', {})
        args = details.get('args', [])
        if args:
            problem_strings.extend(args)
    
    return {
        "total_errors": total_errors,
        "error_types": dict(error_types),
        "stadium_stats": dict(stadium_stats),
        "date_stats": dict(date_stats),
        "error_messages": error_messages[:10],  # 最新10件
        "problem_strings": problem_strings[:10],  # 最新10件
        "analysis_timestamp": datetime.now().isoformat()
    }

def generate_fix_suggestions(analysis: Dict[str, Any]) -> List[str]:
    """修正提案を生成"""
    suggestions = []
    
    if analysis.get("total_errors", 0) == 0:
        suggestions.append("✅ エラーが検出されませんでした")
        return suggestions
    
    total_errors = analysis["total_errors"]
    
    # エラー数の多い会場への対応
    stadium_stats = analysis.get("stadium_stats", {})
    if stadium_stats:
        top_stadiums = sorted(stadium_stats.items(), key=lambda x: x[1], reverse=True)[:3]
        suggestions.append(f"🏟️  エラーが多い会場（上位3会場）:")
        for stadium, count in top_stadiums:
            suggestions.append(f"   - {stadium}: {count}件 ({count/total_errors*100:.1f}%)")
    
    # エラーが多い日付への対応
    date_stats = analysis.get("date_stats", {})
    if date_stats:
        top_dates = sorted(date_stats.items(), key=lambda x: x[1], reverse=True)[:5]
        suggestions.append(f"📅 エラーが多い日付（上位5日）:")
        for date, count in top_dates:
            suggestions.append(f"   - {date}: {count}件")
    
    # 問題の文字列パターンへの対応
    problem_strings = analysis.get("problem_strings", [])
    if problem_strings:
        suggestions.append(f"🔍 問題の文字列パターン:")
        for i, string in enumerate(problem_strings[:5], 1):
            suggestions.append(f"   {i}. '{string}'")
        suggestions.append("   → これらの文字列パターンに対する解析ロジックの改善が必要")
    
    # 一般的な修正提案
    suggestions.extend([
        "🛠️  修正提案:",
        "   1. 選手名解析ロジックの強化",
        "   2. 特殊文字や記号の処理改善",
        "   3. エラー発生時のリトライ回数増加",
        "   4. 部分データ保存機能の活用",
        "   5. 手動確認が必要なケースの特定"
    ])
    
    return suggestions

def main():
    parser = argparse.ArgumentParser(description="選手名取得エラー分析ツール")
    parser.add_argument('--log-dir', type=str, 
                       default=os.path.join(os.path.dirname(__file__), '..', '..', 'logs', 'racer_errors'),
                       help='エラーログディレクトリのパス')
    parser.add_argument('--output', type=str, help='分析結果の出力ファイル（JSON）')
    args = parser.parse_args()
    
    print("🔍 選手名取得エラー分析ツール")
    print("=" * 50)
    
    # エラーログ読み込み
    print(f"📂 ログディレクトリ: {args.log_dir}")
    errors = load_racer_error_logs(args.log_dir)
    
    if not errors:
        print("❌ エラーログが見つかりません")
        return
    
    print(f"📊 読み込み完了: {len(errors)}件のエラー")
    
    # エラー分析
    print("\n🔍 エラー分析中...")
    analysis = analyze_racer_errors(errors)
    
    # 結果表示
    print(f"\n📈 分析結果:")
    print(f"  総エラー数: {analysis['total_errors']}件")
    
    if analysis.get('stadium_stats'):
        print(f"\n🏟️  会場別エラー数:")
        for stadium, count in sorted(analysis['stadium_stats'].items(), key=lambda x: x[1], reverse=True):
            print(f"   {stadium}: {count}件")
    
    if analysis.get('date_stats'):
        print(f"\n📅 日付別エラー数（上位5日）:")
        for date, count in sorted(analysis['date_stats'].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   {date}: {count}件")
    
    # 修正提案
    print(f"\n💡 修正提案:")
    suggestions = generate_fix_suggestions(analysis)
    for suggestion in suggestions:
        print(f"   {suggestion}")
    
    # 結果保存
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, ensure_ascii=False, indent=2)
            print(f"\n💾 分析結果を保存しました: {args.output}")
        except Exception as e:
            print(f"❌ 結果保存エラー: {e}")
    
    print(f"\n✅ 分析完了")

if __name__ == "__main__":
    main() 