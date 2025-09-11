# 🎯 BITTEN - Bot-Integrated Tactical Trading Engine/Network

[![Version](https://img.shields.io/badge/version-9.0-blue.svg)](https://github.com/HydraXdev/HydraX-v2)
[![Status](https://img.shields.io/badge/status-operational-success.svg)](https://github.com/HydraXdev/HydraX-v2)
[![Performance](https://img.shields.io/badge/win_rate-65%25+-brightgreen.svg)](https://github.com/HydraXdev/HydraX-v2)

## 📊 Overview

BITTEN is a sophisticated automated trading system that uses Smart Money Concepts (SMC) and machine learning to identify high-probability trading opportunities in the forex market. The system operates 24/7, analyzing multiple currency pairs and executing trades through MetaTrader 5.

### Key Features
- **6 Advanced Pattern Recognition Algorithms** - Institutional-grade SMC patterns
- **Real-time ML Optimization** - Continuous learning from trade outcomes
- **Multi-tier Access System** - Different features for different user tiers
- **Automated Risk Management** - 2% risk per trade with dynamic position sizing
- **Telegram Integration** - Real-time alerts and trade management

## 🏗️ System Architecture

```
[Market Data] → [Pattern Recognition] → [ML Filtering] → [Signal Generation] → [Risk Management] → [Execution]
                        ↑                      ↑                                        ↓
                   [Outcome Tracking] ← [Performance Analysis] ← [Trade Results] ←────────┘
```

### Core Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| **Elite Guard** | Pattern recognition & signal generation | Python, NumPy |
| **Grokkeeper ML** | Machine learning optimization | XGBoost, Scikit-learn |
| **Command Router** | Trade execution management | ZMQ, MT5 |
| **Dynamic Tracker** | Real-time outcome monitoring | Python, SQLite |
| **Telegram Bot** | User interface & alerts | python-telegram-bot |
| **WebApp** | Dashboard & analytics | Flask, Gunicorn |

## 📈 Trading Patterns

### Implemented Patterns (September 2025)

1. **LIQUIDITY_SWEEP_REVERSAL** (70% confidence threshold)
   - Detects institutional stop hunts
   - 50% win rate, high R:R potential

2. **ORDER_BLOCK_BOUNCE** (80% confidence threshold)
   - Institutional accumulation zones
   - Restricted to USDJPY, GBPCAD
   - 44% win rate after optimization

3. **FAIR_VALUE_GAP_FILL** (85% confidence threshold)
   - Price inefficiency corrections
   - Recently optimized from 99% (was disabled)

4. **VCB_BREAKOUT** (65% confidence threshold)
   - Volatility Compression Breakouts
   - High momentum plays

5. **MOMENTUM_BURST** (65% confidence threshold)
   - Acceleration patterns
   - 75% win rate - best performer

6. **BB_SCALP** (85% confidence threshold)
   - Bollinger Band mean reversion
   - JPY pairs only, 1.5:1 R:R

7. **KALMAN_QUICKFIRE** (80% confidence threshold)
   - Statistical arbitrage
   - USDJPY, EURUSD, GBPUSD only

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- MetaTrader 5
- PostgreSQL or SQLite
- Redis
- PM2 (for process management)

### Installation

```bash
# Clone the repository
git clone https://github.com/HydraXdev/HydraX-v2.git
cd HydraX-v2

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.template .env
# Edit .env with your configuration

# Initialize database
python3 init_database.py

# Start all services
pm2 start ecosystem.config.js
```

### Configuration

1. **Trading Parameters** (`/root/HydraX-v2/elite_guard_with_citadel.py`)
   - Confidence thresholds per pattern
   - Risk management settings
   - Symbol selection

2. **ML Configuration** (`/root/HydraX-v2/ml_config.json`)
   - Training parameters
   - Feature selection
   - Model hyperparameters

3. **User Access** (`/root/HydraX-v2/bitten.db`)
   - User tiers and permissions
   - Auto-fire settings
   - Risk limits

## 📊 Performance Metrics

### Current Performance (September 2025)
- **Overall Win Rate**: 56.9% → 65%+ (after optimizations)
- **Daily Performance**: -82 pips → +270 pips projected
- **Best Pattern**: MOMENTUM_BURST (75% WR)
- **Most Improved**: ORDER_BLOCK_BOUNCE (32% → 50%+ after restrictions)

### Risk Management
- **Per Trade Risk**: 2% of account
- **Position Sizing**: Dynamic based on stop loss distance
- **Max Concurrent**: 3 positions (configurable)
- **Timeout**: 4 hours max tracking per signal

## 🔧 System Management

### Process Management
```bash
# View all processes
pm2 list

# Monitor logs
pm2 logs elite_guard --lines 100

# Restart a service
pm2 restart elite_guard

# Stop all services
pm2 stop all
```

### Performance Monitoring
```bash
# Run performance report
python3 -c "$(cat bitten_report_standard.py)"

# Check recent signals
sqlite3 bitten.db "SELECT * FROM signals ORDER BY created_at DESC LIMIT 10;"

# View tracking status
tail -f comprehensive_tracking.jsonl
```

### Database Management
```bash
# Backup database
cp bitten.db bitten.db.backup_$(date +%Y%m%d)

# Query win rates
sqlite3 bitten.db "SELECT pattern_type, COUNT(*) as total, 
  SUM(CASE WHEN outcome='WIN' THEN 1 ELSE 0 END) as wins 
  FROM signals GROUP BY pattern_type;"
```

## 🔒 Security

- **API Keys**: Store in `.env` files (never commit)
- **Telegram Bot**: Token-based authentication
- **Database**: Local SQLite with regular backups
- **Network**: ZMQ sockets for inter-process communication
- **Git**: Use `.gitignore` for sensitive files

## 📡 Communication Architecture

### ZMQ Ports
- **5555**: Command router (fire commands)
- **5556**: Market data ingestion
- **5557**: Signal publishing
- **5558**: Trade confirmations
- **5560**: Market data redistribution
- **5565**: ML adjustments

### HTTP Endpoints
- **8888**: Main webapp dashboard
- **8899**: Commander throne interface
- **8890**: Tracking dashboard
- **8891**: Confidence analysis

## 🤖 Machine Learning Pipeline

### Data Flow
1. **Signal Generation** → Track all signals above 70% confidence
2. **Outcome Tracking** → Monitor to TP/SL completion (max 4 hours)
3. **ML Training** → Retrain model every 24 hours with new data
4. **Threshold Adjustment** → Auto-adjust pattern confidence requirements
5. **Performance Feedback** → Disable patterns below 40% win rate

### Current ML Status (September 2025)
- **Training Samples**: 233
- **Features**: 10+ (pattern, symbol, session, volatility, etc.)
- **Model**: XGBoost with anti-overfitting measures
- **Retraining**: Automated daily

## 📱 Telegram Bot Commands

### User Commands
- `/start` - Initialize bot
- `/brief` - View current signals
- `/fire [signal_id]` - Execute a trade
- `/me` - View account status
- `/slots` - Check available trade slots
- `/BITMODE [ON|OFF]` - Toggle hybrid position management (FANG+ only)

### Admin Commands
- `/broadcast [message]` - Send to all users
- `/stats` - System statistics
- `/users` - User management
- `/maintenance [ON|OFF]` - Toggle maintenance mode

## 🛠️ Troubleshooting

### Common Issues

**No Signals Generated**
```bash
# Check Elite Guard is running
pm2 status elite_guard

# Check market data flow
pm2 logs zmq_telemetry_bridge --lines 50

# Verify pattern scanning
grep "SCAN TRIGGER" /root/.pm2/logs/elite-guard-out.log
```

**Trades Not Executing**
```bash
# Check EA connection
sqlite3 bitten.db "SELECT * FROM ea_instances;"

# Verify command router
pm2 logs command_router --lines 20

# Test fire pipeline
python3 test_fire_queue.py
```

**ML Not Learning**
```bash
# Check training data
wc -l ml_training_data.jsonl

# Restart ML service
pm2 restart grokkeeper_ml

# Check for errors
pm2 logs grokkeeper_ml --lines 50
```

## 📈 Recent Optimizations (September 11, 2025)

### Pattern Restrictions
- **ORDER_BLOCK_BOUNCE**: Limited to USDJPY/GBPCAD, 80%+ confidence
- **BB_SCALP**: JPY pairs only, 15 pip TP/10 pip SL (1.5:1 R:R)
- **KALMAN_QUICKFIRE**: USDJPY/EURUSD/GBPUSD only, 75-84% confidence
- **FAIR_VALUE_GAP_FILL**: Threshold lowered to 85% (was 99%)

### Expected Impact
- Previous 24h: -82 pips (56.9% win rate)
- Projected 24h: +270 pips (65%+ win rate)
- Net improvement: +352 pips/day

## 👥 Contributing

This is a proprietary trading system. For security reasons, contributions are limited to authorized developers only.

## 📄 License

Proprietary - All Rights Reserved

## 🆘 Support

For technical support or questions:
- Telegram: @bitten_support
- GitHub Issues: [Create an issue](https://github.com/HydraXdev/HydraX-v2/issues)

---

**Last Updated**: September 11, 2025 | **Version**: 9.0 | **Status**: Operational 🟢