#!/bin/bash
# Setup MT5 terminals inside Docker containers

echo "🚀 Setting up MT5 terminals in Docker containers"
echo "==============================================="

# Function to setup MT5 in a container
setup_mt5_container() {
    local CONTAINER=$1
    local BROKER_NUM=$2
    
    echo ""
    echo "📦 Setting up $CONTAINER (Broker $BROKER_NUM)..."
    
    # Create setup script for inside container
    cat << 'MT5_SETUP' > /tmp/mt5_setup_${BROKER_NUM}.sh
#!/bin/bash
echo "Installing MT5 for Broker ${BROKER_NUM}..."

# Install required packages
apt-get update
apt-get install -y wget xvfb x11vnc

# Download MT5
cd /wine/drive_c/mt5
wget -q https://download.mql5.com/cdn/web/metaquotes.ltd/mt5/mt5setup.exe

# Create auto-install script
cat << 'AUTOINSTALL' > install.bat
@echo off
start /wait mt5setup.exe /auto
AUTOINSTALL

# Run installation with virtual display
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x16 &
sleep 5

wine cmd /c install.bat
sleep 30

# Kill Xvfb
pkill Xvfb

# Create MT5 start script
cat << 'STARTMT5' > /wine/drive_c/mt5/start_mt5.sh
#!/bin/bash
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x16 &
x11vnc -display :99 -nopw -listen localhost -xkb -ncache 10 -forever &
cd /wine/drive_c/mt5
wine terminal64.exe /portable
STARTMT5

chmod +x /wine/drive_c/mt5/start_mt5.sh

# Create EA directories
mkdir -p /wine/drive_c/mt5/MQL5/Experts
mkdir -p /wine/drive_c/mt5/MQL5/Files/BITTEN

# Set permissions
chmod -R 777 /wine/drive_c/mt5/MQL5/Files/BITTEN

echo "MT5 installation complete for Broker ${BROKER_NUM}"
MT5_SETUP

    # Copy setup script to container
    docker cp /tmp/mt5_setup_${BROKER_NUM}.sh ${CONTAINER}:/tmp/setup.sh
    
    # Execute setup inside container
    docker exec ${CONTAINER} chmod +x /tmp/setup.sh
    docker exec ${CONTAINER} /tmp/setup.sh
    
    # Copy Enhanced EA to container
    echo "📋 Copying Enhanced EA..."
    docker cp /root/HydraX-v2/src/bridge/BITTENBridge_v3_ENHANCED.mq5 \
        ${CONTAINER}:/wine/drive_c/mt5/MQL5/Experts/BITTENBridge_v3_ENHANCED.mq5
    
    # Create config file for auto-login (template)
    cat << CONFIG > /tmp/broker${BROKER_NUM}_config.ini
[Server]
Name=Demo Server Broker${BROKER_NUM}
Address=demo.server.com:443

[Account]
Login=
Password=
SavePassword=1

[Expert]
AllowLiveTrading=1
AllowDllImports=1
Enabled=1

[Common]
PortableMode=1
CONFIG

    docker cp /tmp/broker${BROKER_NUM}_config.ini ${CONTAINER}:/wine/drive_c/mt5/config.ini
}

# Connect to farm server and run setup
echo "🔌 Connecting to farm server..."

sshpass -p 'bNL9SqfNXhWL4#y' ssh -o StrictHostKeyChecking=no root@129.212.185.102 << 'REMOTE_SETUP'
cd /opt/bitten

# Check if containers are running
echo "Checking Docker containers..."
docker ps

# Setup each broker
for i in 1 2 3; do
    CONTAINER="bitten-mt5-broker${i}"
    
    # Check if container exists
    if docker ps -a | grep -q $CONTAINER; then
        echo "Setting up $CONTAINER..."
        
        # Install Wine and dependencies in container
        docker exec $CONTAINER apt-get update
        docker exec $CONTAINER apt-get install -y wget winbind wine wine64 xvfb x11vnc
        
        # Create directories
        docker exec $CONTAINER mkdir -p /wine/drive_c/mt5
        docker exec $CONTAINER mkdir -p /opt/bitten/broker${i}/Files/BITTEN
        
        # Download and prepare MT5
        docker exec $CONTAINER bash -c "cd /wine/drive_c/mt5 && wget -q https://download.mql5.com/cdn/web/metaquotes.ltd/mt5/mt5setup.exe"
        
        # Create runner script
        cat << 'RUNNER' > /tmp/run_mt5_${i}.sh
#!/bin/bash
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x16 &
sleep 2
cd /wine/drive_c/mt5
wine mt5setup.exe /auto &
sleep 60
pkill wine
pkill Xvfb
RUNNER
        
        docker cp /tmp/run_mt5_${i}.sh $CONTAINER:/tmp/run_mt5.sh
        docker exec $CONTAINER chmod +x /tmp/run_mt5.sh
        
        # Try to install MT5
        echo "Installing MT5 in $CONTAINER..."
        docker exec $CONTAINER /tmp/run_mt5.sh || echo "Installation attempt completed"
        
        # Copy EA
        docker cp /opt/bitten/BITTENBridge_v3_ENHANCED.mq5 $CONTAINER:/wine/drive_c/mt5/MQL5/Experts/ 2>/dev/null || echo "EA will be copied after MT5 setup"
        
        # Create startup script
        cat << 'STARTUP' > /tmp/start_mt5_${i}.sh
