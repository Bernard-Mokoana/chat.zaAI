import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest
from src.utils.decoding import decode_bytes, decode_fields


class TestDecodeBytes:
    def test_decodes_utf8_bytes(self):
        assert decode_bytes(b"hello") == "hello"

    def test_decodes_bytearray(self):
        assert decode_bytes(bytearray(b"world")) == "world"

    def test_passthrough_string(self):
        assert decode_bytes("already str") == "already str"

    def test_decodes_integer_to_string(self):
        assert decode_bytes(42) == "42"

    def test_decodes_none_to_string(self):
        assert decode_bytes(None) == "None"


class TestDecodeFields:
    def test_valid_dict_with_mixed_bytes_and_str(self):
        raw = {b"key": b"value", b"num": 5}
        decoded = decode_fields(raw)
        assert decoded == {"key": "value", "num": "5"}

    def test_empty_dict(self):
        assert decode_fields({}) == {}

    def test_non_dict_returns_fallback(self):
        result = decode_fields("string input")
        assert result == {"raw_fallback_content": "string input"}

    def test_none_returns_fallback(self):
        result = decode_fields(None)
        assert result == {"raw_fallback_content": "None"}

    def test_nested_list_returns_fallback(self):
        result = decode_fields([b"a", b"b"])
        assert result == {"raw_fallback_content": "[b'a', b'b']"}
