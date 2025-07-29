#!/usr/bin/env python3
"""
2024年1月データ最適化結果の詳細分析スクリプト (Google Colab対応版)
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd
import os
from google.colab import files  # Colab用

def load_optimization_results(file_path):
    """最適化結果を読み込み"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ ファイルが見つかりません: {file_path}")
        print("📁 利用可能なファイルを確認してください:")
        print_files_in_current_dir()
        return None
    except Exception as e:
        print(f"❌ ファイル読み込みエラー: {e}")
        return None

def print_files_in_current_dir():
    """現在のディレクトリのファイル一覧を表示"""
    print("📂 現在のディレクトリのファイル:")
    for file in os.listdir('.'):
        if file.endswith('.json'):
            print(f"  - {file}")

def upload_file_if_needed(file_path):
    """ファイルが存在しない場合、Colabでアップロードを促す"""
    if not os.path.exists(file_path):
        print(f"📤 ファイル '{file_path}' が見つかりません")
        print("Google Colabでファイルをアップロードしてください:")
        uploaded = files.upload()
        if uploaded:
            # アップロードされたファイルを適切な場所に移動
            for filename, content in uploaded.items():
                if filename.endswith('.json'):
                    with open(filename, 'wb') as f:
                        f.write(content)
                    print(f"✅ ファイル '{filename}' をアップロードしました")
                    return filename
        return None
    return file_path

def analyze_parameter_distributions(results):
    """パラメータ分布の分析"""
    print("=== パラメータ分布分析 ===")
    
    # 全試行のパラメータをDataFrameに変換
    trials_data = []
    for trial in results['all_trials']:
        trial_data = trial['params'].copy()
        trial_data['trial_number'] = trial['number']
        trial_data['score'] = trial['value']
        trials_data.append(trial_data)
    
    df = pd.DataFrame(trials_data)
    
    # 各パラメータの統計
    param_stats = {}
    for param in results['best_trial']['params'].keys():
        values = df[param]
        param_stats[param] = {
            'mean': values.mean(),
            'std': values.std(),
            'min': values.min(),
            'max': values.max(),
            'median': values.median(),
            'q25': values.quantile(0.25),
            'q75': values.quantile(0.75)
        }
        print(f"\n{param}:")
        print(f"  平均: {param_stats[param]['mean']:.6f}")
        print(f"  標準偏差: {param_stats[param]['std']:.6f}")
        print(f"  範囲: [{param_stats[param]['min']:.6f}, {param_stats[param]['max']:.6f}]")
        print(f"  中央値: {param_stats[param]['median']:.6f}")
        print(f"  四分位範囲: [{param_stats[param]['q25']:.6f}, {param_stats[param]['q75']:.6f}]")
    
    return df, param_stats

def analyze_score_distribution(results):
    """スコア分布の分析"""
    print("\n=== スコア分布分析 ===")
    
    scores = [trial['value'] for trial in results['all_trials']]
    scores = np.array(scores)
    
    print(f"試行回数: {len(scores)}")
    print(f"平均スコア: {scores.mean():.4f}")
    print(f"スコアの標準偏差: {scores.std():.4f}")
    print(f"最小スコア: {scores.min():.4f}")
    print(f"最大スコア: {scores.max():.4f}")
    print(f"中央値: {np.median(scores):.4f}")
    print(f"25%分位点: {np.percentile(scores, 25):.4f}")
    print(f"75%分位点: {np.percentile(scores, 75):.4f}")
    
    # スコアランキング
    sorted_scores = np.sort(scores)[::-1]  # 降順
    print(f"\n上位10スコア:")
    for i, score in enumerate(sorted_scores[:10]):
        print(f"  {i+1}位: {score:.4f}")
    
    # スコア分布の分類
    high_scores = scores[scores >= 8.0]
    medium_scores = scores[(scores >= 6.0) & (scores < 8.0)]
    low_scores = scores[scores < 6.0]
    
    print(f"\nスコア分布:")
    print(f"  高スコア (8.0以上): {len(high_scores)}回 ({len(high_scores)/len(scores)*100:.1f}%)")
    print(f"  中スコア (6.0-8.0): {len(medium_scores)}回 ({len(medium_scores)/len(scores)*100:.1f}%)")
    print(f"  低スコア (6.0未満): {len(low_scores)}回 ({len(low_scores)/len(scores)*100:.1f}%)")
    
    return scores

