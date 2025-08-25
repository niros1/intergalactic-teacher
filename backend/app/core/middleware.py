"""Custom middleware for security and rate limiting."""

import time
import logging
from typing import Callable

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from app.core.config import settings
from app.utils.redis_client import redis_client

logger = structlog.get_logger()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        
        # Skip rate limiting for health checks and static files
        if request.url.path in ["/health", "/", "/openapi.json"] or request.url.path.startswith("/static"):
            return await call_next(request)
        
        # Skip if rate limiting is disabled
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"
        
        # Different limits for different endpoints
        endpoint_limits = {
            "/api/v1/auth/login": (5, 300),  # 5 requests per 5 minutes
            "/api/v1/auth/register": (3, 3600),  # 3 requests per hour
            "/api/v1/stories/generate": (10, 3600),  # 10 generations per hour
            "default": (settings.RATE_LIMIT_REQUESTS_PER_MINUTE, 60)
        }
        
        # Find matching limit
        limit_key = "default"
        for pattern, _ in endpoint_limits.items():
            if pattern != "default" and request.url.path.startswith(pattern):
                limit_key = pattern
                break
        
        limit, window = endpoint_limits[limit_key]
        
        # Check rate limit
        rate_key = f"rate_limit:{limit_key}:{client_ip}"
        is_allowed, remaining = await redis_client.rate_limit_check(
            rate_key, limit, window
        )
        
        if not is_allowed:
            logger.warning(
                "Rate limit exceeded",
                client_ip=client_ip,
                endpoint=request.url.path,
                limit=limit,
                window=window
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {window} seconds.",
                headers={"Retry-After": str(window)}
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(window)
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers."""
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy for API - relaxed for Swagger UI
        path = request.url.path
        if "/docs" in path or "/redoc" in path or path.startswith("/api/v1/docs"):
            # Relaxed CSP for API documentation
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https:; "
                "font-src 'self' data: https://cdn.jsdelivr.net; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none';"
            )
        else:
            # Strict CSP for API endpoints
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none';"
            )
        response.headers["Content-Security-Policy"] = csp
        
        # HSTS for HTTPS
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validate incoming requests for security issues."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate request security."""
        
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                max_size = settings.MAX_UPLOAD_SIZE
                if size > max_size:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Request too large. Maximum size: {max_size} bytes"
                    )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid content-length header"
                )
        
        # Validate User-Agent (basic bot detection)
        user_agent = request.headers.get("user-agent", "").lower()
        suspicious_agents = ["curl", "wget", "python-requests", "bot", "crawler"]
        
        if any(agent in user_agent for agent in suspicious_agents):
            # Log suspicious activity but don't block (might be legitimate)
            logger.info(
                "Suspicious user agent detected",
                user_agent=user_agent,
                client_ip=request.client.host if request.client else "unknown",
                path=request.url.path
            )
        
        # Check for common attack patterns in URLs
        suspicious_patterns = [
            "../", "..\\", "<script", "javascript:", "data:",
            "union select", "drop table", "insert into",
            "eval(", "system(", "exec("
        ]
        
        url_path = request.url.path.lower()
        query_params = str(request.query_params).lower()
        
        for pattern in suspicious_patterns:
            if pattern in url_path or pattern in query_params:
                logger.warning(
                    "Suspicious request pattern detected",
                    pattern=pattern,
                    path=request.url.path,
                    client_ip=request.client.host if request.client else "unknown"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid request"
                )
        
        return await call_next(request)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Enhanced logging middleware with structured logging."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log requests with detailed information."""
        start_time = time.time()
        
        # Generate request ID for tracing
        request_id = f"{int(time.time() * 1000)}-{hash(request.url.path) % 10000:04d}"
        
        # Log request start
        logger.info(
            "Request started",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            content_length=request.headers.get("content-length"),
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log successful response
            logger.info(
                "Request completed",
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                process_time=round(process_time, 4),
                response_size=response.headers.get("content-length")
            )
            
            # Add request ID and timing headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(round(process_time, 4))
            
            return response
            
        except Exception as e:
            # Log failed request
            process_time = time.time() - start_time
            
            logger.error(
                "Request failed",
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                error=str(e),
                process_time=round(process_time, 4),
                exc_info=True
            )
            
            raise


class CORSHeadersMiddleware(BaseHTTPMiddleware):
    """Enhanced CORS handling with security considerations."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle CORS with security checks."""
        
        # Get origin header
        origin = request.headers.get("origin")
        
        # Process request
        response = await call_next(request)
        
        # Only add CORS headers if origin is allowed
        if origin:
            allowed_origins = [str(origin) for origin in settings.BACKEND_CORS_ORIGINS]
            
            if origin in allowed_origins or settings.ENVIRONMENT == "development":
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
                response.headers["Access-Control-Allow-Headers"] = (
                    "Authorization, Content-Type, Accept, Origin, User-Agent, "
                    "X-Requested-With, X-Request-ID"
                )
                response.headers["Access-Control-Expose-Headers"] = (
                    "X-Request-ID, X-Process-Time, X-RateLimit-Limit, "
                    "X-RateLimit-Remaining, X-RateLimit-Window"
                )
                response.headers["Access-Control-Max-Age"] = "86400"  # 24 hours
            else:
                logger.warning(
                    "CORS request from unauthorized origin",
                    origin=origin,
                    allowed_origins=allowed_origins
                )
        
        return response