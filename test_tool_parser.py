#!/usr/bin/env python3
"""Test script for the tool-based command parser."""

import asyncio
import json
from app.commands.parser import CommandParser


async def test_parser_with_tools():
    """Test the command parser with tool-based API calls."""
    
    # Initialize parser
    parser = CommandParser()
    
    # Test case: "Best butter chicken spot in delhi?"
    test_request = "Best butter chicken spot in delhi?"
    
    print(f"Testing request: '{test_request}'")
    print("=" * 50)
    
    try:
        # Parse and execute with tools
        result = parser.parse_and_execute(test_request)
        
        print("✅ Parsing successful!")
        print(f"Command type: {type(result['command']).__name__}")
        
        if result['command']:
            command = result['command']
            print(f"Original request: {command.original_request}")
            
            if hasattr(command, 'search_query'):
                query = command.search_query
                print(f"Query: {query.query}")
                print(f"Place: {query.place}")
                print(f"Cuisine: {query.cuisine}")
            
        if result['tool_response']:
            print("\n🔧 Tool Response:")
            print(json.dumps(result['tool_response'], indent=2))
        
        if result.get('error'):
            print(f"\n❌ Error: {result['error']}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")


def test_tools_directly():
    """Test the restaurant tools directly."""
    
    from app.agent.tools.tools import get_restaurant_tools
    
    print("\n" + "="*50)
    print("Testing tools directly:")
    print("="*50)
    
    # Get tools
    tools = get_restaurant_tools()
    
    print(f"Available tools: {[tool.name for tool in tools]}")
    
    # Test search tool
    search_tool = next((tool for tool in tools if tool.name == "search_restaurants"), None)
    if search_tool:
        print(f"\n🔍 Testing search tool:")
        print(f"Tool name: {search_tool.name}")
        print(f"Description: {search_tool.description}")
        
        # Test with the butter chicken query
        try:
            result = search_tool.func(
                query="best butter chicken",
                place="delhi",
                query_type="current"
            )
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error calling tool: {e}")


if __name__ == "__main__":
    print("🚀 Testing Tool-based Command Parser")
    print("="*50)
    
    # Test tools directly first
    test_tools_directly()
    
    # Test parser with tools
    asyncio.run(test_parser_with_tools()) 