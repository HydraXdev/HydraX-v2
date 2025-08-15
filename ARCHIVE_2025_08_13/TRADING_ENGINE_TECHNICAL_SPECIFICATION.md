# BITTEN Trading Engine Technical Specification
## Version 3.0.0 - Self-Optimizing 10-Pair System

### Executive Summary
The BITTEN trading engine is a sophisticated algorithmic trading system featuring a self-optimizing TCS (Tactical Confidence Score) system, predictive movement detection, and advanced risk management. This specification covers the technical implementation of all trading-related components for the new 10-pair system with self-learning capabilities.

---

## 1. TCS (Tactical Confidence Score) System Specifications

### 1.1 Core Algorithm
The TCS system evaluates trade quality across multiple dimensions using a weighted scoring model:

```
TCS Score = min(Structure + Timeframe + Momentum + Volatility + Session + Liquidity + RiskReward + AI_Bonus, 100)
```

### 1.2 Component Breakdown

#### 1.2.1 Market Structure Analysis (20 points max)
- **Trend Clarity**: 0-8 points based on trend strength (0.7+ = 8pts, 0.5-0.7 = 6pts, 0.3-0.5 = 3pts)
- **Support/Resistance Quality**: 0-7 points (0.8+ = 7pts, 0.6-0.8 = 5pts, 0.4-0.6 = 3pts)
- **Pattern Completion**: 5 points for complete patterns, 3 points for forming patterns

#### 1.2.2 Timeframe Alignment (15 points max)
- **M15**: 2 points weight
- **H1**: 4 points weight
- **H4**: 5 points weight
- **D1**: 4 points weight
- **Perfect Alignment Bonus**: 15 points for all timeframes aligned

#### 1.2.3 Momentum Assessment (15 points max)
- **RSI Momentum**: 5 points for optimal zones (25-35, 65-75), 3 points for good zones
- **MACD Alignment**: 5 points for alignment, 3 points for divergence
- **Volume Confirmation**: 5 points for 1.5x+ volume, 3 points for 1.2x+

#### 1.2.4 Volatility Analysis (10 points max)
- **ATR Range**: 5 points for 15-50 ATR, 3 points for 10-15 or 50-80
- **Spread Conditions**: 3 points for <1.5 spread ratio, 1 point for <2.0
- **Volatility Stability**: 2 points for stable conditions

#### 1.2.5 Session Weighting (10 points max)
- **London**: 10 points
- **New York**: 9 points
- **Overlap**: 8 points
- **Tokyo**: 6 points
- **Sydney**: 5 points
- **Dead Zone**: 2 points

#### 1.2.6 Liquidity Patterns (10 points max)
- **Liquidity Grab**: 5 points
- **Stop Hunt**: 3 points
- **Institutional Levels**: 2 points

#### 1.2.7 Risk/Reward Quality (10 points max)
- **4.0+ RR**: 10 points
- **3.5-4.0 RR**: 9 points
- **3.0-3.5 RR**: 8 points
- **2.5-3.0 RR**: 6 points
- **2.0-2.5 RR**: 4 points
- **1.5-2.0 RR**: 2 points

#### 1.2.8 AI Sentiment Bonus (10 points max)
- Additional scoring from AI analysis (capped at 10 points)

### 1.3 Trade Classification System

#### 1.3.1 Classification Thresholds
- **Hammer Elite (94%+ TCS, 3.5+ RR)**: Top 1% trades with momentum >0.8, structure >0.9
- **Hammer (94%+ TCS, 3.5+ RR)**: Elite setups
- **Shadow Strike Premium (84-93% TCS, 3.0+ RR)**: High probability with premium RR
- **Shadow Strike (84-93% TCS)**: High probability trades
- **Scalp Session (75-83% TCS, London/NY)**: Session-optimized scalps
- **Scalp (75-83% TCS)**: Quick opportunities
- **Watchlist (65-74% TCS)**: Monitor only
- **None (<65% TCS)**: No trade

---

## 2. Self-Optimizing Algorithm Details

### 2.1 Optimization Configuration
```python
TCSOptimizationConfig:
    target_signals_per_day: 65
    min_tcs_threshold: 70.0
    max_tcs_threshold: 78.0
    target_win_rate: 0.85
    min_win_rate: 0.82
    adjustment_interval_hours: 4
    lookback_hours: 24
    signal_volume_tolerance: 0.15  # ±15%
```

