#!/usr/bin/env python3
"""
Show examples of the new compact signal format
"""

print("""
📊 BITTEN COMPACT SIGNAL EXAMPLES
=================================

🔥 SNIPER SIGNAL (90-95% TCS) - RARE & BOLD:
----------------------------------------
🔥🔥 **SNIPER SHOT** 🔥🔥
**EURUSD BUY** | 93% | ⏰ 10min
[🎯 SNIPER INTEL]


⭐ PRECISION SIGNAL (80-89% TCS) - QUALITY:
----------------------------------------
⭐ **Precision Strike** ⭐
GBPUSD SELL | 85% confidence | ⏰ 10min
[⭐ VIEW INTEL]


✅ STANDARD SIGNAL (70-79% TCS) - NIBBLER:
----------------------------------------
✅ Signal: USDJPY BUY | 74%
⏰ Expires in 10 minutes
[📋 VIEW DETAILS]


KEY DIFFERENCES:
================
• SNIPER: All caps, bold, fire emojis, "SNIPER SHOT"
• PRECISION: Mixed case, star emojis, "Precision Strike"  
• STANDARD: Simple format, checkmark, basic text

• Only 2 lines per signal (was 10+ lines before)
• Visual hierarchy makes quality obvious at a glance
• Different button text per signal type

CURRENT SETUP:
==============
✅ Monitoring: EUR/USD, GBP/USD, USD/JPY, AUD/USD, USD/CAD
❌ NOT monitoring: XAU/USD (gold) - removed
📊 Data Source: SIMULATED (MT5 live feed coming soon)
⏱️ Check Rate: Every 20 seconds
🎲 Signal Distribution: 60% Standard, 30% Precision, 10% Sniper
""")

# Show what's in the status now
print("\n/status will now show:")
print("====================")
print("• Data: SIMULATED (Live MT5 feed coming soon)")
print("• Pairs: EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD")
print("• No mention of gold/XAUUSD")
print("\nRun: python3 SIGNALS_COMPACT.py to start!")