# HydraX v2 API Reference

## 🌐 **API Overview**

The HydraX v2 Flask API provides programmatic access to trading operations, system monitoring, and configuration management.

**Base URL**: `http://localhost:5000` (development) / `https://your-domain.com` (production)

## 🚀 **Quick Start**

### Authentication
Most endpoints require API key authentication via header:
```bash
curl -H "X-API-Key: your_dev_api_key" http://localhost:5000/api/endpoint
```

### Environment Setup
```env
DEV_API_KEY=your_secure_api_key_here
FLASK_ENV=development
FLASK_DEBUG=True
```

## 📋 **Core Endpoints**

### **System Endpoints**

#### `GET /`
**Description**: System home page and basic status  
**Authentication**: None  
**Response**: HTML page with system overview

**Example**:
```bash
curl http://localhost:5000/
```

#### `GET /status`
**Description**: Detailed system status and current trading mode  
**Authentication**: None  
**Response**: HTML page with tactical mode and system health

**Example**:
```bash
curl http://localhost:5000/status
```

#### `POST /status` 
**Description**: Telegram webhook endpoint  
**Authentication**: Telegram webhook validation  
**Payload**: Telegram update object  
**Response**: JSON confirmation

**Example Telegram Payload**:
```json
{
  "update_id": 123456789,
  "message": {
    "message_id": 1,
    "from": {"id": 12345, "username": "trader"},
    "chat": {"id": -1001234567890, "type": "supergroup"},
    "text": "/status"
  }
}
```

### **Trading Endpoints**

#### `POST /fire`
**Description**: Execute trading operations  
**Authentication**: API Key required  
**Content-Type**: `application/json`

**Request Body**:
```json
{
  "action": "buy|sell|close",
  "symbol": "XAUUSD",
  "volume": 0.1,
  "sl": 1950.00,
  "tp": 1980.00,
  "comment": "HydraX Auto Trade"
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Trade executed successfully",
  "trade_id": "12345",
  "symbol": "XAUUSD",
  "volume": 0.1,
  "price": 1965.45,
  "timestamp": "2025-07-04T15:30:00Z"
}
```

**Example**:
```bash
curl -X POST http://localhost:5000/fire \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "action": "buy",
    "symbol": "XAUUSD", 
    "volume": 0.1,
    "sl": 1950.00,
    "tp": 1980.00
  }'
```

### **Development Endpoints**

#### `GET /dev`
**Description**: Development commands and system utilities  
**Authentication**: DEV_API_KEY required  
**Query Parameters**:
- `cmd`: Command to execute
- `args`: Command arguments (optional)

**Available Commands**:
- `status`: System status check
- `restart`: Restart trading engine
- `logs`: Retrieve system logs
- `config`: View configuration
- `test`: Run system tests

**Example**:
```bash
curl "http://localhost:5000/dev?cmd=status" \
  -H "X-API-Key: your_dev_api_key"
```

**Response**:
```json
{
  "status": "success",
  "command": "status",
  "result": {
    "trading_active": true,
    "mode": "bit",
    "uptime": "2h 15m 30s",
    "last_trade": "2025-07-04T15:25:00Z"
  }
}
```

#### `GET /logs`
**Description**: Access system logs  
**Authentication**: DEV_API_KEY required  
**Query Parameters**:
- `lines`: Number of log lines (default: 100)
- `level`: Log level filter (debug, info, warning, error)

**Example**:
```bash
curl "http://localhost:5000/logs?lines=50&level=info" \
  -H "X-API-Key: your_dev_api_key"
```

## 🔐 **Authentication**

### **API Key Authentication**
Include API key in request headers:
```
X-API-Key: your_secure_api_key_here
```

### **Telegram Webhook Validation**
Telegram webhooks are validated using bot token verification.

### **Error Responses**
**401 Unauthorized**:
```json
{
  "error": "Unauthorized",
  "message": "Valid API key required"
}
```

**403 Forbidden**:
```json
{
  "error": "Forbidden", 
  "message": "Invalid API key"
}
```

## 📊 **Response Formats**

