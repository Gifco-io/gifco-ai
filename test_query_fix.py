#!/usr/bin/env python3
"""Test script to verify the /query endpoint fix."""

import asyncio
import httpx
import json
import time
from typing import Dict, Any


async def test_query_endpoint():
    """Test the /query endpoint with a timeout to see if it responds."""
    print("🧪 Testing /query endpoint fix...")
    
    # Test data
    test_data = {
        "query": "Best butter chicken spot in new delhi"
    }
    
    base_url = "http://localhost:8000"
    timeout = 30.0  # 30 second timeout
    
    try:
        print(f"📞 Making request to {base_url}/query...")
        print(f"📋 Request data: {json.dumps(test_data, indent=2)}")
        print(f"⏱️  Timeout: {timeout}s")
        
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{base_url}/query",
                json=test_data
            )
            
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Response received in {duration:.2f}s")
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"📦 Response Data:")
            print(json.dumps(response_data, indent=2))
            
            # Check if the response contains expected fields
            expected_fields = ["success", "message", "query"]
            missing_fields = [field for field in expected_fields if field not in response_data]
            
            if missing_fields:
                print(f"⚠️  Missing expected fields: {missing_fields}")
            else:
                print("✅ All expected fields present")
                
            if response_data.get("success"):
                print("✅ Query processed successfully!")
            else:
                print(f"❌ Query failed: {response_data.get('error', 'Unknown error')}")
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"📄 Response text: {response.text}")
            
    except httpx.TimeoutException:
        print(f"⏱️  Request timed out after {timeout}s")
        print("❌ This indicates the endpoint is still hanging")
        
    except httpx.ConnectError:
        print("🔌 Connection error - is the server running?")
        print("💡 Make sure to start the server with: python -m app.api.main")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print(f"❌ Error type: {type(e)}")
        

async def test_health_endpoint():
    """Test the health endpoint to ensure server is running."""
    print("\n🏥 Testing health endpoint...")
    
    base_url = "http://localhost:8000"
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{base_url}/health")
            
        if response.status_code == 200:
            print("✅ Server is running and healthy")
            print(f"📦 Health data: {response.json()}")
        else:
            print(f"⚠️  Health check returned {response.status_code}")
            
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        return False
        
    return True


async def main():
    """Main test function."""
    print("🚀 Starting API endpoint tests...")
    print("=" * 60)
    
    # First check if server is running
    if not await test_health_endpoint():
        print("\n❌ Server is not running. Please start it first:")
        print("   cd gifco-ai")
        print("   python -m app.api.main")
        return
    
    # Test the query endpoint
    await test_query_endpoint()
    
    print("\n" + "=" * 60)
    print("🏁 Test completed!")


if __name__ == "__main__":
    asyncio.run(main()) 