"""Restaurant-specific memory implementation following LangChain hierarchy."""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import PromptTemplate
from pydantic import Field

from .base_memory import RestaurantBaseChatMemory
from ..api.models.responses import RestaurantInfo

logger = logging.getLogger(__name__)


class RestaurantMemory(RestaurantBaseChatMemory):
    """Advanced restaurant-specific memory with context enhancement and smart retrieval."""
    
    max_messages_per_thread: int = Field(default=50)
    max_context_age_hours: int = Field(default=24) 
    enable_preference_learning: bool = Field(default=True)
    
    def __init__(self, **kwargs):
        """Initialize the restaurant memory system."""
        super().__init__(**kwargs)
        logger.info("RestaurantMemory initialized with advanced features")
    
    def add_user_message(self, thread_id: str, content: str, **metadata) -> None:
        """Add a user message with automatic preference learning."""
        message = HumanMessage(content=content)
        if metadata:
            message.additional_kwargs = metadata
        
        self.add_message_to_thread(thread_id, message)
        
        if self.enable_preference_learning:
            self._learn_preferences_from_message(thread_id, content)
        
        logger.debug(f"Added user message to thread {thread_id}")
    
    def add_ai_message(self, thread_id: str, content: str, **metadata) -> None:
        """Add an AI message with metadata."""
        message = AIMessage(content=content)
        if metadata:
            message.additional_kwargs = metadata
            
        self.add_message_to_thread(thread_id, message)
        
        logger.debug(f"Added AI message to thread {thread_id}")
    
    def get_enhanced_context_for_llm(self, thread_id: str) -> str:
        """Get enhanced context string optimized for LLM consumption."""
        context_parts = []
        
        # Add conversation summary
        summary = self.get_conversation_summary(thread_id, 10)
        if summary != "No previous conversation.":
            context_parts.append(f"Recent Conversation:\n{summary}")
        
        # Add restaurant context
        last_restaurants, last_query = self.get_last_restaurants(thread_id)
        if last_restaurants:
            context_parts.append(f"\nPrevious Restaurant Search:")
            context_parts.append(f"Query: {last_query}")
            context_parts.append(f"Found {len(last_restaurants)} restaurants")
        
        return "\n".join(context_parts) if context_parts else "No previous context available."
    
    def create_collection_context(self, thread_id: str, auth_token: str) -> str:
        """Create enhanced context specifically for collection creation requests."""
        last_restaurants, last_query = self.get_last_restaurants(thread_id)
        
        if not last_restaurants:
            return "No recent restaurant search results available for collection creation."
        
        # Format restaurant IDs - extract from description field where IDs are stored as "ID:actual_id|..."
        restaurant_ids = []
        for r in last_restaurants:
            if r.description and r.description.startswith("ID:"):
                # Extract actual ID from "ID:actual_id|other_description" format
                id_part = r.description.split("|")[0].replace("ID:", "").strip()
                restaurant_ids.append(f'"{id_part}"')
            else:
                # Fallback to name-based ID if no actual ID available
                restaurant_ids.append(f'"{r.name.replace(" ", "_").lower()}"')
        
        restaurant_ids_str = "[" + ", ".join(restaurant_ids) + "]"
        
        # Format restaurant details
        restaurant_details = []
        cuisines = set()
        locations = set()
        for i, restaurant in enumerate(last_restaurants[:10], 1):
            details = f"{i}. {restaurant.name}"
            if hasattr(restaurant, 'cuisine') and restaurant.cuisine:
                details += f" - {restaurant.cuisine}"
                cuisines.add(restaurant.cuisine)
            if hasattr(restaurant, 'location') and restaurant.location:
                details += f" in {restaurant.location}"
                locations.add(restaurant.location)
            restaurant_details.append(details)
        
        # Generate collection name suggestions based on context
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        
        context = f"""
COLLECTION CREATION CONTEXT:

Previous Search Query: {last_query or "restaurant search"}
Available Restaurants: {len(last_restaurants)} restaurants found
Cuisines Found: {', '.join(cuisines) if cuisines else 'Mixed'}
Locations: {', '.join(locations) if locations else 'Various'}

Restaurant IDs for Collection:
{restaurant_ids_str}

Restaurant Details:
{chr(10).join(restaurant_details)}

User Auth Token: {auth_token}

COLLECTION NAME GENERATION:
Generate a unique, descriptive collection name based on:
- Search query: "{last_query}"
- Cuisines: {list(cuisines)}
- Locations: {list(locations)}
- Timestamp for uniqueness: {timestamp}

Examples of good collection names:
- "Italian Gems in Delhi - {timestamp}"
- "Best Pizza Spots Found {timestamp}"
- "Romantic Dinner Collection - {timestamp}"
- "Budget Friendly Eats {timestamp}"

Instructions:
- Use the create_collection_with_restaurants tool
- Generate a UNIQUE collection name that won't conflict with existing collections
- Include timestamp or unique identifier in the name
- Base the name on the search context and restaurant types
- Include ALL restaurant IDs listed above
- Set is_public to true unless specified otherwise
- Add relevant tags like ["user_created", "restaurant_search"]
"""
        return context
    
    def get_context_for_agent(self, thread_id: str, message: str, auth_token: Optional[str] = None) -> str:
        """Get context optimized for agent consumption."""
        # Check if this is a collection creation request
        if self._is_collection_request(message) and auth_token:
            return self.create_collection_context(thread_id, auth_token)
        
        # Regular context for other requests
        return self.get_enhanced_context_for_llm(thread_id)
    
    def update_restaurant_search_context(self, thread_id: str, restaurants: List[RestaurantInfo], 
                                       query: str, search_metadata: Optional[Dict] = None) -> None:
        """Update context after a restaurant search with enhanced metadata."""
        # Store restaurants using parent method
        self.set_last_restaurants(thread_id, restaurants, query)
        
        # Add search metadata
        if search_metadata:
            context = self.get_thread_context(thread_id)
            if "search_metadata" not in context:
                context["search_metadata"] = []
            
            context["search_metadata"].append({
                "query": query,
                "results_count": len(restaurants),
                "timestamp": datetime.now().isoformat(),
                **search_metadata
            })
        
        logger.info(f"Updated search context for thread {thread_id}: {len(restaurants)} restaurants")
    
    def get_memory_stats(self, thread_id: str) -> Dict[str, Any]:
        """Get statistics about the memory for a thread."""
        messages = self.get_thread_messages(thread_id)
        context = self.get_thread_context(thread_id)
        
        return {
            "message_count": len(messages),
            "last_activity": context.get("updated_at"),
            "search_count": len(context.get("search_history", [])),
            "has_restaurants": len(context.get("last_restaurants", [])) > 0,
            "preference_count": len(context.get("preferences", {}))
        }
    
    def _learn_preferences_from_message(self, thread_id: str, message: str) -> None:
        """Automatically learn user preferences from messages."""
        message_lower = message.lower()
        
        # Learn cuisine preferences
        cuisines = ["italian", "chinese", "indian", "mexican", "japanese"]
        for cuisine in cuisines:
            if cuisine in message_lower:
                current_prefs = self.get_user_preference(thread_id, "preferred_cuisines", [])
                if cuisine not in current_prefs:
                    current_prefs.append(cuisine)
                    self.set_user_preference(thread_id, "preferred_cuisines", current_prefs)
        
        # Learn budget preferences
        if any(word in message_lower for word in ["cheap", "budget", "affordable"]):
            self.set_user_preference(thread_id, "budget_conscious", True)
    
    def _is_collection_request(self, message: str) -> bool:
        """Check if a message is requesting collection creation."""
        collection_keywords = [
            "create collection", "make collection", "save collection", 
            "add to collection", "create a list", "make a list",
            "save these", "add these", "collection"
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in collection_keywords)
    
    @property
    def memory_variables(self) -> List[str]:
        """Return memory variables that this memory class provides."""
        return [
            "history", "thread_context", "last_restaurants", "conversation_summary",
            "enhanced_context", "user_preferences", "search_history"
        ]
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load comprehensive memory variables from inputs."""
        thread_id = inputs.get("thread_id", "default")
        
        # Get base memory variables
        base_vars = super().load_memory_variables(inputs)
        
        # Add enhanced variables
        enhanced_vars = {
            "enhanced_context": self.get_enhanced_context_for_llm(thread_id),
            "user_preferences": self.get_thread_context(thread_id).get("preferences", {}),
            "search_history": self.get_search_history_summary(thread_id),
            "memory_stats": self.get_memory_stats(thread_id)
        }
        
        # Merge and return
        return {**base_vars, **enhanced_vars} 