#!/usr/bin/env python3
"""
Simple file server for bulletproof agent files
"""
from flask import Flask, send_from_directory, jsonify
import os

app = Flask(__name__)

# Directory containing the bulletproof agent files
FILES_DIR = '/root/HydraX-v2/bulletproof_agents'

@app.route('/')
def index():
    """List available files"""
    files = []
    for file in os.listdir(FILES_DIR):
        if file.endswith('.py') or file.endswith('.bat'):
            files.append(file)
    
    return jsonify({
        'available_files': files,
        'download_url': 'http://134.199.204.67:9999/FILENAME'
    })

@app.route('/<filename>')
def serve_file(filename):
    """Serve a specific file"""
    return send_from_directory(FILES_DIR, filename)

if __name__ == '__main__':
    print("Starting file server on port 9999...")
    print("Available files:")
    for file in os.listdir(FILES_DIR):
        if file.endswith('.py') or file.endswith('.bat'):
            print(f"  http://134.199.204.67:9999/{file}")
    
    app.run(host='0.0.0.0', port=9999, debug=False)