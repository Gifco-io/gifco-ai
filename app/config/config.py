"""Configuration settings for the Restaurant Recommender AI application."""
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class OpenAIConfig:
    """OpenAI/Language Model configuration."""
    
    # Model settings
    MODEL_NAME: str = os.getenv("OPENAI_MODEL_NAME", "openai/gpt-4o-2024-11-20")
    BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Agent settings
    AGENT_TEMPERATURE: float = float(os.getenv("AGENT_TEMPERATURE", "0.7"))
    PARSER_TEMPERATURE: float = float(os.getenv("PARSER_TEMPERATURE", "0.0"))
    
    # Request settings
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "4000"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "60"))


class RestaurantAPIConfig:
    """Restaurant API configuration."""
    
    # Server settings
    SERVER_URL: str = os.getenv("RESTAURANT_SERVER_URL", "http://localhost:8000")
    API_ENDPOINT: str = "/api/questions"
    
    # Default search settings
    DEFAULT_LOCATION: str = os.getenv("DEFAULT_LOCATION", "New Delhi")
    DEFAULT_QUERY_TYPE: str = os.getenv("DEFAULT_QUERY_TYPE", "current")
    
    # Request settings
    API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "30"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))


class AgentConfig:
    """Agent behavior configuration."""
    
    # Agent settings
    HANDLE_PARSING_ERRORS: bool = os.getenv("HANDLE_PARSING_ERRORS", "true").lower() == "true"
    ASYNC_MODE: bool = os.getenv("ASYNC_MODE", "true").lower() == "true"
    
    # Safety settings
    ENABLE_SAFETY_VALIDATION: bool = os.getenv("ENABLE_SAFETY_VALIDATION", "true").lower() == "true"
    MAX_CONVERSATION_LENGTH: int = int(os.getenv("MAX_CONVERSATION_LENGTH", "50"))
    
    # Response settings
    MAX_RESPONSE_LENGTH: int = int(os.getenv("MAX_RESPONSE_LENGTH", "2000"))
    INCLUDE_DEBUG_INFO: bool = os.getenv("INCLUDE_DEBUG_INFO", "false").lower() == "true"


class LoggingConfig:
    """Logging configuration."""
    
    # Log levels
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # Log destinations
    LOG_TO_FILE: bool = os.getenv("LOG_TO_FILE", "false").lower() == "true"
    LOG_FILE_PATH: str = os.getenv("LOG_FILE_PATH", "logs/app.log")
    LOG_TO_CONSOLE: bool = os.getenv("LOG_TO_CONSOLE", "true").lower() == "true"
    
    # Detailed logging flags
    LOG_OPENAI_REQUESTS: bool = os.getenv("LOG_OPENAI_REQUESTS", "true").lower() == "true"
    LOG_API_CALLS: bool = os.getenv("LOG_API_CALLS", "true").lower() == "true"
    LOG_COMMAND_PARSING: bool = os.getenv("LOG_COMMAND_PARSING", "true").lower() == "true"


class ApplicationConfig:
    """Main application configuration."""
    
    # Application info
    APP_NAME: str = "Restaurant Recommender AI"
    APP_VERSION: str = "1.0.0"
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Server settings (if running as web service)
    HOST: str = os.getenv("HOST", "localhost")
    PORT: int = int(os.getenv("PORT", "8080"))


