#!/usr/bin/env python3
"""utils.exceptions の拡張単体テスト（ValidationError, ConfigError, PredictionError, デコレータ, ErrorHandler）"""
import pytest

from kyotei_predictor.utils.exceptions import (
    ValidationError,
    ConfigError,
    PredictionError,
    DataError,
    handle_exception,
    safe_execute,
    ErrorHandler,
    get_error_handler,
    KyoteiError,
)


class TestExtendedExceptions:
    def test_validation_error_inherits_and_to_dict(self):
        e = ValidationError("invalid value", details={"field": "x"})
        assert e.message == "invalid value"
        d = e.to_dict()
        assert d["error"] == "ValidationError"
        assert d["message"] == "invalid value"
        assert d["details"] == {"field": "x"}

    def test_config_error(self):
        e = ConfigError("config file missing")
        assert isinstance(e, KyoteiError)
        assert e.message == "config file missing"

    def test_prediction_error(self):
        e = PredictionError("model failed", error_code="MODEL_ERR")
        assert e.error_code == "MODEL_ERR"


class TestHandleException:
    def test_returns_result_on_success(self):
        @handle_exception
        def ok():
            return 42
        assert ok() == 42

    def test_returns_none_on_kyotei_error(self, capsys):
        @handle_exception
        def fail():
            raise DataError("data missing")
        assert fail() is None
        out = capsys.readouterr()
        assert "DataError" in out.out or "data missing" in out.out

    def test_returns_none_on_generic_exception(self, capsys):
        @handle_exception
        def fail():
            raise ValueError("oops")
        assert fail() is None


class TestSafeExecute:
    def test_returns_result_on_success(self):
        assert safe_execute(lambda x: x + 1, 1) == 2

    def test_returns_none_on_exception(self, capsys):
        assert safe_execute(lambda: 1 / 0) is None


class TestErrorHandler:
    def test_log_error_increments_count(self):
        h = ErrorHandler()
        h.log_error(ValueError("test"))
        assert h.error_count == 1
        assert len(h.error_log) == 1
        assert "ValueError" in h.error_log[0]["type"]

    def test_get_error_summary(self):
        h = ErrorHandler()
        h.log_error(RuntimeError("e1"))
        h.log_error(RuntimeError("e2"))
        s = h.get_error_summary()
        assert s["total_errors"] == 2
        assert len(s["recent_errors"]) == 2

    def test_clear_errors(self):
        h = ErrorHandler()
        h.log_error(ValueError("x"))
        h.clear_errors()
        assert h.error_count == 0
        assert h.error_log == []

    def test_raise_if_too_many_errors(self):
        h = ErrorHandler()
        for _ in range(10):
            h.log_error(ValueError("x"))
        with pytest.raises(KyoteiError) as exc:
            h.raise_if_too_many_errors(max_errors=10)
        assert "TOO_MANY_ERRORS" in str(exc.value.error_code) or exc.value.error_code == "TOO_MANY_ERRORS"

    def test_raise_if_too_many_errors_does_not_raise_under_limit(self):
        h = ErrorHandler()
        h.log_error(ValueError("x"))
        h.raise_if_too_many_errors(max_errors=10)  # no raise


class TestGetErrorHandler:
    def test_returns_error_handler(self):
        assert isinstance(get_error_handler(), ErrorHandler)
