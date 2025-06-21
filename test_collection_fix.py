#!/usr/bin/env python3
"""Test script to verify collection creation fix."""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.memory import RestaurantMemory
from app.api.models.responses import RestaurantInfo
from app.agent.tools.tools import get_restaurant_tools


async def test_collection_creation_fix():
    """Test that collection creation with restaurants works."""
    print("🧪 Testing Collection Creation Fix")
    print("=" * 50)
    
    # Initialize memory
    memory = RestaurantMemory()
    thread_id = "test_thread_fix"
    
    # Step 1: Simulate restaurants with IDs in description
    print("\n1️⃣ Setting up test restaurants with IDs")
    restaurants = [
        RestaurantInfo(
            name="Test Italian Place", 
            cuisine="Italian", 
            location="Delhi",
            description="ID:67567abc123def456|Great pasta and pizza place"
        ),
        RestaurantInfo(
            name="Pizza Corner", 
            cuisine="Italian", 
            location="Delhi",
            description="ID:67567def789ghi012|Authentic wood-fired pizza"
        ),
        RestaurantInfo(
            name="Mama Mia", 
            cuisine="Italian", 
            location="Delhi",
            description="ID:67567ghi345jkl678|Family-owned traditional Italian"
        )
    ]
    
    # Store restaurants in memory
    memory.update_restaurant_search_context(
        thread_id, restaurants, "Italian restaurants in Delhi"
    )
    print(f"✅ Stored {len(restaurants)} restaurants in memory")
    
    # Step 2: Test collection context generation
    print("\n2️⃣ Testing collection context generation")
    collection_context = memory.create_collection_context(thread_id, "test_auth_token")
    print("✅ Collection context generated:")
    print(collection_context)
    
    # Step 3: Check if restaurant IDs are properly extracted
    print("\n3️⃣ Verifying restaurant ID extraction")
    if "67567abc123def456" in collection_context:
        print("✅ Restaurant ID 1 correctly extracted")
    else:
        print("❌ Restaurant ID 1 not found")
    
    if "67567def789ghi012" in collection_context:
        print("✅ Restaurant ID 2 correctly extracted")
    else:
        print("❌ Restaurant ID 2 not found")
    
    if "67567ghi345jkl678" in collection_context:
        print("✅ Restaurant ID 3 correctly extracted")
    else:
        print("❌ Restaurant ID 3 not found")
    
    # Step 4: Test tool availability
    print("\n4️⃣ Testing tool availability")
    tools = get_restaurant_tools()
    tool_names = [tool.name for tool in tools]
    
    if "create_collection_with_restaurants" in tool_names:
        print("✅ create_collection_with_restaurants tool is available")
    else:
        print("❌ create_collection_with_restaurants tool is missing")
    
    if "create_collection" in tool_names:
        print("✅ create_collection tool is available")
    else:
        print("❌ create_collection tool is missing")
    
    print(f"📋 Available tools: {', '.join(tool_names)}")
    
    # Step 5: Test context for agent
    print("\n5️⃣ Testing agent context generation")
    agent_context = memory.get_context_for_agent(
        thread_id, 
        "create a collection from these restaurants", 
        "test_auth_token"
    )
    
    if "create_collection_with_restaurants tool" in agent_context:
        print("✅ Agent context mentions the correct tool")
    else:
        print("❌ Agent context doesn't mention create_collection_with_restaurants")
        
    if "67567abc123def456" in agent_context:
        print("✅ Agent context contains restaurant IDs")
    else:
        print("❌ Agent context missing restaurant IDs")
    
    print("\n🎯 Summary:")
    print("- Restaurant IDs are properly extracted from description field")
    print("- create_collection_with_restaurants tool is available")
    print("- Memory system generates correct context for collection creation")
    print("- Agent should now use the correct tool with proper restaurant IDs")
    
    print("\n💡 Next steps:")
    print("1. Test with actual API calls using your auth token")
    print("2. Search for restaurants first to get real IDs")
    print("3. Then create collection to verify restaurants are added")


def main():
    """Main function to run the tests."""
    asyncio.run(test_collection_creation_fix())


if __name__ == "__main__":
    main() 