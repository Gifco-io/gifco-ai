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
        """Process a unified query that can handle both restaurant search and conversational interactions.
        
        Args:
            query: The query string (restaurant search, conversation, or command)
            location: Optional location override
            thread_id: Optional thread ID for conversation continuity
            auth_token: Optional authorization token for authenticated requests
            
        Returns:
            RestaurantQueryResponse with restaurants list and AI message
        """
        try:
            logger.info(f"Processing unified query: '{query}' with location: {location}, thread_id: {thread_id}")
            
            # Generate thread ID if not provided
            if not thread_id:
                thread_id = str(uuid.uuid4())
            
            # Add user message to conversation memory using LangChain memory
            self.memory.add_user_message(thread_id, query)
            
            # Get conversation context for enhanced processing
            last_restaurants, last_query = self.memory.get_last_restaurants(thread_id)
            
            # Check if this is a collection creation request with previous restaurants
            if last_restaurants and self._is_collection_request(query):
                logger.info(f"Detected collection creation request with {len(last_restaurants)} previous restaurants from query: '{last_query}'")
                logger.info(f"Sample restaurants: {[r.name for r in last_restaurants[:3]]}")
                
                # Handle collection creation through conversational agent
                # Use the new memory system to get enhanced context
                enhanced_message = self.memory.get_context_for_agent(thread_id, query, auth_token)
                logger.info(f"Enhanced message preview: {enhanced_message[:200]}...")
                
                # Process with agent
                try:
                    agent_response = await asyncio.wait_for(
                        self.agent.handle_request(enhanced_message),
                        timeout=20.0
                    )
                    
                    # Check if agent failed with validation errors - use command parser as fallback
                    if not agent_response.success and ("validation error" in agent_response.message.lower() or "field required" in agent_response.message.lower()):
                        logger.info("Agent validation error detected, falling back to command parser")
                        raise Exception("Agent validation error")
                    
                    # Add assistant response to memory using LangChain memory
                    self.memory.add_ai_message(thread_id, agent_response.message)
                    
                    return RestaurantQueryResponse(
                        success=agent_response.success,
                        message=agent_response.message,
                        query=query,
                        thread_id=thread_id,
                        command_type="collection",
                        error=agent_response.error if not agent_response.success else None,
                        timestamp=datetime.now()
                    )
                    
                except asyncio.TimeoutError:
                    logger.error("Collection creation timed out")
                    return RestaurantQueryResponse(
                        success=False,
                        message="Sorry, the collection creation took too long. Please try again.",
                        query=query,
                        thread_id=thread_id,
                        error="Request timeout",
                        timestamp=datetime.now()
                    )
                except Exception as e:
                    logger.info(f"Agent failed with: {str(e)}, falling back to command parser")
                    
                    # Use command parser as fallback for collection creation
                    try:
                        parser_result = self.command_parser.parse_and_execute(enhanced_message, auth_token=auth_token)
                        
                        if parser_result.get('success', False):
                            logger.info("Command parser successfully created collection")
                            success_message = "✅ Successfully created your restaurant collection!"
                            
                            # Add assistant response to memory using LangChain memory
                            self.memory.add_ai_message(thread_id, success_message)
                            
                            return RestaurantQueryResponse(
                                success=True,
                                message=success_message,
                                query=query,
                                thread_id=thread_id,
                                command_type="collection",
                                timestamp=datetime.now()
                            )
                        else:
                            error_msg = parser_result.get('error', 'Unknown error')
                            logger.error(f"Command parser also failed: {error_msg}")
                            
                            return RestaurantQueryResponse(
                                success=False,
                                message=f"❌ Failed to create collection: {error_msg}",
                                query=query,
                                thread_id=thread_id,
                                command_type="collection",
                                error=error_msg,
                                timestamp=datetime.now()
                            )
                    except Exception as parser_error:
                        logger.error(f"Command parser fallback failed: {str(parser_error)}")
                        return RestaurantQueryResponse(
                            success=False,
                            message="❌ Failed to create collection due to technical issues. Please try again.",
                            query=query,
                            thread_id=thread_id,
                            command_type="collection",
                            error=str(parser_error),
                            timestamp=datetime.now()
                        )
            
            # For regular restaurant queries, enhance with location if provided
            enhanced_query = f"{query} in {location}" if location and location.lower() not in query.lower() else query
            
            # Parse and execute using CommandParser to get actual restaurant data
            parser_result = self.command_parser.parse_and_execute(enhanced_query, auth_token=auth_token)
            
            # Handle parser errors
            if parser_result.get('error'):
                return RestaurantQueryResponse(
                    success=False,
                    message=f"Failed to process query: {parser_result['error']}",
                    query=query,
                    thread_id=thread_id,
                    error=parser_result['error'], 
                    timestamp=datetime.now()
                )
            
            # Extract results
            command = parser_result.get('command')
            tool_response = parser_result.get('tool_response')
            collection_prompt = parser_result.get('collection_prompt')
            
            # Check if this is a collection creation result
            if parser_result.get('collection_id') or parser_result.get('successfully_added') is not None:
                # This is a collection creation result
                success = parser_result.get('success', False)
                if success:
                    collection_name = parser_result.get('collection', {}).get('name', 'Collection')
                    added_count = parser_result.get('successfully_added', 0)
                    total_count = parser_result.get('total_restaurants', 0)
                    
                    ai_message = f"✅ Successfully created collection '{collection_name}' with {added_count} out of {total_count} restaurants!"
                    self.memory.add_ai_message(thread_id, ai_message)
                    
                    return RestaurantQueryResponse(
                        success=True,
                        message=ai_message,
                        query=query,
                        thread_id=thread_id,
                        collection_created=True,
                        collection_result=parser_result,
                        timestamp=datetime.now()
                    )
                else:
                    error_msg = parser_result.get('error', 'Unknown error')
                    return RestaurantQueryResponse(
                        success=False,
                        message=f"❌ Failed to create collection: {error_msg}",
                        query=query,
                        thread_id=thread_id,
                        error=error_msg,
                        timestamp=datetime.now()
                    )
            
            # Get command type and query info
            command_type = self._get_command_type(command)
            parsed_location, parsed_cuisine = self._extract_query_info(command)
            
            # Process tool response to get restaurants
            success, raw_message, error, restaurants = self._process_tool_response(tool_response, command_type)
            
            if not success:
                return RestaurantQueryResponse(
                    success=False,
                    message=raw_message,
                    query=query,
                    thread_id=thread_id,
                    error=error,
                    timestamp=datetime.now()
                )
            
            # Generate AI message using the conversational agent
            ai_message = await self._generate_ai_message(query, restaurants, parsed_location)
            
            # Store restaurants in memory for potential collection creation using enhanced memory
            if restaurants and command_type in ['search', 'recommendation']:
                self.memory.update_restaurant_search_context(
                    thread_id, restaurants, query, 
                    search_metadata={"location": location or parsed_location, "result_count": len(restaurants)}
                )
                
                # If there's a collection prompt from parser, use it instead of generating our own
                if collection_prompt:
                    ai_message += f"\n\n{collection_prompt}"
                else:
                    # Add suggestion to create collection
                    ai_message += "\n\n💡 *Would you like me to create a collection from these restaurants? Just say 'create a collection' and I'll save them for you!*"
            
            # Add assistant message to memory using LangChain memory
            self.memory.add_ai_message(thread_id, ai_message)
            
            return RestaurantQueryResponse(
                success=True,
                message=ai_message,  # AI-generated conversational message
                query=query,
                thread_id=thread_id,
                restaurants=restaurants,  # Structured list of restaurant objects
                location=location or parsed_location,
                cuisine=parsed_cuisine,
                command_type=command_type,
                collection_prompt=collection_prompt,  # Include collection prompt for UI
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error in query method: {str(e)}", exc_info=True)
            return RestaurantQueryResponse(
                success=False,
                message="An error occurred while processing your query",
                query=query,
                thread_id=thread_id or str(uuid.uuid4()),
                error=str(e),
                timestamp=datetime.now()
            )
    

    
    async def _generate_ai_message(self, query: str, restaurants: Optional[List[RestaurantInfo]], location: Optional[str]) -> str:
        """Generate a conversational AI message about the restaurants found."""
        try:
            if not restaurants:
                return f"I couldn't find any restaurants for in {location or 'the specified area'}. You might want to try a different search or location."
            
            ai_prompt = f"""Based on the user's query "{query}" in {location or 'New Delhi'}, I found {len(restaurants)} restaurant{'s' if len(restaurants) != 1 else ''}.

Please generate a brief, friendly response that:
1. Acknowledges their query
2. Mentions the number of restaurants found
3. Suggests creating a collection from these restaurants by saying "Would you like me to create a collection from these restaurants? Just say 'create a collection'!"

Keep it short and conversational. Don't list individual restaurants since they're provided separately in the structured data."""

            # Use direct LLM call for simple message generation (not agent)
            from langchain_core.messages import SystemMessage, HumanMessage
            import asyncio
            try:
                messages = [
                    SystemMessage(content="You are a helpful restaurant assistant. Generate brief, friendly responses."),
                    HumanMessage(content=ai_prompt)
                ]
                
                response = await asyncio.wait_for(
                    self.agent.llm.ainvoke(messages),
                    timeout=8.0  # 8 second timeout for direct LLM call
                )
                
                if response and response.content:
                    return response.content.strip()
                else:
                    # Fallback to simple formatting if LLM fails
                    return self._create_simple_ai_message(query, restaurants, location)
            except asyncio.TimeoutError:
                logger.warning("AI message generation timed out, using fallback")
                return self._create_simple_ai_message(query, restaurants, location)
            except Exception as e:
                logger.warning(f"LLM message generation failed: {str(e)}, using fallback")
                return self._create_simple_ai_message(query, restaurants, location)
                
        except Exception as e:
            logger.error(f"Error generating AI message: {str(e)}")
            return self._create_simple_ai_message(query, restaurants, location)
    
    def _create_simple_ai_message(self, query: str, restaurants: List[RestaurantInfo], location: Optional[str]) -> str:
        """Create a simple AI message as fallback."""
        try:
            message = f"Great! I found {len(restaurants)} restaurant{'s' if len(restaurants) != 1 else ''}"
            if location:
                message += f" in {location}"
            message += ". "
            
            message += "💡 *Would you like me to create a collection from these restaurants? Just say 'create a collection' and I'll save them for you!*"
            return message
            
        except Exception as e:
            logger.error(f"Error creating simple AI message: {str(e)}")
            return f"I found some restaurants for your query '{query}', but had trouble formatting the response."

    async def _enhance_message_with_context(self, message: str, thread_id: str, last_restaurants: List[RestaurantInfo], last_query: Optional[str], auth_token: Optional[str]) -> str:
        """Enhance the user message with conversation context using LLM."""
        try:
            # Check if user is asking to create collection and we have previous restaurants
            if last_restaurants and self._is_collection_request(message):
                # Extract restaurant IDs from the last restaurants (limit to top 20 for performance)
                max_restaurants = 20
                limited_restaurants = last_restaurants[:max_restaurants]
                restaurant_ids = []
                restaurant_names = []
                
                for restaurant in limited_restaurants:
                    if restaurant.name:
                        restaurant_names.append(restaurant.name)
                        # Extract actual restaurant ID from description field if available
                        if restaurant.description and restaurant.description.startswith("ID:"):
                            # Extract ID from "ID:actual_id|other_description" format
                            id_part = restaurant.description.split("|")[0].replace("ID:", "").strip()
                            restaurant_ids.append(id_part)
                        else:
                            # Fallback to name-based ID if no actual ID available
                            restaurant_ids.append(restaurant.name.replace(" ", "_").lower())
                
                collection_context = f"""
                Previous restaurant search: "{last_query}"
                Found restaurants: {', '.join(restaurant_names)}
                Restaurant IDs: {', '.join(restaurant_ids)}
                
                User wants to create a collection from these restaurants.
                """
                
                # Generate a unique collection name
                import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                
                collection_name = "My Restaurant Collection"
                if "called" in message.lower() or "named" in message.lower():
                    # Try to extract collection name from user message
                    import re
                    name_match = re.search(r'(?:called|named)\s+["\']?([^"\']+)["\']?', message, re.IGNORECASE)
                    if name_match:
                        collection_name = name_match.group(1).strip()
                        # Add timestamp to make it unique
                        collection_name = f"{collection_name} - {timestamp}"
                elif last_query:
                    # Generate descriptive name based on search query and add timestamp
                    # Extract key terms from the query
                    query_lower = last_query.lower()
                    if "italian" in query_lower:
                        collection_name = f"Italian Favorites - {timestamp}"
                    elif "pizza" in query_lower:
                        collection_name = f"Pizza Collection - {timestamp}"
                    elif "chinese" in query_lower:
                        collection_name = f"Chinese Restaurants - {timestamp}"
                    elif "romantic" in query_lower or "dinner" in query_lower:
                        collection_name = f"Romantic Dining - {timestamp}"
                    elif "budget" in query_lower or "cheap" in query_lower:
                        collection_name = f"Budget Friendly Eats - {timestamp}"
                    else:
                        collection_name = f"Great Finds from '{last_query}' - {timestamp}"
                else:
                    collection_name = f"My Restaurant Collection - {timestamp}"
                
                # Use the create_collection_with_restaurants tool
                # Convert restaurant_ids to a safe string representation
                restaurant_ids_str = str(restaurant_ids).replace('{', '{{').replace('}', '}}')
                
                # Update description based on limitation
                total_found = len(last_restaurants)
                description = f"Collection of top {len(restaurant_names)} restaurants from search: {last_query}"
                if total_found > max_restaurants:
                    description += f" (showing top {max_restaurants} out of {total_found} found)"
                
                enhanced_message = f"""
                TASK: Create a restaurant collection from previous search results.
                
                CONTEXT:
                - Previous search: "{last_query}"
                - Total found: {total_found} restaurants
                - Adding top {len(restaurant_names)} restaurants: {', '.join(restaurant_names[:5])}{'...' if len(restaurant_names) > 5 else ''}
                - Restaurant IDs to add: {restaurant_ids_str}
                
                USER REQUEST: {message}
                
                INSTRUCTIONS:
                1. Use the create_collection_with_restaurants tool
                2. Collection name: "{collection_name}"
                3. Description: "{description}"
                4. Restaurant IDs: {restaurant_ids_str}
                5. Auth token: {auth_token or 'not_provided'}
                6. Set is_public: true
                7. Tags: ["user_created", "restaurant_search"]
                
                The user wants to create a collection from the restaurants found in their previous search. Use the create_collection_with_restaurants tool with the parameters above.
                """
                 
                logger.info(f"Enhanced collection creation message with {len(restaurant_ids)} restaurant IDs: {restaurant_ids[:3]}...")
                return enhanced_message
            
            # For other messages, add conversation history if relevant
            messages = self.memory.get_thread_messages(thread_id)
            recent_messages = messages[-6:] if len(messages) > 6 else messages  # Last 3 exchanges
            
            if recent_messages:
                context = "Recent conversation:\n"
                for msg in recent_messages:
                    role = "Human" if msg.__class__.__name__ == "HumanMessage" else "Assistant"
                    content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                    context += f"{role}: {content}\n"
                
                if last_restaurants:
                    context += f"\nLast restaurant search had {len(last_restaurants)} results."
                
                enhanced_message = f"{context}\n\nCurrent user message: {message}"
                return enhanced_message
            
            return message
            
        except Exception as e:
            logger.error(f"Error enhancing message with context: {str(e)}")
            return message
    
    def _is_collection_request(self, message: str) -> bool:
        """Check if the message is requesting to create a collection."""
        collection_keywords = [
            "create collection", "make collection", "save these", "create list",
            "make list", "save restaurants", "collection", "save them"
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in collection_keywords)
    
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
            # Handle list format with restaurant data
            if isinstance(api_data, list):
                all_restaurants = []
                for item in api_data:
                    if isinstance(item, dict) and 'restaurants' in item:
                        all_restaurants.extend(item['restaurants'])
                
                if all_restaurants:
                    formatted_response = "Here are the restaurant recommendations:\n\n"
                    for i, restaurant in enumerate(all_restaurants, 1):
                        name = restaurant.get('name', 'Restaurant')
                        place = restaurant.get('place', '')
                        
                        formatted_response += f"{i}. **{name}**"
                        if place:
                            formatted_response += f" - {place}"
                        formatted_response += "\n"
                        formatted_response += "\n"
                    
                    return formatted_response.strip()
            
            # Handle dictionary format
            elif isinstance(api_data, dict):
                # Handle restaurant search responses
                if 'questions' in api_data:
                    questions = api_data.get('questions', [])
                    if questions:
                        formatted_response = "Here are some restaurant recommendations:\n\n"
                        for i, question in enumerate(questions, 1):
                            title = question.get('title', 'Restaurant')
                            description = question.get('description', '')
                            formatted_response += f"{i}. **{title}**\n"
                            if description:
                                formatted_response += f"   {description}\n"
                            formatted_response += "\n"
                        return formatted_response.strip()
                
                # Handle direct restaurant listings
                if 'restaurants' in api_data:
                    restaurants = api_data.get('restaurants', [])
                    if restaurants:
                        formatted_response = "Here are the restaurant recommendations:\n\n"
                        for i, restaurant in enumerate(restaurants, 1):
                            name = restaurant.get('name', 'Restaurant')
                            location = restaurant.get('location', '')
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
            
            # Handle direct 'restaurants' key in API response
            if 'restaurants' in api_data:
                for restaurant_data in api_data['restaurants']:
                    name = restaurant_data.get('name')
                    location = restaurant_data.get('location')
                    restaurant_id = restaurant_data.get('_id') or restaurant_data.get('id')
                    
                    if name and location:
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
            
            # Handle array format where each element has 'restaurants' array
            elif isinstance(api_data, list):
                for item in api_data:
                    if isinstance(item, dict) and 'restaurants' in item:
                        for restaurant_data in item['restaurants']:
                            name = restaurant_data.get('name')
                            place = restaurant_data.get('place')
                            restaurant_id = restaurant_data.get('_id') or restaurant_data.get('id')
                            
                            if name and place:
                                restaurant = RestaurantInfo(
                                    name=name,
                                    location=place,
                                    rating=None,  # Not available in this format
                                    cuisine=None,  # Could be extracted from foodTags if needed
                                    price_range=None,  # Not available in this format
                                    description=restaurant_data.get('googleMapLink')
                                )
                                # Store the ID for collection creation
                                if restaurant_id:
                                    restaurant.description = f"ID:{restaurant_id}|{restaurant.description or ''}"
                                restaurants.append(restaurant)
            
            # Handle 'questions' format (from /api/questions endpoint)
            elif 'questions' in api_data:
                for question in api_data['questions']:
                    title = question.get('title')
                    description = question.get('description', '')
                    
                    if title:
                        restaurant = RestaurantInfo(
                            name=title,
                            description=description
                        )
                        restaurants.append(restaurant)
            
            return restaurants if restaurants else None
             
        except Exception as e:
            logger.error(f"Error extracting restaurants from API response: {str(e)}")
            return None

    def _extract_restaurants_from_response(self, response_message: str) -> Optional[List[RestaurantInfo]]:
        """Extract restaurant information from agent response message."""
        try:
            restaurants = []
            
            # Look for restaurant patterns in the response
            lines = response_message.split('\n')
            
            for line in lines:
                line = line.strip()
                # Look for numbered restaurant entries like "1. **Restaurant Name**"
                if line and (line[0].isdigit() or line.startswith('•')):
                    # Extract restaurant name
                    if '**' in line:
                        # Extract text between ** markers
                        parts = line.split('**')
                        if len(parts) >= 3:
                            name = parts[1].strip()
                            # Look for location info after the name
                            remaining = '**'.join(parts[2:]).strip()
                            location = None
                            if ' - ' in remaining:
                                location = remaining.split(' - ')[1].split('\n')[0].strip()
                            
                            if name:
                                restaurant = RestaurantInfo(
                                    name=name,
                                    location=location
                                )
                                restaurants.append(restaurant)
            
            return restaurants if restaurants else None
            
        except Exception as e:
            logger.error(f"Error extracting restaurants from response: {str(e)}")
            return None 