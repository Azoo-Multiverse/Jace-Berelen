"""
AI Agents for specialized automation tasks
Handles different types of work automation for overemployment
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

from .ai_client import ai_client, AIResponse
from .database import Task, Job, create_task, log_ai_interaction

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of AI agents available"""
    TASK_MANAGER = "task_manager"
    CODE_ASSISTANT = "code_assistant"
    COMMUNICATION = "communication"
    RESEARCH = "research"
    AUTOMATION = "automation"
    SCHEDULER = "scheduler"


@dataclass
class AgentResult:
    """Result from an AI agent execution"""
    success: bool
    content: str
    metadata: Dict[str, Any] = None
    cost_usd: float = 0.0
    execution_time_ms: int = 0
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.suggestions is None:
            self.suggestions = []


class BaseAgent(ABC):
    """Base class for all AI agents"""
    
    def __init__(self, agent_type: AgentType, specialization: str = ""):
        self.agent_type = agent_type
        self.specialization = specialization
        self.usage_stats = {
            "total_calls": 0,
            "total_cost": 0.0,
            "total_tokens": 0,
            "success_rate": 0.0
        }
        
    @abstractmethod
    async def execute(self, request: Dict[str, Any], context: Dict[str, Any] = None) -> AgentResult:
        """Execute the agent's primary function"""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent"""
        pass
    
    async def _call_ai(self, prompt: str, context: Dict[str, Any] = None) -> AIResponse:
        """Make an AI call with proper logging and stats tracking"""
        start_time = datetime.utcnow()
        
        try:
            response = await ai_client.ask_claude(
                prompt=prompt,
                system_prompt=self.get_system_prompt(),
                temperature=0.1
            )
            
            # Update usage stats
            self.usage_stats["total_calls"] += 1
            self.usage_stats["total_cost"] += response.cost_usd
            self.usage_stats["total_tokens"] += response.tokens_used
            
            return response
            
        except Exception as e:
            logger.error(f"Agent {self.agent_type.value} AI call failed: {e}")
            raise


class TaskManagerAgent(BaseAgent):
    """Agent specialized in task management and prioritization"""
    
    def __init__(self):
        super().__init__(AgentType.TASK_MANAGER, "Task Management & Prioritization")
    
    def get_system_prompt(self) -> str:
        return """You are a Task Management AI Agent specialized in overemployment scenarios.
        Your expertise includes:
        - Breaking down complex tasks into manageable steps
        - Prioritizing tasks across multiple jobs
        - Estimating time requirements accurately
        - Identifying automation opportunities
        - Suggesting optimal work schedules
        - Managing deadlines and dependencies
        
        Always provide:
        1. Clear, actionable steps
        2. Time estimates
        3. Priority recommendations
        4. Automation suggestions
        5. Risk assessment
        
        Be concise but comprehensive."""
    
    async def execute(self, request: Dict[str, Any], context: Dict[str, Any] = None) -> AgentResult:
        """Break down and prioritize tasks"""
        start_time = datetime.utcnow()
        
        try:
            task_description = request.get("task_description", "")
            current_workload = request.get("current_workload", [])
            available_time = request.get("available_time", "8 hours")
            job_priorities = request.get("job_priorities", {})
            
            prompt = f"""
            Task to analyze: {task_description}
            
            Current workload: {len(current_workload)} active tasks
            Available time: {available_time}
            Job priorities: {job_priorities}
            
            Please provide:
            1. Task breakdown (specific steps)
            2. Time estimate for each step
            3. Overall priority level (1-10)
            4. Automation opportunities
            5. Scheduling recommendations
            6. Risk factors and mitigation
            
            Format as structured JSON with clear sections.
            """
            
            response = await self._call_ai(prompt, context)
            
            execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return AgentResult(
                success=True,
                content=response.content,
                metadata={
                    "agent_type": self.agent_type.value,
                    "task_description": task_description,
                    "model_used": response.model_used
                },
                cost_usd=response.cost_usd,
                execution_time_ms=execution_time_ms,
                suggestions=self._extract_suggestions(response.content)
            )
            
        except Exception as e:
            logger.error(f"TaskManagerAgent execution failed: {e}")
            return AgentResult(
                success=False,
                content=f"Task analysis failed: {str(e)}",
                execution_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000)
            )
    
    def _extract_suggestions(self, content: str) -> List[str]:
        """Extract actionable suggestions from AI response"""
        suggestions = []
        
        # Look for automation opportunities
        if "automat" in content.lower():
            suggestions.append("Consider automation opportunities")
        
        # Look for scheduling recommendations  
        if "schedule" in content.lower() or "time" in content.lower():
            suggestions.append("Review scheduling recommendations")
        
        # Look for priority indicators
        if "priority" in content.lower() or "urgent" in content.lower():
            suggestions.append("Evaluate task priority")
        
        return suggestions


class CodeAssistantAgent(BaseAgent):
    """Agent specialized in code generation and debugging"""
    
    def __init__(self):
        super().__init__(AgentType.CODE_ASSISTANT, "Code Generation & Debugging")
    
    def get_system_prompt(self) -> str:
        return """You are a Code Assistant AI Agent for overemployed developers.
        Your expertise includes:
        - Writing clean, efficient code in multiple languages
        - Debugging and troubleshooting issues
        - Code review and optimization
        - Automated testing suggestions
        - Documentation generation
        - Best practices for rapid development
        
        Always provide:
        1. Working, tested code
        2. Clear comments and documentation
        3. Error handling
        4. Performance considerations
        5. Testing suggestions
        
        Focus on code that works immediately and can be maintained easily."""
    
    async def execute(self, request: Dict[str, Any], context: Dict[str, Any] = None) -> AgentResult:
        """Generate or debug code"""
        start_time = datetime.utcnow()
        
        try:
            code_request = request.get("code_request", "")
            language = request.get("language", "python")
            existing_code = request.get("existing_code", "")
            requirements = request.get("requirements", [])
            
            prompt = f"""
            Code request: {code_request}
            Language: {language}
            
            {'Existing code to modify:' + existing_code if existing_code else ''}
            
            Requirements:
            {chr(10).join(f'- {req}' for req in requirements)}
            
            Please provide:
            1. Complete working code
            2. Detailed comments
            3. Error handling
            4. Usage examples
            5. Testing suggestions
            6. Performance notes
            
            Make the code production-ready and easy to maintain.
            """
            
            response = await self._call_ai(prompt, context)
            
            execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return AgentResult(
                success=True,
                content=response.content,
                metadata={
                    "agent_type": self.agent_type.value,
                    "language": language,
                    "code_request": code_request,
                    "model_used": response.model_used
                },
                cost_usd=response.cost_usd,
                execution_time_ms=execution_time_ms,
                suggestions=["Test the generated code", "Review for security", "Add to version control"]
            )
            
        except Exception as e:
            logger.error(f"CodeAssistantAgent execution failed: {e}")
            return AgentResult(
                success=False,
                content=f"Code generation failed: {str(e)}",
                execution_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000)
            )


class CommunicationAgent(BaseAgent):
    """Agent specialized in professional communication"""
    
    def __init__(self):
        super().__init__(AgentType.COMMUNICATION, "Professional Communication")
    
    def get_system_prompt(self) -> str:
        return """You are a Communication AI Agent for overemployed professionals.
        Your expertise includes:
        - Crafting professional emails and messages
        - Meeting response templates
        - Status update communications
        - Conflict resolution language
        - Time management excuses/explanations
        - Professional boundary setting
        
        Always provide:
        1. Professional, appropriate tone
        2. Clear, concise messaging
        3. Multiple template options
        4. Customization suggestions
        5. Follow-up recommendations
        
        Help maintain professional relationships while managing multiple commitments."""
    
    async def execute(self, request: Dict[str, Any], context: Dict[str, Any] = None) -> AgentResult:
        """Generate professional communication"""
        start_time = datetime.utcnow()
        
        try:
            communication_type = request.get("type", "email")
            recipient = request.get("recipient", "colleague")
            purpose = request.get("purpose", "")
            tone = request.get("tone", "professional")
            context_info = request.get("context", "")
            
            prompt = f"""
            Communication request:
            Type: {communication_type}
            Recipient: {recipient}
            Purpose: {purpose}
            Desired tone: {tone}
            Context: {context_info}
            
            Please provide:
            1. Main message template
            2. Alternative versions (formal/casual)
            3. Subject line options (if applicable)
            4. Follow-up suggestions
            5. Timing recommendations
            
            Ensure the communication is professional and maintains good relationships.
            """
            
            response = await self._call_ai(prompt, context)
            
            execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return AgentResult(
                success=True,
                content=response.content,
                metadata={
                    "agent_type": self.agent_type.value,
                    "communication_type": communication_type,
                    "recipient": recipient,
                    "model_used": response.model_used
                },
                cost_usd=response.cost_usd,
                execution_time_ms=execution_time_ms,
                suggestions=["Review before sending", "Consider timing", "Plan follow-up"]
            )
            
        except Exception as e:
            logger.error(f"CommunicationAgent execution failed: {e}")
            return AgentResult(
                success=False,
                content=f"Communication generation failed: {str(e)}",
                execution_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000)
            )


class ResearchAgent(BaseAgent):
    """Agent specialized in research and information gathering"""
    
    def __init__(self):
        super().__init__(AgentType.RESEARCH, "Research & Information Gathering")
    
    def get_system_prompt(self) -> str:
        return """You are a Research AI Agent for overemployed professionals.
        Your expertise includes:
        - Quick information gathering and synthesis
        - Technical research and analysis
        - Market research and trends
        - Competitive analysis
        - Documentation and knowledge management
        - Fact-checking and verification
        
        Always provide:
        1. Comprehensive yet concise information
        2. Structured findings
        3. Source recommendations
        4. Key takeaways
        5. Action items
        
        Focus on actionable insights that save time and improve decision-making."""
    
    async def execute(self, request: Dict[str, Any], context: Dict[str, Any] = None) -> AgentResult:
        """Conduct research and provide insights"""
        start_time = datetime.utcnow()
        
        try:
            research_topic = request.get("topic", "")
            research_depth = request.get("depth", "medium")
            specific_questions = request.get("questions", [])
            time_constraint = request.get("time_limit", "30 minutes")
            
            prompt = f"""
            Research topic: {research_topic}
            Research depth: {research_depth}
            Time constraint: {time_constraint}
            
            Specific questions to address:
            {chr(10).join(f'- {q}' for q in specific_questions)}
            
            Please provide:
            1. Executive summary
            2. Key findings
            3. Detailed analysis
            4. Recommended sources for further reading
            5. Action items
            6. Potential follow-up research
            
            Focus on practical, actionable insights.
            """
            
            response = await self._call_ai(prompt, context)
            
            execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return AgentResult(
                success=True,
                content=response.content,
                metadata={
                    "agent_type": self.agent_type.value,
                    "research_topic": research_topic,
                    "depth": research_depth,
                    "model_used": response.model_used
                },
                cost_usd=response.cost_usd,
                execution_time_ms=execution_time_ms,
                suggestions=["Verify key facts", "Check recent updates", "Save research notes"]
            )
            
        except Exception as e:
            logger.error(f"ResearchAgent execution failed: {e}")
            return AgentResult(
                success=False,
                content=f"Research failed: {str(e)}",
                execution_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000)
            )


class AgentManager:
    """Manages and coordinates AI agents"""
    
    def __init__(self):
        self.agents = {
            AgentType.TASK_MANAGER: TaskManagerAgent(),
            AgentType.CODE_ASSISTANT: CodeAssistantAgent(),
            AgentType.COMMUNICATION: CommunicationAgent(),
            AgentType.RESEARCH: ResearchAgent()
        }
        
        self.execution_history = []
    
    async def execute_agent(
        self,
        agent_type: AgentType,
        request: Dict[str, Any],
        context: Dict[str, Any] = None,
        user_id: int = None
    ) -> AgentResult:
        """Execute a specific agent"""
        
        if agent_type not in self.agents:
            return AgentResult(
                success=False,
                content=f"Agent type {agent_type.value} not available"
            )
        
        agent = self.agents[agent_type]
        
        try:
            result = await agent.execute(request, context)
            
            # Log execution
            self.execution_history.append({
                "timestamp": datetime.utcnow(),
                "agent_type": agent_type.value,
                "success": result.success,
                "cost": result.cost_usd,
                "user_id": user_id
            })
            
            # Log to database if user_id provided
            if user_id and result.success:
                await log_ai_interaction(
                    user_id=user_id,
                    interaction_type=f"agent_{agent_type.value}",
                    prompt=str(request),
                    response=result.content,
                    model_used=result.metadata.get("model_used", "unknown"),
                    tokens_used=result.metadata.get("tokens_used", 0),
                    cost_usd=result.cost_usd,
                    response_time_ms=result.execution_time_ms
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return AgentResult(
                success=False,
                content=f"Agent execution failed: {str(e)}"
            )
    
    def get_agent_stats(self, agent_type: AgentType = None) -> Dict[str, Any]:
        """Get usage statistics for agents"""
        
        if agent_type:
            if agent_type in self.agents:
                return self.agents[agent_type].usage_stats
            else:
                return {}
        
        # Return stats for all agents
        return {
            agent_type.value: agent.usage_stats
            for agent_type, agent in self.agents.items()
        }
    
    def get_available_agents(self) -> List[Dict[str, str]]:
        """Get list of available agents"""
        
        return [
            {
                "type": agent_type.value,
                "name": agent.specialization,
                "description": agent.get_system_prompt()[:200] + "..."
            }
            for agent_type, agent in self.agents.items()
        ]


# Global agent manager instance
agent_manager = AgentManager()


# Convenience functions
async def analyze_task(task_description: str, context: Dict[str, Any] = None, user_id: int = None) -> AgentResult:
    """Analyze a task using the TaskManagerAgent"""
    return await agent_manager.execute_agent(
        AgentType.TASK_MANAGER,
        {"task_description": task_description},
        context,
        user_id
    )


async def generate_code(code_request: str, language: str = "python", user_id: int = None) -> AgentResult:
    """Generate code using the CodeAssistantAgent"""
    return await agent_manager.execute_agent(
        AgentType.CODE_ASSISTANT,
        {"code_request": code_request, "language": language},
        user_id=user_id
    )


async def draft_communication(
    communication_type: str,
    purpose: str,
    recipient: str = "colleague",
    user_id: int = None
) -> AgentResult:
    """Draft professional communication"""
    return await agent_manager.execute_agent(
        AgentType.COMMUNICATION,
        {
            "type": communication_type,
            "purpose": purpose,
            "recipient": recipient
        },
        user_id=user_id
    )


async def research_topic(topic: str, questions: List[str] = None, user_id: int = None) -> AgentResult:
    """Research a topic"""
    return await agent_manager.execute_agent(
        AgentType.RESEARCH,
        {
            "topic": topic,
            "questions": questions or []
        },
        user_id=user_id
    )


__all__ = [
    "AgentType",
    "AgentResult",
    "BaseAgent",
    "TaskManagerAgent",
    "CodeAssistantAgent", 
    "CommunicationAgent",
    "ResearchAgent",
    "AgentManager",
    "agent_manager",
    "analyze_task",
    "generate_code",
    "draft_communication",
    "research_topic"
] 