#!/usr/bin/env python3
"""Test script for complete conversational restaurant flow."""

import asyncio
import logging
import json
import sys
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent / "gifco-ai"
sys.path.insert(0, str(project_root))

from app.api.services.restaurant_service import RestaurantService
from app.api.models.responses import RestaurantInfo

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ConversationTester:
    """Test class for conversational restaurant flow."""
    
    def __init__(self):
        """Initialize the conversation tester."""
        self.service = RestaurantService()
        
    async def test_complete_conversation_flow(self):
        """Test the complete conversation flow from search to collection creation."""
        
        print("🎯 Testing Complete Conversational Flow")
        print("=" * 60)
        
        # Test data
        thread_id = f"test_conversation_{int(datetime.now().timestamp())}"
        auth_token = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IkV3ZmZncFlOdVoxTTBERHdtdngxTmNIRVlYMm9YSzEwZDhYRFl5ZUllTXMifQ.eyJzaWQiOiJjbWMyNXFmMWowMGk3bDQwbWM3ZGM2cmx5IiwiaXNzIjoicHJpdnkuaW8iLCJpYXQiOjE3NTAyNjM1NjEsImF1ZCI6ImNtOHVqNDRyaDAwMDM4dmJsZGJxMW5vcXUiLCJzdWIiOiJkaWQ6cHJpdnk6Y204dzE2eDM2MDFqZXJheWN5MDdmZHhlaiIsImV4cCI6MTc1MDI2NzE2MX0.mziaGFByr9Oyah9fHtdjExST8F5BP9zb1w4VOLFc0F7njx94biQVyOTCF3WMXC_G7nDBW4OXtZecRy1YvvQitQ"
        
        try:
            # Step 1: Restaurant Query via unified /query endpoint
            print("\n📍 Step 1: Restaurant Query via unified /query endpoint")
            print("-" * 50)
            
            query_response = await self.service.query(
                query="suggest me a good restaurant in new delhi",
                location="New Delhi",
                auth_token=auth_token
            )
            
            print(f"✅ Query Success: {query_response.success}")
            print(f"📝 AI Message: {query_response.message}")
            print(f"🍽️ Restaurants Found: {len(query_response.restaurants) if query_response.restaurants else 0}")
            
            if query_response.restaurants:
                print("\nRestaurant Details:")
                for i, restaurant in enumerate(query_response.restaurants[:3], 1):  # Show first 3
                    print(f"  {i}. {restaurant.name}")
                    if restaurant.location:
                        print(f"     📍 {restaurant.location[:80]}...")
                    if restaurant.description:
                        print(f"     🔗 {restaurant.description[:80]}...")
                print(f"  ... and {len(query_response.restaurants) - 3} more restaurants" if len(query_response.restaurants) > 3 else "")
            
            # Step 2: Verify conversation memory (restaurants automatically stored)
            print("\n💾 Step 2: Verifying conversation memory")
            print("-" * 50)
            
            if query_response.restaurants and query_response.thread_id:
                # Check if restaurants were automatically stored in memory
                stored_restaurants, stored_query = self.service.memory.get_last_restaurants(query_response.thread_id)
                print(f"✅ Restaurants automatically stored in memory: {len(stored_restaurants)}")
                print(f"📝 Stored query: {stored_query}")
            else:
                print("❌ No restaurants found or thread_id missing")
                return
            
            # Step 3: Collection Creation via unified /query endpoint
            print("\n💬 Step 3: Collection Creation via unified /query endpoint")
            print("-" * 50)
            
            collection_response = await self.service.query(
                query="create a collection called 'My Delhi Favorites'",
                thread_id=query_response.thread_id,  # Use thread_id from previous response
                auth_token=auth_token
            )
            
            print(f"✅ Collection Success: {collection_response.success}")
            print(f"📝 AI Response: {collection_response.message}")
            print(f"🎯 Command Type: {collection_response.command_type}")
            print(f"🧵 Thread ID: {collection_response.thread_id}")
            
            if not collection_response.success:
                print(f"❌ Error: {collection_response.error}")
            
            # Step 4: Follow-up conversation
            print("\n🔄 Step 4: Follow-up conversation")
            print("-" * 50)
            
            followup_response = await self.service.query(
                query="What other Indian restaurants do you recommend?",
                thread_id=collection_response.thread_id,  # Continue same conversation
                auth_token=auth_token
            )
            
            print(f"✅ Follow-up Success: {followup_response.success}")
            print(f"📝 AI Response: {followup_response.message}")
            print(f"🧵 Thread ID: {followup_response.thread_id}")
            
            print("\n🎉 Complete conversation flow test completed!")
            
        except Exception as e:
            print(f"❌ Error during conversation flow test: {str(e)}")
            logger.error(f"Conversation flow test failed: {str(e)}", exc_info=True)

    async def test_memory_functionality(self):
        """Test the conversation memory functionality."""
        
        print("\n🧠 Testing Memory Functionality")
        print("=" * 60)
        
        thread_id = "memory_test_123"
        
        # Test 1: Basic memory operations
        print("\n📝 Test 1: Basic memory operations")
        print("-" * 40)
        
        # Add messages to memory
        self.service.memory.add_user_message(thread_id, "Find Italian restaurants in Delhi")
        self.service.memory.add_ai_message(thread_id, "Here are some great Italian places...")
        
        messages = self.service.memory.get_thread_messages(thread_id)
        print(f"✅ Messages stored: {len(messages)}")
        
        for msg in messages:
            role = "Human" if msg.__class__.__name__ == "HumanMessage" else "Assistant"
            content = msg.content
            print(f"  {role}: {content}")
        
        # Test 2: Restaurant memory
        print("\n🍽️ Test 2: Restaurant memory")
        print("-" * 40)
        
        # Create test restaurants
        test_restaurants = [
            RestaurantInfo(
                name="Olive Bar & Kitchen",
                location="Multiple locations in Delhi",
                cuisine="Italian",
                description="ID:test_001|Popular Italian restaurant"
            ),
            RestaurantInfo(
                name="Big Chill Cafe", 
                location="Khan Market, Delhi",
                cuisine="Continental",
                description="ID:test_002|Casual dining with Italian options"
            )
        ]
        
        # Store restaurants in memory
        self.service.memory.set_last_restaurants(thread_id, test_restaurants, "Italian restaurants in Delhi")
        
        # Retrieve restaurants from memory
        retrieved_restaurants, query = self.service.memory.get_last_restaurants(thread_id)
        
        print(f"✅ Restaurants stored and retrieved: {len(retrieved_restaurants)}")
        print(f"📝 Original query: {query}")
        
        for restaurant in retrieved_restaurants:
            print(f"  🍽️ {restaurant.name} - {restaurant.location}")
            if restaurant.description:
                print(f"     📋 {restaurant.description}")
        
        # Test 3: Collection request detection
        print("\n🔍 Test 3: Collection request detection")
        print("-" * 40)
        
        test_messages = [
            "create a collection",
            "make a collection from these",
            "save these restaurants",
            "create list",
            "what's the weather like?",  # Should not be detected
            "collection of restaurants"
        ]
        
        for message in test_messages:
            is_collection = self.service._is_collection_request(message)
            status = "✅" if is_collection else "❌"
            print(f"  {status} '{message}' -> Collection request: {is_collection}")

    async def test_ai_message_generation(self):
        """Test AI message generation functionality."""
        
        print("\n🤖 Testing AI Message Generation")
        print("=" * 60)
        
        # Test 1: Message generation with restaurants
        print("\n📝 Test 1: AI message with restaurants")
        print("-" * 40)
        
        test_restaurants = [
            RestaurantInfo(name="Test Restaurant 1", location="Delhi"),
            RestaurantInfo(name="Test Restaurant 2", location="Mumbai"),
            RestaurantInfo(name="Test Restaurant 3", location="Bangalore")
        ]
        
        try:
            ai_message = await self.service._generate_ai_message(
                query="good restaurants",
                restaurants=test_restaurants,
                location="Delhi"
            )
            print(f"✅ AI Message Generated:")
            print(f"   {ai_message}")
        except Exception as e:
            print(f"❌ AI message generation failed: {str(e)}")
        
        # Test 2: Fallback message
        print("\n🔄 Test 2: Fallback message")
        print("-" * 40)
        
        fallback_message = self.service._create_simple_ai_message(
            query="test query",
            restaurants=test_restaurants,
            location="Delhi"
        )
        print(f"✅ Fallback Message:")
        print(f"   {fallback_message}")

    async def test_error_handling(self):
        """Test error handling scenarios."""
        
        print("\n⚠️ Testing Error Handling")
        print("=" * 60)
        
        # Test 1: Empty query
        print("\n🔍 Test 1: Empty query handling")
        print("-" * 40)
        
        try:
            response = await self.service.query(query="", location="Delhi")
            print(f"Empty query result - Success: {response.success}")
            if not response.success:
                print(f"Error message: {response.error}")
        except Exception as e:
            print(f"Exception handled: {str(e)}")
        
        # Test 2: Query with new thread (auto-generated)
        print("\n🔄 Test 2: Query with new thread")
        print("-" * 40)
        
        try:
            response = await self.service.query(
                query="Hello, I'm looking for restaurants",
                thread_id=None  # Will generate new thread ID
            )
            print(f"New thread result - Success: {response.success}")
            print(f"Generated thread ID: {response.thread_id}")
            print(f"Message: {response.message[:100]}...")
        except Exception as e:
            print(f"Exception handled: {str(e)}")

    async def run_all_tests(self):
        """Run all tests in sequence."""
        
        print("🚀 Starting Complete Conversation Tests")
        print("=" * 80)
        print(f"⏰ Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        try:
            await self.test_memory_functionality()
            await self.test_ai_message_generation()
            await self.test_error_handling()
            await self.test_complete_conversation_flow()
            
            print("\n" + "=" * 80)
            print("🎉 All tests completed successfully!")
            print(f"⏰ End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ Test suite failed with error: {str(e)}")
            logger.error(f"Test suite failed: {str(e)}", exc_info=True)


async def main():
    """Main test function."""
    
    print("🎯 Restaurant Unified Endpoint Tests")
    print("Testing unified /query endpoint for restaurant search and conversation")
    print()
    
    tester = ConversationTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    # Run the complete test suite
    asyncio.run(main()) 