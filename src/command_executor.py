"""
Secure Command Executor for Jace Berelen POC
Allows running AWS CLI and other commands within task folder scope only
"""

import asyncio
import logging
import os
import subprocess
import shlex
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from datetime import datetime
import tempfile
import shutil

from .config import settings
from .database import log_ai_interaction

logger = logging.getLogger(__name__)


@dataclass
class CommandResult:
    """Result from command execution"""
    success: bool
    stdout: str
    stderr: str
    return_code: int
    execution_time_ms: int
    command: str
    working_directory: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class SecureCommandExecutor:
    """
    Secure command executor with strict workspace isolation
    Only allows commands within designated task folders
    """
    
    # Allowed commands - whitelist approach for security
    ALLOWED_COMMANDS = {
        # AWS CLI
        "aws": ["s3", "ec2", "lambda", "iam", "cloudformation", "logs", "sts"],
        
        # Git operations
        "git": ["status", "add", "commit", "push", "pull", "clone", "branch", "checkout", "log", "diff"],
        
        # File operations
        "ls": [],
        "dir": [],  # Windows
        "cat": [],
        "type": [],  # Windows
        "head": [],
        "tail": [],
        "find": [],
        "grep": [],
        
        # Node.js/npm
        "npm": ["install", "run", "test", "build", "start"],
        "node": [],
        "npx": [],
        
        # Python
        "python": [],
        "python3": [],
        "pip": ["install", "list", "show"],
        "pip3": ["install", "list", "show"],
        
        # Docker (limited)
        "docker": ["ps", "images", "logs", "exec", "build", "run"],
        
        # Kubectl (limited)
        "kubectl": ["get", "describe", "logs", "apply", "delete"],
        
        # Terraform
        "terraform": ["init", "plan", "apply", "destroy", "validate", "fmt"],
        
        # General utilities
        "curl": [],
        "wget": [],
        "jq": [],
        "yq": [],
        "which": [],
        "where": [],  # Windows
        "echo": [],
        "pwd": [],
        "cd": [],
    }
    
    # Dangerous patterns to always block
    BLOCKED_PATTERNS = [
        "rm -rf /",
        "rm -rf *",
        "format",
        "del /f /s /q",
        "rmdir /s",
        "sudo rm",
        "sudo dd",
        ":/dev/",
        "shutdown",
        "reboot",
        "halt",
        "poweroff",
        "init 0",
        "init 6",
        "mkfs",
        "fdisk",
        "crontab -r",
        "chmod 777",
        "chown root",
        "su -",
        "sudo su",
        "> /dev/null",
        "2>/dev/null",
        "&& rm",
        "; rm",
        "| rm",
    ]
    
    def __init__(self, base_workspace_path: Union[str, Path] = None):
        """
        Initialize command executor
        
        Args:
            base_workspace_path: Base path for all task workspaces
        """
        self.base_workspace_path = Path(base_workspace_path or Path.cwd() / "workspaces")
        self.base_workspace_path.mkdir(exist_ok=True)
        
        # Current active workspace (set per task)
        self.current_workspace: Optional[Path] = None
        
        # Command history for audit
        self.command_history: List[CommandResult] = []
        
        logger.info(f"Command executor initialized with base workspace: {self.base_workspace_path}")
    
    def set_workspace(self, task_id: str, user_id: str = "default") -> Path:
        """
        Set the current workspace for a specific task
        
        Args:
            task_id: Unique task identifier
            user_id: User identifier for isolation
            
        Returns:
            Path to the workspace directory
        """
        # Create isolated workspace path
        workspace_name = f"user_{user_id}_task_{task_id}"
        workspace_path = self.base_workspace_path / workspace_name
        workspace_path.mkdir(parents=True, exist_ok=True)
        
        self.current_workspace = workspace_path
        
        logger.info(f"Workspace set to: {workspace_path}")
        return workspace_path
    
    def _validate_command(self, command: str) -> Tuple[bool, str]:
        """
        Validate if command is allowed and safe
        
        Args:
            command: Command string to validate
            
        Returns:
            (is_valid, reason)
        """
        # Check for blocked patterns
        command_lower = command.lower()
        for pattern in self.BLOCKED_PATTERNS:
            if pattern in command_lower:
                return False, f"Blocked dangerous pattern: {pattern}"
        
        # Parse command
        try:
            parts = shlex.split(command)
        except ValueError as e:
            return False, f"Invalid command syntax: {e}"
        
        if not parts:
            return False, "Empty command"
        
        base_command = parts[0]
        
        # Check if base command is allowed
        if base_command not in self.ALLOWED_COMMANDS:
            return False, f"Command '{base_command}' not in whitelist"
        
        # Check subcommands for specific commands
        allowed_subcommands = self.ALLOWED_COMMANDS[base_command]
        if allowed_subcommands and len(parts) > 1:
            subcommand = parts[1]
            if subcommand not in allowed_subcommands:
                return False, f"Subcommand '{subcommand}' not allowed for '{base_command}'"
        
        # Additional security checks
        if ".." in command:
            return False, "Path traversal attempt detected"
        
        if "|" in command and any(danger in command for danger in ["rm", "del", "format"]):
            return False, "Potentially dangerous pipe command"
        
        return True, "Command validated"
    
    def _validate_workspace(self) -> Tuple[bool, str]:
        """
        Validate current workspace is set and secure
        
        Returns:
            (is_valid, reason)
        """
        if not self.current_workspace:
            return False, "No workspace set - call set_workspace() first"
        
        if not self.current_workspace.exists():
            return False, f"Workspace does not exist: {self.current_workspace}"
        
        # Ensure workspace is within base path (prevent escape)
        try:
            self.current_workspace.resolve().relative_to(self.base_workspace_path.resolve())
        except ValueError:
            return False, "Workspace outside allowed base path"
        
        return True, "Workspace validated"
    
    async def execute_command(
        self,
        command: str,
        timeout: int = 30,
        user_id: int = None,
        task_id: int = None
    ) -> CommandResult:
        """
        Execute a command securely within the current workspace
        
        Args:
            command: Command to execute
            timeout: Timeout in seconds
            user_id: User ID for logging
            task_id: Task ID for logging
            
        Returns:
            CommandResult with execution details
        """
        start_time = datetime.utcnow()
        
        # Validate command
        is_valid_cmd, cmd_reason = self._validate_command(command)
        if not is_valid_cmd:
            logger.error(f"Command validation failed: {cmd_reason}")
            return CommandResult(
                success=False,
                stdout="",
                stderr=f"Command validation failed: {cmd_reason}",
                return_code=-1,
                execution_time_ms=0,
                command=command,
                working_directory=str(self.current_workspace) if self.current_workspace else "None"
            )
        
        # Validate workspace
        is_valid_ws, ws_reason = self._validate_workspace()
        if not is_valid_ws:
            logger.error(f"Workspace validation failed: {ws_reason}")
            return CommandResult(
                success=False,
                stdout="",
                stderr=f"Workspace validation failed: {ws_reason}",
                return_code=-1,
                execution_time_ms=0,
                command=command,
                working_directory=str(self.current_workspace) if self.current_workspace else "None"
            )
        
        # Prepare environment
        env = os.environ.copy()
        env["PWD"] = str(self.current_workspace)
        
        try:
            logger.info(f"Executing command in {self.current_workspace}: {command}")
            
            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.current_workspace,
                env=env
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                
                end_time = datetime.utcnow()
                execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
                
                result = CommandResult(
                    success=False,
                    stdout="",
                    stderr=f"Command timed out after {timeout} seconds",
                    return_code=-1,
                    execution_time_ms=execution_time_ms,
                    command=command,
                    working_directory=str(self.current_workspace)
                )
                
                self.command_history.append(result)
                return result
            
            end_time = datetime.utcnow()
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Decode output
            stdout_str = stdout.decode('utf-8', errors='replace') if stdout else ""
            stderr_str = stderr.decode('utf-8', errors='replace') if stderr else ""
            
            result = CommandResult(
                success=process.returncode == 0,
                stdout=stdout_str,
                stderr=stderr_str,
                return_code=process.returncode,
                execution_time_ms=execution_time_ms,
                command=command,
                working_directory=str(self.current_workspace)
            )
            
            # Log result
            self.command_history.append(result)
            
            if result.success:
                logger.info(f"Command executed successfully: {command}")
            else:
                logger.warning(f"Command failed with code {result.return_code}: {command}")
            
            # Log to database if user_id provided
            if user_id:
                await log_ai_interaction(
                    user_id=user_id,
                    task_id=task_id,
                    interaction_type="command_execution",
                    prompt=command,
                    response=f"Exit code: {result.return_code}\nSTDOUT: {stdout_str[:500]}\nSTDERR: {stderr_str[:500]}",
                    model_used="command_executor",
                    tokens_used=0,
                    cost_usd=0.0,
                    response_time_ms=execution_time_ms
                )
            
            return result
            
        except Exception as e:
            end_time = datetime.utcnow()
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            logger.error(f"Command execution error: {e}")
            
            result = CommandResult(
                success=False,
                stdout="",
                stderr=f"Execution error: {str(e)}",
                return_code=-1,
                execution_time_ms=execution_time_ms,
                command=command,
                working_directory=str(self.current_workspace)
            )
            
            self.command_history.append(result)
            return result
    
    async def execute_aws_command(
        self,
        aws_command: str,
        profile: str = None,
        region: str = None,
        **kwargs
    ) -> CommandResult:
        """
        Execute AWS CLI command with optional profile and region
        
        Args:
            aws_command: AWS command (without 'aws' prefix)
            profile: AWS profile to use
            region: AWS region to use
            **kwargs: Additional arguments for execute_command
            
        Returns:
            CommandResult
        """
        # Build full AWS command
        command_parts = ["aws"]
        
        if profile:
            command_parts.extend(["--profile", profile])
        
        if region:
            command_parts.extend(["--region", region])
        
        command_parts.append(aws_command)
        full_command = " ".join(command_parts)
        
        return await self.execute_command(full_command, **kwargs)
    
    def get_workspace_files(self, pattern: str = "*") -> List[Path]:
        """
        Get list of files in current workspace
        
        Args:
            pattern: Glob pattern to match files
            
        Returns:
            List of file paths
        """
        if not self.current_workspace or not self.current_workspace.exists():
            return []
        
        try:
            return list(self.current_workspace.glob(pattern))
        except Exception as e:
            logger.error(f"Error listing workspace files: {e}")
            return []
    
    def cleanup_workspace(self, task_id: str, user_id: str = "default") -> bool:
        """
        Clean up workspace for a specific task
        
        Args:
            task_id: Task identifier
            user_id: User identifier
            
        Returns:
            True if cleanup successful
        """
        workspace_name = f"user_{user_id}_task_{task_id}"
        workspace_path = self.base_workspace_path / workspace_name
        
        try:
            if workspace_path.exists():
                shutil.rmtree(workspace_path)
                logger.info(f"Cleaned up workspace: {workspace_path}")
            return True
        except Exception as e:
            logger.error(f"Error cleaning up workspace {workspace_path}: {e}")
            return False
    
    def get_command_history(self, limit: int = 50) -> List[CommandResult]:
        """Get recent command history"""
        return self.command_history[-limit:]
    
    def get_allowed_commands(self) -> Dict[str, List[str]]:
        """Get list of allowed commands"""
        return self.ALLOWED_COMMANDS.copy()


