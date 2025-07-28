# 🎯 BITTEN COMMUNICATION TEST GUIDE

## Overview
This guide tests the complete communication flow between:
1. **PowerShell Agent** → Creates fire signals
2. **MT5 EA** → Executes trades & streams market data
3. **Market Data Receiver** → HTTP endpoint for tick data
4. **VENOM v7** → Consumes real market data (NO FAKE DATA)
5. **Container Bridge** → Manages fire.txt protocol

---

## 🔧 Pre-Test Checklist

### Windows VPS (Master Clone)
```powershell
# 1. Check agent service is running
Get-Service BiTTenDualAgent

# 2. Verify EA is compiled
Test-Path "C:\Program Files\MetaTrader 5\MQL5\Experts\BITTENBridge_TradeExecutor.ex5"

# 3. Check BITTEN directory exists
Test-Path "C:\Program Files\MetaTrader 5\MQL5\Files\BITTEN\"

# 4. Verify agent configuration
$config = Get-Content "C:\BiTTen\Agent\Config\agent_config.json" | ConvertFrom-Json
$config.CloneMode  # Should be True for clones
```

### Linux Server (HydraX Backend)
```bash
# 1. Check market data receiver is running
curl http://localhost:8001/market-data/health

# 2. Verify VENOM is using real data only
grep -n "generate_realistic_market_data" /root/HydraX-v2/apex_venom_v7_real_data_only.py
# Should show RuntimeError

# 3. Check container bridge adapter exists
ls -la /root/HydraX-v2/container_fire_adapter.py
```

---

## 📡 Test 1: Market Data Streaming (EA → HTTP)

### Step 1: Verify EA is Streaming
In MT5, check the Experts tab. You should see:
```
BITTENBridge v2: Streaming market data...
HTTP Response: 200
```

### Step 2: Check Market Data Receiver
```bash
# On Linux server
curl http://localhost:8001/market-data/all | jq '.'
```

Expected output:
```json
{
  "symbols": {
    "EURUSD": {
      "bid": 1.08765,
      "ask": 1.08778,
      "spread": 1.3,
      "volume": 0,
      "last_update": "2025-01-26T10:15:30",
      "is_stale": false,
      "source_count": 1
    },
    // ... other 14 pairs
  },
  "active_symbols": 15,
  "total_symbols": 15
}
```

### Step 3: Test Individual Symbol
```bash
curl http://localhost:8001/market-data/EURUSD | jq '.'
```

### Step 4: Verify NO XAUUSD
```bash
# This should return error
curl http://localhost:8001/market-data/XAUUSD
# Expected: {"error": "Invalid symbol: XAUUSD"}
```

---

## 🔥 Test 2: Fire Signal Execution (Agent → EA)

### Step 1: Create Fire Signal via PowerShell Agent
```powershell
# On Windows VPS
Import-Module "C:\BiTTen\Agent\Modules\EADeployment.psm1"
$eaManager = New-Object EADeploymentManager

# Create test signal
$signal = @{
    symbol = "EURUSD"
    type = "buy"
    lot = 0.01
    sl = 50
    tp = 100
    comment = "BITTEN_TEST"
}

$eaManager.CreateFireSignal($signal)
```

### Step 2: Monitor Fire File
```powershell
# Watch fire.txt
Get-Content "C:\Program Files\MetaTrader 5\MQL5\Files\BITTEN\fire.txt" -Wait
```

### Step 3: Check Trade Result
```powershell
# After EA processes, check result
Get-Content "C:\Program Files\MetaTrader 5\MQL5\Files\BITTEN\trade_result.txt"
```

Expected format:
```json
{"status":"success","ticket":123456789,"symbol":"EURUSD","type":"buy","lot":0.01}
```

---

## 🧪 Test 3: VENOM Real Data Consumption

### Step 1: Test VENOM Data Access
```python
# On Linux server
cd /root/HydraX-v2
python3 -c "
from apex_venom_v7_real_data_only import ApexVenomV7RealDataOnly
engine = ApexVenomV7RealDataOnly()
status = engine.get_market_data_status()
print('Market Data Status:', status)
"
```