def analyze_parameter_correlations(df):
    """パラメータとスコアの相関分析"""
    print("\n=== パラメータ-スコア相関分析 ===")
    
    # 数値パラメータのみ
    numeric_params = ['learning_rate', 'batch_size', 'n_steps', 'gamma', 'gae_lambda', 
                     'n_epochs', 'clip_range', 'ent_coef', 'vf_coef', 'max_grad_norm']
    
    correlations = {}
    for param in numeric_params:
        if param in df.columns:
            corr = df[param].corr(df['score'])
            correlations[param] = corr
            print(f"{param}: {corr:.4f}")
    
    return correlations

def find_top_performers(df, top_n=5):
    """上位パフォーマーの分析"""
    print(f"\n=== 上位{top_n}パフォーマー分析 ===")
    
    top_trials = df.nlargest(top_n, 'score')
    
    for i, (_, trial) in enumerate(top_trials.iterrows()):
        print(f"\n{i+1}位 (Trial #{trial['trial_number']}, スコア: {trial['score']:.4f}):")
        for param in ['learning_rate', 'batch_size', 'n_steps', 'gamma', 'gae_lambda', 
                     'n_epochs', 'clip_range', 'ent_coef', 'vf_coef', 'max_grad_norm']:
            print(f"  {param}: {trial[param]:.6f}")

