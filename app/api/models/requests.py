"""Request models for the Restaurant API."""
from pydantic import BaseModel, Field
from typing import Optional


class RestaurantQueryRequest(BaseModel):
    """Unified request model for all restaurant queries and conversations."""
    
    query: str = Field(
        ..., 
        description="The restaurant query, conversation message, or command (e.g., 'Best butter chicken spot in new delhi', 'create a collection')",
        example="Best butter chicken spot in new delhi"
    )
    location: Optional[str] = Field(
        None,
        description="Optional location override (if not specified in query)",
        example="New Delhi"
    )
    thread_id: Optional[str] = Field(
        None,
        description="Optional thread ID for conversation continuity and memory"
    ) 