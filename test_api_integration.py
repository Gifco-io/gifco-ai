"""Test script to demonstrate the restaurant command parser with API integration."""
import asyncio
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.commands.parser import CommandParser

async def test_parser_with_api():
    """Test the command parser with API integration."""
    print("🧪 Testing Restaurant Command Parser with API Integration\n")
    
    # Initialize parser with dev.gifco.io server URL
    server_url = os.getenv("RESTAURANT_SERVER_URL", "http://dev.gifco.io")
    parser = CommandParser(server_url=server_url)
    
    # Test the specific query you mentioned
    test_query = "Best butter chicken spot in new delhi?"
    
    print(f"🔍 Testing Query: '{test_query}'")
    print(f"🌐 Server URL: {server_url}")
    print("=" * 60)
    
    try:
        # Parse and execute (includes API call if it's a search)
        result = parser.parse_and_execute(test_query)
        
        print("✅ Parsing Results:")
        print(f"Command Type: {type(result['command']).__name__}")
        
        if hasattr(result['command'], 'search_query'):
            q = result['command'].search_query
            print(f"Parsed Query: {q.query}")
            print(f"Parsed Place: {q.place}")
            print(f"Parsed Cuisine: {q.cuisine}")
            
        print("\n🌐 API Call Results:")
        if result.get('error'):
            print(f"❌ Parser Error: {result['error']}")
        elif result.get('tool_response'):
            tool_response = result['tool_response']
            # The tool_response is a JSON string from the API tool
            if isinstance(tool_response, str):
                try:
                    api_data = json.loads(tool_response)
                    if 'error' in api_data:
                        print(f"❌ API Error: {api_data['error']}")
                        if 'status' in api_data:
                            print(f"❌ Status Code: {api_data['status']}")
                    else:
                        print("✅ API Response received successfully:")
                        print("=" * 40)
                        print(json.dumps(api_data, indent=2))
                        print("=" * 40)
                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON response: {tool_response}")
            else:
                print("✅ Tool Response:")
                print("=" * 40)
                print(json.dumps(tool_response, indent=2))
                print("=" * 40)
        else:
            print("ℹ️  No API call made (not a search command)")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🔗 Expected API Call:")
    print(f"URL: {server_url}/api/questions?type=current&place=New Delhi")
    print("\nThis demonstrates how 'Best butter chicken spot in new delhi?' gets converted to the API call you specified!")

async def test_multiple_queries():
    """Test multiple queries to show different parsing scenarios and API responses."""
    print("\n\n🧪 Testing Multiple Query Types with Full API Responses\n")
    
    server_url = os.getenv("RESTAURANT_SERVER_URL", "http://dev.gifco.io")
    parser = CommandParser(server_url=server_url)
    
    test_queries = [
        "Best butter chicken spot in new delhi?",
        "Find Italian restaurants in Mumbai",
        "Recommend a good restaurant for dinner",
        "Pizza places near me in Bangalore",
        "In New York, what is the best butter chicken spot?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"🔍 Test {i}: '{query}'")
        print(f"🌐 Server: {server_url}")
        print("-" * 50)
        
        try:
            # Parse and execute with API call
            result = parser.parse_and_execute(query)
            print(f"✅ Command Type: {type(result['command']).__name__}")
            
            if hasattr(result['command'], 'search_query'):
                q = result['command'].search_query
                print(f"   Parsed Query: {q.query}")
                print(f"   Parsed Place: {q.place}")
                print(f"   Parsed Cuisine: {q.cuisine}")
                
                formatted_place = parser._format_place_name(q.place or "")
                api_url = f"{server_url}/api/questions?type=current&place={formatted_place}"
                print(f"   API URL: {api_url}")
                
                # Show API response
                if result.get('error'):
                    print(f"   ❌ Parser Error: {result['error']}")
                elif result.get('tool_response'):
                    tool_response = result['tool_response']
                    # The tool_response is a JSON string from the API tool
                    if isinstance(tool_response, str):
                        try:
                            api_data = json.loads(tool_response)
                            if 'error' in api_data:
                                print(f"   ❌ API Error: {api_data['error']}")
                                if 'status' in api_data:
                                    print(f"   ❌ Status: {api_data['status']}")
                            else:
                                print("   ✅ API Response:")
                                print("   " + "=" * 30)
                                response_str = json.dumps(api_data, indent=4)
                                for line in response_str.split('\n'):
                                    print(f"   {line}")
                                print("   " + "=" * 30)
                        except json.JSONDecodeError:
                            print(f"   ❌ Invalid JSON response: {tool_response}")
                    else:
                        print("   ✅ Tool Response:")
                        print("   " + "=" * 30)
                        response_str = json.dumps(tool_response, indent=4)
                        for line in response_str.split('\n'):
                            print(f"   {line}")
                        print("   " + "=" * 30)
                else:
                    print("   ℹ️  No API response")
                    
            elif hasattr(result['command'], 'recommendation_query'):
                print(f"   → Recommendation query (different endpoint)")
            else:
                print(f"   → Informational query (no API call)")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 60 + "\n")

if __name__ == "__main__":
    # Run the tests
    asyncio.run(test_parser_with_api())
    asyncio.run(test_multiple_queries()) 