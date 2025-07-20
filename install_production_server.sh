#!/bin/bash
# Install production WSGI server for Commander Throne

echo "Installing production server dependencies..."
pip install gunicorn eventlet

echo "Creating production service file..."
cat > /etc/systemd/system/bitten-throne-production.service << 'EOF'
[Unit]
Description=BITTEN Commander Throne - Production Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/HydraX-v2
Environment="PYTHONPATH=/root/HydraX-v2/src:/root/HydraX-v2"
Environment="THRONE_PORT=8899"
ExecStart=/usr/local/bin/gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:8899 --timeout 120 --access-logfile - --error-logfile - commander_throne:app
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security hardening
PrivateTmp=true
NoNewPrivileges=true

# Resource limits
LimitNOFILE=65536
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
EOF

echo "Production server setup complete. To switch to production:"
echo "1. sudo systemctl stop bitten-throne"
echo "2. sudo systemctl disable bitten-throne"
echo "3. sudo systemctl enable bitten-throne-production"
echo "4. sudo systemctl start bitten-throne-production"