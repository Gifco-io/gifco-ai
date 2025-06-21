# Restaurant Chat CLI

An interactive command-line interface for conversing with the restaurant recommendation agent.

## Features

🍽️ **Restaurant Search**: Find restaurants by cuisine, location, price range, etc.  
💬 **Conversational AI**: Natural language conversations with memory  
📝 **Collection Creation**: Create and manage restaurant collections  
🧵 **Thread Continuity**: Maintains conversation context across exchanges  
📖 **History Tracking**: View and manage conversation history  
🔧 **System Commands**: Built-in commands for enhanced functionality

## Installation

### Prerequisites

```bash
pip install aiohttp
```

### Files

- `chat_cli.py` - Main chat interface implementation
- `chat.py` - Simple launcher script
- `CHAT_CLI.md` - This documentation

## Usage

### Basic Usage

```bash
# Launch chat with default settings
python chat_cli.py

# Or use the simple launcher
python chat.py
```

### Advanced Usage

```bash
# Connect to different API server
python chat_cli.py --url http://localhost:3000

# Include authentication token for collection creation
python chat_cli.py --token "your_jwt_token_here"

# Full configuration
python chat_cli.py --url http://localhost:8000 --token "your_token"
```

### Environment Variables

You can also configure via environment variables:

```bash
export API_BASE_URL="http://localhost:8000"
export AUTH_TOKEN="your_jwt_token_here"
python chat_cli.py
```

## Chat Interface

### Welcome Screen

```
🍽️  Restaurant Recommendation Chat
==================================================
Welcome to the Restaurant AI Assistant!

💡 What you can ask:
   • Find restaurants: 'best Italian restaurants in Delhi'
   • Create collections: 'create a collection called My Favorites'
   • Ask follow-ups: 'what about dessert places?'
   • Get recommendations: 'romantic dinner spots in Mumbai'

🔧 Commands:
   • /location <city> - Set default location
   • /history - Show conversation history
   • /clear - Clear conversation history
   • /thread - Show current thread ID
   • /help - Show this help message
   • /quit or /exit - Exit the chat

🌐 Connected to: http://localhost:8000
🧵 Thread ID: abc123-def456-789...
🔑 Auth: Enabled
==================================================
```

### Example Conversation

```
👤 You: find best Italian restaurants in Delhi

🤖 AI: Thinking...

🤖 AI: I found some excellent Italian restaurants in Delhi for you! Here are the top recommendations:

🍽️  Found 15 restaurants:
----------------------------------------
1. Olive Bar & Kitchen
   📍 One Style Mile, Mehrauli, New Delhi
   🍴 Italian, Continental
   ⭐ 4.2/5

2. Big Chill Cafe
   📍 Khan Market, New Delhi
   🍴 Italian, Continental, Desserts
   ⭐ 4.0/5

3. Cafe Delhi Heights
   📍 Rajouri Garden, New Delhi
   🍴 Italian, North Indian, Continental
   ⭐ 4.1/5

... and 12 more restaurants

👤 You: create a collection called "Italian Favorites"

🤖 AI: Perfect! I've created a collection called "Italian Favorites" and added all 15 Italian restaurants from your search. You can now easily access these restaurants anytime!

👤 You: what about dessert places?

🤖 AI: Great question! Based on your interest in Italian cuisine, here are some excellent dessert places in Delhi:

🍽️  Found 8 restaurants:
----------------------------------------
1. Wenger's
   📍 Connaught Place, New Delhi
   🍴 Bakery, Desserts
   ⭐ 4.3/5

...
```

## System Commands

### `/location <city>`

Set a default location for your queries:

```
👤 You: /location Mumbai
📍 Default location set to: Mumbai

👤 You: find good restaurants
🤖 AI: Here are some great restaurants in Mumbai...
```

### `/history`

View your conversation history:

```
👤 You: /history

📖 Conversation History (3 exchanges)
============================================================
[14:30:15] Exchange 1
👤 You: find Italian restaurants in Delhi
🤖 AI: I found some excellent Italian restaurants in Delhi for you! Here are the top...
🍽️  Found: 15 restaurants
--------------------------------------------
[14:31:22] Exchange 2
👤 You: create a collection called Italian Favorites
🤖 AI: Perfect! I've created a collection called "Italian Favorites" and added all...
--------------------------------------------
```

