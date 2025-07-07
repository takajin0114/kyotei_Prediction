import argparse
# frange関数を先に定義

def frange(start, stop, step):
    while start <= stop:
        yield start
        start += step

import json
import os
import csv
from typing import List, Dict, Any
from kyotei_predictor.utils.common import KyoteiUtils

# 入力ファイルパス（例）
# TRIFECTA_RESULTS_PATH = '../../outputs/trifecta_dependent_bulk_results_20250706_230617.json'
# ODDS_RESULTS_PATH = '../../outputs/real_odds_investment_results_20250706_231105.json'
# OUTPUT_CSV = 'ev_threshold_optimization_results.csv'

# 閾値リスト
# THRESHOLDS = [round(x, 2) for x in list(frange(0.8, 2.01, 0.05))]
STRATEGIES = {
    'conservative': 1.5,
    'balanced': 1.2,
    'aggressive': 1.0
}

def load_json(path: str) -> Any:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calc_performance(trifecta_data, odds_data, threshold):
    total_invest = 0
    total_return = 0
    hit_count = 0
    invest_count = 0
    returns = []
    for race in trifecta_data:
        for combo in race['predictions']:
            comb = combo['combination']
            prob = combo['probability']
            odds = odds_data.get(comb, 0)
            ev = KyoteiUtils.calculate_expected_value(prob, odds)
            if ev >= threshold:
                invest_count += 1
                total_invest += 1
                if combo.get('hit', False):
                    hit_count += 1
                    total_return += odds
                    returns.append(odds)
                else:
                    returns.append(0)
    hit_rate = hit_count / invest_count if invest_count else 0
    return_rate = total_return / total_invest if total_invest else 0
    max_drawdown = calc_max_drawdown(returns)
    return {
        'threshold': threshold,
        'invest_count': invest_count,
        'hit_count': hit_count,
        'hit_rate': hit_rate,
        'return_rate': return_rate,
        'max_drawdown': max_drawdown
    }

def calc_max_drawdown(returns):
    peak = 0
    trough = 0
    max_dd = 0
    balance = 0
    for r in returns:
        balance += r - 1
        if balance > peak:
            peak = balance
            trough = balance
        if balance < trough:
            trough = balance
            dd = peak - trough
            if dd > max_dd:
                max_dd = dd
    return max_dd

def main():
    parser = argparse.ArgumentParser(description='期待値閾値最適化ツール')
    parser.add_argument('--trifecta', type=str, default='../../outputs/trifecta_dependent_bulk_results_20250706_230617.json', help='予測結果ファイルパス')
    parser.add_argument('--odds', type=str, default='../../outputs/real_odds_investment_results_20250706_231105.json', help='オッズデータファイルパス')
    parser.add_argument('--output', type=str, default='ev_threshold_optimization_results.csv', help='出力CSVファイル名')
    parser.add_argument('--th_min', type=float, default=0.8, help='閾値最小値')
    parser.add_argument('--th_max', type=float, default=2.0, help='閾値最大値')
    parser.add_argument('--th_step', type=float, default=0.05, help='閾値刻み幅')
    args = parser.parse_args()

    trifecta_data = load_json(args.trifecta)
    odds_data = load_json(args.odds)
    # odds_data: {comb: odds, ...} 形式に変換
    if isinstance(odds_data, dict) and 'odds' in odds_data:
        odds_data = odds_data['odds']
    thresholds = [round(x, 2) for x in list(frange(args.th_min, args.th_max + 0.001, args.th_step))]
    results = []
    for threshold in thresholds:
        perf = calc_performance(trifecta_data, odds_data, threshold)
        results.append(perf)
    with open(args.output, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f'CSV出力完了: {args.output}')

if __name__ == '__main__':
    main() 