"""Request models for the Restaurant API."""
from pydantic import BaseModel, Field
from typing import Optional


class RestaurantQueryRequest(BaseModel):
    """Request model for restaurant queries."""
    
    query: str = Field(
        ..., 
        description="The restaurant query (e.g., 'Best butter chicken spot in new delhi')",
        example="Best butter chicken spot in new delhi"
    )
    location: Optional[str] = Field(
        None,
        description="Optional location override (if not specified in query)",
        example="New Delhi"
    )


class ChatRequest(BaseModel):
    """Request model for general chat queries."""
    
    message: str = Field(
        ...,
        description="The user's message or question",
        example="I'm looking for a good restaurant for dinner"
    )
    thread_id: Optional[str] = Field(
        None,
        description="Optional thread ID for conversation continuity"
    ) 