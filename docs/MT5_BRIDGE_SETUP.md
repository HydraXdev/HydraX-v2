# MT5 Bridge Setup Guide

## Overview

The BITTEN MT5 Bridge provides file-based communication between the Python BITTEN system and MetaTrader 5 through the `BITTENBridge_HYBRID_v1.2_PRODUCTION.mq5` Expert Advisor.

## Architecture

```
Python BITTEN System
    ↓
MT5BridgeAdapter (mt5_bridge_adapter.py)
    ↓
File System (CSV/JSON files)
    ↓
BITTENBridge EA (MT5)
    ↓
MetaTrader 5 Trading
```

## Installation Steps

### 1. Install the EA in MT5

1. Copy `BITTENBridge_HYBRID_v1.2_PRODUCTION.mq5` to your MT5 Experts folder
2. Open MT5 and compile the EA (F7)
3. Attach the EA to any chart (preferably a major pair like EURUSD)
4. Configure EA settings:
   - Allow automated trading
   - Allow DLL imports (if required by your broker)
   - Check file permissions

### 2. Configure Python Environment

Set the following environment variables:

```bash
# Enable MT5 bridge
export USE_MT5_BRIDGE=true

# Optional: Set custom MT5 files path
export MT5_FILES_PATH="/path/to/MT5/MQL5/Files"

# Disable HTTP bridge (optional)
export USE_LIVE_BRIDGE=false
```

### 3. File Locations

The bridge uses three files for communication:

- **bitten_instructions.txt**: Trade instructions (Python → MT5)
- **bitten_results.txt**: Trade execution results (MT5 → Python)
- **bitten_status.txt**: EA status and heartbeat (MT5 → Python)

Default locations:
- Windows: `C:\Users\[Username]\AppData\Roaming\MetaQuotes\Terminal\[ID]\MQL5\Files\`
- Local fallback: `./mt5_files/`

## Usage

### Basic Trade Execution

```python
from bitten_core.fire_router import FireRouter, TradeRequest, TradeDirection

# Initialize router with MT5 bridge
router = FireRouter()

# Create trade request
request = TradeRequest(
    user_id=123456,
    symbol="XAUUSD",
    direction=TradeDirection.BUY,
    volume=0.01,
    stop_loss=1950.00,
    take_profit=1970.00,
    tcs_score=85
)

# Execute trade
result = router.execute_trade(request)
print(f"Trade result: {result}")
```

### Direct Adapter Usage

```python
from bitten_core.mt5_bridge_adapter import get_bridge_adapter

# Get adapter instance
adapter = get_bridge_adapter()

# Execute trade directly
result = adapter.execute_trade(
    symbol="EURUSD",
    direction="sell",
    volume=0.1,
    stop_loss=1.1100,
    take_profit=1.0900
)

# Check status
status = adapter.get_status()
print(f"MT5 Status: {status}")
```

## File Formats

### Instruction File (CSV)
```
ID,SYMBOL,TYPE,LOT,PRICE,TP,SL
T1234567890,XAUUSD,BUY,0.01,0,1970.00,1950.00
```

### Result File (JSON)
```json
{
  "id": "T1234567890",
  "status": "success",
  "ticket": 12345678,
  "message": "Order executed",
  "timestamp": "2025-01-05 12:34:56",
  "account": {
    "balance": 10000.00,
    "equity": 10050.00,
    "margin": 100.00,
    "free_margin": 9950.00
  }
}
```

### Status File (JSON)
```json
{
  "type": "heartbeat",
  "message": "Bridge active",
  "timestamp": "2025-01-05 12:34:56",
  "connected": true,
  "positions": 2,
  "orders": 0
}
```

## Testing

Run the test suite:

```bash
python test_mt5_bridge.py
```

This will test:
1. File communication
2. Bridge adapter functionality
3. Fire router integration

## Troubleshooting

### Common Issues

1. **"Cannot open instruction file"**
   - Check MT5 file permissions
   - Verify the files path is correct
   - Ensure MT5 is running with admin privileges

2. **"Trade timeout"**
   - Check if EA is attached and running
   - Verify automated trading is enabled
   - Check MT5 journal for errors

3. **"Bridge not connected"**
   - Wait for initial heartbeat (5 seconds)
   - Check status file for error messages
   - Verify EA parameters match Python config

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check EA logs in MT5:
- View → Terminal → Experts tab
- View → Terminal → Journal tab

## Performance Notes

- File check interval: 100ms (configurable)
- Trade timeout: 30 seconds
- Heartbeat interval: 5 seconds
- Maximum concurrent trades: Limited by broker

## Security Considerations

1. Files are stored locally (no network transmission)
2. Trade IDs are unique timestamps
3. No sensitive data in log files
4. File permissions should be restricted

## Integration with BITTEN Features

The MT5 bridge fully supports:
- All fire modes (SINGLE_SHOT, BURST, etc.)
- Tier-based execution
- TCS score integration
- Risk management rules
- Position tracking
- Account monitoring

---

For additional support, check the BITTEN documentation or contact the development team.