"""Main FastAPI application."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.api.api_v1.api import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.base import engine, Base
from app.models import user, child, story, story_session, user_analytics

# Setup structured logging
setup_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan events."""
    # Startup
    logger.info("Starting up Intergalactic Teacher API", version=settings.APP_VERSION)
    
    try:
        # Initialize database
        
        # Create tables if they don't exist (for development)
        # In production, use Alembic migrations
        if settings.ENVIRONMENT == "development":
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created/verified")
        
        # Initialize Redis connection
        from app.utils.redis_client import redis_client
        await redis_client.ping()
        logger.info("Redis connection established")
        
        # Log startup completion
        logger.info("Application startup complete")
        
        yield
        
    except Exception as e:
        logger.error("Failed to start application", error=str(e))
        raise
    finally:
        # Shutdown
        logger.info("Shutting down application")
        
        # Close Redis connection
        try:
            from app.utils.redis_client import redis_client
            await redis_client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.warning("Error closing Redis connection", error=str(e))


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered interactive reading platform for children",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# Add custom middleware
from app.core.middleware import (
    SecurityHeadersMiddleware,
    RequestValidationMiddleware,
    LoggingMiddleware
)

# Add FastAPI CORS middleware first (handles preflight)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174", "http://localhost:8080"] + [str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "User-Agent", "X-Requested-With", "X-Request-ID"],
)

# Add custom middleware in reverse order (they execute in reverse order of addition)
app.add_middleware(SecurityHeadersMiddleware)
# Remove custom CORS middleware since we use FastAPI's built-in
# app.add_middleware(CORSHeadersMiddleware) 
# Rate limiting disabled for development
# app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestValidationMiddleware)
app.add_middleware(LoggingMiddleware)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.localhost", settings.ENVIRONMENT]
)




@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(
        "Unhandled exception",
        method=request.method,
        url=str(request.url),
        error=str(exc),
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": "An unexpected error occurred" if not settings.DEBUG else str(exc)
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        from app.db.base import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        
        # Check Redis connection
        from app.utils.redis_client import redis_client
        await redis_client.ping()
        
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "database": "connected",
            "redis": "connected"
        }
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Intergalactic Teacher API",
        "version": settings.APP_VERSION,
        "docs": f"{settings.API_V1_STR}/docs",
        "health": "/health"
    }


