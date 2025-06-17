"""Restaurant service for API endpoints."""
import logging
import uuid
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime


from ...commands.parser import CommandParser
from ...commands.models import SearchCommand, RecommendationCommand, InformationalCommand
from ..models.responses import RestaurantQueryResponse, ChatResponse, RestaurantInfo

logger = logging.getLogger(__name__)


class RestaurantService:
    """Service class for handling restaurant queries."""
    
    def __init__(self):
        """Initialize the restaurant service."""
        server_url = os.getenv("RESTAURANT_SERVER_URL", "http://dev.gifco.io")
        self.command_parser = CommandParser(server_url=server_url)
        logger.info(f"RestaurantService initialized with server URL: {server_url}")
    
    async def query(self, query: str, location: Optional[str] = None) -> RestaurantQueryResponse:
        """Process a restaurant query using the integrated command parser.
        
        Args:
            query: The restaurant query string
            location: Optional location override
            
        Returns:
            RestaurantQueryResponse with results
        """
        try:
            logger.info(f"Processing query: '{query}' with location: {location}")
            
            # Enhance query with location if provided
            enhanced_query = f"{query} in {location}" if location and location.lower() not in query.lower() else query
            
            # Parse and execute using CommandParser
            parser_result = self.command_parser.parse_and_execute(enhanced_query)
            
            # Handle parser errors
            if parser_result.get('error'):
                return RestaurantQueryResponse(
                    success=False,
                    message=f"Failed to parse query: {parser_result['error']}",
                    query=query,
                    error=parser_result['error'],
                    timestamp=datetime.now()
                )
            
            # Extract results
            command = parser_result.get('command')
            tool_response = parser_result.get('tool_response')
            
            # Get command type and query info
            command_type = self._get_command_type(command)
            parsed_location, parsed_cuisine = self._extract_query_info(command)
            
            # Process tool response
            success, message, error, restaurants = self._process_tool_response(tool_response, command_type)
            
            return RestaurantQueryResponse(
                success=success,
                query=query,
                restaurants=restaurants,
                location=location or parsed_location,
                cuisine=parsed_cuisine,
                command_type=command_type,
                error=error,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error in query method: {str(e)}", exc_info=True)
            return RestaurantQueryResponse(
                success=False,
                message="An error occurred while processing your query",
                query=query,
                error=str(e),
                timestamp=datetime.now()
            )
    
    async def handle_chat(self, message: str, thread_id: Optional[str] = None) -> ChatResponse:
        """Handle a general chat message.
        
        Args:
            message: The user's message
            thread_id: Optional thread ID for conversation continuity
            
        Returns:
            ChatResponse with the result
        """
        try:
            logger.info(f"Processing chat message: '{message}' with thread_id: {thread_id}")
            
            # Generate thread ID if not provided
            if not thread_id:
                thread_id = str(uuid.uuid4())
            
            # Parse and execute using CommandParser
            parser_result = self.command_parser.parse_and_execute(message)
            
            # Extract results
            command = parser_result.get('command')
            tool_response = parser_result.get('tool_response')
            error = parser_result.get('error')
            
            # Get command type
            command_type = self._get_command_type(command)
            
            # Process response
            if error:
                success = False
                response_message = f"Failed to process message: {error}"
            else:
                success = tool_response is not None
                if tool_response:
                    if isinstance(tool_response, dict) and 'help_text' in tool_response:
                        response_message = tool_response['help_text']
                    else:
                        response_message = self._format_tool_response(tool_response)
                else:
                    response_message = "No response generated"
            
            return ChatResponse(
                success=success,
                message=response_message,
                thread_id=thread_id,
                command_type=command_type,
                error=error if not success else None,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error processing chat message: {str(e)}", exc_info=True)
            return ChatResponse(
                success=False,
                message="An error occurred while processing your message",
                thread_id=thread_id or str(uuid.uuid4()),
                error=str(e),
                timestamp=datetime.now()
            )
    
    def _get_command_type(self, command) -> str:
        """Get the command type from a parsed command."""
        if isinstance(command, SearchCommand):
            return "search"
        elif isinstance(command, RecommendationCommand):
            return "recommendation"
        elif isinstance(command, InformationalCommand):
            return "informational"
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
                cuisine = command.search_query.cuisine
            elif isinstance(command, RecommendationCommand):
                location = command.recommendation_query.place
                cuisine = command.recommendation_query.cuisine
            
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
                    
                    if name and location:
                        restaurant = RestaurantInfo(
                            name=name,
                            location=location,
                            rating=restaurant_data.get('rating'),
                            cuisine=restaurant_data.get('cuisine'),
                            price_range=restaurant_data.get('price_range'),
                            description=restaurant_data.get('description')
                        )
                        restaurants.append(restaurant)
            
            # Handle array format where each element has 'restaurants' array
            elif isinstance(api_data, list):
                for item in api_data:
                    if isinstance(item, dict) and 'restaurants' in item:
                        for restaurant_data in item['restaurants']:
                            name = restaurant_data.get('name')
                            place = restaurant_data.get('place')
                            
                            if name and place:
                                restaurant = RestaurantInfo(
                                    name=name,
                                    location=place,
                                    rating=None,  # Not available in this format
                                    cuisine=None,  # Could be extracted from foodTags if needed
                                    price_range=None,  # Not available in this format
                                    description=restaurant_data.get('googleMapLink')
                                )
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