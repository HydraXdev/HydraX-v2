#!/usr/bin/env python3
"""
Test ZMQ Gold Routing - Demonstrate future-proofed architecture
"""

import json
import time
import threading
from zmq_tick_receiver import ZMQTickReceiver


class GoldAnalyzer:
    """
    Specialized gold analyzer for XAUUSD
    Demonstrates how gold can be processed differently
    """
    
    def __init__(self):
        self.gold_stats = {
            'ticks': 0,
            'max_spread': 0,
            'min_spread': float('inf'),
            'avg_spread': 0,
            'volatility_spikes': 0,
            'liquidity_events': 0
        }
        self.spread_history = []
        
    def analyze_gold_tick(self, data: dict):
        """Perform gold-specific analysis"""
        symbol = data.get('symbol')
        bid = data.get('bid', 0)
        ask = data.get('ask', 0)
        spread = ask - bid
        
        # Update statistics
        self.gold_stats['ticks'] += 1
        self.spread_history.append(spread)
        
        # Keep last 100 spreads for volatility analysis
        if len(self.spread_history) > 100:
            self.spread_history.pop(0)
            
        # Update spread stats
        if spread > self.gold_stats['max_spread']:
            self.gold_stats['max_spread'] = spread
        if spread < self.gold_stats['min_spread']:
            self.gold_stats['min_spread'] = spread
            
        # Calculate average spread
        self.gold_stats['avg_spread'] = sum(self.spread_history) / len(self.spread_history)
        
        # Detect volatility spikes (spread > 2x average)
        if spread > self.gold_stats['avg_spread'] * 2:
            self.gold_stats['volatility_spikes'] += 1
            print(f"⚡ GOLD VOLATILITY SPIKE: Spread ${spread:.2f} "
                  f"(avg: ${self.gold_stats['avg_spread']:.2f})")
            
        # Detect liquidity events (very tight spreads)
        if spread < 0.50:  # Less than 50 cents spread
            self.gold_stats['liquidity_events'] += 1
            print(f"💎 GOLD LIQUIDITY EVENT: Tight spread ${spread:.2f}")
            
        # Special gold signals
        if self.should_generate_gold_signal(data):
            self.generate_gold_signal(data)
            
    def should_generate_gold_signal(self, data: dict) -> bool:
        """Determine if gold-specific signal should be generated"""
        # Example logic for gold
        if self.gold_stats['ticks'] < 10:
            return False
            
        spread = data.get('ask', 0) - data.get('bid', 0)
        
        # Gold signal criteria:
        # 1. Spread is tighter than average (good liquidity)
        # 2. Not during volatility spike
        # 3. Sufficient data collected
        
        is_tight_spread = spread < self.gold_stats['avg_spread'] * 0.8
        is_stable = self.gold_stats['volatility_spikes'] < 3
        
        return is_tight_spread and is_stable
        
    def generate_gold_signal(self, data: dict):
        """Generate gold-specific trading signal"""
        print("\n" + "="*60)
        print("🏆 GOLD TRADING SIGNAL GENERATED")
        print("="*60)
        print(f"Symbol: {data.get('symbol')}")
        print(f"Bid: ${data.get('bid', 0):.2f}")
        print(f"Ask: ${data.get('ask', 0):.2f}")
        print(f"Spread: ${data.get('ask', 0) - data.get('bid', 0):.2f}")
        print(f"Average Spread: ${self.gold_stats['avg_spread']:.2f}")
        print(f"Volatility Spikes: {self.gold_stats['volatility_spikes']}")
        print(f"Signal Type: GOLD LIQUIDITY OPPORTUNITY")
        print("="*60 + "\n")
        
    def print_analysis(self):
        """Print gold analysis summary"""
        print("\n" + "="*60)
        print("🏆 GOLD ANALYSIS SUMMARY")
        print("="*60)
        print(f"Total Ticks: {self.gold_stats['ticks']}")
        print(f"Spread Range: ${self.gold_stats['min_spread']:.2f} - "
              f"${self.gold_stats['max_spread']:.2f}")
        print(f"Average Spread: ${self.gold_stats['avg_spread']:.2f}")
        print(f"Volatility Spikes: {self.gold_stats['volatility_spikes']}")
        print(f"Liquidity Events: {self.gold_stats['liquidity_events']}")
        print("="*60)