### 2.2 Adjustment Algorithm
```python
def get_optimal_tcs_threshold(market_condition):
    # 1. Signal Volume Adjustment
    if signal_ratio < 0.85:
        adjustment -= min(2.0, (1.0 - signal_ratio) * 5.0)
    elif signal_ratio > 1.15:
        adjustment += min(2.0, (signal_ratio - 1.0) * 3.0)
    
    # 2. Win Rate Adjustment
    if win_rate < 0.82:
        adjustment += min(3.0, (0.82 - win_rate) * 10.0)
    elif win_rate > 0.85:
        adjustment -= min(1.0, (win_rate - 0.85) * 5.0)
    
    # 3. Market Condition Adjustments
    if volatility == "HIGH":
        adjustment += 1.0
    elif volatility == "LOW":
        adjustment -= 1.0
    
    if news_impact > 0.7:
        adjustment += 1.5
    
    return clamp(current_threshold + adjustment, 70.0, 78.0)
```

### 2.3 Performance Tracking Database Schema
```sql
CREATE TABLE tcs_adjustments (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    old_threshold REAL,
    new_threshold REAL,
    reason TEXT,
    signal_count_24h INTEGER,
    win_rate_24h REAL,
    market_condition TEXT,
    volatility_level TEXT
);

CREATE TABLE signal_performance (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    pair TEXT,
    tcs_score REAL,
    direction TEXT,
    result TEXT,
    pips_gained REAL,
    hold_time_minutes INTEGER,
    market_condition TEXT
);
```

---

## 3. Predictive Movement Detection System

### 3.1 Pre-Movement Signal Detection
The system uses multiple indicators to predict market movement before it occurs:

#### 3.1.1 Detection Criteria
- **Momentum Buildup**: Threshold 0.7+
- **Volume Spike**: Threshold 1.5x+ normal volume
- **Order Flow Pressure**: Threshold 0.6+
- **Support/Resistance Proximity**: Threshold 0.7+
- **Session Transition**: Time-based scoring

#### 3.1.2 Confidence Calculation
```python
def detect_pre_movement_signals(pair_data):
    confidence_factors = []
    
    # Requires minimum 2 factors for signal
    if len(confidence_factors) >= 2:
        total_confidence = sum(scores) / len(confidence_factors)
        return True, total_confidence, reasons
    
    return False, 0.0, "No pre-movement signals"
```

#### 3.1.3 Session Transition Scoring
- **London Open (3 AM EST)**: 0.8 confidence
- **NY Open (8 AM EST)**: 0.9 confidence
- **Asian Close (3 AM EST)**: 0.7 confidence
- **Other times**: 0.3 confidence

---

## 4. Signal Generation Pipeline

### 4.1 Signal Fusion Architecture
The system uses a multi-source intelligence fusion approach:

#### 4.1.1 Confidence Tiers
- **SNIPER (95%+)**: Elite signals with maximum confidence
- **PRECISION (85-94%)**: High-quality signals
- **RAPID (75-84%)**: Fast opportunities
- **TRAINING (65-74%)**: Educational signals

#### 4.1.2 Signal Flow Process
```python
async def process_signal_flow():
    # 1. Collect intelligence from multiple sources
    intelligence = await intelligence_aggregator.collect_intelligence(pair)
    
    # 2. Apply fusion scoring
    fused_signal = signal_fusion_engine.fuse_signals(intelligence)
    
    # 3. Apply live filters
    if live_filter.should_take_signal(fused_signal):
        # 4. Distribute by tier
        await distribute_by_tier(fused_signal)
```

#### 4.1.3 Quality Optimization
- **Performance Tracking**: Real-time win rate monitoring
- **Source Weighting**: Dynamic adjustment based on performance
- **Threshold Adaptation**: Automatic adjustment based on market conditions

---

## 5. Fire Modes and Tier Restrictions

### 5.1 Fire Mode Definitions
```python
class FireMode(Enum):
    SINGLE_SHOT = "single_shot"      # Standard mode
    CHAINGUN = "chaingun"            # Sequential 4-shot system
    AUTO_FIRE = "auto_fire"          # Automated execution
    SEMI_AUTO = "semi_auto"          # Manual with lower TCS
    STEALTH = "stealth"              # Anti-detection mode
    MIDNIGHT_HAMMER = "midnight_hammer" # Community event
```

### 5.2 Tier Configurations
```python
TIER_CONFIGS = {
    PRESS_PASS: {
        price: 0,
        daily_shots: 1,
        min_tcs: 60,
        modes: [SINGLE_SHOT]
    },
    NIBBLER: {
        price: 39,
        daily_shots: 6,
        min_tcs: 70,
        modes: [SINGLE_SHOT]
    },
    FANG: {
        price: 89,
        daily_shots: 10,
        min_tcs: 85,
        modes: [SINGLE_SHOT, CHAINGUN]
    },
    COMMANDER: {
        price: 139,
        daily_shots: 12,
        min_tcs: 91,
        modes: [SINGLE_SHOT, CHAINGUN, AUTO_FIRE]
    }: {
        price: 188,
        daily_shots: 9999,
        min_tcs: 91,
        modes: [ALL_MODES]
    }
}
```

