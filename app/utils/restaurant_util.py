"""Restaurant utility functions for API calls and data processing."""
import os
import json
import logging
import aiohttp
import asyncio
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import concurrent.futures
from dotenv import load_dotenv
from ..config.config import OpenAIConfig
logger = logging.getLogger(__name__)


class RestaurantAPIClient:
    """Client for making restaurant API calls."""
    
    def __init__(self, server_url: str = None):
        """Initialize the restaurant API client.
        
        Args:
            server_url: Base URL for the restaurant API server
        """
        load_dotenv()
        self.server_url = server_url or os.getenv("RESTAURANT_SERVER_URL", "http://localhost:8000")
        
        # Initialize LLM for tag extraction
        self.llm = ChatOpenAI(
            model_name=OpenAIConfig.MODEL_NAME,
            temperature=0.0,
            api_key=OpenAIConfig.API_KEY,
            base_url=OpenAIConfig.BASE_URL,
            request_timeout=30,
            max_retries=1,
            streaming=False
        )

    def _run_async_in_sync(self, async_func, *args, timeout: int = 30, **kwargs):
        """Utility to run async function in sync context.
        
        Args:
            async_func: The async function to run
            *args: Positional arguments for the function
            timeout: Timeout in seconds
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the async function
        """
        try:
            # Check if there's already an event loop running
            try:
                # If we're in an async context, get the current loop
                loop = asyncio.get_running_loop()
                # Create a new thread to run the async function
                
                def run_in_thread():
                    # Create a new event loop in this thread
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        result = new_loop.run_until_complete(async_func(*args, **kwargs))
                        return result
                    finally:
                        new_loop.close()
                
                # Run in a separate thread
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_thread)
                    result = future.result(timeout=timeout)
                    return result
                    
            except RuntimeError:
                # No event loop running, we can create one safely
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(async_func(*args, **kwargs))
                    return result
                finally:
                    loop.close()
        except Exception as e:
            raise e

    def extract_tags_from_query(self, query: str) -> Dict[str, Any]:
        """Extract relevant tags and place from user query using LLM.
        
        Args:
            query: User's search query
            
        Returns:
            Dictionary with 'tags' and 'place' keys
        """
        system_prompt = """You are a tag and location extraction system for restaurant search. Extract relevant tags and location from the user query.

Extract tags for:
1. Food items, dishes, cuisines (e.g., "butter chicken", "pizza", "Italian", "Indian")
2. Restaurant types or categories (e.g., "family restaurant", "fast food", "fine dining", "cafe")
3. Special preferences (e.g., "vegetarian", "halal", "budget-friendly")

Extract place/location separately:
1. Cities, areas, locations (e.g., "New Delhi" -> "delhi", "Mumbai" -> "mumbai", "downtown Mumbai" -> "mumbai")
2. Normalize location names to lowercase and remove common prefixes like "New"

Important rules:
- Extract specific dish names as single tags (e.g., "butter chicken" not ["butter", "chicken"])
- Keep restaurant types as complete phrases (e.g., "family restaurant", "fine dining")
- Extract location separately from tags
- Normalize location names (e.g., "New Delhi" -> "delhi")
- Keep tags concise and relevant for restaurant search
- Return maximum 5 most relevant tags
- Return response as JSON with "tags" array and "place" string

Example:
Query: "best butter chicken in New Delhi"
Response: {"tags": ["butter chicken"], "place": "delhi"}

Query: "good family restaurant serving pizza near downtown Mumbai"
Response: {"tags": ["family restaurant", "pizza"], "place": "mumbai"}

Query: "best Italian restaurant in Bangalore"
Response: {"tags": ["Italian"], "place": "bangalore"}"""

        user_message = f"Extract tags and place from this restaurant search query: {query}"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]

        response = self.llm.invoke(messages)
        
        # Parse the response to extract JSON
        response_text = response.content.strip()
        
        try:
            # Extract JSON from the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            json_part = response_text[start_idx:end_idx]
            result = json.loads(json_part)
            
            # Ensure the result has the expected structure
            if not isinstance(result, dict):
                result = {"tags": [], "place": ""}
            
            # Ensure tags is a list and place is a string
            result["tags"] = result.get("tags", []) if isinstance(result.get("tags"), list) else []
            result["place"] = result.get("place", "") if isinstance(result.get("place"), str) else ""
            
            return result
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response text: {response_text}")
            return {"tags": [], "place": ""}

    async def search_restaurants_by_tags(self, tags: List[str], place: str = "") -> Dict[str, Any]:
        """Search for restaurants using the tags endpoint with optional place filter.
        
        Args:
            tags: List of tags to search for (optional - can be empty)
            place: Location/place to search in (optional - can be empty)
            
        Returns:
            API response as dictionary
        """
        try:
            # Construct API URL for the tags endpoint
            api_url = f"{self.server_url}/api/restaurants/search/tags"
            
            # Prepare request body - only include fields that have values
            request_body = {}
            
            if tags and len(tags) > 0:
                request_body["tags"] = tags
                
            if place and place.strip():
                request_body["place"] = place.strip()
            
            # Prepare headers
            headers = {"Content-Type": "application/json"}
            
            logger.info(f"Making GET request to: {api_url} with body: {request_body}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    api_url, 
                    json=request_body if request_body else None, 
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Restaurant search response status: {response.status}")
                        logger.info(f"Restaurant search response data type: {type(data)}")
                        
                        # Log the structure of the response for debugging
                        if isinstance(data, dict):
                            logger.info(f"Response keys: {list(data.keys())}")
                            if 'restaurants' in data:
                                logger.info(f"Found 'restaurants' key with {len(data['restaurants']) if data['restaurants'] else 0} restaurants")
                        
                        logger.info(f"Restaurant search response received: {data}")
                        return data
                    else:
                        error_text = await response.text()
                        error_msg = f"Restaurant search failed with status {response.status}: {error_text}"
                        logger.error(error_msg)
                        return {"error": error_msg, "status": response.status}
                        
        except Exception as e:
            error_msg = f"Error searching restaurants by tags: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

    def search_restaurants_by_tags_sync(self, query: str) -> str:
        """Search for restaurants by tags and place (synchronous wrapper).
        
        Args:
            query: The search query to extract tags and place from and search restaurants
            
        Returns:
            JSON string with restaurant search results
        """
        try:
            # Extract tags and place from the query using LLM
            extraction_result = self.extract_tags_from_query(query)
            tags = extraction_result.get("tags", [])
            place = extraction_result.get("place", "")
            
            logger.info(f"Extracted from query '{query}': tags={tags}, place='{place}'")
            
            # Use the utility function to run async search
            result = self._run_async_in_sync(self.search_restaurants_by_tags, tags, place)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return self._json_error_response(f"Failed to search restaurants by tags: {str(e)}")

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
            # Use the utility function to run async collection creation
            result = self._run_async_in_sync(
                self.create_collection, 
                name, description, is_public, tags, auth_token
            )
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return self._json_error_response(f"Failed to create collection: {str(e)}")

    async def add_restaurant_to_collection(
        self,
        collection_id: str,
        restaurant_id: str,
        auth_token: str = None
    ) -> Dict[str, Any]:
        """Add a restaurant to a collection.
        
        Args:
            collection_id: ID of the collection
            restaurant_id: ID of the restaurant to add
            auth_token: Authorization token for the API call
            
        Returns:
            API response as dictionary
        """
        try:
            # Construct API URL
            api_url = f"{self.server_url}/api/collections/{collection_id}/add/restaurant/{restaurant_id}"
            
            # Prepare headers
            headers = {}
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}" if not auth_token.startswith("Bearer ") else auth_token
            
            logger.info(f"Adding restaurant {restaurant_id} to collection {collection_id}")
            logger.info(f"API URL: {api_url}")
            logger.info(f"Headers: {headers}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, headers=headers) as response:
                    response_text = await response.text()
                    logger.info(f"Add restaurant response status: {response.status}")
                    logger.info(f"Add restaurant response text: {response_text}")
                    
                    if response.status in [200, 201]:
                        try:
                            data = await response.json()
                            logger.info(f"Restaurant added to collection successfully: {data}")
                            return data
                        except Exception as json_error:
                            logger.warning(f"Response not JSON, treating as success: {json_error}")
                            return {"success": True, "message": response_text}
                    else:
                        error_msg = f"Adding restaurant to collection failed with status {response.status}: {response_text}"
                        logger.error(error_msg)
                        return {"error": error_msg, "status": response.status}
                        
        except Exception as e:
            error_msg = f"Error adding restaurant to collection: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

    async def create_collection_with_restaurants(
        self,
        name: str,
        description: str,
        restaurant_ids: List[str],
        is_public: bool = True,
        tags: List[str] = None,
        auth_token: str = None
    ) -> Dict[str, Any]:
        """Create a collection and add restaurants to it.
        
        Args:
            name: Name of the collection
            description: Description of the collection
            restaurant_ids: List of restaurant IDs to add to the collection
            is_public: Whether the collection is public or private
            tags: List of tags for the collection
            auth_token: Authorization token for the API call
            
        Returns:
            API response as dictionary with collection info and restaurant addition results
        """
        try:
            logger.info(f"Creating collection '{name}' with {len(restaurant_ids)} restaurants")
            logger.info(f"Restaurant IDs to add: {restaurant_ids}")
            
            # First create the collection
            collection_result = await self.create_collection(
                name=name,
                description=description,
                is_public=is_public,
                tags=tags,
                auth_token=auth_token
            )
            
            logger.info(f"Collection creation result: {collection_result}")
            
            if "error" in collection_result:
                logger.error(f"Collection creation failed: {collection_result['error']}")
                return collection_result
            
            # Extract collection ID from response - check both direct ID and nested collection.id
            collection_id = (
                collection_result.get("id") or 
                collection_result.get("_id") or
                (collection_result.get("collection", {}).get("_id")) or
                (collection_result.get("collection", {}).get("id"))
            )
            
            logger.info(f"Extracted collection ID: {collection_id}")
            logger.info(f"Collection result keys: {list(collection_result.keys())}")
            
            if not collection_id:
                logger.error(f"Collection created but no ID found in response: {collection_result}")
                return {"error": "Collection created but no ID returned", "collection_result": collection_result}
            
            # Add each restaurant to the collection
            added_restaurants = []
            failed_restaurants = []
            
            logger.info(f"Starting to add {len(restaurant_ids)} restaurants to collection {collection_id}")
            
            for i, restaurant_id in enumerate(restaurant_ids, 1):
                logger.info(f"Adding restaurant {i}/{len(restaurant_ids)}: {restaurant_id}")
                
                add_result = await self.add_restaurant_to_collection(
                    collection_id=collection_id,
                    restaurant_id=restaurant_id,
                    auth_token=auth_token
                )
                
                logger.info(f"Add result for restaurant {restaurant_id}: {add_result}")
                
                if "error" in add_result:
                    failed_restaurants.append({
                        "restaurant_id": restaurant_id,
                        "error": add_result["error"]
                    })
                    logger.warning(f"Failed to add restaurant {restaurant_id}: {add_result['error']}")
                else:
                    added_restaurants.append(restaurant_id)
                    logger.info(f"Successfully added restaurant {restaurant_id}")
            
            # Return comprehensive result
            final_result = {
                "collection": collection_result,
                "collection_id": collection_id,
                "added_restaurants": added_restaurants,
                "failed_restaurants": failed_restaurants,
                "success": len(failed_restaurants) == 0,
                "total_restaurants": len(restaurant_ids),
                "successfully_added": len(added_restaurants)
            }
            
            logger.info(f"Final collection creation result: Successfully added {len(added_restaurants)}/{len(restaurant_ids)} restaurants")
            if failed_restaurants:
                logger.warning(f"Failed restaurants: {failed_restaurants}")
            
            return final_result
            
        except Exception as e:
            error_msg = f"Error creating collection with restaurants: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

    def create_collection_with_restaurants_sync(
        self,
        name: str,
        description: str,
        restaurant_ids: List[str],
        is_public: bool = True,
        tags: List[str] = None,
        auth_token: str = None
    ) -> str:
        """Create a collection with restaurants (synchronous wrapper).
        
        Args:
            name: Name of the collection
            description: Description of the collection
            restaurant_ids: List of restaurant IDs to add to the collection
            is_public: Whether the collection is public or private
            tags: List of tags for the collection
            auth_token: Authorization token for the API call
            
        Returns:
            JSON string with collection creation and restaurant addition results
        """
        try:
            # Use the utility function to run async collection creation with restaurants
            result = self._run_async_in_sync(
                self.create_collection_with_restaurants,
                name, description, restaurant_ids, is_public, tags, auth_token,
                timeout=45  # Longer timeout for multiple operations
            )
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return self._json_error_response(f"Failed to create collection with restaurants: {str(e)}")

    def _json_error_response(self, error_message: str) -> str:
        """Create a consistent JSON error response.
        
        Args:
            error_message: The error message to include
            
        Returns:
            JSON string with error response
        """
        error_result = {"error": error_message}
        return json.dumps(error_result, indent=2)


 