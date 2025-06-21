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
from ..utils.restaurant_util import RestaurantAPIClient
from .command import get_command_functions
from ..characters.parser import ParserCharacter 

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
        
        logger.info(f"Command functions: {json.dumps(self._functions, indent=2)}")

    def _get_command_functions(self) -> List[Dict[str, Any]]:
        """Get the function definitions for command parsing.
        
        Returns:
            List of function definitions for LLM function calling.
        """
        return get_command_functions()

    def parse_request(self, request: str) -> RestaurantCommand:
        """Parse a natural language request into a structured command.
        
        Args:
            request: Natural language request from user
            
        Returns:
            RestaurantCommand: Parsed command object (defaults to InformationalCommand if no match)
        """
        try:
            logger.info(f"Parsing request: {request}")
            
            # Create system message with parsing instructions
            system_message = ParserCharacter.get_character()

            # Call LLM to parse request
            messages = [system_message, HumanMessage(content=request)]
            llm_with_tools = self.llm.bind_tools(self._functions)
            response = llm_with_tools.invoke(messages)
            
            # Extract function call or default to info
            if (isinstance(response, AIMessage) and 
                hasattr(response, 'additional_kwargs') and 
                'tool_calls' in response.additional_kwargs):
                
                tool_call = response.additional_kwargs['tool_calls'][0]
                func_name = tool_call['function']['name']
                func_args = json.loads(tool_call['function']['arguments'])
                
                logger.info(f"Parsed command: {func_name} with args: {func_args}")

                # Create appropriate command
                if func_name == "search_restaurants":
                    query = RestaurantQuery(
                        query=func_args.get("query", ""),
                        place=func_args.get("place")
                    )
                    return SearchCommand(search_query=query, original_request=request)
                    
                elif func_name == "recommend_restaurants":
                    query = RestaurantQuery(
                        query=func_args.get("query", ""),
                        place=func_args.get("place")
                    )
                    return RecommendationCommand(recommendation_query=query, original_request=request)
                    
                elif func_name == "create_collection":
                    return CollectionCommand(
                        name=func_args.get("name", ""),
                        description=func_args.get("description", ""),
                        is_public=func_args.get("is_public", True),
                        tags=func_args.get("tags", []),
                        auth_token=func_args.get("auth_token", ""),
                        original_request=request
                    )
                elif func_name == "create_collection_with_restaurants":
                    return CollectionCommand(
                        name=func_args.get("name", ""),
                        description=func_args.get("description", ""),
                        is_public=func_args.get("is_public", True),
                        tags=func_args.get("tags", []),
                        auth_token=func_args.get("auth_token", ""),
                        restaurant_ids=func_args.get("restaurant_ids", []),
                        original_request=request
                    )
            # Default to info command for any unmatched request
            logger.info("No specific command matched, defaulting to info")
            return InformationalCommand(topic="help", original_request=request)
        
        except Exception as e:
            logger.error(f"Error parsing request: {str(e)}")
            # Always default to info command on any error
            return InformationalCommand(topic="help", original_request=request)

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
                "error": None
            }
            
            # Handle search and recommendation commands (both use same search logic)
            if isinstance(command, (SearchCommand, RecommendationCommand)):
                search_tool = self.get_restaurant_tool("search_restaurants")
                if search_tool:
                    # Get query from either search_query or recommendation_query
                    query = command.search_query if isinstance(command, SearchCommand) else command.recommendation_query
                    # Combine query and place into a single search string for tag extraction
                    search_text = query.query
                    if query.place:
                        search_text += f" in {query.place}"
                    
                    logger.info(f"Executing search with query: {search_text}")
                    tool_response = search_tool.func(query=search_text)
                    result["tool_response"] = tool_response
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
                token_to_use = auth_token or command.auth_token
                if not token_to_use:
                    result["error"] = "Authorization token required for collection creation"
                else:
                    # Check if we need to create collection with restaurants or just empty collection
                    if command.restaurant_ids:
                        # Create collection with restaurants
                        collection_tool = self.get_restaurant_tool("create_collection_with_restaurants")
                        if collection_tool:
                            logger.info(f"Creating collection with {len(command.restaurant_ids)} restaurants")
                            result["tool_response"] = collection_tool.func(
                                name=command.name,
                                description=command.description,
                                restaurant_ids=command.restaurant_ids,
                                is_public=command.is_public,
                                tags=command.tags,
                                auth_token=token_to_use
                            )
                        else:
                            result["error"] = "Collection with restaurants creation tool not available"
                    else:
                        # Create empty collection
                        collection_tool = self.get_restaurant_tool("create_collection")
                        if collection_tool:
                            logger.info("Creating empty collection")
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
                "error": str(e)
            }

    def parse_and_execute(self, request: str, auth_token: Optional[str] = None) -> Dict[str, Any]:
        """Parse request and execute using tools - simple flow.
        
        Args:
            request: Natural language request from user
            auth_token: Optional authorization token for authenticated operations
            
        Returns:
            Dictionary containing parsed command and tool execution results
        """
        logger.info(f"Processing request: {request}")
        
        # Step 1: Parse the request into a command (defaults to info if no match)
        command = self.parse_request(request)
        
        # Step 2: Execute the command using appropriate tools
        result = self.execute_with_tools(command, auth_token=auth_token)
        
        logger.info(f"Request processed successfully. Command type: {type(command).__name__}")
        return result

