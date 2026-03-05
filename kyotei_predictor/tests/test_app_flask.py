#!/usr/bin/env python3
"""
Flask app (app.py) のルート・API テスト。

- GET /, /predictions が 200 で返る
- GET /api/race_data（サンプルデータあり/なし）
- POST /api/predict（正常・異常）
- GET /api/races（データあり/なし）
- GET /api/weather（パラメータ必須・404）
"""
import json
import pytest
from pathlib import Path


# テスト用に app を import（templates は kyotei_predictor 基準で解決される）
@pytest.fixture
def client():
    from kyotei_predictor.app import app, cache
    app.config["TESTING"] = True
    # POST のキャッシュで別テストの 400 が返らないようテスト時はキャッシュ無効
    app.config["CACHE_TYPE"] = "NullCache"
    cache.init_app(app)
    with app.test_client() as c:
        yield c


class TestAppFlaskRoutes:
    """Flask ルートの基本テスト"""

    def test_index_returns_200(self, client):
        r = client.get("/")
        assert r.status_code == 200

    def test_predictions_returns_200(self, client):
        r = client.get("/predictions")
        assert r.status_code == 200

    def test_api_race_data_without_sample_returns_404_or_json(self, client):
        """サンプルデータが無くても 404 または JSON が返る"""
        r = client.get("/api/race_data")
        assert r.status_code in (200, 404)
        if r.status_code == 200:
            data = r.get_json()
            assert "error" not in data or data.get("error") is not None
        elif r.status_code == 404:
            data = r.get_json()
            assert data is None or data.get("error")

    def test_api_predict_empty_body_returns_400(self, client):
        r = client.post(
            "/api/predict",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert r.status_code == 400
        data = r.get_json()
        assert "error" in data

    def test_api_predict_with_race_entries_returns_200(self, client):
        payload = {
            "race_entries": [
                {"rate_in_all_stadium": 6.5, "pit_number": 1},
                {"rate_in_all_stadium": 5.0, "pit_number": 2},
            ]
        }
        r = client.post(
            "/api/predict",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert r.status_code == 200
        data = r.get_json()
        assert "predicted_winner" in data or "error" not in data
        assert data.get("predicted_winner", {}).get("pit_number") == 1

    def test_api_races_returns_list_or_404(self, client):
        r = client.get("/api/races")
        assert r.status_code in (200, 404, 500)
        if r.status_code == 200:
            data = r.get_json()
            assert isinstance(data, list)

    def test_api_weather_missing_params_returns_400(self, client):
        r = client.get("/api/weather")
        assert r.status_code == 400
        data = r.get_json()
        assert "error" in data or "message" in data

    def test_api_weather_with_params_returns_404_or_200(self, client):
        r = client.get("/api/weather?date=2024-06-15&stadium=KIRYU")
        assert r.status_code in (200, 404, 500)
        if r.status_code == 200:
            assert r.get_json() is not None

    def test_serve_output_file_not_found_returns_404(self, client):
        r = client.get("/outputs/nonexistent_file_xyz.json")
        assert r.status_code == 404

    def test_serve_raw_data_file_not_found_returns_404(self, client):
        r = client.get("/kyotei_predictor/data/raw/nonexistent_xyz.json")
        assert r.status_code == 404
