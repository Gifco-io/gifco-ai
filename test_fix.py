"""Quick test to check if the hanging issue is fixed."""
import asyncio
import aiohttp
import json
import time

async def test_api_fix():
    """Test if the API timeout fix works."""
    print("🧪 Testing API fix...")
    print("🏃 Starting server manually if needed...")
    
    url = "http://localhost:8000/query"
    data = {"query": "Best butter chicken spot in new delhi"}
    
    print(f"🔍 Making API call to: {url}")
    print(f"📋 Request data: {json.dumps(data, indent=2)}")
    
    start_time = time.time()
    
    try:
        timeout = aiohttp.ClientTimeout(total=30)  # 30 second timeout
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=data) as response:
                elapsed = time.time() - start_time
                
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ API call successful in {elapsed:.2f}s!")
                    print(f"   Success: {result.get('success')}")
                    print(f"   Message preview: {result.get('message', '')[:100]}...")
                    return True
                    
                elif response.status == 408:
                    print(f"⏱️  Request timed out after {elapsed:.2f}s (as expected with timeout)")
                    text = await response.text()
                    print(f"   Response: {text}")
                    return True  # This is actually good - timeout is working
                    
                else:
                    print(f"❌ API call failed with status {response.status} after {elapsed:.2f}s")
                    text = await response.text()
                    print(f"   Response: {text[:200]}...")
                    return False
                    
    except asyncio.TimeoutError:
        elapsed = time.time() - start_time
        print(f"❌ Client timeout after {elapsed:.2f}s - server might still be hanging")
        return False
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Error after {elapsed:.2f}s: {str(e)}")
        return False

async def main():
    """Run the test."""
    print("🔧 Testing the hanging fix...")
    print("=" * 50)
    
    success = await test_api_fix()
    
    if success:
        print("\n✅ The fix appears to be working!")
        print("   The API either returned a response or properly timed out.")
    else:
        print("\n❌ The issue might still persist.")
        print("   The API is still hanging without timeout response.")
        
    print("\n" + "=" * 50)

if __name__ == "__main__":
    asyncio.run(main()) 