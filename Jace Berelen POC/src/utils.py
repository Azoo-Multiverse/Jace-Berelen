"""
Utility functions for the Jace Berelen POC
Logging, formatting, parsing, and system helpers
"""

import logging
import os
import platform
import psutil
import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table
from rich.panel import Panel

from .config import settings

console = Console()


def setup_logging():
    """Setup logging configuration with Rich formatting"""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                console=console,
                show_time=True,
                show_level=True,
                show_path=False,
                rich_tracebacks=True
            ),
            logging.FileHandler(
                log_dir / f"jace_{datetime.now().strftime('%Y%m%d')}.log",
                mode='a',
                encoding='utf-8'
            )
        ]
    )
    
    # Set specific logger levels
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("slack_sdk").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized")


def get_system_info() -> Dict[str, Any]:
    """Get comprehensive system information"""
    
    try:
        # Basic system info
        system_info = {
            "timestamp": datetime.utcnow().isoformat(),
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version()
            },
            "hardware": {
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "memory_used_gb": round(psutil.virtual_memory().used / (1024**3), 2),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_total_gb": round(psutil.disk_usage('/').total / (1024**3), 2),
                "disk_used_gb": round(psutil.disk_usage('/').used / (1024**3), 2),
                "disk_percent": psutil.disk_usage('/').percent
            },
            "environment": {
                "environment": settings.environment,
                "debug_mode": settings.debug_mode if hasattr(settings, 'debug_mode') else False,
                "log_level": settings.log_level,
                "database_url": settings.database_url.split('@')[0] + '@***' if '@' in settings.database_url else "sqlite://***",
                "ai_model": settings.ai_model_primary,
                "slack_connected": bool(settings.slack_bot_token)
            }
        }
        
        return system_info
        
    except Exception as e:
        logging.error(f"Error getting system info: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


def format_task_list(tasks: List[Any], show_details: bool = False) -> str:
    """Format task list for display"""
    
    if not tasks:
        return "No tasks found."
    
    table = Table(title="Task List")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="white", max_width=40)
    table.add_column("Status", style="green")
    table.add_column("Priority", style="yellow")
    
    if show_details:
        table.add_column("Created", style="dim")
        table.add_column("Due Date", style="red")
    
    for task in tasks:
        priority_color = {
            "low": "blue",
            "medium": "yellow", 
            "high": "orange1",
            "urgent": "red"
        }.get(task.priority, "white")
        
        status_color = {
            "pending": "yellow",
            "in_progress": "blue",
            "completed": "green",
            "failed": "red",
            "cancelled": "dim"
        }.get(task.status, "white")
        
        row = [
            str(task.id),
            task.title[:40] + "..." if len(task.title) > 40 else task.title,
            f"[{status_color}]{task.status}[/{status_color}]",
            f"[{priority_color}]{task.priority}[/{priority_color}]"
        ]
        
        if show_details:
            row.extend([
                task.created_at.strftime("%m/%d %H:%M"),
                task.due_date.strftime("%m/%d") if task.due_date else "None"
            ])
        
        table.add_row(*row)
    
    # Render table to string
    with console.capture() as capture:
        console.print(table)
    
    return capture.get()


def parse_time_estimate(text: str) -> Optional[float]:
    """Parse time estimate from text"""
    
    # Common patterns
    patterns = [
        r'(\d+(?:\.\d+)?)\s*h(?:ours?)?',
        r'(\d+(?:\.\d+)?)\s*hrs?',
        r'(\d+)\s*m(?:ins?|inutes?)',
        r'(\d+)\s*d(?:ays?)?',
        r'(\d+)\s*w(?:eeks?)?'
    ]
    
    text = text.lower()
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            value = float(match.group(1))
            
            if 'h' in pattern:
                return value
            elif 'm' in pattern:
                return value / 60  # Convert minutes to hours
            elif 'd' in pattern:
                return value * 8  # Convert days to hours (8 hours/day)
            elif 'w' in pattern:
                return value * 40  # Convert weeks to hours (40 hours/week)
    
    return None


def extract_priority(text: str) -> str:
    """Extract priority from text"""
    
    text = text.lower()
    
    if any(word in text for word in ['urgent', 'critical', 'asap', 'emergency']):
        return 'urgent'
    elif any(word in text for word in ['high', 'important', 'priority']):
        return 'high'
    elif any(word in text for word in ['low', 'minor', 'later']):
        return 'low'
    else:
        return 'medium'


def format_currency(amount: float) -> str:
    """Format currency amount"""
    return f"${amount:.2f}"


def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable"""
    
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to maximum length"""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."


