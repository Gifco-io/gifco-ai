"""Restaurant tools for the agent."""
import os
import json
import logging
import aiohttp
import asyncio
from typing import List, Dict, Any
from langchain.tools import Tool, StructuredTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RestaurantSearchInput(BaseModel):
    """Input schema for restaurant search tool."""
    query: str = Field(description="The search query for restaurants")
    place: str = Field(default="New Delhi", description="The location to search in")
    query_type: str = Field(default="current", description="Type of query (current, trending, popular)")


class RestaurantAPITool:
    """Tool for making restaurant API calls."""
    
    def __init__(self, server_url: str = None):
        """Initialize the restaurant API tool.
        
        Args:
            server_url: Base URL for the restaurant API server
        """
        self.server_url = server_url or os.getenv("RESTAURANT_SERVER_URL", "http://localhost:8000")
    
    def _format_place_name(self, place: str) -> str:
        """Format place name for API consistency.
        
        Args:
            place: Raw place name from user input
            
        Returns:
            Formatted place name
        """
        if not place:
            return "New Delhi"  # Default location
            
        place_lower = place.lower().strip()
        
        # Handle common place name variations
        place_mappings = {
            "delhi": "New Delhi",
            "new delhi": "New Delhi",
            "mumbai": "Mumbai",
            "bombay": "Mumbai",
            "bangalore": "Bangalore",
            "bengaluru": "Bangalore",
            "kolkata": "Kolkata",
            "calcutta": "Kolkata",
            "chennai": "Chennai",
            "madras": "Chennai",
            "hyderabad": "Hyderabad",
            "pune": "Pune",
            "ahmedabad": "Ahmedabad",
            "jaipur": "Jaipur",
            "lucknow": "Lucknow",
            "kanpur": "Kanpur",
            "nagpur": "Nagpur",
            "visakhapatnam": "Visakhapatnam",
            "indore": "Indore",
            "thane": "Thane",
            "bhopal": "Bhopal",
            "patna": "Patna",
            "vadodara": "Vadodara",
            "ghaziabad": "Ghaziabad",
            "ludhiana": "Ludhiana",
            "agra": "Agra",
            "nashik": "Nashik"
        }
        
        return place_mappings.get(place_lower, place.title())

    async def _call_restaurant_api(self, query: str, place: str, query_type: str = "current") -> Dict[str, Any]:
        """Make API call to restaurant service.
        
        Args:
            query: The search query
            place: The location to search in
            query_type: Type of query (current, trending, popular)
            
        Returns:
            API response as dictionary
        """
        try:
            # Format place name for API (e.g., "delhi" -> "New Delhi")
            formatted_place = self._format_place_name(place)
            
            # Construct API URL
            logger.info(self.server_url)
            api_url = f"{self.server_url}/api/questions"
            params = {
                "type": query_type,
                "place": formatted_place,
            }
            
            logger.info(f"Making API call to: {api_url} with params: {params}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"API response received: {data}")
                        return data
                    else:
                        error_msg = f"API call failed with status {response.status}"
                        logger.error(error_msg)
                        return {"error": error_msg, "status": response.status}
                        
        except Exception as e:
            error_msg = f"Error calling restaurant API: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

    def search_restaurants(self, query: str, place: str = "New Delhi", query_type: str = "current") -> str:
        """Search for restaurants using the restaurant API.
        
        Args:
            query: The search query for restaurants
            place: The location to search in
            query_type: Type of query (current, trending, popular)
            
        Returns:
            JSON string with restaurant search results
        """
        try:
            # Check if there's already an event loop running
            try:
                # If we're in an async context, get the current loop
                loop = asyncio.get_running_loop()
                # Create a new thread to run the async function
                import concurrent.futures
                import threading
                
                def run_in_thread():
                    # Create a new event loop in this thread
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        result = new_loop.run_until_complete(
                            self._call_restaurant_api(query, place, query_type)
                        )
                        return result
                    finally:
                        new_loop.close()
                
                # Run in a separate thread
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_thread)
                    result = future.result(timeout=30)  # 30 second timeout
                    
            except RuntimeError:
                # No event loop running, we can create one safely
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        self._call_restaurant_api(query, place, query_type)
                    )
                finally:
                    loop.close()
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            error_result = {"error": f"Failed to search restaurants: {str(e)}"}
            return json.dumps(error_result, indent=2)


def get_restaurant_tools(server_url: str = None) -> List[Tool]:
    """Get restaurant-related tools for the agent.
    
    Args:
        server_url: Base URL for the restaurant API server
    
    Returns:
        List of LangChain tools for restaurant operations.
    """
    api_tool = RestaurantAPITool(server_url)
    
    return [
        StructuredTool(
            name="search_restaurants",
            description="Search for restaurants based on query, location and type. Use this tool to find restaurants matching specific criteria or get recommendations.",
            func=api_tool.search_restaurants,
            args_schema=RestaurantSearchInput
        ),
        Tool(
            name="get_restaurant_help",
            description="Get help information about restaurant search capabilities",
            func=lambda x: """I can help you find great restaurants! I can:
- Search for restaurants by location and cuisine
- Find popular dining spots  
- Recommend places based on your preferences
- Provide restaurant details and reviews

Just tell me what you're looking for and where!"""
        )
    ] 