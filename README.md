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

# vanice-ai

API KEY: RSxMcst7d5TS48cgR3dRWL3_AU5qZ68a-HnOj5VZte
OPENAI_API_KEY=h6IyrxVtjX1ThU_Gya6-4XWZlsm1WuVNi4iubngt4z
LLM_MODEL

```
{
    "data": [
        {
            "created": 1742262554,
            "id": "venice-uncensored",
            "model_spec": {
                "pricing": {
                    "input": {
                        "usd": 0.5,
                        "vcu": 5
                    },
                    "output": {
                        "usd": 2,
                        "vcu": 20
                    }
                },
                "availableContextTokens": 32768,
                "capabilities": {
                    "optimizedForCode": false,
                    "quantization": "fp16",
                    "supportsFunctionCalling": false,
                    "supportsReasoning": false,
                    "supportsResponseSchema": true,
                    "supportsVision": false,
                    "supportsWebSearch": true,
                    "supportsLogProbs": true
                },
                "constraints": {
                    "temperature": {
                        "default": 0.3
                    },
                    "top_p": {
                        "default": 1
                    }
                },
                "name": "Venice Uncensored",
                "modelSource": "https://huggingface.co/cognitivecomputations/Dolphin-Mistral-24B-Venice-Edition",
                "offline": false,
                "traits": []
            },
            "object": "model",
            "owned_by": "venice.ai",
            "type": "text"
        },
        {
            "created": 1741218077,
            "id": "qwen-2.5-qwq-32b",
            "model_spec": {
                "pricing": {
                    "input": {
                        "usd": 0.5,
                        "vcu": 5
                    },
                    "output": {
                        "usd": 2,
                        "vcu": 20
                    }
                },
                "availableContextTokens": 32768,
                "capabilities": {
                    "optimizedForCode": false,
                    "quantization": "fp8",
                    "supportsFunctionCalling": false,
                    "supportsReasoning": true,
                    "supportsResponseSchema": true,
                    "supportsVision": false,
                    "supportsWebSearch": true,
                    "supportsLogProbs": true
                },
                "constraints": {
                    "temperature": {
                        "default": 0.6
                    },
                    "top_p": {
                        "default": 0.95
                    }
                },
                "name": "Venice Reasoning",
                "modelSource": "https://huggingface.co/Qwen/QwQ-32B",
                "offline": false,
                "traits": []
            },
            "object": "model",
            "owned_by": "venice.ai",
            "type": "text"
        },
        {
            "created": 1745903059,
            "id": "qwen3-4b",
            "model_spec": {
                "pricing": {
                    "input": {
                        "usd": 0.15,
                        "vcu": 1.5
                    },
                    "output": {
                        "usd": 0.6,
                        "vcu": 6
                    }
                },
                "availableContextTokens": 32768,
                "capabilities": {
                    "optimizedForCode": false,
                    "quantization": "fp8",
                    "supportsFunctionCalling": true,
                    "supportsReasoning": true,
                    "supportsResponseSchema": true,
                    "supportsVision": false,
                    "supportsWebSearch": true,
                    "supportsLogProbs": true
                },
                "constraints": {
                    "temperature": {
                        "default": 0.6
                    },
                    "top_p": {
                        "default": 0.95
                    }
                },
                "name": "Venice Small",
                "modelSource": "https://huggingface.co/Qwen/Qwen3-4B",
                "offline": false,
                "traits": []
            },
            "object": "model",
            "owned_by": "venice.ai",
            "type": "text"
        },
        {
            "created": 1742262554,
            "id": "mistral-31-24b",
            "model_spec": {
                "pricing": {
                    "input": {
                        "usd": 0.5,
                        "vcu": 5
                    },
                    "output": {
                        "usd": 2,
                        "vcu": 20
                    }
                },
                "availableContextTokens": 131072,
                "capabilities": {
                    "optimizedForCode": false,
                    "quantization": "fp16",
                    "supportsFunctionCalling": true,
                    "supportsReasoning": false,
                    "supportsResponseSchema": true,
                    "supportsVision": true,
                    "supportsWebSearch": true,
                    "supportsLogProbs": false
                },
                "constraints": {
                    "temperature": {
                        "default": 0.15
                    },
                    "top_p": {
                        "default": 1
                    }
                },
                "name": "Venice Medium",
                "modelSource": "https://huggingface.co/mistralai/Mistral-Small-3.1-24B-Instruct-2503",
                "offline": false,
                "traits": [
                    "default_vision"
                ]
            },
            "object": "model",
            "owned_by": "venice.ai",
            "type": "text"
        },
        {
            "created": 1745903059,
            "id": "qwen3-235b",
            "model_spec": {
                "pricing": {
                    "input": {
                        "usd": 1.5,
                        "vcu": 15
                    },
                    "output": {
                        "usd": 6,
                        "vcu": 60
                    }
                },
                "availableContextTokens": 131072,
                "capabilities": {
                    "optimizedForCode": false,
                    "quantization": "fp8",
                    "supportsFunctionCalling": true,
                    "supportsReasoning": true,
                    "supportsResponseSchema": true,
                    "supportsVision": false,
                    "supportsWebSearch": true,
                    "supportsLogProbs": true
                },
                "constraints": {
                    "temperature": {
                        "default": 0.6
                    },
                    "top_p": {
                        "default": 0.95
                    }
                },
                "name": "Venice Large",
                "modelSource": "https://huggingface.co/Qwen/Qwen3-235B-A22B",
                "offline": false,
                "traits": []
            },
            "object": "model",
            "owned_by": "venice.ai",
            "type": "text"
        },
        {
            "created": 1727966436,
            "id": "llama-3.2-3b",
            "model_spec": {
                "pricing": {
                    "input": {
                        "usd": 0.15,
                        "vcu": 1.5
                    },
                    "output": {
                        "usd": 0.6,
                        "vcu": 6
                    }
                },
                "availableContextTokens": 131072,
                "capabilities": {
                    "optimizedForCode": false,
                    "quantization": "fp16",
                    "supportsFunctionCalling": true,
                    "supportsReasoning": false,
                    "supportsResponseSchema": true,
                    "supportsVision": false,
                    "supportsWebSearch": true,
                    "supportsLogProbs": true
                },
                "constraints": {
                    "temperature": {
                        "default": 0.6
                    },
                    "top_p": {
                        "default": 0.95
                    }
                },
                "name": "Llama 3.2 3B",
                "modelSource": "https://huggingface.co/meta-llama/Llama-3.2-3B",
                "offline": false,
                "traits": [
                    "fastest"
                ]
            },
            "object": "model",
            "owned_by": "venice.ai",
            "type": "text"
        },
        {
            "created": 1733768349,
            "id": "llama-3.3-70b",
            "model_spec": {
                "pricing": {
                    "input": {
                        "usd": 0.7,
                        "vcu": 7
                    },
                    "output": {
                        "usd": 2.8,
                        "vcu": 28
                    }
                },
                "availableContextTokens": 65536,
                "capabilities": {
                    "optimizedForCode": false,
                    "quantization": "fp8",
                    "supportsFunctionCalling": true,
                    "supportsReasoning": false,
                    "supportsResponseSchema": false,
                    "supportsVision": false,
                    "supportsWebSearch": true,
                    "supportsLogProbs": false
                },
                "constraints": {
                    "temperature": {
                        "default": 0.6
                    },
                    "top_p": {
                        "default": 0.95
                    }
                },
                "name": "Llama 3.3 70B",
                "modelSource": "https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct",
                "offline": false,
                "traits": [
                    "function_calling_default",
                    "default"
                ]
            },
            "object": "model",
            "owned_by": "venice.ai",
            "type": "text"
        },
        {
            "created": 1730396371,
            "id": "llama-3.1-405b",
            "model_spec": {
                "pricing": {
                    "input": {
                        "usd": 1.5,
                        "vcu": 15
                    },
                    "output": {
                        "usd": 6,
                        "vcu": 60
                    }
                },
                "availableContextTokens": 65536,
                "capabilities": {
                    "optimizedForCode": false,
                    "quantization": "fp8",
                    "supportsFunctionCalling": false,
                    "supportsReasoning": false,
                    "supportsResponseSchema": true,
                    "supportsVision": false,
                    "supportsWebSearch": true,
                    "supportsLogProbs": true
                },
                "constraints": {
                    "temperature": {
                        "default": 0.6
                    },
                    "top_p": {
                        "default": 0.95
                    }
                },
                "name": "Llama 3.1 405B",
                "modelSource": "https://huggingface.co/meta-llama/Meta-Llama-3.1-405B-Instruct",
                "offline": false,
                "traits": [
                    "most_intelligent"
                ]
            },
            "object": "model",
            "owned_by": "venice.ai",
            "type": "text"
        },
        {
            "created": 1726869022,
            "id": "dolphin-2.9.2-qwen2-72b",
            "model_spec": {
                "pricing": {
                    "input": {
                        "usd": 0.7,
                        "vcu": 7
                    },
                    "output": {
                        "usd": 2.8,
                        "vcu": 28
                    }
                },
                "availableContextTokens": 32768,
                "capabilities": {
                    "optimizedForCode": false,
                    "quantization": "fp8",
                    "supportsFunctionCalling": false,
                    "supportsReasoning": false,
                    "supportsResponseSchema": true,
                    "supportsVision": false,
                    "supportsWebSearch": true,
                    "supportsLogProbs": true
                },
                "constraints": {
                    "temperature": {
                        "default": 0.7
                    },
                    "top_p": {
                        "default": 0.8
                    }
                },
                "name": "Dolphin 72B",
                "modelSource": "https://huggingface.co/cognitivecomputations/dolphin-2.9.2-qwen2-72b",
                "offline": false,
                "traits": [
                    "most_uncensored"
                ]
            },
            "object": "model",
            "owned_by": "venice.ai",
            "type": "text"
        },
        {
            "created": 1739074852,
            "id": "qwen-2.5-vl",
            "model_spec": {
                "pricing": {
                    "input": {
                        "usd": 0.7,
                        "vcu": 7
                    },
                    "output": {
                        "usd": 2.8,
                        "vcu": 28
                    }
                },
                "availableContextTokens": 32768,
                "capabilities": {
                    "optimizedForCode": false,
                    "quantization": "fp8",
                    "supportsFunctionCalling": false,
                    "supportsReasoning": false,
                    "supportsResponseSchema": true,
                    "supportsVision": true,
                    "supportsWebSearch": true,
                    "supportsLogProbs": true
                },
                "constraints": {
                    "temperature": {
                        "default": 0.7
                    },
                    "top_p": {
                        "default": 0.8
                    }
                },
                "name": "Qwen 2.5 VL 72B",
                "modelSource": "https://huggingface.co/Qwen/Qwen2.5-VL-72B-Instruct",
                "offline": false,
                "traits": []
            },
            "object": "model",
            "owned_by": "venice.ai",
            "type": "text"
        },
        {
            "created": 1731628653,
            "id": "qwen-2.5-coder-32b",
            "model_spec": {
                "pricing": {
                    "input": {
                        "usd": 0.5,
                        "vcu": 5
                    },
                    "output": {
                        "usd": 2,
                        "vcu": 20
                    }
                },
                "availableContextTokens": 32768,
                "capabilities": {
                    "optimizedForCode": true,
                    "quantization": "fp8",
                    "supportsFunctionCalling": false,
                    "supportsReasoning": false,
                    "supportsResponseSchema": false,
                    "supportsVision": false,
                    "supportsWebSearch": false,
                    "supportsLogProbs": true
                },
                "constraints": {
                    "temperature": {
                        "default": 0.7
                    },
                    "top_p": {
                        "default": 0.8
                    }
                },
                "name": "Qwen 2.5 Coder 32B",
                "modelSource": "https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct-GGUF",
                "offline": false,
                "traits": [
                    "default_code"
                ]
            },
            "object": "model",
            "owned_by": "venice.ai",
            "type": "text"
        },
        {
            "created": 1738690625,
            "id": "deepseek-r1-671b",
            "model_spec": {
                "pricing": {
                    "input": {
                        "usd": 3.5,
                        "vcu": 35
                    },
                    "output": {
                        "usd": 14,
                        "vcu": 140
                    }
                },
                "availableContextTokens": 131072,
                "capabilities": {
                    "optimizedForCode": false,
                    "quantization": "fp8",
                    "supportsFunctionCalling": false,
                    "supportsReasoning": true,
                    "supportsResponseSchema": true,
                    "supportsVision": false,
                    "supportsWebSearch": true,
                    "supportsLogProbs": false
                },
                "constraints": {
                    "temperature": {
                        "default": 0.6
                    },
                    "top_p": {
                        "default": 0.95
                    }
                },
                "name": "DeepSeek R1 671B",
                "modelSource": "https://huggingface.co/deepseek-ai/DeepSeek-R1",
                "offline": false,
                "traits": [
                    "default_reasoning"
                ]
            },
            "object": "model",
            "owned_by": "venice.ai",
            "type": "text"
        },
        {
            "created": 1740253117,
            "id": "deepseek-coder-v2-lite",
            "model_spec": {
                "pricing": {
                    "input": {
                        "usd": 0.5,
                        "vcu": 5
                    },
                    "output": {
                        "usd": 2,
                        "vcu": 20
                    }
                },
                "availableContextTokens": 131072,
                "capabilities": {
                    "optimizedForCode": true,
                    "quantization": "fp16",
                    "supportsFunctionCalling": false,
                    "supportsReasoning": false,
                    "supportsResponseSchema": true,
                    "supportsVision": false,
                    "supportsWebSearch": false,
                    "supportsLogProbs": false
                },
                "constraints": {
                    "temperature": {
                        "default": 0.6
                    },
                    "top_p": {
                        "default": 0.95
                    }
                },
                "name": "DeepSeek Coder V2 Lite",
                "modelSource": "https://huggingface.co/deepseek-ai/deepseek-coder-v2-lite-Instruct",
                "offline": false,
                "traits": []
            },
            "object": "model",
            "owned_by": "venice.ai",
            "type": "text"
        }
    ],
    "object": "list",
    "type": "text"
}
```