# Global command executor instance
command_executor = SecureCommandExecutor()


# Convenience functions
async def run_command(
    command: str,
    task_id: str,
    user_id: str = "default",
    **kwargs
) -> CommandResult:
    """
    Quick function to run a command in a task workspace
    
    Args:
        command: Command to execute
        task_id: Task identifier
        user_id: User identifier
        **kwargs: Additional arguments
        
    Returns:
        CommandResult
    """
    # Set workspace for task
    command_executor.set_workspace(task_id, user_id)
    
    # Execute command
    return await command_executor.execute_command(command, **kwargs)


async def run_aws_command(
    aws_command: str,
    task_id: str,
    user_id: str = "default",
    **kwargs
) -> CommandResult:
    """
    Quick function to run an AWS command in a task workspace
    
    Args:
        aws_command: AWS command (without 'aws' prefix)
        task_id: Task identifier
        user_id: User identifier
        **kwargs: Additional arguments
        
    Returns:
        CommandResult
    """
    # Set workspace for task
    command_executor.set_workspace(task_id, user_id)
    
    # Execute AWS command
    return await command_executor.execute_aws_command(aws_command, **kwargs)


__all__ = [
    "CommandResult",
    "SecureCommandExecutor",
    "command_executor",
    "run_command",
    "run_aws_command"
] 