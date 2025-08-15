# BITTEN System Integration Specifications

## Overview
This document provides comprehensive technical specifications for all integration points within the BITTEN trading system, including data formats, communication protocols, error handling, and integration patterns.

## 1. MT5 Farm Integration and Bridge System

### 1.1 Architecture Overview
The BITTEN system uses a hybrid approach for MT5 integration:
- **Remote MT5 Farm**: Remote server-based MT5 instances (129.212.185.102:8001)
- **Local MT5 Bridge**: File-based communication via EA (Expert Advisor)
- **Adaptive Routing**: Fallback mechanisms between remote and local bridges

### 1.2 MT5 Farm Adapter (`mt5_farm_adapter.py`)

#### Connection Configuration
```python
{
    "farm_url": "http://129.212.185.102:8001",
    "timeout": 30,
    "max_retries": 3,
    "heartbeat_interval": 5
}
```

#### API Endpoints
- **Health Check**: `GET /health`
- **Execute Trade**: `POST /execute`
- **Get Status**: `GET /status`
- **Close Trade**: `POST /close`
- **Live Data**: `GET /live_data`
- **Positions**: `GET /positions`

#### Trade Execution Request Format
```json
{
    "action": "OPEN_TRADE",
    "symbol": "EURUSD",
    "direction": "BUY",
    "lot_size": 0.01,
    "stop_loss": 1.0950,
    "take_profit": 1.1050,
    "comment": "BITTEN",
    "magic_number": 12345,
    "timestamp": 1672531200
}
```

#### Response Format
```json
{
    "success": true,
    "broker": "broker1",
    "ticket": 12345678,
    "message": "Trade executed successfully",
    "execution_time": 1672531201,
    "price": 1.1000
}
```

### 1.3 Local MT5 Bridge Configuration (`mt5_bridge.json`)

#### Bridge Settings
```json
{
    "mt5": {
        "enabled": true,
        "files_path": null,
        "check_interval_ms": 100,
        "trade_timeout": 30,
        "max_retries": 3,
        "slippage_points": 20,
        "magic_number": 20250626
    },
    "bridge": {
        "instruction_file": "bitten_instructions.txt",
        "result_file": "bitten_results.txt",
        "status_file": "bitten_status.txt",
        "heartbeat_interval": 5
    }
}
```

#### File Communication Protocol
- **Instruction File**: Write trade instructions
- **Result File**: Read execution results
- **Status File**: Monitor EA status

### 1.4 Error Handling
```python
# Connection failures
{
    "success": false,
    "error": "Farm request timeout",
    "fallback": "local_bridge",
    "retry_count": 3
}

# Trade execution errors
{
    "success": false,
    "error": "Insufficient margin",
    "error_code": "TRADE_RETCODE_NO_MONEY",
    "ticket": null
}
```

## 2. Telegram Bot Integration and Commands

### 2.1 Bot Configuration (`config/telegram.py`)

#### Core Settings
```python
{
    "BOT_TOKEN": "7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ",
    "MAIN_CHAT_ID": -1002581996861,
    "ADMIN_USER_ID": 7176191872,
    "PARSE_MODE": "HTML",
    "ALERT_TIMEOUT": 30,
    "MAX_ALERTS_PER_MINUTE": 10
}
```

### 2.2 Command Router (`telegram_router.py`)

#### Command Categories
```python
{
    "System": ["start", "help", "intel", "status", "me", "callsign"],
    "Trading Info": ["positions", "balance", "history", "performance"],
    "Trading Commands": ["fire", "close", "mode"],
    "Uncertainty Control": ["uncertainty", "bitmode", "yes", "no"],
    "Elite Features": ["tactical", "tcs", "signals", "closeall"],
    "Emergency Stop": ["emergency_stop", "panic", "halt_all"],
    "Education": ["learn", "missions", "journal", "achievements"],
    "Press Pass": ["presspass", "pp_status", "pp_upgrade"],
    "Admin Only": ["logs", "restart", "backup", "promote"]
}
```

#### Command Processing Flow
1. **Input Validation**: Sanitize user input
2. **Authentication**: Check user permissions
3. **Rate Limiting**: Prevent spam
4. **Command Routing**: Route to appropriate handler
5. **Response Generation**: Format response
6. **Error Handling**: Log and respond to errors

### 2.3 Message Formats

#### Signal Alert Format
```python
{
    "type": "signal_alert",
    "pair": "EURUSD",
    "direction": "BUY",
    "entry": 1.1000,
    "stop_loss": 1.0950,
    "take_profit": 1.1050,
    "confidence": 85,
    "tier": "PRECISION",
    "timestamp": "2024-01-01T12:00:00Z"
}
```

