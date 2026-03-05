#!/usr/bin/env python3
"""
utils.logger の単体テスト（リファクタ後の日時分秒・config 連携）。
"""
import re
import pytest


class TestLoggerConfig:
    """ログ設定読み込みのテスト"""

    def test_get_logging_format_returns_string(self):
        from kyotei_predictor.utils.logger import get_logging_format
        fmt = get_logging_format()
        assert isinstance(fmt, str)
        assert "%(asctime)s" in fmt or "asctime" in fmt

    def test_get_logging_datefmt_returns_string(self):
        from kyotei_predictor.utils.logger import get_logging_datefmt
        datefmt = get_logging_datefmt()
        assert isinstance(datefmt, str)
        # 日時分秒の書式が含まれる
        assert "%Y" in datefmt and "%H" in datefmt and "%S" in datefmt

    def test_get_logging_formatter_returns_formatter(self):
        import logging
        from kyotei_predictor.utils.logger import get_logging_formatter
        formatter = get_logging_formatter()
        assert isinstance(formatter, logging.Formatter)

    def test_format_timestamp_contains_date_and_time(self):
        from kyotei_predictor.utils.logger import format_timestamp
        ts = format_timestamp()
        # YYYY-MM-DD HH:MM:SS 形式
        assert re.match(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}", ts), f"unexpected format: {ts!r}"

    def test_format_log_line_prefixed_with_timestamp(self):
        from kyotei_predictor.utils.logger import format_log_line
        line = format_log_line("hello")
        assert "[20" in line or "[19" in line  # 日付 [YYYY-
        assert "hello" in line
