import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.model import query_model

class TestQueryModel:
    @pytest.mark.asyncio
    async def test_returns_result_within_timeout(self):
        gpt = MagicMock()
        gpt.query = MagicMock(return_value="model response")

        result = await query_model(gpt, "prompt", timeout=1.0)
        assert result == "model response"
        gpt.query.assert_called_once_with("prompt")

    @pytest.mark.asyncio
    async def test_timeout_cancels_future_and_spawns_background_task(self):
        gpt = MagicMock()
        gpt.query = MagicMock(side_effect=asyncio.sleep(10))

        loop = asyncio.get_event_loop()
        with patch.object(loop, "create_task") as mock_create_task:
            with pytest.raises(asyncio.TimeoutError):
                await query_model(gpt, "prompt", timeout=0.01)
            mock_create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_exception_from_model_propagates(self):
        gpt = MagicMock()
        gpt.query = MagicMock(side_effect=RuntimeError("boom"))

        with pytest.raises(RuntimeError, match="Model query failed"):
            await query_model(gpt, "prompt", timeout=1.0)

    @pytest.mark.asyncio
    async def test_timeout_does_not_await_long_future(self):
        gpt = MagicMock()
        gpt.query = MagicMock(side_effect=asyncio.sleep(10))

        start = asyncio.get_event_loop().time()
        with pytest.raises(asyncio.TimeoutError):
            await query_model(gpt, "prompt", timeout=0.05)
        elapsed = asyncio.get_event_loop().time() - start
        assert elapsed < 1.0
