"""
Main FastAPI application for Jace Berelen POC
Entry point that ties together all components
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from pydantic import BaseModel

from .config import settings, validate_environment, get_openrouter_config
from .database import init_database, db_manager, get_or_create_user, get_active_tasks
from .ai_client import ai_client, ask_ai
from .slack_handler import slack_handler
from .utils import setup_logging, get_system_info

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting Jace Berelen POC...")
    
    # Validate environment
    is_valid, missing = validate_environment()
    if not is_valid:
        logger.error(f"Environment validation failed. Missing: {missing}")
        sys.exit(1)
    
    # Initialize database
    try:
        init_database()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)
    
    # Test AI connection
    try:
        test_response = await ai_client.ask_claude("Hello, are you working?")
        logger.info(f"AI connection test successful: {test_response.content[:50]}...")
    except Exception as e:
        logger.error(f"AI connection test failed: {e}")
        sys.exit(1)
    
    # Start Slack handler in background
    if settings.slack_bot_token:
        try:
            # Start Slack app server
            slack_task = asyncio.create_task(
                slack_handler.start_server(port=settings.port + 1)
            )
            logger.info("Slack handler started")
        except Exception as e:
            logger.error(f"Slack handler failed to start: {e}")
    
    logger.info("Jace Berelen POC started successfully!")
    
    yield
    
    logger.info("Shutting down Jace Berelen POC...")


# Create FastAPI app
app = FastAPI(
    title="Jace Berelen POC",
    description="AI-driven workflow automation platform for overemployment support",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.environment == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# MODELS
# ============================================================================

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    environment: str
    database_connected: bool
    ai_connected: bool


class TaskRequest(BaseModel):
    title: str
    description: str = ""
    priority: str = "medium"
    job_id: int = None


class AIRequest(BaseModel):
    prompt: str
    system_prompt: str = None
    temperature: float = 0.1


class AIResponse(BaseModel):
    content: str
    model_used: str
    tokens_used: int
    cost_usd: float
    response_time_ms: int


# ============================================================================
# ROUTES
# ============================================================================

@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with basic info"""
    return {
        "name": "Jace Berelen POC",
        "version": "0.1.0",
        "description": "AI-driven workflow automation platform for overemployment support",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "health": "/health",
            "ai": "/ai/chat",
            "tasks": "/tasks",
            "docs": "/docs"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    # Test database connection
    db_connected = await db_manager.health_check()
    
    # Test AI connection
    ai_connected = True
    try:
        await ai_client.ask_claude("ping", temperature=0.0)
    except Exception:
        ai_connected = False
    
    return HealthResponse(
        status="healthy" if db_connected and ai_connected else "degraded",
        timestamp=datetime.utcnow(),
        version="0.1.0",
        environment=settings.environment,
        database_connected=db_connected,
        ai_connected=ai_connected
    )


@app.get("/system-info")
async def system_info():
    """Get system information"""
    return get_system_info()


# ============================================================================
# AI ENDPOINTS
# ============================================================================

@app.post("/ai/chat", response_model=AIResponse)
async def chat_with_ai(request: AIRequest):
    """Chat with AI assistant"""
    try:
        response = await ai_client.ask_claude(
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            temperature=request.temperature
        )
        
        return AIResponse(
            content=response.content,
            model_used=response.model_used,
            tokens_used=response.tokens_used,
            cost_usd=response.cost_usd,
            response_time_ms=response.response_time_ms
        )
    
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ai/code-help")
async def get_code_help(request: dict):
    """Get AI help with code"""
    try:
        code_request = request.get("code_request")
        language = request.get("language", "python")
        context = request.get("context", "")
        
        if not code_request:
            raise HTTPException(status_code=400, detail="code_request is required")
        
        response = await ai_client.code_assistant(
            code_request=code_request,
            language=language,
            context=context
        )
        
        return AIResponse(
            content=response.content,
            model_used=response.model_used,
            tokens_used=response.tokens_used,
            cost_usd=response.cost_usd,
            response_time_ms=response.response_time_ms
        )
    
    except Exception as e:
        logger.error(f"Code help error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ai/task-breakdown")
async def break_down_task(request: dict):
    """Break down a complex task using AI"""
    try:
        task_description = request.get("task_description")
        time_estimate = request.get("time_estimate")
        priority = request.get("priority", "medium")
        
        if not task_description:
            raise HTTPException(status_code=400, detail="task_description is required")
        
        response = await ai_client.task_decomposition(
            task_description=task_description,
            time_estimate=time_estimate,
            priority=priority
        )
        
        return AIResponse(
            content=response.content,
            model_used=response.model_used,
            tokens_used=response.tokens_used,
            cost_usd=response.cost_usd,
            response_time_ms=response.response_time_ms
        )
    
    except Exception as e:
        logger.error(f"Task breakdown error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TASK MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/tasks")
async def create_task_endpoint(request: TaskRequest):
    """Create a new task"""
    try:
        # For POC, we'll use a default user
        # In production, this would be extracted from authentication
        user = await get_or_create_user("default_user", "poc_user")
        
        task = await create_task(
            user_id=user.id,
            title=request.title,
            description=request.description,
            priority=request.priority,
            job_id=request.job_id
        )
        
        return {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "created_at": task.created_at.isoformat()
        }
    
    except Exception as e:
        logger.error(f"Task creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks")
async def get_tasks():
    """Get active tasks"""
    try:
        # For POC, we'll use a default user
        user = await get_or_create_user("default_user", "poc_user")
        
        tasks = await get_active_tasks(user.id, limit=20)
        
        return {
            "tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "status": task.status,
                    "priority": task.priority,
                    "created_at": task.created_at.isoformat(),
                    "due_date": task.due_date.isoformat() if task.due_date else None
                }
                for task in tasks
            ],
            "total": len(tasks)
        }
    
    except Exception as e:
        logger.error(f"Task retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# METRICS AND MONITORING
# ============================================================================

@app.get("/metrics/usage")
async def get_usage_metrics():
    """Get AI usage metrics"""
    try:
        today_stats = ai_client.get_usage_stats()
        total_cost = ai_client.get_total_cost()
        
        return {
            "today": today_stats,
            "total_cost_today": total_cost,
            "budget_remaining": settings.monthly_budget_limit - total_cost,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics/performance")
async def get_performance_metrics():
    """Get system performance metrics"""
    try:
        return {
            "database_health": await db_manager.health_check(),
            "ai_client_status": "connected",
            "active_tasks": 0,  # TODO: Implement
            "total_users": 1,   # TODO: Implement
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Performance metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WEBHOOK ENDPOINTS
# ============================================================================

@app.post("/webhooks/slack")
async def slack_webhook(request: dict):
    """Handle Slack webhook events"""
    # This will be handled by the Slack handler
    return {"status": "received"}


@app.post("/webhooks/github")
async def github_webhook(request: dict):
    """Handle GitHub webhook events"""
    # TODO: Implement GitHub integration
    return {"status": "received"}


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url)
        }
    )


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )