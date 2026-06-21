import pytest
import time
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from backend.server.src.middlewares.rateLimiter import (
    TokenBucket,
    RateLimiterStore,
    RateLimitRule,
    cleanup_loop,
    _parse_int_env,
    _parse_float_env,
    get_client_ip,
    select_http_rule,
    should_skip_rate_limit,
    AUTH_RULE,
    CHAT_SESSION_RULE,
    API_RULE
)

class TestTokenBucket:
    def test_bucket_initialization_invalid_args(self):
        with pytest.raises(ValueError, match="max_tokens must be positive"):
            TokenBucket(max_tokens=0, refill_tokens=10, refill_interval_seconds=60)
            
        with pytest.raises(ValueError, match="refill_tokens must be positive"):
            TokenBucket(max_tokens=10, refill_tokens=-5, refill_interval_seconds=60)

        with pytest.raises(ValueError, match="refill_interval_seconds must be positive"):
            TokenBucket(max_tokens=10, refill_tokens=10, refill_interval_seconds=0)

    @patch("backend.server.src.middlewares.rateLimiter.time.monotonic")
    def test_consume_happy_path(self, mock_monotonic):
        mock_monotonic.return_value = 1000.0 
        bucket = TokenBucket(max_tokens=5, refill_tokens=5, refill_interval_seconds=60)
        
        result = bucket.consume(cost=1)
        
        assert result.allowed is True
        assert result.remaining == 4
        assert bucket.tokens == 4

    @patch("backend.server.src.middlewares.rateLimiter.time.monotonic")
    def test_consume_exceeds_limit(self, mock_monotonic):
        mock_monotonic.return_value = 1000.0
        bucket = TokenBucket(max_tokens=5, refill_tokens=5, refill_interval_seconds=60)
        
        bucket.consume(cost=5)
        
        result = bucket.consume(cost=1)
        
        assert result.allowed is False
        assert result.remaining == 0
        assert bucket.tokens == 0

    @patch("backend.server.src.middlewares.rateLimiter.time.monotonic")
    def test_refill_logic(self, mock_monotonic):
        mock_monotonic.return_value = 1000.0
        bucket = TokenBucket(max_tokens=10, refill_tokens=5, refill_interval_seconds=10.0)
        
        bucket.consume(cost=8)
        assert bucket.tokens == 2
        
        mock_monotonic.return_value = 1015.0
        
        result = bucket.consume(cost=1)
        
        assert result.allowed is True
        assert result.remaining == 6 
        assert bucket.tokens == 6

class TestRateLimiterStore:
    def test_store_check_creates_bucket(self):
        store = RateLimiterStore()
        rule = RateLimitRule(name="test_rule", max_tokens=10, refill_tokens=1, refill_interval_seconds=60.0)
        
        result = store.check(key="user_123", rule=rule)
        
        assert result.allowed is True
        assert store.size() == 1

    @patch("backend.server.src.middlewares.rateLimiter.time.monotonic")
    def test_store_cleanup_removes_stale_keys(self, mock_monotonic):
        store = RateLimiterStore()
        rule = RateLimitRule(name="test_rule", max_tokens=10, refill_tokens=1, refill_interval_seconds=60.0)
        
        mock_monotonic.return_value = 100.0
        store.check(key="active_user", rule=rule)
        
        mock_monotonic.return_value = 5000.0
        
        store.cleanup(max_idle_seconds=3600.0)
        
        assert store.size() == 0

@pytest.mark.asyncio
class TestCleanupLoop:
    @patch("backend.server.src.middlewares.rateLimiter.asyncio.sleep")
    async def test_cleanup_loop_execution(self, mock_sleep):
        store = MagicMock(spec=RateLimiterStore)
        store.size.side_effect = [5, 2] 
        
        mock_sleep.side_effect = asyncio.CancelledError()
        
        try:
            await cleanup_loop(store=store, interval_seconds=10.0, max_idle_seconds=60.0)
        except asyncio.CancelledError:
            pass
            
        store.cleanup.assert_called_once_with(max_idle_seconds=60.0)


class TestRateLimiterHelpers:
    @patch.dict("os.environ", {"VALID_INT": "100", "INVALID_INT": "abc"})
    def test_parse_int_env(self):
        assert _parse_int_env("VALID_INT", "10") == 100
        assert _parse_int_env("MISSING_INT", "50") == 50
        
        with pytest.raises(ValueError, match="must be a valid integer"):
            _parse_int_env("INVALID_INT", "10")

    @patch.dict("os.environ", {"VALID_FLOAT": "1.5", "INVALID_FLOAT": "xyz"})
    def test_parse_float_env(self):
        assert _parse_float_env("VALID_FLOAT", "2.0") == 1.5
        assert _parse_float_env("MISSING_FLOAT", "3.14") == 3.14
        
        with pytest.raises(ValueError, match="must be a valid float"):
            _parse_float_env("INVALID_FLOAT", "1.0")

    def test_get_client_ip(self):
        mock_request = MagicMock()
        
        mock_request.headers = {"x-forwarded-for": "203.0.113.1, 198.51.100.1"}
        assert get_client_ip(mock_request) == "203.0.113.1"

        mock_request.headers = {"x-real-ip": "198.51.100.2"}
        assert get_client_ip(mock_request) == "198.51.100.2"
        
        mock_request.headers = {}
        mock_request.client.host = "10.0.0.5"
        assert get_client_ip(mock_request) == "10.0.0.5"

    def test_select_http_rule(self):
        assert select_http_rule("/api/v1/auth/login").name == AUTH_RULE.name
        assert select_http_rule("/api/v1/chat/token").name == CHAT_SESSION_RULE.name
        assert select_http_rule("/api/v1/some-other-endpoint").name == API_RULE.name

    def test_should_skip_rate_limit(self):
        assert should_skip_rate_limit("/api/v1/data", method="OPTIONS") is True
        assert should_skip_rate_limit("/docs", method="GET") is True
        assert should_skip_rate_limit("/openapi.json", method="GET") is True
        assert should_skip_rate_limit("/api/v1/chat/token", method="POST") is False