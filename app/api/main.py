"""FastAPI application for Restaurant Recommender AI."""
import logging
import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from typing import Optional

from .models.requests import RestaurantQueryRequest, ChatRequest
from .models.responses import (
    RestaurantQueryResponse, ChatResponse, HealthResponse, ErrorResponse
)
from .services.restaurant_service import RestaurantService
from .core.middleware import setup_middleware

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global service instance
restaurant_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    global restaurant_service
    
    # Startup
    logger.info("Starting Restaurant Recommender API...")
    restaurant_service = RestaurantService()
    logger.info("Restaurant Recommender API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Restaurant Recommender API...")


# Create FastAPI app
app = FastAPI(
    title="Restaurant Recommender API",
    description="AI-powered restaurant recommendation service that processes natural language queries",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup middleware
setup_middleware(app)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors.
    
    Args:
        request: The request that caused the error
        exc: The exception that was raised
        
    Returns:
        JSON error response
    """
    logger.error(f"Unhandled error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            details={"message": str(exc)}
        ).model_dump()
    )


@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information.
    
    Returns:
        Basic API information
    """
    return {
        "message": "Restaurant Recommender API",
        "version": "1.0.0",
        "description": "AI-powered restaurant recommendation service",
        "endpoints": {
            "health": "/health",
            "query": "/query",
            "chat": "/chat",
            "docs": "/docs"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint.
    
    Returns:
        Health status of the service
    """
    return HealthResponse(status="healthy")


@app.post("/query", response_model=RestaurantQueryResponse)
async def query_restaurants(
    request: RestaurantQueryRequest,
    authorization: Optional[str] = Header(None)
):
    """Query restaurants using natural language.
    
    This endpoint processes natural language queries like:
    - "Best butter chicken spot in new delhi"
    - "Find Italian restaurants in Mumbai"
    - "Recommend a good restaurant for dinner"
    
    Args:
        request: Restaurant query request
        authorization: Optional Authorization header (e.g., "Bearer token")
        
    Returns:
        Restaurant query response with results
        
    Raises:
        HTTPException: If the service is not available
    """
    if not restaurant_service:
        raise HTTPException(
            status_code=503,
            detail="Restaurant service not available"
        )
    
    try:
        logger.info(f"Processing restaurant query: '{request.query}'")
        
        # Extract token from Authorization header
        auth_token = None
        if authorization:
            if authorization.startswith("Bearer "):
                auth_token = authorization[7:]  # Remove "Bearer " prefix
            else:
                auth_token = authorization  # Use as-is if no Bearer prefix
        
        # Add timeout to prevent hanging
        import asyncio
        response = await asyncio.wait_for(
            restaurant_service.query(
                query=request.query,
                location=request.location,
                auth_token=auth_token
            ),
            timeout=25.0  # 25 second timeout (less than client timeout)
        )
        
        logger.info(f"Query processed successfully: {response.success}")
        return response
        
    except asyncio.TimeoutError:
        logger.error(f"Query timed out after 25 seconds: '{request.query}'")
        raise HTTPException(
            status_code=408,
            detail="Request timed out. The AI service is taking too long to respond."
        )
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    authorization: Optional[str] = Header(None)
):
    """Chat with the restaurant recommender AI.
    
    This endpoint provides a conversational interface for restaurant queries.
    It can handle various types of messages including:
    - Restaurant search queries
    - General questions about restaurants
    - Help requests
    - Collection creation requests (requires authorization)
    
    Args:
        request: Chat request with message and optional thread ID
        authorization: Optional Authorization header (e.g., "Bearer token")
        
    Returns:
        Chat response with AI-generated reply
        
    Raises:
        HTTPException: If the service is not available
    """
    if not restaurant_service:
        raise HTTPException(
            status_code=503,
            detail="Restaurant service not available"
        )
    
    try:
        logger.info(f"Processing chat message: '{request.message}'")
        
        # Extract token from Authorization header
        auth_token = None
        if authorization:
            if authorization.startswith("Bearer "):
                auth_token = authorization[7:]  # Remove "Bearer " prefix
            else:
                auth_token = authorization  # Use as-is if no Bearer prefix
        
        response = await restaurant_service.handle_chat(
            message=request.message,
            thread_id=request.thread_id,
            auth_token=auth_token
        )
        
        logger.info(f"Chat processed successfully: {response.success}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat: {str(e)}"
        )



if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
