"""Command function definitions for restaurant operations."""
from typing import List, Dict, Any


def get_command_functions() -> List[Dict[str, Any]]:
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
                "description": "Create a new empty restaurant collection. Use this when the user wants to create a curated list of restaurants with a name, description, tags, and privacy settings, but WITHOUT adding specific restaurants.",
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
                "name": "create_collection_with_restaurants",
                "description": "Create a restaurant collection and add specific restaurants to it. Use this ONLY when the user wants to create a collection FROM previously found/searched restaurants (like 'create collection from these results' or 'save these restaurants as collection'). Do NOT use this for general collection creation requests.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the collection (e.g., 'Best Pizza Places from Search', 'My Favorites')"
                        },
                        "description": {
                            "type": "string",
                            "description": "Description of the collection (e.g., 'A collection of restaurants from my recent search')"
                        },
                        "is_public": {
                            "type": "boolean",
                            "description": "Whether the collection should be public (true) or private (false). Default is true."
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of tags for the collection (e.g., ['search_results', 'curated', 'favorites'])"
                        },
                        "restaurant_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of restaurant IDs to add to the collection. These should be from previous search results."
                        },
                        "auth_token": {
                            "type": "string",
                            "description": "Authorization token for creating the collection"
                        }
                    },
                    "required": ["name", "description", "restaurant_ids", "auth_token"]
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