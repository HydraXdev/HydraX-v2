"""
🎯 BITTEN Volatility Manager Usage Examples
Shows how volatility affects trading without wimpy position reductions
"""

import asyncio
from datetime import datetime

from src.bitten_core.volatility_manager import (
    VolatilityManager, VolatilityLevel, VolatilityData
)
from src.bitten_core.volatility_integration import (
    VolatilityIntegration, get_volatility_integration
)
from src.bitten_core.fire_modes import FireMode


async def example_normal_market():
    """Example: Normal market conditions"""
    print("\n=== NORMAL MARKET CONDITIONS ===\n")
    
    manager = VolatilityManager()
    
    # Normal market data
    data = VolatilityData(
        atr_current=0.0010,
        atr_average=0.0010,
        atr_percentile=50.0,
        spread_current=1.0,
        spread_normal=1.0,
        recent_gaps=[]
    )
    
    level = manager.calculate_volatility_level(data)
    print(f"Volatility Level: {level.value}")
    print(f"TCS Requirement: {level.get_tcs_requirement(72)}% (base: 72%)")
    print(f"Stop Multiplier: {level.get_stop_multiplier()}x")
    print(f"Confirmation Required: {level.requires_confirmation()}")
    
    # No mission brief in normal conditions
    brief = manager.get_mission_brief(level, data, 'EURUSD', 72)
    print(f"Mission Brief: {brief or 'None - normal operations'}")


async def example_high_volatility_news():
    """Example: High volatility from news event"""
    print("\n=== HIGH VOLATILITY - NEWS EVENT ===\n")
    
    manager = VolatilityManager()
    
    # High volatility data
    data = VolatilityData(
        atr_current=0.0018,  # 80% above normal
        atr_average=0.0010,
        atr_percentile=85.0,
        spread_current=4.2,  # Spread widened
        spread_normal=1.0,
        recent_gaps=[],
        vix_level=28.0,
        news_events=['FOMC Rate Decision', 'Powell Speech']
    )
    
    level = manager.calculate_volatility_level(data)
    print(f"Volatility Level: {level.value}")
    
    # Generate mission brief
    brief = manager.get_mission_brief(level, data, 'EURUSD', 72)
    print("\nMission Brief:")
    print(brief)
    
    # Show confirmation message
    confirmation = manager.get_confirmation_message(level, 'EURUSD', 'BUY')
    print("\nConfirmation Required:")
    print(confirmation)


async def example_trade_flow_with_volatility():
    """Example: Complete trade flow with volatility checks"""
    print("\n=== TRADE FLOW WITH VOLATILITY ===\n")
    
    integration = get_volatility_integration()
    
    # Simulate trade attempt in high volatility
    trade_params = {
        'symbol': 'GBPUSD',
        'tcs': 78.0,
        'tier': 'NIBBLER',
        'fire_mode': FireMode.SPRAY
    }
    
    print(f"Trade Attempt: {trade_params['symbol']} @ {trade_params['tcs']}% TCS")
    
    # Check volatility requirements
    result = await integration.check_volatility_requirements(**trade_params)
    
    print(f"\nVolatility Check Results:")
    print(f"  Level: {result['level'].value}")
    print(f"  Allowed: {result['allowed']}")
    print(f"  Adjusted TCS Required: {result['adjusted_tcs']}%")
    print(f"  Stop Multiplier: {result['stop_multiplier']}x")
    print(f"  Message: {result['message']}")
    
    if result.get('mission_brief'):
        print(f"\n{result['mission_brief']}")
    
    # If requires confirmation
    if result['requires_confirmation'] and result['allowed']:
        print("\n⚠️ High volatility detected - storing pending confirmation")
        integration.store_pending_confirmation(
            user_id=123,
            trade_details={
                'symbol': trade_params['symbol'],
                'direction': 'BUY',
                'tcs': trade_params['tcs'],
                'volatility_level': result['level'].value
            }
        )
        
        # Simulate user response
        print("\nUser types: CONFIRM")
        confirm_result = await integration.process_volatility_confirmation(
            123, 'CONFIRM'
        )
        print(f"Result: {confirm_result['message']}")


async def example_stop_loss_adjustment():
    """Example: Stop loss adjustment for volatility"""
    print("\n=== STOP LOSS ADJUSTMENT ===\n")
    
    manager = VolatilityManager()
    base_stop = 100.0  # Base 100 pip stop
    
    for level in VolatilityLevel:
        adjusted = manager.calculate_adjusted_stop(base_stop, level)
        print(f"{level.value:10} -> {adjusted:.0f} pips ({level.get_stop_multiplier()}x)")
    
    print("\nNOTE: Same dollar risk maintained - wider stop = same 2% risk")


async def example_market_briefing():
    """Example: Market volatility briefing"""
    print("\n=== MARKET VOLATILITY BRIEFING ===\n")
    
    integration = get_volatility_integration()
    
    # Get briefing for major pairs
    symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']
    briefing = await integration.volatility_briefing(symbols)
    
    print(briefing)


async def example_philosophy_in_action():
    """Example: BITTEN philosophy - no position reduction"""
    print("\n=== BITTEN PHILOSOPHY IN ACTION ===\n")
    
    manager = VolatilityManager()
    
    # Extreme volatility scenario
    data = VolatilityData(
        atr_current=0.0025,  # 150% above normal
        atr_average=0.0010,
        atr_percentile=95.0,
        spread_current=8.0,
        spread_normal=1.0,
        recent_gaps=[80.0],
        vix_level=40.0,
        news_events=['Banking Crisis', 'Emergency Fed Meeting']
    )
    
    level = manager.calculate_volatility_level(data)
    
    print("Market Condition: EXTREME VOLATILITY")
    print("\nTraditional Systems Would Say:")
    print("  ❌ Reduce position size to 0.5%")
    print("  ❌ Avoid trading")
    print("  ❌ Wait for calm markets")
    
    print("\nBITTEN Says:")
    print("  ✅ FULL 2% position or don't trade")
    print(f"  ✅ Require {level.get_tcs_requirement(72)}% TCS (up from 72%)")
    print(f"  ✅ Use {level.get_stop_multiplier()}x wider stops")
    print("  ✅ Get confirmation before firing")
    
    print("\n💪 No half measures. Trust your TCS or stand down.")


async def main():
    """Run all examples"""
    print("🎯 BITTEN Volatility Manager Examples")
    print("=" * 50)
    
    await example_normal_market()
    await example_high_volatility_news()
    await example_trade_flow_with_volatility()
    await example_stop_loss_adjustment()
    await example_market_briefing()
    await example_philosophy_in_action()
    
    print("\n✅ All examples completed!")
    print("\nRemember: BITTEN never reduces position size.")
    print("Higher standards, not smaller bullets.")


if __name__ == "__main__":
    asyncio.run(main())