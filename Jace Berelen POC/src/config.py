"""
Configuration management for Jace Berelen POC
Handles environment variables and application settings
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    app_name: str = "Jace Berelen POC"
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=True, alias="DEBUG_MODE")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    secret_key: str = Field(alias="SECRET_KEY")
    
    # Slack Configuration
    slack_bot_token: str = Field(alias="SLACK_BOT_TOKEN")
    slack_signing_secret: str = Field(alias="SLACK_SIGNING_SECRET")
    slack_app_token: Optional[str] = Field(default=None, alias="SLACK_APP_TOKEN")
    
    # OpenRouter Configuration (for Claude and other models)
    openrouter_api_key: str = Field(alias="OPENROUTER_API_KEY")
    aider_model: str = Field(default="anthropic/claude-3.5-sonnet", alias="AIDER_MODEL")
    ai_model_primary: str = Field(default="anthropic/claude-3.5-sonnet", alias="AI_MODEL_PRIMARY")
    ai_model_fallback: str = Field(default="anthropic/claude-3-haiku", alias="AI_MODEL_FALLBACK")
    openrouter_site_url: str = Field(default="https://jace-berelen.com", alias="OPENROUTER_SITE_URL")
    openrouter_app_name: str = Field(default="Jace Berelen POC", alias="OPENROUTER_APP_NAME")
    
    # Database
    database_url: str = Field(default="sqlite:///./jace_berelen.db", alias="DATABASE_URL")
    
    # Cost Management
    monthly_budget_limit: float = Field(default=100.0, alias="MONTHLY_BUDGET_LIMIT")
    ai_cost_alert_threshold: float = Field(default=80.0, alias="AI_COST_ALERT_THRESHOLD")
    default_client_budget: float = Field(default=20.0, alias="DEFAULT_CLIENT_BUDGET")
    
    # Security
    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")
    session_timeout_minutes: int = Field(default=30, alias="SESSION_TIMEOUT_MINUTES")
    
    # Feature Flags
    enable_web_scraping: bool = Field(default=True, alias="ENABLE_WEB_SCRAPING")
    enable_file_uploads: bool = Field(default=False, alias="ENABLE_FILE_UPLOADS")
    enable_system_commands: bool = Field(default=False, alias="ENABLE_SYSTEM_COMMANDS")
    
    # Testing
    test_database_url: str = Field(default="sqlite:///./test_jace_berelen.db", alias="TEST_DATABASE_URL")
    test_slack_channel: Optional[str] = Field(default=None, alias="TEST_SLACK_CHANNEL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings


def validate_environment() -> tuple[bool, list[str]]:
    """Validate that all required environment variables are present"""
    missing = []
    
    # Check critical settings
    if not settings.slack_bot_token:
        missing.append("SLACK_BOT_TOKEN")
    
    if not settings.slack_signing_secret:
        missing.append("SLACK_SIGNING_SECRET")
    
    if not settings.openrouter_api_key:
        missing.append("OPENROUTER_API_KEY")
    
    if not settings.secret_key:
        missing.append("SECRET_KEY")
    
    # Validate token formats
    if settings.slack_bot_token and not settings.slack_bot_token.startswith("xoxb-"):
        missing.append("SLACK_BOT_TOKEN (invalid format - should start with 'xoxb-')")
    
    if settings.openrouter_api_key and not settings.openrouter_api_key.startswith("sk-or-"):
        missing.append("OPENROUTER_API_KEY (invalid format - should start with 'sk-or-')")
    
    return len(missing) == 0, missing


def get_database_url() -> str:
    """Get the appropriate database URL based on environment"""
    if settings.environment == "test":
        return settings.test_database_url
    return settings.database_url


def is_production() -> bool:
    """Check if running in production environment"""
    return settings.environment.lower() == "production"


def is_development() -> bool:
    """Check if running in development environment"""
    return settings.environment.lower() == "development"


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
        "base_url": "https://openrouter.ai/api/v1",
        "model": settings.ai_model_primary,
        "fallback_model": settings.ai_model_fallback,
        "max_tokens": 4000,
        "temperature": 0.1,
        "headers": {
            "HTTP-Referer": settings.openrouter_site_url,
            "X-Title": settings.openrouter_app_name,
        }
    }


# Export commonly used settings
__all__ = [
    "Settings",
    "settings",
    "get_settings",
    "validate_environment",
    "get_database_url",
    "is_production",
    "is_development",
    "get_slack_config",
    "get_openrouter_config",
] 