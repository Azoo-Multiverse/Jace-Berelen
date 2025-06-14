"""
Jace Berelen POC - Public Environment Configuration
Configurações que podem ser commitadas no git (não sensíveis)
"""

# ============================================================================
# APPLICATION SETTINGS (Public)
# ============================================================================

APP_NAME = "Jace Berelen POC"
VERSION = "0.1.0"
DESCRIPTION = "AI-driven workflow automation platform for overemployment support"

# Default environment (pode ser sobrescrito por ENV var)
DEFAULT_ENVIRONMENT = "development"
DEFAULT_DEBUG_MODE = True
DEFAULT_LOG_LEVEL = "INFO"

# ============================================================================
# SERVER SETTINGS (Public)
# ============================================================================

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000

# ============================================================================
# DATABASE SETTINGS (Public)
# ============================================================================

# URLs de desenvolvimento (não sensíveis)
DEFAULT_DATABASE_URL = "sqlite:///./jace_berelen.db"
DEFAULT_TEST_DATABASE_URL = "sqlite:///./test_jace_berelen.db"

# ============================================================================
# AI MODEL CONFIGURATION (Public)
# ============================================================================

# Modelos disponíveis
DEFAULT_AIDER_MODEL = "anthropic/claude-3.5-sonnet"
DEFAULT_AI_MODEL_PRIMARY = "anthropic/claude-3.5-sonnet"
DEFAULT_AI_MODEL_FALLBACK = "anthropic/claude-3-haiku"

# URLs públicas padrão
DEFAULT_OPENROUTER_SITE_URL = "https://jace-berelen.com"
DEFAULT_OPENROUTER_APP_NAME = "Jace Berelen POC"

# OpenRouter API base URL (público)
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# ============================================================================
# COST MANAGEMENT (Public Defaults)
# ============================================================================

DEFAULT_MONTHLY_BUDGET_LIMIT = 100.0
DEFAULT_AI_COST_ALERT_THRESHOLD = 80.0
DEFAULT_CLIENT_BUDGET = 20.0

# ============================================================================
# SECURITY SETTINGS (Public Defaults)
# ============================================================================

DEFAULT_RATE_LIMIT_PER_MINUTE = 60
DEFAULT_SESSION_TIMEOUT_MINUTES = 30

# ============================================================================
# FEATURE FLAGS (Public Defaults)
# ============================================================================

DEFAULT_ENABLE_WEB_SCRAPING = True
DEFAULT_ENABLE_FILE_UPLOADS = False
DEFAULT_ENABLE_SYSTEM_COMMANDS = False

# ============================================================================
# API CONFIGURATION (Public)
# ============================================================================

# CORS settings
CORS_ALLOW_ORIGINS = ["*"]  # Restringir em produção
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

# Health check settings
HEALTH_CHECK_PATH = "/health"
HEALTH_CHECK_TIMEOUT = 300

# ============================================================================
# AI MODEL COSTS (Public Reference)
# ============================================================================

# Custos aproximados por modelo (referência pública)
MODEL_COSTS = {
    "anthropic/claude-3.5-sonnet": {
        "input_cost_per_token": 0.000003,
        "output_cost_per_token": 0.000015,
    },
    "anthropic/claude-3-haiku": {
        "input_cost_per_token": 0.00000025,
        "output_cost_per_token": 0.00000125,
    },
    "openai/gpt-4": {
        "input_cost_per_token": 0.00003,
        "output_cost_per_token": 0.00006,
    },
    "openai/gpt-3.5-turbo": {
        "input_cost_per_token": 0.0000015,
        "output_cost_per_token": 0.000002,
    }
}

# ============================================================================
# DEPLOYMENT CONFIGURATION (Public)
# ============================================================================

# Railway detection
RAILWAY_ENVIRONMENTS = ["production", "staging"]

# Allowed hosts for different environments
ALLOWED_HOSTS = {
    "development": ["localhost", "127.0.0.1", "*.ngrok.io", "*.loca.lt"],
    "production": ["*.railway.app", "*.herokuapp.com"],
    "staging": ["*.railway.app", "*.ngrok.io"]
}

# ============================================================================
# LOGGING CONFIGURATION (Public)
# ============================================================================

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

LOG_LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50
}

# ============================================================================
# TASK MANAGEMENT (Public Defaults)
# ============================================================================

DEFAULT_TASK_PRIORITIES = ["low", "medium", "high", "urgent"]
DEFAULT_TASK_STATUSES = ["pending", "in_progress", "completed", "failed", "cancelled"]
DEFAULT_JOB_TYPES = ["remote", "hybrid", "onsite"]

