#!/usr/bin/env python3
"""Simple script to run conversation tests."""

import os
import sys
import subprocess
from pathlib import Path

def setup_environment():
    """Set up the environment for testing."""
    # Set environment variables if not already set
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set. You may need to set this environment variable.")
    
    if not os.getenv("OPENAI_BASE_URL"):
        os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"
        print("🔧 Set OPENAI_BASE_URL to OpenRouter")
    
    if not os.getenv("RESTAURANT_SERVER_URL"):
        os.environ["RESTAURANT_SERVER_URL"] = "http://dev.gifco.io"
        print("🔧 Set RESTAURANT_SERVER_URL to dev.gifco.io")

def run_tests():
    """Run the conversation tests."""
    print("🚀 Running Restaurant Conversation Tests")
    print("=" * 50)
    
    # Setup environment
    setup_environment()
    
    # Get the path to the test file
    test_file = Path(__file__).parent / "test_conversation_flow.py"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return 1
    
    try:
        # Run the test file
        result = subprocess.run([sys.executable, str(test_file)], 
                              capture_output=False, 
                              text=True)
        
        if result.returncode == 0:
            print("\n✅ All tests completed successfully!")
        else:
            print(f"\n❌ Tests failed with return code: {result.returncode}")
        
        return result.returncode
        
    except Exception as e:
        print(f"❌ Error running tests: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code) 