#### User Status Response
```python
{
    "user_id": 123456,
    "username": "trader123",
    "tier": "xp": 15000,
    "balance": 5000.00,
    "active_positions": 2,
    "session_pnl": 150.50
}
```

### 2.4 Webhook Security (`webhook_security.py`)

#### Security Middleware
- **Signature Verification**: Verify Telegram webhook signature
- **Rate Limiting**: 30 requests per minute
- **Request Size Validation**: 1MB maximum
- **Token Verification**: Validate webhook tokens
- **JSON Sanitization**: Sanitize incoming data

## 3. WebApp Integration and Endpoints

### 3.1 Flask Application (`web_app.py`)

#### Core Endpoints
```python
@app.route('/')                    # Landing page
@app.route('/terms')               # Terms of service
@app.route('/privacy')             # Privacy policy
@app.route('/refund')              # Refund policy
@app.route('/health')              # Health check
@app.route('/stripe/webhook')      # Stripe webhooks
```

### 3.2 WebApp Router (`webapp_router.py`)

#### HUD Interfaces
- **Sniper HUD**: `/sniper_hud` - Precision trading interface
- **Commander HUD**: `/commander_hud` - Advanced command interface
- **Mission HUD**: `/mission_hud` - Educational interface
- **Fang HUD**: `/fang_hud` - Aggressive trading interface

#### API Endpoints
```python
GET /api/user/profile              # User profile data
GET /api/trades/history            # Trade history
GET /api/signals/live              # Live signals
POST /api/trades/execute           # Execute trade
GET /api/analytics/performance     # Performance metrics
```

### 3.3 WebApp Signal Integration

#### Signal Display Format
```javascript
{
    "signal_id": "SIG_20240101_001",
    "pair": "EURUSD",
    "direction": "BUY",
    "entry": 1.1000,
    "stop_loss": 1.0950,
    "take_profit": 1.1050,
    "confidence": 85,
    "tier": "PRECISION",
    "tcs_score": 85,
    "visual_cues": {
        "color": "#00ff88",
        "icon": "🎯",
        "pattern": "Bullish breakout"
    }
}
```

## 4. External API Integrations

### 4.1 News API Integration (`news_api_client.py`)

#### Configuration
```python
{
    "provider": "economic_calendar",
    "api_key": "your_api_key",
    "monitored_currencies": ["USD", "EUR", "GBP", "JPY"],
    "cache_duration": 300,
    "buffer_before": 15,
    "buffer_after": 15
}
```

#### Event Structure
```python
{
    "event_time": "2024-01-01T14:30:00Z",
    "currency": "USD",
    "impact": "high",
    "event_name": "Non-Farm Payrolls",
    "forecast": "200K",
    "previous": "190K",
    "actual": "210K"
}
```

### 4.2 Market Data Integration

#### TraderMade API Client
```python
{
    "endpoint": "https://marketdata.tradermade.com/api/v1",
    "symbols": ["EURUSD", "GBPUSD", "USDJPY"],
    "update_interval": 1,
    "historical_data": true
}
```

#### Live Data Filter
```python
{
    "max_positions": 10,
    "max_per_symbol": 2,
    "drawdown_limit": 500,
    "risk_per_trade": 0.02
}
```

### 4.3 Stripe Payment Integration

#### Webhook Handler
```python
@app.route('/stripe/webhook', methods=['POST'])
def handle_stripe_webhook():
    event_types = [
        'subscription_created',
        'subscription_updated', 
        'subscription_deleted',
        'payment_succeeded',
        'payment_failed',
        'trial_ending'
    ]
```

#### Payment Processor
```python
{
    "stripe_key": "sk_live_YOUR_SECRET_KEY_HERE",
    "webhook_secret": "whsec_YOUR_WEBHOOK_SECRET_HERE",
    "products": {
        "nibbler": "price_nibbler_monthly",
        "apex": "price_apex_monthly",
        "press_pass": "price_press_pass_7day"
    }
}
```

## 5. Database Integration Patterns

### 5.1 Database Connection (`database/connection.py`)

#### Current Implementation
```python
class DatabaseSession:
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass
    
    def commit(self):
        pass
    
    def rollback(self):
        pass
```

### 5.2 Data Models

#### User Profile
```python
{
    "user_id": 123456,
    "telegram_id": 987654321,
    "tier": "xp": 15000,
    "subscription_status": "active",
    "callsign": "ALPHA_TRADER",
    "created_at": "2024-01-01T00:00:00Z",
    "last_activity": "2024-01-01T12:00:00Z"
}
```

#### Trade Record
```python
{
    "trade_id": "TRD_20240101_001",
    "user_id": 123456,
    "symbol": "EURUSD",
    "direction": "BUY",
    "lot_size": 0.01,
    "entry_price": 1.1000,
    "stop_loss": 1.0950,
    "take_profit": 1.1050,
    "status": "open",
    "profit": 0.00,
    "opened_at": "2024-01-01T12:00:00Z"
}
```