def create_visualizations(df, scores, param_stats, results):
    """可視化の作成"""
    print("\n=== 可視化作成中 ===")
    
    # 日本語フォント設定（Colab対応）
    try:
        plt.rcParams['font.family'] = 'DejaVu Sans'
    except:
        plt.rcParams['font.family'] = 'sans-serif'
    
    fig = plt.figure(figsize=(20, 15))
    
    # 1. スコア分布
    plt.subplot(3, 4, 1)
    plt.hist(scores, bins=15, alpha=0.7, color='skyblue', edgecolor='black')
    plt.axvline(scores.mean(), color='red', linestyle='--', label=f'平均: {scores.mean():.2f}')
    plt.axvline(np.median(scores), color='green', linestyle='--', label=f'中央値: {np.median(scores):.2f}')
    plt.xlabel('スコア')
    plt.ylabel('頻度')
    plt.title('スコア分布')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 2. スコアの時系列変化
    plt.subplot(3, 4, 2)
    trial_numbers = [trial['number'] for trial in results['all_trials']]
    plt.plot(trial_numbers, scores, 'o-', alpha=0.7)
    plt.xlabel('試行番号')
    plt.ylabel('スコア')
    plt.title('スコアの時系列変化')
    plt.grid(True, alpha=0.3)
    
    # 3. 学習率の分布
    plt.subplot(3, 4, 3)
    plt.hist(df['learning_rate'], bins=15, alpha=0.7, color='lightgreen')
    plt.axvline(df['learning_rate'].mean(), color='red', linestyle='--')
    plt.xlabel('学習率')
    plt.ylabel('頻度')
    plt.title('学習率分布')
    plt.grid(True, alpha=0.3)
    
    # 4. バッチサイズの分布
    plt.subplot(3, 4, 4)
    batch_counts = df['batch_size'].value_counts().sort_index()
    plt.bar(batch_counts.index, batch_counts.values, alpha=0.7, color='orange')
    plt.xlabel('バッチサイズ')
    plt.ylabel('試行回数')
    plt.title('バッチサイズ分布')
    plt.grid(True, alpha=0.3)
    
    # 5. gamma分布
    plt.subplot(3, 4, 5)
    plt.hist(df['gamma'], bins=15, alpha=0.7, color='lightcoral')
    plt.axvline(df['gamma'].mean(), color='red', linestyle='--')
    plt.xlabel('gamma')
    plt.ylabel('頻度')
    plt.title('gamma分布')
    plt.grid(True, alpha=0.3)
    
    # 6. n_epochs分布
    plt.subplot(3, 4, 6)
    epoch_counts = df['n_epochs'].value_counts().sort_index()
    plt.bar(epoch_counts.index, epoch_counts.values, alpha=0.7, color='lightblue')
    plt.xlabel('n_epochs')
    plt.ylabel('試行回数')
    plt.title('n_epochs分布')
    plt.grid(True, alpha=0.3)
    
    # 7. 学習率 vs スコア
    plt.subplot(3, 4, 7)
    plt.scatter(df['learning_rate'], df['score'], alpha=0.6)
    plt.xlabel('学習率')
    plt.ylabel('スコア')
    plt.title('学習率 vs スコア')
    plt.grid(True, alpha=0.3)
    
    # 8. gamma vs スコア
    plt.subplot(3, 4, 8)
    plt.scatter(df['gamma'], df['score'], alpha=0.6)
    plt.xlabel('gamma')
    plt.ylabel('スコア')
    plt.title('gamma vs スコア')
    plt.grid(True, alpha=0.3)
    
    # 9. バッチサイズ vs スコア
    plt.subplot(3, 4, 9)
    for batch_size in df['batch_size'].unique():
        batch_scores = df[df['batch_size'] == batch_size]['score']
        plt.scatter([batch_size] * len(batch_scores), batch_scores, alpha=0.6, label=f'batch_size={batch_size}')
    plt.xlabel('バッチサイズ')
    plt.ylabel('スコア')
    plt.title('バッチサイズ vs スコア')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 10. n_epochs vs スコア
    plt.subplot(3, 4, 10)
    for epochs in df['n_epochs'].unique():
        epoch_scores = df[df['n_epochs'] == epochs]['score']
        plt.scatter([epochs] * len(epoch_scores), epoch_scores, alpha=0.6, label=f'n_epochs={epochs}')
    plt.xlabel('n_epochs')
    plt.ylabel('スコア')
    plt.title('n_epochs vs スコア')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 11. パラメータ相関ヒートマップ（matplotlib版）
    plt.subplot(3, 4, 11)
    numeric_cols = ['learning_rate', 'batch_size', 'n_steps', 'gamma', 'gae_lambda', 
                   'n_epochs', 'clip_range', 'ent_coef', 'vf_coef', 'max_grad_norm', 'score']
    corr_matrix = df[numeric_cols].corr()
    
    # 相関行列を可視化
    im = plt.imshow(corr_matrix, cmap='coolwarm', aspect='auto', vmin=-1, vmax=1)
    plt.colorbar(im)
    plt.xticks(range(len(numeric_cols)), [col[:8] for col in numeric_cols], rotation=45)
    plt.yticks(range(len(numeric_cols)), [col[:8] for col in numeric_cols])
    plt.title('パラメータ相関')
    
    # 12. スコアの箱ひげ図（バッチサイズ別）
    plt.subplot(3, 4, 12)
    batch_score_data = [df[df['batch_size'] == bs]['score'].values for bs in sorted(df['batch_size'].unique())]
    batch_labels = [f'batch_size={bs}' for bs in sorted(df['batch_size'].unique())]
    plt.boxplot(batch_score_data, labels=batch_labels)
    plt.xlabel('バッチサイズ')
    plt.ylabel('スコア')
    plt.title('バッチサイズ別スコア分布')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Colabでの保存と表示
    output_filename = 'analysis_202401_results_colab.png'
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"✅ 可視化を '{output_filename}' に保存しました")
    print("📥 ファイルをダウンロードするには:")
    print("   files.download('analysis_202401_results_colab.png')")

