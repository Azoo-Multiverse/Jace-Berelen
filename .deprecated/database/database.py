"""
Database models and connection management
SQLite for development, PostgreSQL for Railway production
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum

from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, Text, Boolean, 
    Float, JSON, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.sql import text

from .config import settings, is_railway, get_database_url

logger = logging.getLogger(__name__)

# Base class for all models
Base = declarative_base()


class TaskStatus(Enum):
    """Task status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(Enum):
    """Job priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# ============================================================================
# MODELS
# ============================================================================

class User(Base):
    """User model for authentication and job management"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    slack_user_id = Column(String(50), unique=True, index=True)
    username = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True)
    full_name = Column(String(200))
    
    # Overemployment settings
    max_concurrent_jobs = Column(Integer, default=5)
    monthly_budget_usd = Column(Float, default=100.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    ai_interactions = relationship("AIInteraction", back_populates="user", cascade="all, delete-orphan")


class Job(Base):
    """Job/Client model for managing multiple employment"""
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    
    # Job details
    company_name = Column(String(200), nullable=False)
    position_title = Column(String(200), nullable=False)
    job_type = Column(String(50), default="remote")  # remote, hybrid, onsite
    
    # Priority and status
    priority = Column(String(20), default=JobPriority.MEDIUM.value)
    is_active = Column(Boolean, default=True)
    
    # Financial tracking
    hourly_rate = Column(Float, nullable=True)
    monthly_budget = Column(Float, default=20.0)
    
    # Work schedule
    work_hours_start = Column(String(10))  # "09:00"
    work_hours_end = Column(String(10))    # "17:00"
    timezone = Column(String(50), default="UTC")
    
    # Integration settings
    slack_channel = Column(String(100), nullable=True)
    github_repo = Column(String(200), nullable=True)
    trello_board_id = Column(String(50), nullable=True)
    
    # Metadata
    notes = Column(Text)
    tags = Column(JSON)  # ["python", "backend", "startup"]
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    start_date = Column(DateTime)
    end_date = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="jobs")
    tasks = relationship("Task", back_populates="job", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_job_user_active', 'user_id', 'is_active'),
        Index('idx_job_priority', 'priority'),
    )


class Task(Base):
    """Task model for work items across all jobs"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), index=True, nullable=True)
    
    # Task details
    title = Column(String(500), nullable=False)
    description = Column(Text)
    status = Column(String(20), default=TaskStatus.PENDING.value)
    priority = Column(String(20), default=JobPriority.MEDIUM.value)
    
    # Time tracking
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, default=0.0)
    due_date = Column(DateTime, nullable=True)
    
    # AI assistance
    ai_generated = Column(Boolean, default=False)
    ai_model_used = Column(String(100), nullable=True)
    ai_cost_usd = Column(Float, default=0.0)
    
    # Automation
    is_automated = Column(Boolean, default=False)
    automation_script = Column(Text, nullable=True)
    automation_success_rate = Column(Float, default=0.0)
    
    # Metadata
    tags = Column(JSON)
    external_id = Column(String(200), nullable=True)  # Trello card ID, GitHub issue, etc.
    external_url = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="tasks")
    job = relationship("Job", back_populates="tasks")
    ai_interactions = relationship("AIInteraction", back_populates="task", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_task_user_status', 'user_id', 'status'),
        Index('idx_task_job_status', 'job_id', 'status'),
        Index('idx_task_due_date', 'due_date'),
        Index('idx_task_priority', 'priority'),
    )


class AIInteraction(Base):
    """Track all AI interactions for cost and performance monitoring"""
    __tablename__ = "ai_interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), index=True, nullable=True)
    
    # Interaction details
    interaction_type = Column(String(50))  # "task_breakdown", "code_generation", "chat"
    prompt = Column(Text)
    response = Column(Text)
    
    # AI model info
    model_used = Column(String(100))
    tokens_used = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    response_time_ms = Column(Integer, default=0)
    
    # Quality metrics
    user_rating = Column(Integer, nullable=True)  # 1-5 stars
    was_helpful = Column(Boolean, nullable=True)
    
    # Metadata
    context = Column(JSON)  # Additional context data
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="ai_interactions")
    task = relationship("Task", back_populates="ai_interactions")
    
    # Indexes
    __table_args__ = (
        Index('idx_ai_user_date', 'user_id', 'created_at'),
        Index('idx_ai_cost', 'cost_usd'),
        Index('idx_ai_model', 'model_used'),
    )


class WorkSession(Base):
    """Track work sessions for time management and billing"""
    __tablename__ = "work_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), index=True, nullable=True)
    
    # Session details
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, default=0)
    
    # Activity tracking
    activity_type = Column(String(50))  # "coding", "meeting", "research", "automation"
    description = Column(Text)
    productivity_score = Column(Float, default=0.0)  # 0.0-1.0
    
    # Automation tracking
    automated_percentage = Column(Float, default=0.0)  # How much was automated
    ai_assistance_used = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    job = relationship("Job")
    task = relationship("Task")
    
    # Indexes
    __table_args__ = (
        Index('idx_session_user_date', 'user_id', 'start_time'),
        Index('idx_session_job_date', 'job_id', 'start_time'),
    )


class SystemMetrics(Base):
    """System-wide metrics and monitoring"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Metric details
    metric_name = Column(String(100), index=True)
    metric_value = Column(Float)
    metric_unit = Column(String(20))  # "usd", "tokens", "requests", "seconds"
    
    # Context
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True, index=True)
    
    # Metadata
    tags = Column(JSON)
    
    # Timestamps
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_metrics_name_date', 'metric_name', 'recorded_at'),
        Index('idx_metrics_user_date', 'user_id', 'recorded_at'),
    )


