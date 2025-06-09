"""Test script to demonstrate the restaurant command parser."""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.commands.parser import CommandParser
from app.agent.base import RestaurantRecommenderAgent

async def test_parser():
    """Test the command parser with example queries."""
    print("🧪 Testing Restaurant Command Parser\n")
    
    # Initialize parser
    parser = CommandParser()
    
    # Test queries
    test_queries = [
        "Best butter chicken spot in new delhi?",
        "Find Italian restaurants in NYC",
        "Recommend a good restaurant for dinner",
        "Help me find restaurants",
        "Cheap vegetarian places near me"
    ]
    
    for query in test_queries:
        print(f"🔍 Query: '{query}'")
        try:
            command = parser.parse_request(query)
            print(f"✅ Parsed as: {type(command).__name__}")
            
            if hasattr(command, 'search_query'):
                q = command.search_query
                print(f"   - Query: {q.query}")
                print(f"   - Place: {q.place}")
                print(f"   - Cuisine: {q.cuisine}")
                
            elif hasattr(command, 'recommendation_query'):
                q = command.recommendation_query
                print(f"   - Query: {q.query}")
                print(f"   - Place: {q.place}")
                
            elif hasattr(command, 'topic'):
                print(f"   - Topic: {command.topic}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print("-" * 50)

async def test_full_agent():
    """Test the full agent with a restaurant query."""
    print("\n🤖 Testing Full Restaurant Agent\n")
    
    # Initialize agent
    agent = RestaurantRecommenderAgent()
    
    # Test the specific query
    query = "Best butter chicken spot in new delhi?"
    print(f"🔍 Query: '{query}'")
    
    try:
        response = await agent.handle_request(query)
        print(f"✅ Success: {response.success}")
        print(f"📝 Response:\n{response.message}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("=" * 60)
    print("🍽️  RESTAURANT RECOMMENDER SYSTEM TEST")
    print("=" * 60)
    
    # Run parser tests
    asyncio.run(test_parser())
    
    # Run full agent test
    asyncio.run(test_full_agent())
    
    print("\n✨ Test complete!") 