def demonstrate_routing():
    """Demonstrate the gold routing capabilities"""
    
    # Create specialized handlers
    gold_analyzer = GoldAnalyzer()
    regular_tick_count = 0
    
    def handle_regular_tick(data: dict):
        """Handle non-gold ticks"""
        nonlocal regular_tick_count
        regular_tick_count += 1
        symbol = data.get('symbol')
        
        # Print every 10th tick
        if regular_tick_count % 10 == 0:
            print(f"📈 Regular: {symbol} - "
                  f"Bid: {data.get('bid', 0):.5f}, "
                  f"Ticks: {regular_tick_count}")
            
    def handle_market_data(data: dict):
        """Route data based on symbol"""
        if data.get('gold', False):
            # Route to gold analyzer
            gold_analyzer.analyze_gold_tick(data)
        else:
            # Route to regular handler
            handle_regular_tick(data)
            
    # Create receiver
    print("🚀 Starting Gold Routing Demonstration...")
    print("=" * 60)
    print("This demonstrates how XAUUSD can be processed differently")
    print("Watch for:")
    print("  ⚡ GOLD ticks (special processing)")
    print("  💎 Liquidity events (tight spreads)")
    print("  🏆 Gold-specific signals")
    print("=" * 60)
    
    receiver = ZMQTickReceiver("tcp://localhost:5555")
    receiver.set_market_handler(handle_market_data)
    
    # Run for demonstration
    try:
        # Start receiver in thread
        receiver_thread = threading.Thread(target=receiver.run)
        receiver_thread.daemon = True
        receiver_thread.start()
        
        # Run for 60 seconds
        print("\nRunning for 60 seconds...\n")
        time.sleep(60)
        
    except KeyboardInterrupt:
        print("\n⏹️ Stopped by user")
    finally:
        receiver.stop()
        gold_analyzer.print_analysis()
        print(f"\n📊 Regular ticks processed: {regular_tick_count}")


def test_topic_filtering():
    """Test subscribing to specific topics only"""
    print("\n🔍 Testing Topic-Specific Subscription...")
    print("=" * 60)
    print("Subscribing ONLY to XAUUSD topic")
    print("=" * 60)
    
    # Create receiver with custom subscription
    receiver = ZMQTickReceiver("tcp://localhost:5555")
    
    # Override subscription to gold only
    if receiver.connect():
        # Unsubscribe from all
        receiver.socket.setsockopt(zmq.SUBSCRIBE, b"")
        # Subscribe only to XAUUSD
        receiver.socket.setsockopt(zmq.SUBSCRIBE, b"XAUUSD")
        print("✅ Subscribed to XAUUSD only")
        
        gold_count = 0
        
        def count_gold(data: dict):
            nonlocal gold_count
            gold_count += 1
            print(f"⚡ GOLD ONLY: {data.get('symbol')} - "
                  f"Tick #{gold_count}")
                  
        receiver.set_market_handler(count_gold)
        
        # Run for 10 seconds
        try:
            print("\nRunning for 10 seconds (GOLD ONLY)...\n")
            receiver_thread = threading.Thread(target=receiver.run)
            receiver_thread.daemon = True
            receiver_thread.start()
            time.sleep(10)
        finally:
            receiver.stop()
            print(f"\n✅ Received {gold_count} GOLD ticks only")
            

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--gold-only":
        test_topic_filtering()
    else:
        demonstrate_routing()
        # Optionally test topic filtering after
        test_topic_filtering()