# ============================================================================
# DATABASE CONNECTION AND MANAGEMENT
# ============================================================================

class DatabaseManager:
    """Manage database connections and operations"""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self.async_engine = None
        self.async_session_factory = None
        
    def initialize_sync_db(self):
        """Initialize synchronous database connection"""
        database_url = get_database_url()
        
        if database_url.startswith("sqlite"):
            # SQLite configuration
            self.engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                echo=settings.environment == "development"
            )
        else:
            # PostgreSQL configuration for Railway
            self.engine = create_engine(
                database_url,
                echo=settings.environment == "development",
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=300
            )
        
        self.session_factory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False
        )
        
        logger.info(f"Initialized sync database: {settings.database_url}")
    
    def initialize_async_db(self):
        """Initialize asynchronous database connection"""
        # Convert sync URL to async URL
        database_url = get_database_url()
        async_url = database_url
        
        if async_url.startswith("sqlite"):
            async_url = async_url.replace("sqlite://", "sqlite+aiosqlite://")
            # SQLite async engine
            self.async_engine = create_async_engine(
                async_url,
                echo=settings.environment == "development"
            )
        elif async_url.startswith("postgresql"):
            async_url = async_url.replace("postgresql://", "postgresql+asyncpg://")
            # PostgreSQL async engine for Railway
            self.async_engine = create_async_engine(
                async_url,
                echo=settings.environment == "development",
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=300
            )
        
        self.async_session_factory = async_sessionmaker(
            bind=self.async_engine,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False
        )
        
        logger.info(f"Initialized async database: {async_url}")
    
    def create_tables(self):
        """Create all database tables"""
        if not self.engine:
            self.initialize_sync_db()
        
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")
    
    def get_session(self) -> Session:
        """Get synchronous database session"""
        if not self.session_factory:
            self.initialize_sync_db()
        return self.session_factory()
    
    def get_async_session(self) -> AsyncSession:
        """Get asynchronous database session"""
        if not self.async_session_factory:
            self.initialize_async_db()
        return self.async_session_factory()
    
    async def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            if not self.async_engine:
                self.initialize_async_db()
            
            async with self.async_session_factory() as session:
                result = await session.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager()


# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

async def get_or_create_user(slack_user_id: str, username: str, email: str = None) -> User:
    """Get existing user or create new one"""
    async with db_manager.get_async_session() as session:
        # Try to find existing user
        result = await session.execute(
            text("SELECT * FROM users WHERE slack_user_id = :slack_user_id"),
            {"slack_user_id": slack_user_id}
        )
        user_data = result.fetchone()
        
        if user_data:
            # Update last active
            await session.execute(
                text("UPDATE users SET last_active = :now WHERE id = :user_id"),
                {"now": datetime.utcnow(), "user_id": user_data[0]}
            )
            await session.commit()
            
            # Convert to User object
            user = User(
                id=user_data[0],
                slack_user_id=user_data[1],
                username=user_data[2],
                email=user_data[3],
                full_name=user_data[4],
                max_concurrent_jobs=user_data[5],
                monthly_budget_usd=user_data[6],
                created_at=user_data[7],
                updated_at=user_data[8],
                last_active=user_data[9]
            )
            return user
        else:
            # Create new user
            new_user = User(
                slack_user_id=slack_user_id,
                username=username,
                email=email or f"{username}@example.com",
                full_name=username
            )
            
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            
            logger.info(f"Created new user: {username} ({slack_user_id})")
            return new_user


