# BITTEN System Architecture

## Table of Contents
1. [High-Level System Overview](#high-level-system-overview)
2. [Component Architecture](#component-architecture)
3. [Technology Stack](#technology-stack)
4. [Database Architecture](#database-architecture)
5. [API Endpoints & Interfaces](#api-endpoints--interfaces)
6. [Security Architecture](#security-architecture)
7. [Deployment Architecture](#deployment-architecture)

---

## 1. High-Level System Overview

```
                        ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
                        │                                  BITTEN TRADING OPERATIONS CENTER                                   │
                        │                                     (HydraX v2 Platform)                                           │
                        └─────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                                      │
                                                                      ▼
                        ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
                        │                                  TELEGRAM INTERFACE LAYER                                          │
                        │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
                        │  │   Bot Commands  │  │   Press Pass    │  │   Webhooks      │  │   Web Apps      │            │
                        │  │   & Messaging   │  │   System        │  │   Handler       │  │   Integration   │            │
                        │  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
                        └─────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                                      │
                                                                      ▼
                        ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
                        │                                    BITTEN CORE SYSTEM                                             │
                        │                                                                                                     │
                        │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
                        │  │   Core Engine   │  │   Rank Access   │  │   Fire Router   │  │   XP System     │            │
                        │  │   Controller    │  │   Manager       │  │   & Execution   │  │   & Achievements│            │
                        │  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
                        │                                                                                                     │
                        │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
                        │  │   TCS Engine    │  │   Risk Manager  │  │   News System   │  │   Stealth       │            │
                        │  │   Self-Optimizing│  │   & Controls    │  │   & Scheduler   │  │   Protocol      │            │
                        │  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
                        └─────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                                      │
                                                                      ▼
                        ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
                        │                                    TRADING LAYER                                                   │
                        │                                                                                                     │
                        │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
                        │  │   MT5 Farm      │  │   10-Pair       │  │   Strategy      │  │   Signal        │            │
                        │  │   Integration   │  │   Self-Optimizer│  │   Engine        │  │   Generation    │            │
                        │  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
                        │                                                                                                     │
                        │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
                        │  │   Order Flow    │  │   Market Data   │  │   Sentiment     │  │   News Filter   │            │
                        │  │   Analysis      │  │   Processing    │  │   Analysis      │  │   & Blackouts   │            │
                        │  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
                        └─────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                                      │
                                                                      ▼
                        ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
                        │                                    DATA LAYER                                                      │
                        │                                                                                                     │
                        │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
                        │  │   PostgreSQL    │  │   SQLite        │  │   File System   │  │   Redis Cache   │            │
                        │  │   Production DB │  │   Local Storage │  │   JSON/CSV      │  │   (Optional)    │            │
                        │  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
                        └─────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                                      │
                                                                      ▼
                        ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
                        │                                  EXTERNAL INTEGRATIONS                                            │
                        │                                                                                                     │
                        │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
                        │  │   Telegram API  │  │   MT5 Brokers   │  │   News APIs     │  │   Payment       │            │
                        │  │   Bot Platform  │  │   Multi-Broker  │  │   Economic Data │  │   Processors    │            │
                        │  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
                        └─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### System Flow Overview
1. **User Interface**: Telegram bot serves as primary interface
2. **Core Processing**: BITTEN core processes commands and manages state
3. **Trading Logic**: Self-optimizing TCS engine filters and executes signals
4. **Data Management**: Multi-tier storage with PostgreSQL and SQLite
5. **External Services**: Integration with MT5 farm and market data providers

---

## 2. Component Architecture

### 2.1 Core Components

#### BITTEN Core (`bitten_core.py`)
- **Purpose**: Central system orchestrator and state manager
- **Responsibilities**:
  - System mode management (BIT, COMMANDER, TACTICAL, STEALTH)
  - User session handling
  - Component coordination
  - Performance monitoring
  - Health status tracking

```python
class BittenCore:
    - system_health: SystemHealth
    - rank_access: RankAccess 
    - telegram_router: TelegramRouter
    - fire_router: FireRouter
    - user_sessions: Dict[UserSession]
    - performance_stats: Dict
```

#### Self-Optimizing TCS Engine (`self_optimizing_tcs.py`)
- **Purpose**: Dynamic threshold adjustment for optimal signal volume
- **Key Features**:
  - Target: 65 signals/day across 10 pairs
  - TCS threshold range: 70-78%
  - Market condition adaptation
  - Performance-based adjustment

```python
class SelfOptimizingTCS:
    - target_signals_per_day: 65
    - current_tcs_threshold: 70.0-78.0
    - market_condition_assessment
    - signal_volume_optimization
```

#### MT5 Farm Adapter (`mt5_farm_adapter.py`)
- **Purpose**: Multi-broker trade execution
- **Features**:
  - Remote MT5 server communication
  - Trade execution across multiple brokers
  - Real-time status monitoring
  - Failover capabilities

### 2.2 Trading Components

#### Fire Router (`fire_router.py`)
- **Purpose**: Trade execution and routing
- **Functions**:
  - Signal validation and filtering
  - Risk management enforcement
  - Trade execution coordination
  - Position management

#### Strategy Engine (`strategies/`)
- **Components**:
  - `london_breakout.py`: London session breakout strategy
  - `mean_reversion.py`: Mean reversion signals
  - `momentum_continuation.py`: Trend continuation
  - `cross_asset_correlation.py`: Multi-asset analysis

#### Risk Management (`risk_management.py`)
- **Features**:
  - Real-time exposure monitoring
  - Daily loss limits
  - Position sizing calculations
  - Emergency stop mechanisms

### 2.3 User Interface Components

#### Telegram Router (`telegram_router.py`)
- **Purpose**: Command processing and response handling
- **Commands**: 25+ specialized trading commands
- **Features**:
  - Command validation and routing
  - Response formatting
  - User context management

#### Web Applications (`ui/`)
- **Sniper HUD**: Real-time trading interface
- **Mission HUD**: Gamified trading dashboard
- **Commander HUD**: Advanced trading controls
- **Education HUD**: Training and tutorials

### 2.4 Data Processing

#### XP System (`xp_*.py`)
- **Purpose**: Gamification and achievement tracking
- **Features**:
  - XP calculation and tracking
  - Achievement system
  - Rank progression
  - Reward distribution

#### Analytics Engine (`analytics/`)
- **Components**:
  - Real-time performance monitoring
  - Funnel analysis
  - Anomaly detection
  - Reporting system

---

## 3. Technology Stack

### 3.1 Backend Technologies

#### Core Framework
- **Python 3.8+**: Primary programming language
- **Flask**: Web framework for API endpoints
- **AsyncIO**: Asynchronous processing
- **SQLAlchemy**: ORM for database operations

#### Libraries & Dependencies
```yaml
Core:
  - flask: Web framework
  - requests: HTTP client
  - asyncio: Async operations
  - json: Data serialization
  - sqlite3: Local database
  - psycopg2: PostgreSQL adapter

Trading:
  - numpy: Mathematical operations
  - pandas: Data analysis
  - matplotlib: Visualization
  - ta-lib: Technical analysis (optional)

Security:
  - cryptography: Encryption
  - hashlib: Hashing
  - secrets: Secure random generation
```

### 3.2 Frontend Technologies

#### Web UI Stack
- **HTML5**: Markup structure
- **CSS3**: Styling and animations
- **JavaScript (ES6+)**: Interactive functionality
- **WebSockets**: Real-time communication

#### Styling Framework
```css
Fonts:
  - Rajdhani: Primary UI font
  - Orbitron: Monospace for data
  - Google Fonts CDN

Effects:
  - CSS animations
  - Matrix effects
  - Glitch effects
  - Tier-based themes
```

### 3.3 Integration Technologies

#### APIs & Protocols
- **Telegram Bot API**: Primary user interface
- **WebHooks**: Real-time event handling
- **REST API**: Internal service communication
- **HTTP/HTTPS**: Web protocols

#### Data Formats
- **JSON**: API responses and configuration
- **YAML**: Configuration files
- **CSV**: Data export format
- **SQLite**: Local data storage

---

## 4. Database Architecture

### 4.1 Production Database (PostgreSQL)

#### Schema Overview
```sql
-- Core Tables
users                  -- User accounts and subscription data
user_profiles          -- XP, achievements, trading stats
trades                 -- Trade history and results
trade_modifications    -- Trade modification log

-- Risk Management
risk_sessions          -- Daily risk tracking
news_events           -- Economic calendar events

-- Gamification
xp_transactions       -- XP earning history
achievements          -- Achievement definitions
user_achievements     -- User achievement progress

-- Subscriptions
subscription_plans    -- Tier definitions
user_subscriptions    -- User subscription status
payment_transactions  -- Payment history

-- System
audit_log            -- System audit trail
```

#### Key Relationships
```sql
users (1) ←→ (1) user_profiles
users (1) ←→ (n) trades
users (1) ←→ (n) xp_transactions
users (1) ←→ (n) user_achievements
users (1) ←→ (n) user_subscriptions
```

### 4.2 Local Storage (SQLite)

#### Purpose-Specific Databases
```
/data/bitten_xp.db          -- XP and achievement tracking
/data/trades/trades.db      -- Trade history storage
/data/live_market.db        -- Real-time market data
/data/tcs_optimization.db   -- TCS optimization tracking
```

#### File-Based Storage
```
/data/onboarding/           -- User onboarding sessions
/data/trades/exports/       -- Trade export files
/logs/                      -- System logs
/backups/                   -- Automated backups
```

### 4.3 Data Flow & Synchronization

#### Real-Time Data Pipeline
```
Market Data → TCS Engine → Signal Generation → Trade Execution → Database Storage
     ↓              ↓            ↓               ↓                    ↓
Analytics ←  Optimization ← Filtering ← Position Mgmt ← Performance Tracking
```

#### Backup Strategy
- **Automated Backups**: Daily full backups
- **Version Control**: Configuration file versioning
- **Disaster Recovery**: Multi-tier backup system

---

## 5. API Endpoints & Interfaces

### 5.1 Core API Endpoints

#### System Management
```http
GET  /                    # System overview
GET  /status              # System health status
POST /status              # Telegram webhook endpoint
GET  /health              # Health check
GET  /stats               # System statistics
```

#### Trading Operations
```http
POST /fire                # Execute trade
POST /close               # Close position
GET  /positions           # List open positions
GET  /performance         # Performance metrics
```

#### Development & Admin
```http
GET  /dev                 # Development commands
GET  /logs                # System logs
POST /webhook             # Telegram webhook
GET  /news                # News events
```

### 5.2 Internal Service APIs

#### BITTEN Core Interface
```python
class BittenCoreAPI:
    def process_telegram_update(update_data: Dict) -> Dict
    def execute_trade(trade_request: TradeRequest) -> TradeResult
    def get_user_session(user_id: int) -> UserSession
    def update_system_mode(mode: SystemMode) -> bool
```

#### MT5 Farm Interface
```python
class MT5FarmAPI:
    def execute_trade(trade_params: Dict) -> Dict
    def get_status() -> Dict
    def close_trade(ticket: int) -> Dict
    def check_health() -> Dict
```

### 5.3 Telegram Bot Interface

#### Command Structure
```python
# Core Commands
/start                    # Initialize bot
/status                   # System status
/mode [bit|commander]     # Switch modes
/fire SYMBOL BUY/SELL     # Execute trade
/close TICKET             # Close position
/performance              # Show stats

# Advanced Commands (25+ total)
/gear                     # Equipment management
/xp                       # XP status
/achievements             # Achievement list
/press_pass               # Press pass system
/stealth                  # Stealth mode
```

#### Response Format
```json
{
  "success": true,
  "message": "Trade executed successfully",
  "data": {
    "trade_id": "12345",
    "symbol": "GBPUSD",
    "direction": "BUY",
    "lot_size": 0.1,
    "entry_price": 1.2650,
    "timestamp": "2025-07-09T10:30:00Z"
  }
}
```

---

## 6. Security Architecture

### 6.1 Authentication & Authorization

#### Multi-Tier Access Control
```python
class UserRank(Enum):
    RECRUIT = "recruit"           # Basic access
    AUTHORIZED = "authorized"     # Standard features
    ELITE = "elite"              # Advanced features
    ADMIN = "admin"              # System administration
```

#### Press Pass System
```python
class PressPassManager:
    - daily_limit: 10 passes/day
    - duration: 7 days
    - tier_granted: - urgency_mechanism: Real-time scarcity
```

### 6.2 Security Measures

#### Input Validation
```python
class SecurityValidator:
    - String sanitization
    - Path traversal prevention
    - SQL injection protection
    - XSS prevention
    - Rate limiting
```

#### Webhook Security
```python
class WebhookSecurity:
    - Telegram signature verification
    - Request size validation
    - Rate limiting (30 req/min)
    - IP filtering
    - Token validation
```

### 6.3 Data Protection

#### Encryption & Hashing
- **API Keys**: Secure generation and storage
- **User Data**: Encrypted sensitive information
- **Database**: Connection encryption
- **Backups**: Encrypted storage

#### Privacy Controls
```python
class PrivacyManager:
    - Data minimization
    - Consent management
    - Right to deletion
    - Data portability
    - Audit logging
```

---

## 7. Deployment Architecture

### 7.1 Production Environment

#### Server Architecture
```
Load Balancer (nginx)
    ├── Web Application Server (Flask + Gunicorn)
    ├── Database Server (PostgreSQL)
    ├── Cache Layer (Redis - Optional)
    └── MT5 Farm Server (Remote)
```

#### Process Management
```bash
# System Services
bitten-web.service          # Main web application
bitten_email_scheduler.service  # Email automation
press_pass_monitoring.service   # Press pass analytics
press_pass_reset.service       # Daily reset tasks
```

### 7.2 Deployment Components

#### Docker Configuration (Optional)
```dockerfile
FROM python:3.8-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "start_bitten.py"]
```

#### Environment Configuration
```env
# Application
FLASK_ENV=production
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=9001

# Database
DATABASE_URL=postgresql://user:pass@host:5432/bitten
SQLITE_PATH=/data/bitten.db

# Security
SECRET_KEY=your_secret_key
DEV_API_KEY=your_api_key
TELEGRAM_BOT_TOKEN=your_bot_token

# Trading
MT5_FARM_URL=http://129.212.185.102:8001
TCS_THRESHOLD=70.0
```

### 7.3 Monitoring & Maintenance

#### Health Monitoring
```python
class HealthMonitor:
    - System uptime tracking
    - Resource usage monitoring
    - Error rate tracking
    - Performance metrics
    - Alert system
```

#### Backup Strategy
```bash
# Automated Backups
*/30 * * * * /backup/backup_script.sh  # Every 30 minutes
0 2 * * * /backup/daily_backup.sh      # Daily at 2 AM
0 0 * * 0 /backup/weekly_backup.sh     # Weekly on Sunday
```

#### Scaling Considerations
- **Horizontal**: Multiple application instances
- **Vertical**: Resource allocation scaling
- **Database**: Read replicas for high load
- **Caching**: Redis for frequently accessed data

---

## System Specifications Summary

### Performance Targets
- **Signal Generation**: 65 signals/day across 10 pairs
- **Response Time**: < 200ms for API calls
- **Uptime**: 99.9% availability target
- **Concurrent Users**: 1000+ simultaneous users

### Resource Requirements
- **CPU**: 2+ cores for production
- **Memory**: 4GB+ RAM recommended
- **Storage**: 100GB+ for data and logs
- **Network**: Stable internet for MT5 farm

### Scalability Features
- **Microservice Architecture**: Component separation
- **Database Sharding**: User-based partitioning
- **Caching Layer**: Redis for performance
- **Load Balancing**: Multi-instance deployment

This architecture supports the BITTEN system's core functionality while maintaining security, performance, and scalability for production deployment.