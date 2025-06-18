"""
OpenRouter AI Client for Claude access
Handles communication with Claude via OpenRouter's unified API
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime

import httpx
from openai import AsyncOpenAI

from .config import get_openrouter_config, settings


logger = logging.getLogger(__name__)


@dataclass
class AIMessage:
    """Represents a conversation message"""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = None
    model_used: str = None
    tokens_used: int = 0
    cost_usd: float = 0.0
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass 
class AIResponse:
    """Represents an AI response with metadata"""
    content: str
    model_used: str
    tokens_used: int
    cost_usd: float
    response_time_ms: int
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class OpenRouterClient:
    """
    OpenRouter client for accessing Claude models
    Provides unified interface for AI interactions
    """
    
    def __init__(self):
        self.config = get_openrouter_config()
        self.client = AsyncOpenAI(
            api_key=self.config["api_key"],
            base_url=self.config["base_url"],
            default_headers=self.config["headers"]
        )
        self.usage_tracker = {}
        
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4000,
        stream: bool = False
    ) -> AIResponse:
        """
        Send chat completion request to OpenRouter
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to primary)
            temperature: Randomness (0.0-1.0)
            max_tokens: Maximum response tokens
            stream: Whether to stream response
            
        Returns:
            AIResponse with content and metadata
        """
        start_time = datetime.utcnow()
        model = model or self.config["model"]
        
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            
            if stream:
                # Handle streaming response
                return await self._handle_stream_response(response, model, start_time)
            else:
                # Handle regular response
                return self._handle_regular_response(response, model, start_time)
                
        except Exception as e:
            logger.error(f"AI completion failed with {model}: {e}")
            
            # Try fallback model if available
            if model != self.config["fallback_model"]:
                logger.info(f"Trying fallback model: {self.config['fallback_model']}")
                return await self.chat_completion(
                    messages=messages,
                    model=self.config["fallback_model"],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream
                )
            
            raise Exception(f"AI completion failed: {e}")
    
    def _handle_regular_response(self, response, model: str, start_time: datetime) -> AIResponse:
        """Handle non-streaming response"""
        end_time = datetime.utcnow()
        response_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        content = response.choices[0].message.content
        tokens_used = response.usage.total_tokens if response.usage else 0
        cost_usd = self._calculate_cost(model, tokens_used)
        
        # Track usage
        self._track_usage(model, tokens_used, cost_usd)
        
        return AIResponse(
            content=content,
            model_used=model,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            response_time_ms=response_time_ms,
            timestamp=end_time
        )
    
    async def _handle_stream_response(self, response_stream, model: str, start_time: datetime) -> AIResponse:
        """Handle streaming response"""
        content_chunks = []
        
        async for chunk in response_stream:
            if chunk.choices[0].delta.content:
                content_chunks.append(chunk.choices[0].delta.content)
        
        end_time = datetime.utcnow()
        response_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        content = "".join(content_chunks)
        tokens_used = len(content.split()) * 1.3  # Rough estimate
        cost_usd = self._calculate_cost(model, tokens_used)
        
        # Track usage
        self._track_usage(model, tokens_used, cost_usd)
        
        return AIResponse(
            content=content,
            model_used=model,
            tokens_used=int(tokens_used),
            cost_usd=cost_usd,
            response_time_ms=response_time_ms,
            timestamp=end_time
        )
    
    def _calculate_cost(self, model: str, tokens: int) -> float:
        """
        Calculate cost in USD based on model and tokens
        OpenRouter pricing (approximate)
        """
        # Rough pricing per 1K tokens (as of 2024)
        pricing = {
            "anthropic/claude-3.5-sonnet": 0.003,  # $3/1M tokens
            "anthropic/claude-3-haiku": 0.00025,   # $0.25/1M tokens
            "anthropic/claude-3-opus": 0.015,      # $15/1M tokens
        }
        
        rate = pricing.get(model, 0.003)  # Default to Sonnet pricing
        return (tokens / 1000) * rate
    
    def _track_usage(self, model: str, tokens: int, cost: float):
        """Track usage statistics"""
        today = datetime.utcnow().date().isoformat()
        
        if today not in self.usage_tracker:
            self.usage_tracker[today] = {}
        
        if model not in self.usage_tracker[today]:
            self.usage_tracker[today][model] = {
                "requests": 0,
                "tokens": 0,
                "cost": 0.0
            }
        
        self.usage_tracker[today][model]["requests"] += 1
        self.usage_tracker[today][model]["tokens"] += tokens
        self.usage_tracker[today][model]["cost"] += cost
        
        logger.info(f"AI Usage - Model: {model}, Tokens: {tokens}, Cost: ${cost:.4f}")
    
    async def ask_claude(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.1
    ) -> AIResponse:
        """
        Simplified interface for asking Claude a question
        
        Args:
            prompt: User question/prompt
            system_prompt: Optional system context
            context: Optional conversation history
            temperature: Response randomness
            
        Returns:
            AIResponse with Claude's answer
        """
        messages = []
        
        # Add system prompt if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation context if provided
        if context:
            messages.extend(context)
        
        # Add user prompt
        messages.append({"role": "user", "content": prompt})
        
        return await self.chat_completion(messages, temperature=temperature)
    
    async def code_assistant(
        self,
        code_request: str,
        language: str = "python",
        context: Optional[str] = None
    ) -> AIResponse:
        """
        Specialized method for code generation/assistance
        
        Args:
            code_request: What code to generate/fix
            language: Programming language
            context: Additional context about the codebase
            
        Returns:
            AIResponse with code solution
        """
        system_prompt = f"""You are an expert {language} developer. 
        Provide clean, well-documented, production-ready code.
        Include error handling and follow best practices.
        Explain your approach briefly."""
        
        if context:
            system_prompt += f"\n\nContext: {context}"
        
        return await self.ask_claude(
            prompt=code_request,
            system_prompt=system_prompt,
            temperature=0.1  # Low temperature for code
        )
    
    async def task_decomposition(
        self,
        task_description: str,
        time_estimate: Optional[str] = None,
        priority: str = "medium"
    ) -> AIResponse:
        """
        Break down complex tasks into manageable steps
        
        Args:
            task_description: What needs to be done
            time_estimate: How much time is available
            priority: Task priority level
            
        Returns:
            AIResponse with task breakdown
        """
        system_prompt = """You are a productivity expert specializing in overemployment.
        Break down tasks into:
        1. Specific actionable steps
        2. Time estimates for each step
        3. Priority levels
        4. Dependencies between steps
        5. Potential automation opportunities
        
        Format as a structured plan that's easy to follow."""
        
        prompt = f"""Task: {task_description}
        Time Available: {time_estimate or 'Not specified'}
        Priority: {priority}
        
        Please provide a detailed breakdown."""
        
        return await self.ask_claude(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.2
        )
    
    def get_usage_stats(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get usage statistics for a specific date
        
        Args:
            date: Date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Usage statistics dictionary
        """
        if date is None:
            date = datetime.utcnow().date().isoformat()
        
        return self.usage_tracker.get(date, {})
    
    def get_total_cost(self, date: Optional[str] = None) -> float:
        """Get total cost for a specific date"""
        stats = self.get_usage_stats(date)
        return sum(model_stats["cost"] for model_stats in stats.values())


# Global client instance
ai_client = OpenRouterClient()


# Convenience functions
async def ask_ai(prompt: str, **kwargs) -> str:
    """Quick function to ask AI and get string response"""
    response = await ai_client.ask_claude(prompt, **kwargs)
    return response.content


async def generate_code(request: str, language: str = "python", **kwargs) -> str:
    """Quick function to generate code"""
    response = await ai_client.code_assistant(request, language, **kwargs)
    return response.content


async def break_down_task(task: str, **kwargs) -> str:
    """Quick function to break down tasks"""
    response = await ai_client.task_decomposition(task, **kwargs)
    return response.content


__all__ = [
    "OpenRouterClient",
    "AIMessage",
    "AIResponse", 
    "ai_client",
    "ask_ai",
    "generate_code",
    "break_down_task"
] 