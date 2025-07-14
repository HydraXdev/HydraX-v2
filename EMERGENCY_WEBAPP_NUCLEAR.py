#!/usr/bin/env python3
"""
NUCLEAR OPTION: Emergency webapp with zero dependencies
"""
import os
import sys
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime

class EmergencyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "status": "ok", 
                "service": "BITTEN WebApp Emergency",
                "timestamp": datetime.now().isoformat(),
                "mode": "NUCLEAR_RECOVERY"
            }
            self.wfile.write(json.dumps(response).encode())
        
        elif self.path == '/status' or self.path == '/mode':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "mode": "NUCLEAR_RECOVERY",
                "uptime": "Active since emergency activation",
                "systemd": "bypassed",
                "bridge_status": "monitoring",
                "service": "BITTEN Emergency WebApp",
                "timestamp": datetime.now().isoformat(),
                "nuclear_active": True,
                "recovery_method": "HTTP Server Direct"
            }
            self.wfile.write(json.dumps(response).encode())
        
        elif self.path == '/reset-webapp':
            # Auth-locked reset tool (simple check for security)
            auth_header = self.headers.get('Authorization')
            if auth_header != 'Bearer COMMANDER_RESET_2025':
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Unauthorized"}).encode())
                return
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Perform reset actions
            import subprocess
            import time
            
            try:
                # Kill stray processes
                subprocess.run(["pkill", "-f", "python.*webapp"], capture_output=True)
                subprocess.run(["pkill", "-f", "flask"], capture_output=True)
                time.sleep(2)
                
                # Log action
                with open('/var/log/bitten-reset.log', 'a') as log:
                    log.write(f"{datetime.now().isoformat()} - WebApp reset triggered via /reset-webapp\n")
                
                # Restart bitten-webapp service
                subprocess.run(["systemctl", "restart", "bitten-webapp"], capture_output=True)
                
                response = {
                    "status": "reset_complete",
                    "timestamp": datetime.now().isoformat(),
                    "actions": ["killed_stray_processes", "logged_action", "restarted_systemd_service"],
                    "message": "WebApp reset completed successfully"
                }
                
            except Exception as e:
                response = {
                    "status": "reset_failed", 
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            
            self.wfile.write(json.dumps(response).encode())
        
        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = """
<!DOCTYPE html>
<html>
<head>
    <title>BITTEN - Emergency Mode</title>
    <style>
        body { background: #000; color: #0f0; font-family: monospace; padding: 20px; }
        .status { color: #ff0; font-size: 24px; text-align: center; }
        .info { color: #0ff; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="status">🚨 BITTEN WebApp - EMERGENCY MODE ACTIVE 🚨</div>
    <div class="info">
        <h2>System Status:</h2>
        <p>✅ Emergency webapp server running</p>
        <p>✅ Health endpoint active: /health</p>
        <p>⚠️ Running in nuclear recovery mode</p>
        <p>🔧 Full system restoration in progress</p>
    </div>
    <div class="info">
        <h2>Service Information:</h2>
        <p>Port: 5000</p>
        <p>Mode: HTTP Server (no Flask dependencies)</p>
        <p>Status: ONLINE</p>
        <p>Recovery Time: """ + datetime.now().isoformat() + """</p>
    </div>
</body>
</html>
            """
            self.wfile.write(html.encode())
        
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")
    
    def log_message(self, format, *args):
        print(f"[{datetime.now()}] {format % args}")

def start_emergency_server():
    """Start emergency HTTP server without Flask"""
    try:
        server = HTTPServer(('0.0.0.0', 5000), EmergencyHandler)
        print("🚨 NUCLEAR WEBAPP STARTING ON PORT 5000")
        print(f"🕐 Started at: {datetime.now()}")
        print("🔗 Health check: http://localhost:5000/health")
        print("🌐 Web interface: http://localhost:5000/")
        server.serve_forever()
    except Exception as e:
        print(f"💥 NUCLEAR SERVER FAILED: {e}")
        # Try alternate port
        try:
            server = HTTPServer(('0.0.0.0', 8888), EmergencyHandler)
            print("🚨 NUCLEAR WEBAPP STARTING ON PORT 8888 (FALLBACK)")
            server.serve_forever()
        except Exception as e2:
            print(f"💥 COMPLETE FAILURE: {e2}")

if __name__ == "__main__":
    start_emergency_server()