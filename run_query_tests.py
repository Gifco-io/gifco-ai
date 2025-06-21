#!/usr/bin/env python3
"""Simple script to run /query API tests with different configurations."""

import asyncio
import sys
import os
from pathlib import Path

def print_usage():
    """Print usage information."""
    print("🎯 /query API Test Runner")
    print("=" * 50)
    print("Usage:")
    print("  python run_query_tests.py [options]")
    print()
    print("Options:")
    print("  --url <url>      API base URL (default: http://localhost:8000)")
    print("  --token <token>  Authorization token for collection creation")
    print("  --no-auth        Skip collection creation tests")
    print("  --help           Show this help message")
    print()
    print("Examples:")
    print("  python run_query_tests.py")
    print("  python run_query_tests.py --url http://localhost:8000")
    print("  python run_query_tests.py --token your_jwt_token")
    print("  python run_query_tests.py --no-auth")

def parse_args():
    """Parse command line arguments."""
    args = sys.argv[1:]
    config = {
        "url": "http://localhost:8000",
        "token": "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IkV3ZmZncFlOdVoxTTBERHdtdngxTmNIRVlYMm9YSzEwZDhYRFl5ZUllTXMifQ.eyJzaWQiOiJjbWMyNXFmMWowMGk3bDQwbWM3ZGM2cmx5IiwiaXNzIjoicHJpdnkuaW8iLCJpYXQiOjE3NTAyNjM1NjEsImF1ZCI6ImNtOHVqNDRyaDAwMDM4dmJsZGJxMW5vcXUiLCJzdWIiOiJkaWQ6cHJpdnk6Y204dzE2eDM2MDFqZXJheWN5MDdmZHhlaiIsImV4cCI6MTc1MDI2NzE2MX0.mziaGFByr9Oyah9fHtdjExST8F5BP9zb1w4VOLFc0F7njx94biQVyOTCF3WMXC_G7nDBW4OXtZecRy1YvvQitQ",
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
    """Run the /query API tests with the given configuration."""
    
    print("🚀 Starting /query API Tests")
    print("=" * 40)
    print(f"🌐 API URL: {config['url']}")
    print(f"🔑 Auth Token: {'Provided' if config['token'] else 'Not provided'}")
    print("=" * 40)
    
    try:
        # Import the test class
        from test_query_api import QueryAPITester
        
        async with QueryAPITester(config["url"]) as tester:
            await tester.run_complete_query_test(config["token"])
        
        print("\n✅ /query API tests completed successfully!")
        return 0
        
    except ImportError as e:
        print(f"\n❌ Failed to import test module: {str(e)}")
        print("Make sure test_query_api.py exists in the same directory")
        return 1
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
    
    # Check if test file exists
    test_file = Path(__file__).parent / "test_query_api.py"
    if not test_file.exists():
        print(f"❌ Error: Test file not found: {test_file}")
        print("Make sure test_query_api.py exists in the same directory")
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