# Query API Testing Suite

This testing suite is designed to test the `/query` API endpoint for the complete restaurant recommendation and collection creation flow.

## Overview

The test suite performs the following operations:

1. **Multiple Restaurant Queries**: Tests various restaurant search queries across different cities and cuisines
2. **Collection Creation**: Creates collections from the restaurant search results using conversational AI
3. **Follow-up Queries**: Tests conversation continuity using thread IDs
4. **Error Handling**: Tests various error scenarios and edge cases

## Files

- `test_query_api.py` - Main test implementation with `QueryAPITester` class
- `run_query_tests.py` - Command-line runner script with configuration options
- `QUERY_API_TESTING.md` - This documentation file

## Prerequisites

### Required Dependencies

```bash
pip install aiohttp
```

### Environment Setup

1. **API Server**: Make sure your API server is running (default: `http://localhost:8000`)
2. **OpenAI API Key**: Set your OpenAI API key in environment variables
3. **Auth Token**: For collection creation, you'll need a valid JWT token

## Usage

### Basic Usage

```bash
# Run all tests with default settings
python run_query_tests.py

# Run tests against a different API server
python run_query_tests.py --url http://localhost:3000

# Skip collection creation tests (no auth required)
python run_query_tests.py --no-auth

# Use a specific auth token
python run_query_tests.py --token "your_jwt_token_here"
```

### Direct Test Execution

You can also run the test file directly:

```bash
python test_query_api.py
```

## Test Flow

### 1. Restaurant Query Tests

The suite tests multiple restaurant queries:

- **Italian restaurants in Delhi**
- **Chinese restaurants in Mumbai**
- **Vegetarian restaurants in Bangalore**
- **Fine dining in Chennai**
- **Budget-friendly restaurants in Pune**

Each query:

- Sends a POST request to `/query` endpoint
- Captures the response with restaurants and thread_id
- Displays sample restaurants found
- Stores results for collection creation

### 2. Collection Creation Tests

For each successful restaurant query:

- Generates a collection name (e.g., "Italian Favorites in Delhi")
- Uses the same thread_id to maintain conversation context
- Sends a collection creation request: "create a collection called 'Collection Name'"
- Verifies the collection was created successfully

### 3. Follow-up Query Tests

Tests conversation continuity by:

- Using existing thread_ids from restaurant searches
- Sending follow-up queries like "What about dessert places?"
- Verifying the AI remembers previous context
- Checking for new restaurant recommendations

## Expected Output

### Successful Restaurant Query

```
🔍 Making API request: best Italian restaurants in Delhi
   📍 Location: New Delhi
   ✅ Success: 200
   ✅ Found 10 restaurants
   🧵 Thread ID: abc123...
   💬 AI Message: Here are some excellent Italian restaurants in Delhi...
   🍽️ Sample restaurants:
      1. Olive Bar & Kitchen - Mehrauli
      2. Big Chill Cafe - Khan Market
      3. Cafe Delhi Heights - Rajouri Garden
```

### Successful Collection Creation

```
📋 Creating Collection 1: Italian cuisine search
   Original Query: 'best Italian restaurants in Delhi'
   Location: New Delhi
   Restaurants Available: 10
   Collection Name: 'Italian Favorites in Delhi'
   Collection Query: 'create a collection called 'Italian Favorites in Delhi''
   ✅ Collection created successfully!
   💬 AI Response: Great! I've created a collection called "Italian Favorites in Delhi" and added all 10 restaurants...
```

### Follow-up Query

```
🔄 Follow-up 1: Using thread from 'Italian cuisine search'
   Original Location: New Delhi
   Thread ID: abc123...
   Follow-up Query: 'What about dessert places?'
   ✅ Follow-up successful
   💬 AI Response: Based on your interest in Italian restaurants in Delhi, here are some great dessert places...
   🍽️ Found 5 new restaurants
```

## Configuration Options

### Command Line Arguments

- `--url <url>`: API base URL (default: `http://localhost:8000`)
- `--token <token>`: Authorization token for collection creation
- `--no-auth`: Skip collection creation tests that require authentication
- `--help`: Show usage information

### Environment Variables

You can also set configuration via environment variables:

```bash
export API_BASE_URL="http://localhost:8000"
export AUTH_TOKEN="your_jwt_token_here"
```

## Error Handling

The test suite handles various error scenarios:

- **Network errors**: Connection timeouts, DNS failures
- **HTTP errors**: 4xx and 5xx status codes
- **Authentication errors**: Invalid or expired tokens
- **JSON parsing errors**: Malformed responses
- **Missing fields**: Incomplete API responses

## Customization

### Adding New Test Queries

Edit the `test_queries` list in `test_multiple_restaurant_queries()`:

```python
test_queries = [
    {
        "query": "your custom query",
        "location": "Your City",
        "description": "Custom search description"
    },
    # ... existing queries
]
```

### Modifying Follow-up Queries

Edit the `follow_up_queries` list in `test_follow_up_queries()`:

```python
follow_up_queries = [
    "Your custom follow-up question?",
    # ... existing queries
]
```

### Changing Timeouts

Modify the timeout settings in `QueryAPITester.__aenter__()`:

```python
self.session = aiohttp.ClientSession(
    timeout=aiohttp.ClientTimeout(total=60)  # 60 second timeout
)
```

## Troubleshooting

### Common Issues

1. **Import Error**: Make sure `aiohttp` is installed

   ```bash
   pip install aiohttp
   ```

2. **Connection Error**: Verify your API server is running

   ```bash
   curl http://localhost:8000/health
   ```

3. **Authentication Error**: Check your JWT token is valid and not expired

4. **Timeout Error**: Increase timeout values or check server performance

### Debug Mode

For detailed logging, modify the logging level:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Integration with CI/CD

You can integrate these tests into your CI/CD pipeline:

```bash
# In your CI script
python run_query_tests.py --url $API_URL --token $AUTH_TOKEN
if [ $? -eq 0 ]; then
    echo "✅ All tests passed"
else
    echo "❌ Tests failed"
    exit 1
fi
```

## Performance Metrics

The test suite tracks:

- **Response times** for each API call
- **Success rates** for restaurant queries
- **Collection creation rates**
- **Memory usage** during conversation flows
- **Error rates** and types

## Contributing

To add new test scenarios:

1. Extend the `QueryAPITester` class with new test methods
2. Add new test cases to the existing test arrays
3. Update this documentation with new features
4. Ensure error handling for new scenarios

## Support

For issues or questions about the testing suite:

1. Check the console output for detailed error messages
2. Verify your API server is running and accessible
3. Ensure all dependencies are installed
4. Check authentication tokens are valid
