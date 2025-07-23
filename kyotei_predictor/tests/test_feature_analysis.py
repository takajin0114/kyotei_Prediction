import pytest
from kyotei_predictor.pipelines import feature_analysis as fa

# --- analyze_featuresのモックテスト雛形 ---
def test_analyze_features_csv_mock(mocker):
    # pandas, os, plt等をモック
    mock_df = mocker.Mock(
        isnull=lambda: mocker.Mock(mean=lambda **kwargs: mocker.Mock(sort_values=lambda **kwargs: mocker.Mock(to_csv=lambda *a, **k: None))),
        describe=lambda **kwargs: mocker.Mock(T=mocker.Mock(to_csv=lambda *a, **k: None)),
        select_dtypes=lambda include: mocker.Mock(columns=["a", "b"], corr=lambda: mocker.Mock(to_csv=lambda *a, **k: None)),
        __getitem__=lambda self, key: mocker.Mock(),
        columns=["a", "b"],
        value_counts=lambda dropna: mocker.Mock(to_csv=lambda *a, **k: None, plot=lambda kind: mocker.Mock()),
        drop=lambda columns: mocker.Mock(),
        fillna=lambda v: mocker.Mock(),
        astype=lambda t: mocker.Mock()
    )
    mocker.patch("kyotei_predictor.pipelines.feature_analysis.pd.read_csv", return_value=mock_df)
    mocker.patch("kyotei_predictor.pipelines.feature_analysis.os.makedirs", return_value=None)
    mocker.patch("kyotei_predictor.pipelines.feature_analysis.plt.savefig", return_value=None)
    mocker.patch("kyotei_predictor.pipelines.feature_analysis.plt.close", return_value=None)
    mocker.patch("kyotei_predictor.pipelines.feature_analysis.sns.heatmap", return_value=None)
    mocker.patch("kyotei_predictor.pipelines.feature_analysis.pd.read_json", return_value=None)
    mocker.patch("kyotei_predictor.pipelines.feature_analysis.LabelEncoder", return_value=mocker.Mock(fit_transform=lambda x: [0,1]))
    mocker.patch("kyotei_predictor.pipelines.feature_analysis.RandomForestClassifier", return_value=mocker.Mock(fit=lambda X, y: None, feature_importances_=[0.7, 0.3]))
    fa.analyze_features("dummy.csv", target_col=None, output_dir="dummy_out") 