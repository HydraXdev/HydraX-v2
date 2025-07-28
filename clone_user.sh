#!/bin/bash
# BITTEN User Clone Script
# Usage: ./clone_user.sh USER_ID ACCOUNT PASSWORD SERVER

USER_ID=$1
ACCOUNT=$2
PASSWORD=$3
SERVER=$4

if [ -z "$USER_ID" ]; then
    echo "Usage: $0 USER_ID ACCOUNT PASSWORD SERVER"
    exit 1
fi

USER_CLONE_PATH="/root/.wine_user_$USER_ID"
MASTER_PATH="/root/.wine_master_clone"

echo "🔄 Cloning master to user $USER_ID..."

# Copy entire master structure
cp -r "$MASTER_PATH" "$USER_CLONE_PATH"

# Update config with user credentials
sed -i "s/TEMPLATE_LOGIN/$ACCOUNT/g" "$USER_CLONE_PATH/drive_c/MetaTrader5/config.ini"
sed -i "s/TEMPLATE_PASSWORD/$PASSWORD/g" "$USER_CLONE_PATH/drive_c/MetaTrader5/config.ini"
sed -i "s/TEMPLATE_SERVER/$SERVER/g" "$USER_CLONE_PATH/drive_c/MetaTrader5/config.ini"

# Create user-specific drop directories
mkdir -p "$USER_CLONE_PATH/drive_c/MetaTrader5/Files/BITTEN/Drop/user_$USER_ID"
mkdir -p "$USER_CLONE_PATH/drive_c/MetaTrader5/Files/BITTEN/Results/user_$USER_ID"

# Update pair instruction files for user
PAIRS=(EURUSD GBPUSD USDJPY USDCAD GBPJPY EURJPY AUDJPY GBPCHF AUDUSD NZDUSD USDCHF EURGBP GBPNZD GBPAUD EURAUD)

for pair in "${PAIRS[@]}"; do
    USER_FILE="$USER_CLONE_PATH/drive_c/MetaTrader5/Files/BITTEN/bitten_instructions_${pair,,}_user_$USER_ID.json"
    
    cat > "$USER_FILE" << EOF
{
  "pair": "$pair",
  "action": "monitor",
  "magic_number": 20250626,
  "account": "$ACCOUNT",
  "server": "$SERVER",
  "user_id": "$USER_ID",
  "status": "ready",
  "timestamp": "$(date -Iseconds)"
}
EOF
done

echo "✅ Clone complete for user $USER_ID"
echo "Account: $ACCOUNT@$SERVER"
echo "Path: $USER_CLONE_PATH"
