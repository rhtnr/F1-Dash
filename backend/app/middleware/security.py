"""Security middleware for the F1 Plots API."""

import hashlib
import hmac
import logging
import secrets
import time
from typing import Callable, Optional

from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # XSS protection (legacy but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Prevent caching of sensitive data
        if "/api/" in request.url.path:
            response.headers["Cache-Control"] = "no-store, max-age=0"

        # Content Security Policy - adjust for your needs
        # This allows D3.js from CDN and inline styles (needed for charts)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://d3js.org https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob:; "
            "connect-src 'self' http://localhost:* https://localhost:*; "
            "frame-ancestors 'none';"
        )

        # Permissions Policy (formerly Feature-Policy)
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()"
        )

        return response


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    API Key authentication middleware.

    For sensitive endpoints (ingestion, training), require a valid API key.
    Public endpoints (sessions, laps, telemetry reads) don't require auth.
    """

    # Endpoints that require API key authentication
    PROTECTED_PATHS = [
        "/api/v1/ingest",
        "/api/v1/predictions/train",
    ]

    # Endpoints that are always public
    PUBLIC_PATHS = [
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/static",
    ]

    def __init__(self, app, api_keys: list[str] | None = None):
        super().__init__(app)
        self.api_keys = set(api_keys) if api_keys else set()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        # Skip auth for public paths
        if any(path.startswith(p) for p in self.PUBLIC_PATHS):
            return await call_next(request)

        # Skip auth for GET requests to API (read-only is public)
        if request.method == "GET" and path.startswith("/api/"):
            return await call_next(request)

        # Check if path requires authentication
        requires_auth = any(path.startswith(p) for p in self.PROTECTED_PATHS)

        if requires_auth and self.api_keys:
            # Get API key from header
            api_key = request.headers.get("X-API-Key")

            if not api_key:
                logger.warning(f"Missing API key for protected endpoint: {path}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "API key required"},
                )

            # Use constant-time comparison to prevent timing attacks
            if not self._validate_api_key(api_key):
                logger.warning(f"Invalid API key attempt for: {path}")
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Invalid API key"},
                )

        return await call_next(request)

    def _validate_api_key(self, provided_key: str) -> bool:
        """Validate API key using constant-time comparison."""
        for valid_key in self.api_keys:
            if secrets.compare_digest(provided_key, valid_key):
                return True
        return False


class RateLimitState:
    """Simple in-memory rate limit state."""

    def __init__(self):
        self.requests: dict[str, list[float]] = {}

    def is_rate_limited(
        self, key: str, max_requests: int, window_seconds: int
    ) -> bool:
        """Check if a key is rate limited."""
        now = time.time()
        window_start = now - window_seconds

        # Get existing requests for this key
        if key not in self.requests:
            self.requests[key] = []

        # Clean up old requests
        self.requests[key] = [t for t in self.requests[key] if t > window_start]

        # Check if rate limited
        if len(self.requests[key]) >= max_requests:
            return True

        # Record this request
        self.requests[key].append(now)
        return False


# Global rate limit state (in production, use Redis)
_rate_limit_state = RateLimitState()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware.

    Different limits for different endpoint types:
    - General API: 100 requests/minute
    - Ingestion: 5 requests/minute
    - Training: 2 requests/minute
    """

    # Rate limits: (max_requests, window_seconds)
    RATE_LIMITS = {
        "/api/v1/ingest": (5, 60),  # 5 per minute
        "/api/v1/predictions/train": (2, 60),  # 2 per minute
        "/api/": (100, 60),  # 100 per minute for general API
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client identifier (IP address)
        client_ip = self._get_client_ip(request)
        path = request.url.path

        # Find applicable rate limit
        max_requests, window = self._get_rate_limit(path)

        # Create rate limit key
        rate_key = f"{client_ip}:{path.split('/')[3] if '/api/v1/' in path else 'general'}"

        # Check rate limit
        if _rate_limit_state.is_rate_limited(rate_key, max_requests, window):
            logger.warning(f"Rate limit exceeded for {client_ip} on {path}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": window,
                },
                headers={"Retry-After": str(window)},
            )

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Window"] = str(window)

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP, handling proxies."""
        # Check for forwarded header (when behind proxy/load balancer)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _get_rate_limit(self, path: str) -> tuple[int, int]:
        """Get rate limit for a path."""
        for prefix, limit in self.RATE_LIMITS.items():
            if path.startswith(prefix):
                return limit
        return (100, 60)  # Default


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validate and sanitize incoming requests."""

    # Maximum content length (10MB)
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_CONTENT_LENGTH:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": "Request body too large"},
            )

        # Validate content type for POST/PUT requests
        if request.method in ("POST", "PUT", "PATCH"):
            content_type = request.headers.get("content-type", "")
            if not content_type.startswith(("application/json", "multipart/form-data")):
                # Allow requests without body
                if content_length and int(content_length) > 0:
                    return JSONResponse(
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        content={"detail": "Content-Type must be application/json"},
                    )

        return await call_next(request)


def generate_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)
