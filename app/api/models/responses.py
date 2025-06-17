"""Response models for the Restaurant API."""
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
    """Response model for restaurant queries."""
    
    success: bool = Field(..., description="Whether the query was successful")
    query: str = Field(..., description="The original query")
    restaurants: Optional[List[RestaurantInfo]] = Field(
        None, 
        description="List of restaurants (if applicable)"
    )
    location: Optional[str] = Field(None, description="Location searched")
    cuisine: Optional[str] = Field(None, description="Cuisine type searched")
    error: Optional[str] = Field(None, description="Error message if any")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class ChatResponse(BaseModel):
    """Response model for chat queries."""
    
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Response message")
    thread_id: str = Field(..., description="Thread ID for conversation continuity")
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