### **Success Response**
```json
{
  "status": "success",
  "message": "Operation completed successfully",
  "data": {
    // Response data
  },
  "timestamp": "2025-07-04T15:30:00Z"
}
```

### **Error Response**
```json
{
  "status": "error",
  "error": "ErrorType",
  "message": "Detailed error message",
  "code": 400,
  "timestamp": "2025-07-04T15:30:00Z"
}
```

## 🛠️ **Trading Operations**

### **Order Types**
- `buy`: Market buy order
- `sell`: Market sell order
- `buy_limit`: Limit buy order
- `sell_limit`: Limit sell order
- `close`: Close position by ID
- `close_all`: Close all positions

### **Symbol Format**
Use standard broker symbol format:
- Forex: `EURUSD`, `GBPJPY`, `USDCAD`
- Metals: `XAUUSD`, `XAGUSD`
- Indices: `US30`, `SPX500`, `USTEC`

### **Volume Specification**
- Forex: Standard lots (0.01 = 1,000 units)
- Metals: Troy ounces (0.1 = 10 oz)
- Indices: Contract size varies by instrument

## 📈 **Webhook Integration**

### **Telegram Webhook Setup**
Configure webhook URL with Telegram:
```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-domain.com/status"}'
```

### **Webhook Processing**
The `/status` endpoint handles both GET and POST requests:
- **GET**: Display status page
- **POST**: Process Telegram updates

### **Supported Telegram Commands**
- `/start`: Bot initialization
- `/status`: System status check
- `/mode bit|commander`: Switch trading modes
- Advanced commands as defined in bot implementation

## 🔧 **Configuration Management**

### **Environment Variables**
```env
# Flask Configuration
FLASK_APP=src/core/TEN_elite_commands_FULL.py
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your_secret_key_here

# API Security
DEV_API_KEY=your_secure_api_key_here

# Telegram Integration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Trading Configuration
BRIDGE_URL=http://127.0.0.1:9000
MAX_RISK_PERCENT=2.0
MAX_CONCURRENT_TRADES=3
```

### **Runtime Configuration**
System configuration can be modified via development endpoints or environment variables.

## 📝 **Logging**

### **Log Levels**
- `DEBUG`: Detailed diagnostic information
- `INFO`: General operational messages
- `WARNING`: Warning messages for unusual events
- `ERROR`: Error messages for failed operations

### **Log Format**
```
2025-07-04 15:30:00 [INFO] Trading: Buy order executed - XAUUSD 0.1 @ 1965.45
2025-07-04 15:30:05 [DEBUG] API: /fire endpoint called with valid authentication
2025-07-04 15:30:10 [WARNING] Risk: Position size exceeds recommended risk level
```

## 🚨 **Error Handling**

### **Common Error Codes**
- `400`: Bad Request - Invalid parameters
- `401`: Unauthorized - Missing or invalid API key
- `403`: Forbidden - Access denied
- `404`: Not Found - Endpoint not found
- `500`: Internal Server Error - System error

### **Trading Errors**
- `INSUFFICIENT_MARGIN`: Not enough margin for trade
- `INVALID_SYMBOL`: Unknown trading instrument
- `MARKET_CLOSED`: Trading not available
- `POSITION_NOT_FOUND`: Trade ID not found

## 🧪 **Testing**

### **Health Check**
```bash
curl http://localhost:5000/status
```

### **API Authentication Test**
```bash
curl -H "X-API-Key: SECRET123" http://localhost:5000/dev?cmd=status
```

### **Trading API Test**
```bash
curl -X POST http://localhost:5000/fire \
  -H "Content-Type: application/json" \
  -H "X-API-Key: SECRET123" \
  -d '{"action": "test", "symbol": "XAUUSD"}'
```

## 📚 **Additional Resources**

- [Development Guide](development.md) - Setup and development workflow
- [BITTEN Bot Commands](bitten/commands.md) - Telegram bot reference
- [Security Guidelines](security.md) - Security best practices
- [Deployment Guide](deployment.md) - Production deployment

---

**📝 Note**: This API reference is based on the current Flask implementation in `src/core/TEN_elite_commands_FULL.py`. Additional endpoints may be available based on system configuration.