#!/usr/bin/env python3
"""Simple launcher for the restaurant chat CLI."""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Launch the chat CLI with environment variables."""
    
    # Set default environment variables if not already set
    if not os.getenv("API_BASE_URL"):
        os.environ["API_BASE_URL"] = "http://localhost:8000"
    
    # Get the path to the chat CLI
    chat_cli_path = Path(__file__).parent / "chat_cli.py"
    
    if not chat_cli_path.exists():
        print("❌ Error: chat_cli.py not found")
        return 1
    
    # Launch the chat CLI with all arguments passed through
    try:
        result = subprocess.run([sys.executable, str(chat_cli_path)] + sys.argv[1:])
        return result.returncode
    except KeyboardInterrupt:
        print("\n👋 Chat interrupted. Goodbye!")
        return 0
    except Exception as e:
        print(f"❌ Error launching chat: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 