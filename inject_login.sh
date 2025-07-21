#!/bin/bash
#=================================================================
# HydraX Login Injection Script
# Sets login.ini for terminal startup with user credentials
#=================================================================

set -e

# Parameters
LOGIN="$1"
PASSWORD="$2"
SERVER="$3"

if [[ -z "$LOGIN" || -z "$PASSWORD" || -z "$SERVER" ]]; then
    echo "Usage: $0 <login> <password> <server>"
    exit 1
fi

echo "🔑 Injecting MT5 credentials..."
echo "   Login: $LOGIN"
echo "   Server: $SERVER"

# Create config directory
mkdir -p /wine/drive_c/MetaTrader5/config

# Generate login.ini
cat > /wine/drive_c/MetaTrader5/config/login.ini << EOF
[Server]
Name=$SERVER
Server=$SERVER

[Account] 
Login=$LOGIN
Password=$PASSWORD
SavePassword=1

[Common]
Login=$LOGIN
Password=$PASSWORD  
Server=$SERVER

[StartUp]
Login=$LOGIN
Password=$PASSWORD
Server=$SERVER
AutoLogin=1

[Terminal]
StartupProfile=Default
EOF

echo "✅ Login configuration injected successfully"
echo "📁 Config file: /wine/drive_c/MetaTrader5/config/login.ini"