#!/usr/bin/env python3
"""
Update BITTEN bot to use local webapp URL
"""
import os
import sys
sys.path.append('/root/HydraX-v2')

from config.webapp_local import WebAppConfig

def update_bot_config():
    """Update bot configuration to use local webapp URL"""
    
    print("🔧 Updating BITTEN Bot Configuration")
    print(f"📍 New webapp URL: {WebAppConfig.BASE_URL}")
    print(f"🎯 HUD URL: {WebAppConfig.HUD_URL}")
    
    # Create environment variable file for bot
    env_content = f"""# BITTEN Bot Environment Configuration
export BITTEN_WEBAPP_URL="{WebAppConfig.BASE_URL}"
export BITTEN_HUD_URL="{WebAppConfig.HUD_URL}"
export BITTEN_ENV="local"
"""
    
    with open('/root/HydraX-v2/.env.bitten', 'w') as f:
        f.write(env_content)
    
    print("✅ Environment file created: .env.bitten")
    
    # Create bot launcher script
    launcher_content = f"""#!/bin/bash
# BITTEN Bot Launcher with Local Webapp

# Load environment
source /root/HydraX-v2/.env.bitten

# Kill existing bot processes
pkill -f "bitten_bot.py" || true

# Start bot with new configuration
cd /root/HydraX-v2
python3 bitten_bot.py \\
    --webapp-url "$BITTEN_WEBAPP_URL" \\
    --hud-url "$BITTEN_HUD_URL" \\
    2>&1 | tee -a bitten_bot.log &

echo "✅ BITTEN bot started with local webapp configuration"
echo "📍 Webapp URL: $BITTEN_WEBAPP_URL"
echo "🎯 HUD URL: $BITTEN_HUD_URL"
"""
    
    launcher_path = '/root/HydraX-v2/start_bot_local.sh'
    with open(launcher_path, 'w') as f:
        f.write(launcher_content)
    
    os.chmod(launcher_path, 0o755)
    print(f"✅ Bot launcher created: {launcher_path}")
    
    # Create systemd service for webapp
    systemd_content = """[Unit]
Description=BITTEN WebApp Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/HydraX-v2
Environment="PYTHONPATH=/root/HydraX-v2"
ExecStart=/usr/bin/python3 /root/HydraX-v2/webapp_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    service_path = '/etc/systemd/system/bitten-webapp.service'
    with open(service_path, 'w') as f:
        f.write(systemd_content)
    
    print(f"✅ Systemd service created: {service_path}")
    
    return True

if __name__ == "__main__":
    if update_bot_config():
        print("\n🎉 Configuration updated successfully!")
        print("\nNext steps:")
        print("1. Enable webapp service: systemctl enable bitten-webapp")
        print("2. Start webapp service: systemctl start bitten-webapp")
        print("3. Start bot with: ./start_bot_local.sh")
        print(f"4. Test webapp at: {WebAppConfig.BASE_URL}")
    else:
        print("❌ Configuration update failed!")