"""RestaurantRecommender agent implementation."""
import os
from typing import Dict, List, Optional, Union
from dotenv import load_dotenv
import uuid
import logging
import json
from decimal import Decimal

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.callbacks import BaseCallbackHandler
from pydantic import BaseModel

from .tools.tools import get_restaurant_tools
from .character.character import RestaurantRecommenderCharacter
from .safety.validator import SafetyValidator
from .operations.restaurant import RestaurantOperations
from ..commands.parser import CommandParser
from ..commands.models import (
    RestaurantCommand, RestaurantQuery, SearchCommand, 
    RecommendationCommand, InformationalCommand
)
from .models import AgentResponse
from app.config.config import OpenAIConfig, RestaurantAPIConfig

logger = logging.getLogger(__name__)

class OpenAILoggingHandler(BaseCallbackHandler):
    """Callback handler for logging OpenAI interactions."""
    
    def on_llm_start(self, serialized, prompts, **kwargs):
        """Log when LLM starts generating."""
        logger.info(f"\n{'='*50}\nLLM Request:")
        for i, prompt in enumerate(prompts):
            logger.info(f"Prompt {i}:\n{prompt}\n")
    
    def on_llm_end(self, response, **kwargs):
        """Log when LLM finishes generating."""
        logger.info(f"\nLLM Response:")
        try:
            # Try to get function call details
            if hasattr(response, 'additional_kwargs') and 'function_call' in response.additional_kwargs:
                func_call = response.additional_kwargs['function_call']
                logger.info(f"Function Call:\n  Name: {func_call.get('name')}\n  Arguments: {func_call.get('arguments')}")
            # Log the full response
            if hasattr(response, 'model_dump'):
                logger.info(f"Full Response:\n{json.dumps(response.model_dump(), indent=2)}")
            else:
                logger.info(f"Full Response:\n{json.dumps(response.dict(), indent=2)}")
        except Exception as e:
            logger.error(f"Error logging response: {e}")
            logger.info(f"Raw Response: {response}")
        logger.info(f"{'='*50}\n")
    
    def on_llm_error(self, error, **kwargs):
        """Log when LLM errors."""
        logger.error(f"\nLLM Error: {str(error)}")
        
    def on_tool_start(self, serialized, input_str, **kwargs):
        """Log when a tool starts."""
        logger.info(f"\nTool Start: {serialized.get('name', 'Unknown Tool')}")
        logger.info(f"Input: {input_str}")
        
    def on_tool_end(self, output, **kwargs):
        """Log when a tool ends."""
        logger.info(f"\nTool Output: {output}")
        
    def on_tool_error(self, error, **kwargs):
        """Log when a tool errors."""
        logger.error(f"\nTool Error: {str(error)}")

    def on_chain_start(self, serialized, inputs, **kwargs):
        """Log when a chain starts."""
        logger.info(f"\nChain Start: {serialized.get('name', 'Unknown Chain')}")
        logger.info(f"Inputs: {json.dumps(inputs, indent=2)}")

    def on_chain_end(self, outputs, **kwargs):
        """Log when a chain ends."""
        logger.info(f"\nChain Output:")
        logger.info(f"Outputs: {json.dumps(outputs, indent=2)}")

    def on_agent_action(self, action, **kwargs):
        """Log agent actions."""
        logger.info(f"\nAgent Action:")
        logger.info(f"Tool: {action.tool}")
        logger.info(f"Input: {action.tool_input}")
        logger.info(f"Thought: {action.log}")

    def on_agent_finish(self, finish, **kwargs):
        """Log agent finish."""
        logger.info(f"\nAgent Finish:")
        logger.info(f"Output: {finish.return_values}")
        logger.info(f"Log: {finish.log}")


# Create prompt template for the agent
AGENT_PROMPT = PromptTemplate.from_template(
    """You are a Restaurant Recommender, a helpful assistant that helps users find great restaurants. You help users by:
    - Finding restaurants based on location, cuisine, and preferences
    - Providing restaurant recommendations
    - Searching for specific types of food or dining experiences
    - Offering information about restaurants and dining options
    
    When users ask questions about restaurants, provide detailed and helpful responses that include:
    1. Restaurant names and descriptions
    2. Location and contact information if available
    3. Cuisine types and specialties
    4. Price ranges and dining atmosphere
    5. Any relevant ratings or reviews
    
    For restaurant searches, always:
    1. Consider the user's location preferences
    2. Match their cuisine or food type requests
    3. Take into account any dietary restrictions
    4. Suggest appropriate price ranges
    5. Provide multiple options when possible
    
    You have access to the following tools:
    
    {tools}
    
    Use the following format:
    
    Question: the input question you must answer
    Thought: you should always think about what to do
    Action: the action to take, should be one of [{tool_names}]
    Action Input: the input to the action
    Observation: the result of the action
    ... (this Thought/Action/Action Input/Observation can repeat N times)
    Thought: I now know the final answer
    Final Answer: the final answer to the original input question
    
    Begin!
    
    Question: {input}
    Thought:{agent_scratchpad}"""
)


