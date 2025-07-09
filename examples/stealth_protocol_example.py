#!/usr/bin/env python3
# stealth_protocol_example.py
# Example usage of BITTEN Stealth Protocol in trading scenarios

import asyncio
from datetime import datetime
from typing import Dict, List

# Import stealth components
from src.bitten_core.stealth_protocol import (
    StealthProtocol, StealthLevel, get_stealth_protocol
)
from src.bitten_core.stealth_integration import (
    StealthFireModeIntegration, apply_stealth_to_fire_command
)
from src.bitten_core.stealth_config_loader import get_stealth_config_loader
from src.bitten_core.fire_modes import FireMode, TierLevel

class StealthTradingExample:
    """Example implementation of stealth-enabled trading"""
    
    def __init__(self):
        self.stealth = get_stealth_protocol()
        self.integration = StealthFireModeIntegration()
        self.config_loader = get_stealth_config_loader()
        
    async def example_single_trade_with_stealth(self):
        """Example: Execute a single trade with stealth protocols"""
        print("\n📍 EXAMPLE 1: Single Trade with Stealth")
        print("-" * 40)
        
        # Trade parameters
        trade = {
            'symbol': 'EURUSD',
            'volume': 0.1,
            'entry_price': 1.0850,
            'tp': 1.0900,
            'sl': 1.0800,
            'trade_id': 'DEMO_001'
        }
        
        # Apply stealth
        print(f"Original trade: {trade}")
        stealth_trade = self.stealth.apply_full_stealth(trade)
        
        if stealth_trade.get('skip_trade'):
            print(f"❌ Trade skipped by stealth protocol: {stealth_trade.get('skip_reason')}")
        else:
            print(f"✅ Stealth applied:")
            print(f"   Entry delay: {stealth_trade.get('entry_delay', 0):.2f}s")
            print(f"   Volume: {trade['volume']} -> {stealth_trade['volume']}")
            print(f"   TP: {trade['tp']} -> {stealth_trade['tp']}")
            print(f"   SL: {trade['sl']} -> {stealth_trade['sl']}")
            
    async def example_tier_based_stealth(self):
        """Example: Different stealth behaviors for different tiers"""
        print("\n\n📍 EXAMPLE 2: Tier-Based Stealth Application")
        print("-" * 40)
        
        trade_params = {
            'symbol': 'GBPUSD',
            'volume': 0.2,
            'entry_price': 1.2500,
            'tp': 1.2550,
            'sl': 1.2450
        }
        
        tiers = [TierLevel.NIBBLER, TierLevel.FANG, TierLevel.COMMANDER, TierLevel.APEX]
        
        for tier in tiers:
            print(f"\n{tier.value.upper()} Tier:")
            
            # Check if tier can use stealth
            permissions = self.config_loader.get_tier_permissions(tier.value)
            if not permissions.get('enabled'):
                print("  ❌ No stealth access")
                continue
                
            # Configure stealth for tier
            config = self.integration.configure_stealth_for_tier(tier)
            self.stealth.config = config
            
            # Apply stealth
            result = self.stealth.apply_full_stealth(trade_params.copy())
            
            print(f"  ✅ Stealth Level: {config.level.value}")
            print(f"  Entry delay range: {config.entry_delay_min}-{config.entry_delay_max}s")
            print(f"  Lot jitter range: {config.lot_jitter_min*100:.1f}-{config.lot_jitter_max*100:.1f}%")
            
    async def example_batch_execution_with_shuffle(self):
        """Example: Execute multiple trades with stealth shuffle"""
        print("\n\n📍 EXAMPLE 3: Batch Execution with Shuffle")
        print("-" * 40)
        
        # Create batch of trades
        trades = [
            {'symbol': 'EURUSD', 'volume': 0.1, 'priority': 1},
            {'symbol': 'GBPUSD', 'volume': 0.15, 'priority': 2},
            {'symbol': 'USDJPY', 'volume': 0.2, 'priority': 3},
            {'symbol': 'AUDUSD', 'volume': 0.1, 'priority': 4}
        ]
        
        print("Original order:", [t['symbol'] for t in trades])
        
        # Apply shuffle
        shuffled = self.stealth.execution_shuffle(trades)
        print("Shuffled order:", [t['symbol'] for t in shuffled])
        
        # Show delays
        print("\nExecution schedule:")
        total_time = 0
        for i, trade in enumerate(shuffled):
            delay = trade.get('shuffle_delay', 0)
            total_time += delay
            print(f"  {i+1}. {trade['symbol']} - execute at {total_time:.2f}s")
            
    async def example_volume_cap_management(self):
        """Example: Volume cap to prevent detection"""
        print("\n\n📍 EXAMPLE 4: Volume Cap Management")
        print("-" * 40)
        
        # Reset tracking
        self.stealth.active_trades.clear()
        
        # Try to execute multiple trades on same asset
        asset = 'EURUSD'
        print(f"Attempting to execute 5 trades on {asset}:")
        print(f"(Max per asset: {self.stealth.config.max_concurrent_per_asset})")
        
        for i in range(5):
            trade_id = f"VOL_TEST_{i:03d}"
            allowed = self.stealth.vol_cap(asset, trade_id)
            print(f"  Trade {i+1}: {'✅ ALLOWED' if allowed else '❌ DENIED'}")
            
    async def example_stealth_mode_trading(self):
        """Example: APEX-exclusive STEALTH mode"""
        print("\n\n📍 EXAMPLE 5: APEX Stealth Mode Trading")
        print("-" * 40)
        
        # Configure for APEX stealth mode
        self.stealth.set_level(StealthLevel.GHOST)
        
        trade_params = {
            'symbol': 'XAUUSD',
            'volume': 0.5,
            'entry_price': 1950.00,
            'tp': 1955.00,
            'sl': 1945.00
        }
        
        # Execute with maximum stealth
        result = await self.integration.execute_stealth_trade(
            user_id=99999,
            tier=TierLevel.APEX,
            fire_mode=FireMode.STEALTH,
            trade_params=trade_params
        )
        
        print("APEX Stealth Mode Result:")
        if result.get('success'):
            print("  ✅ Trade executed with maximum stealth")
            print(f"  Trade ID: {result.get('trade_id')}")
            print(f"  All stealth protocols applied")
        else:
            print(f"  ❌ Error: {result.get('error')}")
            
    async def example_pattern_breaking(self):
        """Example: Pattern breaking to avoid detection"""
        print("\n\n📍 EXAMPLE 6: Pattern Breaking Behavior")
        print("-" * 40)
        
        # Get pattern breaking config
        pattern_config = self.config_loader.get_special_behavior('pattern_break')
        
        if pattern_config.get('enabled'):
            print("Pattern Breaking ENABLED")
            print(f"Change behavior every {pattern_config['trade_interval']['min']}-"
                  f"{pattern_config['trade_interval']['max']} trades")
        else:
            print("Pattern Breaking DISABLED")
            
        # Simulate pattern breaking
        print("\nSimulating 20 trades with pattern breaking:")
        levels = [StealthLevel.LOW, StealthLevel.MEDIUM, StealthLevel.HIGH]
        current_level_idx = 0
        trades_until_change = 10
        
        for i in range(20):
            if trades_until_change <= 0:
                # Change pattern
                current_level_idx = (current_level_idx + 1) % len(levels)
                self.stealth.set_level(levels[current_level_idx])
                trades_until_change = 10
                print(f"\n  🔄 Pattern change at trade {i+1}: "
                      f"Switched to {levels[current_level_idx].value}")
            
            trades_until_change -= 1
            
        print("\n✅ Pattern breaking helps avoid detection by regulators")
        
    async def example_stealth_statistics(self):
        """Example: View stealth protocol statistics"""
        print("\n\n📍 EXAMPLE 7: Stealth Protocol Statistics")
        print("-" * 40)
        
        stats = self.stealth.get_stealth_stats()
        
        print("Current Stealth Statistics:")
        print(f"  Status: {'ACTIVE' if stats['enabled'] else 'INACTIVE'}")
        print(f"  Level: {stats['level']}")
        print(f"  Active Trades: {stats['total_active']}")
        print(f"  Actions Logged: {stats['actions_logged']}")
        
        if stats['recent_actions']:
            print("\nRecent Actions:")
            for action in stats['recent_actions'][-3:]:
                print(f"  - {action['type']} at {action['timestamp']} "
                      f"(Level: {action['level']})")

async def main():
    """Run all examples"""
    print("🥷 BITTEN STEALTH PROTOCOL EXAMPLES")
    print("=" * 50)
    print("Demonstrating stealth protocol usage in trading scenarios")
    
    example = StealthTradingExample()
    
    try:
        # Run all examples
        await example.example_single_trade_with_stealth()
        await example.example_tier_based_stealth()
        await example.example_batch_execution_with_shuffle()
        await example.example_volume_cap_management()
        await example.example_stealth_mode_trading()
        await example.example_pattern_breaking()
        await example.example_stealth_statistics()
        
        print("\n\n✅ All examples completed successfully!")
        
        # Final tips
        print("\n💡 STEALTH PROTOCOL TIPS:")
        print("  1. Higher tiers get more sophisticated stealth options")
        print("  2. APEX tier has exclusive GHOST level for maximum stealth")
        print("  3. Stealth actions are logged for monitoring and adjustment")
        print("  4. Use pattern breaking to avoid regulatory detection")
        print("  5. Volume caps prevent suspicious trading patterns")
        
    except Exception as e:
        print(f"\n❌ Error in examples: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import os
    import sys
    
    # Add project root to path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    
    # Run examples
    asyncio.run(main())