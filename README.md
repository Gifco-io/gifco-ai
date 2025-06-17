# Restaurant Recommender API

An AI-powered FastAPI application that processes natural language restaurant queries and provides intelligent recommendations.

## 🚀 Features

- **Natural Language Processing**: Query restaurants using natural language like "Best butter chicken spot in new delhi"
- **Multiple Endpoints**:
  - `/query` - Direct restaurant queries
  - `/chat` - Conversational interface with thread support
  - `/health` - Health check endpoint
  - `/examples` - Get example queries
- **Intelligent Parsing**: Automatically extracts location, cuisine, and preferences from queries
- **Structured Responses**: Returns well-formatted JSON with restaurant information
- **Interactive Documentation**: Swagger UI at `/docs` and ReDoc at `/redoc`

## 🛠️ Installation

1. **Install dependencies:**

   ```bash
   cd gifco-ai
   pip install -r requirements-api.txt
   ```

2. **Set up environment variables:**
   Create a `.env` file in the `gifco-ai` directory:

   ```env
   # OpenAI Configuration (required for AI processing)
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_BASE_URL=https://openrouter.ai/api/v1

   # Restaurant API Configuration
   RESTAURANT_SERVER_URL=http://dev.gifco.io

   # API Server Configuration (optional)
   API_HOST=0.0.0.0
   API_PORT=8000
   API_RELOAD=true
   API_LOG_LEVEL=info
   ```

## 🚀 Running the API

### Method 1: Using the startup script (Recommended)

```bash
cd gifco-ai
python start_api.py
```

### Method 2: Using uvicorn directly

```bash
cd gifco-ai
python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Method 3: Using the main module

```bash
cd gifco-ai
python -m app.api.main
```

The API will be available at:

- **Server**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📚 API Endpoints

### 1. **POST /query** - Restaurant Query

Process natural language restaurant queries.

**Request:**

```json
{
  "query": "Best butter chicken spot in new delhi",
  "location": "New Delhi" // Optional location override
}
```

**Response:**

```json
{
  "success": true,
  "message": "🔍 **Searching for restaurants...**\n\n**Query:** Best butter chicken spot in new delhi\n...",
  "query": "Best butter chicken spot in new delhi",
  "restaurants": [
    {
      "name": "Karim's",
      "cuisine": "Indian Cuisine",
      "location": "New Delhi",
      "rating": 4.2,
      "price_range": "Moderate Price",
      "description": "Famous for authentic butter chicken and mughlai cuisine"
    }
  ],
  "location": "New Delhi",
  "cuisine": "Indian",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 2. **POST /chat** - Chat Interface

Conversational interface with thread support.

**Request:**

```json
{
  "message": "I'm looking for a good restaurant for dinner",
  "thread_id": "optional-thread-id" // For conversation continuity
}
```

**Response:**

```json
{
  "success": true,
  "message": "I'd be happy to help you find a great restaurant for dinner! Could you tell me...",
  "thread_id": "generated-or-provided-thread-id",
  "command_type": "recommendation",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 3. **GET /health** - Health Check

Check API health status.

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0"
}
```

### 4. **GET /examples** - Example Queries

Get example queries and usage information.

**Response:**

```json
{
  "examples": [
    {
      "query": "Best butter chicken spot in new delhi",
      "description": "Search for the best butter chicken restaurants in New Delhi",
      "type": "location_cuisine_search"
    }
  ],
  "usage": {
    "query_endpoint": "POST /query with {'query': 'your question here'}",
    "chat_endpoint": "POST /chat with {'message': 'your message here'}"
  }
}
```

## 🧪 Testing the API

### Using the test script:

```bash
cd gifco-ai
python test_api.py
```

### Using curl:

```bash
# Test health endpoint
curl -X GET "http://localhost:8000/health"

# Test query endpoint
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Best butter chicken spot in new delhi"}'

# Test chat endpoint
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Best butter chicken spot in new delhi?"}'
```

### Using Python:

```python
import httpx
import asyncio

async def test_api():
    async with httpx.AsyncClient() as client:
        # Test query
        response = await client.post(
            "http://localhost:8000/query",
            json={"query": "Best butter chicken spot in new delhi"}
        )
        print(response.json())

asyncio.run(test_api())
```

## 📋 Example Queries

The API can handle various types of restaurant queries:

### Location + Cuisine Searches:

- "Best butter chicken spot in new delhi"
- "Find Italian restaurants in Mumbai"
- "Pizza places near me in Bangalore"

### General Recommendations:

- "Recommend a good restaurant for dinner"
- "I want to try something new for lunch"
- "Best restaurants in Delhi"

### Specific Food Searches:

- "Where can I get good biryani?"
- "Best Chinese food in Mumbai"
- "Vegetarian restaurants near me"

### Help and Information:

- "help"
- "What can you do?"
- "How do I search for restaurants?"

## 🏗️ Architecture

The API is built with:

- **FastAPI**: Modern, fast web framework for building APIs
- **LangChain**: AI framework for natural language processing
- **OpenAI**: Language model for understanding and processing queries
- **Pydantic**: Data validation using Python type annotations
- **Async/Await**: Asynchronous processing for better performance

### Key Components:

1. **API Layer** (`app/api/main.py`): FastAPI application with endpoints
2. **Service Layer** (`app/api/services/restaurant_service.py`): Business logic
3. **Models** (`app/api/models/`): Request/response models
4. **Agent Layer** (`app/agent/base.py`): AI agent for processing queries
5. **Command Parser** (`app/commands/parser.py`): Natural language understanding
6. **Tools** (`app/agent/tools/tools.py`): Integration with external APIs

## 🔧 Configuration

### Environment Variables:

| Variable                | Description                       | Default                      |
| ----------------------- | --------------------------------- | ---------------------------- |
| `OPENAI_API_KEY`        | OpenAI API key (required)         | -                            |
| `OPENAI_BASE_URL`       | OpenAI API base URL               | https://openrouter.ai/api/v1 |
| `RESTAURANT_SERVER_URL` | External restaurant API URL       | http://dev.gifco.io          |
| `API_HOST`              | API server host                   | 0.0.0.0                      |
| `API_PORT`              | API server port                   | 8000                         |
| `API_RELOAD`            | Enable auto-reload in development | true                         |
| `API_LOG_LEVEL`         | Logging level                     | info                         |

## 🚨 Error Handling

The API provides comprehensive error handling:

- **400 Bad Request**: Invalid input data
- **422 Unprocessable Entity**: Data validation errors
- **500 Internal Server Error**: Server-side errors
- **503 Service Unavailable**: When AI service is not available

Example error response:

```json
{
  "success": false,
  "error": "Error message here",
  "details": {
    "message": "Additional error details"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 📊 Logging

The API includes comprehensive logging:

- Request/response logging
- AI model interactions
- Error tracking
- Performance metrics

Logs are structured and include timestamps, request IDs, and detailed context.

## 🔒 Security Considerations

- CORS is configured (update for production)
- Request validation using Pydantic
- Error messages don't expose sensitive information
- Rate limiting should be added for production use

## 🚀 Production Deployment

For production deployment:

1. Set environment variables appropriately
2. Use a production WSGI server (e.g., Gunicorn with Uvicorn workers)
3. Add rate limiting
4. Configure proper CORS origins
5. Set up monitoring and logging
6. Use HTTPS

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.
