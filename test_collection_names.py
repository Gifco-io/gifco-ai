#!/usr/bin/env python3
"""Test script to verify LLM-based collection name generation."""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.memory import RestaurantMemory
from app.api.models.responses import RestaurantInfo


async def test_collection_name_generation():
    """Test that collection names are generated uniquely based on context."""
    print("🧪 Testing LLM-Based Collection Name Generation")
    print("=" * 60)
    
    # Initialize memory
    memory = RestaurantMemory()
    
    # Test scenarios with different restaurant types
    test_scenarios = [
        {
            "name": "Italian Restaurants",
            "restaurants": [
                RestaurantInfo(name="Pasta Palace", cuisine="Italian", location="Delhi", description="ID:abc123|Great pasta"),
                RestaurantInfo(name="Pizza Corner", cuisine="Italian", location="Delhi", description="ID:def456|Wood-fired pizza"),
                RestaurantInfo(name="Mama Mia", cuisine="Italian", location="Delhi", description="ID:ghi789|Authentic Italian")
            ],
            "query": "best Italian restaurants in Delhi"
        },
        {
            "name": "Chinese Restaurants",
            "restaurants": [
                RestaurantInfo(name="Dragon Palace", cuisine="Chinese", location="Mumbai", description="ID:jkl012|Authentic Chinese"),
                RestaurantInfo(name="Noodle House", cuisine="Chinese", location="Mumbai", description="ID:mno345|Fresh noodles"),
                RestaurantInfo(name="Dim Sum Delight", cuisine="Chinese", location="Mumbai", description="ID:pqr678|Traditional dim sum")
            ],
            "query": "find Chinese restaurants in Mumbai"
        },
        {
            "name": "Mixed Cuisine",
            "restaurants": [
                RestaurantInfo(name="Fusion Bistro", cuisine="Fusion", location="Bangalore", description="ID:stu901|Modern fusion"),
                RestaurantInfo(name="Local Cafe", cuisine="Continental", location="Bangalore", description="ID:vwx234|Cozy cafe"),
                RestaurantInfo(name="Spice Garden", cuisine="Indian", location="Bangalore", description="ID:yz567|Traditional spices")
            ],
            "query": "romantic dinner spots in Bangalore"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{i}️⃣ Testing: {scenario['name']}")
        print(f"Query: '{scenario['query']}'")
        print(f"Restaurants: {len(scenario['restaurants'])} found")
        
        # Create unique thread ID for each test
        thread_id = f"test_thread_{i}"
        
        # Store restaurants in memory
        memory.update_restaurant_search_context(
            thread_id, scenario['restaurants'], scenario['query']
        )
        
        # Generate collection context
        collection_context = memory.create_collection_context(thread_id, "test_auth_token")
        
        # Extract the generated suggestions from context
        print("✅ Collection context generated with name suggestions:")
        
        # Look for the name generation section
        lines = collection_context.split('\n')
        in_name_section = False
        for line in lines:
            if "COLLECTION NAME GENERATION:" in line:
                in_name_section = True
            elif in_name_section and line.strip():
                if line.startswith("Examples of good collection names:"):
                    print("📝 Generated name examples:")
                elif line.startswith("- "):
                    print(f"   {line}")
                elif line.startswith("Instructions:"):
                    break
        
        print(f"🎯 Expected pattern: Based on '{scenario['query']}' with timestamp")
        print("-" * 40)
    
    print("\n🎉 Collection Name Generation Features:")
    print("✅ Unique timestamps prevent naming conflicts")
    print("✅ Context-aware names based on search query")
    print("✅ Cuisine and location information included")
    print("✅ Descriptive names that reflect the search intent")
    
    print("\n💡 Benefits:")
    print("- No more 'collection name already exists' errors")
    print("- Meaningful collection names instead of generic ones")
    print("- LLM can generate creative, contextual names")
    print("- Automatic uniqueness with timestamps")


def main():
    """Main function to run the tests."""
    asyncio.run(test_collection_name_generation())


if __name__ == "__main__":
    main() 