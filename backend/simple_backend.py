#!/usr/bin/env python3

"""
Simple FastAPI backend for testing authentication integration.
Uses SQLite database and implements proper auth endpoints.
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sqlite3
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
import uvicorn

# Initialize FastAPI app
app = FastAPI(title="Intergalactic Teacher API", version="0.1.0")

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
    allow_headers=["*"],
)

# JWT Configuration
SECRET_KEY = "your-super-secret-key-change-this"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 3000

# Database setup
def init_db():
    """Initialize the SQLite database."""
    conn = sqlite3.connect('auth.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            hashed_password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create children table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS children (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            reading_level TEXT NOT NULL,
            language TEXT NOT NULL,
            interests TEXT, -- JSON string
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Pydantic models
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    createdAt: str
    updatedAt: str

class AuthResponse(BaseModel):
    accessToken: str
    refreshToken: str
    user: UserResponse

class CreateChildRequest(BaseModel):
    name: str
    age: int
    readingLevel: str
    language: str
    interests: list[str]

class Child(BaseModel):
    id: str
    parentId: str
    name: str
    age: int
    readingLevel: str
    language: str
    interests: list[str]
    createdAt: str
    updatedAt: str

# Helper functions
def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_from_db(email: str):
    """Get user from database by email."""
    conn = sqlite3.connect('auth.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, name, hashed_password, created_at, updated_at FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def create_user_in_db(email: str, name: str, hashed_password: str):
    """Create a new user in the database."""
    conn = sqlite3.connect('auth.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (email, name, hashed_password) VALUES (?, ?, ?)",
        (email, name, hashed_password)
    )
    user_id = cursor.lastrowid
    conn.commit()
    
    # Get the created user
    cursor.execute("SELECT id, email, name, created_at, updated_at FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

# Auth endpoints
@app.post("/api/v1/auth/register")
async def register(request: RegisterRequest):
    """Register a new user."""
    # Check if user already exists
    existing_user = get_user_from_db(request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password and create user
    hashed_password = hash_password(request.password)
    user_data = create_user_in_db(request.email, request.name, hashed_password)
    
    # Create tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": request.email}, expires_delta=access_token_expires
    )
    refresh_token = create_access_token(
        data={"sub": request.email}, expires_delta=timedelta(days=30)
    )
    
    user_response = UserResponse(
        id=str(user_data[0]),
        email=user_data[1],
        name=user_data[2],
        createdAt=user_data[3],
        updatedAt=user_data[4]
    )
    
    return {
        "data": AuthResponse(
            accessToken=access_token,
            refreshToken=refresh_token,
            user=user_response
        )
    }

@app.post("/api/v1/auth/login")
async def login(request: LoginRequest):
    """Login a user."""
    user = get_user_from_db(request.email)
    
    if not user or not verify_password(request.password, user[3]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": request.email}, expires_delta=access_token_expires
    )
    refresh_token = create_access_token(
        data={"sub": request.email}, expires_delta=timedelta(days=30)
    )
    
    user_response = UserResponse(
        id=str(user[0]),
        email=user[1],
        name=user[2],
        createdAt=user[4],
        updatedAt=user[5]
    )
    
    return {
        "data": AuthResponse(
            accessToken=access_token,
            refreshToken=refresh_token,
            user=user_response
        )
    }

@app.post("/api/v1/auth/logout")
async def logout():
    """Logout endpoint."""
    return {"message": "Successfully logged out"}

# Children endpoints
@app.post("/api/v1/children")
async def create_child(request: CreateChildRequest):
    """Create a new child profile."""
    # For simplicity, using user_id = 1 (first user)
    conn = sqlite3.connect('auth.db')
    cursor = conn.cursor()
    
    interests_json = ",".join(request.interests)
    cursor.execute(
        """INSERT INTO children (parent_id, name, age, reading_level, language, interests) 
           VALUES (1, ?, ?, ?, ?, ?)""",
        (request.name, request.age, request.readingLevel, request.language, interests_json)
    )
    child_id = cursor.lastrowid
    conn.commit()
    
    # Get the created child
    cursor.execute("""
        SELECT id, parent_id, name, age, reading_level, language, interests, created_at, updated_at 
        FROM children WHERE id = ?
    """, (child_id,))
    child_data = cursor.fetchone()
    conn.close()
    
    child_response = Child(
        id=str(child_data[0]),
        parentId=str(child_data[1]),
        name=child_data[2],
        age=child_data[3],
        readingLevel=child_data[4],
        language=child_data[5],
        interests=child_data[6].split(",") if child_data[6] else [],
        createdAt=child_data[7],
        updatedAt=child_data[8]
    )
    
    return {"data": child_response}

@app.get("/api/v1/children")
async def get_children():
    """Get all children for the user."""
    conn = sqlite3.connect('auth.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, parent_id, name, age, reading_level, language, interests, created_at, updated_at 
        FROM children WHERE parent_id = 1
    """)
    children_data = cursor.fetchall()
    conn.close()
    
    children = []
    for child_data in children_data:
        child = Child(
            id=str(child_data[0]),
            parentId=str(child_data[1]),
            name=child_data[2],
            age=child_data[3],
            readingLevel=child_data[4],
            language=child_data[5],
            interests=child_data[6].split(",") if child_data[6] else [],
            createdAt=child_data[7],
            updatedAt=child_data[8]
        )
        children.append(child)
    
    return {"data": children}

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)