async def create_task(
    user_id: int,
    title: str,
    description: str = "",
    job_id: int = None,
    priority: str = "medium",
    due_date: datetime = None
) -> Task:
    """Create a new task"""
    async with db_manager.get_async_session() as session:
        task = Task(
            user_id=user_id,
            job_id=job_id,
            title=title,
            description=description,
            priority=priority,
            due_date=due_date
        )
        
        session.add(task)
        await session.commit()
        await session.refresh(task)
        
        logger.info(f"Created task: {title} (ID: {task.id})")
        return task


async def log_ai_interaction(
    user_id: int,
    interaction_type: str,
    prompt: str,
    response: str,
    model_used: str,
    tokens_used: int,
    cost_usd: float,
    response_time_ms: int,
    task_id: int = None
) -> AIInteraction:
    """Log an AI interaction for tracking"""
    async with db_manager.get_async_session() as session:
        interaction = AIInteraction(
            user_id=user_id,
            task_id=task_id,
            interaction_type=interaction_type,
            prompt=prompt,
            response=response,
            model_used=model_used,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            response_time_ms=response_time_ms
        )
        
        session.add(interaction)
        await session.commit()
        await session.refresh(interaction)
        
        return interaction


async def get_user_daily_ai_cost(user_id: int, date: datetime = None) -> float:
    """Get user's AI cost for a specific day"""
    if date is None:
        date = datetime.utcnow().date()
    
    start_date = datetime.combine(date, datetime.min.time())
    end_date = start_date + timedelta(days=1)
    
    async with db_manager.get_async_session() as session:
        result = await session.execute(
            text("""
                SELECT COALESCE(SUM(cost_usd), 0) 
                FROM ai_interactions 
                WHERE user_id = :user_id 
                AND created_at >= :start_date 
                AND created_at < :end_date
            """),
            {
                "user_id": user_id,
                "start_date": start_date,
                "end_date": end_date
            }
        )
        
        return result.scalar() or 0.0


async def get_active_tasks(user_id: int, limit: int = 10) -> List[Task]:
    """Get active tasks for a user"""
    async with db_manager.get_async_session() as session:
        result = await session.execute(
            text("""
                SELECT * FROM tasks 
                WHERE user_id = :user_id 
                AND status IN ('pending', 'in_progress')
                ORDER BY priority DESC, created_at ASC
                LIMIT :limit
            """),
            {"user_id": user_id, "limit": limit}
        )
        
        tasks = []
        for row in result.fetchall():
            task = Task(
                id=row[0],
                user_id=row[1],
                job_id=row[2],
                title=row[3],
                description=row[4],
                status=row[5],
                priority=row[6],
                estimated_hours=row[7],
                actual_hours=row[8],
                due_date=row[9],
                ai_generated=row[10],
                ai_model_used=row[11],
                ai_cost_usd=row[12],
                is_automated=row[13],
                automation_script=row[14],
                automation_success_rate=row[15],
                tags=row[16],
                external_id=row[17],
                external_url=row[18],
                created_at=row[19],
                updated_at=row[20],
                started_at=row[21],
                completed_at=row[22]
            )
            tasks.append(task)
        
        return tasks


# Initialize database on import
def init_database():
    """Initialize database connection and create tables"""
    try:
        db_manager.initialize_sync_db()
        db_manager.initialize_async_db()
        db_manager.create_tables()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


__all__ = [
    "Base",
    "User",
    "Job", 
    "Task",
    "AIInteraction",
    "WorkSession",
    "SystemMetrics",
    "TaskStatus",
    "JobPriority",
    "DatabaseManager",
    "db_manager",
    "get_or_create_user",
    "create_task",
    "log_ai_interaction",
    "get_user_daily_ai_cost",
    "get_active_tasks",
    "init_database"
] 