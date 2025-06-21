#!/usr/bin/env python3
"""Simple script to run API conversation tests with different configurations."""

import asyncio
import sys
import os
from test_api_conversation import APIConversationTester

def print_usage():
    """Print usage information."""
    print("🎯 Restaurant API Test Runner")
    print("=" * 50)
    print("Usage:")
    print("  python run_api_tests.py [options]")
    print()
    print("Options:")
    print("  --url <url>      API base URL (default: http://localhost:8000)")
    print("  --token <token>  Authorization token for collection creation")
    print("  --no-auth        Skip collection creation tests")
    print("  --help           Show this help message")
    print()
    print("Examples:")
    print("  python run_api_tests.py")
    print("  python run_api_tests.py --url http://localhost:8000")
    print("  python run_api_tests.py --token your_jwt_token")
    print("  python run_api_tests.py --no-auth")

def parse_args():
    """Parse command line arguments."""
    args = sys.argv[1:]
    config = {
        "url": "http://localhost:8000",
        "token": None,
        "help": False
    }
    
    i = 0
    while i < len(args):
        arg = args[i]
        
        if arg in ["--help", "-h"]:
            config["help"] = True
            break
        elif arg == "--url":
            if i + 1 < len(args):
                config["url"] = args[i + 1]
                i += 1
            else:
                print("❌ Error: --url requires a value")
                sys.exit(1)
        elif arg == "--token":
            if i + 1 < len(args):
                config["token"] = args[i + 1]
                i += 1
            else:
                print("❌ Error: --token requires a value")
                sys.exit(1)
        elif arg == "--no-auth":
            config["token"] = None
        else:
            print(f"❌ Error: Unknown argument '{arg}'")
            print("Use --help for usage information")
            sys.exit(1)
        
        i += 1
    
    return config

async def run_tests(config):
    """Run the API tests with the given configuration."""
    
    print("🚀 Starting API Tests")
    print("=" * 40)
    print(f"🌐 API URL: {config['url']}")
    print(f"🔑 Auth Token: {'Provided' if config['token'] else 'Not provided'}")
    print("=" * 40)
    
    try:
        async with APIConversationTester(config["url"]) as tester:
            await tester.run_complete_api_test(config["token"])
        
        print("\n✅ API tests completed successfully!")
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Tests failed with error: {str(e)}")
        return 1

def main():
    """Main function."""
    
    # Parse arguments
    config = parse_args()
    
    if config["help"]:
        print_usage()
        return 0
    
    # Check if aiohttp is available
    try:
        import aiohttp
    except ImportError:
        print("❌ Error: aiohttp is required for API tests")
        print("Install it with: pip install aiohttp")
        return 1
    
    # Run tests
    try:
        exit_code = asyncio.run(run_tests(config))
        return exit_code
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 