"""Middleware for the FastAPI application."""
import time
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging API requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details.
        
        Args:
            request: The incoming request
            call_next: The next middleware/endpoint
            
        Returns:
            Response from the endpoint
        """
        start_time = time.time()
        
        # Log request details (without body to avoid stream consumption issues)
        logger.info(f"Request: {request.method} {request.url}")
        
        # Log query parameters if present
        if request.query_params:
            logger.info(f"Query params: {dict(request.query_params)}")
        
        # Log headers (excluding sensitive ones)
        safe_headers = {k: v for k, v in request.headers.items() 
                      if k.lower() not in ['authorization', 'cookie', 'x-api-key']}
        if safe_headers:
            logger.info(f"Headers: {safe_headers}")
        
        # Note: Body logging is disabled to prevent stream consumption issues
        # The request body can only be read once, and reading it here would
        # prevent the endpoint from accessing it
        
        # Process request
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Response: {response.status_code} for {request.method} {request.url} "
            f"in {process_time:.3f}s"
        )
        
        return response


def setup_cors(app):
    """Setup CORS middleware for the FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify allowed origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )


def setup_middleware(app):
    """Setup all middleware for the FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    # Setup CORS
    setup_cors(app)
    
    # Add logging middleware
    app.add_middleware(LoggingMiddleware) 