import pytest
from kyotei_predictor.pipelines.data_preprocessor import DataPreprocessor

# --- _create_base_featuresのテスト雛形 ---
def test_create_base_features():
    prep = DataPreprocessor()
    race_data = {
        'race_entries': [
            {
                'performance': {'rate_in_all_stadium': 6.5, 'rate_in_event_going_stadium': 5.2},
                'motor': {'quinella_rate': 30.0},
                'racer': {'current_rating': 'A1'}
            },
            {
                'performance': {},
                'motor': {},
                'racer': {}
            }
        ],
        'weather_condition': {'weather': 'FINE'}
    }
    df = prep._create_base_features(race_data)
    assert 'win_rate' in df.columns
    assert 'boat_class' in df.columns
    assert df.shape[0] == 2

# --- fit_transformのモックテスト雛形 ---
def test_fit_transform_mock(mocker):
    prep = DataPreprocessor()
    mock_df = mocker.Mock()
    mocker.patch.object(prep, '_create_base_features', return_value=mock_df)
    prep.preprocessor = mocker.Mock(fit_transform=lambda x: 'transformed')
    result = prep.fit_transform({'dummy': 1})
    assert result == 'transformed' 