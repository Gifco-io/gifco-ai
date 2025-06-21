#!/usr/bin/env python3
"""End-to-end test for collection creation workflow."""

import asyncio
import aiohttp
import json
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class EndToEndTester:
    """Test the complete collection creation workflow."""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        """Initialize the tester.
        
        Args:
            api_base_url: Base URL of the API server
        """
        self.api_base_url = api_base_url
        self.auth_token = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IkV3ZmZncFlOdVoxTTBERHdtdngxTmNIRVlYMm9YSzEwZDhYRFl5ZUllTXMifQ.eyJzaWQiOiJjbWM1NHQzaHQwMGUwankwbW5jc2VqbjZwIiwiaXNzIjoicHJpdnkuaW8iLCJpYXQiOjE3NTA0NDM0MDUsImF1ZCI6ImNtOHVqNDRyaDAwMDM4dmJsZGJxMW5vcXUiLCJzdWIiOiJkaWQ6cHJpdnk6Y204dzE2eDM2MDFqZXJheWN5MDdmZHhlaiIsImV4cCI6MTc1MDQ0NzAwNX0.kJQ9iMgmaqyjLoH5_tvnTiSzWkO2P-LlNuIqsTzdXaep3sELQohETkUUpOxTyV3ptnNr8KUGUJDcbj65slDhoA"
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def send_query(self, query: str, thread_id: str, location: str = None) -> dict:
        """Send a query to the restaurant API.
        
        Args:
            query: The user's query
            thread_id: Thread ID for conversation continuity
            location: Optional location for the query
            
        Returns:
            Response from the API
        """
        url = f"{self.api_base_url}/query"
        
        # Prepare request body
        request_data = {
            "query": query,
            "thread_id": thread_id
        }
        if location:
            request_data["location"] = location
        
        # Prepare headers
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        try:
            async with self.session.post(url, json=request_data, headers=headers) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    return json.loads(response_text)
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {response_text}",
                        "status_code": response.status
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_complete_workflow(self):
        """Test the complete collection creation workflow."""
        print("🧪 End-to-End Collection Creation Test")
        print("=" * 50)
        
        # Generate unique thread ID
        import uuid
        thread_id = str(uuid.uuid4())
        print(f"🧵 Thread ID: {thread_id}")
        
        # Step 1: Search for restaurants
        print("\n1️⃣ Step 1: Searching for restaurants...")
        search_response = await self.send_query(
            "find best Italian restaurants in Delhi", 
            thread_id, 
            "Delhi"
        )
        
        if search_response.get("success") is not False:
            print("✅ Restaurant search successful!")
            restaurants = search_response.get("restaurants") or []
            print(f"📊 Found {len(restaurants)} restaurants")
            
            # Show first few restaurants
            for i, restaurant in enumerate(restaurants[:3], 1):
                name = restaurant.get('name', 'Unknown')
                location = restaurant.get('location', 'Unknown location')
                print(f"   {i}. {name} - {location}")
            
            collection_prompt = search_response.get("collection_prompt", "")
            if collection_prompt:
                print(f"💬 Collection Prompt: {collection_prompt}")
            else:
                print("⚠️  No collection prompt received")
        else:
            print(f"❌ Restaurant search failed: {search_response.get('error')}")
            return False
        
        # Step 2: Create collection by saying "yes"
        print("\n2️⃣ Step 2: Creating collection by saying 'yes'...")
        collection_response = await self.send_query("yes", thread_id)
        
        if collection_response.get("success") is not False:
            print("✅ Collection creation request successful!")
            
            # Check for collection result
            collection_result = collection_response.get("collection_result")
            if collection_result:
                if collection_result.get("success"):
                    collection_name = collection_result.get("collection", {}).get("name", "Unknown")
                    added_count = collection_result.get("successfully_added", 0)
                    total_count = collection_result.get("total_restaurants", 0)
                    collection_id = collection_result.get("collection_id", "Unknown")
                    
                    print(f"🎉 Collection '{collection_name}' created successfully!")
                    print(f"📊 Results: {added_count}/{total_count} restaurants added")
                    print(f"🆔 Collection ID: {collection_id}")
                    
                    # Check for failed restaurants
                    failed_restaurants = collection_result.get("failed_restaurants", [])
                    if failed_restaurants:
                        print(f"⚠️  {len(failed_restaurants)} restaurants failed to add:")
                        for failed in failed_restaurants:
                            print(f"   • {failed.get('restaurant_id', 'Unknown')}: {failed.get('error', 'Unknown error')}")
                    
                    return True
                else:
                    error_msg = collection_result.get("error", "Unknown error")
                    print(f"❌ Collection creation failed: {error_msg}")
                    return False
            else:
                print(f"💬 AI Response: {collection_response.get('message', 'No message')}")
                if collection_response.get("collection_created"):
                    print("✅ Collection was created (legacy format)")
                    return True
                else:
                    print("⚠️  No collection result found in response")
                    return False
        else:
            print(f"❌ Collection creation failed: {collection_response.get('error')}")
            return False
    
    async def test_direct_collection_creation(self):
        """Test direct collection creation with a specific name."""
        print("\n\n🧪 Direct Collection Creation Test")
        print("=" * 50)
        
        # Generate unique thread ID
        import uuid
        thread_id = str(uuid.uuid4())
        print(f"🧵 Thread ID: {thread_id}")
        
        # Step 1: Search for restaurants
        print("\n1️⃣ Step 1: Searching for restaurants...")
        search_response = await self.send_query(
            "find Chinese restaurants in Mumbai", 
            thread_id, 
            "Mumbai"
        )
        
        if search_response.get("success") is not False:
            print("✅ Restaurant search successful!")
            restaurants = search_response.get("restaurants") or []
            print(f"📊 Found {len(restaurants)} restaurants")
        else:
            print(f"❌ Restaurant search failed: {search_response.get('error')}")
            return False
        
        # Step 2: Create collection with specific name (LLM will add timestamp for uniqueness)
        print("\n2️⃣ Step 2: Creating collection with specific name...")
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        collection_response = await self.send_query(
            f"create a collection called 'Mumbai Chinese Favorites {timestamp}'", 
            thread_id
        )
        
        if collection_response.get("success") is not False:
            print("✅ Direct collection creation successful!")
            
            # Check for collection result
            collection_result = collection_response.get("collection_result")
            if collection_result and collection_result.get("success"):
                collection_name = collection_result.get("collection", {}).get("name", "Unknown")
                added_count = collection_result.get("successfully_added", 0)
                total_count = collection_result.get("total_restaurants", 0)
                
                print(f"🎉 Collection '{collection_name}' created successfully!")
                print(f"📊 Results: {added_count}/{total_count} restaurants added")
                return True
            else:
                print(f"💬 AI Response: {collection_response.get('message', 'No message')}")
                return False
        else:
            print(f"❌ Direct collection creation failed: {collection_response.get('error')}")
            return False


async def main():
    """Main function to run the tests."""
    
    # Check if API server is running
    print("🔍 Checking if API server is running...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/health") as response:
                if response.status == 200:
                    print("✅ API server is running")
                else:
                    print("⚠️  API server responded but may have issues")
    except Exception as e:
        print(f"❌ API server is not running: {e}")
        print("💡 Please start the API server first with: python start_api.py")
        return 1
    
    # Run the tests
    try:
        async with EndToEndTester() as tester:
            # Test 1: Complete workflow (search → "yes")
            success1 = await tester.test_complete_workflow()
            
            # Test 2: Direct collection creation
            success2 = await tester.test_direct_collection_creation()
            
            print("\n🎯 Test Summary:")
            print("=" * 30)
            print(f"✅ Search → 'yes' workflow: {'PASSED' if success1 else 'FAILED'}")
            print(f"✅ Direct collection creation: {'PASSED' if success2 else 'FAILED'}")
            
            if success1 and success2:
                print("\n🎉 All tests passed! Collection creation is working correctly.")
                return 0
            else:
                print("\n❌ Some tests failed. Please check the logs above.")
                return 1
                
    except Exception as e:
        print(f"❌ Test execution failed: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 