### 5.3 Data Persistence

#### File-Based Storage
- **User Profiles**: `data/bitten_xp.db`
- **Trade Records**: `data/trades/trades.db`
- **Market Data**: `data/live_market.db`
- **Onboarding**: `data/onboarding/active/`

#### Migration System
```bash
# Database migrations
migrations/
├── add_callsign_column.sql
├── press_pass_tables.sql
├── education_tables.sql
└── email_tracking_tables.sql
```

## 6. Real-time Communication Systems

### 6.1 WebSocket Integration

#### Signal Distribution
```python
{
    "type": "signal_update",
    "channel": "signals",
    "data": {
        "signal_id": "SIG_001",
        "status": "active",
        "pair": "EURUSD",
        "confidence": 85
    }
}
```

#### Position Updates
```python
{
    "type": "position_update",
    "channel": "positions",
    "data": {
        "ticket": 12345678,
        "symbol": "EURUSD",
        "profit": 25.50,
        "status": "open"
    }
}
```

### 6.2 Event System (`event_system.py`)

#### Event Types
- **signal_generated**: New signal created
- **trade_executed**: Trade opened/closed
- **user_upgraded**: User tier upgrade
- **emergency_stop**: Emergency stop triggered
- **news_alert**: High-impact news event

#### Event Handler Registration
```python
@event_system.on('signal_generated')
def handle_signal(event_data):
    # Process signal
    pass

@event_system.on('trade_executed')
def handle_trade(event_data):
    # Update positions
    pass
```

### 6.3 Notification System

#### Multi-Channel Notifications
- **Telegram**: Primary notification channel
- **WebApp**: Real-time updates
- **Email**: Important alerts
- **SMS**: Critical notifications (premium)

## 7. Monitoring and Logging Systems

### 7.1 Logging Configuration

#### Log Levels
- **DEBUG**: Development debugging
- **INFO**: General information
- **WARNING**: Warning messages
- **ERROR**: Error conditions
- **CRITICAL**: Critical failures

#### Log Files
```
logs/
├── bulletproof_agent.log
├── signal_bot.log
├── webapp_bitten_ultimate.log
├── mt5_bridge.log
└── stealth_log.txt
```

### 7.2 Health Monitoring

#### Health Check Endpoints
```python
@app.route('/health')
def health_check():
    return {
        'status': 'healthy',
        'service': 'BITTEN',
        'version': '2.0',
        'uptime': uptime_seconds,
        'components': {
            'database': 'healthy',
            'mt5_farm': 'healthy',
            'telegram_bot': 'healthy'
        }
    }
```

### 7.3 Performance Metrics

#### Key Performance Indicators
- **Signal Latency**: Time from generation to delivery
- **Trade Execution Time**: MT5 execution latency
- **System Uptime**: Service availability
- **Error Rate**: Error frequency
- **User Engagement**: Activity metrics

#### Metrics Collection
```python
{
    "timestamp": "2024-01-01T12:00:00Z",
    "metric": "signal_latency",
    "value": 150,
    "unit": "milliseconds",
    "tags": {
        "pair": "EURUSD",
        "tier": "PRECISION"
    }
}
```

## 8. Third-Party Service Integrations

### 8.1 Email Service Integration

#### Email Scheduler
```python
{
    "provider": "smtp",
    "host": "smtp.gmail.com",
    "port": 587,
    "username": "your_email@gmail.com",
    "password": "your_app_password",
    "tls": true
}
```

#### Email Templates
- **Welcome Email**: New user onboarding
- **Press Pass**: 7-day trial activation
- **Upgrade Notifications**: Tier upgrades
- **Performance Reports**: Weekly summaries

### 8.2 Payment Processing

#### Stripe Integration
```python
{
    "webhook_events": [
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
        "invoice.payment_succeeded",
        "invoice.payment_failed"
    ]
}
```

### 8.3 Social Media Integration

#### Twitter/X Integration
```python
{
    "api_key": "your_api_key",
    "api_secret": "your_api_secret",
    "bearer_token": "your_bearer_token",
    "auto_tweet": false,
    "hashtags": ["#BITTEN", "#Forex", "#Trading"]
}
```

## 9. Security and Error Handling

### 9.1 Security Measures

#### Input Validation
```python
def validate_trade_request(request):
    required_fields = ['symbol', 'direction', 'lot_size']
    for field in required_fields:
        if field not in request:
            raise ValueError(f"Missing required field: {field}")
    
    if request['lot_size'] <= 0 or request['lot_size'] > 10:
        raise ValueError("Invalid lot size")
```

