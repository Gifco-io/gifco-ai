"""Command parser for restaurant recommendation requests."""
import os
import json
import logging
import asyncio
from typing import Dict, List, Any, Union, Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.callbacks import BaseCallbackHandler
from pydantic import BaseModel

from .models import (
    RestaurantCommand, RestaurantQuery, SearchCommand, 
    RecommendationCommand, InformationalCommand, CollectionCommand, CommandParseError
)
from ..agent.tools.tools import RestaurantTool

logger = logging.getLogger(__name__)


class CommandParserLoggingHandler(BaseCallbackHandler):
    """Callback handler for logging command parser interactions."""
    
    def on_llm_start(self, serialized, prompts, **kwargs):
        """Log when LLM starts generating."""
        logger.info(f"\n{'='*80}\nCommand Parser LLM Request:")
        logger.info(f"Model: {serialized.get('name', 'unknown')}")
        logger.info(f"Input:")
        for i, prompt in enumerate(prompts):
            logger.info(f"\nPrompt {i}:")
            if hasattr(prompt, 'to_messages'):
                messages = prompt.to_messages()
                for msg in messages:
                    logger.info(f"{msg.type}: {msg.content}")
            else:
                logger.info(str(prompt))
        
        if 'invocation_params' in kwargs:
            logger.info(f"\nInvocation params: {json.dumps(kwargs['invocation_params'], indent=2)}")
        logger.info(f"\nTools:")
        for tool in kwargs.get('tools', []):
            logger.info(json.dumps(tool, indent=2))
        logger.info('='*80)
    
    def on_llm_end(self, response, **kwargs):
        """Log when LLM finishes generating."""
        logger.info(f"\n{'='*80}\nCommand Parser LLM Response:")
        try:
            # Log response type for debugging
            logger.info(f"Response type: {type(response)}")
            
            # Handle different response types more robustly
            if hasattr(response, 'generations') and response.generations:
                # LLMResult object - get the first generation
                logger.info("Handling LLMResult object")
                generation = response.generations[0][0]
                
                if hasattr(generation, 'message'):
                    # AIMessage within generation
                    message = generation.message
                    logger.info(f"Found message in generation: {type(message)}")
                    
                    # Log tool calls if present
                    if hasattr(message, 'additional_kwargs') and message.additional_kwargs:
                        if 'tool_calls' in message.additional_kwargs:
                            tool_calls = message.additional_kwargs['tool_calls']
                            logger.info(f"Tool calls: {json.dumps(tool_calls, indent=2)}")
                    
                    # Log content if present
                    if hasattr(message, 'content') and message.content:
                        logger.info(f"Response content: {message.content}")
                    else:
                        logger.info(f"Message object: {str(message)}")
                        
                elif hasattr(generation, 'text'):
                    # Simple text generation
                    logger.info(f"Response text: {generation.text}")
                elif hasattr(generation, 'content'):
                    logger.info(f"Generation content: {generation.content}")
                else:
                    logger.info(f"Generation object: {str(generation)}")
                    
            elif hasattr(response, 'additional_kwargs'):
                # Direct AIMessage or similar
                logger.info("Handling direct message response")
                
                if response.additional_kwargs and 'tool_calls' in response.additional_kwargs:
                    tool_calls = response.additional_kwargs['tool_calls']
                    logger.info(f"Tool calls: {json.dumps(tool_calls, indent=2)}")
                
                if hasattr(response, 'content') and response.content:
                    logger.info(f"Response content: {response.content}")
                else:
                    logger.info(f"Response object: {str(response)}")
                    
            else:
                # Fallback - log what we can safely
                logger.info("Fallback response handling")
                
                # Try to serialize the response
                if hasattr(response, 'model_dump'):
                    try:
                        logger.info(f"Response data: {json.dumps(response.model_dump(), indent=2)}")
                    except Exception as serialize_error:
                        logger.info(f"Could not serialize response: {serialize_error}")
                        logger.info(f"Response string: {str(response)}")
                elif hasattr(response, 'dict'):
                    try:
                        logger.info(f"Response data: {json.dumps(response.dict(), indent=2)}")
                    except Exception as serialize_error:
                        logger.info(f"Could not serialize response: {serialize_error}")
                        logger.info(f"Response string: {str(response)}")
                else:
                    logger.info(f"Response: {str(response)}")
                
        except Exception as e:
            logger.error(f"Error logging response: {e}")
            logger.error(f"Response type: {type(response)}")
            logger.error(f"Response attributes: {dir(response) if hasattr(response, '__dict__') else 'No attributes'}")
            logger.info(f"Raw Response: {response}")
        
        logger.info('='*80)
    
    def on_llm_error(self, error, **kwargs):
        """Log when LLM errors."""
        logger.error(f"\nCommand Parser LLM Error: {str(error)}")


