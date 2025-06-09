"""Command parser for restaurant recommendation requests."""
import os
import json
import logging
from typing import Dict, List, Any, Union

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.callbacks import BaseCallbackHandler
from pydantic import BaseModel

from .models import (
    RestaurantCommand, RestaurantQuery, SearchCommand, 
    RecommendationCommand, InformationalCommand, CommandParseError
)
from ..agent.tools.tools import get_restaurant_tools

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
            if hasattr(response, 'additional_kwargs') and 'tool_calls' in response.additional_kwargs:
                tool_calls = response.additional_kwargs['tool_calls']
                logger.info(f"Tool calls: {json.dumps(tool_calls, indent=2)}")
            logger.info(f"Response content: {response.content}")
        except Exception as e:
            logger.error(f"Error logging response: {e}")
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

    def __init__(self, model_name: str = "openai/gpt-4o-2024-11-20", temperature: float = 0.0, server_url: str = None):
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
            base_url=os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
        )
        self.server_url = server_url or os.getenv("RESTAURANT_SERVER_URL", "http://localhost:8000")
        self._functions = self._get_command_functions()
        self._tools = get_restaurant_tools(self.server_url)
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
                content="""You are a restaurant command parser. Your job is to analyze user requests and extract structured information about restaurant searches and recommendations.

Guidelines for parsing:
1. For specific searches (like "best butter chicken spot", "pizza near me"), use search_restaurants
2. For general recommendations ("recommend a restaurant", "suggest somewhere"), use recommend_restaurants  
3. For help or informational requests, use get_info
4. Always try to extract location/place information from context
5. Extract cuisine type, price preferences, and dietary restrictions when mentioned
6. Be flexible with location - users might say "near me", "downtown", city names, etc.

Examples:
- "Best butter chicken spot?" → search_restaurants with query="best butter chicken", place="near me" (if no location specified)
- "Find Italian restaurants in NYC" → search_restaurants with query="Italian restaurants", place="NYC", cuisine="Italian"
- "Recommend a good restaurant for dinner" → recommend_restaurants with query="good restaurant for dinner"
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
                        cuisine=func_args.get("cuisine"),
                        price_range=func_args.get("price_range"),
                        dietary_restrictions=func_args.get("dietary_restrictions")
                    )
                    command = SearchCommand(search_query=query)
                    command.original_request = request
                    return command
                    
                elif func_name == "recommend_restaurants":
                    query = RestaurantQuery(
                        query=func_args.get("query", ""),
                        place=func_args.get("place"),
                        cuisine=func_args.get("cuisine"),
                        price_range=func_args.get("price_range"),
                        dietary_restrictions=func_args.get("dietary_restrictions")
                    )
                    command = RecommendationCommand(recommendation_query=query)
                    command.original_request = request
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

    def execute_with_tools(self, command: RestaurantCommand) -> Dict[str, Any]:
        """Execute a command using the appropriate tools.
        
        Args:
            command: The parsed command to execute
            
        Returns:
            Dictionary containing command and tool execution results
        """
        try:
            result = {
                "command": command,
                "tool_response": None,
                "error": None
            }
            
            # Handle search commands with tools
            if isinstance(command, SearchCommand):
                search_tool = self.get_restaurant_tool("search_restaurants")
                if search_tool:
                    query = command.search_query
                    tool_response = search_tool.func(
                        query=query.query,
                        place=query.place or "New Delhi",
                        query_type="current"
                    )
                    result["tool_response"] = json.loads(tool_response) if isinstance(tool_response, str) else tool_response
                else:
                    result["error"] = "Search tool not available"
                    
            elif isinstance(command, RecommendationCommand):
                # Use the same search tool for recommendations
                search_tool = self.get_restaurant_tool("search_restaurants")
                if search_tool:
                    query = command.recommendation_query
                    tool_response = search_tool.func(
                        query=query.query,
                        place=query.place or "New Delhi",
                        query_type="trending"  # Use trending for recommendations
                    )
                    result["tool_response"] = json.loads(tool_response) if isinstance(tool_response, str) else tool_response
                else:
                    result["error"] = "Search tool not available"
                    
            elif isinstance(command, InformationalCommand):
                help_tool = self.get_restaurant_tool("get_restaurant_help")
                if help_tool:
                    tool_response = help_tool.func(command.topic)
                    result["tool_response"] = {"help_text": tool_response}
                else:
                    result["error"] = "Help tool not available"
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing command with tools: {str(e)}")
            return {
                "command": command,
                "tool_response": None,
                "error": str(e)
            }

    def parse_and_execute(self, request: str) -> Dict[str, Any]:
        """Parse request and execute using tools.
        
        Args:
            request: Natural language request from user
            
        Returns:
            Dictionary containing parsed command and tool execution results
        """
        try:
            # Parse the request first
            command = self.parse_request(request)
            
            # Execute with tools
            return self.execute_with_tools(command)
            
        except Exception as e:
            logger.error(f"Error in parse_and_execute: {str(e)}")
            return {
                "error": str(e),
                "command": None,
                "tool_response": None
            }
