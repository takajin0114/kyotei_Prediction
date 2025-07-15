import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import LabelEncoder
import argparse
import os


def analyze_features(
    input_path: str,
    target_col: str | None = None,
    output_dir: str = "outputs/feature_analysis"
) -> None:
    """
    特徴量分布・相関・重要度分析を実行し、各種レポート・可視化を出力する。
    Args:
        input_path (str): 入力データ（CSV/JSONファイルパス）
        target_col (str|None): 重要度分析用のターゲット列名（省略可）
        output_dir (str): 出力ディレクトリ
    Returns:
        None
    """
    os.makedirs(output_dir, exist_ok=True)
    # データ読み込み
    if input_path.endswith('.csv'):
        df = pd.read_csv(input_path)
    elif input_path.endswith('.json'):
        df = pd.read_json(input_path)
    else:
        raise ValueError("サポートされていないファイル形式です")

    # 欠損率
    nulls = df.isnull().mean().sort_values(ascending=False)
    nulls.to_csv(f"{output_dir}/missing_ratio.csv")
    print("[INFO] 欠損率をmissing_ratio.csvに出力")

    # 基本統計量
    desc = df.describe(include='all').T
    desc.to_csv(f"{output_dir}/describe.csv")
    print("[INFO] 基本統計量をdescribe.csvに出力")

    # 相関行列（数値のみ）
    num_cols = df.select_dtypes(include=[np.number]).columns
    corr = df[num_cols].corr()
    corr.to_csv(f"{output_dir}/correlation.csv")
    plt.figure(figsize=(10,8))
    sns.heatmap(corr, annot=False, cmap='coolwarm')
    plt.title('Feature Correlation')
    plt.tight_layout()
    plt.savefig(f"{output_dir}/correlation_heatmap.png")
    plt.close()
    print("[INFO] 相関ヒートマップをcorrelation_heatmap.pngに出力")

    # カテゴリ分布
    cat_cols = df.select_dtypes(include=['object', 'category']).columns
    for col in cat_cols:
        vc = df[col].value_counts(dropna=False)
        vc.to_csv(f"{output_dir}/category_{col}_value_counts.csv")
        plt.figure()
        vc.plot(kind='bar')
        plt.title(f'Category Distribution: {col}')
        plt.tight_layout()
        plt.savefig(f"{output_dir}/category_{col}_bar.png")
        plt.close()
    print("[INFO] カテゴリ分布をcategory_*_value_counts.csv/bar.pngに出力")

    # 重要度分析（ターゲット指定時のみ）
    if target_col and target_col in df.columns:
        X = df.drop(columns=[target_col])
        y = df[target_col]
        # 欠損補完
        for col in X.columns:
            if X[col].dtype.kind in 'biufc':
                X[col] = X[col].fillna(X[col].median())
            else:
                X[col] = X[col].fillna('missing')
        # カテゴリエンコーディング
        for col in X.select_dtypes(include=['object', 'category']).columns:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
        # 分類器
        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        rf.fit(X, y)
        importances = pd.Series(rf.feature_importances_, index=X.columns).sort_values(ascending=False)
        importances.to_csv(f"{output_dir}/feature_importance.csv")
        plt.figure(figsize=(10,6))
        importances.head(20).plot(kind='barh')
        plt.title('Feature Importance (RandomForest)')
        plt.tight_layout()
        plt.savefig(f"{output_dir}/feature_importance.png")
        plt.close()
        print("[INFO] 重要度分析をfeature_importance.csv/pngに出力")
    else:
        print("[INFO] ターゲット列が指定されていないため重要度分析はスキップ")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="特徴量分布・相関・重要度分析スクリプト")
    parser.add_argument('--input', type=str, required=True, help='入力データ（CSV/JSON）')
    parser.add_argument('--target', type=str, default=None, help='ターゲット列（重要度分析用）')
    parser.add_argument('--output-dir', type=str, default="outputs/feature_analysis", help='出力ディレクトリ')
    args = parser.parse_args()
    analyze_features(args.input, args.target, args.output_dir) 