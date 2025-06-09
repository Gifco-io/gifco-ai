"""Restaurant recommendation models."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from enum import Enum


class QueryType(str, Enum):
    """Types of restaurant queries."""
    CURRENT = "current"
    TRENDING = "trending"
    POPULAR = "popular"


class Restaurant(BaseModel):
    """Restaurant data model."""
    id: Optional[str] = None
    name: str
    address: Optional[str] = None
    cuisine: Optional[str] = None
    rating: Optional[float] = None
    price_range: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    
    def __str__(self) -> str:
        """String representation of restaurant."""
        parts = [f"🍽️  **{self.name}**"]
        
        if self.cuisine:
            parts.append(f"   Cuisine: {self.cuisine}")
        if self.address:
            parts.append(f"   Address: {self.address}")
        if self.rating:
            parts.append(f"   Rating: ⭐ {self.rating}/5")
        if self.price_range:
            parts.append(f"   Price: {self.price_range}")
        if self.phone:
            parts.append(f"   Phone: {self.phone}")
        if self.description:
            parts.append(f"   Description: {self.description}")
            
        return "\n".join(parts)


class RestaurantQuery(BaseModel):
    """Restaurant query model."""
    question: str
    place: str
    query_type: QueryType = QueryType.CURRENT
    cuisine_filter: Optional[str] = None
    price_filter: Optional[str] = None


class RestaurantResponse(BaseModel):
    """Response model for restaurant queries."""
    success: bool
    restaurants: List[Restaurant] = []
    message: str = ""
    total_count: int = 0
    error: Optional[str] = None
    
    def format_response(self) -> str:
        """Format the response for display."""
        if not self.success:
            return f"❌ Error: {self.error or self.message}"
        
        if not self.restaurants:
            return f"🤔 No restaurants found for your query. Try a different location or cuisine type."
        
        response_parts = [
            f"🎯 Found {len(self.restaurants)} restaurants:",
            "",
        ]
        
        for i, restaurant in enumerate(self.restaurants, 1):
            response_parts.append(f"{i}. {str(restaurant)}")
            response_parts.append("")  # Empty line between restaurants
            
        return "\n".join(response_parts)


class AgentRequest(BaseModel):
    """Agent request model."""
    user_query: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    """Agent response model."""
    success: bool
    message: str
    restaurants: Optional[List[Restaurant]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None 