#!/usr/bin/env python3
"""
Simple HTTP File Server for bridge_rescue_agent.py
Serves the rescue agent script at http://134.199.204.67:9999/bridge_rescue_agent.py
"""

import http.server
import socketserver
import os
from pathlib import Path

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/bridge_rescue_agent.py':
            # Serve the bridge rescue agent script
            script_path = Path('/root/HydraX-v2/bridge_rescue_agent.py')
            if script_path.exists():
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain; charset=utf-8')
                self.send_header('Content-Disposition', 'attachment; filename="bridge_rescue_agent.py"')
                self.end_headers()
                
                with open(script_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "Bridge rescue agent script not found")
        
        elif self.path == '/primary_agent_mt5_enhanced.py':
            # Serve the enhanced MT5 bridge agent
            script_path = Path('/root/HydraX-v2/primary_agent_mt5_enhanced.py')
            if script_path.exists():
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain; charset=utf-8')
                self.send_header('Content-Disposition', 'attachment; filename="primary_agent_mt5_enhanced.py"')
                self.end_headers()
                
                with open(script_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "Enhanced MT5 agent script not found")
        
        elif self.path == '/rdt_command_agent.py':
            # Serve the RDT command agent
            script_path = Path('/root/HydraX-v2/rdt_command_agent.py')
            if script_path.exists():
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain; charset=utf-8')
                self.send_header('Content-Disposition', 'attachment; filename="rdt_command_agent.py"')
                self.end_headers()
                
                with open(script_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "RDT command agent script not found")
        
        else:
            # Default behavior
            super().do_GET()

def main():
    PORT = 9999
    
    # Change to the directory containing the script
    os.chdir('/root/HydraX-v2')
    
    with socketserver.TCPServer(("0.0.0.0", PORT), CustomHTTPRequestHandler) as httpd:
        print(f"✅ File server running on port {PORT}")
        print(f"📁 Serving files at:")
        print(f"   http://134.199.204.67:{PORT}/bridge_rescue_agent.py")
        print(f"   http://134.199.204.67:{PORT}/primary_agent_mt5_enhanced.py")
        print(f"   http://localhost:{PORT}/bridge_rescue_agent.py")
        print(f"   http://localhost:{PORT}/primary_agent_mt5_enhanced.py")
        print()
        print("Press Ctrl+C to stop server")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")

if __name__ == "__main__":
    main()