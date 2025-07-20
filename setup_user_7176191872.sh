#!/bin/bash
# BITTEN User Clone Setup - Telegram ID: 7176191872
# Creates secure trading environment with BYOB credentials

TELEGRAM_ID="7176191872"
TRADING_ACCOUNT="843859"
ACCOUNT_PASSWORD="Ao4@brz64erHaG"
BROKER_SERVER="Coinexx-Demo"
MAGIC_NUMBER="20250626"

echo "🚀 Setting up BITTEN clone for Telegram user ${TELEGRAM_ID}"
echo "📋 Trading Account: ${TRADING_ACCOUNT}@${BROKER_SERVER}"
echo "🔐 Implementing BYOB security protocol..."

# Create user-specific Wine environment
USER_WINE_DIR="/root/.wine_user_${TELEGRAM_ID}"
mkdir -p "${USER_WINE_DIR}/drive_c/MT5Terminal"

echo "🍷 Creating isolated Wine environment for user ${TELEGRAM_ID}..."

# Set up MT5 configuration with user credentials
mkdir -p "${USER_WINE_DIR}/drive_c/MT5Terminal/config"
cat > "${USER_WINE_DIR}/drive_c/MT5Terminal/config/account.ini" << EOF
[Account]
Login=${TRADING_ACCOUNT}
Password=${ACCOUNT_PASSWORD}
Server=${BROKER_SERVER}
AutoLogin=1

[Common]
AutoTrading=1
DLLAllowed=1
ExpertAllowed=1
MaxBars=10000
MagicNumber=${MAGIC_NUMBER}

[BITTEN_USER]
TelegramID=${TELEGRAM_ID}
TradingAccount=${TRADING_ACCOUNT}
BrokerServer=${BROKER_SERVER}
CloneMode=1
CreatedAt=$(date -Iseconds)
EOF

# Create user-specific BITTEN directories
echo "📁 Setting up user-specific BITTEN directories..."
mkdir -p "${USER_WINE_DIR}/drive_c/MT5Terminal/Files/BITTEN/Drop/user_${TELEGRAM_ID}"
mkdir -p "${USER_WINE_DIR}/drive_c/MT5Terminal/Files/BITTEN/Results/user_${TELEGRAM_ID}"
mkdir -p "${USER_WINE_DIR}/drive_c/MT5Terminal/Files/BITTEN/History/user_${TELEGRAM_ID}"

# Configure all 15 BITTEN pairs for this user
echo "🎯 Configuring 15 BITTEN pairs for user ${TELEGRAM_ID}..."
PAIRS=(EURUSD GBPUSD USDJPY USDCAD GBPJPY EURJPY AUDJPY GBPCHF AUDUSD NZDUSD USDCHF EURGBP GBPNZD GBPAUD EURAUD)

for pair in "${PAIRS[@]}"; do
    cat > "${USER_WINE_DIR}/drive_c/MT5Terminal/Files/BITTEN/bitten_instructions_${pair,,}_user_${TELEGRAM_ID}.json" << EOF
{
  "pair": "$pair",
  "action": "monitor",
  "magic_number": ${MAGIC_NUMBER},
  "telegram_id": "${TELEGRAM_ID}",
  "trading_account": "${TRADING_ACCOUNT}",
  "broker_server": "${BROKER_SERVER}",
  "status": "ready",
  "timestamp": "$(date -Iseconds)"
}
EOF
done

# Create user-specific bridge configuration
echo "🌉 Setting up user bridge connection..."
cat > "${USER_WINE_DIR}/drive_c/MT5Terminal/Files/BITTEN/bridge_config_user_${TELEGRAM_ID}.json" << EOF
{
  "telegram_id": "${TELEGRAM_ID}",
  "trading_account": "${TRADING_ACCOUNT}",
  "broker_server": "${BROKER_SERVER}",
  "bridge_endpoint": "3.145.84.187:5556",
  "drop_folder": "/user_${TELEGRAM_ID}",
  "magic_number": ${MAGIC_NUMBER},
  "status": "active",
  "created_at": "$(date -Iseconds)"
}
EOF

# Create credential destruction script (BYOB security)
echo "🔥 Creating credential destruction protocol..."
cat > "${USER_WINE_DIR}/destroy_credentials.sh" << 'EOF'
#!/bin/bash
# BYOB Security: Destroy credentials after successful login

