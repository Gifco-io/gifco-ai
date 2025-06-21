"""Test script to demonstrate the new parser workflow with temporary restaurant storage."""

import sys
import os
sys.path.append('gifco-ai')

from app.commands.parser import CommandParser


def test_parser_workflow():
    """Test the new parser workflow with temporary restaurant storage."""
    
    # Initialize parser
    parser = CommandParser()
    
    print("🍽️  Restaurant Parser Workflow Test")
    print("=" * 50)
    
    # Step 1: Search for restaurants (this should add restaurants to temp storage)
    print("\n1. Searching for restaurants...")
    search_result = parser.parse_and_execute("find best pizza places in New York")
    
    print(f"Command: {search_result.get('command')}")
    print(f"Tool Response: {search_result.get('tool_response', 'None')[:200]}...")
    
    # Check if we got a collection prompt
    if search_result.get('collection_prompt'):
        print(f"\n📋 Collection Prompt: {search_result['collection_prompt']}")
        
        # Step 2: Simulate user saying "yes" to create collection
        print("\n2. User responds 'yes' to create collection...")
        
        # For testing, we'll need an auth token (in real usage this would come from user)
        mock_auth_token = "test_token_123"
        
        yes_result = parser.parse_and_execute("yes", auth_token=mock_auth_token)
        
        print(f"Collection Creation Result: {yes_result}")
        
    else:
        print("❌ No collection prompt generated")
    
    # Step 3: Check temporary storage
    print(f"\n3. Temporary restaurants count: {len(parser.get_temp_restaurants())}")
    
    # Step 4: Test clearing temp storage
    parser.clear_temp_restaurants()
    print(f"4. After clearing - Temporary restaurants count: {len(parser.get_temp_restaurants())}")
    
    print("\n✅ Workflow test completed!")


def test_collection_prompt():
    """Test collection prompt generation."""
    
    parser = CommandParser()
    
    # Add mock restaurants to temp storage
    mock_restaurants = [
        {"id": "rest_1", "name": "Tony's Pizza Palace"},
        {"id": "rest_2", "name": "Mario's Italian Kitchen"},
        {"id": "rest_3", "name": "Giuseppe's Pizzeria"},
        {"id": "rest_4", "name": "Luigi's Pizza Corner"},
    ]
    
    parser.add_to_temp_restaurants(mock_restaurants)
    
    prompt = parser.get_collection_prompt()
    print(f"🎯 Collection prompt: {prompt}")
    
    # Test with fewer restaurants
    parser.clear_temp_restaurants()
    parser.add_to_temp_restaurants(mock_restaurants[:2])
    
    prompt = parser.get_collection_prompt()
    print(f"🎯 Collection prompt (2 restaurants): {prompt}")


if __name__ == "__main__":
    print("Testing collection prompt generation...")
    test_collection_prompt()
    
    print("\n" + "="*60 + "\n")
    
    print("Testing full parser workflow...")
    test_parser_workflow() 