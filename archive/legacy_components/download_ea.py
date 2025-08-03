#!/usr/bin/env python3
"""
Simple file server to download the EA
"""
from flask import Flask, send_file
import os

app = Flask(__name__)

@app.route('/ea')
def download_ea():
    """Direct download of the EA file"""
    ea_path = '/root/HydraX-v2/BITTEN_Windows_Package/EA/BITTENBridge_v3_ENHANCED.mq5'
    return send_file(ea_path, as_attachment=True, download_name='BITTENBridge_v3_ENHANCED.mq5')

@app.route('/package')
def download_package():
    """Download the full package"""
    package_path = '/root/HydraX-v2/BITTEN_EA_Package.tar.gz'
    return send_file(package_path, as_attachment=True)

@app.route('/')
def index():
    return """
    <h1>BITTEN EA Download</h1>
    <ul>
        <li><a href="/ea">Download EA Only (BITTENBridge_v3_ENHANCED.mq5)</a></li>
        <li><a href="/package">Download Full Package (includes docs)</a></li>
    </ul>
    """

if __name__ == '__main__':
    print("Starting download server on port 8890...")
    print("Access from Windows: http://134.199.204.67:8890/")
    app.run(host='0.0.0.0', port=8890)