#!/usr/bin/env python3
"""
Jace Berelen POC - Main Run Script
Starts the application with proper initialization sequence
"""

import asyncio
import logging
import sys
import signal
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src import (
    settings, 
    validate_environment, 
    init_database, 
    display_startup_banner,
    setup_logging
)
from src.main import app

logger = logging.getLogger(__name__)


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


async def startup_checks():
    """Perform startup checks and initialization"""
    
    # Display banner
    display_startup_banner()
    
    # Environment validation
    logger.info("Validating environment...")
    is_valid, missing = validate_environment()
    if not is_valid:
        logger.error(f"Environment validation failed!")
        for var in missing:
            logger.error(f"  Missing: {var}")
        logger.info("Please check your .env file or environment variables")
        return False
    
    logger.info("Environment validation passed")
    
    # Database initialization
    logger.info("Initializing database...")
    try:
        init_database()
        logger.info("Database initialization completed")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False
    
    # Additional startup tasks can be added here
    logger.info("All startup checks completed successfully")
    return True


def main():
    """Main entry point"""
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run startup checks
    if not asyncio.run(startup_checks()):
        logger.error("Startup failed, exiting...")
        sys.exit(1)
    
    # Import and run uvicorn
    import uvicorn
    
    logger.info(f"Starting Jace Berelen POC on {settings.host}:{settings.port}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"API Documentation: http://{settings.host}:{settings.port}/docs")
    
    try:
        uvicorn.run(
            "src.main:app",
            host=settings.host,
            port=settings.port,
            reload=settings.environment == "development",
            log_level=settings.log_level.lower(),
            access_log=True,
            loop="asyncio"
        )
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"Application crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 