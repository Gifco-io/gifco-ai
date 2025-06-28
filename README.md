# Restaurant Recommender API

An AI-powered FastAPI application that processes natural language restaurant queries and provides intelligent recommendations.

## 🚀 Features

- **Natural Language Processing**: Query restaurants using natural language like "Best butter chicken spot in new delhi"
- **Multiple Endpoints**:
  - `/chat` - Conversational interface with thread support
  - `/health` - Health check endpoint
- **Intelligent Parsing**: Automatically extracts location, cuisine, and preferences from queries using Venice AI
- **Structured Responses**: Returns well-formatted JSON with restaurant information
- **Interactive Documentation**: Swagger UI at `/docs` and ReDoc at `/redoc`

## 🛠️ Installation

1. **Install dependencies:**

   ```bash
   cd gifco-ai
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   Create a `.env` file in the `gifco-ai` directory:

   ```env
   # Venice AI Configuration (required for AI processing)
   LLM_API_KEY=vanice-api-key
   LLM_BASE_URL=https://api.venice.ai/api/v1
   LLM_MODEL=venice-uncensored

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
python main.py
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

### 1. **POST /chat** - Restaurant Query

Process natural language restaurant queries.

**Request:**

```json
{
  "query": "Best butter chicken family restaurant in new delhi",
  "thread_id": "c4b8a624-4ed8-4e65-89ea-e71c1adfdb11" //uuid for keeping chat history
}
```

**Response:**

```json
{
  "success": true,
  "message": "Awesome news! I found a fantastic restaurant for you, including Kake Da Hotel. Would you like me to create a collection from this and any other spots you discover? Just say \"yes\" or \"create collection,\" and I’ll get it all set up for you!",
  "query": "best butter chicken family restaurant in delhi",
  "thread_id": "c4b8a624-4ed8-4e65-89ea-e71c1adfdb11",
  "restaurants": [
    {
      "name": "Kake Da Hotel",
      "cuisine": null,
      "location": "Shop No. 67, Municipal Market, Connaught Cir, Connaught Lane, Connaught Place, New Delhi, Delhi 110001, India",
      "rating": null,
      "price_range": null,
      "description": "ID:681908e7df1013eec0053ae6|",
      "address": null,
      "phone": null
    }
  ],
  "response_count": 1,
  "command_type": "search",
  "error": null,
  "timestamp": "2025-06-23T19:58:31.028055"
}
```

### 2. **GET /health** - Health Check

Check API health status.

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0"
}
```

### Using curl:

````bash
# Test health endpoint
curl -X GET "http://localhost:8000/health"

# Test query endpoint
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "Best butter chicken spot in new delhi"}'


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
````

## 📋 Example Queries

The API can handle various types of restaurant queries:

### Location + Cuisine Searches:

- "Best butter chicken spot in new delhi"
- "Find Italian restaurants in Mumbai"
- "Pizza places near me in Bangalore"
- "Create a collection of these restaurant" //run after search queries

### Help and Information:

- "help"
- "What can you do?"
- "How do I search for restaurants?"

## 🏗️ Architecture

The API is built with:

- **FastAPI**: Modern, fast web framework for building APIs
- **LangChain**: AI framework for natural language processing
- **Venice AI**: Advanced language models for understanding and processing queries
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
| `LLM_API_KEY`           | Venice AI API key (required)      | -                            |
| `LLM_BASE_URL`          | Venice AI API base URL            | https://api.venice.ai/api/v1 |
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

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.
