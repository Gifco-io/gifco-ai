#!/usr/bin/env python3
"""Test script for /query API endpoint - Restaurant search and collection creation flow."""

import asyncio
import aiohttp
import json
import logging
import base64
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def decode_jwt_payload(token: str) -> Optional[Dict]:
    """Decode JWT payload without verification (for debugging only).
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload or None if invalid
    """
    try:
        # Split the token into parts
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        # Decode the payload (second part)
        payload_b64 = parts[1]
        # Add padding if needed
        payload_b64 += '=' * (4 - len(payload_b64) % 4)
        
        # Decode base64
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_bytes.decode('utf-8'))
        
        return payload
    except Exception as e:
        logger.error(f"Failed to decode JWT payload: {e}")
        return None


def check_token_expiry(token: str) -> Dict[str, Any]:
    """Check if JWT token is expired.
    
    Args:
        token: JWT token string
        
    Returns:
        Dictionary with expiry information
    """
    payload = decode_jwt_payload(token)
    if not payload:
        return {"valid": False, "error": "Invalid token format"}
    
    # Check expiry
    exp = payload.get('exp')
    if not exp:
        return {"valid": True, "error": "No expiry time found"}
    
    exp_datetime = datetime.fromtimestamp(exp, tz=timezone.utc)
    now = datetime.now(timezone.utc)
    
    is_expired = now > exp_datetime
    time_left = exp_datetime - now
    
    return {
        "valid": not is_expired,
        "expired": is_expired,
        "exp_timestamp": exp,
        "exp_datetime": exp_datetime.isoformat(),
        "current_time": now.isoformat(),
        "time_left": str(time_left) if not is_expired else "Expired",
        "payload": payload
    }


