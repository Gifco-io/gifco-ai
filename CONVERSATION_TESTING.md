# Restaurant Conversation Testing

This directory contains comprehensive tests for the restaurant conversation functionality, including memory management, restaurant search, and collection creation.

## Overview

The conversation system enables:

- 🔍 **Restaurant Search**: Users can search for restaurants via natural language queries
- 🧠 **Memory Management**: Conversation context is maintained across interactions
- 📝 **Collection Creation**: Users can create collections from previously searched restaurants
- 💬 **Conversational Flow**: Natural back-and-forth interactions with AI suggestions

## Test Files

### `test_conversation_flow.py`

Comprehensive test suite that covers:

- Complete conversation flow from search to collection creation
- Memory functionality (storing and retrieving conversation context)
- AI message generation (conversational responses)
- Error handling scenarios
- Restaurant data processing

### `run_conversation_tests.py`

Simple runner script that:

- Sets up environment variables
- Runs the complete test suite
- Provides clear output and error handling

## Running the Tests

### Prerequisites

1. Python 3.8+
2. Required dependencies installed (`pip install -r requirements.txt`)
3. Environment variables configured

### Environment Variables

Set these before running tests:

```bash
export OPENAI_API_KEY="your_openai_api_key"
export OPENAI_BASE_URL="https://openrouter.ai/api/v1"  # Optional, defaults to OpenRouter
export RESTAURANT_SERVER_URL="http://dev.gifco.io"    # Optional, defaults to dev server
```

### Running Tests

#### Option 1: Using the runner script (Recommended)

```bash
python run_conversation_tests.py
```

#### Option 2: Direct execution

```bash
python test_conversation_flow.py
```

## Test Scenarios

### 1. Complete Conversation Flow

```
User: "suggest me a good restaurant in new delhi"
-> System searches restaurants
-> AI suggests collection creation
User: "create a collection called 'My Delhi Favorites'"
-> System creates collection with found restaurants
```

### 2. Memory Functionality

- Tests conversation history storage
- Restaurant search result caching
- Context-aware response generation
- Collection request detection

### 3. AI Message Generation

- Conversational response creation
- Fallback message handling
- Restaurant information formatting
- Collection suggestion integration

### 4. Error Handling

- Empty query handling
- Invalid thread ID management
- Timeout protection
- API error responses

## Expected Output

Successful test run will show:

```
🚀 Starting Complete Conversation Tests
===============================================================================
⏰ Start time: 2024-01-XX XX:XX:XX
===============================================================================

🧠 Testing Memory Functionality
===============================================================================
📝 Test 1: Basic memory operations
✅ Messages stored: 2

🍽️ Test 2: Restaurant memory
✅ Restaurants stored and retrieved: 2
📝 Original query: Italian restaurants in Delhi

🔍 Test 3: Collection request detection
✅ 'create a collection' -> Collection request: True
✅ 'make a collection from these' -> Collection request: True
...

🎯 Testing Complete Conversational Flow
===============================================================================
📍 Step 1: Restaurant Query via /query endpoint
✅ Query Success: True
📝 AI Message: Great! I found X restaurants in New Delhi...
🍽️ Restaurants Found: X

💾 Step 2: Adding restaurants to conversation memory
✅ Added X restaurants to memory

💬 Step 3: Collection Creation via /chat endpoint
✅ Chat Success: True
📝 AI Response: [Collection creation response]
🎯 Command Type: collection

🎉 Complete conversation flow test completed!

===============================================================================
🎉 All tests completed successfully!
⏰ End time: 2024-01-XX XX:XX:XX
===============================================================================
```

## Understanding the Flow

### 1. Restaurant Search (`/query` endpoint)

- User queries for restaurants
- System returns structured restaurant list + AI message
- Results stored in conversation memory

### 2. Collection Creation (`/chat` endpoint)

- User requests collection creation
- System detects collection intent
- Previous restaurant results automatically included
- Collection created via API with all restaurants added

### 3. Memory Integration

- `ConversationMemory` class maintains state
- Thread-based conversation tracking
- Restaurant search results cached for collection creation
- Context-aware message enhancement

## Troubleshooting

### Common Issues

1. **ImportError**: Make sure you're running from the correct directory
2. **API Connection Failed**: Check environment variables and network connection
3. **Timeout Errors**: Tests include timeout protection, but slow networks may cause issues
4. **Missing Dependencies**: Run `pip install -r requirements.txt`

### Debug Mode

Add this to see detailed logs:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Integration with API

These tests work with the actual restaurant API endpoints:

- `/api/query` - Restaurant search with AI messages
- `/api/chat` - Conversational interface with memory
- `/api/collections` - Collection creation and management

The tests simulate real user interactions and verify the complete conversation flow works as expected.
