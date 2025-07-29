#!/usr/bin/env python3
"""
Debug EA Data Format
Capture and analyze the exact data format being sent by the EA
"""

from flask import Flask, request
import json
import time
from datetime import datetime

app = Flask(__name__)

@app.route('/market-data', methods=['POST'])
def debug_market_data():
    """Debug endpoint to see exactly what the EA is sending"""
    
    print("\n" + "="*60)
    print(f"🔍 DEBUG CAPTURE: {datetime.now()}")
    print("="*60)
    
    # Get raw data
    raw_data = request.get_data()
    print(f"📦 Raw Data (bytes): {raw_data}")
    print(f"📏 Data Length: {len(raw_data)} bytes")
    
    # Get headers
    print(f"📋 Headers:")
    for key, value in request.headers:
        print(f"   {key}: {value}")
    
    # Try to decode as text
    try:
        text_data = raw_data.decode('utf-8')
        print(f"📝 Text Data: {repr(text_data)}")
    except:
        print("❌ Cannot decode as UTF-8")
    
    # Try to parse as JSON
    try:
        json_data = request.get_json()
        print(f"🎯 JSON Data: {json.dumps(json_data, indent=2)}")
    except Exception as e:
        print(f"❌ JSON Parse Error: {e}")
    
    # Try manual JSON parse
    try:
        if raw_data:
            manual_json = json.loads(raw_data.decode('utf-8'))
            print(f"🔧 Manual JSON: {json.dumps(manual_json, indent=2)}")
    except Exception as e:
        print(f"❌ Manual JSON Parse Error: {e}")
    
    print("="*60)
    
    return "DEBUG: Data captured", 200

@app.route('/health')
def health():
    return {"status": "debug_active", "time": datetime.now().isoformat()}

if __name__ == '__main__':
    print("🔍 EA DATA FORMAT DEBUGGER")
    print("Listening on port 8001 to capture EA data...")
    print("Will show exact format being sent by EA at 185.244.67.11")
    print("Press Ctrl+C to stop")
    
    app.run(host='0.0.0.0', port=8001, debug=False)