### Step 2: Validate Data Sources
```python
python3 -c "
from apex_venom_v7_real_data_only import ApexVenomV7RealDataOnly
engine = ApexVenomV7RealDataOnly()
validation = engine.validate_data_sources()
for symbol, valid in validation.items():
    print(f'{symbol}: {"✅" if valid else "❌"}')
"
```

### Step 3: Test XAUUSD Blocking
```python
python3 -c "
from apex_venom_v7_real_data_only import ApexVenomV7RealDataOnly
engine = ApexVenomV7RealDataOnly()
try:
    data = engine.get_real_mt5_data('XAUUSD')
    print('ERROR: XAUUSD not blocked!')
except Exception as e:
    print('✅ XAUUSD correctly blocked')
"
```

### Step 4: Verify NO Synthetic Data
```python
python3 -c "
from apex_venom_v7_real_data_only import ApexVenomV7RealDataOnly
from datetime import datetime
engine = ApexVenomV7RealDataOnly()
try:
    fake_data = engine.generate_realistic_market_data('EURUSD', datetime.now())
    print('ERROR: Synthetic data generation not blocked!')
except RuntimeError as e:
    print('✅ Synthetic data correctly blocked:', str(e))
"
```

---

## 🔄 Test 4: Full Integration Test

### Step 1: Start All Components
```bash
# 1. Ensure market data receiver is running
cd /root/HydraX-v2
python3 market_data_receiver.py &

# 2. Monitor incoming data
tail -f market_data_receiver.log
```

### Step 2: Generate VENOM Signal (with real data)
```python
# Only works if real data is flowing
python3 -c "
from apex_venom_v7_real_data_only import ApexVenomV7RealDataOnly
from datetime import datetime
engine = ApexVenomV7RealDataOnly()
signal = engine.generate_venom_signal('EURUSD', datetime.now())
if signal:
    print('✅ Signal generated:', signal['signal_id'])
else:
    print('❌ No signal (check if market data is flowing)')
"
```

### Step 3: Test Container Fire Adapter
```python
# Test with specific container
python3 -c "
from container_fire_adapter import ContainerFireAdapter
adapter = ContainerFireAdapter('bitten_engine_mt5')
status = adapter.check_ea_status()
print('EA Status:', status)
"
```

---

## 🐛 Troubleshooting

### No Market Data
1. Check MT5 is logged in and EA attached to charts
2. Verify WebRequest URL is allowed in MT5
3. Check firewall allows localhost:8001
4. Look for HTTP errors in MT5 Journal tab

### Fire Signals Not Executing
1. Verify EA shows smiley face on chart
2. Check fire.txt location is correct
3. Ensure no file permission issues
4. Look for errors in Experts tab

### VENOM Not Getting Data
1. Verify market_data_receiver.py is running
2. Check http://localhost:8001/market-data/health
3. Ensure MT5 EA is streaming (5-second intervals)
4. Check for stale data warnings

### PowerShell Agent Issues
```powershell
# Check agent logs
Get-Content "C:\BiTTen\Agent\Logs\*.log" -Tail 50

# Test EA detection
$eaManager = New-Object EADeploymentManager
$eaManager.DetectEA()

# Verify currency pairs
$eaManager.GetCurrencyPairs()
```

---

## ✅ Success Criteria

All tests pass when:
1. ✅ Market data streams from EA to HTTP endpoint (15 pairs, NO XAUUSD)
2. ✅ Fire signals execute trades via fire.txt protocol
3. ✅ VENOM consumes ONLY real market data (no synthetic generation)
4. ✅ PowerShell agent manages EA without recompilation
5. ✅ Container adapter communicates with MT5 containers
6. ✅ All XAUUSD attempts are blocked at every level

---

## 📊 Performance Benchmarks

- Market data update frequency: Every 5 seconds
- Fire signal execution time: < 2 seconds
- VENOM data validation: < 100ms
- Agent health check interval: 60 seconds
- Stale data threshold: 30 seconds

---

## 🚀 Next Steps

After all tests pass:
1. Create master container snapshot
2. Test clone deployment with credential injection
3. Verify headless operation (no GUI needed)
4. Scale to multiple user containers
5. Monitor system performance

---

**Remember**: This master setup will be cloned 5000+ times. Ensure everything works perfectly before creating the golden image!