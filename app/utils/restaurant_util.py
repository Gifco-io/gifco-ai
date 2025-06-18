"""Restaurant utility functions for API calls and data processing."""
import os
import json
import logging
import aiohttp
import asyncio
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class RestaurantAPIClient:
    """Client for making restaurant API calls."""
    
    def __init__(self, server_url: str = None):
        """Initialize the restaurant API client.
        
        Args:
            server_url: Base URL for the restaurant API server
        """
        self.server_url = server_url or os.getenv("RESTAURANT_SERVER_URL", "http://localhost:8000")
    
    def format_place_name(self, place: str) -> str:
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

    async def call_restaurant_api(self, query: str, place: str, query_type: str = "current") -> Dict[str, Any]:
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
            formatted_place = self.format_place_name(place)
            
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

    def search_restaurants_sync(self, query: str, place: str = "New Delhi", query_type: str = "current") -> str:
        """Search for restaurants using the restaurant API (synchronous wrapper).
        
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
                            self.call_restaurant_api(query, place, query_type)
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
                        self.call_restaurant_api(query, place, query_type)
                    )
                finally:
                    loop.close()
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            error_result = {"error": f"Failed to search restaurants: {str(e)}"}
            return json.dumps(error_result, indent=2)

    async def create_collection(
        self, 
        name: str, 
        description: str, 
        is_public: bool = True, 
        tags: List[str] = None,
        auth_token: str = None
    ) -> Dict[str, Any]:
        """Create a new collection via the collections API.
        
        Args:
            name: Name of the collection
            description: Description of the collection
            is_public: Whether the collection is public or private
            tags: List of tags for the collection
            auth_token: Authorization token for the API call
            
        Returns:
            API response as dictionary
        """
        try:
            # Construct API URL
            api_url = f"{self.server_url}/api/collections"
            
            # Prepare request body
            request_body = {
                "name": name,
                "description": description,
                "isPublic": is_public,
                "tags": tags or []
            }
            
            # Prepare headers
            headers = {
                "Content-Type": "application/json"
            }
            
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}" if not auth_token.startswith("Bearer ") else auth_token
            
            logger.info(f"Making POST request to: {api_url} with body: {request_body}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    api_url, 
                    json=request_body, 
                    headers=headers
                ) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        logger.info(f"Collection created successfully: {data}")
                        return data
                    else:
                        error_text = await response.text()
                        error_msg = f"Collection creation failed with status {response.status}: {error_text}"
                        logger.error(error_msg)
                        return {"error": error_msg, "status": response.status}
                        
        except Exception as e:
            error_msg = f"Error creating collection: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

    def create_collection_sync(
        self, 
        name: str, 
        description: str, 
        is_public: bool = True, 
        tags: List[str] = None,
        auth_token: str = None
    ) -> str:
        """Create a new collection (synchronous wrapper).
        
        Args:
            name: Name of the collection
            description: Description of the collection
            is_public: Whether the collection is public or private
            tags: List of tags for the collection
            auth_token: Authorization token for the API call
            
        Returns:
            JSON string with collection creation result
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
                            self.create_collection(name, description, is_public, tags, auth_token)
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
                        self.create_collection(name, description, is_public, tags, auth_token)
                    )
                finally:
                    loop.close()
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            error_result = {"error": f"Failed to create collection: {str(e)}"}
            return json.dumps(error_result, indent=2)


 