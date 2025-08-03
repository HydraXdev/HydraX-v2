#!/usr/bin/env python3
"""
Emergency webapp dependency installer and service starter
"""
import subprocess
import sys
import os

def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(f"COMMAND: {cmd}")
        print(f"STDOUT: {result.stdout}")
        if result.stderr:
            print(f"STDERR: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"ERROR running {cmd}: {e}")
        return False

def main():
    os.chdir('/root/HydraX-v2')
    
    print("🚨 EMERGENCY WEBAPP RECOVERY")
    print("=" * 50)
    
    # Create venv
    print("Step 1: Creating virtual environment...")
    run_command("/usr/bin/python3 -m venv .venv")
    
    # Install dependencies
    print("Step 2: Installing dependencies...")
    deps = [
        "flask>=2.3.0",
        "flask-socketio>=5.3.0", 
        "eventlet>=0.33.0",
        "requests>=2.31.0",
        "redis>=4.6.0",
        "python-socketio>=5.8.0"
    ]
    
    for dep in deps:
        print(f"Installing {dep}...")
        run_command(f".venv/bin/pip install {dep}")
    
    # Test import
    print("Step 3: Testing imports...")
    test_result = run_command('.venv/bin/python -c "import flask, flask_socketio, eventlet; print(\'✅ All imports successful\')"')
    
    if test_result:
        print("✅ Dependencies installed successfully")
    else:
        print("❌ Dependency installation failed")
        return False
    
    # Start webapp directly
    print("Step 4: Starting webapp...")
    run_command('.venv/bin/python src/bitten_core/web_app.py &')
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)