# ============================================================================
# WORKSPACE CONFIGURATION (Public)
# ============================================================================

DEFAULT_WORKSPACE_DIR = "./workspaces"
DEFAULT_LOGS_DIR = "./logs"
DEFAULT_TEMP_DIR = "./temp"

# ============================================================================
# API ENDPOINTS (Public)
# ============================================================================

API_ENDPOINTS = {
    "health": "/health",
    "docs": "/docs",
    "redoc": "/redoc",
    "openapi": "/openapi.json",
    "ai_chat": "/ai/chat",
    "ai_code_help": "/ai/code-help",
    "ai_task_breakdown": "/ai/task-breakdown",
    "tasks": "/tasks",
    "webhooks_slack": "/webhooks/slack",
    "webhooks_github": "/webhooks/github",
    "metrics_usage": "/metrics/usage",
    "metrics_performance": "/metrics/performance"
}

# ============================================================================
# VALIDATION RULES (Public)
# ============================================================================

# Formatos de token válidos (para validação)
TOKEN_FORMATS = {
    "slack_bot": "xoxb-",
    "slack_app": "xapp-",
    "openrouter": "sk-or-",
    "openai": "sk-",
    "anthropic": "ant-"
}

# Tamanhos mínimos/máximos
VALIDATION_RULES = {
    "secret_key_min_length": 32,
    "password_min_length": 8,
    "username_min_length": 3,
    "username_max_length": 50,
    "task_title_max_length": 500,
    "task_description_max_length": 5000
}

# ============================================================================
# DEVELOPMENT HELPERS (Public)
# ============================================================================

# Para facilitar desenvolvimento
DEVELOPMENT_DEFAULTS = {
    "auto_reload": True,
    "debug_toolbar": True,
    "log_sql": True,
    "mock_ai_responses": False,
    "skip_auth": False
}

# ============================================================================
# EXPORT ALL PUBLIC CONFIGS
# ============================================================================

__all__ = [
    # App
    "APP_NAME", "VERSION", "DESCRIPTION",
    
    # Defaults
    "DEFAULT_ENVIRONMENT", "DEFAULT_DEBUG_MODE", "DEFAULT_LOG_LEVEL",
    "DEFAULT_HOST", "DEFAULT_PORT",
    
    # Database
    "DEFAULT_DATABASE_URL", "DEFAULT_TEST_DATABASE_URL",
    
    # AI
    "DEFAULT_AIDER_MODEL", "DEFAULT_AI_MODEL_PRIMARY", "DEFAULT_AI_MODEL_FALLBACK",
    "DEFAULT_OPENROUTER_SITE_URL", "DEFAULT_OPENROUTER_APP_NAME", "OPENROUTER_BASE_URL",
    
    # Costs
    "DEFAULT_MONTHLY_BUDGET_LIMIT", "DEFAULT_AI_COST_ALERT_THRESHOLD", 
    "DEFAULT_CLIENT_BUDGET", "MODEL_COSTS",
    
    # Security
    "DEFAULT_RATE_LIMIT_PER_MINUTE", "DEFAULT_SESSION_TIMEOUT_MINUTES",
    
    # Features
    "DEFAULT_ENABLE_WEB_SCRAPING", "DEFAULT_ENABLE_FILE_UPLOADS", 
    "DEFAULT_ENABLE_SYSTEM_COMMANDS",
    
    # CORS
    "CORS_ALLOW_ORIGINS", "CORS_ALLOW_CREDENTIALS", "CORS_ALLOW_METHODS", 
    "CORS_ALLOW_HEADERS",
    
    # Health
    "HEALTH_CHECK_PATH", "HEALTH_CHECK_TIMEOUT",
    
    # Deployment
    "RAILWAY_ENVIRONMENTS", "ALLOWED_HOSTS",
    
    # Logging
    "LOG_FORMAT", "LOG_DATE_FORMAT", "LOG_LEVELS",
    
    # Tasks
    "DEFAULT_TASK_PRIORITIES", "DEFAULT_TASK_STATUSES", "DEFAULT_JOB_TYPES",
    
    # Workspace
    "DEFAULT_WORKSPACE_DIR", "DEFAULT_LOGS_DIR", "DEFAULT_TEMP_DIR",
    
    # API
    "API_ENDPOINTS",
    
    # Validation
    "TOKEN_FORMATS", "VALIDATION_RULES",
    
    # Development
    "DEVELOPMENT_DEFAULTS"
] 