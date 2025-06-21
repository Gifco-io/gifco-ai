# LangChain Memory Implementation

## Overview

This implementation follows the LangChain memory hierarchy: **BaseMemory → BaseChatMemory → RestaurantMemory**

## Architecture

### 1. RestaurantBaseChatMemory (Base Layer)

**File**: `app/memory/base_memory.py`

- Extends LangChain's `BaseChatMemory`
- Provides thread-based conversation management
- Restaurant-specific context storage
- Core memory operations

**Key Features**:

- Thread-based conversation history using `InMemoryChatMessageHistory`
- Restaurant context storage with search history
- User preference tracking
- Memory variable management compatible with LangChain

### 2. RestaurantMemory (Implementation Layer)

**File**: `app/memory/restaurant_memory.py`

- Extends `RestaurantBaseChatMemory`
- Advanced restaurant-specific features
- Smart context generation for LLM consumption
- Collection creation context management

**Key Features**:

- Automatic preference learning from user messages
- Enhanced context generation for LLM prompts
- Collection creation context with restaurant IDs
- Restaurant search context management
- Memory statistics and analytics

## Integration Points

### 1. Restaurant Service Integration

**File**: `app/api/services/restaurant_service.py`

- Replaced simple `ConversationMemory` with `RestaurantMemory`
- Updated to use LangChain memory methods:
  - `add_user_message()` instead of `add_message()`
  - `add_ai_message()` instead of `add_message()`
  - `update_restaurant_search_context()` for enhanced search tracking
  - `get_context_for_agent()` for intelligent context generation

### 2. Agent Integration

**File**: `app/agent/base.py`

- Agent now accepts memory instance in constructor
- AgentExecutor configured with memory support
- Context injection into agent prompts
- Thread-aware conversation handling

## Memory Hierarchy Implementation

```
BaseMemory (LangChain)
    ↓
BaseChatMemory (LangChain)
    ↓
RestaurantBaseChatMemory (Custom)
    ↓
RestaurantMemory (Custom)
```

## Key Methods

### RestaurantBaseChatMemory

- `get_thread_history(thread_id)` - Get/create chat history for thread
- `add_message_to_thread(thread_id, message)` - Add message to specific thread
- `get_thread_context(thread_id)` - Get restaurant-specific context
- `set_last_restaurants(thread_id, restaurants, query)` - Store search results
- `get_last_restaurants(thread_id)` - Retrieve search results
- `set_user_preference(thread_id, key, value)` - Store user preferences

### RestaurantMemory

- `add_user_message(thread_id, content)` - Add user message with preference learning
- `add_ai_message(thread_id, content)` - Add AI message
- `get_enhanced_context_for_llm(thread_id)` - Generate LLM-optimized context
- `create_collection_context(thread_id, auth_token)` - Generate collection creation context
- `get_context_for_agent(thread_id, message, auth_token)` - Smart context for agents
- `update_restaurant_search_context()` - Enhanced search context management

## Memory Variables

The memory system provides these variables to LangChain components:

- `history` - Message history for the thread
- `thread_context` - Restaurant-specific context
- `last_restaurants` - Recent restaurant search results
- `conversation_summary` - Summarized conversation history
- `enhanced_context` - LLM-optimized context string
- `user_preferences` - Learned user preferences
- `search_history` - Summary of recent searches
- `memory_stats` - Memory usage statistics

## Features

### 1. Automatic Preference Learning

- Cuisine preferences from user messages
- Budget consciousness detection
- Location preferences

### 2. Smart Context Generation

- Conversation summarization
- Restaurant search history
- User preference integration
- Collection creation context

### 3. Thread Management

- Multi-conversation support
- Context isolation per thread
- Message history management
- Search result tracking

### 4. LangChain Compatibility

- Full integration with LangChain agents
- Memory variable loading
- Context saving and loading
- Standard LangChain memory interface

## Testing

Run the test suite to verify the implementation:

```bash
python test_langchain_memory.py
```

The test suite validates:

- ✅ Basic message handling
- ✅ Restaurant context storage
- ✅ Enhanced context generation
- ✅ Collection context creation
- ✅ Memory variable loading
- ✅ Preference learning
- ✅ Memory statistics
- ✅ Agent context generation

## Usage Example

```python
from app.memory import RestaurantMemory

# Initialize memory
memory = RestaurantMemory()

# Add conversation messages
memory.add_user_message("thread_123", "Find Italian restaurants in Delhi")
memory.add_ai_message("thread_123", "I found 5 great Italian places!")

# Store restaurant search results
restaurants = [...]  # List of RestaurantInfo objects
memory.update_restaurant_search_context("thread_123", restaurants, "Italian restaurants in Delhi")

# Get enhanced context for LLM
context = memory.get_enhanced_context_for_llm("thread_123")

# Get collection creation context
collection_context = memory.get_context_for_agent("thread_123", "Create a collection", "auth_token")
```

## Benefits

1. **Conversation Continuity**: Maintains context across multiple interactions
2. **Smart Context**: Provides relevant information to LLMs for better responses
3. **Preference Learning**: Automatically learns user preferences over time
4. **Collection Support**: Seamless collection creation from search results
5. **LangChain Integration**: Full compatibility with LangChain ecosystem
6. **Thread Safety**: Supports multiple concurrent conversations
7. **Extensible**: Easy to add new memory features and capabilities

## Memory Hierarchy Compliance

This implementation strictly follows the LangChain memory hierarchy:

- **BaseMemory**: Core memory interface and variables
- **BaseChatMemory**: Chat-specific memory with message history
- **RestaurantMemory**: Domain-specific memory with restaurant features

The implementation maintains full compatibility with LangChain agents, chains, and other components while providing restaurant-specific enhancements.
