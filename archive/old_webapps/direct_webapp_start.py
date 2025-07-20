#!/usr/bin/env python3
"""
Direct webapp startup bypassing all issues
"""
import os
import sys
import subprocess

# Add to Python path
sys.path.insert(0, '/root/HydraX-v2/src')

def install_deps():
    """Install dependencies directly"""
    deps = ['flask', 'flask-socketio', 'eventlet', 'redis']
    for dep in deps:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', dep], check=True)
            print(f"✅ Installed {dep}")
        except:
            print(f"⚠️ Failed to install {dep}")

def start_webapp():
    """Start webapp directly"""
    os.chdir('/root/HydraX-v2')
    
    try:
        # Install deps first
        install_deps()
        
        # Import and start
        from bitten_core.web_app import app, socketio
        print("🚀 BITTEN WebApp starting on 0.0.0.0:5000")
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        
        # Fallback: Simple Flask app
        try:
            from flask import Flask
            fallback_app = Flask(__name__)
            
            @fallback_app.route('/health')
            def health():
                return {"status": "ok", "service": "BITTEN WebApp", "mode": "fallback"}
            
            @fallback_app.route('/')
            def index():
                return "<h1>BITTEN WebApp - Emergency Mode</h1><p>Service is running in fallback mode.</p>"
            
            print("🚨 Starting in EMERGENCY FALLBACK mode")
            fallback_app.run(host='0.0.0.0', port=5000)
            
        except Exception as fallback_error:
            print(f"💥 Complete failure: {fallback_error}")

if __name__ == "__main__":
    start_webapp()