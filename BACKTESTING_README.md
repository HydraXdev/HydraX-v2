# 🎯 BITTEN BACKTESTING SYSTEM

**Comprehensive signal quality validation and performance testing framework**

## 🚀 Quick Start

### 1. **Validate System**
```bash
python quick_backtest_validation.py
```
This runs a complete validation to ensure all components work.

### 2. **Setup Environment**
```bash
python setup_backtesting.py
```
Creates directories, databases, and sample data.

### 3. **Run Backtests**
```bash
python run_backtest.py
```
Interactive menu with 6 different backtesting scenarios.

---

## 📊 What It Tests

### **Signal Quality Validation**
- **TCS Accuracy**: Win rates at different TCS thresholds
- **Signal Volume**: Target 60-70 signals per day across 10 pairs
- **Classification**: ARCADE vs SNIPER signal types
- **Risk-Velocity Engine**: Mathematical classification accuracy

### **Trading System Validation**
- **Fire Mode Rules**: Tier-based access control
- **Risk Management**: Drawdown limits, position sizing
- **Execution Logic**: Realistic spreads, slippage, commissions
- **Performance Metrics**: Win rates, profit factors, Sharpe ratios

### **Tier Performance Testing**
- **NIBBLER**: 70%+ TCS, 6 shots/day
- **FANG**: 85%+ TCS, 10 shots/day
- **COMMANDER Manual**: 85%+ TCS, 12 shots/day
- **COMMANDER Auto**: 91%+ TCS, 12 shots/day
- **APEX**: 91%+ TCS, unlimited shots

---

## 🧪 Test Scenarios

### **1. Signal Quality Test**
**Purpose**: Validate TCS accuracy and signal generation
**Duration**: 1 month
**Validation**: 85%+ win rate at 85%+ TCS

```bash
# Expected Results:
✅ 75%+ overall win rate
✅ 85%+ win rate at 85% TCS
✅ 60-70 signals per day
✅ Proper ARCADE/SNIPER classification
```

### **2. Tier Performance Test**
**Purpose**: Compare performance across tier configurations
**Duration**: 1 month
**Validation**: Each tier meets performance expectations

```bash
# Expected Results:
NIBBLER:    75-80% win rate, 6 trades/day max
FANG:       80-85% win rate, 10 trades/day max
COMMANDER:  85-90% win rate, varies by mode
APEX:       85-90% win rate, unlimited
```

### **3. Stress Test**
**Purpose**: Extended testing across market conditions
**Duration**: 3 months, all 10 pairs
**Validation**: System resilience and consistency

```bash
# Expected Results:
✅ <15% maximum drawdown
✅ >1.5 profit factor
✅ <5 consecutive losses
✅ 75%+ sustained win rate
```

### **4. TCS Threshold Analysis**
**Purpose**: Find optimal TCS thresholds for different goals
**Validation**: Balance between signal volume and quality

```bash
# Optimization Targets:
Volume Goal:  60+ signals/day → Optimal TCS threshold
Quality Goal: 85%+ win rate → Required TCS threshold
```

### **5. Custom Backtest**
**Purpose**: User-defined parameters and date ranges
**Flexibility**: Test specific periods or market conditions

### **6. Full Test Suite**
**Purpose**: Run all tests sequentially
**Duration**: ~30 minutes
**Validation**: Complete system verification

---

## 📈 Performance Targets

| Metric | Target | Validation |
|--------|--------|------------|
| **Overall Win Rate** | 75%+ | ✅ Must achieve |
| **85%+ TCS Win Rate** | 85%+ | ✅ Must achieve |
| **Signal Volume** | 60-70/day | ✅ Must achieve |
| **Max Drawdown** | <15% | ✅ Must not exceed |
| **Profit Factor** | >1.5 | ✅ Must achieve |
| **Consecutive Losses** | <5 | ✅ Must not exceed |

---

## 🏗️ System Architecture

### **Core Components**

1. **HistoricalDataManager**
   - Loads/generates price data for backtesting
   - Manages bid/ask spreads by session
   - Handles news events and market conditions

