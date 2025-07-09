# Save this as 'a.py' in C:\ (super short name!)
import subprocess
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/c':
            l = int(self.headers['Content-Length'])
            d = json.loads(self.rfile.read(l))
            r = subprocess.run(d['c'], shell=True, capture_output=True, text=True)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({'o': r.stdout, 'e': r.stderr}).encode())
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')

print("Agent on :5555")
HTTPServer(('', 5555), H).serve_forever()