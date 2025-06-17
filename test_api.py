"""Test script for the Restaurant Recommender API."""
import asyncio
import json
import httpx
from typing import Dict, Any


class RestaurantAPIClient:
    """Client for testing the Restaurant Recommender API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the API client.
        
        Args:
            base_url: Base URL of the API server
        """
        self.base_url = base_url
    
    async def test_health(self) -> Dict[str, Any]:
        """Test the health endpoint.
        
        Returns:
            Health check response
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/health")
            return response.json()
    
    async def test_query(self, query: str, location: str = None) -> Dict[str, Any]:
        """Test the query endpoint.
        
        Args:
            query: The restaurant query
            location: Optional location override
            
        Returns:
            Query response
        """
        data = {"query": query}
        if location:
            data["location"] = location
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/query",
                json=data,
                timeout=30.0
            )
            return response.json()
    
    async def test_chat(self, message: str, thread_id: str = None) -> Dict[str, Any]:
        """Test the chat endpoint.
        
        Args:
            message: The chat message
            thread_id: Optional thread ID
            
        Returns:
            Chat response
        """
        data = {"message": message}
        if thread_id:
            data["thread_id"] = thread_id
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat",
                json=data,
                timeout=30.0
            )
            return response.json()
    
    async def get_examples(self) -> Dict[str, Any]:
        """Get example queries.
        
        Returns:
            Examples response
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/examples")
            return response.json()


async def main():
    """Main test function."""
    print("🧪 Testing Restaurant Recommender API\n")
    
    # Initialize client
    client = RestaurantAPIClient()
    
    # Test health endpoint
    print("1. Testing health endpoint...")
    try:
        health_response = await client.test_health()
        print(f"✅ Health check: {health_response}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    print("\n" + "="*60 + "\n")
    
    # Test query endpoint with the specific example
    print("2. Testing query endpoint...")
    test_queries = [
        "Best butter chicken spot in new delhi",
        "Find Italian restaurants in Mumbai",
        "Recommend a good restaurant for dinner"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n2.{i}. Testing query: '{query}'")
        try:
            query_response = await client.test_query(query)
            print(f"✅ Query successful: {query_response['success']}")
            print(f"📝 Message: {query_response['message'][:200]}...")
            
            if query_response.get('restaurants'):
                print(f"🍽️  Found {len(query_response['restaurants'])} restaurants")
                for j, restaurant in enumerate(query_response['restaurants'][:2], 1):
                    print(f"   {j}. {restaurant['name']} - {restaurant.get('location', 'N/A')}")
            
        except Exception as e:
            print(f"❌ Query failed: {e}")
    
    print("\n" + "="*60 + "\n")
    
    # Test chat endpoint
    print("3. Testing chat endpoint...")
    chat_messages = [
        "Hello, I'm looking for a good restaurant",
        "Best butter chicken spot in new delhi?",
        "help"
    ]
    
    thread_id = None
    for i, message in enumerate(chat_messages, 1):
        print(f"\n3.{i}. Testing chat: '{message}'")
        try:
            chat_response = await client.test_chat(message, thread_id)
            thread_id = chat_response.get('thread_id')  # Continue conversation
            
            print(f"✅ Chat successful: {chat_response['success']}")
            print(f"💬 Response: {chat_response['message'][:200]}...")
            print(f"🧵 Thread ID: {thread_id}")
            
            if chat_response.get('command_type'):
                print(f"🔍 Command type: {chat_response['command_type']}")
            
        except Exception as e:
            print(f"❌ Chat failed: {e}")
    
    print("\n" + "="*60 + "\n")
    
    # Get examples
    print("4. Getting example queries...")
    try:
        examples_response = await client.get_examples()
        print("✅ Examples retrieved:")
        for example in examples_response['examples']:
            print(f"   • {example['query']} ({example['type']})")
            print(f"     {example['description']}")
        
        print(f"\n📖 Usage:")
        for endpoint, usage in examples_response['usage'].items():
            print(f"   {endpoint}: {usage}")
            
    except Exception as e:
        print(f"❌ Failed to get examples: {e}")
    
    print("\n" + "="*60 + "\n")
    print("🎉 API testing completed!")
    print("\nTo start the API server, run:")
    print("   cd gifco-ai")
    print("   python -m app.api.main")
    print("\nThen visit http://localhost:8000/docs for interactive API documentation")


if __name__ == "__main__":
    asyncio.run(main()) 