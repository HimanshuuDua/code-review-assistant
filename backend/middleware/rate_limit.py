import time
from collections import defaultdict

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

from backend.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 30, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith("/api/review"):
            return await call_next(request)

        ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
        ip = ip.split(",")[0].strip()
        now = time.time()
        window_start = now - self.window_seconds
        self._hits[ip] = [t for t in self._hits[ip] if t > window_start]

        if len(self._hits[ip]) >= self.max_requests:
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again in a minute.")

        self._hits[ip].append(now)
        return await call_next(request)


def add_rate_limit(app) -> None:
    if settings.rate_limit_enabled:
        app.add_middleware(RateLimitMiddleware, max_requests=settings.rate_limit_per_minute)
