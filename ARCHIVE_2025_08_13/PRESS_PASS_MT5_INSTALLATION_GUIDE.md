# 🎯 PRESS PASS MT5 INSTALLATION GUIDE

## ✅ PERFECT - Directory Renamed Successfully!
- **Old**: `C:\MT5_Farm\Masters\Generic_Demo\`
- **New**: `C:\MT5_Farm\Masters\PRESS_PASS\` ✅

## 📥 METAQUOTES MT5 - INSTANT DEMO ACCOUNTS

### **Direct Download Link (No Credentials Required)**
```
https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe
```

### **Why This Specific MT5?**
- ✅ **Instant Demo**: Creates demo accounts automatically
- ✅ **No Registration**: No email or personal info required
- ✅ **$10,000 Balance**: Instant virtual trading capital
- ✅ **All Pairs**: Full forex pair access
- ✅ **No Expiry**: Demo accounts don't expire
- ✅ **Perfect for Press Pass**: Immediate value for trial users

### **Installation Instructions**

#### **Step 1: Download MT5**
```powershell
# Download MetaQuotes MT5 directly to server
powershell -Command "Invoke-WebRequest -Uri 'https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe' -OutFile 'C:\MT5_Farm\mt5_metaquotes.exe'"
```

#### **Step 2: Install to PRESS_PASS Directory**
1. **Run**: `C:\MT5_Farm\mt5_metaquotes.exe`
2. **Install Path**: `C:\MT5_Farm\Masters\PRESS_PASS\`
3. **Complete Installation**: Follow wizard (all defaults are fine)

#### **Step 3: First Launch**
1. **Open MT5** from PRESS_PASS directory
2. **Demo Account**: Will auto-prompt for demo account creation
3. **Select**: "MetaQuotes-Demo" server (default)
4. **Account Created**: Instant $10,000 demo account
5. **No Forms**: No email, phone, or verification required

#### **Step 4: Deploy EA**
```batch
# Copy EA to MT5 installation
copy "C:\MT5_Farm\EA.mq5" "C:\MT5_Farm\Masters\PRESS_PASS\MQL5\Experts\BITTENBridge_v3_ENHANCED.mq5"
```

#### **Step 5: Configure EA**
1. **MetaEditor**: Press F4 in MT5
2. **Compile EA**: Press F7 to compile BITTENBridge_v3_ENHANCED.mq5
3. **Success Check**: No compilation errors
4. **Attach to Charts**: Drag EA to 10 currency pairs
5. **Enable AutoTrading**: Ctrl+E (green button should show)

### **PRESS PASS Configuration**

#### **Magic Number Range**: 50001-50200
- Each PRESS_PASS user gets unique magic number
- Prevents trade conflicts between users
- Easy identification in logs

#### **Currency Pairs for PRESS_PASS**
- EURUSD (most popular)
- GBPUSD (volatile, good for demos)
- USDJPY (Asian session coverage)
- USDCAD (North American session)
- GBPJPY (high volatility for excitement)
- AUDUSD (commodity pair)
- NZDUSD (Pacific session)
- EURGBP (European cross)
- USDCHF (safe haven)
- EURJPY (carry trade pair)

#### **PRESS_PASS User Experience**
1. **Instant Access**: Demo account ready in 30 seconds
2. **Real Market Data**: Live prices, real spreads
3. **Full Trading**: All BITTEN features available
4. **XP Earning**: Real progression system
5. **7-Day Trial**: Full week to experience system
6. **Upgrade Path**: Easy conversion to paid tiers

### **Alternative MetaQuotes Servers (If Needed)**

#### **Primary**: MetaQuotes-Demo
- **Server**: MetaQuotes-Demo
- **Balance**: $10,000
- **Leverage**: 1:100
- **Perfect for**: Press Pass users

#### **Backup**: MetaQuotes Software Corp
- **Server**: MetaQuotes Software Corp-Demo
- **Balance**: $10,000
- **Leverage**: 1:500
- **Use if**: Primary server unavailable

### **Verification Commands**

#### **Check MT5 Installation**
```powershell
# Verify MT5 installed
Test-Path "C:\MT5_Farm\Masters\PRESS_PASS\terminal64.exe"

# Check EA deployment
Test-Path "C:\MT5_Farm\Masters\PRESS_PASS\MQL5\Experts\BITTENBridge_v3_ENHANCED.mq5"

# List MT5 processes
Get-Process terminal64 -ErrorAction SilentlyContinue
```

#### **Test Demo Account Creation**
1. **Launch MT5**: `C:\MT5_Farm\Masters\PRESS_PASS\terminal64.exe`
2. **Auto-Prompt**: Demo account dialog should appear
3. **Quick Setup**: Select MetaQuotes-Demo, click Next
4. **Instant Account**: Should receive login credentials immediately
5. **$10,000 Balance**: Verify account balance shows

### **🎯 Success Criteria**

#### **PRESS_PASS Installation Complete When**:
- ✅ MT5 launches from PRESS_PASS directory
- ✅ Demo account created (no credentials required)
- ✅ $10,000 balance visible
- ✅ EA compiled and attached to 10 pairs
- ✅ AutoTrading enabled (green button)
- ✅ Connection to BITTEN Linux server established

#### **User Ready When**:
- ✅ Can open MT5 and see live charts
- ✅ EA is running on all pairs (smiley faces visible)
- ✅ BITTEN signals arrive and execute
- ✅ XP system tracking trades
- ✅ 7-day countdown timer active

### **🚀 Quick Installation Script**

```batch
@echo off
echo ========================================
echo    PRESS PASS MT5 INSTALLATION
echo ========================================
echo.

echo 1. Downloading MetaQuotes MT5...
powershell -Command "Invoke-WebRequest -Uri 'https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe' -OutFile 'C:\MT5_Farm\mt5_metaquotes.exe'"

echo.
echo 2. Installing to PRESS_PASS directory...
echo    Install path: C:\MT5_Farm\Masters\PRESS_PASS\
echo    Use all default settings
echo.
start "" "C:\MT5_Farm\mt5_metaquotes.exe"

echo.
echo 3. After installation completes:
echo    - Launch MT5 from PRESS_PASS folder
echo    - Create demo account (MetaQuotes-Demo server)
echo    - Copy and compile EA
echo    - Attach to 10 currency pairs
echo.
pause
```

**This MetaQuotes MT5 is perfect for Press Pass because it provides instant trading access without any barriers - exactly what trial users need!** 🎯