### `/clear`

Clear conversation history:

```
👤 You: /clear
✅ Conversation history cleared.
```

### `/thread`

Show current thread ID:

```
👤 You: /thread
🧵 Current Thread ID: abc123-def456-789ghi-012jkl
```

### `/help`

Show help message with examples and commands.

### `/quit` or `/exit`

Exit the chat application.

## Query Examples

### Restaurant Search

```
"find Italian restaurants in Delhi"
"best vegetarian places in Mumbai"
"romantic dinner spots near me"
"budget-friendly cafes in Bangalore"
"top rated Chinese restaurants"
"restaurants with outdoor seating"
"places open late night"
```

### Collection Management

```
"create a collection called My Favorites"
"make a list of romantic restaurants"
"save these restaurants to Italian Favorites"
"add these to my collection"
```

### Follow-up Queries

```
"what about dessert places?"
"show me more options"
"any places with live music?"
"what are the most popular dishes?"
"which ones have home delivery?"
```

## Features in Detail

### 🧵 Thread Continuity

- Each chat session has a unique thread ID
- AI remembers previous conversations within the session
- Context is maintained across restaurant searches and collection creation

### 📖 History Tracking

- All conversations are saved in memory during the session
- View timestamp, user input, AI response, and restaurant count
- Clear history when needed

### 🍽️ Restaurant Display

- Formatted display of restaurant information
- Shows name, location, cuisine type, and rating
- Limits display to 5 restaurants by default with "show more" option

### 🔐 Authentication

- Optional JWT token support for collection creation
- Automatic error handling for authentication failures
- Clear messaging when auth is required

### ⚡ Performance

- Async HTTP requests for responsive chat
- Typing indicators during API calls
- Graceful error handling and recovery

## Error Handling

### Network Errors

```
❌ Error: Connection failed
💡 Please check if the API server is running and try again.
```

### Authentication Errors

```
❌ Error: HTTP 401: Access denied - Invalid token
💡 This might be an authentication issue. Collection creation requires a valid token.
```

### Invalid Commands

```
❌ Unknown command: /invalid
💡 Type /help for available commands.
```

## Configuration

### Default Settings

- **API URL**: `http://localhost:8000`
- **Timeout**: 30 seconds
- **Max Restaurants Displayed**: 5
- **Auth**: Optional (required for collections)

### Customization

You can modify the default settings in `chat_cli.py`:

```python
# Change default API URL
api_base_url = "http://your-api-server.com"

# Change timeout
timeout=aiohttp.ClientTimeout(total=60)  # 60 seconds

# Change max restaurants displayed
max_display = 10
```

## Troubleshooting

### Common Issues

1. **Import Error**: Make sure `aiohttp` is installed

   ```bash
   pip install aiohttp
   ```

2. **Connection Error**: Verify API server is running

   ```bash
   curl http://localhost:8000/health
   ```

3. **Authentication Error**: Check if JWT token is valid and not expired

4. **Timeout Error**: Increase timeout or check server performance

### Debug Mode

For detailed logging, modify the logging level in `chat_cli.py`:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Integration

### With Existing API

The chat CLI works with your existing `/query` endpoint and expects:

**Request Format:**

```json
{
  "query": "user's question",
  "thread_id": "unique-thread-id",
  "location": "optional-location"
}
```

**Response Format:**

```json
{
  "success": true,
  "message": "AI response text",
  "restaurants": [...],
  "thread_id": "same-thread-id"
}
```

### With Authentication

For collection creation, include JWT token in Authorization header:

```
Authorization: Bearer your_jwt_token_here
```

## Development

### Adding New Commands

To add new system commands, modify the `handle_command` method:

```python
elif command.startswith('/newcommand '):
    # Handle your new command
    parameter = command[12:].strip()
    print(f"Executing new command with: {parameter}")
```

### Customizing Display

Modify the `display_restaurants` method to change how restaurants are shown:

```python
def display_restaurants(self, restaurants: list, max_display: int = 10):
    # Your custom display logic
    pass
```

### Adding Features

The `RestaurantChatCLI` class can be extended with additional methods for new functionality.

## Support

For issues or feature requests:

1. Check the console output for detailed error messages
2. Verify API server connectivity
3. Ensure authentication tokens are valid
4. Review the conversation history for context

Happy chatting! 🍽️💬
