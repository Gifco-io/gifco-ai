"""FastAPI application for Restaurant Recommender AI."""
import logging
import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from typing import Optional

from .models.requests import RestaurantQueryRequest
from .models.responses import (
    RestaurantQueryResponse, HealthResponse, ErrorResponse
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
    """Unified endpoint for restaurant queries and conversations.
    
    This endpoint handles all types of interactions including:
    - Restaurant search queries: "Best butter chicken spot in new delhi"
    - General conversations: "I'm looking for a good restaurant for dinner"
    - Collection creation: "create a collection" (requires authorization)
    - Follow-up questions with conversation memory via thread_id
    
    Args:
        request: Restaurant query request with query, optional location, and optional thread_id
        authorization: Optional Authorization header (e.g., "Bearer token")
        
    Returns:
        Restaurant query response with results, AI message, and conversation thread_id
        
    Raises:
        HTTPException: If the service is not available
    """
    if not restaurant_service:
        raise HTTPException(
            status_code=503,
            detail="Restaurant service not available"
        )
    
    try:
        logger.info(f"Processing unified query: '{request.query}' with thread_id: {request.thread_id}")
        
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
                thread_id=request.thread_id,
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
