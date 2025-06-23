from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class RestaurantInfo(BaseModel):
    """Model for restaurant information."""
    
    name: str = Field(..., description="Restaurant name")
    cuisine: Optional[str] = Field(None, description="Cuisine type")
    location: Optional[str] = Field(None, description="Restaurant location")
    rating: Optional[float] = Field(None, description="Restaurant rating")
    price_range: Optional[str] = Field(None, description="Price range (e.g., '$', '$$', '$$$')")
    description: Optional[str] = Field(None, description="Restaurant description")
    address: Optional[str] = Field(None, description="Full address")
    phone: Optional[str] = Field(None, description="Phone number")


class RestaurantQueryResponse(BaseModel):
    """Unified response model for all restaurant queries and conversations."""
    
    success: bool = Field(..., description="Whether the query was successful")
    message: str = Field(..., description="AI-generated response message")
    query: str = Field(..., description="The original query")
    thread_id: Optional[str] = Field(None, description="Thread ID for conversation continuity")
    restaurants: Optional[List[RestaurantInfo]] = Field(
        None, 
        description="List of restaurants (if applicable)"
    )
    response_count: Optional[int] = Field(None, description="Number of restaurants found in the response")
    command_type: Optional[str] = Field(None, description="Type of command detected")
    error: Optional[str] = Field(None, description="Error message if any")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class HealthResponse(BaseModel):
    """Response model for health check."""
    
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Health check timestamp")
    version: str = Field(default="1.0.0", description="API version")


class ErrorResponse(BaseModel):
    """Response model for errors."""
    
    success: bool = Field(False, description="Always false for errors")
    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp") 