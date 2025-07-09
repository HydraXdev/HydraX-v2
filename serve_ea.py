#!/usr/bin/env python3
import http.server
import socketserver
import os

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/ea':
            self.send_response(200)
            self.send_header('Content-type', 'application/octet-stream')
            self.send_header('Content-Disposition', 'attachment; filename="BITTENBridge_v3_ENHANCED.mq5"')
            self.end_headers()
            with open('/root/HydraX-v2/BITTEN_Windows_Package/EA/BITTENBridge_v3_ENHANCED.mq5', 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'''
<html>
<body>
<h1>BITTEN EA Download</h1>
<h2>From Windows PowerShell, run:</h2>
<pre style="background: #f0f0f0; padding: 20px;">
Invoke-WebRequest -Uri "http://134.199.204.67:9999/ea" -OutFile "C:\\BITTENBridge_v3_ENHANCED.mq5"
</pre>
<p>Or click: <a href="/ea">Download EA</a></p>
</body>
</html>
''')

print("Server running on http://134.199.204.67:9999")
print("")
print("FROM WINDOWS POWERSHELL, RUN:")
print('Invoke-WebRequest -Uri "http://134.199.204.67:9999/ea" -OutFile "C:\\BITTENBridge_v3_ENHANCED.mq5"')
print("")

with socketserver.TCPServer(("", 9999), MyHTTPRequestHandler) as httpd:
    httpd.serve_forever()
