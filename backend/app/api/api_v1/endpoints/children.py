"""Children management endpoints."""

import logging
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.schemas.child import (
    ChildCreate,
    ChildResponse,
    ChildUpdate,
    ChildWithProgress,
    ChildDashboard,
    ReadingLevelAssessment,
    ReadingLevelResult
)
from app.services.child_service import ChildService
from app.utils.redis_client import redis_client

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[ChildResponse])
async def get_children(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get all children for the current user."""
    try:
        child_service = ChildService(db)
        children = child_service.get_children_by_parent(current_user.id)
        
        logger.info(f"Retrieved {len(children)} children for user: {current_user.id}")
        return children
        
    except Exception as e:
        logger.error(f"Error getting children for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve children"
        )


@router.post("/", response_model=ChildResponse, status_code=status.HTTP_201_CREATED)
async def create_child(
    child_data: ChildCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Create a new child profile."""
    try:
        child_service = ChildService(db)
        
        # Check if user already has maximum children (let's say 5)
        existing_children = child_service.get_children_by_parent(current_user.id)
        if len(existing_children) >= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum number of children (5) reached"
            )
        
        child = child_service.create_child(current_user.id, child_data)
        
        logger.info(f"Created child profile: {child.name} for user: {current_user.id}")
        return child
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating child profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create child profile"
        )


@router.get("/{child_id}", response_model=ChildWithProgress)
async def get_child(
    child_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get a specific child profile with progress data."""
    try:
        child_service = ChildService(db)
        
        # Check if user has access to this child
        if not child_service.check_child_access(child_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this child profile"
            )
        
        child = child_service.get_child_by_id(child_id)
        if not child:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child not found"
            )
        
        logger.info(f"Retrieved child profile: {child_id} for user: {current_user.id}")
        return child
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting child {child_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve child profile"
        )


@router.put("/{child_id}", response_model=ChildResponse)
async def update_child(
    child_id: int,
    child_update: ChildUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update a child profile."""
    try:
        child_service = ChildService(db)
        
        # Check access
        if not child_service.check_child_access(child_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this child profile"
            )
        
        child = child_service.update_child(child_id, child_update)
        if not child:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child not found"
            )
        
        # Invalidate any cached data for this child
        await redis_client.delete(f"child_dashboard:{child_id}")
        
        logger.info(f"Updated child profile: {child_id} for user: {current_user.id}")
        return child
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating child {child_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update child profile"
        )


@router.delete("/{child_id}")
async def delete_child(
    child_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Delete a child profile."""
    try:
        child_service = ChildService(db)
        
        # Check access
        if not child_service.check_child_access(child_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this child profile"
            )
        
        success = child_service.delete_child(child_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child not found"
            )
        
        # Clear cached data
        await redis_client.delete(f"child_dashboard:{child_id}")
        
        logger.info(f"Deleted child profile: {child_id} for user: {current_user.id}")
        return {"message": "Child profile deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting child {child_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete child profile"
        )


@router.get("/{child_id}/dashboard", response_model=ChildDashboard)
async def get_child_dashboard(
    child_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get dashboard data for a child."""
    try:
        child_service = ChildService(db)
        
        # Check access
        if not child_service.check_child_access(child_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this child profile"
            )
        
        # Check cache first
        cached_dashboard = await redis_client.get(f"child_dashboard:{child_id}")
        if cached_dashboard:
            logger.info(f"Returning cached dashboard for child: {child_id}")
            return cached_dashboard
        
        dashboard_data = child_service.get_child_dashboard_data(child_id)
        if not dashboard_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child not found"
            )
        
        # Cache the dashboard data for 5 minutes
        await redis_client.set(
            f"child_dashboard:{child_id}",
            dashboard_data,
            expire=300
        )
        
        logger.info(f"Retrieved dashboard for child: {child_id}")
        return dashboard_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dashboard for child {child_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve child dashboard"
        )


@router.post("/{child_id}/reading-assessment", response_model=ReadingLevelResult)
async def conduct_reading_assessment(
    child_id: int,
    assessment: ReadingLevelAssessment,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Conduct reading level assessment for a child."""
    try:
        child_service = ChildService(db)
        
        # Check access
        if not child_service.check_child_access(child_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this child profile"
            )
        
        # Calculate assessment results
        total_questions = len(assessment.questions)
        correct_answers = 0
        
        for i, answer in enumerate(assessment.answers):
            if i < len(assessment.questions):
                question = assessment.questions[i]
                correct_answer = question.get("correct_answer", "")
                if answer.lower().strip() == correct_answer.lower().strip():
                    correct_answers += 1
        
        score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        # Update child's reading level based on assessment
        assessment_results = {
            "score": correct_answers,
            "total_questions": total_questions,
            "percentage": score
        }
        
        child = child_service.conduct_reading_assessment(child_id, assessment_results)
        if not child:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child not found"
            )
        
        # Generate recommendations based on results
        recommendations = []
        if score < 50:
            recommendations.extend([
                "Focus on basic reading comprehension exercises",
                "Practice reading aloud daily",
                "Start with simpler story themes"
            ])
        elif score < 70:
            recommendations.extend([
                "Continue with current difficulty level",
                "Introduce slightly more complex vocabulary",
                "Encourage independent reading"
            ])
        else:
            recommendations.extend([
                "Ready for more challenging content",
                "Explore advanced story themes",
                "Consider introducing chapter books"
            ])
        
        result = ReadingLevelResult(
            reading_level=child.reading_level,
            score=int(score),
            recommendations=recommendations
        )
        
        # Clear cached dashboard
        await redis_client.delete(f"child_dashboard:{child_id}")
        
        logger.info(f"Conducted reading assessment for child: {child_id}, score: {score}%")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error conducting reading assessment for child {child_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to conduct reading assessment"
        )