#!/usr/bin/env python3
"""Command-line interface for conversing with the restaurant recommendation agent."""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

class RestaurantChatCLI:
    """Command-line interface for restaurant recommendation conversations."""
    
    def __init__(self, api_base_url: str = "http://localhost:8000", auth_token: Optional[str] = None):
        """Initialize the chat CLI.
        
        Args:
            api_base_url: Base URL of the API server
            auth_token: Optional authorization token for collection creation
        """
        self.api_base_url = api_base_url
        self.auth_token = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IkV3ZmZncFlOdVoxTTBERHdtdngxTmNIRVlYMm9YSzEwZDhYRFl5ZUllTXMifQ.eyJzaWQiOiJjbWM1N2JydW4wMW5sbDcwbWE0emt5OXg4IiwiaXNzIjoicHJpdnkuaW8iLCJpYXQiOjE3NTA0NDc2MzUsImF1ZCI6ImNtOHVqNDRyaDAwMDM4dmJsZGJxMW5vcXUiLCJzdWIiOiJkaWQ6cHJpdnk6Y204dzE2eDM2MDFqZXJheWN5MDdmZHhlaiIsImV4cCI6MTc1MDQ1MTIzNX0.yXBZKj9-lo6ygVVy8JvQzCn6y8-NuQV173lV5XVfEJtQYduTATUfxDXvmHpAhGptvD9VFbtQjT27T41z9ees1g"
        self.session = None
        self.thread_id = str(uuid.uuid4())  # Generate unique thread ID for this session
        self.conversation_history = []
        self.default_location = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def send_query(self, query: str, location: Optional[str] = None) -> Dict[str, Any]:
        """Send a query to the restaurant API.
        
        Args:
            query: The user's query
            location: Optional location for the query
            
        Returns:
            Response from the API
        """
        url = f"{self.api_base_url}/query"
        
        # Use provided location or default location
        query_location = location or self.default_location
        
        # Prepare request body
        request_data = {
            "query": query,
            "thread_id": self.thread_id
        }
        if query_location:
            request_data["location"] = query_location
        
        # Prepare headers
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        try:
            async with self.session.post(url, json=request_data, headers=headers) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    return json.loads(response_text)
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {response_text}",
                        "status_code": response.status
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def display_welcome(self):
        """Display welcome message and instructions."""
        print("🍽️  Restaurant Recommendation Chat")
        print("=" * 50)
        print("Welcome to the Restaurant AI Assistant!")
        print()
        print("💡 What you can ask:")
        print("   • Find restaurants: 'best Italian restaurants in Delhi'")
        print("   • Get recommendations: 'romantic dinner spots in Mumbai'")
        print("   • Create collections: Search first, then say 'yes' or 'create collection'")
        print("   • Ask follow-ups: 'what about dessert places?'")
        print("   • Direct collection: 'create a collection called My Favorites'")
        print()
        print("🔧 Commands:")
        print("   • /location <city> - Set default location")
        print("   • /history - Show conversation history")
        print("   • /clear - Clear conversation history")
        print("   • /thread - Show current thread ID")
        print("   • /newthread - Create new conversation thread")
        print("   • /test - Show collection creation test instructions")
        print("   • /help - Show this help message")
        print("   • /quit or /exit - Exit the chat")
        print()
        print(f"🌐 Connected to: {self.api_base_url}")
        print(f"🧵 Thread ID: {self.thread_id}")
        print(f"🔑 Auth: {'Enabled' if self.auth_token else 'Disabled'}")
        print("=" * 50)
        print()
    
    def display_help(self):
        """Display help message."""
        print("\n📚 Help - Restaurant Chat Commands")
        print("=" * 40)
        print("🍽️  Restaurant Queries:")
        print("   'find Italian restaurants in Delhi'")
        print("   'best vegetarian places near me'")
        print("   'romantic dinner spots in Mumbai'")
        print("   'budget-friendly cafes in Bangalore'")
        print()
        print("📝 Collection Management:")
        print("   1. Search for restaurants first")
        print("   2. System will ask if you want to create a collection")
        print("   3. Respond with 'yes' or 'create collection' to create the collection")
        print("   4. Or directly: 'create a collection called My Favorites'")
        print("   Examples: 'yes', 'y', 'sure', 'okay', 'create collection'")
        print()
        print("💬 Conversation:")
        print("   'what about dessert places?'")
        print("   'show me more options'")
        print("   'any places with outdoor seating?'")
        print()
        print("🔧 System Commands:")
        print("   /location Delhi     - Set default location")
        print("   /history           - Show conversation")
        print("   /clear             - Clear history")
        print("   /thread            - Show thread ID")
        print("   /newthread         - Create new thread")
        print("   /test              - Collection test guide")
        print("   /quit              - Exit chat")
        print("=" * 40)
        print()
    
    def display_restaurants(self, restaurants: list, max_display: int = 5):
        """Display restaurant results in a formatted way.
        
        Args:
            restaurants: List of restaurant data
            max_display: Maximum number of restaurants to display
        """
        if not restaurants:
            return
            
        print(f"\n🍽️  Found {len(restaurants)} restaurants:")
        print("-" * 40)
        
        for i, restaurant in enumerate(restaurants[:max_display], 1):
            name = restaurant.get('name') or restaurant.get('title', 'Unknown Restaurant')
            location = restaurant.get('location') or restaurant.get('address', 'Location not specified')
            cuisine = restaurant.get('cuisine', '')
            rating = restaurant.get('rating', '')
            restaurant_id = restaurant.get('id') or restaurant.get('_id', '')
            
            print(f"{i}. {name}")
            print(f"   📍 {location}")
            if cuisine:
                print(f"   🍴 {cuisine}")
            if rating:
                print(f"   ⭐ {rating}")
            if restaurant_id:
                print(f"   🆔 {restaurant_id[:8]}...")
            print()
        
        if len(restaurants) > max_display:
            print(f"... and {len(restaurants) - max_display} more restaurants")
            print()

    def display_collection_result(self, response: Dict[str, Any]):
        """Display collection creation results.
        
        Args:
            response: Response from the API containing collection result
        """
        # Check if this is a collection creation response
        collection_result = response.get("collection_result")
        
        if collection_result:
            # Handle collection creation result from agent/parser
            if collection_result.get("success"):
                collection_name = collection_result.get("collection", {}).get("name", "Collection")
                added_count = collection_result.get("successfully_added", 0)
                total_count = collection_result.get("total_restaurants", 0)
                failed_restaurants = collection_result.get("failed_restaurants", [])
                
                print(f"\n✅ Collection '{collection_name}' created successfully!")
                print(f"📊 Results: {added_count}/{total_count} restaurants added")
                
                if failed_restaurants:
                    print(f"⚠️  {len(failed_restaurants)} restaurants failed to add:")
                    for failed in failed_restaurants:
                        restaurant_id = failed.get('restaurant_id', 'Unknown')
                        error = failed.get('error', 'Unknown error')
                        print(f"   • ID {restaurant_id}: {error}")
                
                # Show collection ID if available
                collection_id = collection_result.get("collection_id")
                if collection_id:
                    print(f"🆔 Collection ID: {collection_id}")
                    
            else:
                error_msg = collection_result.get("error", "Unknown error occurred")
                print(f"❌ Collection creation failed: {error_msg}")
        else:
            # Fallback for direct success/error messages
            if response.get("success"):
                print(f"\n✅ {response.get('message', 'Collection created successfully!')}")
            else:
                error_msg = response.get("error", "Unknown error occurred")
                print(f"❌ Collection creation failed: {error_msg}")
    
    def save_to_history(self, user_query: str, ai_response: str, restaurants: list = None):
        """Save conversation to history.
        
        Args:
            user_query: User's input
            ai_response: AI's response
            restaurants: List of restaurants if any
        """
        self.conversation_history.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "user": user_query,
            "ai": ai_response,
            "restaurants_count": len(restaurants) if restaurants else 0
        })
    
    def display_history(self):
        """Display conversation history."""
        if not self.conversation_history:
            print("\n💭 No conversation history yet.")
            return
        
        print(f"\n📖 Conversation History ({len(self.conversation_history)} exchanges)")
        print("=" * 60)
        
        for i, entry in enumerate(self.conversation_history, 1):
            print(f"[{entry['timestamp']}] Exchange {i}")
            print(f"👤 You: {entry['user']}")
            print(f"🤖 AI: {entry['ai'][:100]}{'...' if len(entry['ai']) > 100 else ''}")
            if entry['restaurants_count'] > 0:
                print(f"🍽️  Found: {entry['restaurants_count']} restaurants")
            print("-" * 40)
        print()
    
    def handle_command(self, command: str) -> bool:
        """Handle system commands.
        
        Args:
            command: Command string starting with /
            
        Returns:
            True if should continue, False if should exit
        """
        command = command.lower().strip()
        
        if command in ['/quit', '/exit']:
            return False
        elif command == '/help':
            self.display_help()
        elif command == '/history':
            self.display_history()
        elif command == '/clear':
            self.conversation_history.clear()
            print("✅ Conversation history cleared.")
        elif command == '/thread':
            print(f"🧵 Current Thread ID: {self.thread_id}")
        elif command == '/newthread':
            import uuid
            self.thread_id = str(uuid.uuid4())
            print(f"🆕 New thread created: {self.thread_id}")
        elif command.startswith('/location '):
            location = command[10:].strip()
            self.default_location = location
            print(f"📍 Default location set to: {location}")
        elif command == '/test':
            print("🧪 Running collection creation test...")
            print("1. First, I'll search for Italian restaurants")
            print("2. Then you can say 'yes' to create a collection")
            print("   This will test the fixed collection creation workflow")
        else:
            print(f"❌ Unknown command: {command}")
            print("💡 Type /help for available commands.")
        
        return True
    
    async def run_chat(self):
        """Run the interactive chat session."""
        self.display_welcome()
        
        print("💬 Start chatting! (Type /help for commands, /quit to exit)")
        print()
        
        while True:
            try:
                # Get user input
                user_input = input("👤 You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle system commands
                if user_input.startswith('/'):
                    should_continue = self.handle_command(user_input)
                    if not should_continue:
                        break
                    continue
                
                # Show typing indicator
                print("🤖 AI: Thinking...", end="", flush=True)
                
                # Send query to API
                response = await self.send_query(user_input)
                
                # Clear typing indicator
                print("\r" + " " * 20 + "\r", end="", flush=True)
                
                # Handle response
                if response.get("success") is not False:  # Handle both True and None
                    ai_message = response.get("message", "I received your request.")
                    restaurants = response.get("restaurants", []) or []
                    collection_prompt = response.get("collection_prompt", "")
                    
                    # Check if this is a collection creation result
                    if response.get("collection_created") or response.get("collection_result"):
                        self.display_collection_result(response)
                        # Still show the AI message if it's not just a generic success message
                        if ai_message and not ai_message.startswith("✅"):
                            print(f"🤖 AI: {ai_message}")
                    else:
                        # Display AI response
                        print(f"🤖 AI: {ai_message}")
                        
                        # Display restaurants if any
                        if restaurants:
                            self.display_restaurants(restaurants)
                        
                        # Display collection prompt if available
                        if collection_prompt:
                            print(f"💬 {collection_prompt}")
                    
                    # Save to history
                    self.save_to_history(user_input, ai_message, restaurants)
                    
                else:
                    error_msg = response.get("error", "Unknown error occurred")
                    print(f"❌ Error: {error_msg}")
                    
                    # Check for auth errors
                    if "401" in str(error_msg) or "Access denied" in str(error_msg):
                        print("💡 This might be an authentication issue. Collection creation requires a valid token.")
                    elif "Authorization token required" in str(error_msg):
                        print("💡 Collection creation requires authentication. Please provide a valid auth token.")
                        print("   Use: python chat_cli.py --token 'your_jwt_token'")
                    elif "No recent restaurant search results" in str(error_msg):
                        print("💡 To create a collection, first search for restaurants, then say 'yes' or 'create collection'")
                        print("   Example: 'find Italian restaurants' → then → 'yes'")
                
                print()  # Add spacing
                
            except KeyboardInterrupt:
                print("\n\n👋 Chat interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {str(e)}")
                print("💡 Please try again or restart the chat.")
                print()


async def main():
    """Main function to run the chat CLI."""
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(
        description="Restaurant Recommendation Chat CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python chat_cli.py
  python chat_cli.py --url http://localhost:8000
  python chat_cli.py --token "your_jwt_token"
  python chat_cli.py --url http://localhost:3000 --token "token"
        """
    )
    
    parser.add_argument(
        "--url", 
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)"
    )
    
    parser.add_argument(
        "--token",
        help="JWT token for authentication (for collection creation)"
    )
    
    args = parser.parse_args()
    
    # Get configuration from environment variables if not provided
    api_url = args.url or os.getenv("API_BASE_URL", "http://localhost:8000")
    auth_token = args.token or os.getenv("AUTH_TOKEN")
    
    # Check if aiohttp is available
    try:
        import aiohttp
    except ImportError:
        print("❌ Error: aiohttp is required for the chat CLI")
        print("Install it with: pip install aiohttp")
        return 1
    
    # Run the chat
    try:
        async with RestaurantChatCLI(api_url, auth_token) as chat:
            await chat.run_chat()
        
        print("👋 Thanks for using Restaurant Chat! Goodbye!")
        return 0
        
    except KeyboardInterrupt:
        print("\n👋 Chat interrupted. Goodbye!")
        return 0
    except Exception as e:
        print(f"❌ Failed to start chat: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 