#!/usr/bin/env python3
"""
ENABLE LIVE TRADING - Real Money Warning
This will modify the system to place actual trades
"""

def enable_live_trading():
    print("⚠️" * 20)
    print("DANGER: REAL MONEY TRADING")
    print("⚠️" * 20)
    print()
    print("This will enable ACTUAL trading on account 843859")
    print("Real money will be at risk!")
    print()
    print("Current settings:")
    print("- Account: 843859")
    print("- Risk per trade: 1% of balance")
    print("- Stop losses: 10-20 pips")
    print("- Max trades: Unlimited")
    print()
    
    confirm1 = input("Type 'I UNDERSTAND THE RISKS' to continue: ")
    if confirm1 != "I UNDERSTAND THE RISKS":
        print("❌ Live trading NOT enabled")
        return False
    
    confirm2 = input("Type 'ENABLE LIVE TRADING' to confirm: ")
    if confirm2 != "ENABLE LIVE TRADING":
        print("❌ Live trading NOT enabled")
        return False
    
    print("✅ Live trading will be enabled")
    print("⚠️ Make sure you monitor your trades!")
    return True

if __name__ == "__main__":
    enable_live_trading()