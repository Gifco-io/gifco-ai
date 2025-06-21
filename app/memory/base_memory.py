"""Base chat memory implementation for restaurant recommender system."""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import logging

from langchain.memory.chat_memory import BaseChatMemory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.chat_history import InMemoryChatMessageHistory
from pydantic import Field

from ..api.models.responses import RestaurantInfo

logger = logging.getLogger(__name__)


class RestaurantBaseChatMemory(BaseChatMemory):
    """Base chat memory class for restaurant recommender with enhanced context storage.
    
    Extends LangChain's BaseChatMemory to add restaurant-specific functionality:
    - Store and retrieve restaurant search results
    - Maintain conversation context across sessions
    - Support thread-based conversations
    """
    
    # Restaurant-specific storage
    restaurant_context: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    conversation_threads: Dict[str, InMemoryChatMessageHistory] = Field(default_factory=dict)
    
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
    
    def __init__(self, **kwargs):
        """Initialize the base chat memory."""
        super().__init__(**kwargs)
        self.restaurant_context = {}
        self.conversation_threads = {}
        logger.info("RestaurantBaseChatMemory initialized")
    
    def get_thread_history(self, thread_id: str) -> InMemoryChatMessageHistory:
        """Get or create chat message history for a specific thread."""
        if thread_id not in self.conversation_threads:
            self.conversation_threads[thread_id] = InMemoryChatMessageHistory()
            logger.debug(f"Created new chat history for thread: {thread_id}")
        return self.conversation_threads[thread_id]
    
    def add_message_to_thread(self, thread_id: str, message: BaseMessage) -> None:
        """Add a message to a specific conversation thread."""
        history = self.get_thread_history(thread_id)
        history.add_message(message)
        logger.debug(f"Added message to thread {thread_id}: {type(message).__name__}")
    
    def get_thread_messages(self, thread_id: str) -> List[BaseMessage]:
        """Get all messages from a specific conversation thread."""
        history = self.get_thread_history(thread_id)
        return history.messages
    
    def clear_thread(self, thread_id: str) -> None:
        """Clear all messages and context for a specific thread."""
        if thread_id in self.conversation_threads:
            self.conversation_threads[thread_id].clear()
        if thread_id in self.restaurant_context:
            del self.restaurant_context[thread_id]
        logger.info(f"Cleared thread: {thread_id}")
    
    def get_thread_context(self, thread_id: str) -> Dict[str, Any]:
        """Get restaurant context for a specific thread."""
        if thread_id not in self.restaurant_context:
            self.restaurant_context[thread_id] = {
                "last_restaurants": [],
                "last_query": None,
                "search_history": [],
                "preferences": {},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        return self.restaurant_context[thread_id]
    
    def update_thread_context(self, thread_id: str, **kwargs) -> None:
        """Update restaurant context for a specific thread."""
        context = self.get_thread_context(thread_id)
        context.update(kwargs)
        context["updated_at"] = datetime.now().isoformat()
        logger.debug(f"Updated context for thread {thread_id}: {list(kwargs.keys())}")
    
    def set_last_restaurants(self, thread_id: str, restaurants: List[RestaurantInfo], query: str) -> None:
        """Store the last restaurant search results for a thread."""
        context = self.get_thread_context(thread_id)
        context["last_restaurants"] = restaurants
        context["last_query"] = query
        
        # Add to search history
        if "search_history" not in context:
            context["search_history"] = []
        
        context["search_history"].append({
            "query": query,
            "restaurant_count": len(restaurants),
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 10 searches
        if len(context["search_history"]) > 10:
            context["search_history"] = context["search_history"][-10:]
        
        context["updated_at"] = datetime.now().isoformat()
        logger.info(f"Stored {len(restaurants)} restaurants for thread {thread_id}, query: {query}")
    
    def get_last_restaurants(self, thread_id: str) -> tuple[List[RestaurantInfo], Optional[str]]:
        """Get the last restaurant search results for a thread."""
        context = self.get_thread_context(thread_id)
        restaurants = context.get("last_restaurants", [])
        query = context.get("last_query")
        logger.debug(f"Retrieved {len(restaurants)} restaurants for thread {thread_id}")
        return restaurants, query
    
    def set_user_preference(self, thread_id: str, key: str, value: Any) -> None:
        """Set a user preference for a specific thread."""
        context = self.get_thread_context(thread_id)
        if "preferences" not in context:
            context["preferences"] = {}
        context["preferences"][key] = value
        context["updated_at"] = datetime.now().isoformat()
        logger.debug(f"Set preference for thread {thread_id}: {key} = {value}")
    
    def get_user_preference(self, thread_id: str, key: str, default: Any = None) -> Any:
        """Get a user preference for a specific thread."""
        context = self.get_thread_context(thread_id)
        return context.get("preferences", {}).get(key, default)
    
    def get_conversation_summary(self, thread_id: str, max_messages: int = 5) -> str:
        """Get a summary of recent conversation messages."""
        messages = self.get_thread_messages(thread_id)
        if not messages:
            return "No previous conversation."
        
        # Get last N messages
        recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages
        
        summary_parts = []
        for msg in recent_messages:
            role = "Human" if isinstance(msg, HumanMessage) else "Assistant"
            content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            summary_parts.append(f"{role}: {content}")
        
        return "\n".join(summary_parts)
    
    def get_search_history_summary(self, thread_id: str, max_searches: int = 3) -> str:
        """Get a summary of recent restaurant searches."""
        context = self.get_thread_context(thread_id)
        search_history = context.get("search_history", [])
        
        if not search_history:
            return "No previous searches."
        
        recent_searches = search_history[-max_searches:] if len(search_history) > max_searches else search_history
        
        summary_parts = []
        for search in recent_searches:
            summary_parts.append(f"- {search['query']} ({search['restaurant_count']} results)")
        
        return "\n".join(summary_parts)
    
    @property 
    def memory_variables(self) -> List[str]:
        """Return memory variables that this memory class provides."""
        return ["history", "thread_context", "last_restaurants", "conversation_summary"]
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load memory variables from inputs."""
        thread_id = inputs.get("thread_id", "default")
        
        # Get conversation messages
        messages = self.get_thread_messages(thread_id)
        history = self.chat_memory.messages if hasattr(self, 'chat_memory') else messages
        
        # Get restaurant context
        last_restaurants, last_query = self.get_last_restaurants(thread_id)
        
        # Get conversation summary
        conversation_summary = self.get_conversation_summary(thread_id)
        
        return {
            "history": history,
            "thread_context": self.get_thread_context(thread_id),
            "last_restaurants": last_restaurants,
            "last_query": last_query,
            "conversation_summary": conversation_summary
        }
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """Save context from the conversation."""
        thread_id = inputs.get("thread_id", "default")
        
        # Save human message
        if "input" in inputs:
            human_message = HumanMessage(content=inputs["input"])
            self.add_message_to_thread(thread_id, human_message)
        
        # Save AI message
        if "output" in outputs:
            ai_message = AIMessage(content=outputs["output"])
            self.add_message_to_thread(thread_id, ai_message)
        
        logger.debug(f"Saved context for thread {thread_id}")
    
    def clear(self) -> None:
        """Clear all memory."""
        self.restaurant_context.clear()
        self.conversation_threads.clear()
        logger.info("Cleared all memory") 