#!/bin/bash
export DISPLAY=:99
cd /opt/bitten/broker${i}
Xvfb :99 -screen 0 1024x768x16 &
sleep 2
x11vnc -display :99 -nopw -listen 0.0.0.0 -xkb -ncache 10 -forever &
cd /wine/drive_c/mt5
wine terminal64.exe /portable /config:config.ini
STARTUP
        
        docker cp /tmp/start_mt5_${i}.sh $CONTAINER:/start_mt5.sh
        docker exec $CONTAINER chmod +x /start_mt5.sh
        
        echo "✅ Container $CONTAINER prepared"
    else
        echo "❌ Container $CONTAINER not found"
    fi
done

echo ""
echo "Creating manual setup instructions..."

cat << 'MANUAL_SETUP' > /opt/bitten/MANUAL_MT5_SETUP.md
# Manual MT5 Setup Instructions

Since MT5 requires GUI interaction, you'll need to complete setup manually:

## For Each Broker Container (1, 2, 3):

### 1. Access Container with VNC

```bash
# Start VNC server in container
docker exec -d bitten-mt5-broker1 /start_mt5.sh

# Forward VNC port (from your local machine)
ssh -L 5901:129.212.185.102:5901 root@129.212.185.102

# Connect with VNC viewer to localhost:5901
```

### 2. Complete MT5 Installation

1. MT5 installer should auto-start
2. Click through installation (Next, Next, Finish)
3. MT5 will launch automatically

### 3. Login to Broker Account

1. File → Login to Trade Account
2. Enter your broker credentials:
   - Server: Your broker's server
   - Login: Your account number
   - Password: Your password
3. Click OK

### 4. Install the EA

1. Open MetaEditor (F4)
2. Navigator → Experts → Right-click → Refresh
3. Find BITTENBridge_v3_ENHANCED
4. Double-click to open
5. Compile (F7)
6. Close MetaEditor

### 5. Attach EA to Chart

1. Open EURUSD chart (or any major pair)
2. Navigator → Experts → BITTENBridge_v3_ENHANCED
3. Drag to chart
4. In settings:
   - Common tab: Allow live trading ✓
   - Inputs tab: Leave defaults
5. Click OK

### 6. Verify EA is Running

- EA should show "BITTEN Enhanced Bridge v3 ready" in Experts tab
- Check Files tab → BITTEN folder exists
- Files should start appearing:
  - bitten_account_secure.txt
  - bitten_status_secure.txt
  - bitten_market_secure.txt

### 7. Test Communication

From farm server:
```bash
# Check account data
cat /opt/bitten/broker1/Files/BITTEN/bitten_account_secure.txt

# Check status
cat /opt/bitten/broker1/Files/BITTEN/bitten_status_secure.txt
```

## Repeat for broker2 and broker3

## Troubleshooting

If MT5 won't start:
```bash
docker exec bitten-mt5-broker1 apt-get install -y winbind
docker exec bitten-mt5-broker1 wineboot --init
```

If EA won't compile:
- Ensure file has .mq5 extension
- Check for syntax errors in Errors tab
- Try Tools → Options → Compiler → Unicode

If no files appear:
- Check EA is enabled (smiley face)
- Check AutoTrading is ON
- Check file permissions: chmod -R 777 /opt/bitten/broker*/Files/BITTEN
MANUAL_SETUP

echo "✅ Setup preparation complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Check /opt/bitten/MANUAL_MT5_SETUP.md for detailed instructions"
echo "2. Use VNC to access each container and complete MT5 setup"
echo "3. Login with your broker credentials"
echo "4. Attach the Enhanced EA to charts"
echo ""
echo "Note: MT5 requires manual GUI setup for initial configuration"
REMOTE_SETUP

echo ""
echo "🎯 Creating VNC access script..."

cat << 'VNC_SCRIPT' > /root/HydraX-v2/access_mt5_vnc.sh
#!/bin/bash
# Access MT5 containers via VNC

echo "🖥️ MT5 VNC Access"
echo "=================="
echo ""
echo "1. Start VNC in container:"
echo "   ssh root@129.212.185.102"
echo "   docker exec -d bitten-mt5-broker1 /start_mt5.sh"
echo ""
echo "2. Forward VNC port locally:"
echo "   ssh -L 5901:localhost:5901 root@129.212.185.102"
echo ""
echo "3. Connect VNC viewer to:"
echo "   localhost:5901"
echo ""
echo "For broker2: use port 5902"
echo "For broker3: use port 5903"
VNC_SCRIPT

chmod +x /root/HydraX-v2/access_mt5_vnc.sh

echo ""
echo "✅ MT5 container setup prepared!"
echo ""
echo "Since MT5 requires GUI interaction, I've prepared:"
echo "1. Scripts to install MT5 in containers"
echo "2. VNC server setup for remote access"
echo "3. Detailed manual setup instructions"
echo ""
echo "To complete setup:"
echo "1. Run: ./access_mt5_vnc.sh for VNC instructions"
echo "2. Access each container via VNC"
echo "3. Complete MT5 installation and EA setup"
echo ""
echo "The farm server now has /opt/bitten/MANUAL_MT5_SETUP.md with step-by-step instructions!"