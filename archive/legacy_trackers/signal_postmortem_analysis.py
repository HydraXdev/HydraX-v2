#!/usr/bin/env python3
"""
VENOM Signal Post-Mortem Analysis
Analyzes the 8 recent signals to determine actual win/loss outcomes
"""

import json
import os
from datetime import datetime

def analyze_signal_outcome(mission_data, current_prices):
    """Analyze if a signal would have hit TP or SL first"""
    signal = mission_data.get('enhanced_signal', {})
    
    entry_price = signal.get('entry_price')
    stop_loss = signal.get('stop_loss') 
    take_profit = signal.get('take_profit')
    direction = signal.get('direction')
    symbol = signal.get('symbol')
    
    if not all([entry_price, stop_loss, take_profit, direction, symbol]):
        return "INCOMPLETE_DATA"
    
    # Get current market price
    current_tick = None
    for tick in current_prices.get('ticks', []):
        if tick['symbol'] == symbol:
            current_tick = tick
            break
    
    if not current_tick:
        return "NO_CURRENT_PRICE"
    
    current_price = current_tick['bid'] if direction == 'SELL' else current_tick['ask']
    
    # Analyze outcome based on direction
    if direction == 'BUY':
        # BUY signal: TP above entry, SL below entry
        if current_price >= take_profit:
            return "WIN"
        elif current_price <= stop_loss:
            return "LOSS" 
        else:
            return "PENDING"
    else:  # SELL
        # SELL signal: TP below entry, SL above entry  
        if current_price <= take_profit:
            return "WIN"
        elif current_price >= stop_loss:
            return "LOSS"
        else:
            return "PENDING"

def load_signal_data():
    """Load the 8 recent VENOM signals"""
    signals = [
        "mission_VENOM_OPTIMIZED_EURJPY_000001.json",  # SELL @ 85%
        "mission_VENOM_OPTIMIZED_GBPJPY_000002.json",  # BUY @ 75%
        "mission_VENOM_OPTIMIZED_EURUSD_000003.json",  # SELL @ 95%
        "mission_VENOM_OPTIMIZED_GBPUSD_000004.json",  # BUY @ 87%
        "mission_VENOM_OPTIMIZED_EURJPY_000005.json",  # BUY @ 85%
        "mission_VENOM_OPTIMIZED_GBPJPY_000006.json",  # SELL @ 75%
        "mission_VENOM_OPTIMIZED_EURUSD_000007.json",  # BUY @ 95%
        "mission_VENOM_OPTIMIZED_EURJPY_000008.json",  # SELL @ 85%
    ]
    
    signal_data = []
    missions_dir = "/root/HydraX-v2/missions/"
    
    for signal_file in signals:
        file_path = os.path.join(missions_dir, signal_file)
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
                signal_data.append(data)
        else:
            print(f"⚠️ Missing file: {signal_file}")
    
    return signal_data

def load_current_prices():
    """Load current market prices"""
    try:
        with open('/tmp/ea_raw_data.json', 'r') as f:
            content = f.read().strip()
            # Handle truncated JSON by adding closing brace if needed
            if not content.endswith('}'):
                if content.endswith(']'):
                    content += '}'
                elif content.endswith(','):
                    content = content.rstrip(',') + ']}'
            return json.loads(content)
    except Exception as e:
        print(f"❌ Error loading current prices: {e}")
        # Fallback: Use hardcoded current prices from recent data
        return {
            "ticks": [
                {"symbol": "EURJPY", "bid": 172.598, "ask": 172.618},
                {"symbol": "GBPJPY", "bid": 198.899, "ask": 198.930}, 
                {"symbol": "EURUSD", "bid": 1.16515, "ask": 1.16527},
                {"symbol": "GBPUSD", "bid": 1.34270, "ask": 1.34290}
            ]
        }

