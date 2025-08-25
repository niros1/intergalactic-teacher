"""Analytics endpoints for parent dashboard."""

import logging
from datetime import datetime, timedelta
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.schemas.analytics import (
    ChildAnalytics,
    ParentDashboard,
    ReadingProgressReport,
    EngagementMetrics,
    LearningOutcomes
)
from app.services.analytics_service import AnalyticsService
from app.services.child_service import ChildService
from app.utils.redis_client import redis_client

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/dashboard", response_model=ParentDashboard)
async def get_parent_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get comprehensive parent dashboard data."""
    try:
        analytics_service = AnalyticsService(db)
        
        # Check cache first
        cache_key = f"parent_dashboard:{current_user.id}"
        cached_dashboard = await redis_client.get(cache_key)
        if cached_dashboard:
            logger.info(f"Returning cached parent dashboard for user: {current_user.id}")
            return cached_dashboard
        
        # Generate dashboard data
        dashboard_data = analytics_service.get_parent_dashboard(current_user.id)
        
        if not dashboard_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate dashboard data"
            )
        
        # Cache for 10 minutes
        await redis_client.set(cache_key, dashboard_data, expire=600)
        
        logger.info(f"Generated parent dashboard for user: {current_user.id}")
        return dashboard_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating parent dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dashboard data"
        )


@router.get("/child/{child_id}", response_model=ChildAnalytics)
async def get_child_analytics(
    child_id: int,
    days: int = Query(30, description="Number of days to include in analytics"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get detailed analytics for a specific child."""
    try:
        analytics_service = AnalyticsService(db)
        child_service = ChildService(db)
        
        # Check access
        if not child_service.check_child_access(child_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this child profile"
            )
        
        # Check cache
        cache_key = f"child_analytics:{child_id}:{days}"
        cached_analytics = await redis_client.get(cache_key)
        if cached_analytics:
            logger.info(f"Returning cached analytics for child: {child_id}")
            return cached_analytics
        
        # Generate analytics
        analytics_data = analytics_service.get_child_analytics(child_id, days)
        
        if not analytics_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child not found or no data available"
            )
        
        # Cache for 15 minutes
        await redis_client.set(cache_key, analytics_data, expire=900)
        
        logger.info(f"Generated analytics for child: {child_id}")
        return analytics_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting child analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get child analytics"
        )


@router.get("/child/{child_id}/progress", response_model=ReadingProgressReport)
async def get_reading_progress(
    child_id: int,
    period: str = Query("month", description="Time period: week, month, quarter, year"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get reading progress report for a child."""
    try:
        analytics_service = AnalyticsService(db)
        child_service = ChildService(db)
        
        # Check access
        if not child_service.check_child_access(child_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this child profile"
            )
        
        # Validate period
        if period not in ["week", "month", "quarter", "year"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid period. Must be one of: week, month, quarter, year"
            )
        
        # Generate progress report
        progress_report = analytics_service.get_reading_progress_report(child_id, period)
        
        if not progress_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child not found or no data available"
            )
        
        logger.info(f"Generated progress report for child: {child_id}, period: {period}")
        return progress_report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting reading progress: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get reading progress"
        )


@router.get("/child/{child_id}/engagement", response_model=EngagementMetrics)
async def get_engagement_metrics(
    child_id: int,
    days: int = Query(30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get engagement metrics for a child."""
    try:
        analytics_service = AnalyticsService(db)
        child_service = ChildService(db)
        
        # Check access
        if not child_service.check_child_access(child_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this child profile"
            )
        
        # Generate engagement metrics
        engagement_data = analytics_service.get_engagement_metrics(child_id, days)
        
        if not engagement_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child not found or no data available"
            )
        
        logger.info(f"Generated engagement metrics for child: {child_id}")
        return engagement_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting engagement metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get engagement metrics"
        )


@router.get("/child/{child_id}/learning-outcomes", response_model=LearningOutcomes)
async def get_learning_outcomes(
    child_id: int,
    period: str = Query("month", description="Time period for analysis"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get learning outcomes analysis for a child."""
    try:
        analytics_service = AnalyticsService(db)
        child_service = ChildService(db)
        
        # Check access
        if not child_service.check_child_access(child_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this child profile"
            )
        
        # Generate learning outcomes
        learning_data = analytics_service.get_learning_outcomes(child_id, period)
        
        if not learning_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child not found or no data available"
            )
        
        logger.info(f"Generated learning outcomes for child: {child_id}")
        return learning_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting learning outcomes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get learning outcomes"
        )


@router.post("/child/{child_id}/refresh-cache")
async def refresh_analytics_cache(
    child_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Refresh cached analytics data for a child."""
    try:
        child_service = ChildService(db)
        
        # Check access
        if not child_service.check_child_access(child_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this child profile"
            )
        
        # Clear all analytics cache for this child
        cache_keys = [
            f"child_analytics:{child_id}:*",
            f"child_dashboard:{child_id}",
            f"parent_dashboard:{current_user.id}"
        ]
        
        for cache_key in cache_keys:
            if "*" in cache_key:
                # For wildcard patterns, we'd need to implement a pattern delete
                # For now, clear common variations
                for days in [7, 30, 90]:
                    await redis_client.delete(f"child_analytics:{child_id}:{days}")
            else:
                await redis_client.delete(cache_key)
        
        logger.info(f"Refreshed analytics cache for child: {child_id}")
        return {"message": "Analytics cache refreshed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing analytics cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh analytics cache"
        )