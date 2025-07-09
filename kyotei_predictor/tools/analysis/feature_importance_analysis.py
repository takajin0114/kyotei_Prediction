import os
import argparse
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from kyotei_predictor.pipelines.data_preprocessor import DataPreprocessor
from kyotei_predictor.pipelines.feature_enhancer import FeatureEnhancer
from kyotei_predictor.pipelines.trifecta_dependent_model import TrifectaDependentModel


def analyze_feature_importance(data_dir, output_dir, max_files=500, miss_samples_path=None):
    os.makedirs(output_dir, exist_ok=True)
    files = [f for f in os.listdir(data_dir) if f.startswith('race_data_') and f.endswith('.json')]
    # 失敗レースのみ抽出する場合
    if miss_samples_path:
        with open(miss_samples_path, 'r', encoding='utf-8') as f:
            miss_list = json.load(f)
        miss_files = set([d['file'] for d in miss_list if 'file' in d])
        files = [f for f in files if f in miss_files]
    records = []
    preprocessor = DataPreprocessor()
    enhancer = FeatureEnhancer()
    model = TrifectaDependentModel()
    model.learn_conditional_probabilities(data_dir=data_dir, max_files=max_files)

    for i, fname in enumerate(files[:max_files]):
        with open(os.path.join(data_dir, fname), 'r', encoding='utf-8') as f:
            race_data = json.load(f)
        # 特徴量生成
        base_df = preprocessor._create_base_features(race_data)
        enhanced_df = enhancer.enhance(base_df)
        # 予測確率
        pred = model.calculate_dependent_probabilities(race_data)
        if not pred or 'top_combinations' not in pred:
            continue
        top_prob = pred['top_combinations'][0]['probability']
        # 1レースごとに特徴量＋上位確率を記録
        row = enhanced_df.iloc[0].to_dict()
        row['top_prob'] = top_prob
        row['file'] = fname
        records.append(row)

    df = pd.DataFrame(records)
    if df.empty:
        print('No valid records for analysis.')
        return

    # 特徴量ごとの値と上位確率の関係を可視化
    for col in [c for c in df.columns if c not in ('top_prob','file')]:
        plt.figure(figsize=(6,4))
        sns.scatterplot(x=df[col], y=df['top_prob'])
        plt.title(f'Feature: {col} vs Top Prediction Probability')
        plt.xlabel(col)
        plt.ylabel('Top Prediction Probability')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'feature_vs_topprob_{col}.png'))
        plt.close()

    # 数値特徴量のみで相関ヒートマップ
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if 'top_prob' in numeric_cols:
        numeric_cols.remove('top_prob')
    if numeric_cols:
        plt.figure(figsize=(8,6))
        corr = df[numeric_cols + ['top_prob']].corr()
        sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm')
        plt.title('Feature Correlation Matrix (Numeric Only)')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'feature_correlation_matrix.png'))
        plt.close()

    # カテゴリ変数ごとにtop_probの箱ひげ図
    for cat_col in df.select_dtypes(include=['object']).columns:
        if cat_col in ('file',):
            continue
        plt.figure(figsize=(8,4))
        sns.boxplot(x=df[cat_col], y=df['top_prob'])
        plt.title(f'Top Prediction Probability by {cat_col}')
        plt.xlabel(cat_col)
        plt.ylabel('Top Prediction Probability')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'topprob_by_{cat_col}.png'))
        plt.close()

    print(f'Feature importance analysis completed. Results saved to {output_dir}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, required=True)
    parser.add_argument('--output_dir', type=str, required=True)
    parser.add_argument('--max_files', type=int, default=500)
    parser.add_argument('--miss_samples', type=str, default=None, help='miss_samples_*.jsonのパス（失敗レースのみ分析したい場合）')
    args = parser.parse_args()
    analyze_feature_importance(args.data_dir, args.output_dir, args.max_files, args.miss_samples)

if __name__ == '__main__':
    main() 