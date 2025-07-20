#!/bin/bash
# Master Clone Integrity Checker
# Verifies master clone has not been modified

echo "🔍 MASTER CLONE INTEGRITY CHECK"
echo "==============================="

# Variables
WINE_MASTER="/root/.wine_master_clone"
CHECKSUMS_FILE="/root/master_clone_checksums.txt"
FREEZE_STATE="$WINE_MASTER/FROZEN_STATE.md"

# Initialize status
INTEGRITY_OK=true

# Check if master clone exists
if [ ! -d "$WINE_MASTER" ]; then
    echo "❌ CRITICAL: Master clone missing at $WINE_MASTER"
    exit 1
fi

# Check if checksums file exists
if [ ! -f "$CHECKSUMS_FILE" ]; then
    echo "❌ CRITICAL: Checksums file missing at $CHECKSUMS_FILE"
    echo "   Master clone may never have been properly frozen"
    exit 1
fi

# Check freeze state documentation
if [ -f "$FREEZE_STATE" ]; then
    echo "✅ Freeze state documentation found"
    echo "   Frozen on: $(grep "Date:" "$FREEZE_STATE" | cut -d: -f2-)"
else
    echo "❌ WARNING: Freeze state documentation missing"
    INTEGRITY_OK=false
fi

# Verify file checksums
echo "🔍 Verifying file integrity..."
if cd / && md5sum -c "$CHECKSUMS_FILE" --quiet 2>/dev/null; then
    echo "✅ File integrity verified - all checksums match"
else
    echo "❌ CRITICAL: File integrity compromised!"
    echo "   One or more files have been modified since freeze"
    INTEGRITY_OK=false
    
    # Show which files changed
    echo "🔍 Changed files:"
    cd / && md5sum -c "$CHECKSUMS_FILE" 2>/dev/null | grep FAILED
fi

# Check critical file permissions
echo "🔐 Checking file permissions..."
MT5_PATH="$WINE_MASTER/drive_c/Program Files/MetaTrader 5"

if [ -f "$MT5_PATH/terminal64.exe" ]; then
    if [ ! -w "$MT5_PATH/terminal64.exe" ]; then
        echo "✅ Terminal executable permissions protected"
    else
        echo "❌ WARNING: Terminal executable is writable"
        INTEGRITY_OK=false
    fi
else
    echo "⚠️  Terminal executable not found"
fi

if [ -f "$MT5_PATH/MQL5/Experts/BITTEN_EA.ex5" ]; then
    if [ ! -w "$MT5_PATH/MQL5/Experts/BITTEN_EA.ex5" ]; then
        echo "✅ EA file permissions protected"
    else
        echo "❌ WARNING: EA file is writable"
        INTEGRITY_OK=false
    fi
else
    echo "⚠️  EA file not found"
fi

# Check hosts file for update blocks
HOSTS_FILE="$WINE_MASTER/drive_c/windows/system32/drivers/etc/hosts"
if [ -f "$HOSTS_FILE" ] && grep -q "update.mql5.com" "$HOSTS_FILE"; then
    echo "✅ MT5 update servers blocked in hosts file"
else
    echo "❌ WARNING: MT5 update servers not blocked"
    INTEGRITY_OK=false
fi

# Check registry settings
echo "🔧 Checking registry settings..."
export WINEPREFIX="$WINE_MASTER"
if wine reg query "HKEY_CURRENT_USER\\Software\\MetaQuotes\\Terminal" /v "AutoUpdate" 2>/dev/null | grep -q "0x0"; then
    echo "✅ Auto-update disabled in registry"
else
    echo "❌ WARNING: Auto-update not disabled in registry"
    INTEGRITY_OK=false
fi

# Check immutable attributes
echo "🛡️ Checking immutable attributes..."
if command -v lsattr >/dev/null 2>&1; then
    if [ -f "$MT5_PATH/terminal64.exe" ]; then
        if lsattr "$MT5_PATH/terminal64.exe" 2>/dev/null | grep -q "i"; then
            echo "✅ Terminal executable has immutable attribute"
        else
            echo "⚠️  Terminal executable missing immutable attribute"
        fi
    fi
    
    if [ -f "$MT5_PATH/MQL5/Experts/BITTEN_EA.ex5" ]; then
        if lsattr "$MT5_PATH/MQL5/Experts/BITTEN_EA.ex5" 2>/dev/null | grep -q "i"; then
            echo "✅ EA file has immutable attribute"
        else
            echo "⚠️  EA file missing immutable attribute"
        fi
    fi
else
    echo "⚠️  lsattr not available, cannot check immutable attributes"
fi

# Final status report
echo ""
echo "📊 INTEGRITY CHECK RESULTS"
echo "=========================="

if [ "$INTEGRITY_OK" = true ]; then
    echo "🔒 MASTER CLONE INTEGRITY: VERIFIED"
    echo "✅ All security measures active"
    echo "✅ Master clone properly frozen"
    echo "✅ Ready for user clone creation"
    
    # Log successful check
    echo "$(date): Master clone integrity verified" >> /var/log/master_clone_integrity.log
    
    exit 0
else
    echo "🚨 MASTER CLONE INTEGRITY: COMPROMISED"
    echo "❌ Security measures may be compromised"
    echo "❌ Master clone may have been modified"
    echo "🔧 Recommended action: Re-run freeze protocol"
    
    # Log integrity failure
    echo "$(date): Master clone integrity FAILED" >> /var/log/master_clone_integrity.log
    
    # Send alert
    echo "ALERT: Master clone integrity compromised at $(date)" | \
        logger -t master_clone_alert
    
    echo ""
    echo "🛠️ RECOVERY OPTIONS:"
    echo "1. Re-run freeze protocol: ./freeze_master_clone.sh"
    echo "2. Restore from backup: tar -xzf /root/master_clone_backup_*.tar.gz"
    echo "3. Rebuild master clone from scratch"
    
    exit 1
fi