### 5.3 Chaingun System
The Chaingun mode implements a progressive risk system:
- **Shot 1**: 2% risk, 85% TCS required
- **Shot 2**: 4% risk, 87% TCS required
- **Shot 3**: 8% risk, 89% TCS required
- **Shot 4**: 16% risk, 91% TCS required

Maximum 2 sequences per day with 4-hour time limit.

### 5.4 Pair-Specific TCS Requirements
- **Core Pairs**: Use tier defaults
- **Extra Pairs**: Require 85% minimum TCS for enhanced safety

---

## 6. Risk Management System

### 6.1 Multi-Layer Risk Architecture

#### 6.1.1 Daily Loss Limits (Updated)
- **NIBBLER**: -6% daily limit
- **FANG**: -8.5% daily limit
- **COMMANDER**: -8.5% daily limit
- ****: -8.5% daily limit

#### 6.1.2 Trading States
```python
class TradingState(Enum):
    NORMAL = "normal"
    TILT_WARNING = "tilt_warning"
    TILT_LOCKOUT = "tilt_lockout"
    MEDIC_MODE = "medic_mode"
    WEEKEND_LIMITED = "weekend_limited"
    NEWS_LOCKOUT = "news_lockout"
    DAILY_LIMIT_HIT = "daily_limit_hit"
```

#### 6.1.3 Tilt Detection Algorithm
- **Threshold**: 3 consecutive losses
- **Tilt Strikes**: Maximum 2 strikes before lockout
- **Recovery**: Requires 2 consecutive wins
- **Lockout Duration**: 1 hour after second strike

#### 6.1.4 Medic Mode
- **Trigger**: -5% daily loss
- **Risk Reduction**: 50% of normal risk
- **Position Limit**: 1 concurrent position
- **Duration**: Until next trading day

### 6.2 Position Sizing Algorithm
```python
def calculate_position_size(account, profile, symbol, entry, sl, mode):
    # 1. Check trading restrictions
    if not can_trade:
        return blocked_result
    
    # 2. Calculate pip risk
    pip_risk = abs(entry - sl) / pip_value
    
    # 3. Get risk percentage from controller
    risk_percent = get_user_risk_percent(user_id, tier)
    
    # 4. Calculate position size
    risk_amount = account.balance * (risk_percent / 100)
    lot_size = risk_amount / (pip_risk * pip_value_per_lot)
    
    # 5. Apply constraints
    lot_size = clamp(lot_size, min_lot, max_lot)
    
    # 6. Hard lock validation
    if actual_risk > max_safe_risk:
        lot_size = recalculate_safe_size()
    
    return position_details
```

### 6.3 XP-Based Trade Management Features
- **Breakeven Shield (100 XP)**: Move SL to entry at 50% target
- **Profit Lock (500 XP)**: Lock small profit on favorable moves
- **Hunter Protocol (1000 XP)**: Trailing stop system
- **Tactical Harvest (2000 XP)**: Partial profit taking
- **Marathon Mode (5000 XP)**: 75% close, 25% runner
- **Free Money Glitch (15000 XP)**: Zero-risk runners
- **Leroy Jenkins (20000 XP)**: Ultra-aggressive management
- **Apex Predator (50000 XP)**: Full AI optimization

---

## 7. Stealth Protocol Implementation

### 7.1 Stealth Levels
```python
class StealthLevel(Enum):
    OFF = "off"
    LOW = "low"           # 1-3% variations
    MEDIUM = "medium"     # 3-7% variations
    HIGH = "high"         # 5-10% variations
    GHOST = "ghost"       # 7-15% variations
```

### 7.2 Stealth Components

#### 7.2.1 Entry Delay
- **Range**: 1-12 seconds base
- **Level Multipliers**: LOW=0.5x, MEDIUM=1.0x, HIGH=1.5x, GHOST=2.0x
- **Cryptographic Randomization**: Uses `secrets.randbelow()` for unpredictability

#### 7.2.2 Lot Size Jitter
- **Variation Ranges**: 
  - LOW: ±1-3%
  - MEDIUM: ±3-7%
  - HIGH: ±5-10%
  - GHOST: ±7-15%
- **Application**: Random increase/decrease with proper rounding

#### 7.2.3 TP/SL Offset
- **Pip Offsets**: 1-3 pips base with level multipliers
- **Direction**: Randomly positive or negative
- **Pip Value Calculation**: 0.0001 for non-JPY, 0.01 for JPY pairs

#### 7.2.4 Ghost Skip
- **Skip Rates**:
  - LOW: 5% skip rate
  - MEDIUM: 16.7% skip rate
  - HIGH: 25% skip rate
  - GHOST: 33% skip rate

#### 7.2.5 Volume Caps
- **Per-Asset Limit**: 3 concurrent trades
- **Total Limit**: 10 concurrent trades
- **Tracking**: Real-time active trade monitoring

