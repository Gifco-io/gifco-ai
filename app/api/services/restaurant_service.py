"""Restaurant service for API endpoints with conversational memory."""
import logging
import uuid
import json
import os
from typing import Dict, Any, Optional, List, Union, Tuple
from datetime import datetime
import asyncio

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage

from ...agent.base import RestaurantRecommenderAgent, AgentState
from ...commands.parser import CommandParser
from ...commands.models import SearchCommand, RecommendationCommand, InformationalCommand, CollectionCommand
from ..models.responses import RestaurantQueryResponse, RestaurantInfo
from ...memory import RestaurantMemory  # Use new LangChain memory

logger = logging.getLogger(__name__)


class RestaurantService:
    """Service class for handling restaurant queries with conversational memory."""
    
    def __init__(self):
        """Initialize the restaurant service."""
        server_url = os.getenv("RESTAURANT_SERVER_URL", "http://dev.gifco.io")
        self.memory = RestaurantMemory()  # Initialize memory first
        self.agent = RestaurantRecommenderAgent(memory=self.memory)  # Pass memory to agent
        self.command_parser = CommandParser(server_url=server_url)
        logger.info(f"RestaurantService initialized with server URL: {server_url}")
    
    async def query(self, query: str, location: Optional[str] = None, thread_id: Optional[str] = None, auth_token: Optional[str] = None) -> RestaurantQueryResponse:
        """Process a restaurant query and return a response.
        
        Args:
            query: Natural language query from user
            location: Optional location filter
            thread_id: Thread ID for conversation context
            auth_token: Optional authentication token for collection operations
            
        Returns:
            RestaurantQueryResponse with processed results
        """
        try:
            logger.info(f"Processing query: '{query}', location: {location}, thread_id: {thread_id}")
            
            # Step 1: Set up thread context
            if not thread_id:
                thread_id = str(uuid.uuid4())
                
            # Add user message to memory
            self.memory.add_user_message(thread_id, query)
            
            # Step 2: Check if this is a collection creation request with stored restaurants
            if self._is_collection_request_with_stored_restaurants(query, thread_id, auth_token):
                return await self._handle_collection_creation_from_memory(query, thread_id, auth_token)
            
            # Step 3: Parse query using the command parser
            parse_result = self.command_parser.parse_and_execute(query, auth_token=auth_token)
            command = parse_result["command"]
            tool_response = parse_result["tool_response"]
            error = parse_result["error"]
            
            command_type = self._get_command_type(command)
            logger.info(f"Parsed command type: {command_type}")
            
            # Step 4: Handle parsing errors
            if error:
                error_message = f"Error processing request: {error}"
                self.memory.add_ai_message(thread_id, error_message)
                return RestaurantQueryResponse(
                    success=False,
                    message=error_message,
                    query=query,
                    thread_id=thread_id,
                    response_count=0,
                    error=error,
                    timestamp=datetime.now()
                )
            
            # Step 5: Process tool response
            success, raw_message, error, restaurants = self._process_tool_response(tool_response, command_type)
            
            if not success:
                self.memory.add_ai_message(thread_id, raw_message)
                return RestaurantQueryResponse(
                    success=False,
                    message=raw_message,
                    query=query,
                    thread_id=thread_id,
                    response_count=0,
                    error=error,
                    timestamp=datetime.now()
                )
            
            # Step 6: Generate AI response using LLM
            if command_type in ['search', 'recommendation']:
                ai_message = await self._generate_ai_message(query, restaurants, location)
            
                # Store restaurants in memory for potential future use (only if we have results)
                if restaurants and len(restaurants) > 0:
                    self.memory.update_restaurant_search_context(
                        thread_id, restaurants, query, 
                        search_metadata={"location": location, "result_count": len(restaurants)}
                    )
            else:           
                # For info commands or other responses
                ai_message = raw_message
            
            # Step 7: Add AI response to memory
            self.memory.add_ai_message(thread_id, ai_message)
            
            # Step 8: Return response
            return RestaurantQueryResponse(
                success=True,
                message=ai_message,
                query=query,
                thread_id=thread_id,
                command_type=command_type,
                restaurants=restaurants,
                response_count=len(restaurants) if restaurants else 0,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            error_message = "Sorry, I encountered an error processing your request. Please try again."
            
            if thread_id:
                self.memory.add_ai_message(thread_id, error_message)
            
            return RestaurantQueryResponse(
                success=False,
                message=error_message,
                query=query,
                thread_id=thread_id or str(uuid.uuid4()),
                response_count=0,
                error=str(e),
                timestamp=datetime.now()
            )

    def _is_collection_request_with_stored_restaurants(self, query: str, thread_id: str, auth_token: Optional[str]) -> bool:
        """Check if this is a collection creation request and we have stored restaurants."""
        logger.info(f"Checking collection request: query='{query}', thread_id={thread_id}, has_auth_token={bool(auth_token)}")
        
        if not auth_token:
            logger.info("No auth token provided - not a collection request")
            return False
        
        # Use LLM to classify if this is a collection creation request
        is_collection_request = self._classify_collection_request(query, thread_id)
        
        if not is_collection_request:
            logger.info("Query classified as NOT a collection request")
            return False
            
        # Check if we have stored restaurants
        last_restaurants, _ = self.memory.get_last_restaurants(thread_id)
        has_restaurants = len(last_restaurants) > 0
        
        logger.info(f"Memory check: has_restaurants={has_restaurants}, restaurant_count={len(last_restaurants)}")
        
        if has_restaurants:
            logger.info("✅ Collection request detected with stored restaurants - triggering collection creation")
        else:
            logger.info("❌ Collection request detected but no stored restaurants found")
            
        return has_restaurants

    def _classify_collection_request(self, query: str, thread_id: str) -> bool:
        """Use LLM to classify if a query is asking for collection creation."""
        try:
            # Get conversation context if available
            conversation_context = ""
            try:
                conversation_history = self.memory.get_conversation_history(thread_id)
                if conversation_history and len(conversation_history) > 0:
                    # Get the last AI message for context
                    for msg in reversed(conversation_history):
                        if hasattr(msg, 'type') and msg.type == 'ai':
                            conversation_context = f"Previous AI message: {msg.content[:200]}..."
                            break
            except Exception as e:
                logger.warning(f"Could not get conversation context: {str(e)}")
            
            classification_prompt = f"""Analyze if the user's query is asking to create a restaurant collection.

User Query: "{query}"
{conversation_context}

A collection creation request is when the user wants to:
1. Create/make/save a collection of restaurants
2. Save restaurant search results
3. Organize restaurants into a group
4. Respond affirmatively (yes/ok/sure) to a previous AI suggestion about creating a collection

Return ONLY "YES" if this is a collection creation request, or "NO" if it's not.

Examples:
- "create a collection" → YES
- "save these restaurants" → YES  
- "make a collection from these results" → YES
- "yes" (when previous AI asked about creating collection) → YES
- "what are the opening hours?" → NO
- "tell me about Italian cuisine" → NO
- "find more restaurants" → NO
- "yes I want more information about restaurants" → NO

Answer:"""

            from langchain_core.messages import SystemMessage, HumanMessage
            
            messages = [
                SystemMessage(content="You are a classification assistant. Analyze queries to determine if they're asking for collection creation. Respond with only 'YES' or 'NO'."),
                HumanMessage(content=classification_prompt)
            ]
            
            response = self.agent.llm.invoke(messages)
            classification = response.content.strip().upper()
            
            is_collection_request = classification == "YES"
            logger.info(f"LLM classification for query '{query}': {classification} → {is_collection_request}")
            
            return is_collection_request
            
        except Exception as e:
            logger.error(f"Error classifying collection request: {str(e)}")
            # Fallback: if LLM fails, be conservative and return False
            return False

    async def _handle_collection_creation_from_memory(self, query: str, thread_id: str, auth_token: str) -> RestaurantQueryResponse:
        """Handle collection creation using restaurants stored in memory."""
        try:
            logger.info(f"Handling collection creation from memory for thread {thread_id}")
            
            # Get stored restaurants and query context
            last_restaurants, last_query = self.memory.get_last_restaurants(thread_id)
            
            if not last_restaurants:
                error_message = "No recent restaurant search results available for collection creation."
                self.memory.add_ai_message(thread_id, error_message)
                return RestaurantQueryResponse(
                    success=False,
                    message=error_message,
                    query=query,
                    thread_id=thread_id,
                    response_count=0,
                    error="No stored restaurants",
                    timestamp=datetime.now()
                )
            
            # Extract restaurant IDs from stored restaurants
            restaurant_ids = []
            logger.info(f"Extracting restaurant IDs from {len(last_restaurants)} stored restaurants")
            
            for i, restaurant in enumerate(last_restaurants):
                logger.info(f"Restaurant {i+1}: name='{restaurant.name}', description='{restaurant.description}'")
                
                if restaurant.description and restaurant.description.startswith("ID:"):
                    # Extract actual ID from "ID:actual_id|other_description" format
                    id_part = restaurant.description.split("|")[0].replace("ID:", "").strip()
                    restaurant_ids.append(id_part)
                    logger.info(f"  → Extracted real ID: {id_part}")
                else:
                    # Fallback to name-based ID if no actual ID available
                    fallback_id = restaurant.name.replace(" ", "_").lower()
                    restaurant_ids.append(fallback_id)
                    logger.info(f"  → Using fallback ID: {fallback_id}")
            
            logger.info(f"Final restaurant IDs to add to collection: {restaurant_ids}")
            
            # Generate collection name and description using LLM
            collection_details = await self._generate_collection_details(last_query, last_restaurants)
            
            # Create collection with restaurants using the API client
            from ...utils.restaurant_util import RestaurantAPIClient
            api_client = RestaurantAPIClient(self.command_parser.server_url)
            
            result = api_client.create_collection_with_restaurants_sync(
                name=collection_details["name"],
                description=collection_details["description"],
                restaurant_ids=restaurant_ids,
                is_public=True,
                tags=collection_details["tags"],
                auth_token=auth_token
            )
            
            # Parse the result
            import json
            result_data = json.loads(result)
            
            if result_data.get("error"):
                error_message = f"Failed to create collection: {result_data['error']}"
                self.memory.add_ai_message(thread_id, error_message)
                return RestaurantQueryResponse(
                    success=False,
                    message=error_message,
                    query=query,
                    thread_id=thread_id,
                    response_count=0,
                    error=result_data["error"],
                    timestamp=datetime.now()
                )
            
            # Generate success message
            collection_name = collection_details["name"]
            added_count = result_data.get("successfully_added", 0)
            total_count = result_data.get("total_restaurants", len(restaurant_ids))
            
            success_message = f"✅ Collection '{collection_name}' created successfully!\n"
            success_message += f"📊 Added {added_count}/{total_count} restaurants to your collection."
            
            if result_data.get("failed_restaurants"):
                failed_count = len(result_data["failed_restaurants"])
                success_message += f"\n⚠️ {failed_count} restaurants failed to add."
            
            self.memory.add_ai_message(thread_id, success_message)
            
            return RestaurantQueryResponse(
                success=True,
                message=success_message,
                query=query,
                thread_id=thread_id,
                command_type="collection",
                collection_result=result_data,
                response_count=len(restaurant_ids),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error handling collection creation from memory: {str(e)}")
            error_message = "Sorry, I encountered an error creating the collection. Please try again."
            
            self.memory.add_ai_message(thread_id, error_message)
            return RestaurantQueryResponse(
                success=False,
                message=error_message,
                query=query,
                thread_id=thread_id,
                response_count=0,
                error=str(e),
                timestamp=datetime.now()
            )

    async def _generate_collection_details(self, search_query: str, restaurants: List[RestaurantInfo]) -> Dict[str, Any]:
        """Generate collection name, description and tags based on search context."""
        try:
            # Extract cuisines and locations from restaurants
            cuisines = set()
            locations = set()
            
            for restaurant in restaurants:
                if hasattr(restaurant, 'cuisine') and restaurant.cuisine:
                    cuisines.add(restaurant.cuisine)
                if hasattr(restaurant, 'location') and restaurant.location:
                    locations.add(restaurant.location)
            
            # Create prompt for LLM to generate collection details
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
            
            prompt = f"""Generate collection details for a restaurant collection based on this context:

Search Query: {search_query}
Number of Restaurants: {len(restaurants)}
Cuisines Found: {', '.join(cuisines) if cuisines else 'Mixed'}
Locations: {', '.join(locations) if locations else 'Various'}

Generate a JSON response with:
1. "name": A unique, descriptive collection name
2. "description": A detailed description of the collection
3. "tags": An array of 3-5 relevant tags

Requirements:
- Name should be catchy and descriptive and it should be short and concise
- Description should mention the search context and it should be one short and concise sentence
- Tags should be relevant to the cuisine/location/search

Example format:
{{
  "name": "Italian Spots (Delhi)",
  "description": "A curated collection of top Italian restaurants found during our search in Delhi, featuring authentic cuisine and great ambiance.",
  "tags": ["italian", "delhi", "curated", "authentic", "dining"]
}}"""

            from langchain_core.messages import SystemMessage, HumanMessage
            
            messages = [
                SystemMessage(content="You are a helpful assistant that generates restaurant collection details. Always respond with valid JSON only."),
                HumanMessage(content=prompt)
            ]
            
            response = await self.agent.llm.ainvoke(messages)
            
            # Parse JSON response
            import json
            collection_details = json.loads(response.content.strip())
            
            # Validate required fields
            if not all(key in collection_details for key in ["name", "description", "tags"]):
                raise ValueError("Missing required fields in LLM response")
                
            return collection_details
            
        except Exception as e:
            logger.error(f"Error generating collection details: {str(e)}")
            # Fallback to simple details
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
            
            return {
                "name": f"Restaurant Collection - {timestamp}",
                "description": f"A curated collection of restaurants from search: {search_query}",
                "tags": ["curated", "restaurants", "search_results"]
            }
    
    async def _generate_ai_message(self, query: str, restaurants: Optional[List[RestaurantInfo]], location: Optional[str]) -> str:
        """Generate a conversational AI message about the restaurants found or no results."""
        logger.info(f"Generating AI message for query: '{query}', restaurants: {len(restaurants) if restaurants else 0}, location: {location}")
        
        if not restaurants or len(restaurants) == 0:
            logger.info(f"No restaurants found for query '{query}' in location '{location}', generating no-results message")
            
            # Prompt for no results scenario
            ai_prompt = f"""Generate a helpful and friendly response when no restaurants were found for the user's query.

User Query: {query}
Location: {location or 'not specified'}

The response should:
1. Acknowledge that no restaurants were found
2. Be empathetic and helpful
3. Suggest alternative search options (try different keywords, location, cuisine type)
4. Keep it conversational and encouraging
5. Keep it concise (2-3 sentences max)

Example: "I couldn't find any restaurants matching your search for [query]. You might want to try searching with different keywords, a broader location, or a different cuisine type. I'm here to help you find the perfect place!"

Keep the tone friendly and supportive."""

            system_message = "You are a helpful restaurant assistant. Generate empathetic and helpful responses when no restaurants are found."
            
        else:
            logger.info(f"Found {len(restaurants)} restaurants: {[r.name for r in restaurants[:3]]}")
            
            # Create a more engaging message that proactively asks about collection creation
            restaurant_names = [r.name for r in restaurants[:3]]  # Show first 3 restaurant names
            name_preview = ", ".join(restaurant_names)
            if len(restaurants) > 3:
                name_preview += f" and {len(restaurants) - 3} more"
            
            # Prompt for successful results scenario
            ai_prompt = f"""Generate a friendly, conversational response about finding {len(restaurants)} restaurants including {name_preview}.

The response should:
1. Briefly mention the search results (don't list all restaurants)
2. Proactively ask if the user wants to create a collection from these restaurants
3. Make it clear they can just say "yes" or "create collection"
4. Be enthusiastic and helpful
5. Keep it concise (2-3 sentences max)

Example: "Great! I found 5 amazing restaurants for you including [Restaurant Name], [Restaurant Name], and [Restaurant Name]. Would you like me to create a collection from these restaurants? Just say 'yes' and I'll create one with a perfect name!"

Keep the tone friendly and conversational."""

            system_message = "You are a helpful restaurant assistant. Generate brief, friendly, and engaging responses that proactively suggest collection creation."

        # Use direct LLM call for message generation
        from langchain_core.messages import SystemMessage, HumanMessage
        
        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=ai_prompt)
        ]
                
        logger.info("Calling LLM for AI message generation")
        response = await self.agent.llm.ainvoke(messages)
        
        logger.info("LLM response received successfully")
        return response.content.strip()
    
    def _extract_restaurant_location(self, restaurant_data: dict) -> str:
        """Extract location from restaurant data handling different field names.
        
        Args:
            restaurant_data: Dictionary containing restaurant information
            
        Returns:
            Location string or empty string if not found
        """
        return (restaurant_data.get('location') or 
                restaurant_data.get('place') or 
                restaurant_data.get('address') or
                restaurant_data.get('area') or '')
    
    def _get_command_type(self, command) -> str:
        """Get the command type from a parsed command."""
        if isinstance(command, SearchCommand):
            return "search"
        elif isinstance(command, RecommendationCommand):
            return "recommendation"
        elif isinstance(command, InformationalCommand):
            return "informational"
        elif isinstance(command, CollectionCommand):
            return "collection"
        else:
            return "unknown"
    
    def _extract_query_info(self, command) -> tuple[Optional[str], Optional[str]]:
        """Extract location and cuisine information from a parsed command."""
        try:
            if not command:
                return None, None
                
            location = None
            cuisine = None
            
            if isinstance(command, SearchCommand):
                location = command.search_query.place
                cuisine = getattr(command.search_query, 'cuisine', None)
            elif isinstance(command, RecommendationCommand):
                location = command.recommendation_query.place
                cuisine = getattr(command.recommendation_query, 'cuisine', None)
            
            return location, cuisine
            
        except Exception as e:
            logger.error(f"Error extracting query info: {str(e)}")
            return None, None
    
    def _process_tool_response(self, tool_response, command_type: str) -> tuple[bool, str, Optional[str], Optional[list[RestaurantInfo]]]:
        """Process the tool response and return formatted results."""
        try:
            if not tool_response:
                return False, "No restaurants found", "No tool response", None
            
            if isinstance(tool_response, str):
                try:
                    # Parse JSON response from API tool
                    api_data = json.loads(tool_response)
                    if 'error' in api_data:
                        return False, f"API Error: {api_data['error']}", api_data.get('error'), None
                    else:
                        message = self._format_api_response(api_data)
                        restaurants = self._extract_restaurants_from_api_response(api_data) if command_type in ['search', 'recommendation'] else None
                        return True, message, None, restaurants
                except json.JSONDecodeError:
                    return False, f"Invalid API response: {tool_response}", "Invalid JSON response", None
            elif isinstance(tool_response, (dict, list)):
                # Direct tool response as dict or list
                if isinstance(tool_response, dict) and 'help_text' in tool_response:
                    message = tool_response['help_text']
                    return True, message, None, None
                else:
                    message = self._format_api_response(tool_response)
                    restaurants = self._extract_restaurants_from_api_response(tool_response) if command_type in ['search', 'recommendation'] else None
                    return True, message, None, restaurants
            else:
                # Other tool response types
                message = self._format_tool_response(tool_response)
                return True, message, None, None
                
        except Exception as e:
            logger.error(f"Error processing tool response: {str(e)}")
            return False, "Error processing response", str(e), None
    
    def _format_api_response(self, api_data) -> str:
        """Format the API response for display."""
        try:
            # Handle new tag-based search response format
            if isinstance(api_data, dict) and 'restaurants' in api_data:
                restaurants = api_data.get('restaurants', [])
                if restaurants and isinstance(restaurants, list):
                    formatted_response = "Here are the restaurant recommendations:\n\n"
                    for i, restaurant in enumerate(restaurants, 1):
                        name = restaurant.get('name', 'Restaurant')
                        # Handle different location field names from the API
                        location = self._extract_restaurant_location(restaurant)
                        rating = restaurant.get('rating', '')
                        cuisine = restaurant.get('cuisine', '')
                        price_range = restaurant.get('price_range', '')
                        
                        formatted_response += f"{i}. **{name}**"
                        if location:
                            formatted_response += f" - {location}"
                        formatted_response += "\n"
                        
                        details = []
                        if rating:
                            details.append(f"⭐ {rating}")
                        if cuisine:
                            details.append(f"{cuisine}")
                        if price_range:
                            details.append(f"{price_range}")
                        
                        if details:
                            formatted_response += f"   {' | '.join(details)}\n"
                        formatted_response += "\n"
                    
                    return formatted_response.strip()
            
            # Generic formatting for other response types
            return self._format_tool_response(api_data)
             
        except Exception as e:
            logger.error(f"Error formatting API response: {str(e)}")
            return f"API Response: {json.dumps(api_data, indent=2) if isinstance(api_data, dict) else str(api_data)}"
    
    def _format_tool_response(self, response: Any) -> str:
        """Format any tool response for display."""
        try:
            if isinstance(response, dict):
                formatted_response = "Response:\n"
                for key, value in response.items():
                    if isinstance(value, (list, dict)):
                        formatted_response += f"{key}: {json.dumps(value, indent=2)}\n"
                    else:
                        formatted_response += f"{key}: {value}\n"
                return formatted_response.strip()
            else:
                return str(response)
        except Exception as e:
            logger.error(f"Error formatting tool response: {str(e)}")
            return str(response)
    
    def _extract_restaurants_from_api_response(self, api_data: dict) -> Optional[list[RestaurantInfo]]:
        """Extract restaurants from the API response."""
        try:
            restaurants = []
            
            # Handle new tag-based search response format - restaurants directly in response
            if isinstance(api_data, dict) and 'restaurants' in api_data:
                restaurant_list = api_data['restaurants']
                if restaurant_list and isinstance(restaurant_list, list):
                    for restaurant_data in restaurant_list:
                        name = restaurant_data.get('name')
                        # Handle different location field names from the API
                        location = self._extract_restaurant_location(restaurant_data)
                        restaurant_id = restaurant_data.get('_id') or restaurant_data.get('id')
                    
                        if name:  # Only require name, location is optional
                            description = restaurant_data.get('description', '')
                            # Store the ID for collection creation if available
                            if restaurant_id:
                                description = f"ID:{restaurant_id}|{description}"
                            
                            restaurant = RestaurantInfo(
                                name=name,
                                location=location,
                                rating=restaurant_data.get('rating'),
                                cuisine=restaurant_data.get('cuisine'),
                                price_range=restaurant_data.get('price_range'),
                                description=description
                            )
                            restaurants.append(restaurant)
            
            return restaurants if restaurants else None
             
        except Exception as e:
            logger.error(f"Error extracting restaurants from API response: {str(e)}")
            return None 