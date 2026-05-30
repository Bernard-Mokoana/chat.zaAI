import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
import contextlib
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.routes.chat import chat
from src.routes.auth import auth
from src.services.conversation_services import ws_message_limiter

from src.middlewares.rateLimiter import (
    RateLimiterStore,
    cleanup_loop,
    get_client_ip,
    select_http_rule,
    should_skip_rate_limit,
)

load_dotenv()

limiter = RateLimiterStore()


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    cleanup_interval = float(os.environ.get("RATE_LIMIT_CLEANUP_INTERVAL", "600"))
    max_idle_seconds = float(os.environ.get("RATE_LIMIT_MAX_IDLE_SECONDS", "3600"))

    cleanup_tasks = [
        asyncio.create_task(
            cleanup_loop(
                limiter,
                interval_seconds=cleanup_interval,
                max_idle_seconds=max_idle_seconds,
            )
        ),
        asyncio.create_task(
            cleanup_loop(
                ws_message_limiter,
                interval_seconds=cleanup_interval,
                max_idle_seconds=max_idle_seconds,
            )
        ),
    ]

    try:
        yield
    finally:
        for task in cleanup_tasks:
            task.cancel()

        for task in cleanup_tasks:
            with contextlib.suppress(asyncio.CancelledError):
                await task


api = FastAPI(lifespan=lifespan)
api.include_router(chat)
api.include_router(auth)

allowed_origins = [
    origin.strip()
    for origin in os.environ.get(
    'ALLOWED_ORIGINS',
    'http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001'
).split(',')
]
api.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@api.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    path = request.url.path
    method = request.method

    if should_skip_rate_limit(path, method):
        return await call_next(request)
    
    client_ip = get_client_ip(request)
    rule = select_http_rule(path)

    result = limiter.check(key=client_ip, rule=rule)

# Check if the client has tokens available
    if not result.allowed:
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Too many requests. Please slow down and try again.",
                "rate_limit": {
                    "scope": rule.name,
                    "limit": result.limit,
                    "remaining": result.remaining,
                    "retry_after": result.retry_after,
                    "reset_at": result.reset_at,
                },
            },
            headers={
                "Retry-After": str(result.retry_after),
                "X-RateLimit-Scope": rule.name,
                "X-RateLimit-Limit": str(result.limit),
                "X-RateLimit-Remaining": str(result.remaining),
                "X-RateLimit-Reset": str(result.reset_at),
            }
        )
    
    # Request is allowed. Process it and add rate limit headers to the response
    response = await call_next(request)

    response.headers["X-RateLimit-Scope"] = rule.name
    response.headers["X-RateLimit-Limit"] = str(result.limit)
    response.headers["X-RateLimit-Remaining"] = str(result.remaining)
    response.headers["X-RateLimit-Reset"] = str(result.reset_at)
    return response

@api.get("/test")
async def root():
    return {"message": "API is Online"}

if __name__ == "__main__":
    if os.environ.get('APP_ENV') == "development":
        uvicorn.run("main:api", host="0.0.0.0", port=3500, reload=True)
    else:
        uvicorn.run("main:api", host="0.0.0.0", port=3500, reload=False)
        
