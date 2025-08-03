#!/usr/bin/env python3
"""
Test XP Integration with ZMQ telemetry
"""

from zmq_xp_integration import ZMQXPIntegration

def test_xp_integration():
    """Test XP integration logic"""
    print("🧪 Testing XP Integration")
    print("="*50)
    
    # Create XP integration
    xp_integration = ZMQXPIntegration()
    
    # Test telemetry-based XP
    print("\n📊 Testing telemetry-based XP awards...")
    
    # Simulate telemetry with profit milestone
    telemetry = {
        'uuid': 'test_user_001',
        'balance': 1050,
        'equity': 1050,
        'margin': 0,
        'free_margin': 1050,
        'profit': 50,
        'positions': 0
    }
    
    # Initialize starting balance
    xp_integration.user_stats['test_user_001'] = {
        'first_trade': True,
        'total_trades': 0,
        'winning_streak': 0,
        'daily_trades': 0,
        'last_trade_date': None,
        'starting_balance': 1000,  # 5% profit
        'highest_equity': 1000,
        'profit_milestones': set()
    }
    
    xp_award = xp_integration.process_telemetry_for_xp(telemetry)
    if xp_award:
        print(f"✅ XP Award: {xp_award['reason']} (+{xp_award['xp_amount']} XP)")
    else:
        print("❌ No XP award for telemetry")
    
    # Test trade result XP
    print("\n📈 Testing trade result XP awards...")
    
    trade_result = {
        'signal_id': 'VENOM_EURUSD_001_user_test_user_001',
        'status': 'success',
        'ticket': 12345,
        'price': 1.1234
    }
    
    xp_award = xp_integration.process_trade_result_for_xp(trade_result)
    if xp_award:
        print(f"✅ XP Award: {xp_award['reason']} (+{xp_award['xp_amount']} XP)")
    else:
        print("❌ No XP award for trade result")
    
    # Test winning streak
    print("\n🎯 Testing winning streak XP...")
    
    for i in range(3):
        trade_result['signal_id'] = f'VENOM_EURUSD_{i:03d}_user_test_user_001'
        xp_award = xp_integration.process_trade_result_for_xp(trade_result)
        if xp_award and 'streak' in xp_award['reason']:
            print(f"✅ Streak Award: {xp_award['reason']} (+{xp_award['xp_amount']} XP)")
    
    print("\n" + "="*50)
    print("✅ XP Integration test complete")

if __name__ == "__main__":
    test_xp_integration()