"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.middleware.security import (
    APIKeyMiddleware,
    RateLimitMiddleware,
    RequestValidationMiddleware,
    SecurityHeadersMiddleware,
)

# Path to frontend directory
FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend"
from app.api.v1 import router as v1_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment.value}")
    logger.info(f"Storage backend: {settings.storage_backend.value}")
    logger.info(f"Data directory: {settings.data_dir}")
    logger.info(f"Rate limiting: {'enabled' if settings.rate_limit_enabled else 'disabled'}")
    logger.info(f"API key auth: {'enabled' if settings.api_key_auth_enabled else 'disabled'}")
    yield
    logger.info("Shutting down...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    # Disable docs in production for security
    docs_url = "/docs" if settings.is_development else None
    redoc_url = "/redoc" if settings.is_development else None

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="F1 Data Visualization API - Powered by FastF1",
        docs_url=docs_url,
        redoc_url=redoc_url,
        lifespan=lifespan,
    )

    # Global exception handler - hide internal errors in production
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle uncaught exceptions without exposing internal details."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)

        if settings.is_development:
            # In development, show the error
            return JSONResponse(
                status_code=500,
                content={"detail": str(exc)},
            )
        else:
            # In production, hide internal details
            return JSONResponse(
                status_code=500,
                content={"detail": "An internal error occurred. Please try again later."},
            )

    # ==========================================
    # Security Middleware (order matters!)
    # ==========================================

    # 1. Security headers (outermost - runs last on response)
    app.add_middleware(SecurityHeadersMiddleware)

    # 2. Request validation
    app.add_middleware(RequestValidationMiddleware)

    # 3. Rate limiting
    if settings.rate_limit_enabled:
        app.add_middleware(RateLimitMiddleware)

    # 4. API key authentication for protected endpoints
    if settings.api_key_auth_enabled and settings.api_keys:
        app.add_middleware(APIKeyMiddleware, api_keys=settings.api_keys)

    # 5. Trusted hosts (only in production)
    if settings.is_production:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.trusted_hosts,
        )

    # 6. CORS middleware (innermost - runs first)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # API routes
    app.include_router(v1_router, prefix=settings.api_v1_prefix)

    # Mount static files for frontend (if directory exists)
    if FRONTEND_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")

    # Health check
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "app": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment.value,
        }

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        response = {
            "app": settings.app_name,
            "version": settings.app_version,
            "api": settings.api_v1_prefix,
        }
        # Only show docs URL in development
        if settings.is_development:
            response["docs"] = "/docs"
        return response

    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
