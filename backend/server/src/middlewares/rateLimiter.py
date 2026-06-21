import asyncio
import logging
import os
import threading
import time
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RateLimitRule:
    name: str
    max_tokens: int
    refill_tokens: int
    refill_interval_seconds: float
@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    reset_at: int
    retry_after: int

class TokenBucket:
    def __init__(self, max_tokens: int, refill_tokens: int, refill_interval_seconds: float):
        if max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        if refill_tokens <= 0:
            raise ValueError("refill_tokens must be positive")
        if refill_interval_seconds <= 0:
            raise ValueError("refill_interval_seconds must be positive")

        self.max_tokens = max_tokens
        self.refill_tokens = refill_tokens
        self.refill_interval_seconds = refill_interval_seconds

        self.tokens = max_tokens
        self.refilled_at = time.monotonic()
        self.lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.refilled_at

        if elapsed < self.refill_interval_seconds:
            return

        refill_count = int(elapsed // self.refill_interval_seconds)
        tokens_to_add = refill_count * self.refill_tokens

        self.tokens = min(self.max_tokens, self.tokens + tokens_to_add)
        self.refilled_at += refill_count * self.refill_interval_seconds

    def consume(self, cost: int = 1) -> RateLimitResult:
        if cost <= 0:
            raise ValueError("cost must be positive")

        with self.lock:
            self._refill()

            if self.tokens >= cost:
                self.tokens -= cost
                allowed = True
            else:
                allowed = False

            reset_after = max(
                0,
                self.refill_interval_seconds - (time.monotonic() - self.refilled_at),
            )

            return RateLimitResult(
                allowed=allowed,
                limit=self.max_tokens,
                remaining=max(0, int(self.tokens)),
                reset_at=int(time.time() + reset_after),
                retry_after=max(1, int(reset_after)),
            )

class RateLimiterStore:
    def __init__(self):
        self._buckets: dict[str, TokenBucket] = {}
        self._last_seen: dict[str, float] = {}
        self._lock = threading.Lock()

    def check(self, key: str, rule: RateLimitRule, cost: int = 1) -> RateLimitResult:
        bucket_key = f"{rule.name}:{key}"

        with self._lock:
            bucket = self._buckets.get(bucket_key)

            if bucket is None:
                bucket = TokenBucket(
                    max_tokens=rule.max_tokens,
                    refill_tokens=rule.refill_tokens,
                    refill_interval_seconds=rule.refill_interval_seconds,
                )
                self._buckets[bucket_key] = bucket

            self._last_seen[bucket_key] = time.monotonic()

        return bucket.consume(cost)

    def cleanup(self, max_idle_seconds: float = 3600) -> None:
        now = time.monotonic()

        with self._lock:
            stale_keys = [
                key
                for key, last_seen in self._last_seen.items()
                if now - last_seen > max_idle_seconds
            ]

            for key in stale_keys:
                self._buckets.pop(key, None)
                self._last_seen.pop(key, None)

    def size(self) -> int:
        with self._lock:
            return len(self._buckets)
        
async def cleanup_loop(
    store: RateLimiterStore,
    interval_seconds: float = 600.0,
    max_idle_seconds: float = 3600.0,
) -> None:
    while True:
        before = store.size()
        store.cleanup(max_idle_seconds=max_idle_seconds)
        after = store.size()

        if after != before:
            logger.info(
                "Cleaned rate limiter store: before=%d after=%d removed=%d",
                before,
                after,
                before - after,
            )
        await asyncio.sleep(interval_seconds)

def _parse_int_env(name: str, default: str) -> int:
    val = os.environ.get(name, default)
    try:
        return int(val)
    except ValueError:
        raise ValueError(f"{name} must be a valid integer, got: {val!r}")

def _parse_float_env(name: str, default: str) -> float:
    val = os.environ.get(name,  default)
    try:
        return float(val)
    except ValueError:
        raise ValueError(f"{name} must be a valid float, got: {val!r}")

AUTH_RULE = RateLimitRule(
    name="auth",
    max_tokens=_parse_int_env("RATE_LIMIT_AUTH_MAX", "5"),
    refill_tokens=_parse_int_env("RATE_LIMIT_AUTH_REFILL", "5"),
    refill_interval_seconds=_parse_float_env("RATE_LIMIT_AUTH_INTERVAL", "60"),
)

CHAT_SESSION_RULE = RateLimitRule(
    name="chat_session",
    max_tokens=_parse_int_env("RATE_LIMIT_CHAT_SESSION_MAX", "20"),
    refill_tokens=_parse_int_env("RATE_LIMIT_CHAT_SESSION_REFILL", "20"),
    refill_interval_seconds=_parse_float_env("RATE_LIMIT_CHAT_SESSION_INTERVAL", "60"),
)

API_RULE = RateLimitRule(
    name="api",
    max_tokens=_parse_int_env("RATE_LIMIT_API_MAX", "120"),
    refill_tokens=_parse_int_env("RATE_LIMIT_API_REFILL", "120"),
    refill_interval_seconds=_parse_float_env("RATE_LIMIT_API_INTERVAL", "60"),
)

WS_MESSAGE_RULE = RateLimitRule(
    name="ws_message",
    max_tokens=_parse_int_env("RATE_LIMIT_WS_MESSAGE_MAX", "20"),
    refill_tokens=_parse_int_env("RATE_LIMIT_WS_MESSAGE_REFILL", "20"),
    refill_interval_seconds=_parse_float_env("RATE_LIMIT_WS_MESSAGE_INTERVAL", "60"),
)


def get_client_ip(request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    if request.client:
        return request.client.host

    return "unknown"


def select_http_rule(path: str) -> RateLimitRule:
    if path.startswith("/api/v1/auth/login"):
        return AUTH_RULE

    if path.startswith("/api/v1/auth/register"):
        return AUTH_RULE

    if path.startswith("/api/v1/auth/refresh"):
        return AUTH_RULE

    if path.startswith("/api/v1/chat/token"):
        return CHAT_SESSION_RULE

    if path.startswith("/api/v1/chat/refresh_token"):
        return CHAT_SESSION_RULE

    return API_RULE


def should_skip_rate_limit(path: str, method: str) -> bool:
    if method.upper() == "OPTIONS":
        return True

    return path in {
        "/docs",
        "/redoc",
        "/openapi.json",
    }
