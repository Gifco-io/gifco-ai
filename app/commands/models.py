"""Command models for restaurant recommendation commands."""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from enum import Enum


class CommandType(str, Enum):
    """Types of restaurant commands."""
    SEARCH = "search"
    RECOMMENDATION = "recommendation"
    INFO = "info"
    COLLECTION = "collection"


class RestaurantCommand(BaseModel):
    """Base class for restaurant commands."""
    command_type: CommandType
    original_request: Optional[str] = None
    

class RestaurantQuery(BaseModel):
    """Restaurant search query model."""
    query: str
    place: Optional[str] = None
    cuisine: Optional[str] = None
    price_range: Optional[str] = None
    dietary_restrictions: Optional[str] = None
    

class SearchCommand(RestaurantCommand):
    """Command for searching restaurants."""
    command_type: CommandType = CommandType.SEARCH
    search_query: RestaurantQuery
    

class RecommendationCommand(RestaurantCommand):
    """Command for getting restaurant recommendations."""
    command_type: CommandType = CommandType.RECOMMENDATION
    recommendation_query: RestaurantQuery
    

class InformationalCommand(RestaurantCommand):
    """Command for informational requests."""
    command_type: CommandType = CommandType.INFO
    topic: str


class CollectionCommand(RestaurantCommand):
    """Command for creating restaurant collections."""
    command_type: CommandType = CommandType.COLLECTION
    name: str
    description: str
    is_public: bool = True
    tags: List[str] = []
    auth_token: str
    restaurant_ids: Optional[List[str]] = None


class CommandParseError(Exception):
    """Exception raised when command parsing fails."""
    pass 