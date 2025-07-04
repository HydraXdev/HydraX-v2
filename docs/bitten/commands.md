# BITTEN Bot Commands Reference

## 🤖 **Bot Overview**
BITTEN (Bit by Bit Edition) is the Telegram command interface for HydraX v2 trading system.

## 📋 **Core Commands**

### **System Commands**

#### `/start`
**Description**: Initialize bot and display welcome message  
**Usage**: `/start`  
**Response**: Bot introduction and available commands  
**Access Level**: All users

#### `/status`
**Description**: Display current system status and tactical mode  
**Usage**: `/status`  
**Response**: 
- System health status
- Current trading mode (Bit/Commander)
- Active tactical logic mode
- Recent trade summary
**Access Level**: All users

#### `/mode [mode_name]`
**Description**: Switch between trading modes  
**Usage**: 
- `/mode bit` - Switch to Bit Mode (safe scalping)
- `/mode commander` - Switch to Commander Mode (high risk)
- `/mode` - Display current mode
**Response**: Mode confirmation and settings  
**Access Level**: Authorized users only

### **Trading Commands**

#### `/fire [pair] [direction] [size]`
**Description**: Execute manual trade  
**Usage**: `/fire XAUUSD buy 0.1`  
**Parameters**:
- `pair`: Trading instrument (XAUUSD, EURUSD, etc.)
- `direction`: buy/sell
- `size`: Position size in lots
**Response**: Trade execution confirmation with details  
**Access Level**: Authorized traders only

#### `/close [trade_id]`
**Description**: Close specific trade by ID  
**Usage**: `/close 12345`  
**Response**: Trade closure confirmation  
**Access Level**: Authorized traders only

#### `/closeall`
**Description**: Close all open positions  
**Usage**: `/closeall`  
**Response**: Confirmation of all trades closed  
**Access Level**: Admin only

### **Information Commands**

#### `/positions`
**Description**: Display all open positions  
**Usage**: `/positions`  
**Response**: List of open trades with P&L  
**Access Level**: Authorized users

#### `/balance`
**Description**: Show account balance and equity  
**Usage**: `/balance`  
**Response**: Account financial summary  
**Access Level**: Authorized users

#### `/history [days]`
**Description**: Show trading history  
**Usage**: `/history 7` (last 7 days)  
**Response**: Trade history with performance stats  
**Access Level**: Authorized users

#### `/performance`
**Description**: Display performance metrics  
**Usage**: `/performance`  
**Response**: Win rate, profit factor, drawdown stats  
**Access Level**: Authorized users

### **Configuration Commands**

#### `/risk [percentage]`
**Description**: Set risk percentage per trade  
**Usage**: `/risk 2.5` (2.5% risk per trade)  
**Response**: Risk setting confirmation  
**Access Level**: Admin only

#### `/maxpos [number]`
**Description**: Set maximum concurrent positions  
**Usage**: `/maxpos 3`  
**Response**: Position limit confirmation  
**Access Level**: Admin only

#### `/notify [on/off]`
**Description**: Toggle trade notifications  
**Usage**: `/notify on`  
**Response**: Notification setting confirmation  
**Access Level**: All users

### **Elite Commands** (Advanced)

#### `/tactical [mode]`
**Description**: Set tactical logic mode  
**Usage**: 
- `/tactical auto` - Fully automated
- `/tactical semi` - Semi-automated with confirmations
- `/tactical sniper` - Precision timing
- `/tactical leroy` - High-frequency aggressive
**Response**: Tactical mode confirmation  
**Access Level**: Elite users only

#### `/tcs [pair]`
**Description**: Get Trade Confidence Score for instrument  
**Usage**: `/tcs XAUUSD`  
**Response**: TCS score (0-100) with analysis breakdown  
**Access Level**: Elite users only

#### `/signals [pair]`
**Description**: Get current market signals  
**Usage**: `/signals EURUSD`  
**Response**: Technical analysis and trade recommendations  
**Access Level**: Elite users only

### **Admin Commands**

#### `/logs [lines]`
**Description**: Display recent system logs  
**Usage**: `/logs 50`  
**Response**: Recent log entries  
**Access Level**: Admin only

#### `/restart`
**Description**: Restart trading system  
**Usage**: `/restart`  
**Response**: System restart confirmation  
**Access Level**: Admin only

#### `/backup`
**Description**: Create system backup  
**Usage**: `/backup`  
**Response**: Backup creation confirmation  
**Access Level**: Admin only

## 🔐 **Access Levels**

### **All Users**
- Basic system information
- Personal notification settings
- Bot initialization

### **Authorized Users**
- Trading information viewing
- Basic trading commands
- Personal account data

### **Elite Users**
- Advanced trading features
- Tactical mode switching
- Signal analysis tools

### **Admin**
- System configuration
- Risk management settings
- System maintenance commands

## 📱 **Usage Examples**

### **Daily Trading Workflow**
```
/start                    # Initialize session
/status                   # Check system status
/mode bit                 # Set to safe mode
/positions               # Check open trades
/tcs XAUUSD              # Check trade confidence
/fire XAUUSD buy 0.1     # Execute trade
/notify on               # Enable notifications
```

### **Risk Management**
```
/risk 2.0                # Set 2% risk per trade
/maxpos 3                # Maximum 3 positions
/balance                 # Check account status
/performance             # Review performance
```

### **System Monitoring**
```
/status                  # System health check
/logs 100                # Recent system logs
/history 30              # Last 30 days performance
```

## ⚙️ **Bot Configuration**

### **Environment Variables**
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_authorized_chat_id
ADMIN_CHAT_ID=your_admin_chat_id
ELITE_USERS=user1,user2,user3
```

### **Command Permissions**
Commands are filtered by user authorization level. Unauthorized users receive permission denied messages.

### **Rate Limiting**
- Basic commands: No limit
- Trading commands: 10 per minute
- Admin commands: 5 per minute

## 🔔 **Notification Types**

### **Trade Notifications**
- Trade execution confirmations
- Position closure alerts
- Stop loss/take profit triggers
- Margin call warnings

### **System Notifications**
- Mode switch confirmations
- System startup/shutdown
- Error alerts
- Performance milestones

### **Market Notifications**
- High-confidence signals
- Market volatility alerts
- Economic news impact warnings

## 🛠️ **Implementation Status**

### ✅ **Implemented**
- Basic system commands (/start, /status)
- Mode switching framework
- Command parsing infrastructure
- User authorization system

### 🚧 **In Development**
- Trading execution commands
- Position management
- Performance analytics
- Elite command features

### 🎯 **Planned**
- Advanced signal analysis
- Automated trade management
- Custom alert configurations
- Portfolio optimization commands

---

**📝 Note**: Command availability depends on your authorization level and system configuration. Contact your administrator for access level upgrades.