#### Rate Limiting
```python
@rate_limit(max_requests=30, window=60)
def protected_endpoint():
    pass
```

### 9.2 Error Handling Patterns

#### Graceful Degradation
```python
def execute_trade_with_fallback(trade_request):
    try:
        # Try MT5 farm first
        result = mt5_farm_adapter.execute_trade(trade_request)
        if result['success']:
            return result
    except Exception as e:
        logger.warning(f"Farm failed: {e}")
    
    try:
        # Fallback to local bridge
        result = local_bridge.execute_trade(trade_request)
        return result
    except Exception as e:
        logger.error(f"All bridges failed: {e}")
        return {'success': False, 'error': 'Trading unavailable'}
```

#### Circuit Breaker Pattern
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'
    
    def call(self, func, *args, **kwargs):
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise e
```

## 10. Data Flow and Integration Patterns

### 10.1 Signal Flow Architecture

```
Intelligence Sources → Signal Fusion → Tier Router → User Delivery
     ↓                      ↓              ↓             ↓
Market Data            Confidence      Tier-Based    Telegram/WebApp
News Events           Calculation      Filtering     Notifications
AI Analysis              ↓              ↓             ↓
Technical Indicators  TCS Scoring    Permission    Real-time Updates
```

### 10.2 User Journey Integration

```
Registration → Onboarding → Tier Assignment → Signal Access → Trading
     ↓              ↓             ↓              ↓            ↓
Telegram Bot   13-Phase      XP System     Live Signals   MT5 Bridge
     ↓         Education         ↓              ↓            ↓
WebApp        Press Pass    Tier Unlock   Alert System  Position Mgmt
```

### 10.3 Risk Management Integration

```
Pre-Trade → Position Sizing → Execution → Monitoring → Management
    ↓           ↓               ↓           ↓           ↓
Risk Check  Account Info    MT5 Bridge   Live Data   Emergency Stop
    ↓           ↓               ↓           ↓           ↓
News Filter   Tier Limits   Error Handle  PnL Track   Tilt Control
```

## 11. Configuration Management

### 11.1 Configuration Files

#### Core Configuration
```yaml
# config/stealth_settings.yml
stealth:
  enabled: true
  protocols:
    - tor_routing
    - vpn_rotation
    - proxy_chains
  security_level: high
```

#### Trading Configuration
```yaml
# config/trading.yml
trading:
  max_positions: 10
  max_risk_per_trade: 0.02
  session_limits:
    london: 5
    new_york: 8
    tokyo: 3
```

### 11.2 Environment Variables

```bash
# Core settings
TELEGRAM_BOT_TOKEN=7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ
TELEGRAM_CHAT_ID=-1002581996861
TELEGRAM_USER_ID=7176191872

# MT5 settings
MT5_FARM_URL=http://129.212.185.102:8001
MT5_MAGIC_NUMBER=20250626

# Stripe settings
STRIPE_SECRET_KEY=sk_live_YOUR_SECRET_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET_HERE

# Database
DATABASE_URL=sqlite:///bitten_profiles.db
```

## 12. Deployment and Scaling

### 12.1 Service Architecture

```
Load Balancer → Web Server → Application Server → Database
     ↓              ↓              ↓               ↓
Nginx/HAProxy   Flask/Gunicorn   BITTEN Core    SQLite/PostgreSQL
     ↓              ↓              ↓               ↓
SSL/TLS       WebApp Router    Signal Engine    User Data
```

### 12.2 Monitoring Services

```bash
# SystemD services
bitten-web.service          # Web application
bitten-signals.service      # Signal processing
bitten-monitoring.service   # Health monitoring
press-pass-reset.service    # Press pass management
```

### 12.3 Backup and Recovery

```bash
# Backup script
#!/bin/bash
backup_dir="/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $backup_dir

# Backup databases
cp data/bitten_xp.db $backup_dir/
cp data/trades/trades.db $backup_dir/
cp data/live_market.db $backup_dir/

# Backup configuration
cp -r config/ $backup_dir/
cp -r src/bitten_core/ $backup_dir/bitten_core_backup/
```

## Conclusion

The BITTEN system represents a comprehensive trading platform with sophisticated integration patterns across multiple services. Key architectural strengths include:

1. **Modular Design**: Clear separation of concerns with dedicated modules
2. **Fault Tolerance**: Multiple fallback mechanisms and error handling
3. **Scalability**: Microservice-ready architecture with clear API boundaries
4. **Security**: Multiple layers of security and input validation
5. **Monitoring**: Comprehensive logging and health monitoring
6. **User Experience**: Gamified progression system with tiered access

The system effectively integrates MT5 trading, Telegram communication, web applications, payment processing, and real-time data feeds into a cohesive trading platform designed for both novice and experienced traders.