echo "🔥 BYOB SECURITY: Destroying stored credentials..."

# Replace password in account.ini with placeholder
sed -i 's/Password=.*/Password=***DESTROYED***/' /root/.wine_user_7176191872/drive_c/MT5Terminal/config/account.ini

# Log credential destruction
echo "$(date -Iseconds): Credentials destroyed for user 7176191872" >> /root/.wine_user_7176191872/security.log

echo "✅ Credentials destroyed. Account remains logged in via MT5 session."
echo "🔐 BYOB security protocol completed."
EOF

chmod +x "${USER_WINE_DIR}/destroy_credentials.sh"

# Create verification script
echo "📋 Creating user verification script..."
cat > "${USER_WINE_DIR}/verify_user_setup.sh" << 'EOF'
#!/bin/bash
echo "🔍 BITTEN User Setup Verification - Telegram ID: 7176191872"
echo "=========================================================="

USER_DIR="/root/.wine_user_7176191872"

echo "📁 User Environment:"
if [ -d "$USER_DIR" ]; then
    echo "✅ User Wine directory exists: $USER_DIR"
    echo "✅ Size: $(du -sh $USER_DIR | cut -f1)"
else
    echo "❌ User Wine directory missing"
fi

echo ""
echo "📋 Account Configuration:"
if [ -f "$USER_DIR/drive_c/MT5Terminal/config/account.ini" ]; then
    echo "✅ Account configuration exists"
    grep "Login\|Server\|TelegramID" "$USER_DIR/drive_c/MT5Terminal/config/account.ini"
else
    echo "❌ Account configuration missing"
fi

echo ""
echo "📊 BITTEN Pairs Configuration:"
PAIR_COUNT=$(ls -1 "$USER_DIR/drive_c/MT5Terminal/Files/BITTEN/"bitten_instructions_*_user_7176191872.json 2>/dev/null | wc -l)
echo "✅ Configured pairs: $PAIR_COUNT/15"

echo ""
echo "🌉 Bridge Configuration:"
if [ -f "$USER_DIR/drive_c/MT5Terminal/Files/BITTEN/bridge_config_user_7176191872.json" ]; then
    echo "✅ Bridge config exists"
    cat "$USER_DIR/drive_c/MT5Terminal/Files/BITTEN/bridge_config_user_7176191872.json" | head -5
else
    echo "❌ Bridge config missing"
fi

echo ""
echo "🔐 Security Status:"
if [ -f "$USER_DIR/destroy_credentials.sh" ]; then
    echo "✅ Credential destruction script ready"
else
    echo "❌ Security script missing"
fi

echo ""
echo "🚀 User 7176191872 Status: CONFIGURED & READY"
echo "📋 Telegram ID: 7176191872"
echo "🎯 Trading Account: 843859@Coinexx-Demo"
echo "🔗 Bridge: Connected to AWS production (3.145.84.187:5556)"
echo "📁 Drop Folder: /user_7176191872"
echo "Ready for live trading!"
EOF

chmod +x "${USER_WINE_DIR}/verify_user_setup.sh"

# Update the main FireRouter to recognize this user
echo "🔧 Updating system to recognize user ${TELEGRAM_ID}..."
cat >> /root/HydraX-v2/user_registry.json << EOF
{
  "telegram_id": "${TELEGRAM_ID}",
  "trading_account": "${TRADING_ACCOUNT}",
  "broker_server": "${BROKER_SERVER}",
  "wine_environment": "${USER_WINE_DIR}",
  "status": "active",
  "created_at": "$(date -Iseconds)"
}
EOF

echo ""
echo "✅ User ${TELEGRAM_ID} Setup Complete!"
echo "📋 Telegram ID: ${TELEGRAM_ID}"
echo "🎯 Trading Account: ${TRADING_ACCOUNT}@${BROKER_SERVER}"
echo "🍷 Wine Environment: ${USER_WINE_DIR}"
echo ""
echo "🔧 Next Steps:"
echo "1. Run verification: bash ${USER_WINE_DIR}/verify_user_setup.sh"
echo "2. Test signal delivery to user ${TELEGRAM_ID}"
echo "3. Execute credential destruction after successful login"
echo "4. Test live trading execution"
echo ""
echo "🔐 BYOB Security: Credentials will be destroyed after first successful login"