class LocationConfig:
    """Location and place name configuration."""
    
    # Place name mappings for API consistency
    PLACE_MAPPINGS: Dict[str, str] = {
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
    
    # Supported locations
    SUPPORTED_LOCATIONS: List[str] = list(PLACE_MAPPINGS.values())


class MessageConfig:
    """Message and response templates configuration."""
    
    # Default messages
    HELP_MESSAGE: str = """I can help you find great restaurants! I can:

- Search for restaurants by location and cuisine
- Find popular dining spots  
- Recommend places based on your preferences
- Provide restaurant details and information
- Help with specific food cravings like "best butter chicken"

Just ask me what you're looking for!"""
    
    ERROR_MESSAGE: str = "I'm sorry, I encountered an error while processing your request. Please try again."
    
    # Response formatting
    SEARCH_HEADER: str = "🔍 **Searching for restaurants...**"
    RECOMMENDATION_HEADER: str = "🎯 **Restaurant Recommendations**"
    
    # Emoji settings
    USE_EMOJIS: bool = os.getenv("USE_EMOJIS", "true").lower() == "true"


class ToolConfig:
    """Tool configuration settings."""
    
    # Available tools
    ENABLE_SEARCH_TOOL: bool = os.getenv("ENABLE_SEARCH_TOOL", "true").lower() == "true"
    ENABLE_RECOMMENDATION_TOOL: bool = os.getenv("ENABLE_RECOMMENDATION_TOOL", "true").lower() == "true"
    ENABLE_HELP_TOOL: bool = os.getenv("ENABLE_HELP_TOOL", "true").lower() == "true"
    
    # Tool settings
    TOOL_TIMEOUT: int = int(os.getenv("TOOL_TIMEOUT", "30"))
    MAX_TOOL_RETRIES: int = int(os.getenv("MAX_TOOL_RETRIES", "2"))


# Configuration instances for easy import
openai_config = OpenAIConfig()
restaurant_api_config = RestaurantAPIConfig()
agent_config = AgentConfig()
logging_config = LoggingConfig()
app_config = ApplicationConfig()
location_config = LocationConfig()
message_config = MessageConfig()
tool_config = ToolConfig()


def get_all_config() -> Dict[str, any]:
    """Get all configuration as a dictionary.
    
    Returns:
        Dictionary containing all configuration settings
    """
    return {
        "openai": {
            "model_name": openai_config.MODEL_NAME,
            "base_url": openai_config.BASE_URL,
            "agent_temperature": openai_config.AGENT_TEMPERATURE,
            "parser_temperature": openai_config.PARSER_TEMPERATURE,
            "max_tokens": openai_config.MAX_TOKENS,
            "request_timeout": openai_config.REQUEST_TIMEOUT
        },
        "restaurant_api": {
            "server_url": restaurant_api_config.SERVER_URL,
            "api_endpoint": restaurant_api_config.API_ENDPOINT,
            "default_location": restaurant_api_config.DEFAULT_LOCATION,
            "default_query_type": restaurant_api_config.DEFAULT_QUERY_TYPE,
            "api_timeout": restaurant_api_config.API_TIMEOUT,
            "max_retries": restaurant_api_config.MAX_RETRIES
        },
        "agent": {
            "handle_parsing_errors": agent_config.HANDLE_PARSING_ERRORS,
            "async_mode": agent_config.ASYNC_MODE,
            "enable_safety_validation": agent_config.ENABLE_SAFETY_VALIDATION,
            "max_conversation_length": agent_config.MAX_CONVERSATION_LENGTH,
            "max_response_length": agent_config.MAX_RESPONSE_LENGTH,
            "include_debug_info": agent_config.INCLUDE_DEBUG_INFO
        },
        "logging": {
            "log_level": logging_config.LOG_LEVEL,
            "log_format": logging_config.LOG_FORMAT,
            "log_to_file": logging_config.LOG_TO_FILE,
            "log_file_path": logging_config.LOG_FILE_PATH,
            "log_to_console": logging_config.LOG_TO_CONSOLE,
            "log_openai_requests": logging_config.LOG_OPENAI_REQUESTS,
            "log_api_calls": logging_config.LOG_API_CALLS,
            "log_command_parsing": logging_config.LOG_COMMAND_PARSING
        },
        "application": {
            "app_name": app_config.APP_NAME,
            "app_version": app_config.APP_VERSION,
            "environment": app_config.ENVIRONMENT,
            "debug": app_config.DEBUG,
            "host": app_config.HOST,
            "port": app_config.PORT
        },
        "location": {
            "place_mappings": location_config.PLACE_MAPPINGS,
            "supported_locations": location_config.SUPPORTED_LOCATIONS
        },
        "messages": {
            "help_message": message_config.HELP_MESSAGE,
            "error_message": message_config.ERROR_MESSAGE,
            "search_header": message_config.SEARCH_HEADER,
            "recommendation_header": message_config.RECOMMENDATION_HEADER,
            "use_emojis": message_config.USE_EMOJIS
        },
        "tools": {
            "enable_search_tool": tool_config.ENABLE_SEARCH_TOOL,
            "enable_recommendation_tool": tool_config.ENABLE_RECOMMENDATION_TOOL,
            "enable_help_tool": tool_config.ENABLE_HELP_TOOL,
            "tool_timeout": tool_config.TOOL_TIMEOUT,
            "max_tool_retries": tool_config.MAX_TOOL_RETRIES
        }
    }


def validate_config() -> List[str]:
    """Validate configuration settings.
    
    Returns:
        List of validation errors (empty if all valid)
    """
    errors = []
    
    # Check required environment variables
    if not openai_config.API_KEY:
        errors.append("OPENAI_API_KEY is not set")
    
    # Validate numeric ranges
    if not (0.0 <= openai_config.AGENT_TEMPERATURE <= 2.0):
        errors.append("AGENT_TEMPERATURE must be between 0.0 and 2.0")
    
    if not (0.0 <= openai_config.PARSER_TEMPERATURE <= 2.0):
        errors.append("PARSER_TEMPERATURE must be between 0.0 and 2.0")
    
    if openai_config.MAX_TOKENS <= 0:
        errors.append("MAX_TOKENS must be positive")
    
    if restaurant_api_config.API_TIMEOUT <= 0:
        errors.append("API_TIMEOUT must be positive")
    
    if app_config.PORT <= 0 or app_config.PORT > 65535:
        errors.append("PORT must be between 1 and 65535")
    
    return errors


def print_config():
    """Print current configuration (for debugging)."""
    import json
    config = get_all_config()
    print(json.dumps(config, indent=2))


if __name__ == "__main__":
    # Validate and print config when run directly
    errors = validate_config()
    if errors:
        print("Configuration validation errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Configuration is valid!")
    
    print("\nCurrent configuration:")
    print_config()