def clean_slack_text(text: str) -> str:
    """Clean Slack-formatted text"""
    
    # Remove user mentions
    text = re.sub(r'<@[A-Z0-9]+>', '', text)
    
    # Remove channel mentions
    text = re.sub(r'<#[A-Z0-9]+\|[^>]+>', '', text)
    
    # Remove links
    text = re.sub(r'<http[^>]+>', '', text)
    
    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def parse_slack_command(text: str) -> Dict[str, Any]:
    """Parse Slack command text into structured data"""
    
    # Split into words
    words = text.strip().split()
    
    if not words:
        return {"command": None, "args": [], "options": {}}
    
    command = words[0].lower()
    args = words[1:]
    options = {}
    
    # Parse options (--key value or --flag)
    i = 0
    while i < len(args):
        if args[i].startswith('--'):
            key = args[i][2:]
            
            # Check if next arg is a value
            if i + 1 < len(args) and not args[i + 1].startswith('--'):
                options[key] = args[i + 1]
                i += 2
            else:
                options[key] = True
                i += 1
        else:
            i += 1
    
    # Remove options from args
    args = [arg for arg in args if not arg.startswith('--')]
    
    return {
        "command": command,
        "args": args,
        "options": options,
        "raw_text": text
    }


def validate_email(email: str) -> bool:
    """Validate email address format"""
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system usage"""
    
    # Remove/replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    
    return filename


def create_progress_bar(current: int, total: int, width: int = 20) -> str:
    """Create a text progress bar"""
    
    if total == 0:
        return "█" * width
    
    progress = current / total
    filled = int(width * progress)
    bar = "█" * filled + "░" * (width - filled)
    
    return f"{bar} {current}/{total} ({progress:.1%})"


def parse_json_safely(text: str) -> Optional[Dict[str, Any]]:
    """Safely parse JSON from text"""
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```json\s*\n(.*?)\n```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to extract JSON from regular code blocks
        code_match = re.search(r'```\s*\n(.*?)\n```', text, re.DOTALL)
        if code_match:
            try:
                return json.loads(code_match.group(1))
            except json.JSONDecodeError:
                pass
        
        return None


def get_file_size_mb(file_path: Union[str, Path]) -> float:
    """Get file size in MB"""
    
    try:
        return os.path.getsize(file_path) / (1024 * 1024)
    except OSError:
        return 0.0


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure directory exists, create if necessary"""
    
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_relative_time(timestamp: datetime) -> str:
    """Get relative time string (e.g., '2 hours ago')"""
    
    now = datetime.utcnow()
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "just now"


def highlight_code(code: str, language: str = "python") -> str:
    """Highlight code syntax (basic implementation)"""
    
    # For now, just wrap in code blocks
    # In a full implementation, you'd use pygments or similar
    return f"```{language}\n{code}\n```"


def extract_urls(text: str) -> List[str]:
    """Extract URLs from text"""
    
    url_pattern = r'https?://[^\s<>"\']+[^\s<>"\'.,;:!?]'
    return re.findall(url_pattern, text)


def mask_sensitive_data(text: str) -> str:
    """Mask sensitive data in text"""
    
    # Mask API keys
    text = re.sub(r'(sk-[a-zA-Z0-9]{32,})', r'\1[:8]***', text)
    
    # Mask email addresses
    text = re.sub(r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', r'\1***@\2', text)
    
    # Mask tokens
    text = re.sub(r'(xoxb-[a-zA-Z0-9-]+)', r'\1[:10]***', text)
    
    return text


def display_startup_banner():
    """Display startup banner"""
    
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║                      JACE BERELEN POC                         ║
    ║                                                               ║
    ║        AI-Driven Workflow Automation Platform                 ║
    ║              for Overemployment Support                       ║
    ║                                                               ║
    ║                        Version 0.1.0                         ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    
    console.print(Panel(banner, style="bold blue"))
    console.print(f"Starting in [bold]{settings.environment}[/bold] mode")
    console.print(f"Log level: [bold]{settings.log_level}[/bold]")
    console.print(f"Database: [bold]{settings.database_url.split('://')[0]}[/bold]")
    console.print(f"AI Model: [bold]{settings.ai_model_primary}[/bold]")
    console.print("")


__all__ = [
    "setup_logging",
    "get_system_info",
    "format_task_list",
    "parse_time_estimate",
    "extract_priority",
    "format_currency",
    "format_duration",
    "truncate_text",
    "clean_slack_text",
    "parse_slack_command",
    "validate_email",
    "sanitize_filename",
    "create_progress_bar",
    "parse_json_safely",
    "get_file_size_mb",
    "ensure_directory",
    "get_relative_time",
    "highlight_code",
    "extract_urls",
    "mask_sensitive_data",
    "display_startup_banner"
] 