class CommandParser:
    """Parser for converting natural language into strongly-typed restaurant commands.
    
    This parser uses LangChain's function calling to extract command parameters
    and classify the command type. It handles restaurant search requests, 
    recommendation requests, and informational queries.
    """

    def __init__(self, model_name: str = "openai/gpt-4o-mini-2024-07-18", temperature: float = 0.0, server_url: str = None):
        """Initialize the command parser.
        
        Args:
            model_name: Name of the language model to use
            temperature: Temperature parameter for model output
            server_url: Base URL for the restaurant API server
        """
        load_dotenv()
        
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            callbacks=[CommandParserLoggingHandler()],
            base_url=os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1"),
            request_timeout=10,  # Reduced to 10 seconds for parser
            max_retries=0,  # No retries for faster parsing
            streaming=False  # Disable streaming
        )
        self.server_url = server_url or os.getenv("RESTAURANT_SERVER_URL", "http://localhost:8000")
        self._functions = self._get_command_functions()
        self._tools = RestaurantTool.get_restaurant_tools(self.server_url)
        
        # Temporary storage for restaurants
        self._temp_restaurants = []
        
        logger.info(f"Command functions: {json.dumps(self._functions, indent=2)}")

    def _get_command_functions(self) -> List[Dict[str, Any]]:
        """Get the function definitions for command parsing.
        
        Returns:
            List of function definitions for LLM function calling.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_restaurants",
                    "description": "Search for restaurants based on a specific query and location. Use this when the user wants to find restaurants matching specific criteria.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string", 
                                "description": "The main search query (e.g., 'best butter chicken', 'pizza place', 'romantic dinner')"
                            },
                            "place": {
                                "type": "string",
                                "description": "The location/place to search in (e.g., 'New York', 'downtown', 'near me'). Extract from context if not explicitly mentioned."
                            },
                            "cuisine": {
                                "type": "string",
                                "description": "Type of cuisine if mentioned (e.g., 'Indian', 'Italian', 'Chinese')"
                            },
                            "price_range": {
                                "type": "string", 
                                "description": "Price preference if mentioned (e.g., 'budget', 'cheap', 'expensive', 'fine dining')"
                            },
                            "dietary_restrictions": {
                                "type": "string",
                                "description": "Any dietary restrictions mentioned (e.g., 'vegetarian', 'vegan', 'gluten-free')"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "recommend_restaurants",
                    "description": "Get restaurant recommendations based on preferences or general requests. Use this when the user wants recommendations rather than searching for something specific.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The recommendation request (e.g., 'recommend a good restaurant', 'suggest somewhere for dinner')"
                            },
                            "place": {
                                "type": "string",
                                "description": "The location for recommendations (e.g., 'New York', 'downtown', 'near me')"
                            },
                            "cuisine": {
                                "type": "string",
                                "description": "Preferred cuisine type if mentioned"
                            },
                            "price_range": {
                                "type": "string",
                                "description": "Price preference if mentioned"
                            },
                            "dietary_restrictions": {
                                "type": "string",
                                "description": "Any dietary restrictions mentioned"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_collection",
                    "description": "Create a new restaurant collection. Use this when the user wants to create a curated list of restaurants with a name, description, tags, and privacy settings.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name of the collection (e.g., 'Best Pizza Places', 'Romantic Dinner Spots')"
                            },
                            "description": {
                                "type": "string",
                                "description": "Description of the collection (e.g., 'A curated list of the best pizza restaurants in the city')"
                            },
                            "is_public": {
                                "type": "boolean",
                                "description": "Whether the collection should be public (true) or private (false). Default is true."
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of tags for the collection (e.g., ['pizza', 'italian', 'comfort food'])"
                            },
                            "auth_token": {
                                "type": "string",
                                "description": "Authorization token for creating the collection"
                            }
                        },
                        "required": ["name", "description", "auth_token"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_info",
                    "description": "Handle informational requests about restaurants, help requests, or general questions.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "The topic of the informational request (e.g., 'help', 'how to use', 'about')"
                            }
                        },
                        "required": ["topic"]
                    }
                }
            }
        ]

    def add_to_temp_restaurants(self, restaurants: List[Dict[str, Any]]) -> None:
        """Add restaurants to temporary storage.
        
        Args:
            restaurants: List of restaurant dictionaries with id and other details
        """
        if restaurants:
            for restaurant in restaurants:
                if isinstance(restaurant, dict):
                    # Handle both 'id' and '_id' fields
                    restaurant_id = restaurant.get('id') or restaurant.get('_id')
                    if restaurant_id:
                        # Normalize the restaurant dict to always use 'id'
                        normalized_restaurant = restaurant.copy()
                        normalized_restaurant['id'] = restaurant_id
                        
                        # Check if restaurant is not already in temp storage
                        if not any(r['id'] == restaurant_id for r in self._temp_restaurants):
                            self._temp_restaurants.append(normalized_restaurant)
                            restaurant_name = restaurant.get('name') or restaurant.get('title') or restaurant_id
                            logger.info(f"Added restaurant {restaurant_name} to temporary storage")

    def get_temp_restaurants(self) -> List[Dict[str, Any]]:
        """Get restaurants from temporary storage.
        
        Returns:
            List of restaurants in temporary storage
        """
        return self._temp_restaurants.copy()

    def clear_temp_restaurants(self) -> None:
        """Clear temporary restaurant storage."""
        self._temp_restaurants.clear()
        logger.info("Cleared temporary restaurant storage")

    def _extract_restaurants_from_response(self, tool_response) -> List[Dict[str, Any]]:
        """Extract restaurants from API response.
        
        Args:
            tool_response: Response from restaurant search tool
            
        Returns:
            List of restaurant dictionaries
        """
        try:
            import json
            if isinstance(tool_response, str):
                response_data = json.loads(tool_response)
            else:
                response_data = tool_response
            
            restaurants = []
            if isinstance(response_data, list):
                # Response might be a list of objects, check if first item has restaurants
                if response_data and isinstance(response_data[0], dict):
                    first_item = response_data[0]
                    if 'restaurants' in first_item and isinstance(first_item['restaurants'], list):
                        restaurants = first_item['restaurants']
            elif isinstance(response_data, dict):
                # Check various possible keys where restaurants might be stored
                for key in ['restaurants', 'results', 'data', 'items']:
                    if key in response_data and isinstance(response_data[key], list):
                        restaurants = response_data[key]
                        break
            
            return restaurants
            
        except Exception as e:
            logger.warning(f"Could not parse restaurants from response: {e}")
            return []

    def get_collection_prompt(self) -> str:
        """Generate a prompt asking user if they want to create a collection.
        
        Returns:
            String prompt for collection creation
        """
        if not self._temp_restaurants:
            return ""
        
        restaurant_count = len(self._temp_restaurants)
        restaurant_names = [r.get('name') or r.get('title') or f"Restaurant {r['id']}" for r in self._temp_restaurants[:3]]
        
        if restaurant_count > 3:
            restaurant_list = ", ".join(restaurant_names) + f" and {restaurant_count - 3} more"
        else:
            restaurant_list = ", ".join(restaurant_names)
        
        return f"\nI found {restaurant_count} restaurants: {restaurant_list}. Would you like me to create a collection with these restaurants? (Type 'yes' to create collection, or continue with other queries)"

    async def create_collection_with_temp_restaurants(
        self, 
        collection_name: str, 
        collection_description: str,
        auth_token: str,
        is_public: bool = True,
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """Create a collection and add temporary restaurants to it.
        
        Args:
            collection_name: Name for the collection
            collection_description: Description for the collection
            auth_token: Authorization token
            is_public: Whether collection should be public
            tags: Tags for the collection
            
        Returns:
            Result of collection creation and restaurant addition
        """
        if not self._temp_restaurants:
            return {"error": "No restaurants in temporary storage"}
        
        try:
            from ..utils.restaurant_util import RestaurantAPIClient
            api_client = RestaurantAPIClient(self.server_url)
            
            # Extract restaurant IDs from temporary storage
            restaurant_ids = [restaurant['id'] for restaurant in self._temp_restaurants]
            original_count = len(self._temp_restaurants)
            
            # Generate unique collection name if default name provided
            import datetime
            if collection_name == "My Restaurant Collection":
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
                # Try to generate a better name based on restaurant data
                restaurant_names = [r.get('name', '') for r in self._temp_restaurants[:3]]
                cuisines = set()
                for r in self._temp_restaurants:
                    cuisine = r.get('cuisine') or r.get('foodTags', [])
                    if isinstance(cuisine, list):
                        cuisines.update(cuisine)
                    elif cuisine:
                        cuisines.add(cuisine)
                
                if cuisines:
                    main_cuisine = list(cuisines)[0] if cuisines else "Mixed"
                    collection_name = f"{main_cuisine} Collection - {timestamp}"
                else:
                    collection_name = f"Restaurant Collection - {timestamp}"
            
            # Use the efficient create_collection_with_restaurants method
            result = await api_client.create_collection_with_restaurants(
                name=collection_name,
                description=collection_description,
                restaurant_ids=restaurant_ids,
                is_public=is_public,
                tags=tags or [],
                auth_token=auth_token
            )
            
            # Clear temporary storage after processing
            self.clear_temp_restaurants()
            
            # Return consistent format with additional message
            if result.get("success", False):
                result["message"] = f"Created collection '{collection_name}' and added {result.get('successfully_added', 0)} restaurants"
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating collection with temp restaurants: {str(e)}")
            return {"error": f"Failed to create collection: {str(e)}"}

    def parse_request(self, request: str) -> RestaurantCommand:
        """Parse a natural language request into a structured command.
        
        Args:
            request: Natural language request from user
            
        Returns:
            RestaurantCommand: Parsed command object
            
        Raises: 
            CommandParseError: If parsing fails
        """
        try:
            logger.info(f"Parsing request: {request}")
            
            # Create system message with parsing instructions
            system_message = SystemMessage(
                content="""You are a restaurant command parser. Your job is to analyze user requests and extract structured information about restaurant searches, recommendations, and collection creation.

