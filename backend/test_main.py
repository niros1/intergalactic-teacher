"""Simplified main FastAPI application for testing."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI app
app = FastAPI(
    title="Intergalactic Teacher API - Test",
    version="0.1.0",
    description="AI-powered interactive reading platform for children - Test Mode",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:5173", 
        "http://localhost:5174", 
        "http://localhost:8080"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "User-Agent", "X-Requested-With"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "environment": "test"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Intergalactic Teacher API - Test Mode",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }

# Basic auth endpoints for testing
@app.post("/api/v1/auth/login")
async def login():
    """Mock login endpoint."""
    return {
        "data": {
            "accessToken": "test-access-token",
            "refreshToken": "test-refresh-token",
            "user": {
                "id": 1,
                "email": "test@example.com",
                "full_name": "Test User"
            }
        }
    }

@app.post("/api/v1/auth/register")
async def register():
    """Mock register endpoint."""
    return {
        "data": {
            "id": 1,
            "email": "test@example.com", 
            "full_name": "Test User",
            "is_active": True
        }
    }

# Mock children endpoints
@app.get("/api/v1/children")
async def get_children():
    """Mock get children endpoint."""
    return {
        "data": [
            {
                "id": 1,
                "name": "Test Child",
                "age": 8,
                "language": "hebrew",
                "reading_level": "beginner"
            }
        ]
    }

@app.post("/api/v1/children")
async def create_child():
    """Mock create child endpoint."""
    return {
        "data": {
            "id": 1,
            "name": "Test Child",
            "age": 8,
            "language": "hebrew",
            "reading_level": "beginner"
        }
    }

# Mock stories endpoints
@app.post("/api/v1/stories/generate")
async def generate_story():
    """Mock story generation endpoint."""
    return {
        "data": {
            "id": 1,
            "title": "The Magic Adventure",
            "content": "Once upon a time...",
            "choices": [
                {"id": 1, "text": "Go to the forest"},
                {"id": 2, "text": "Stay in the village"}
            ]
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)