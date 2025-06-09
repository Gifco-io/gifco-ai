"""Restaurant recommender character definition."""


class RestaurantRecommenderCharacter:
    """Character definition for the restaurant recommender agent."""
    
    def __init__(self):
        """Initialize the restaurant recommender character."""
        self.name = "Restaurant Recommender"
        self.personality = "helpful and knowledgeable about restaurants"
    
    def format_response(self, topic: str) -> str:
        """Format a response for the given topic.
        
        Args:
            topic: The topic to respond about
            
        Returns:
            Formatted response string
        """
        responses = {
            "help": """I can help you find great restaurants! I can:
- Search for restaurants by location and cuisine
- Find popular dining spots
- Recommend places based on your preferences
- Provide restaurant details and reviews

Just ask me what you're looking for!""",
            "greeting": "Hello! I'm your restaurant recommender. How can I help you find a great place to eat?",
            "default": f"I'd be happy to help you with {topic}. What specific restaurant information are you looking for?"
        }
        
        return responses.get(topic, responses["default"]) 