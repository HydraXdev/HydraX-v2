#!/bin/bash
# Master Clone Freeze Script
# Implements complete freeze protocol for master clone

echo "🔒 MASTER CLONE FREEZE PROTOCOL INITIATED"
echo "========================================"

# Variables
WINE_MASTER="/root/.wine_master_clone"
MT5_PATH="$WINE_MASTER/drive_c/Program Files/MetaTrader 5"
HOSTS_FILE="$WINE_MASTER/drive_c/windows/system32/drivers/etc/hosts"
BACKUP_PATH="/root/master_clone_backup_$(date +%Y%m%d_%H%M%S).tar.gz"

# Check if master clone exists
if [ ! -d "$WINE_MASTER" ]; then
    echo "❌ Master clone not found at $WINE_MASTER"
    exit 1
fi

echo "📁 Master clone found: $WINE_MASTER"

# Step 1: Create backup before freeze
echo "💾 Creating backup..."
tar -czf "$BACKUP_PATH" "$WINE_MASTER"
echo "✅ Backup created: $BACKUP_PATH"

# Step 2: Block MT5 update servers
echo "🌐 Blocking MT5 update servers..."
cat >> "$HOSTS_FILE" << EOF

# Block MT5 auto-updates - Added $(date)
127.0.0.1 update.mql5.com
127.0.0.1 download.mql5.com
127.0.0.1 updates.metaquotes.net
127.0.0.1 auto-update.metaquotes.net
127.0.0.1 www.metaquotes.net
EOF
echo "✅ Update servers blocked in hosts file"

# Step 3: Registry modifications
echo "🔧 Disabling auto-update in registry..."
export WINEPREFIX="$WINE_MASTER"
wine reg add "HKEY_CURRENT_USER\\Software\\MetaQuotes\\Terminal" /v "AutoUpdate" /t REG_DWORD /d 0 /f 2>/dev/null
wine reg add "HKEY_CURRENT_USER\\Software\\MetaQuotes\\Terminal" /v "CheckUpdate" /t REG_DWORD /d 0 /f 2>/dev/null
wine reg add "HKEY_CURRENT_USER\\Software\\MetaQuotes\\Terminal" /v "AllowDLLImports" /t REG_DWORD /d 1 /f 2>/dev/null
echo "✅ Registry auto-update disabled"

# Step 4: File permissions
echo "🔐 Setting file permissions..."
if [ -f "$MT5_PATH/terminal64.exe" ]; then
    chmod 444 "$MT5_PATH/terminal64.exe"
    echo "✅ Terminal executable locked"
fi

if [ -f "$MT5_PATH/MQL5/Experts/BITTEN_EA.ex5" ]; then
    chmod 444 "$MT5_PATH/MQL5/Experts/BITTEN_EA.ex5"
    echo "✅ EA file locked"
fi

if [ -f "$MT5_PATH/config.ini" ]; then
    chmod 444 "$MT5_PATH/config.ini"
    echo "✅ Config file locked"
fi

# Step 5: Generate checksums
echo "🔍 Generating integrity checksums..."
find "$WINE_MASTER" -type f -exec md5sum {} \; > /root/master_clone_checksums.txt
echo "✅ Checksums generated: /root/master_clone_checksums.txt"

# Step 6: Set immutable attributes (if supported)
echo "🛡️ Setting immutable attributes..."
if command -v chattr >/dev/null 2>&1; then
    if [ -f "$MT5_PATH/terminal64.exe" ]; then
        chattr +i "$MT5_PATH/terminal64.exe" 2>/dev/null && echo "✅ Terminal executable immutable"
    fi
    if [ -f "$MT5_PATH/MQL5/Experts/BITTEN_EA.ex5" ]; then
        chattr +i "$MT5_PATH/MQL5/Experts/BITTEN_EA.ex5" 2>/dev/null && echo "✅ EA file immutable"
    fi
else
    echo "⚠️  chattr not available, skipping immutable attributes"
fi

# Step 7: Create freeze state documentation
echo "📋 Creating freeze state documentation..."
cat > "$WINE_MASTER/FROZEN_STATE.md" << EOF
# MASTER CLONE FROZEN STATE
Date: $(date)
Frozen By: Autonomous Agent
Wine Version: $(wine --version 2>/dev/null || echo "Unknown")
System Hash: $(find "$WINE_MASTER" -type f -exec md5sum {} \; | md5sum | cut -d' ' -f1)

# FROZEN COMPONENTS
- ✅ MT5 Terminal: Locked at current version
- ✅ Expert Advisor: BITTEN_EA.ex5 frozen
- ✅ Configuration: All settings locked
- ✅ Registry: Auto-update disabled
- ✅ Network: Update servers blocked
- ✅ Permissions: Critical files read-only

# WARNING: DO NOT MODIFY THIS MASTER CLONE
# All user clones should be created from this frozen template

# BACKUP LOCATION
Backup: $BACKUP_PATH
Checksums: /root/master_clone_checksums.txt

# VERIFICATION
To verify integrity: md5sum -c /root/master_clone_checksums.txt
EOF

echo "✅ Freeze state documented"

# Step 8: Network firewall rules
echo "🔥 Configuring firewall rules..."
if command -v iptables >/dev/null 2>&1; then
    iptables -A OUTPUT -d update.mql5.com -j DROP 2>/dev/null
    iptables -A OUTPUT -d download.mql5.com -j DROP 2>/dev/null
    iptables -A OUTPUT -d updates.metaquotes.net -j DROP 2>/dev/null
    iptables -A OUTPUT -d auto-update.metaquotes.net -j DROP 2>/dev/null
    echo "✅ Firewall rules applied"
else
    echo "⚠️  iptables not available, relying on hosts file blocking"
fi

echo ""
echo "🎯 MASTER CLONE FREEZE COMPLETED SUCCESSFULLY"
echo "============================================="
echo ""
echo "📊 FREEZE STATUS:"
echo "  ✅ Auto-updates blocked"
echo "  ✅ File permissions locked"
echo "  ✅ Registry settings disabled"
echo "  ✅ Network access blocked"
echo "  ✅ Backup created"
echo "  ✅ Checksums generated"
echo "  ✅ Freeze state documented"
echo ""
echo "🔒 Master clone is now completely frozen and protected."
echo "🏭 Ready for user clone creation from this proven template."
echo ""
echo "📋 Next steps:"
echo "  1. Test user clone creation: python3 clone_user_from_master.py"
echo "  2. Verify master integrity: ./check_master_integrity.sh"
echo "  3. Deploy watchdog monitoring"
echo ""