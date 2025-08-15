# 📁 EA Location & MT5 Allocator Summary

## 🎯 EA File Location

### On Linux Server:
```
/root/HydraX-v2/BITTEN_Windows_Package/EA/BITTENBridge_v3_ENHANCED.mq5
```

### Where it needs to go on Windows (each MT5):
```
C:\MT5_Farm\Masters\[InstanceType]\MQL5\Experts\BITTENBridge_v3_ENHANCED.mq5
```

### After MT5 Installation:
1. **Copy EA** to each master's `MQL5\Experts\` folder
2. **Open MT5** terminal for that instance
3. **Press F4** to open MetaEditor
4. **Navigate** to Experts folder in Navigator panel
5. **Double-click** BITTENBridge_v3_ENHANCED.mq5
6. **Press F7** to compile (should see 0 errors, 0 warnings)
7. **EA appears** in Navigator under "Expert Advisors"
8. **Drag EA** to each of the 10 currency pair charts
9. **Configure**:
   - ✅ Allow live trading
   - ✅ Allow DLL imports (if needed)
   - Set magic number for this instance
   - Set risk percentage (2% default)

## 🎮 MT5 Instance Allocator

### Yes, we built an allocator\! (`mt5_instance_allocator.py`)

**What it does:**
- Automatically assigns MT5 instances to users based on tier
- Tracks which user has which instance
- Handles Press Pass 7-day recycling
- Manages broker preferences (regulated vs offshore)

### Allocation Logic:
```
PRESS_PASS → Generic_Demo (instant, no login needed)
NIBBLER/FANG → Forex_Demo (default) or Coinexx_Demo (if user prefers)
COMMANDER/→ Forex_Live (conservative) or Coinexx_Live (high leverage)
```

### Key Features:
- **Smart Assignment**: Finds next available instance
- **Preference Tracking**: Remembers user's broker preference
- **Automatic Recycling**: Press Pass instances cleaned after 7 days
- **Database Tracking**: All allocations logged in SQLite

### Usage Examples:
```python
from mt5_instance_allocator import MT5InstanceAllocator

allocator = MT5InstanceAllocator()

# Allocate instance for new Press Pass user
instance, msg = allocator.allocate_instance(user_id="12345", tier="PRESS_PASS")
# Returns: Magic 50001, Port 9401, expires in 7 days

# Get user's current instance
instance = allocator.get_user_instance(user_id="12345")
# Returns: All details about their allocated MT5

# Recycle expired instances
recycled = allocator.recycle_expired_instances()
# Automatically cleans up 7-day old Press Pass assignments
```

## 📊 Quick Reference

### Instance Distribution:
- **200x Generic_Demo**: Press Pass trials (7-day auto-recycle)
- **20x Forex_Demo**: Regulated broker testing
- **10x Coinexx_Demo**: Offshore broker testing
- **5x Forex_Live**: Conservative live trading
- **10x Coinexx_Live**: High-leverage live trading

### Magic Number Ranges:
- 10001-10010: Coinexx Live
- 20001-20005: Forex Live
- 30001-30020: Forex Demo
- 40001-40010: Coinexx Demo
- 50001-50200: Generic Demo (Press Pass)

### Port Ranges:
- 9001-9010: Coinexx Live
- 9101-9105: Forex Live
- 9201-9220: Forex Demo
- 9301-9310: Coinexx Demo
- 9401-9600: Generic Demo

## 🔧 Manual EA Transfer Options

Since the EA file is large, you can:

1. **Download from webapp**:
   ```
   https://joinbitten.com/static/BITTENBridge_v3_ENHANCED.mq5
   ```

2. **Use Windows RDP/Session Manager** to copy file directly

3. **Create download script** on Windows:
   ```powershell
   Invoke-WebRequest -Uri "https://joinbitten.com/static/BITTENBridge_v3_ENHANCED.mq5" `
                     -OutFile "C:\MT5_Farm\BITTENBridge_v3_ENHANCED.mq5"
   ```

## ✅ Everything is Ready\!

- **Allocator**: Built and tested ✅
- **Instance Tracking**: Complete with database ✅
- **EA Location**: Known and documented ✅
- **Deployment Path**: Clear instructions ✅
- **Recycling System**: Automated for Press Pass ✅