2. **SignalReplayEngine**
   - Replays BITTEN signal generation algorithms
   - Uses actual TCS calculation methods
   - Applies ARCADE/SNIPER classification

3. **TradeSimulator**
   - Realistic trade execution with spreads/slippage
   - Proper TP/SL hit detection
   - Commission and cost calculations

4. **BacktestAnalyzer**
   - Comprehensive performance metrics
   - TCS accuracy analysis
   - Risk and drawdown calculations

5. **BittenBacktester**
   - Main orchestrator
   - Generates detailed reports
   - Integrates all components

### **Data Requirements**

```
Historical Data Structure:
├── Price Data (OHLC + Bid/Ask)
├── Session Information (Asian/London/NY)
├── Volume Data
├── News Events (Optional)
└── Market Conditions
```

### **Validation Flow**

```
1. Load Historical Data
2. Replay Signal Generation
3. Apply Tier Restrictions
4. Simulate Trade Execution
5. Calculate Performance Metrics
6. Validate Against Targets
7. Generate Reports
```

---

## 📋 Reports Generated

### **Performance Summary**
- Win rate, profit/loss, drawdown metrics
- Signal volume and frequency analysis
- Risk-adjusted returns and Sharpe ratio

### **TCS Accuracy Analysis**
- Win rates by TCS threshold (70%, 75%, 80%, 85%, 90%, 95%)
- Signal quality validation
- Threshold optimization recommendations

### **Trade Details**
- Individual trade results with entry/exit data
- Hold times and profit/loss breakdown
- Success/failure pattern analysis

### **Risk Analysis**
- Maximum drawdown periods
- Consecutive loss streaks
- Volatility and correlation analysis

---

## 🔧 Configuration Options

### **BacktestConfig Parameters**

```python
config = BacktestConfig(
    start_date="2024-01-01",        # Test start date
    end_date="2024-03-31",          # Test end date
    pairs=["EURUSD", "GBPUSD"],     # Currency pairs to test
    initial_balance=10000.0,        # Starting capital
    realistic_spreads=True,         # Use realistic spreads
    include_news_events=True,       # Include news filtering
    slippage_pips=0.5,             # Execution slippage
    commission_per_lot=7.0         # Trading commission
)
```

### **Customization Options**
- Test specific date ranges
- Select currency pairs
- Adjust risk parameters
- Modify TCS thresholds
- Include/exclude market conditions

---

## 🚨 Troubleshooting

### **Common Issues**

**"No historical data found"**
- Run `setup_backtesting.py` to create sample data
- Add real historical data to `/data/historical/historical_data.db`

**"Signal generation failed"**
- Ensure hybrid risk-velocity engine is working
- Check TCS calculation components
- Verify fire mode configurations

**"Trade simulation errors"**
- Check spread and commission settings
- Verify TP/SL level calculations
- Ensure realistic market conditions

### **Performance Issues**
- Reduce test duration for faster results
- Test fewer currency pairs
- Use sample data instead of full historical dataset

---

## 🎯 Expected Outcomes

### **System Validation**
Running the backtesting system will validate:

1. **Signal Quality**: TCS scores accurately predict outcomes
2. **Volume Targets**: System generates 60-70 signals/day
3. **Risk Management**: Drawdowns stay within acceptable limits
4. **Tier Logic**: Each tier performs according to specifications
5. **Fire Modes**: Access controls work correctly
6. **Performance**: System meets 85%+ win rate at high TCS

### **Business Validation**
- Confirms user tier pricing is justified
- Validates marketing claims (85%+ win rate)
- Identifies optimal TCS thresholds
- Demonstrates system edge over random trading

### **Technical Validation**
- Proves signal algorithms work as intended
- Confirms risk management is effective
- Validates trading execution logic
- Tests system under various market conditions

---

## 🚀 Next Steps After Backtesting

1. **Fix Issues**: Address any failed validations
2. **Optimize Thresholds**: Adjust TCS based on results
3. **Deploy Live**: Connect to real MT5 data
4. **Monitor Performance**: Compare live vs backtest results
5. **Iterate**: Continuously improve based on live data

---

**The backtesting system provides comprehensive validation that BITTEN delivers on its promises before risking real capital.**