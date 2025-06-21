#!/usr/bin/env python3
"""Demonstration of improved collection name generation."""

import datetime


def demonstrate_collection_name_generation():
    """Show how collection names are now generated."""
    print("🎯 Collection Name Generation - Before vs After")
    print("=" * 60)
    
    # Get current timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    
    print("❌ BEFORE (Fixed names causing conflicts):")
    print("   - 'My Restaurant Collection' (always the same)")
    print("   - 'Collection' (generic)")
    print("   - 'Favorites from search' (predictable)")
    print("   - Result: 'Collection name already exists' errors")
    
    print("\n✅ AFTER (LLM-generated unique names):")
    
    # Example scenarios
    scenarios = [
        {
            "query": "best Italian restaurants in Delhi",
            "cuisines": ["Italian"],
            "locations": ["Delhi"],
            "generated_names": [
                f"Italian Gems in Delhi - {timestamp}",
                f"Best Italian Spots - {timestamp}",
                f"Delhi Italian Collection - {timestamp}"
            ]
        },
        {
            "query": "find pizza places near me",
            "cuisines": ["Italian", "Fast Food"],
            "locations": ["New Delhi"],
            "generated_names": [
                f"Pizza Collection - {timestamp}",
                f"Best Pizza Spots Found - {timestamp}",
                f"Pizza Favorites - {timestamp}"
            ]
        },
        {
            "query": "romantic dinner spots in Mumbai",
            "cuisines": ["Continental", "Indian"],
            "locations": ["Mumbai"],
            "generated_names": [
                f"Romantic Dining - {timestamp}",
                f"Mumbai Date Night - {timestamp}",
                f"Romantic Dinner Collection - {timestamp}"
            ]
        },
        {
            "query": "budget friendly restaurants",
            "cuisines": ["Mixed"],
            "locations": ["Various"],
            "generated_names": [
                f"Budget Friendly Eats - {timestamp}",
                f"Affordable Dining - {timestamp}",
                f"Budget Collection - {timestamp}"
            ]
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. Query: '{scenario['query']}'")
        print(f"   Context: {', '.join(scenario['cuisines'])} in {', '.join(scenario['locations'])}")
        print(f"   LLM Generated Names:")
        for name in scenario['generated_names']:
            print(f"      • {name}")
    
    print(f"\n🔧 Technical Implementation:")
    print(f"   • Timestamp format: YYYYMMDD_HHMM (e.g., {timestamp})")
    print(f"   • Context analysis: Query + Cuisines + Locations")
    print(f"   • LLM instruction: Generate unique, descriptive names")
    print(f"   • Fallback: Smart keyword detection + timestamp")
    
    print(f"\n🎉 Benefits:")
    print(f"   ✅ No more 'collection name already exists' errors")
    print(f"   ✅ Meaningful names based on search context")
    print(f"   ✅ Automatic uniqueness with timestamps")
    print(f"   ✅ User can still specify custom names")
    print(f"   ✅ LLM creativity for better naming")
    
    print(f"\n💡 Examples in Action:")
    print(f"   User: 'find Italian restaurants' → 'yes'")
    print(f"   System: Creates 'Italian Gems in Delhi - {timestamp}'")
    print(f"   ")
    print(f"   User: 'create collection called My Favorites'")
    print(f"   System: Creates 'My Favorites - {timestamp}'")
    print(f"   ")
    print(f"   User: 'budget restaurants' → 'yes'")
    print(f"   System: Creates 'Budget Friendly Eats - {timestamp}'")


if __name__ == "__main__":
    demonstrate_collection_name_generation() 