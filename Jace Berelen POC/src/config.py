"""
Configuration management for Jace Berelen POC
Uses env.py for public configs and .env for secrets
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings

# Import public configurations (can be committed to git)
from env import *


class Settings(BaseSettings):
    """Application settings - secrets from .env, public configs from env.py"""
    
    # ========================================================================
    # APPLICATION (Public configs with .env overrides)
    # ========================================================================
    
    app_name: str = APP_NAME
    version: str = VERSION
    description: str = DESCRIPTION
    environment: str = Field(default=DEFAULT_ENVIRONMENT, alias="ENVIRONMENT")
    debug: bool = Field(default=DEFAULT_DEBUG_MODE, alias="DEBUG_MODE")
    log_level: str = Field(default=DEFAULT_LOG_LEVEL, alias="LOG_LEVEL")
    
    # ========================================================================
    # SERVER (Public configs with .env overrides)
    # ========================================================================
    
    host: str = Field(default=DEFAULT_HOST, alias="HOST")
    port: int = Field(default=DEFAULT_PORT, alias="PORT")
    
    # ========================================================================
    # SECRETS (Only from .env - REQUIRED)
    # ========================================================================
    
    secret_key: str = Field(alias="SECRET_KEY")
    
    # Slack Credentials
    slack_bot_token: str = Field(alias="SLACK_BOT_TOKEN")
    slack_signing_secret: str = Field(alias="SLACK_SIGNING_SECRET")
    slack_app_token: Optional[str] = Field(default=None, alias="SLACK_APP_TOKEN")
    
    # AI Credentials
    openrouter_api_key: str = Field(alias="OPENROUTER_API_KEY")
    
    # ========================================================================
    # AI MODELS (Public configs with .env overrides)
    # ========================================================================
    
    aider_model: str = Field(default=DEFAULT_AIDER_MODEL, alias="AIDER_MODEL")
    ai_model_primary: str = Field(default=DEFAULT_AI_MODEL_PRIMARY, alias="AI_MODEL_PRIMARY")
    ai_model_fallback: str = Field(default=DEFAULT_AI_MODEL_FALLBACK, alias="AI_MODEL_FALLBACK")
    
    # URLs (can be overridden for development)
    openrouter_site_url: str = Field(default=DEFAULT_OPENROUTER_SITE_URL, alias="OPENROUTER_SITE_URL")
    openrouter_app_name: str = Field(default=DEFAULT_OPENROUTER_APP_NAME, alias="OPENROUTER_APP_NAME")
    
    # ========================================================================
    # DATABASE (Public default, can be overridden for production)
    # ========================================================================
    
    database_url: str = Field(default=DEFAULT_DATABASE_URL, alias="DATABASE_URL")
    test_database_url: str = Field(default=DEFAULT_TEST_DATABASE_URL, alias="TEST_DATABASE_URL")
    
    # Railway environment detection
    railway_environment: Optional[str] = Field(default=None, alias="RAILWAY_ENVIRONMENT")
    public_url: Optional[str] = Field(default=None, alias="PUBLIC_URL")
    
    # ========================================================================
    # COST MANAGEMENT (Public defaults, can be overridden)
    # ========================================================================
    
    monthly_budget_limit: float = Field(default=DEFAULT_MONTHLY_BUDGET_LIMIT, alias="MONTHLY_BUDGET_LIMIT")
    ai_cost_alert_threshold: float = Field(default=DEFAULT_AI_COST_ALERT_THRESHOLD, alias="AI_COST_ALERT_THRESHOLD")
    default_client_budget: float = Field(default=DEFAULT_CLIENT_BUDGET, alias="DEFAULT_CLIENT_BUDGET")
    
    # ========================================================================
    # SECURITY (Public defaults, can be overridden)
    # ========================================================================
    
    rate_limit_per_minute: int = Field(default=DEFAULT_RATE_LIMIT_PER_MINUTE, alias="RATE_LIMIT_PER_MINUTE")
    session_timeout_minutes: int = Field(default=DEFAULT_SESSION_TIMEOUT_MINUTES, alias="SESSION_TIMEOUT_MINUTES")
    
    # ========================================================================
    # FEATURE FLAGS (Public defaults, can be overridden)
    # ========================================================================
    
    enable_web_scraping: bool = Field(default=DEFAULT_ENABLE_WEB_SCRAPING, alias="ENABLE_WEB_SCRAPING")
    enable_file_uploads: bool = Field(default=DEFAULT_ENABLE_FILE_UPLOADS, alias="ENABLE_FILE_UPLOADS")
    enable_system_commands: bool = Field(default=DEFAULT_ENABLE_SYSTEM_COMMANDS, alias="ENABLE_SYSTEM_COMMANDS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def is_railway() -> bool:
    """Check if running on Railway"""
    return settings.railway_environment is not None or os.getenv("RAILWAY_ENVIRONMENT") is not None


def is_development() -> bool:
    """Check if running in development environment"""
    return settings.environment.lower() == "development" and not is_railway()


def is_production() -> bool:
    """Check if running in production environment"""
    return settings.environment.lower() == "production" or is_railway()


def get_port() -> int:
    """Get port for Railway deployment"""
    # Railway sets PORT environment variable
    return int(os.getenv("PORT", settings.port))


def get_database_url() -> str:
    """Get the appropriate database URL based on environment"""
    if settings.environment == "test":
        return settings.test_database_url
    
    # Railway automatically provides DATABASE_URL for PostgreSQL
    if is_railway() and settings.database_url.startswith("postgresql"):
        return settings.database_url
    
    return settings.database_url


def validate_environment() -> tuple[bool, list[str]]:
    """Validate that all required environment variables are present"""
    missing = []
    
    # Check critical secrets
    if not settings.slack_bot_token:
        missing.append("SLACK_BOT_TOKEN")
    
    if not settings.slack_signing_secret:
        missing.append("SLACK_SIGNING_SECRET")
    
    if not settings.openrouter_api_key:
        missing.append("OPENROUTER_API_KEY")
    
    if not settings.secret_key:
        missing.append("SECRET_KEY")
    
    # Validate token formats (from env.py)
    if settings.slack_bot_token and not settings.slack_bot_token.startswith(TOKEN_FORMATS["slack_bot"]):
        missing.append("SLACK_BOT_TOKEN (invalid format - should start with 'xoxb-')")
    
    if settings.openrouter_api_key and not settings.openrouter_api_key.startswith(TOKEN_FORMATS["openrouter"]):
        missing.append("OPENROUTER_API_KEY (invalid format - should start with 'sk-or-')")
    
    # Validate secret key length (from env.py)
    if settings.secret_key and len(settings.secret_key) < VALIDATION_RULES["secret_key_min_length"]:
        missing.append(f"SECRET_KEY (too short - minimum {VALIDATION_RULES['secret_key_min_length']} characters)")
    
    return len(missing) == 0, missing


def get_slack_config() -> dict:
    """Get Slack configuration dictionary"""
    config = {
        "bot_token": settings.slack_bot_token,
        "signing_secret": settings.slack_signing_secret,
    }
    
    if settings.slack_app_token:
        config["app_token"] = settings.slack_app_token
    
    return config


def get_openrouter_config() -> dict:
    """Get OpenRouter configuration dictionary for Claude access"""
    return {
        "api_key": settings.openrouter_api_key,
        "base_url": OPENROUTER_BASE_URL,  # From env.py
        "model": settings.ai_model_primary,
        "fallback_model": settings.ai_model_fallback,
        "max_tokens": 4000,
        "temperature": 0.1,
        "headers": {
            "HTTP-Referer": settings.openrouter_site_url,
            "X-Title": settings.openrouter_app_name,
        }
    }


def get_cors_config() -> dict:
    """Get CORS configuration from env.py"""
    # Restrict CORS in production
    if is_production():
        allowed_origins = []
        for host_pattern in ALLOWED_HOSTS.get("production", []):
            allowed_origins.append(f"https://{host_pattern}")
    else:
        allowed_origins = CORS_ALLOW_ORIGINS
    
    return {
        "allow_origins": allowed_origins,
        "allow_credentials": CORS_ALLOW_CREDENTIALS,
        "allow_methods": CORS_ALLOW_METHODS,
        "allow_headers": CORS_ALLOW_HEADERS,
    }


def get_model_cost(model_name: str) -> dict:
    """Get cost information for AI model from env.py"""
    return MODEL_COSTS.get(model_name, {
        "input_cost_per_token": 0.000001,  # Default fallback
        "output_cost_per_token": 0.000002,
    })


def get_api_endpoints() -> dict:
    """Get API endpoints from env.py"""
    return API_ENDPOINTS


# Export commonly used settings and functions
__all__ = [
    "Settings",
    "settings",
    "is_railway",
    "is_development", 
    "is_production",
    "get_port",
    "get_database_url",
    "validate_environment",
    "get_slack_config",
    "get_openrouter_config",
    "get_cors_config",
    "get_model_cost",
    "get_api_endpoints",
] 