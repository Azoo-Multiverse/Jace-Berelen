"""
Slack integration and message handling
Processes user commands and provides AI-powered responses
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable

from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError
from slack_bolt.async_app import AsyncApp
from slack_bolt.context.async_context import AsyncBoltContext
from slack_bolt.request.async_request import AsyncBoltRequest
from slack_bolt.response import BoltResponse

from .config import get_slack_config, settings
from .ai_client import ai_client, AIResponse
from .database import get_or_create_user, create_task, log_ai_interaction, get_active_tasks, User, Task
from .utils import format_task_list, parse_time_estimate, extract_priority

logger = logging.getLogger(__name__)


class SlackHandler:
    """
    Main Slack integration handler
    Processes commands and provides AI-powered responses
    """
    
    def __init__(self):
        self.config = get_slack_config()
        self.app = AsyncApp(
            token=self.config["bot_token"],
            signing_secret=self.config["signing_secret"]
        )
        self.client = AsyncWebClient(token=self.config["bot_token"])
        
        # Command registry
        self.commands = {}
        self.setup_handlers()
        
        # Usage tracking
        self.daily_usage = {}
        
    def setup_handlers(self):
        """Set up Slack event and command handlers"""
        logger.info("Setting up Slack handlers...")
        
        # Message handlers
        self.app.message()(self.handle_message)
        
        # Command handlers
        self.app.command("/jace")(self.handle_jace_command)
        self.app.command("/tasks")(self.handle_tasks_command)
        self.app.command("/ai")(self.handle_ai_command)
        
        # App mention handlers
        self.app.event("app_mention")(self.handle_app_mention)
        
        logger.info("Slack handlers setup complete")
    
    async def handle_message(self, message: dict, context: AsyncBoltContext):
        """Handle direct messages and mentions"""
        try:
            user_id = message.get("user")
            channel_id = message.get("channel")
            text = message.get("text", "").strip()
            
            # Skip bot messages
            if message.get("subtype") == "bot_message":
                return
            
            # Get or create user
            user_info = await self.client.users_info(user=user_id)
            username = user_info["user"]["name"]
            email = user_info["user"]["profile"].get("email", f"{username}@example.com")
            
            user = await get_or_create_user(user_id, username, email)
            
            # Check if it's a DM
            if channel_id.startswith("D"):
                await self.handle_direct_message(user, text, channel_id)
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self.send_error_message(message.get("channel"), str(e))
    
    async def handle_direct_message(self, user: User, text: str, channel_id: str):
        """Handle direct messages with AI assistance"""
        try:
            # Log the interaction
            await log_ai_interaction(
                user_id=user.id,
                interaction_type="direct_message",
                prompt=text,
                response="",  # Will update after AI response
                model_used="",
                tokens_used=0,
                cost_usd=0.0,
                response_time_ms=0
            )
            
            # Check for specific commands
            if text.lower().startswith("create task"):
                await self.handle_create_task_from_text(user, text, channel_id)
            elif text.lower().startswith("help"):
                await self.send_help_message(channel_id)
            elif text.lower().startswith("status"):
                await self.send_status_update(user, channel_id)
            else:
                # General AI assistance
                await self.handle_ai_conversation(user, text, channel_id)
                
        except Exception as e:
            logger.error(f"Error handling DM: {e}")
            await self.send_error_message(channel_id, "Sorry, I encountered an error processing your message.")
    
    async def handle_jace_command(self, ack, body: dict, context: AsyncBoltContext):
        """Handle /jace slash command"""
        await ack()
        
        try:
            user_id = body["user_id"]
            channel_id = body["channel_id"]
            command_text = body.get("text", "").strip()
            
            # Get user
            user_info = await self.client.users_info(user=user_id)
            username = user_info["user"]["name"]
            email = user_info["user"]["profile"].get("email", f"{username}@example.com")
            user = await get_or_create_user(user_id, username, email)
            
            if not command_text or command_text == "help":
                await self.send_jace_help(channel_id)
            elif command_text.startswith("create"):
                await self.handle_create_task_command(user, command_text[6:].strip(), channel_id)
            elif command_text == "status":
                await self.send_status_update(user, channel_id)
            elif command_text == "tasks":
                await self.send_task_list(user, channel_id)
            else:
                # AI assistance for any other query
                response = await ai_client.ask_claude(
                    prompt=command_text,
                    system_prompt="You are Jace Berelen, an AI assistant specialized in overemployment support. Help the user manage multiple jobs efficiently."
                )
                
                await self.client.chat_postMessage(
                    channel=channel_id,
                    text=response.content,
                    blocks=[
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Jace AI Response:*\n\n{response.content}"
                            }
                        },
                        {
                            "type": "context",
                            "elements": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"Model: {response.model_used} | Tokens: {response.tokens_used} | Cost: ${response.cost_usd:.4f}"
                                }
                            ]
                        }
                    ]
                )
                
                # Log interaction
                await log_ai_interaction(
                    user_id=user.id,
                    interaction_type="slash_command",
                    prompt=command_text,
                    response=response.content,
                    model_used=response.model_used,
                    tokens_used=response.tokens_used,
                    cost_usd=response.cost_usd,
                    response_time_ms=response.response_time_ms
                )
        
        except Exception as e:
            logger.error(f"Error handling /jace command: {e}")
            await self.send_error_message(channel_id, "Error processing command")
    
    async def handle_tasks_command(self, ack, body: dict, context: AsyncBoltContext):
        """Handle /tasks slash command"""
        await ack()
        
        try:
            user_id = body["user_id"]
            channel_id = body["channel_id"]
            
            # Get user
            user_info = await self.client.users_info(user=user_id)
            username = user_info["user"]["name"]
            user = await get_or_create_user(user_id, username)
            
            # Get active tasks
            tasks = await get_active_tasks(user.id, limit=10)
            
            if not tasks:
                await self.client.chat_postMessage(
                    channel=channel_id,
                    text="No active tasks! You're all caught up.",
                    blocks=[
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "*No active tasks!*\n\nYou're all caught up. Ready to take on new challenges?"
                            }
                        },
                        {
                            "type": "actions",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                        "text": "Create New Task"
                                    },
                                    "action_id": "create_task_modal",
                                    "style": "primary"
                                }
                            ]
                        }
                    ]
                )
            else:
                task_blocks = self.build_task_list_blocks(tasks)
                await self.client.chat_postMessage(
                    channel=channel_id,
                    text=f"You have {len(tasks)} active tasks",
                    blocks=task_blocks
                )
        
        except Exception as e:
            logger.error(f"Error handling /tasks command: {e}")
            await self.send_error_message(channel_id, "Error retrieving tasks")
    
    async def handle_ai_command(self, ack, body: dict, context: AsyncBoltContext):
        """Handle /ai slash command for direct AI assistance"""
        await ack()
        
        try:
            user_id = body["user_id"]
            channel_id = body["channel_id"]
            command_text = body.get("text", "").strip()
            
            if not command_text:
                await self.client.chat_postMessage(
                    channel=channel_id,
                    text="Please provide a question or request. Example: `/ai How do I prioritize tasks across 3 different jobs?`"
                )
                return
            
            # Get user
            user_info = await self.client.users_info(user=user_id)
            username = user_info["user"]["name"]
            user = await get_or_create_user(user_id, username)
            
            # Get AI response
            response = await ai_client.ask_claude(
                prompt=command_text,
                system_prompt="""You are Jace Berelen, an expert AI assistant for overemployed professionals. 
                You help people manage multiple jobs simultaneously by providing:
                - Task prioritization strategies
                - Time management techniques
                - Automation suggestions
                - Communication templates
                - Productivity hacks
                
                Be concise, practical, and actionable in your responses."""
            )
            
            # Send response
            await self.client.chat_postMessage(
                channel=channel_id,
                text=response.content,
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"🧠 *AI Assistant Response:*\n\n{response.content}"
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "👍 Helpful"
                                },
                                "action_id": "rate_response_positive",
                                "value": str(response.tokens_used)
                            },
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "👎 Not helpful"
                                },
                                "action_id": "rate_response_negative",
                                "value": str(response.tokens_used)
                            },
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "Follow up"
                                },
                                "action_id": "ai_follow_up",
                                "value": "follow_up"
                            }
                        ]
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"Cost: ${response.cost_usd:.4f} | Tokens: {response.tokens_used} | Response time: {response.response_time_ms}ms"
                            }
                        ]
                    }
                ]
            )
            
            # Log interaction
            await log_ai_interaction(
                user_id=user.id,
                interaction_type="ai_command",
                prompt=command_text,
                response=response.content,
                model_used=response.model_used,
                tokens_used=response.tokens_used,
                cost_usd=response.cost_usd,
                response_time_ms=response.response_time_ms
            )
        
        except Exception as e:
            logger.error(f"Error handling /ai command: {e}")
            await self.send_error_message(channel_id, "Error processing AI request")
    
    async def handle_app_mention(self, event: dict, context: AsyncBoltContext):
        """Handle @jace mentions in channels"""
        try:
            user_id = event["user"]
            channel_id = event["channel"]
            text = event["text"]
            
            # Remove mention from text
            text = re.sub(r'<@[A-Z0-9]+>', '', text).strip()
            
            if not text:
                await self.client.chat_postMessage(
                    channel=channel_id,
                    text="👋 Hi! I'm Jace, your overemployment AI assistant. Try asking me something like 'help me prioritize my tasks' or use `/jace help` for commands."
                )
                return
            
            # Get user
            user_info = await self.client.users_info(user=user_id)
            username = user_info["user"]["name"]
            user = await get_or_create_user(user_id, username)
            
            # Process mention as AI request
            response = await ai_client.ask_claude(
                prompt=text,
                system_prompt="You are Jace Berelen, helping with overemployment in a Slack channel. Be helpful but concise since others can see this."
            )
            
            await self.client.chat_postMessage(
                channel=channel_id,
                text=f"<@{user_id}> {response.content}",
                thread_ts=event.get("ts")  # Reply in thread if possible
            )
            
            # Log interaction
            await log_ai_interaction(
                user_id=user.id,
                interaction_type="mention",
                prompt=text,
                response=response.content,
                model_used=response.model_used,
                tokens_used=response.tokens_used,
                cost_usd=response.cost_usd,
                response_time_ms=response.response_time_ms
            )
        
        except Exception as e:
            logger.error(f"Error handling app mention: {e}")
    
    async def handle_create_task_from_text(self, user: User, text: str, channel_id: str):
        """Create task from natural language"""
        try:
            # Use AI to parse the task creation request
            response = await ai_client.ask_claude(
                prompt=f"""Parse this task creation request and extract:
                1. Task title (clear, actionable)
                2. Task description (details)
                3. Priority (low, medium, high, urgent)
                4. Estimated hours (if mentioned)
                5. Due date (if mentioned)
                
                Request: "{text}"
                
                Respond in JSON format:
                {{
                    "title": "...",
                    "description": "...",
                    "priority": "medium",
                    "estimated_hours": null,
                    "due_date": null
                }}""",
                system_prompt="You are a task parsing expert. Extract structured data from natural language requests."
            )
            
            try:
                task_data = json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback to simple parsing
                task_title = text.replace("create task", "").strip()
                task_data = {
                    "title": task_title,
                    "description": "",
                    "priority": "medium",
                    "estimated_hours": None,
                    "due_date": None
                }
            
            # Create the task
            task = await create_task(
                user_id=user.id,
                title=task_data["title"],
                description=task_data["description"],
                priority=task_data["priority"]
            )
            
            await self.client.chat_postMessage(
                channel=channel_id,
                text=f"Task created: {task.title}",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                                                          "text": f"*Task Created Successfully*\n\n*Title:* {task.title}\n*Priority:* {task.priority}\n*Status:* {task.status}"
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "Start Task"
                                },
                                "action_id": "start_task",
                                "value": str(task.id),
                                "style": "primary"
                            },
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "Get AI Help"
                                },
                                "action_id": "get_ai_help",
                                "value": str(task.id)
                            }
                        ]
                    }
                ]
            )
            
            # Log AI interaction
            await log_ai_interaction(
                user_id=user.id,
                task_id=task.id,
                interaction_type="task_creation",
                prompt=text,
                response=response.content,
                model_used=response.model_used,
                tokens_used=response.tokens_used,
                cost_usd=response.cost_usd,
                response_time_ms=response.response_time_ms
            )
        
        except Exception as e:
            logger.error(f"Error creating task from text: {e}")
            await self.send_error_message(channel_id, "Error creating task")
    
    def build_task_list_blocks(self, tasks: List[Task]) -> List[Dict]:
        """Build Slack blocks for task list display"""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                                            "text": f"Your Active Tasks ({len(tasks)})"
                }
            }
        ]
        
        for i, task in enumerate(tasks[:5]):  # Show max 5 tasks
            priority_emoji = {
                "low": "🔵",
                "medium": "🟡", 
                "high": "🟠",
                "urgent": "🔴"
            }.get(task.priority, "⚪")
            
            status_emoji = {
                                  "pending": "PENDING",
                  "in_progress": "IN_PROGRESS",
                  "completed": "DONE",
                  "failed": "FAILED",
                  "cancelled": "CANCELLED"
              }.get(task.status, "UNKNOWN")
            
            blocks.extend([
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{priority_emoji} *{task.title}*\n{status_emoji} {task.status.replace('_', ' ').title()}"
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Details"
                        },
                        "action_id": "view_task_details",
                        "value": str(task.id)
                    }
                }
            ])
            
            if i < len(tasks) - 1:
                blocks.append({"type": "divider"})
        
        if len(tasks) > 5:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"... and {len(tasks) - 5} more tasks. Use `/tasks all` to see everything."
                    }
                ]
            })
        
        # Add action buttons
        blocks.extend([
            {"type": "divider"},
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Create New Task"
                        },
                        "action_id": "create_task_modal",
                        "style": "primary"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Get AI Help"
                        },
                        "action_id": "get_ai_task_help"
                    }
                ]
            }
        ])
        
        return blocks
    
    async def send_help_message(self, channel_id: str):
        """Send help information"""
        help_text = """
        *Jace Berelen - Your Overemployment AI Assistant*

