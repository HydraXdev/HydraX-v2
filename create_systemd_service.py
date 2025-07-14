#!/usr/bin/env python3
"""
Create proper systemd service for BITTEN webapp
"""
import os

SERVICE_CONTENT = """[Unit]
Description=BITTEN WebApp Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/HydraX-v2
Environment=PYTHONPATH=/root/HydraX-v2/src
ExecStart=/root/HydraX-v2/.venv/bin/python /root/HydraX-v2/src/bitten_core/web_app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""

def create_service():
    print("🔧 Creating systemd service...")
    
    # Write service file
    with open('/etc/systemd/system/bitten-webapp.service', 'w') as f:
        f.write(SERVICE_CONTENT)
    
    # Reload systemd
    os.system('systemctl daemon-reload')
    
    print("✅ Systemd service created")
    return True

if __name__ == "__main__":
    create_service()