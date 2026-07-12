import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import os
import logging
from unittest.mock import MagicMock, patch

import pytest

from src.model.gptj import GPT

logging.disable(logging.CRITICAL)


class TestResolveModelId:
    @patch.dict(os.environ, {"MODEL_ID": "custom/model"}, clear=False)
    def test_uses_model_id_env(self):
        gpt = GPT.__new__(GPT)
        assert gpt._resolve_model_id() == "custom/model"

    @patch.dict(os.environ, {"MODEL_URL": "https://huggingface.co/org/model-name/info"}, clear=False)
    def test_resolves_model_url_with_models(self):
        gpt = GPT.__new__(GPT)
        assert gpt._resolve_model_id() == "org/model-name"

    @patch.dict(os.environ, {"MODEL_URL": "https://huggingface.co/org/model-name"}, clear=True)
    def test_resolves_model_url_last_two_parts(self):
        gpt = GPT.__new__(GPT)
        assert gpt._resolve_model_id() == "org/model-name"

    @patch.dict(os.environ, {}, clear=True)
    def test_falls_back_to_default(self):
        gpt = GPT.__new__(GPT)
        assert gpt._resolve_model_id() == gpt.DEFAULT_MODEL_ID


class TestGPTInit:
    def test_init_raises_without_hf_token(self, monkeypatch):
        monkeypatch.delenv("HUGGINGFACE_INFERENCE_TOKEN", raising=False)
        with pytest.raises(RuntimeError, match="Missing HUGGINGFACE_INFERENCE_TOKEN"):
            GPT()

    @patch.dict(os.environ, {"HUGGINGFACE_INFERENCE_TOKEN": "hf-fake-token", "MODEL_ID": "fake/model"})
    @patch("src.model.gptj.InferenceClient")
    def test_init_sets_attributes(self, MockClient):
        gpt = GPT()
        assert isinstance(gpt.client, MagicMock)
        assert gpt.model_id == "fake/model"
        gpt.client.chat.completions.create.assert_not_called()

    @patch.dict(os.environ, {"HUGGINGFACE_INFERENCE_TOKEN": "hf-fake-token", "MAX_NEW_TOKENS": "9999"})
    @patch("src.model.gptj.InferenceClient")
    def test_init_parses_max_new_tokens(self, MockClient):
        gpt = GPT()
        assert gpt.max_new_tokens == 9999

    @patch.dict(os.environ, {"HUGGINGFACE_INFERENCE_TOKEN": "hf-fake-token", "MAX_NEW_TOKENS": "invalid"})
    @patch("src.model.gptj.InferenceClient")
    def test_init_falls_back_on_invalid_max_tokens(self, MockClient):
        gpt = GPT()
        assert gpt.max_new_tokens == GPT.DEFAULT_MAX_TOKENS


class TestGPTQuery:
    @patch.dict(os.environ, {"HUGGINGFACE_INFERENCE_TOKEN": "hf-fake-token"})
    @patch("src.model.gptj.InferenceClient")
    def test_query_returns_text(self, MockClient):
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "model reply"
        mock_response.choices = [mock_choice]
        MockClient.return_value.chat.completions.create.return_value = mock_response

        gpt = GPT()
        result = gpt.query("hello")
        assert result == "model reply"

    @patch.dict(os.environ, {"HUGGINGFACE_INFERENCE_TOKEN": "hf-fake-token"})
    @patch("src.model.gptj.InferenceClient")
    def test_query_empty_content_raises(self, MockClient):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=None))]
        MockClient.return_value.chat.completions.create.return_value = mock_response

        gpt = GPT()
        with pytest.raises(RuntimeError, match="Empty response from model"):
            gpt.query("hello")

    @patch.dict(os.environ, {"HUGGINGFACE_INFERENCE_TOKEN": "hf-fake-token"})
    @patch("src.model.gptj.InferenceClient")
    def test_query_wraps_exception(self, MockClient):
        MockClient.return_value.chat.completions.create.side_effect = RuntimeError("api down")
        gpt = GPT()
        with pytest.raises(RuntimeError, match="Model query failed: api down"):
            gpt.query("hello")
