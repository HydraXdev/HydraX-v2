#!/usr/bin/env python3
"""
Simple Market Data Receiver - Get EA back online ASAP
"""

from flask import Flask, request, jsonify
import time
import json

app = Flask(__name__)

@app.route('/market-data/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy', 
        'symbols_active': 0, 
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
    })

@app.route('/market-data', methods=['POST'])
def receive_data():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data received'}), 400
        
        # Accept data for now - EA v5.1 should have source field
        source = data.get('source', 'unknown')
        print(f"📡 Source: {source}")
            
        ticks = data.get('ticks', [])
        broker = data.get('broker', 'unknown')
        
        print(f"✅ Received {len(ticks)} ticks from {broker}")
        
        return jsonify({
            'status': 'success', 
            'processed': len(ticks),
            'broker': broker
        })
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/market-data/all', methods=['GET'])  
def get_all():
    return jsonify({
        'data': {}, 
        'total_symbols': 0, 
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
    })

if __name__ == '__main__':
    print("🚀 Simple Market Data Receiver starting on port 8001")
    app.run(host='0.0.0.0', port=8001, debug=False, threaded=True)