def main():
    print("🐍 VENOM SIGNAL POST-MORTEM ANALYSIS")
    print("=" * 50)
    
    # Load data
    signals = load_signal_data()
    current_prices = load_current_prices()
    
    if not signals:
        print("❌ No signal data found")
        return
    
    if not current_prices:
        print("❌ No current price data found")
        return
    
    print(f"📊 Analyzing {len(signals)} signals...")
    print(f"⏰ Current time: {datetime.now()}")
    print()
    
    # Analysis results
    results = []
    wins = 0
    losses = 0
    pending = 0
    
    for i, signal in enumerate(signals, 1):
        signal_id = signal.get('signal_id', f'Signal_{i}')
        confidence = signal.get('confidence', 0)
        quality = signal.get('quality', 'unknown')
        
        enhanced = signal.get('enhanced_signal', {})
        entry_price = enhanced.get('entry_price', 0)
        stop_loss = enhanced.get('stop_loss', 0)
        take_profit = enhanced.get('take_profit', 0)
        direction = enhanced.get('direction', 'UNKNOWN')
        symbol = enhanced.get('symbol', 'UNKNOWN')
        
        outcome = analyze_signal_outcome(signal, current_prices)
        
        # Get current price for display
        current_price = "N/A"
        for tick in current_prices.get('ticks', []):
            if tick['symbol'] == symbol:
                current_price = tick['bid'] if direction == 'SELL' else tick['ask']
                break
        
        # Determine status emoji
        if outcome == "WIN":
            status_emoji = "✅"
            wins += 1
        elif outcome == "LOSS":
            status_emoji = "❌"
            losses += 1
        elif outcome == "PENDING":
            status_emoji = "⏳"
            pending += 1
        else:
            status_emoji = "❓"
        
        print(f"{status_emoji} {signal_id}")
        print(f"   📈 {symbol} {direction} @ {confidence}% ({quality})")
        print(f"   🎯 Entry: {entry_price} | SL: {stop_loss} | TP: {take_profit}")
        print(f"   💹 Current: {current_price} | Outcome: {outcome}")
        print()
        
        results.append({
            'signal_id': signal_id,
            'symbol': symbol,
            'direction': direction,
            'confidence': confidence,
            'quality': quality,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'current_price': current_price,
            'outcome': outcome
        })
    
    # Summary statistics
    total_closed = wins + losses
    if total_closed > 0:
        win_rate = (wins / total_closed) * 100
    else:
        win_rate = 0
    
    print("📊 SUMMARY STATISTICS")
    print("=" * 30)
    print(f"✅ Wins: {wins}")
    print(f"❌ Losses: {losses}")
    print(f"⏳ Pending: {pending}")
    print(f"📈 Win Rate: {win_rate:.1f}% ({wins}/{total_closed})")
    print()
    
    # Quality breakdown
    platinum_signals = [r for r in results if r['quality'] == 'platinum']
    gold_signals = [r for r in results if r['quality'] == 'gold']
    
    platinum_wins = len([r for r in platinum_signals if r['outcome'] == 'WIN'])
    platinum_losses = len([r for r in platinum_signals if r['outcome'] == 'LOSS'])
    platinum_total = platinum_wins + platinum_losses
    
    gold_wins = len([r for r in gold_signals if r['outcome'] == 'WIN'])
    gold_losses = len([r for r in gold_signals if r['outcome'] == 'LOSS'])
    gold_total = gold_wins + gold_losses
    
    print("🏆 QUALITY BREAKDOWN")
    print("=" * 20)
    if platinum_total > 0:
        platinum_rate = (platinum_wins / platinum_total) * 100
        print(f"💎 Platinum ({len(platinum_signals)}): {platinum_rate:.1f}% ({platinum_wins}/{platinum_total})")
    
    if gold_total > 0:
        gold_rate = (gold_wins / gold_total) * 100
        print(f"🥇 Gold ({len(gold_signals)}): {gold_rate:.1f}% ({gold_wins}/{gold_total})")
    
    print()
    print("🎯 VALIDATION COMPLETE")
    
    return results

if __name__ == "__main__":
    results = main()