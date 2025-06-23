"""Restaurant tools for the agent."""
import json
import logging
from typing import List, Optional
from langchain.tools import Tool, StructuredTool
from pydantic import BaseModel, Field
from ...utils.restaurant_util import RestaurantAPIClient

logger = logging.getLogger(__name__)


class RestaurantSearchInput(BaseModel):
    """Input schema for restaurant search tool."""
    query: str = Field(description="The search query for restaurants from which tags will be extracted")


class CollectionCreateInput(BaseModel):
    """Input schema for collection creation tool."""
    name: str = Field(description="Name of the collection")
    description: str = Field(description="Description of the collection")
    is_public: bool = Field(default=True, description="Whether the collection is public or private")
    tags: List[str] = Field(default=[], description="List of tags for the collection")
    auth_token: str = Field(description="Authorization token for the API call")


class CollectionWithRestaurantsInput(BaseModel):
    """Input schema for creating a collection with restaurants."""
    name: str = Field(description="Name of the collection")
    description: str = Field(description="Description of the collection")
    restaurant_ids: List[str] = Field(description="List of restaurant IDs to add to the collection")
    is_public: bool = Field(default=True, description="Whether the collection is public or private")
    tags: List[str] = Field(default=[], description="List of tags for the collection")
    auth_token: str = Field(description="Authorization token for the API call")



class RestaurantTool:
    """Tool for making restaurant API calls."""
    
    def __init__(self, server_url: str = None):
        """Initialize the restaurant API tool.
        
        Args:
            server_url: Base URL for the restaurant API server
        """
        self.server_url = server_url


    @staticmethod
    def get_restaurant_tools(server_url: str = None) -> List[Tool]:
        """Get restaurant-related tools for the agent.
        
        Args:
            server_url: Base URL for the restaurant API server
        
        Returns:
            List of LangChain tools for restaurant operations.
        """
        api_tool = RestaurantAPIClient(server_url)
        
        return [
            StructuredTool(
                name="search_restaurants",
                description="Search for restaurants based on extracted tags from user query. Use this tool to find restaurants matching specific criteria or get recommendations. The tool will automatically extract relevant tags from the query such as food items, locations, and preferences.",
                func=api_tool.search_restaurants_by_tags_sync,  
                args_schema=RestaurantSearchInput
            ),
            StructuredTool(
                name="create_collection",
                description="Create a new restaurant collection. Use this tool to create curated lists of restaurants with a name, description, tags, and privacy settings.",
                func=api_tool.create_collection_sync,
                args_schema=CollectionCreateInput
            ),
            StructuredTool(
                name="create_collection_with_restaurants",
                description="Create a new restaurant collection and add specific restaurants to it. Use this tool when you have restaurant IDs and want to create a collection that contains those restaurants.",
                func=api_tool.create_collection_with_restaurants_sync,
                args_schema=CollectionWithRestaurantsInput
            ),

            Tool(
                name="get_restaurant_help",
                description="Get help information about restaurant search capabilities",
                func=lambda x: """I can help you find great restaurants! I can:
    - Search for restaurants by location and cuisine
    - Find popular dining spots  
    - Recommend places based on your preferences
    - Create curated restaurant collections

    Just tell me what you're looking for and where!"""
            )
        ]


def get_restaurant_tools(server_url: str = None) -> List[Tool]:
    """Get restaurant-related tools for the agent.
    
    Args:
        server_url: Base URL for the restaurant API server
    
    Returns:
        List of LangChain tools for restaurant operations.
    """
    return RestaurantTool.get_restaurant_tools(server_url) 