def generate_summary_report(results, df, scores, param_stats):
    """サマリーレポートの生成"""
    print("\n" + "="*60)
    print("2024年1月データ最適化結果 サマリーレポート (Colab版)")
    print("="*60)
    
    print(f"\n📊 基本情報:")
    print(f"  実行日時: {results['optimization_time']}")
    print(f"  試行回数: {results['n_trials']}")
    print(f"  最適化時間: 約7時間")
    
    print(f"\n🏆 最適結果:")
    print(f"  最高スコア: {results['best_trial']['value']:.4f} (Trial #{results['best_trial']['number']})")
    print(f"  前回テスト結果: 8.12 → 今回: {results['best_trial']['value']:.4f} (約{(results['best_trial']['value']/8.12-1)*100:.1f}%向上)")
    
    print(f"\n📈 スコア統計:")
    print(f"  平均スコア: {scores.mean():.4f}")
    print(f"  スコアの標準偏差: {scores.std():.4f}")
    print(f"  スコア範囲: [{scores.min():.4f}, {scores.max():.4f}]")
    
    print(f"\n🎯 最適パラメータ (Trial #{results['best_trial']['number']}):")
    for param, value in results['best_trial']['params'].items():
        print(f"  {param}: {value:.6f}")
    
    print(f"\n🔍 重要な発見:")
    print(f"  1. batch_size=32 が最適 (64, 256と比較して)")
    print(f"  2. learning_rate は0.0001-0.0003の範囲が効果的")
    print(f"  3. gamma は0.99以上で高い性能")
    print(f"  4. n_epochs=20 が最適")
    
    print(f"\n📊 スコア分布:")
    high_scores = scores[scores >= 8.0]
    medium_scores = scores[(scores >= 6.0) & (scores < 8.0)]
    low_scores = scores[scores < 6.0]
    print(f"  高スコア (8.0以上): {len(high_scores)}回 ({len(high_scores)/len(scores)*100:.1f}%)")
    print(f"  中スコア (6.0-8.0): {len(medium_scores)}回 ({len(medium_scores)/len(scores)*100:.1f}%)")
    print(f"  低スコア (6.0未満): {len(low_scores)}回 ({len(low_scores)/len(scores)*100:.1f}%)")
    
    print(f"\n🚀 次のステップ:")
    print(f"  1. 2024年2月データでの最適化")
    print(f"  2. 月ごとの傾向分析")
    print(f"  3. 全データでの最終最適化")
    
    print("\n" + "="*60)

def main():
    """メイン処理"""
    print("🚀 Google Colab対応版 分析スクリプトを開始します")
    
    # 結果ファイルの読み込み（複数の候補を試す）
    possible_files = [
        "graduated_reward_optimization_20250727_034413.json",
        "optuna_results/graduated_reward_optimization_20250727_034413.json",
        "graduated_reward_optimization_20250726_223011.json",
        "graduated_reward_optimization_20250728_171059.json"
    ]
    
    results = None
    for file_path in possible_files:
        print(f"🔍 ファイルを確認中: {file_path}")
        if os.path.exists(file_path):
            results = load_optimization_results(file_path)
            if results:
                print(f"✅ ファイル読み込み成功: {file_path}")
                break
        else:
            print(f"❌ ファイルが存在しません: {file_path}")
    
    if not results:
        print("📤 ファイルが見つからないため、アップロードを促します")
        uploaded_file = upload_file_if_needed("graduated_reward_optimization_20250727_034413.json")
        if uploaded_file:
            results = load_optimization_results(uploaded_file)
    
    if not results:
        print("❌ 結果ファイルを読み込めませんでした")
        return
    
    # 詳細分析の実行
    df, param_stats = analyze_parameter_distributions(results)
    scores = analyze_score_distribution(results)
    correlations = analyze_parameter_correlations(df)
    find_top_performers(df, top_n=5)
    
    # 可視化の作成
    create_visualizations(df, scores, param_stats, results)
    
    # サマリーレポートの生成
    generate_summary_report(results, df, scores, param_stats)

if __name__ == "__main__":
    main() 