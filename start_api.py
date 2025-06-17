"""Startup script for the Restaurant Recommender API."""
import os
import sys
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Start the FastAPI server."""
    # Get configuration from environment or use defaults
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "true").lower() == "true"
    log_level = os.getenv("API_LOG_LEVEL", "info")
    
    print("🚀 Starting Restaurant Recommender API...")
    print(f"📍 Server: http://{host}:{port}")
    print(f"📖 Docs: http://{host}:{port}/docs")
    print(f"🔄 Reload: {reload}")
    print(f"📝 Log Level: {log_level}")
    print("\n" + "="*50 + "\n")
    
    try:
        # Start the server
        uvicorn.run(
            "app.api.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level=log_level,
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 