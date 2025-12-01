"""Application configuration using Pydantic Settings."""

from enum import Enum
from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class StorageBackend(str, Enum):
    """Supported storage backends."""
    FILE = "file"
    DYNAMODB = "dynamodb"


class Environment(str, Enum):
    """Application environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be overridden via environment variables
    prefixed with F1_ (e.g., F1_DEBUG=true).
    """

    model_config = SettingsConfigDict(
        env_prefix="F1_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # API Settings
    app_name: str = "F1-Dash API"
    app_version: str = "0.1.0"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    environment: Environment = Environment.DEVELOPMENT

    # Storage Settings
    storage_backend: StorageBackend = StorageBackend.FILE
    data_dir: Path = Path("./data")

    # FastF1 Settings
    fastf1_cache_dir: Path = Path("./data/cache")

    # DynamoDB Settings (for future use)
    dynamodb_endpoint: str | None = None
    dynamodb_region: str = "us-east-1"
    dynamodb_table_prefix: str = "f1plots_"

    # CORS Settings - SECURE DEFAULTS
    # In production, set F1_CORS_ORIGINS to your actual domain(s)
    # Use str type to avoid pydantic-settings parsing issues, parsed in validator
    cors_origins: str | list[str] = "http://localhost:3000,http://localhost:8000,http://localhost:8080,http://127.0.0.1:3000,http://127.0.0.1:8000,http://127.0.0.1:8080"
    # Don't allow credentials with wildcards - security risk
    cors_allow_credentials: bool = False
    # Only allow specific methods, not wildcards
    cors_allow_methods: list[str] = ["GET", "POST", "OPTIONS"]
    # Only allow specific headers
    cors_allow_headers: list[str] = [
        "Content-Type",
        "Authorization",
        "X-API-Key",
        "X-Request-ID",
    ]

    # Security Settings
    # API keys for protected endpoints (comma-separated in env var)
    api_keys: str = ""
    # Trusted hosts (for production, set to your domain)
    # Include wildcard for render.com health checks
    trusted_hosts: str = "localhost,127.0.0.1,*.onrender.com"
    # Enable rate limiting
    rate_limit_enabled: bool = True
    # Enable API key authentication for protected endpoints
    api_key_auth_enabled: bool = False  # Set to True in production

    # Logging
    log_level: str = "INFO"

    @field_validator("api_keys", mode="after")
    @classmethod
    def parse_api_keys(cls, v):
        """Parse comma-separated API keys from environment variable."""
        if isinstance(v, str):
            if not v.strip():
                return []
            return [k.strip() for k in v.split(",") if k.strip()]
        if isinstance(v, list):
            return v
        return []

    @field_validator("cors_origins", mode="after")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if v is None:
            return []
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            # Handle JSON-like string
            if v.startswith("["):
                import json
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Handle comma-separated string
            return [o.strip() for o in v.split(",") if o.strip()]
        return []

    @field_validator("trusted_hosts", mode="after")
    @classmethod
    def parse_trusted_hosts(cls, v):
        """Parse trusted hosts from string or list."""
        if isinstance(v, str):
            if not v.strip():
                return []
            return [h.strip() for h in v.split(",") if h.strip()]
        if isinstance(v, list):
            return v
        return []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.fastf1_cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == Environment.DEVELOPMENT


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.

    Returns:
        Settings instance (cached)
    """
    return Settings()
