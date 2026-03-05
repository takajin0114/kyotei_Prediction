#!/usr/bin/env python3
"""errors モジュールの単体テスト"""
import pytest


class TestAPIError:
    def test_init_and_to_dict(self):
        from kyotei_predictor.errors import APIError
        e = APIError("bad request", status_code=400, payload={"key": "value"})
        assert e.message == "bad request"
        assert e.status_code == 400
        d = e.to_dict()
        assert d["message"] == "bad request"
        assert d["status_code"] == 400
        assert d["key"] == "value"

    def test_register_error_handlers(self):
        from kyotei_predictor.errors import register_error_handlers, APIError
        from flask import Flask
        app = Flask(__name__)
        register_error_handlers(app)

        @app.route("/api-error")
        def raise_api_error():
            raise APIError("test error", status_code=400, payload={"key": "v"})

        @app.route("/server-error")
        def raise_server_error():
            raise RuntimeError("trigger 500")

        with app.test_client() as c:
            r = c.get("/nonexistent")
            assert r.status_code == 404
            data = r.get_json()
            assert data is not None
            assert data.get("status_code") == 404

            r2 = c.get("/api-error")
            assert r2.status_code == 400
            assert r2.get_json()["message"] == "test error"

            r3 = c.get("/server-error")
            assert r3.status_code == 500
            assert r3.get_json()["status_code"] == 500
