#!/usr/bin/env python3
"""Setup script for Intergalactic Teacher backend."""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import logging
from sqlalchemy import text
from alembic.config import Config
from alembic import command

from app.core.config import settings
from app.db.base import engine, Base
from app.models import *  # Import all models
from app.utils.redis_client import redis_client


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_redis_connection():
    """Check Redis connection."""
    try:
        await redis_client.ping()
        logger.info("✅ Redis connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        return False


def check_database_connection():
    """Check database connection."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            logger.info(f"✅ Database connection successful: {version}")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


def create_tables():
    """Create database tables."""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        return False


def run_migrations():
    """Run Alembic migrations."""
    try:
        logger.info("Running database migrations...")
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        logger.info("✅ Database migrations completed")
        return True
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False


def create_sample_data():
    """Create sample data for development."""
    try:
        from sqlalchemy.orm import sessionmaker
        from app.services.user_service import UserService
        from app.services.child_service import ChildService
        from app.schemas.user import UserCreate
        from app.schemas.child import ChildCreate
        
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        try:
            user_service = UserService(db)
            child_service = ChildService(db)
            
            # Check if sample user exists
            existing_user = user_service.get_user_by_email("demo@intergalactic.com")
            if existing_user:
                logger.info("Sample data already exists")
                return True
            
            logger.info("Creating sample data...")
            
            # Create demo user
            demo_user_data = UserCreate(
                email="demo@intergalactic.com",
                password="Demo123!",
                full_name="Demo Parent"
            )
            demo_user = user_service.create_user(demo_user_data)
            
            # Create demo children
            child1_data = ChildCreate(
                name="Emma",
                age=8,
                language_preference="english",
                reading_level="beginner",
                interests=["animals", "adventure", "friendship"]
            )
            child_service.create_child(demo_user.id, child1_data)
            
            child2_data = ChildCreate(
                name="Alex",
                age=10,
                language_preference="english",
                reading_level="intermediate",
                interests=["science", "fantasy", "mystery"]
            )
            child_service.create_child(demo_user.id, child2_data)
            
            logger.info("✅ Sample data created successfully")
            logger.info("Demo login: demo@intergalactic.com / Demo123!")
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Failed to create sample data: {e}")
        return False


async def setup_development_environment():
    """Set up the complete development environment."""
    logger.info("🚀 Setting up Intergalactic Teacher backend...")
    
    # Check connections
    db_ok = check_database_connection()
    redis_ok = await check_redis_connection()
    
    if not db_ok:
        logger.error("Database connection required. Please start PostgreSQL.")
        return False
    
    if not redis_ok:
        logger.error("Redis connection required. Please start Redis.")
        return False
    
    # Set up database
    if settings.ENVIRONMENT == "development":
        # For development, create tables directly
        tables_ok = create_tables()
        if not tables_ok:
            return False
        
        # Create sample data
        sample_ok = create_sample_data()
        if not sample_ok:
            logger.warning("Sample data creation failed, but continuing...")
    else:
        # For production, use migrations
        migrate_ok = run_migrations()
        if not migrate_ok:
            return False
    
    logger.info("✅ Backend setup completed successfully!")
    logger.info("\nNext steps:")
    logger.info("1. Start the server: uvicorn app.main:app --reload")
    logger.info("2. Visit the docs: http://localhost:8000/api/v1/docs")
    logger.info("3. Use demo account: demo@intergalactic.com / Demo123!")
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(setup_development_environment())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)