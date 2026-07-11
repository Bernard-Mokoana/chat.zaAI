import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import os
import pytest
from src.config.settings import get_model_query_timeout, DEFAULT_MODEL_QUERY_TIMEOUT_SEC


class TestSettings:
    def test_returns_default_when_unset(self, monkeypatch):
        monkeypatch.delenv("MODEL_QUERY_TIMEOUT_SEC", raising=False)
        assert get_model_query_timeout() == DEFAULT_MODEL_QUERY_TIMEOUT_SEC

    def test_reads_valid_env(self, monkeypatch):
        monkeypatch.setenv("MODEL_QUERY_TIMEOUT_SEC", "45.5")
        assert get_model_query_timeout() == 45.5

    def test_invalid_string_returns_default(self, monkeypatch):
        monkeypatch.setenv("MODEL_QUERY_TIMEOUT_SEC", "not-a-float")
        assert get_model_query_timeout() == DEFAULT_MODEL_QUERY_TIMEOUT_SEC

    def test_zero_returns_default(self, monkeypatch):
        monkeypatch.setenv("MODEL_QUERY_TIMEOUT_SEC", "0")
        assert get_model_query_timeout() == DEFAULT_MODEL_QUERY_TIMEOUT_SEC

    def test_negative_returns_default(self, monkeypatch):
        monkeypatch.setenv("MODEL_QUERY_TIMEOUT_SEC", "-10")
        assert get_model_query_timeout() == DEFAULT_MODEL_QUERY_TIMEOUT_SEC
