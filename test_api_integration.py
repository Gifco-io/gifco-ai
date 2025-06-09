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
    
    # Initialize parser with server URL
    server_url = os.getenv("RESTAURANT_SERVER_URL", "{{server}}")  # Your server placeholder
    parser = CommandParser(server_url=server_url)
    
    # Test the specific query you mentioned
    test_query = "Best butter chicken spot in delhi?"
    
    print(f"🔍 Testing Query: '{test_query}'")
    print("=" * 60)
    
    try:
        # Parse and execute (includes API call if it's a search)
        result = await parser.parse_and_execute(test_query)
        
        print("✅ Parsing Results:")
        print(f"Command Type: {type(result['command']).__name__}")
        
        if hasattr(result['command'], 'search_query'):
            q = result['command'].search_query
            print(f"Parsed Query: {q.query}")
            print(f"Parsed Place: {q.place}")
            print(f"Parsed Cuisine: {q.cuisine}")
            
        print("\n🌐 API Call Details:")
        if result['api_response']:
            if 'error' in result['api_response']:
                print(f"❌ API Error: {result['api_response']['error']}")
            else:
                print("✅ API Response received:")
                print(json.dumps(result['api_response'], indent=2))
        else:
            print("ℹ️  No API call made (not a search command)")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🔗 Expected API Call:")
    print("URL: {{server}}/api/questions?type=current&place=New Delhi&q=best butter chicken")
    print("\nThis demonstrates how 'Best butter chicken spot in delhi?' gets converted to the API call you specified!")

async def test_multiple_queries():
    """Test multiple queries to show different parsing scenarios."""
    print("\n\n🧪 Testing Multiple Query Types\n")
    
    server_url = os.getenv("RESTAURANT_SERVER_URL", "{{server}}")
    parser = CommandParser(server_url=server_url)
    
    test_queries = [
        "Best butter chicken spot in delhi?",
        "Find Italian restaurants in Mumbai",
        "Recommend a good restaurant for dinner",
        "Pizza places near me in Bangalore"
    ]
    
    for query in test_queries:
        print(f"🔍 Query: '{query}'")
        try:
            # Just show the parsing (not API call to avoid spam)
            command = parser.parse_request(query)
            print(f"   → Command: {type(command).__name__}")
            
            if hasattr(command, 'search_query'):
                q = command.search_query
                formatted_place = parser._format_place_name(q.place or "")
                api_url = f"{{server}}/api/questions?type=current&place={formatted_place}&q={q.query}"
                print(f"   → Would call: {api_url}")
            elif hasattr(command, 'recommendation_query'):
                print(f"   → Recommendation query (different endpoint)")
            else:
                print(f"   → Informational query (no API call)")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
        print()

if __name__ == "__main__":
    # Run the tests
    asyncio.run(test_parser_with_api())
    asyncio.run(test_multiple_queries()) 