#### 7.2.6 Execution Shuffle
- **Queue Randomization**: Secure random shuffle algorithm
- **Inter-Trade Delays**: 0.5-2.0 seconds between trades
- **Order Preservation**: Maintains essential execution order

### 7.3 Stealth Logging
```python
@dataclass
class StealthAction:
    timestamp: datetime
    action_type: str
    original_value: Any
    modified_value: Any
    level: StealthLevel
    details: Dict[str, Any]
```

---

## 8. Order Execution Flow

### 8.1 Execution Pipeline

#### 8.1.1 Pre-Execution Validation
```python
def validate_execution():
    # 1. Signal validity check
    if signal_expired():
        return reject("Signal expired")
    
    # 2. Tier access verification
    if not has_tier_access():
        return reject("Insufficient tier access")
    
    # 3. Trading restrictions check
    if not can_trade():
        return reject("Trading restricted")
    
    # 4. Hard lock validation
    if exceeds_risk_limits():
        return reject("Risk limits exceeded")
    
    return approve()
```

#### 8.1.2 Execution Process
```python
async def execute_trade():
    # 1. Apply stealth protocol
    stealth_params = stealth_protocol.apply_full_stealth(trade_params)
    
    if stealth_params.get('skip_trade'):
        return skip_result
    
    # 2. Calculate position size
    position_size = risk_calculator.calculate_position_size(...)
    
    # 3. Set up trade management
    management_plan = create_trade_management_plan(...)
    
    # 4. Execute with MT5 bridge
    result = mt5_adapter.execute_trade_with_risk(...)
    
    # 5. Send confirmation
    await send_execution_confirmation(...)
    
    return result
```

### 8.2 Multi-Level Take Profit System
For COMMANDER tier on high-confidence signals:
- **TP1**: 50% of distance (30% position close)
- **TP2**: 80% of distance (30% position close)
- **TP3**: Full distance (40% position close)

### 8.3 Trade Metadata System
```python
comment_format = "BITTEN_{tier}_{signal_tier}_{confidence}"
# Example: "BITTEN_commander_sniper_94"
```

---

## 9. Technical Parameters Summary

### 9.1 Core Trading Pairs (10 pairs)
```yaml
Core Pairs (5):
  - EURUSD: pip_value=0.0001, contract_size=100000
  - GBPUSD: pip_value=0.0001, contract_size=100000
  - USDJPY: pip_value=0.01, contract_size=100000
  - USDCAD: pip_value=0.0001, contract_size=100000
  - GBPJPY: pip_value=0.01, contract_size=100000

Extra Pairs (5):
  - AUDUSD: pip_value=0.0001, min_tcs=85%
  - NZDUSD: pip_value=0.0001, min_tcs=85%
  - EURJPY: pip_value=0.01, min_tcs=85%
  - EURGBP: pip_value=0.0001, min_tcs=85%
  - USDCHF: pip_value=0.0001, min_tcs=85%
```

### 9.2 System Performance Targets
- **Daily Signal Volume**: 65 signals/day
- **Target Win Rate**: 85%
- **Minimum Win Rate**: 82%
- **Signal Distribution**: 30-second monitoring cycles
- **TCS Optimization**: 4-hour adjustment intervals

### 9.3 Database Performance Requirements
- **Signal Response Time**: <100ms
- **TCS Calculation**: <50ms
- **Risk Validation**: <25ms
- **Stealth Processing**: <200ms

---

## 10. Implementation Notes

### 10.1 Security Considerations
- All random operations use cryptographically secure `secrets` module
- Trade IDs use secure random tokens
- Input validation on all user inputs
- Rate limiting on API endpoints

### 10.2 Scalability Features
- Asynchronous processing for all I/O operations
- Database connection pooling
- Caching for frequently accessed data
- Horizontal scaling support for multiple instances

### 10.3 Monitoring and Alerting
- Real-time performance metrics
- Automated system health checks
- Critical alert notifications
- Performance degradation detection

---

## 11. Configuration Files

### 11.1 Trading Pairs Configuration
Location: `/root/HydraX-v2/config/trading_pairs.yml`
- Complete pair specifications
- Session timing definitions
- Strategy assignments
- Heat map tracking configuration

### 11.2 TCS Optimization Settings
Location: `/root/HydraX-v2/data/tcs_optimization.db`
- Real-time threshold tracking
- Performance history
- Adjustment logging

### 11.3 Stealth Protocol Settings
Location: `/root/HydraX-v2/config/stealth_settings.yml`
- Level configurations
- Randomization parameters
- Volume cap settings

---

This technical specification provides comprehensive coverage of the BITTEN trading engine's architecture, algorithms, and implementation details. The system is designed for high-frequency, low-latency trading with sophisticated risk management and anti-detection capabilities.