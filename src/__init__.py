"""
Jace Berelen POC - AI-driven workflow automation platform
for overemployment support

This package provides:
- AI-powered task management and automation
- Slack integration for seamless workflow management
- Multi-job coordination and prioritization
- Cost tracking and budget management
- Automated task breakdown and execution
"""

__version__ = "0.1.0"
__author__ = "Jace Berelen Team"
__description__ = "AI-driven workflow automation platform for overemployment support"

# Import core components
from .config import settings, validate_environment
from .database import init_database, db_manager
from .ai_client import ai_client, ask_ai, generate_code, break_down_task
from .slack_handler import slack_handler, send_notification
from .command_executor import command_executor, run_command, run_aws_command
from .utils import setup_logging, display_startup_banner

# Initialize logging on import
setup_logging()

__all__ = [
    # Core components
    "settings",
    "validate_environment", 
    "init_database",
    "db_manager",
    "ai_client",
    "slack_handler",
    "command_executor",
    
    # Convenience functions
    "ask_ai",
    "generate_code", 
    "break_down_task",
    "send_notification",
    "run_command",
    "run_aws_command",
    "setup_logging",
    "display_startup_banner",
    
    # Package info
    "__version__",
    "__author__",
    "__description__"
] 