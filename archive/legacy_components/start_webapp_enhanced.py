#!/usr/bin/env python3
"""
Enhanced BITTEN WebApp Server with Socket.IO support
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        # Install Flask-SocketIO and dependencies
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements_webapp.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_redis():
    """Check if Redis is available"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        print("✅ Redis connection verified")
        return True
    except Exception as e:
        print(f"⚠️  Redis not available: {e}")
        print("   Using in-memory storage fallback")
        return False

def start_server():
    """Start the enhanced web application server"""
    print("🚀 Starting BITTEN Enhanced WebApp Server...")
    
    # Import the app
    from src.bitten_core.web_app import app, socketio
    
    # Set environment variables
    os.environ['FLASK_ENV'] = 'production'
    os.environ['FLASK_SECRET_KEY'] = 'bitten-mission-briefing-secret-key'
    
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    
    print(f"🌐 Server starting on http://0.0.0.0:{port}")
    print(f"🎯 Mission briefing available at: http://localhost:{port}/mission/<signal_id>")
    print(f"📊 API endpoints available at: http://localhost:{port}/api/")
    print(f"🔌 Socket.IO enabled for real-time updates")
    print(f"💾 Data storage: {'Redis' if check_redis() else 'In-memory'}")
    
    try:
        # Start the server with Socket.IO support
        socketio.run(app, 
                    host='0.0.0.0', 
                    port=port, 
                    debug=False,
                    use_reloader=False,
                    log_output=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

def main():
    """Main entry point"""
    print("🎯 BITTEN Enhanced WebApp Server")
    print("=" * 50)
    
    # Check if running from correct directory
    if not Path("src/bitten_core/web_app.py").exists():
        print("❌ Please run this script from the HydraX-v2 root directory")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies. Please install manually:")
        print("   pip install Flask Flask-SocketIO redis python-socketio eventlet")
        sys.exit(1)
    
    # Check Redis (optional)
    check_redis()
    
    # Start the server
    start_server()

if __name__ == "__main__":
    main()