*Available Commands:*
• `/jace help` - Show this help message
• `/jace create [task description]` - Create a new task
• `/jace status` - Show your current status
• `/tasks` - View your active tasks
• `/ai [question]` - Ask me anything about overemployment

*Direct Message Commands:*
• `create task [description]` - Create a task via DM
• `help` - Get help
• `status` - Check your status
• Just ask me anything naturally!

*Tips:*
• I can help you prioritize tasks across multiple jobs
• Ask me for automation suggestions
• I provide time management strategies
• Mention me in channels with `@jace [question]`

*Examples:*
• "How do I manage 3 different codebases efficiently?"
• "Create task: Review pull requests for Project Alpha"
• "What's the best way to handle overlapping meetings?"
"""
        
        await self.client.chat_postMessage(
            channel=channel_id,
            text=help_text,
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": help_text
                    }
                }
            ]
        )
    
    async def send_error_message(self, channel_id: str, error_message: str):
        """Send user-friendly error message"""
        await self.client.chat_postMessage(
            channel=channel_id,
                text=f"Error: {error_message}",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                                                  "text": f"*Error*\n\n{error_message}\n\nTry using `/jace help` for available commands."
                    }
                }
            ]
        )
    
    async def start_server(self, port: int = 3000):
        """Start the Slack app server"""
        try:
            logger.info(f"Starting Slack app server on port {port}")
            await self.app.async_start(port=port)
        except Exception as e:
            logger.error(f"Failed to start Slack server: {e}")
            raise


# Global handler instance
slack_handler = SlackHandler()


async def send_notification(user_id: str, message: str, channel: str = None):
    """Send notification to user"""
    try:
        target_channel = channel or user_id  # DM if no channel specified
        
        await slack_handler.client.chat_postMessage(
            channel=target_channel,
            text=message
        )
        
        logger.info(f"Sent notification to {user_id}: {message[:50]}...")
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")


__all__ = [
    "SlackHandler",
    "slack_handler",
    "send_notification"
] 