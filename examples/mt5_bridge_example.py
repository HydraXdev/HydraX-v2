"""
🎯 MT5 Bridge Usage Example
Demonstrates how to use the MT5 result parser and integration
"""

import asyncio
import logging
from datetime import datetime

from src.mt5_bridge import (
    MT5ResultParser,
    MT5ResultAggregator,
    TradeResult,
    MT5BridgeIntegration
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_basic_parsing():
    """Example of basic MT5 result parsing"""
    print("\n=== Basic MT5 Result Parsing ===\n")
    
    parser = MT5ResultParser()
    
    # Example 1: Trade opened
    result1 = parser.parse(
        "TRADE_OPENED|ticket:12345|symbol:EURUSD|type:BUY|"
        "volume:0.01|price:1.12345|sl:1.11345|tp:1.13345|comment:BITTEN"
    )
    print("Trade Opened Result:")
    print(f"  Type: {result1['type']}")
    print(f"  Ticket: {result1['ticket']}")
    print(f"  Symbol: {result1['symbol']}")
    print(f"  Status: {result1['status']}")
    
    # Example 2: Trade closed
    result2 = parser.parse(
        "TRADE_CLOSED|ticket:12345|close_price:1.12445|"
        "profit:10.50|swap:0|commission:-0.20|close_time:2024-01-07 15:30:45"
    )
    print("\nTrade Closed Result:")
    print(f"  Type: {result2['type']}")
    print(f"  Profit: ${result2['profit']}")
    print(f"  Net Profit: ${result2['net_profit']}")
    
    # Example 3: Error
    result3 = parser.parse(
        "ERROR|code:10019|message:Insufficient funds|context:TRADE_OPEN"
    )
    print("\nError Result:")
    print(f"  Type: {result3['type']}")
    print(f"  Error: {result3['error_message']}")
    print(f"  Description: {result3['error_description']}")


def example_trade_result_model():
    """Example of using TradeResult model"""
    print("\n=== Trade Result Model ===\n")
    
    # Create from parsed result
    parsed = {
        'type': 'trade_opened',
        'ticket': 12346,
        'symbol': 'GBPUSD',
        'order_type': 'SELL',
        'volume': 0.02,
        'price': 1.26500,
        'stop_loss': 1.27500,
        'take_profit': 1.25500,
        'status': 'OPEN'
    }
    
    trade_result = TradeResult.from_parser_result(parsed)
    
    print("Trade Result Model:")
    print(f"  Symbol: {trade_result.symbol}")
    print(f"  Direction: {trade_result.order_type}")
    print(f"  Risk/Reward: {trade_result.risk_reward_ratio}")
    print(f"  Summary: {trade_result.format_summary()}")


def example_batch_processing():
    """Example of batch result processing"""
    print("\n=== Batch Processing ===\n")
    
    aggregator = MT5ResultAggregator()
    
    # Add multiple results
    results = [
        "TRADE_CLOSED|ticket:12345|close_price:1.12445|profit:10.50|swap:0|commission:-0.20|close_time:2024-01-07 15:30:45",
        "TRADE_CLOSED|ticket:12346|close_price:1.26300|profit:-5.00|swap:0|commission:-0.20|close_time:2024-01-07 16:30:45",
        "TRADE_CLOSED|ticket:12347|close_price:145.750|profit:25.00|swap:-0.50|commission:-0.20|close_time:2024-01-07 17:30:45",
        "ERROR|code:10019|message:Insufficient funds"
    ]
    
    for result in results:
        parsed = aggregator.add_result(result)
        print(f"Added: {parsed['type']}")
    
    # Get summary
    summary = aggregator.get_summary()
    print("\nBatch Summary:")
    print(f"  Total Results: {summary['total_results']}")
    print(f"  Total Trades: {summary['total_trades']}")
    print(f"  Win Rate: {summary['win_rate']:.1f}%")
    print(f"  Total Profit: ${summary['total_profit']}")
    print(f"  Errors: {len(summary['errors'])}")


async def example_integration():
    """Example of full integration with BITTEN system"""
    print("\n=== MT5 Bridge Integration ===\n")
    
    # Note: This requires database to be set up
    # For demo purposes, we'll just show the structure
    
    bridge = MT5BridgeIntegration()
    
    # Example MT5 result
    mt5_result = (
        "TRADE_OPENED|ticket:12348|symbol:EURUSD|type:BUY|"
        "volume:0.01|price:1.12345|sl:1.11345|tp:1.13345|comment:BITTEN"
    )
    
    print("Processing MT5 result...")
    print(f"Result: {mt5_result}")
    
    # In real usage, this would:
    # 1. Parse the result
    # 2. Create database trade record
    # 3. Update risk session
    # 4. Send Telegram confirmation
    # 5. Calculate and award XP
    
    # Simulate processing
    parser = MT5ResultParser()
    parsed = parser.parse(mt5_result)
    trade_result = TradeResult.from_parser_result(parsed)
    
    print("\nWould perform:")
    print("  ✓ Save to database")
    print("  ✓ Update risk tracking")
    print("  ✓ Send Telegram notification")
    print("  ✓ Award XP for trade")


def example_real_world_scenarios():
    """Example of real-world MT5 scenarios"""
    print("\n=== Real-World Scenarios ===\n")
    
    parser = MT5ResultParser()
    
    scenarios = [
        # Scenario 1: Successful scalp trade
        {
            'name': 'Successful Scalp',
            'open': "TRADE_OPENED|ticket:50001|symbol:EURUSD|type:BUY|volume:0.10|price:1.09852|sl:1.09752|tp:1.09952",
            'close': "TRADE_CLOSED|ticket:50001|close_price:1.09952|profit:100.00|swap:0|commission:-2.00|close_time:2024-01-07 10:15:30"
        },
        
        # Scenario 2: Stop loss hit
        {
            'name': 'Stop Loss Hit',
            'open': "TRADE_OPENED|ticket:50002|symbol:GBPUSD|type:SELL|volume:0.05|price:1.27650|sl:1.27850|tp:1.27250",
            'close': "TRADE_CLOSED|ticket:50002|close_price:1.27850|profit:-100.00|swap:0|commission:-1.00|close_time:2024-01-07 11:30:45"
        },
        
        # Scenario 3: Requote error
        {
            'name': 'Requote Error',
            'error': "ERROR|code:10004|message:Requote|context:TRADE_OPEN"
        }
    ]
    
    for scenario in scenarios:
        print(f"\nScenario: {scenario['name']}")
        print("-" * 40)
        
        if 'open' in scenario:
            # Parse open
            open_result = parser.parse(scenario['open'])
            trade = TradeResult.from_parser_result(open_result)
            print(f"Opened: {trade.format_summary()}")
            
            # Parse close
            close_result = parser.parse(scenario['close'])
            trade_closed = TradeResult.from_parser_result(close_result)
            
            # Update trade with close info
            trade.close_price = trade_closed.close_price
            trade.net_profit = trade_closed.net_profit
            trade.status = 'CLOSED'
            
            print(f"Closed: {trade.format_summary()}")
            print(f"Pips: {trade.get_pips()}")
            
        elif 'error' in scenario:
            error_result = parser.parse(scenario['error'])
            print(f"Error: {error_result['error_description']}")


def main():
    """Run all examples"""
    print("🎯 MT5 Bridge Examples")
    print("=" * 50)
    
    # Run synchronous examples
    example_basic_parsing()
    example_trade_result_model()
    example_batch_processing()
    example_real_world_scenarios()
    
    # Run async example
    print("\n" + "=" * 50)
    asyncio.run(example_integration())
    
    print("\n✅ All examples completed!")


if __name__ == "__main__":
    main()