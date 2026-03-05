#!/usr/bin/env python3
"""utils.compression (DataCompressor) の単体テスト"""
import json
import tempfile
from pathlib import Path

import pytest

from kyotei_predictor.utils.compression import DataCompressor


class TestDataCompressor:
    def test_save_compressed_json_returns_true(self):
        c = DataCompressor()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            assert c.save_compressed_json({"a": 1, "b": "x"}, path) is True
            with open(path, "r", encoding="utf-8") as f:
                assert json.load(f) == {"a": 1, "b": "x"}
        finally:
            Path(path).unlink(missing_ok=True)

    def test_save_creates_parent_dir(self):
        c = DataCompressor()
        with tempfile.TemporaryDirectory() as d:
            path = str(Path(d) / "sub" / "out.json")
            assert c.save_compressed_json([1, 2, 3], path) is True
            assert Path(path).exists()
            assert json.load(open(path, encoding="utf-8")) == [1, 2, 3]

    def test_load_compressed_json_returns_data(self):
        c = DataCompressor()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump({"k": "v"}, f, ensure_ascii=False)
            path = f.name
        try:
            assert c.load_compressed_json(path) == {"k": "v"}
        finally:
            Path(path).unlink(missing_ok=True)

    def test_load_nonexistent_returns_none(self):
        c = DataCompressor()
        assert c.load_compressed_json("/nonexistent/path/file.json") is None

    def test_load_invalid_json_returns_none(self):
        c = DataCompressor()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            f.write("not json {")
            path = f.name
        try:
            assert c.load_compressed_json(path) is None
        finally:
            Path(path).unlink(missing_ok=True)

    def test_save_non_serializable_returns_false(self):
        c = DataCompressor()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            assert c.save_compressed_json({"x": lambda: 1}, path) is False
        finally:
            Path(path).unlink(missing_ok=True)
