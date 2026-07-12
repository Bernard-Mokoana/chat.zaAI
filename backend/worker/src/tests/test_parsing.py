import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest
from src.utils.parsing import parse_stream_message


class TestParseStreamMessage:
    def test_valid_semantic_message_with_string_id(self):
        message = ("msg-1", {"token": "tok-1", "text": "hello"})
        assert parse_stream_message(message) == ("msg-1", "tok-1", "hello", 0)

    def test_valid_semantic_message_with_bytes_id_and_str_fields(self):
        message = (b"msg-2", {"token": "tok-2", "text": "hello"})
        assert parse_stream_message(message) == ("msg-2", "tok-2", "hello", 0)

    def test_original_format_token_in_field_name(self):
        message = ("msg-3", {"tok-3": "hello"})
        assert parse_stream_message(message) == ("msg-3", "tok-3", "hello", 0)

    def test_original_format_with_bytes_values(self):
        message = (b"msg-4", {b"tok-4": b"hello"})
        assert parse_stream_message(message) == ("msg-4", "tok-4", "hello", 0)

    def test_valid_semantic_message_with_bytes_and_values(self):
        message = (b"msg-5", {b"token": b"tok-5", b"text": b"hello"})
        assert parse_stream_message(message) == ("msg-5", "tok-5", "hello", 0)

    def test_semantic_message_with_retry_count(self):
        message = ("msg-5", {"token": "tok-5", "text": "hello", "retry_count": "2"})
        assert parse_stream_message(message) == ("msg-5", "tok-5", "hello", 2)

    def test_semantic_message_with_bytes_retry_count(self):
        message = ("msg-6", {b"token": b"tok-6", b"text": b"hello", b"retry_count": b"3"})
        assert parse_stream_message(message) == ("msg-6", "tok-6", "hello", 3)

    def test_invalid_message_not_list_or_tuple(self):
        assert parse_stream_message("bad") is None
        assert parse_stream_message({"token": "x", "text": "y"}) is None

    def test_invalid_message_too_short(self):
        assert parse_stream_message(()) is None
        assert parse_stream_message(("id",)) is None

    def test_empty_fields(self):
        assert parse_stream_message(("msg-10", {})) is None

    def test_non_dict_fields(self):
        assert parse_stream_message(("msg-11", "payload")) is None

    def test_empty_token_string_in_semantic_format(self):
        # semantic format: empty token is valid key match, but falsy after decode
        assert parse_stream_message(("msg-15", {"token": "", "text": "hello"})) is None

    def test_empty_text_string_in_semantic_format(self):
        assert parse_stream_message(("msg-16", {"token": "tok-16", "text": ""})) is None

    def test_invalid_retry_count_string(self):
        message = ("msg-17", {"token": "tok-17", "text": "hello", "retry_count": "abc"})
        assert parse_stream_message(message) == ("msg-17", "tok-17", "hello", 0)

    def test_negative_retry_count_clamped_to_zero(self):
        message = ("msg-18", {"token": "tok-18", "text": "hello", "retry_count": "-5"})
        assert parse_stream_message(message) == ("msg-18", "tok-18", "hello", 0)