class AgentState(BaseModel):
    """State of the agent.
    
    Attributes:
        messages: List of message dictionaries
        thread_id: Unique identifier for the conversation
        output: Optional output from the agent
    """
    messages: List[Dict[str, str]]
    thread_id: str
    output: Optional[str] = None


class RestaurantRecommenderAgent:
    """RestaurantRecommender agent for optimizing staking rewards.
    
    This agent uses LangChain's function calling and React framework to handle
    staking operations. It processes natural language commands into strongly-typed
    command models and executes them using appropriate tools.
    
    Attributes:
        llm: Language model for agent
        character: Agent character definition
        validator: Safety validator
        operations: Restaurant operations handler
        command_parser: Command parser for natural language input
        tools: List of available tools
        agent: React agent instance
        agent_executor: Agent executor instance
    """

    def __init__(
        self,
        model_name: str = "openai/gpt-4o-2024-11-20",

        temperature: float = 0.7,
        command_parser: Optional[CommandParser] = None,
        safety_validator: Optional[SafetyValidator] = None,
    ):
        """Initialize the RestaurantRecommender agent.

        Args:
            model_name: Name of the OpenAI model to use
            temperature: Temperature setting for the model
            command_parser: Optional command parser instance
            safety_validator: Optional safety validator instance
        """
        # Load environment variables
        load_dotenv()

        # Initialize components
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            callbacks=[OpenAILoggingHandler()],
            base_url=os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
        )
        
        

        self.character = RestaurantRecommenderCharacter()       
        self.validator = safety_validator or SafetyValidator()
        self.operations = RestaurantOperations()
        self.command_parser = command_parser or CommandParser()
        
        # Create agent with tools
        self.tools = self._get_tools()
        self.agent = create_react_agent(self.llm, self.tools, AGENT_PROMPT)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            handle_parsing_errors=True,  # Handle cases where LLM output includes both action and final answer
            async_mode=True  # Enable async mode
        )

    def _get_tools(self):
        """Get the list of tools available to the agent.
    
        Returns:
            List of LangChain tools for restaurant operations.
        """
        return get_restaurant_tools()

    def _validate_request(self, state: AgentState) -> bool:
        """Validate a user request.

        Args:
            state: Current agent state

        Returns:
            Whether the request is valid
        """
        request = state.messages[-1]["content"]
        is_valid, reason = self.validator.validate_request(request)
        if not is_valid:
            state.output = reason
        return is_valid

    async def invoke(self, state: AgentState) -> AgentState:
        """Invoke the agent.

        Args:
            state: Initial agent state

        Returns:
            Final agent state
        """
        try:
            if not self._validate_request(state):
                error_message = self.validator.get_last_error_message()
                state.output = error_message
                return state

            # Convert state to format expected by agent
            input_dict = {
                "input": state.messages[0]["content"],
                "agent_scratchpad": "",
                "tools": "\n".join(f"{tool.name}: {tool.description}" for tool in self.tools),
                "tool_names": ", ".join(tool.name for tool in self.tools)
            }

            # Run agent
            response = await self.agent_executor.ainvoke(input_dict)
            state.output = response["output"]
            return state
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            logger.error(error_msg)
            state.output = error_msg
            return state

    async def handle_request(self, request: str) -> AgentResponse:
        """Handle a user request.
        
        Args:
            request: User's request string
            
        Returns:
            AgentResponse containing the result
        """
        try:
            # Parse request into command
            command = self.command_parser.parse_request(request)
            logger.info(f"Parsed command type: {type(command)}")
            
            # Execute command
            if isinstance(command, InformationalCommand) and command.topic == "help":
                help_msg = """I can help you find great restaurants! I can:

- Search for restaurants by location and cuisine
- Find popular dining spots  
- Recommend places based on your preferences
- Provide restaurant details and information
- Help with specific food cravings like "best butter chicken"

Just ask me what you're looking for!"""
                return AgentResponse(success=True, message=help_msg)
            
            return await self.execute_command(command)
            
        except Exception as e:
            logger.error(f"Error handling request: {str(e)}", exc_info=True)
            return AgentResponse(
                success=False,
                message=str(e),
                error=str(e)
            )

    async def execute_command(self, command) -> AgentResponse:
        """Execute a parsed command.
        
        Args:
            command: The command to execute
            
        Returns:
            AgentResponse: Response with success status and message
        """
        try:
            if isinstance(command, SearchCommand):
                # Execute restaurant search
                query = command.search_query
                logger.info(f"Executing search command: query='{query.query}', place='{query.place}'")
                
                # For now, return a mock response with the parsed information
                response_msg = f"🔍 **Searching for restaurants...**\n\n"
                response_msg += f"**Query:** {query.query}\n"
                
                if query.place:
                    response_msg += f"**Location:** {query.place}\n"
                if query.cuisine:
                    response_msg += f"**Cuisine:** {query.cuisine}\n"
                if query.price_range:
                    response_msg += f"**Price Range:** {query.price_range}\n"
                if query.dietary_restrictions:
                    response_msg += f"**Dietary Restrictions:** {query.dietary_restrictions}\n"
                
                # Mock restaurant results based on the query
                if "butter chicken" in query.query.lower():
                    response_msg += f"\n🍽️ **Top Results:**\n\n"
                    response_msg += f"1. **Karim's** - {query.place or 'Delhi'}\n"
                    response_msg += f"   ⭐ 4.2/5 | Indian Cuisine | Moderate Price\n"
                    response_msg += f"   Famous for authentic butter chicken and mughlai cuisine\n\n"
                    
                    response_msg += f"2. **Punjabi By Nature** - {query.place or 'Multiple Locations'}\n"
                    response_msg += f"   ⭐ 4.0/5 | North Indian | Mid-Range\n"
                    response_msg += f"   Known for rich, creamy butter chicken\n\n"
                    
                    response_msg += f"3. **Moti Mahal Delux** - {query.place or 'Delhi'}\n"
                    response_msg += f"   ⭐ 4.1/5 | Indian | Moderate\n"
                    response_msg += f"   Legendary restaurant, birthplace of butter chicken\n"
                else:
                    # Generic restaurant search response
                    response_msg += f"\n🍽️ **Found restaurants matching your search!**\n\n"
                    response_msg += f"Here are some great options in {query.place or 'your area'} for {query.query}.\n"
                    response_msg += f"I'd be happy to provide more specific recommendations if you can tell me more about what you're looking for!"
                
                return AgentResponse(success=True, message=response_msg)
                
            elif isinstance(command, RecommendationCommand):
                # Execute restaurant recommendation
                query = command.recommendation_query
                logger.info(f"Executing recommendation command: query='{query.query}', place='{query.place}'")
                
                response_msg = f"🎯 **Restaurant Recommendations**\n\n"
                response_msg += f"Based on your request: '{query.query}'\n"
                
                if query.place:
                    response_msg += f"Location: {query.place}\n\n"
                
                response_msg += f"Here are some great options I'd recommend:\n\n"
                response_msg += f"• Look for highly-rated local favorites\n"
                response_msg += f"• Consider trying authentic cuisine specific to {query.place or 'the area'}\n"
                response_msg += f"• Check recent reviews for current quality\n\n"
                response_msg += f"Would you like me to search for something more specific?"
                
                return AgentResponse(success=True, message=response_msg)
                
            elif isinstance(command, InformationalCommand):
                # Handle info request
                if command.topic == "help":
                    # Return a more detailed help message
                    help_msg = """I can help you find great restaurants! I can:

- Search for restaurants by location and cuisine
- Find popular dining spots  
- Recommend places based on your preferences
- Provide restaurant details and information
- Help with specific food cravings like "best butter chicken"

Just ask me what you're looking for!"""
                    return AgentResponse(success=True, message=help_msg)
                else:
                    return AgentResponse(success=True, message=self.character.format_response(command.topic))
                
            else:
                return AgentResponse(
                    success=False,
                    message=f"Unknown command type: {type(command)}",
                    error="Invalid command type"
                )
                
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            return AgentResponse(success=False, message=str(e), error=str(e))