class QueryAPITester:
    """Test class for /query API endpoint with restaurant and collection flow."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the API tester.
        
        Args:
            base_url: Base URL of the API server
        """
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)  # 30 second timeout
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def query_api(
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
            print(f"🔍 Making API request: {query}")
            if location:
                print(f"   📍 Location: {location}")
            if thread_id:
                print(f"   🧵 Thread ID: {thread_id[:8]}...")
            if auth_token:
                print(f"   🔑 Auth: Bearer token provided (length: {len(auth_token)})")
            
            async with self.session.post(url, json=request_data, headers=headers) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    data = json.loads(response_text)
                    print(f"   ✅ Success: {response.status}")
                    return data
                else:
                    print(f"   ❌ Failed: HTTP {response.status}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {response_text}",
                        "status_code": response.status
                    }
                    
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_multiple_restaurant_queries(self) -> List[Dict[str, Any]]:
        """Test multiple restaurant search queries and collect results.
        
        Returns:
            List of query results with thread_ids
        """
        print("\n🍽️ Testing Multiple Restaurant Queries")
        print("=" * 60)
        
        # Define multiple test queries
        test_queries = [
            {
                "query": "best Italian restaurants in Delhi",
                "location": "New Delhi",
                "description": "Italian cuisine search"
            },
            {
                "query": "top rated Chinese restaurants in Mumbai", 
                "location": "Mumbai",
                "description": "Chinese cuisine search"
            },
            {
                "query": "good vegetarian restaurants in Bangalore",
                "location": "Bangalore", 
                "description": "Vegetarian restaurant search"
            },
            {
                "query": "fine dining restaurants in Chennai",
                "location": "Chennai",
                "description": "Fine dining search"
            },
            {
                "query": "budget friendly restaurants in Pune",
                "location": "Pune",
                "description": "Budget restaurant search"
            }
        ]
        
        results = []
        
        for i, test_case in enumerate(test_queries, 1):
            print(f"\n📝 Query {i}: {test_case['description']}")
            print(f"   Query: '{test_case['query']}'")
            print(f"   Location: {test_case['location']}")
            
            # Make the query
            response = await self.query_api(
                query=test_case["query"],
                location=test_case["location"]
            )
            
            # Check if response is successful (either explicit success=True or HTTP 200 with data)
            is_successful = (
                response.get("success") is True or 
                (response.get("success") is not False and response.get("restaurants") is not None)
            )
            
            if is_successful:
                restaurants = response.get("restaurants", []) or []  # Handle None case
                thread_id = response.get("thread_id")
                
                print(f"   ✅ Found {len(restaurants)} restaurants")
                print(f"   🧵 Thread ID: {thread_id}")
                print(f"   💬 AI Message: {response.get('message', '')[:100]}...")
                
                # Show first few restaurants
                if restaurants:
                    print(f"   🍽️ Sample restaurants:")
                    for j, restaurant in enumerate(restaurants[:3], 1):
                        name = restaurant.get('name', 'Unknown')
                        location = restaurant.get('location', 'Unknown location')
                        print(f"      {j}. {name} - {location}")
                
                # Store result for collection creation
                results.append({
                    "query": test_case["query"],
                    "location": test_case["location"],
                    "description": test_case["description"],
                    "thread_id": thread_id,
                    "restaurants": restaurants,
                    "restaurant_count": len(restaurants),
                    "response": response
                })
            else:
                print(f"   ❌ Failed: {response.get('error', 'Unknown error')}")
            
            # Small delay between requests
            await asyncio.sleep(1)
        
        print(f"\n📊 Summary: {len(results)} successful restaurant queries out of {len(test_queries)} total")
        return results
    
    async def test_collection_creation_from_restaurants(
        self, 
        restaurant_results: List[Dict[str, Any]], 
        auth_token: str
    ) -> List[Dict[str, Any]]:
        """Test creating collections from restaurant search results.
        
        Args:
            restaurant_results: Results from restaurant queries
            auth_token: Authorization token for collection creation
            
        Returns:
            List of collection creation results
        """
        print("\n📝 Testing Collection Creation from Restaurant Results")
        print("=" * 60)
        
        collection_results = []
        
        for i, result in enumerate(restaurant_results, 1):
            if result["restaurant_count"] == 0:
                print(f"\n🔄 Skipping collection {i}: No restaurants found in '{result['description']}'")
                continue
            
            print(f"\n📋 Creating Collection {i}: {result['description']}")
            print(f"   Original Query: '{result['query']}'")
            print(f"   Location: {result['location']}")
            print(f"   Restaurants Available: {result['restaurant_count']}")
            
            # Generate collection name and description
            location = result['location']
            cuisine_type = result['description'].split()[0].title()  # e.g., "Italian", "Chinese"
            collection_name = f"{cuisine_type} Favorites in {location}"
            
            collection_query = f"create a collection called '{collection_name}'"
            
            print(f"   Collection Name: '{collection_name}'")
            print(f"   Collection Query: '{collection_query}'")
            
            # Create collection using the same thread_id
            response = await self.query_api(
                query=collection_query,
                thread_id=result["thread_id"],
                auth_token=auth_token
            )
            
            if response.get("success"):
                print(f"   ✅ Collection created successfully!")
                print(f"   💬 AI Response: {response.get('message', '')[:150]}...")
                
                collection_results.append({
                    "collection_name": collection_name,
                    "original_query": result['query'],
                    "location": result['location'],
                    "restaurant_count": result['restaurant_count'],
                    "thread_id": result["thread_id"],
                    "success": True,
                    "response": response
                })
            else:
                error = response.get('error', 'Unknown error')
                print(f"   ❌ Collection creation failed: {error}")
                
                collection_results.append({
                    "collection_name": collection_name,
                    "original_query": result['query'],
                    "location": result['location'],
                    "restaurant_count": result['restaurant_count'],
                    "thread_id": result["thread_id"],
                    "success": False,
                    "error": error
                })
            
            # Small delay between collection creations
            await asyncio.sleep(1)
        
        successful_collections = len([r for r in collection_results if r["success"]])
        print(f"\n📊 Collection Summary: {successful_collections} successful collections out of {len(collection_results)} attempts")
        
        return collection_results
    
    async def test_follow_up_queries(self, restaurant_results: List[Dict[str, Any]]) -> None:
        """Test follow-up queries using the same thread IDs.
        
        Args:
            restaurant_results: Results from restaurant queries with thread_ids
        """
        print("\n💬 Testing Follow-up Queries with Conversation Memory")
        print("=" * 60)
        
        follow_up_queries = [
            "What about dessert places?",
            "Any recommendations for romantic dinner?",
            "Show me more options",
            "What are the most popular dishes?",
            "Any places with outdoor seating?"
        ]
        
        # Test follow-up queries with a few of the thread IDs
        for i, result in enumerate(restaurant_results[:3], 1):  # Test with first 3 results
            if not result.get("thread_id"):
                continue
                
            print(f"\n🔄 Follow-up {i}: Using thread from '{result['description']}'")
            print(f"   Original Location: {result['location']}")
            print(f"   Thread ID: {result['thread_id'][:8]}...")
            
            # Pick a random follow-up query
            follow_up = follow_up_queries[(i-1) % len(follow_up_queries)]
            print(f"   Follow-up Query: '{follow_up}'")
            
            response = await self.query_api(
                query=follow_up,
                thread_id=result["thread_id"]
            )
            
            # Check if response is successful (more flexible success checking)
            is_successful = (
                response.get("success") is True or 
                (response.get("success") is not False and response.get("message"))
            )
            
            if is_successful:
                print(f"   ✅ Follow-up successful")
                print(f"   💬 AI Response: {response.get('message', '')[:100]}...")
                
                # Check if new restaurants were found
                new_restaurants = response.get("restaurants", []) or []  # Handle None case
                if new_restaurants:
                    print(f"   🍽️ Found {len(new_restaurants)} new restaurants")
            else:
                print(f"   ❌ Follow-up failed: {response.get('error', 'Unknown error')}")
            
            await asyncio.sleep(0.5)
    
    async def run_complete_query_test(self, auth_token: Optional[str] = None):
        """Run the complete /query API test suite.
        
        Args:
            auth_token: Optional authorization token for collection creation
        """
        print("🚀 Starting Complete /query API Test Suite")
        print("=" * 80)
        print(f"⏰ Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 API Base URL: {self.base_url}")
        print(f"🔑 Auth Token: {'Provided' if auth_token else 'Not provided'}")
        print("=" * 80)
        
        try:
            # Step 1: Test multiple restaurant queries
            restaurant_results = await self.test_multiple_restaurant_queries()
            
            if not restaurant_results:
                print("❌ No successful restaurant queries, aborting remaining tests")
                return
            
            # Step 2: Test collection creation (if auth token provided)
            if auth_token:
                # Check token validity first
                print("\n🔐 Checking Auth Token Validity")
                print("=" * 60)
                token_info = check_token_expiry(auth_token)
                
                print(f"🔍 Token Valid: {token_info.get('valid', False)}")
                if token_info.get('expired'):
                    print(f"⏰ Token Status: EXPIRED")
                    print(f"📅 Expired At: {token_info.get('exp_datetime', 'Unknown')}")
                    print(f"🕐 Current Time: {token_info.get('current_time', 'Unknown')}")
                else:
                    print(f"⏰ Token Status: Valid")
                    print(f"⏳ Time Left: {token_info.get('time_left', 'Unknown')}")
                
                if token_info.get('payload'):
                    payload = token_info['payload']
                    print(f"👤 Subject: {payload.get('sub', 'Unknown')}")
                    print(f"🏢 Issuer: {payload.get('iss', 'Unknown')}")
                    print(f"🎯 Audience: {payload.get('aud', 'Unknown')}")
                
                if not token_info.get('valid', False):
                    print("\n❌ Token is expired or invalid! Collection creation will likely fail.")
                    print("💡 Please get a new token from your authentication provider.")
                
                print("=" * 60)
                
                collection_results = await self.test_collection_creation_from_restaurants(
                    restaurant_results, auth_token
                )
            else:
                print("\n💡 Skipping collection creation tests (no auth token provided)")
                collection_results = []
            
            # Step 3: Test follow-up queries
            await self.test_follow_up_queries(restaurant_results)
            
            # Final summary
            print("\n" + "=" * 80)
            print("🎉 Complete /query API Test Results")
            print("=" * 80)
            print(f"📊 Restaurant Queries: {len(restaurant_results)} successful")
            
            if collection_results:
                successful_collections = len([r for r in collection_results if r["success"]])
                print(f"📝 Collections Created: {successful_collections} successful")
            
            print(f"⏰ End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ Test suite failed: {str(e)}")
            logger.error(f"Test suite failed: {str(e)}", exc_info=True)


async def main():
    """Main test function."""
    
    print("🎯 /query API Endpoint Test Suite")
    print("Testing restaurant search and collection creation flow")
    print()
    
    # Configuration
    api_base_url = "http://localhost:8000"  # Change this to your API server URL
    auth_token = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IkV3ZmZncFlOdVoxTTBERHdtdngxTmNIRVlYMm9YSzEwZDhYRFl5ZUllTXMifQ.eyJzaWQiOiJjbWMzczhyb2owMHB5angwbmNmdXZiZTRtIiwiaXNzIjoicHJpdnkuaW8iLCJpYXQiOjE3NTAzNjE4MzUsImF1ZCI6ImNtOHVqNDRyaDAwMDM4dmJsZGJxMW5vcXUiLCJzdWIiOiJkaWQ6cHJpdnk6Y204dzE2eDM2MDFqZXJheWN5MDdmZHhlaiIsImV4cCI6MTc1MDM2NTQzNX0.8yQDaGocFckpDLO3S8R-okfcYuey5FFvWSbhugzfrj3HGSMQzOcYOKhBQx0iRXrvstwmw9mw1JGjsQakh_dN2A"
    
    # You can also get these from environment variables
    import os
    api_base_url = os.getenv("API_BASE_URL", api_base_url)
    auth_token = os.getenv("AUTH_TOKEN", auth_token)
    
    print(f"🌐 Testing API at: {api_base_url}")
    print(f"🔑 Auth token: {'Provided' if auth_token else 'Not provided'}")
    print()
    
    # Run tests
    async with QueryAPITester(api_base_url) as tester:
        await tester.run_complete_query_test(auth_token)


def check_token_only():
    """Helper function to just check token validity."""
    import os
    auth_token = os.getenv("AUTH_TOKEN") or "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IkV3ZmZncFlOdVoxTTBERHdtdngxTmNIRVlYMm9YSzEwZDhYRFl5ZUllTXMifQ.eyJzaWQiOiJjbWMyNXFmMWowMGk3bDQwbWM3ZGM2cmx5IiwiaXNzIjoicHJpdnkuaW8iLCJpYXQiOjE3NTAyNjM1NjEsImF1ZCI6ImNtOHVqNDRyaDAwMDM4dmJsZGJxMW5vcXUiLCJzdWIiOiJkaWQ6cHJpdnk6Y204dzE2eDM2MDFqZXJheWN5MDdmZHhlaiIsImV4cCI6MTc1MDI2NzE2MX0.mziaGFByr9Oyah9fHtdjExST8F5BP9zb1w4VOLFc0F7njx94biQVyOTCF3WMXC_G7nDBW4OXtZecRy1YvvQitQ"
    
    print("🔐 JWT Token Analysis")
    print("=" * 50)
    token_info = check_token_expiry(auth_token)
    
    print(f"🔍 Token Valid: {token_info.get('valid', False)}")
    if token_info.get('expired'):
        print(f"⏰ Token Status: EXPIRED")
        print(f"📅 Expired At: {token_info.get('exp_datetime', 'Unknown')}")
    else:
        print(f"⏰ Token Status: Valid")
        print(f"⏳ Time Left: {token_info.get('time_left', 'Unknown')}")
    
    if token_info.get('payload'):
        payload = token_info['payload']
        print(f"👤 Subject: {payload.get('sub', 'Unknown')}")
        print(f"🏢 Issuer: {payload.get('iss', 'Unknown')}")
        print(f"🎯 Audience: {payload.get('aud', 'Unknown')}")
        print(f"🕐 Issued At: {datetime.fromtimestamp(payload.get('iat', 0), tz=timezone.utc).isoformat() if payload.get('iat') else 'Unknown'}")
    
    print("=" * 50)


if __name__ == "__main__":
    import sys
    
    # Check if user wants to just check token
    if len(sys.argv) > 1 and sys.argv[1] == "--check-token":
        check_token_only()
        exit(0)
    
    # Check if aiohttp is available
    try:
        import aiohttp
    except ImportError:
        print("❌ Error: aiohttp is required for API tests")
        print("Install it with: pip install aiohttp")
        exit(1)
    
    # Run the test suite
    asyncio.run(main()) 