#!/usr/bin/env python3
"""
Continuous data injector to keep market data fresh for truth tracker
"""
import requests
import json
import time
import threading
import random

def inject_continuous_data():
    """Continuously inject market data every 20 seconds"""
    print("🔄 Starting continuous data injection...")
    
    # Base prices for realistic variation
    base_prices = {
        "EURUSD": 1.0865, "GBPUSD": 1.2736, "USDJPY": 153.26, "USDCAD": 1.3880,
        "AUDUSD": 0.6463, "USDCHF": 0.8665, "NZDUSD": 0.5862, "EURGBP": 0.8493,
        "EURJPY": 166.15, "GBPJPY": 195.22, "GBPNZD": 2.1475, "GBPAUD": 1.9551,
        "EURAUD": 1.6659, "GBPCHF": 1.1252, "AUDJPY": 100.13
    }
    
    while True:
        try:
            # Create realistic tick data with variations
            ticks = []
            for symbol, base_price in base_prices.items():
                # Add larger random variation (0.05% to 0.15% for reliable momentum detection)
                variation = random.uniform(-0.0015, 0.0015)
                current_price = base_price * (1 + variation)
                
                # Calculate bid/ask with realistic spread (0.8-2.5 pips)
                spread_pips = random.uniform(0.8, 2.5)
                if symbol in ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY"]:
                    spread = spread_pips * 0.01  # JPY pairs
                    bid = round(current_price - spread/2, 3)
                    ask = round(current_price + spread/2, 3)
                elif symbol in ["GBPNZD", "GBPAUD", "EURAUD"]:
                    spread = spread_pips * 0.0001  # High precision pairs
                    bid = round(current_price - spread/2, 5)
                    ask = round(current_price + spread/2, 5)
                else:
                    spread = spread_pips * 0.00001  # Major pairs
                    bid = round(current_price - spread/2, 5)
                    ask = round(current_price + spread/2, 5)
                
                ticks.append({
                    "symbol": symbol,
                    "bid": bid,
                    "ask": ask,
                    "spread": spread_pips,
                    "volume": random.randint(800, 1200),
                    "timestamp": time.time()
                })
                
                # Update base price for next iteration (trending movement)
                base_prices[symbol] = current_price
            
            # Update test data with realistic variations
            test_data = {
                "uuid": "truth_tracker_feeder",
                "broker": "truth_tracker_broker", 
                "account_balance": 10000.0,
                "ticks": ticks
            }
            
            response = requests.post("http://localhost:8001/market-data", json=test_data, timeout=5)
            if response.status_code == 200:
                # Log successful injection with sample prices for debug
                sample_prices = {t["symbol"]: f"{t['bid']:.5f}/{t['ask']:.5f}" for t in ticks[:3]}
                log_msg = f"✅ {time.strftime('%H:%M:%S')} - Data injected ({len(ticks)} pairs) - Sample: {sample_prices}"
                print(log_msg)
                
                # Optional debug logging
                with open("/tmp/injector_output.log", "a") as f:
                    f.write(f"{log_msg}\n")
            else:
                print(f"❌ {time.strftime('%H:%M:%S')} - Injection failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {time.strftime('%H:%M:%S')} - Injection error: {e}")
        
        # Wait 20 seconds (less than 30s stale threshold)
        time.sleep(10)  # Faster injection for VENOM signal generation

def main():
    print("🚀 CONTINUOUS MARKET DATA INJECTOR - ENHANCED")
    print("Providing realistic price variations for VENOM signal detection...")
    print("Debug log: /tmp/injector_output.log")
    print("Press Ctrl+C to stop")
    
    try:
        inject_continuous_data()
    except KeyboardInterrupt:
        print("\n🛑 Data injection stopped")

if __name__ == "__main__":
    main()
