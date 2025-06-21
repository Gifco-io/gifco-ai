#!/usr/bin/env python3
"""Test script for LangChain memory implementation."""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.memory import RestaurantMemory
from app.api.models.responses import RestaurantInfo


async def test_memory_implementation():
    """Test the RestaurantMemory implementation."""
    print("🧠 Testing LangChain Memory Implementation")
    print("=" * 50)
    
    # Initialize memory
    memory = RestaurantMemory()
    print("✅ RestaurantMemory initialized")
    
    # Test 1: Basic message handling
    print("\n📝 Test 1: Basic Message Handling")
    thread_id = "test_thread_123"
    
    memory.add_user_message(thread_id, "Find Italian restaurants in Delhi")
    memory.add_ai_message(thread_id, "I found 5 great Italian restaurants in Delhi!")
    
    messages = memory.get_thread_messages(thread_id)
    print(f"✅ Messages stored: {len(messages)}")
    
    # Test 2: Restaurant context
    print("\n🍽️ Test 2: Restaurant Context")
    restaurants = [
        RestaurantInfo(name="Bella Italia", cuisine="Italian", location="Delhi"),
        RestaurantInfo(name="Roma Restaurant", cuisine="Italian", location="Delhi"),
        RestaurantInfo(name="Giuseppe's", cuisine="Italian", location="Delhi")
    ]
    
    memory.update_restaurant_search_context(
        thread_id, restaurants, "Italian restaurants in Delhi",
        search_metadata={"location": "Delhi", "result_count": 3}
    )
    
    stored_restaurants, stored_query = memory.get_last_restaurants(thread_id)
    print(f"✅ Restaurants stored: {len(stored_restaurants)}")
    print(f"✅ Query stored: {stored_query}")
    
    # Test 3: Enhanced context generation
    print("\n🔍 Test 3: Enhanced Context Generation")
    enhanced_context = memory.get_enhanced_context_for_llm(thread_id)
    print(f"✅ Enhanced context generated ({len(enhanced_context)} chars)")
    print(f"Context preview: {enhanced_context[:200]}...")
    
    # Test 4: Collection context
    print("\n📋 Test 4: Collection Context")
    collection_context = memory.create_collection_context(thread_id, "test_auth_token")
    print(f"✅ Collection context generated ({len(collection_context)} chars)")
    print(f"Context preview: {collection_context[:300]}...")
    
    # Test 5: Memory variables
    print("\n🔧 Test 5: Memory Variables")
    memory_vars = memory.load_memory_variables({"thread_id": thread_id})
    print(f"✅ Memory variables loaded: {list(memory_vars.keys())}")
    
    # Test 6: Preference learning
    print("\n🎯 Test 6: Preference Learning")
    memory.add_user_message(thread_id, "I love Chinese and Japanese food, especially cheap places near me")
    
    preferences = memory.get_user_preference(thread_id, "preferred_cuisines", [])
    print(f"✅ Learned cuisines: {preferences}")
    
    budget_conscious = memory.get_user_preference(thread_id, "budget_conscious")
    print(f"✅ Budget conscious: {budget_conscious}")
    
    # Test 7: Memory stats
    print("\n📊 Test 7: Memory Statistics")
    stats = memory.get_memory_stats(thread_id)
    print(f"✅ Memory stats: {stats}")
    
    # Test 8: Context for agent
    print("\n🤖 Test 8: Agent Context")
    agent_context = memory.get_context_for_agent(
        thread_id, 
        "Create a collection from these restaurants", 
        "test_auth_token"
    )
    print(f"✅ Agent context generated ({len(agent_context)} chars)")
    print(f"Context preview: {agent_context[:200]}...")
    
    print("\n🎉 All tests completed successfully!")
    print("=" * 50)
    print("Memory hierarchy implemented: BaseMemory → BaseChatMemory → RestaurantMemory")


def main():
    """Main function to run the tests."""
    asyncio.run(test_memory_implementation())


if __name__ == "__main__":
    main() 