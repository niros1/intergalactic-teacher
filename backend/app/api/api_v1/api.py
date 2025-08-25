"""API v1 main router."""

from fastapi import APIRouter

from app.api.api_v1.endpoints import auth, children, stories, analytics, users

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(children.router, prefix="/children", tags=["children"])
api_router.include_router(stories.router, prefix="/stories", tags=["stories"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])