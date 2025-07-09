#!/usr/bin/env python3
# microstructure_analysis_demo.py
# Demonstration of Market Microstructure Analysis Components

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import random
import numpy as np
from src.order_flow import (
    MicrostructureScorer,
    IcebergDetector,
    SpoofingDetector,
    HFTActivityDetector,
    QuoteStuffingIdentifier,
    HiddenLiquidityScanner,
    MarketMakerAnalyzer
)

class MicrostructureDemo:
    """Demonstration of microstructure analysis capabilities"""
    
    def __init__(self):
        self.symbol = 'EURUSD'
        self.tick_size = 0.0001
        self.scorer = MicrostructureScorer(self.symbol, self.tick_size)
        
    def generate_market_data(self, base_price: float = 1.0850) -> tuple:
        """Generate simulated market data"""
        
        # Generate order book
        bid_book = {}
        ask_book = {}
        
        # Normal market maker quotes
        for i in range(10):
            bid_price = base_price - (i + 1) * self.tick_size
            ask_price = base_price + (i + 1) * self.tick_size
            
            # Add some variation
            bid_size = random.randint(10000, 100000) * (10 - i) / 10
            ask_size = random.randint(10000, 100000) * (10 - i) / 10
            
            bid_book[bid_price] = bid_size
            ask_book[ask_price] = ask_size
        
        # Generate trades
        trades = []
        for i in range(20):
            side = random.choice(['buy', 'sell'])
            if side == 'buy':
                price = base_price + random.uniform(0, 5) * self.tick_size
            else:
                price = base_price - random.uniform(0, 5) * self.tick_size
            
            trades.append({
                'timestamp': datetime.now() - timedelta(seconds=20-i),
                'price': price,
                'volume': random.randint(1000, 50000),
                'side': side,
                'spread': 2.0
            })
        
        # Generate quotes
        quotes = []
        for i in range(50):
            quotes.append({
                'timestamp': datetime.now() - timedelta(seconds=50-i),
                'event_type': random.choice(['quote', 'trade', 'cancel', 'modify']),
                'price': base_price + random.uniform(-10, 10) * self.tick_size,
                'size': random.randint(1000, 20000),
                'side': random.choice(['bid', 'ask']),
                'action': random.choice(['add', 'modify', 'cancel']),
                'message_id': f'MSG_{i}',
                'aggressive': random.random() > 0.7
            })
        
        return bid_book, ask_book, trades, quotes
    
    def simulate_iceberg_order(self, base_price: float = 1.0850):
        """Simulate iceberg order detection"""
        
        print("\n=== ICEBERG ORDER DETECTION DEMO ===")
        
        detector = IcebergDetector(self.symbol, self.tick_size)
        
        # Simulate iceberg order slices
        iceberg_price = base_price + 2 * self.tick_size
        slice_size = 10000  # Consistent slice size
        
        print(f"Simulating iceberg order at {iceberg_price:.5f}")
        
        for i in range(8):  # 8 slices
            timestamp = datetime.now() + timedelta(seconds=i*30)
            
            # Add some noise
            actual_size = slice_size + random.randint(-500, 500)
            
            signal = detector.update_order_flow(
                timestamp=timestamp,
                price=iceberg_price,
                volume=actual_size,
                side='buy',
                spread=2.0
            )
            
            if signal:
                print(f"\n✓ Iceberg detected!")
                print(f"  Price: {signal.price_level:.5f}")
                print(f"  Total Volume: {signal.total_volume:,.0f}")
                print(f"  Slices: {signal.slice_count}")
                print(f"  Pattern: {signal.pattern_type}")
                print(f"  Confidence: {signal.confidence:.2%}")
                print(f"  Institutional Probability: {signal.institutional_probability:.2%}")
    
    def simulate_spoofing(self, base_price: float = 1.0850):
        """Simulate spoofing detection"""
        
        print("\n=== SPOOFING DETECTION DEMO ===")
        
        detector = SpoofingDetector(self.symbol, self.tick_size)
        
        # Create normal order book
        bid_levels = []
        ask_levels = []
        
        for i in range(5):
            bid_levels.append((base_price - (i+1) * self.tick_size, 50000))
            ask_levels.append((base_price + (i+1) * self.tick_size, 50000))
        
        # Update with normal book
        detector.update_order_book(datetime.now(), bid_levels, ask_levels)
        
        # Now add spoofing layers
        print("Adding large fake orders on bid side...")
        
        # Large fake orders
        fake_bid_levels = bid_levels.copy()
        for i in range(2, 5):
            fake_bid_levels[i] = (fake_bid_levels[i][0], 500000)  # 10x size
        
        event = detector.update_order_book(
            datetime.now() + timedelta(seconds=1),
            fake_bid_levels,
            ask_levels
        )
        
        if event:
            print(f"\n✓ Spoofing detected!")
            print(f"  Pattern: {event.pattern_type}")
            print(f"  Side: {event.side}")
            print(f"  Spoofed Volume: {event.spoofed_volume:,.0f}")
            print(f"  Affected Levels: {event.affected_levels}")
            print(f"  Confidence: {event.confidence:.2%}")
            print(f"  Price Impact: {event.price_impact:.1f} pips")
    
    def simulate_hft_activity(self):
        """Simulate HFT activity detection"""
        
        print("\n=== HFT ACTIVITY DETECTION DEMO ===")
        
        detector = HFTActivityDetector(self.symbol, self.tick_size)
        
        base_time = datetime.now()
        
        # Simulate different HFT patterns
        patterns = {
            'market_making': {
                'message_rate': 30,
                'cancel_ratio': 0.85,
                'aggressive': False
            },
            'momentum': {
                'message_rate': 20,
                'cancel_ratio': 0.3,
                'aggressive': True
            },
            'predatory': {
                'message_rate': 100,
                'cancel_ratio': 0.9,
                'aggressive': True
            }
        }
        
        for pattern_name, params in patterns.items():
            print(f"\nSimulating {pattern_name} HFT pattern...")
            
            # Generate events
            for i in range(100):
                timestamp = base_time + timedelta(milliseconds=i * (1000 / params['message_rate']))
                
                # Mix of event types based on pattern
                if random.random() < params['cancel_ratio']:
                    event_type = random.choice(['cancel', 'modify'])
                else:
                    event_type = random.choice(['quote', 'trade'])
                
                signal = detector.process_event(
                    timestamp=timestamp,
                    event_type=event_type,
                    price=1.0850 + random.uniform(-5, 5) * self.tick_size,
                    size=random.randint(1000, 10000),
                    side=random.choice(['bid', 'ask']),
                    aggressive=params['aggressive']
                )
                
                if signal:
                    print(f"\n✓ HFT activity detected!")
                    print(f"  Type: {signal.activity_type}")
                    print(f"  Message Rate: {signal.message_rate:.1f}/sec")
                    print(f"  Cancel Ratio: {signal.cancel_replace_ratio:.2%}")
                    print(f"  Quote Life: {signal.quote_life_ms:.1f}ms")
                    print(f"  Intensity: {signal.intensity:.2%}")
                    break
    
    def simulate_quote_stuffing(self):
        """Simulate quote stuffing detection"""
        
        print("\n=== QUOTE STUFFING DETECTION DEMO ===")
        
        identifier = QuoteStuffingIdentifier(self.symbol, self.tick_size)
        
        base_time = datetime.now()
        
        # Normal quote flow
        print("Processing normal quote flow...")
        for i in range(20):
            identifier.process_quote_message(
                timestamp=base_time + timedelta(seconds=i),
                message_id=f'NORM_{i}',
                action='add',
                price=1.0850 + random.uniform(-5, 5) * self.tick_size,
                size=random.randint(10000, 50000),
                side=random.choice(['bid', 'ask'])
            )
        
        # Quote stuffing burst
        print("\nSimulating quote stuffing attack...")
        stuff_time = base_time + timedelta(seconds=25)
        
        for i in range(200):  # 200 messages in quick succession
            timestamp = stuff_time + timedelta(milliseconds=i * 5)  # 5ms apart
            
            event = identifier.process_quote_message(
                timestamp=timestamp,
                message_id=f'STUFF_{i}',
                action=random.choice(['add', 'cancel', 'modify']),
                price=1.0850 + (i % 3) * self.tick_size,  # Oscillating prices
                size=random.randint(100000, 200000),
                side='bid' if i % 2 == 0 else 'ask'
            )
            
            if event:
                print(f"\n✓ Quote stuffing detected!")
                print(f"  Pattern: {event.pattern_type}")
                print(f"  Duration: {event.duration_ms:.0f}ms")
                print(f"  Message Count: {event.message_count}")
                print(f"  Peak Rate: {event.peak_rate:.0f} msg/sec")
                print(f"  Severity: {event.severity}")
                print(f"  Market Impact:")
                for key, value in event.market_impact.items():
                    print(f"    {key}: {value:.1f}")
                break
    
    def simulate_hidden_liquidity(self, base_price: float = 1.0850):
        """Simulate hidden liquidity detection"""
        
        print("\n=== HIDDEN LIQUIDITY DETECTION DEMO ===")
        
        scanner = HiddenLiquidityScanner(self.symbol, self.tick_size)
        
        # Create visible order book
        displayed_liquidity = {}
        for i in range(5):
            price = base_price + (i + 1) * self.tick_size
            displayed_liquidity[price] = 20000  # Small displayed size
        
        # Update order book
        bid_book = {base_price - i * self.tick_size: 20000 for i in range(1, 6)}
        ask_book = displayed_liquidity
        
        scanner.update_order_book(datetime.now(), bid_book, ask_book)
        
        # Simulate execution that exceeds displayed
        print("Simulating large execution exceeding displayed liquidity...")
        
        signal = scanner.analyze_execution(
            timestamp=datetime.now(),
            price=base_price + self.tick_size,
            executed_size=100000,  # 5x displayed
            displayed_liquidity=displayed_liquidity,
            side='buy'
        )
        
        if signal:
            print(f"\n✓ Hidden liquidity detected!")
            print(f"  Type: {signal.liquidity_type}")
            print(f"  Estimated Hidden Size: {signal.estimated_size:,.0f}")
            print(f"  Detection Method: {signal.detection_method}")
            print(f"  Confidence: {signal.confidence:.2%}")
            print(f"  Evidence:")
            for key, value in signal.evidence.items():
                print(f"    {key}: {value}")
    
    def run_comprehensive_analysis(self):
        """Run comprehensive microstructure analysis"""
        
        print("\n=== COMPREHENSIVE MICROSTRUCTURE ANALYSIS ===")
        
        # Generate market data
        bid_book, ask_book, trades, quotes = self.generate_market_data()
        
        # Add some manipulation patterns
        # Add spoofing
        if random.random() > 0.5:
            print("\nInjecting spoofing pattern...")
            for i in range(3, 6):
                price = list(bid_book.keys())[i]
                bid_book[price] *= 10  # Inflate size
        
        # Add quote stuffing
        if random.random() > 0.5:
            print("Injecting quote stuffing...")
            stuff_quotes = []
            base_time = datetime.now()
            for i in range(100):
                stuff_quotes.append({
                    'timestamp': base_time + timedelta(milliseconds=i * 10),
                    'event_type': 'quote',
                    'price': 1.0850 + random.uniform(-2, 2) * self.tick_size,
                    'size': random.randint(50000, 100000),
                    'side': random.choice(['bid', 'ask']),
                    'action': random.choice(['add', 'cancel']),
                    'message_id': f'STUFF_{i}',
                    'aggressive': False
                })
            quotes.extend(stuff_quotes)
        
        # Update scorer with market data
        score = self.scorer.update_market_data(
            timestamp=datetime.now(),
            bid_book=bid_book,
            ask_book=ask_book,
            trades=trades,
            quotes=quotes
        )
        
        # Display results
        print(f"\n📊 MICROSTRUCTURE ANALYSIS RESULTS")
        print(f"{'='*50}")
        print(f"Overall Score: {score.overall_score:.1f}/100")
        print(f"Market Quality: {score.market_quality.upper()}")
        print(f"\nComponent Scores:")
        print(f"  💧 Liquidity: {score.liquidity_score:.1f}/100")
        print(f"  ⚖️  Stability: {score.stability_score:.1f}/100")
        print(f"  🤝 Fairness: {score.fairness_score:.1f}/100")
        print(f"  ⚡ Efficiency: {score.efficiency_score:.1f}/100")
        
        print(f"\nRisk Metrics:")
        print(f"  🚨 Manipulation Risk: {score.manipulation_risk:.1f}%")
        print(f"  🏦 Institutional Presence: {score.institutional_presence:.1f}%")
        
        print(f"\nKey Insights:")
        for insight in score.key_insights:
            print(f"  {insight}")
        
        # Get trading recommendations
        recommendations = self.scorer.get_trading_recommendations()
        
        print(f"\n💡 TRADING RECOMMENDATIONS")
        print(f"{'='*50}")
        print(f"Can Trade: {'YES' if recommendations['can_trade'] else 'NO'}")
        print(f"Preferred Style: {recommendations['preferred_style'].upper()}")
        print(f"Size Recommendation: {recommendations['size_recommendation'].upper()}")
        print(f"Timing: {recommendations['timing_recommendation'].upper()}")
        
        if recommendations['warnings']:
            print(f"\n⚠️  Warnings:")
            for warning in recommendations['warnings']:
                print(f"  - {warning}")
        
        # Get current state
        state = self.scorer.get_current_state()
        
        print(f"\n📈 CURRENT MARKET STATE")
        print(f"{'='*50}")
        print(f"Spread: {state.spread:.1f} pips")
        print(f"HFT Intensity: {state.hft_intensity:.2%}")
        print(f"Active Market Makers: {state.maker_count}")
        print(f"Recent Manipulation Events: {state.recent_manipulation_events}")
        print(f"Hidden Liquidity Estimate: {state.hidden_liquidity_estimate:,.0f}")

def main():
    """Run the demonstration"""
    
    print("="*60)
    print("MARKET MICROSTRUCTURE ANALYSIS DEMONSTRATION")
    print("="*60)
    
    demo = MicrostructureDemo()
    
    # Run individual component demos
    demo.simulate_iceberg_order()
    demo.simulate_spoofing()
    demo.simulate_hft_activity()
    demo.simulate_quote_stuffing()
    demo.simulate_hidden_liquidity()
    
    # Run comprehensive analysis
    demo.run_comprehensive_analysis()
    
    print("\n" + "="*60)
    print("Demonstration completed!")

if __name__ == "__main__":
    main()