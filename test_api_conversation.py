#!/usr/bin/env python3
"""Test script for conversation flow using actual API calls."""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class APIConversationTester:
    """Test class for conversation flow using actual API calls."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the API tester.
        
        Args:
            base_url: Base URL of the API server
        """
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def make_query_request(
        self, 
        query: str, 
        location: Optional[str] = None, 
        thread_id: Optional[str] = None,
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make a request to the /query endpoint.
        
        Args:
            query: The query string
            location: Optional location
            thread_id: Optional thread ID for conversation continuity
            auth_token: Optional authorization token
            
        Returns:
            Response data as dictionary
        """
        url = f"{self.base_url}/query"
        
        # Prepare request body
        request_data = {"query": query}
        if location:
            request_data["location"] = location
        if thread_id:
            request_data["thread_id"] = thread_id
        
        # Prepare headers
        headers = {"Content-Type": "application/json"}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        try:
            logger.info(f"Making API request to {url}")
            logger.info(f"Request data: {json.dumps(request_data, indent=2)}")
            
            async with self.session.post(url, json=request_data, headers=headers) as response:
                response_text = await response.text()
                
                logger.info(f"Response status: {response.status}")
                logger.info(f"Response: {response_text}")
                
                if response.status == 200:
                    return json.loads(response_text)
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {response_text}",
                        "status_code": response.status
                    }
                    
        except Exception as e:
            logger.error(f"Error making API request: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_health_check(self):
        """Test the health endpoint."""
        print("\n🏥 Testing Health Check")
        print("=" * 50)
        
        try:
            url = f"{self.base_url}/health"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check passed: {data}")
                    return True
                else:
                    print(f"❌ Health check failed: HTTP {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Health check error: {str(e)}")
            return False
    
    async def test_restaurant_search(self) -> Optional[str]:
        """Test restaurant search and return thread_id for follow-up.
        
        Returns:
            Thread ID for conversation continuity, or None if failed
        """
        print("\n🔍 Testing Restaurant Search via API")
        print("=" * 50)
        
        response = await self.make_query_request(
            query="suggest me a good restaurant in new delhi",
            location="New Delhi"
        )
        
        if response.get("success"):
            print(f"✅ Search Success: {response['success']}")
            print(f"📝 AI Message: {response['message']}")
            print(f"🧵 Thread ID: {response.get('thread_id')}")
            print(f"🍽️ Restaurants Found: {len(response.get('restaurants', []))}")
            print(f"🎯 Command Type: {response.get('command_type')}")
            
            # Show first few restaurants
            restaurants = response.get('restaurants', [])
            if restaurants:
                print("\nFirst 3 restaurants:")
                for i, restaurant in enumerate(restaurants[:3], 1):
                    print(f"  {i}. {restaurant.get('name', 'Unknown')}")
                    if restaurant.get('location'):
                        print(f"     📍 {restaurant['location']}")
                    if restaurant.get('cuisine'):
                        print(f"     🍽️ {restaurant['cuisine']}")
            
            return response.get('thread_id')
        else:
            print(f"❌ Search Failed: {response.get('error', 'Unknown error')}")
            return None
    
    async def test_collection_creation(self, thread_id: str, auth_token: str) -> bool:
        """Test collection creation with conversation memory.
        
        Args:
            thread_id: Thread ID from previous restaurant search
            auth_token: Authorization token for collection creation
            
        Returns:
            True if successful, False otherwise
        """
        print("\n📝 Testing Collection Creation via API")
        print("=" * 50)
        
        response = await self.make_query_request(
            query="create a collection called 'My Delhi Favorites'",
            thread_id=thread_id,
            auth_token=auth_token
        )
        
        if response.get("success"):
            print(f"✅ Collection Success: {response['success']}")
            print(f"📝 AI Response: {response['message']}")
            print(f"🧵 Thread ID: {response.get('thread_id')}")
            print(f"🎯 Command Type: {response.get('command_type')}")
            return True
        else:
            print(f"❌ Collection Failed: {response.get('error', 'Unknown error')}")
            if response.get('status_code') == 401:
                print("   💡 This might be due to invalid auth token")
            return False
    
    async def test_follow_up_conversation(self, thread_id: str) -> bool:
        """Test follow-up conversation with memory.
        
        Args:
            thread_id: Thread ID for conversation continuity
            
        Returns:
            True if successful, False otherwise
        """
        print("\n💬 Testing Follow-up Conversation via API")
        print("=" * 50)
        
        response = await self.make_query_request(
            query="What other Indian restaurants do you recommend?",
            thread_id=thread_id
        )
        
        if response.get("success"):
            print(f"✅ Follow-up Success: {response['success']}")
            print(f"📝 AI Response: {response['message']}")
            print(f"🧵 Thread ID: {response.get('thread_id')}")
            print(f"🎯 Command Type: {response.get('command_type')}")
            
            # Check if new restaurants were found
            restaurants = response.get('restaurants', [])
            if restaurants:
                print(f"🍽️ New Restaurants Found: {len(restaurants)}")
            
            return True
        else:
            print(f"❌ Follow-up Failed: {response.get('error', 'Unknown error')}")
            return False
    
    async def test_general_conversation(self):
        """Test general conversational queries."""
        print("\n🗣️ Testing General Conversation via API")
        print("=" * 50)
        
        test_queries = [
            "What kind of restaurants do you recommend?",
            "I'm looking for something romantic for dinner",
            "Help me find a good place for lunch"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n  Query {i}: '{query}'")
            
            response = await self.make_query_request(query=query)
            
            if response.get("success"):
                print(f"  ✅ Success: {response['message'][:100]}...")
                print(f"  🎯 Command Type: {response.get('command_type')}")
            else:
                print(f"  ❌ Failed: {response.get('error', 'Unknown error')}")
    
    async def test_error_scenarios(self):
        """Test various error scenarios."""
        print("\n⚠️ Testing Error Scenarios via API")
        print("=" * 50)
        
        # Test 1: Empty query
        print("\n  Test 1: Empty query")
        response = await self.make_query_request(query="")
        if not response.get("success"):
            print(f"  ✅ Empty query properly rejected: {response.get('error', 'Unknown error')}")
        else:
            print(f"  ❌ Empty query unexpectedly succeeded")
        
        # Test 2: Invalid endpoint
        print("\n  Test 2: Invalid endpoint")
        try:
            url = f"{self.base_url}/invalid_endpoint"
            async with self.session.post(url, json={"query": "test"}) as response:
                if response.status == 404:
                    print(f"  ✅ Invalid endpoint properly rejected: HTTP {response.status}")
                else:
                    print(f"  ❌ Unexpected response for invalid endpoint: HTTP {response.status}")
        except Exception as e:
            print(f"  ✅ Invalid endpoint error handled: {str(e)}")
        
        # Test 3: Malformed JSON
        print("\n  Test 3: Malformed request")
        try:
            url = f"{self.base_url}/query"
            async with self.session.post(url, data="invalid json", headers={"Content-Type": "application/json"}) as response:
                if response.status >= 400:
                    print(f"  ✅ Malformed request properly rejected: HTTP {response.status}")
                else:
                    print(f"  ❌ Malformed request unexpectedly succeeded: HTTP {response.status}")
        except Exception as e:
            print(f"  ✅ Malformed request error handled: {str(e)}")
    
    async def run_complete_api_test(self, auth_token: Optional[str] = None):
        """Run the complete API conversation test suite.
        
        Args:
            auth_token: Optional authorization token for collection creation
        """
        print("🚀 Starting Complete API Conversation Tests")
        print("=" * 80)
        print(f"⏰ Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 API Base URL: {self.base_url}")
        print("=" * 80)
        
        try:
            # Test 1: Health check
            health_ok = await self.test_health_check()
            if not health_ok:
                print("❌ Health check failed, aborting tests")
                return
            
            # Test 2: Restaurant search
            thread_id = await self.test_restaurant_search()
            if not thread_id:
                print("❌ Restaurant search failed, skipping conversation tests")
            else:
                # Test 3: Collection creation (if auth token provided)
                if auth_token:
                    await self.test_collection_creation(thread_id, auth_token)
                else:
                    print("\n💡 Skipping collection creation test (no auth token provided)")
                
                # Test 4: Follow-up conversation
                await self.test_follow_up_conversation(thread_id)
            
            # Test 5: General conversation
            await self.test_general_conversation()
            
            # Test 6: Error scenarios
            await self.test_error_scenarios()
            
            print("\n" + "=" * 80)
            print("🎉 All API tests completed!")
            print(f"⏰ End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ API test suite failed: {str(e)}")
            logger.error(f"API test suite failed: {str(e)}", exc_info=True)


async def main():
    """Main test function."""
    
    print("🎯 Restaurant API Conversation Tests")
    print("Testing unified /query endpoint via HTTP API calls")
    print()
    
    # Configuration
    api_base_url = "http://localhost:8000"  # Change this to your API server URL
    auth_token = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IkV3ZmZncFlOdVoxTTBERHdtdngxTmNIRVlYMm9YSzEwZDhYRFl5ZUllTXMifQ.eyJzaWQiOiJjbWMyNXFmMWowMGk3bDQwbWM3ZGM2cmx5IiwiaXNzIjoicHJpdnkuaW8iLCJpYXQiOjE3NTAyNjM1NjEsImF1ZCI6ImNtOHVqNDRyaDAwMDM4dmJsZGJxMW5vcXUiLCJzdWIiOiJkaWQ6cHJpdnk6Y204dzE2eDM2MDFqZXJheWN5MDdmZHhlaiIsImV4cCI6MTc1MDI2NzE2MX0.mziaGFByr9Oyah9fHtdjExST8F5BP9zb1w4VOLFc0F7njx94biQVyOTCF3WMXC_G7nDBW4OXtZecRy1YvvQitQ"  # Optional: for collection creation
    
    # Run tests
    async with APIConversationTester(api_base_url) as tester:
        await tester.run_complete_api_test(auth_token)


if __name__ == "__main__":
    asyncio.run(main()) 