Guidelines for parsing:
1. For specific searches (like "best butter chicken spot", "pizza near me"), use search_restaurants
2. For general recommendations ("recommend a restaurant", "suggest somewhere"), use recommend_restaurants  
3. For creating collections ("create a collection", "make a list of restaurants"), use create_collection
4. For help or informational requests, use get_info
5. Always try to extract location/place information from context
6. Extract cuisine type, price preferences, and dietary restrictions when mentioned
7. Be flexible with location - users might say "near me", "downtown", city names, etc.
8. For collection creation, extract name, description, tags, privacy settings from user input

Note: Restaurants found in searches will be temporarily stored and user will be prompted if they want to create a collection.

Examples:
- "Best butter chicken spot?" → search_restaurants with query="best butter chicken", place="near me" (if no location specified)
- "Find Italian restaurants in NYC" → search_restaurants with query="Italian restaurants", place="NYC", cuisine="Italian"
- "Recommend a good restaurant for dinner" → recommend_restaurants with query="good restaurant for dinner"
- "Create a collection of pizza places" → create_collection with name="Pizza Places", description extracted from context
- "Help me find restaurants" → get_info with topic="help"

Extract all relevant information and choose the most appropriate function."""
            )

            # Call LLM to parse request
            messages = [
                system_message,
                HumanMessage(content=request)
            ]

            # Get response with function calling
            llm_with_tools = self.llm.bind_tools(self._functions)
            response = llm_with_tools.invoke(messages)
            
            # Debug log
            logger.info(f"Response type: {type(response)}")
            logger.info(f"Response dir: {dir(response)}")
            
            # Extract function call
            if isinstance(response, AIMessage):
                if not hasattr(response, 'additional_kwargs') or 'tool_calls' not in response.additional_kwargs:
                    # If no tool calls, default to help
                    return InformationalCommand(topic="help", original_request=request)

                tool_call = response.additional_kwargs['tool_calls'][0]
                logger.info(f"tool call: {tool_call}")
                
                # Get function name and arguments
                func_name = tool_call['function']['name']
                logger.info(f"function name: {func_name}")
                
                func_args = json.loads(tool_call['function']['arguments'])
                logger.info(f"function args: {func_args}")

                # Create appropriate command based on function name
                if func_name == "search_restaurants":
                    query = RestaurantQuery(
                        query=func_args.get("query", ""),
                        place=func_args.get("place"),
                        # cuisine=func_args.get("cuisine"), 
                        # price_range=func_args.get("price_range"),
                        # dietary_restrictions=func_args.get("dietary_restrictions")
                    )
                    command = SearchCommand(search_query=query)
                    command.original_request = request
                    return command
                    
                elif func_name == "recommend_restaurants":
                    query = RestaurantQuery(
                        query=func_args.get("query", ""),
                        place=func_args.get("place"),
                        # cuisine=func_args.get("cuisine"),
                        # price_range=func_args.get("price_range"),
                        # dietary_restrictions=func_args.get("dietary_restrictions")
                    )
                    command = RecommendationCommand(recommendation_query=query)
                    command.original_request = request
                    return command
                    
                elif func_name == "create_collection":
                    command = CollectionCommand(
                        name=func_args.get("name", ""),
                        description=func_args.get("description", ""),
                        is_public=func_args.get("is_public", True),
                        tags=func_args.get("tags", []),
                        auth_token=func_args.get("auth_token", ""),
                        original_request=request
                    )
                    return command
                    
                elif func_name == "get_info":
                    command = InformationalCommand(topic=func_args.get("topic", "help"))
                    command.original_request = request
                    return command
                else:
                    # Unknown function, default to help
                    return InformationalCommand(topic="help", original_request=request)
            else:
                # Unknown response type, default to help
                raise CommandParseError(f"Unexpected response type: {type(response)}")
        
        except Exception as e:
            logger.error(f"Error parsing request: {str(e)}", exc_info=True)
            # On any error, raise error
            raise CommandParseError(f"Failed to parse command: {str(e)}") from e

    def get_restaurant_tool(self, tool_name: str):
        """Get a specific restaurant tool by name.
        
        Args:
            tool_name: Name of the tool to retrieve
            
        Returns:
            The tool object if found, None otherwise
        """
        for tool in self._tools:
            if tool.name == tool_name:
                return tool
        return None

    def execute_with_tools(self, command: RestaurantCommand, auth_token: Optional[str] = None) -> Dict[str, Any]:
        """Execute a command using the appropriate tools.
        
        Args:
            command: The parsed command to execute
            auth_token: Optional authorization token for authenticated operations
            
        Returns:
            Dictionary containing command and tool execution results
        """
        try:
            result = {
                "command": command,
                "tool_response": None,
                "error": None,
                "collection_prompt": None
            }
            
            # Handle search commands with tools
            if isinstance(command, SearchCommand):
                search_tool = self.get_restaurant_tool("search_restaurants")
                if search_tool:
                    query = command.search_query
                    tool_response = search_tool.func(
                        query=query.query,
                        place=query.place or "New Delhi"
                    )
                    result["tool_response"] = tool_response
                    
                    # Parse the response and extract restaurants for temporary storage
                    restaurants = self._extract_restaurants_from_response(tool_response)
                    if restaurants:
                        self.add_to_temp_restaurants(restaurants)
                        result["collection_prompt"] = self.get_collection_prompt()
                        
                else:
                    result["error"] = "Search tool not available"
                    
            elif isinstance(command, RecommendationCommand):
                # Use the same search tool for recommendations
                search_tool = self.get_restaurant_tool("search_restaurants")
                if search_tool:
                    query = command.recommendation_query
                    tool_response = search_tool.func(
                        query=query.query,
                        place=query.place or "New Delhi"
                    )
                    result["tool_response"] = tool_response
                    
                    # Parse the response and extract restaurants for temporary storage
                    restaurants = self._extract_restaurants_from_response(tool_response)
                    if restaurants:
                        self.add_to_temp_restaurants(restaurants)
                        result["collection_prompt"] = self.get_collection_prompt()
                        
                else:
                    result["error"] = "Search tool not available"
                    
            elif isinstance(command, InformationalCommand):
                help_tool = self.get_restaurant_tool("get_restaurant_help")
                if help_tool:
                    tool_response = help_tool.func(command.topic)
                    result["tool_response"] = {"help_text": tool_response}
                else:
                    result["error"] = "Help tool not available"
            
            elif isinstance(command, CollectionCommand):
                collection_tool = self.get_restaurant_tool("create_collection")
                if collection_tool:
                    # Use the auth_token from the parameter if provided, otherwise use the one from command
                    token_to_use = auth_token or command.auth_token
                    if not token_to_use:
                        result["error"] = "Authorization token required for collection creation"
                    else:
                        result["tool_response"] = collection_tool.func(
                            name=command.name,
                            description=command.description,
                            is_public=command.is_public,
                            tags=command.tags,
                            auth_token=token_to_use
                        )
                else:
                    result["error"] = "Collection creation tool not available"
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing command with tools: {str(e)}")
            return {
                "command": command,
                "tool_response": None,
                "error": str(e),
                "collection_prompt": None
            }

    def handle_collection_creation_request(
        self, 
        collection_name: str = None, 
        collection_description: str = None,
        auth_token: str = None,
        is_public: bool = True,
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """Handle collection creation with temporary restaurants synchronously.
        
        Args:
            collection_name: Name for the collection
            collection_description: Description for the collection
            auth_token: Authorization token
            is_public: Whether collection should be public
            tags: Tags for the collection
            
        Returns:
            Result of collection creation and restaurant addition
        """
        try:
            # Check if there's already an event loop running
            try:
                # If we're in an async context, get the current loop
                loop = asyncio.get_running_loop()
                # Create a new thread to run the async function
                import concurrent.futures
                
                def run_in_thread():
                    # Create a new event loop in this thread
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        result = new_loop.run_until_complete(
                            self.create_collection_with_temp_restaurants(
                                collection_name or "My Restaurant Collection",
                                collection_description or "A curated collection of restaurants",
                                auth_token,
                                is_public,
                                tags
                            )
                        )
                        return result
                    finally:
                        new_loop.close()
                
                # Run in a separate thread
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_thread)
                    result = future.result(timeout=60)  # Longer timeout for multiple operations
                    
            except RuntimeError:
                # No event loop running, we can create one safely
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        self.create_collection_with_temp_restaurants(
                            collection_name or "My Restaurant Collection",
                            collection_description or "A curated collection of restaurants",
                            auth_token,
                            is_public,
                            tags
                        )
                    )
                finally:
                    loop.close()
            
            return result
            
        except Exception as e:
            logger.error(f"Error handling collection creation request: {str(e)}")
            return {"error": f"Failed to create collection: {str(e)}"}

    def parse_and_execute(self, request: str, auth_token: Optional[str] = None) -> Dict[str, Any]:
        """Parse request and execute using tools.
        
        Args:
            request: Natural language request from user
            auth_token: Optional authorization token for authenticated operations
            
        Returns:
            Dictionary containing parsed command and tool execution results
        """
        try:
            # Check if this is a "yes" response to create collection
            if request.lower().strip() in ['yes', 'y', 'yeah', 'yep', 'sure', 'ok', 'okay']:
                if self._temp_restaurants and auth_token:
                    result = self.handle_collection_creation_request(auth_token=auth_token)
                    # Add the success flag and other metadata for proper response handling
                    result["command"] = None
                    result["tool_response"] = None
                    result["collection_prompt"] = None
                    return result
                elif self._temp_restaurants and not auth_token:
                    return {
                        "error": "Authorization token required for collection creation",
                        "command": None,
                        "tool_response": None,
                        "collection_prompt": None,
                        "success": False
                    }
                else:
                    return {
                        "error": "No restaurants available for collection creation",
                        "command": None,
                        "tool_response": None,
                        "collection_prompt": None,
                        "success": False
                    }
            
            # Parse the request first
            command = self.parse_request(request)
            
            # Execute with tools, passing auth_token
            return self.execute_with_tools(command, auth_token=auth_token)
            
        except Exception as e:
            logger.error(f"Error in parse_and_execute: {str(e)}")
            return {
                "error": str(e),
                "command": None,
                "tool_response": None,
                "collection_prompt": None
            }

    def _format_place_name(self, place: str) -> str:
        """Format place name for API consistency (copied from RestaurantAPITool)."""
        if not place:
            return "New Delhi"  # Default location
        place_lower = place.lower().strip()
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

