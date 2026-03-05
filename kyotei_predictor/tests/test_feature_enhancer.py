#!/usr/bin/env python3
"""pipelines.feature_enhancer の単体テスト"""
import pandas as pd
import pytest


class TestFeatureEnhancer:
    def test_import(self):
        from kyotei_predictor.pipelines.feature_enhancer import FeatureEnhancer
        assert FeatureEnhancer is not None

    def test_enhance_adds_columns(self):
        from kyotei_predictor.pipelines.feature_enhancer import FeatureEnhancer
        enhancer = FeatureEnhancer()
        df = pd.DataFrame({
            "win_rate": [50.0, 60.0],
            "motor_win_rate": [55.0, 58.0],
            "local_win_rate": [45.0, 50.0],
            "boat_class": ["A1", "B1"],
            "weather_condition": ["晴", "曇"],
        })
        out = enhancer.enhance(df.copy(), auto_correct=True)
        assert "speed_index" in out.columns
        assert "stability" in out.columns
        assert len(out) == 2
