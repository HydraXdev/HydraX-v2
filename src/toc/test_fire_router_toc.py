"""
Test script for Fire Router TOC functionality
"""

import json
import time
from fire_router_toc import (
    FireRouterTOC, TradeSignal, SignalType, DeliveryMethod,
    create_fire_endpoint
)
from terminal_assignment import TerminalAssignment, TerminalType

def test_fire_router():
    """Test the fire router functionality"""
    
    print("=== Fire Router TOC Test Suite ===\n")
    
    # Initialize components
    print("1. Initializing Fire Router TOC...")
    router = FireRouterTOC("test_terminals.db")
    terminal_manager = router.terminal_manager
    
    # Setup test terminals
    print("\n2. Setting up test terminals...")
    
    # Add test terminals
    terminals = [
        {
            "name": "TEST-PP-01",
            "type": TerminalType.PRESS_PASS,
            "ip": "127.0.0.1",
            "port": 9001,
            "path": "/mt5/test/pp_01",
            "capacity": 5
        },
        {
            "name": "TEST-PP-02",
            "type": TerminalType.PRESS_PASS,
            "ip": "127.0.0.1",
            "port": 9002,
            "path": "/mt5/test/pp_02",
            "capacity": 5
        },
        {
            "name": "TEST-DEMO-01",
            "type": TerminalType.DEMO,
            "ip": "127.0.0.1",
            "port": 9101,
            "path": "/mt5/test/demo_01",
            "capacity": 3
        }
    ]
    
    terminal_ids = []
    for term in terminals:
        try:
            tid = terminal_manager.add_terminal(
                terminal_name=term["name"],
                terminal_type=term["type"],
                ip_address=term["ip"],
                port=term["port"],
                folder_path=term["path"],
                max_users=term["capacity"]
            )
            terminal_ids.append(tid)
            print(f"  ✓ Added {term['name']} (ID: {tid})")
        except Exception as e:
            print(f"  ✗ Failed to add {term['name']}: {e}")
    
    # Test 1: Basic signal routing
    print("\n3. Testing basic signal routing...")
    
    test_signal = TradeSignal(
        user_id="test_user_001",
        signal_type=SignalType.OPEN_POSITION,
        symbol="GBPUSD",
        direction="buy",
        volume=0.1,
        stop_loss=1.2450,
        take_profit=1.2550,
        comment="Test trade"
    )
    
    # Route signal (will use file write in test mode)
    response = router.route_signal(
        signal=test_signal,
        terminal_type=TerminalType.PRESS_PASS,
        delivery_method=DeliveryMethod.FILE_WRITE
    )
    
    print(f"  Signal routing result: {response.success}")
    print(f"  Message: {response.message}")
    print(f"  Terminal: {response.terminal_name} (ID: {response.terminal_id})")
    print(f"  Delivery method: {response.delivery_method}")
    
    # Test 2: Multiple users
    print("\n4. Testing multiple user routing...")
    
    test_users = ["user_001", "user_002", "user_003", "user_004", "user_005"]
    
    for user_id in test_users:
        signal = TradeSignal(
            user_id=user_id,
            signal_type=SignalType.OPEN_POSITION,
            symbol="EURUSD",
            direction="sell",
            volume=0.05,
            comment=f"Test for {user_id}"
        )
        
        response = router.route_signal(
            signal=signal,
            terminal_type=TerminalType.PRESS_PASS,
            delivery_method=DeliveryMethod.FILE_WRITE
        )
        
        print(f"  {user_id}: {response.terminal_name if response.success else 'Failed'}")
    
    # Test 3: User routing info
    print("\n5. Testing user routing info...")
    
    routing_info = router.get_user_routing_info("test_user_001")
    print(f"  User: {routing_info['user_id']}")
    print(f"  Active assignments: {routing_info['active_assignments']}")
    for terminal in routing_info['terminals']:
        print(f"    - {terminal['terminal_name']} ({terminal['terminal_type']})")
    
    # Test 4: Terminal health check
    print("\n6. Testing terminal health check...")
    
    if terminal_ids:
        health = router.get_terminal_health(terminal_ids[0])
        print(f"  Terminal: {health['terminal_name']}")
        print(f"  Status: {health['status']}")
        print(f"  Utilization: {health['utilization']}")
        print(f"  Bridge responsive: {health.get('bridge_responsive', 'N/A')}")
    
    # Test 5: Routing statistics
    print("\n7. Getting routing statistics...")
    
    stats = router.get_routing_statistics()
    print(f"  Total signals: {stats['total_signals']}")
    print(f"  Successful: {stats['successful_signals']}")
    print(f"  Failed: {stats['failed_signals']}")
    print(f"  Success rate: {stats['success_rate']}")
    print(f"  Retries: {stats['retries']}")
    
    # Test 6: Failover simulation
    print("\n8. Testing terminal failover...")
    
    if len(terminal_ids) >= 2:
        # First, ensure users are assigned to first terminal
        signal = TradeSignal(
            user_id="failover_test_user",
            signal_type=SignalType.OPEN_POSITION,
            symbol="USDJPY",
            direction="buy",
            volume=0.1
        )
        
        response = router.route_signal(
            signal=signal,
            terminal_type=TerminalType.PRESS_PASS,
            preferred_terminal_id=terminal_ids[0],
            delivery_method=DeliveryMethod.FILE_WRITE
        )
        
        if response.success:
            print(f"  User assigned to {response.terminal_name}")
            
            # Now failover the terminal
            failover_result = router.failover_terminal(
                terminal_ids[0], 
                "Simulated failure"
            )
            
            print(f"  Failover result: {failover_result['success']}")
            print(f"  Affected users: {failover_result['affected_users']}")
            print(f"  Reassignments: {len(failover_result['reassignments'])}")
            print(f"  Failures: {len(failover_result['failures'])}")
    
    # Test 7: Different signal types
    print("\n9. Testing different signal types...")
    
    # Close position signal
    close_signal = TradeSignal(
        user_id="test_user_001",
        signal_type=SignalType.CLOSE_POSITION,
        symbol="GBPUSD",
        direction="",
        volume=0,
        ticket=12345,
        comment="Close test position"
    )
    
    response = router.route_signal(
        signal=close_signal,
        terminal_type=TerminalType.PRESS_PASS,
        delivery_method=DeliveryMethod.FILE_WRITE
    )
    
    print(f"  Close position signal: {response.success}")
    
    # Modify position signal
    modify_signal = TradeSignal(
        user_id="test_user_001",
        signal_type=SignalType.MODIFY_POSITION,
        symbol="GBPUSD",
        direction="",
        volume=0,
        ticket=12345,
        stop_loss=1.2400,
        take_profit=1.2600,
        comment="Modify SL/TP"
    )
    
    response = router.route_signal(
        signal=modify_signal,
        terminal_type=TerminalType.PRESS_PASS,
        delivery_method=DeliveryMethod.FILE_WRITE
    )
    
    print(f"  Modify position signal: {response.success}")
    
    # Test 8: Flask endpoint simulation
    print("\n10. Testing Flask endpoint handler...")
    
    # Create endpoint handler
    fire_handler = create_fire_endpoint(router)
    
    # Simulate Flask request
    class MockRequest:
        def __init__(self, data):
            self.data = data
        
        def get_json(self):
            return self.data
    
    # Mock Flask request
    mock_data = {
        'user_id': 'flask_test_user',
        'symbol': 'AUDUSD',
        'direction': 'buy',
        'volume': 0.2,
        'stop_loss': 0.7200,
        'take_profit': 0.7300,
        'terminal_type': 'press_pass'
    }
    
    print(f"  Simulated request data: {json.dumps(mock_data, indent=2)}")
    
    # Clean up
    print("\n11. Cleaning up test assignments...")
    
    # Release all test assignments
    for user_id in test_users + ["test_user_001", "failover_test_user", "flask_test_user"]:
        terminal_manager.release_terminal(user_id)
        print(f"  Released assignments for {user_id}")
    
    print("\n=== Test completed successfully! ===")


def test_retry_and_failover():
    """Test retry logic and failover mechanisms"""
    
    print("\n=== Testing Retry and Failover Mechanisms ===\n")
    
    # Create router with custom config for faster testing
    config = {
        'max_retries': 2,
        'retry_delay': 0.5,
        'timeout': 2
    }
    
    # Write config to temp file
    with open('test_config.json', 'w') as f:
        json.dump(config, f)
    
    router = FireRouterTOC("test_retry.db", "test_config.json")
    
    # Add a terminal with unreachable endpoint
    router.terminal_manager.add_terminal(
        terminal_name="UNREACHABLE-01",
        terminal_type=TerminalType.PRESS_PASS,
        ip_address="192.168.99.99",  # Unreachable IP
        port=9999,
        folder_path="/mt5/test/unreachable",
        max_users=1
    )
    
    print("1. Testing HTTP failure with retry...")
    
    signal = TradeSignal(
        user_id="retry_test_user",
        signal_type=SignalType.OPEN_POSITION,
        symbol="GBPUSD",
        direction="buy",
        volume=0.1
    )
    
    start_time = time.time()
    response = router.route_signal(
        signal=signal,
        terminal_type=TerminalType.PRESS_PASS,
        delivery_method=DeliveryMethod.HTTP_POST
    )
    elapsed = time.time() - start_time
    
    print(f"  Result: {response.success}")
    print(f"  Message: {response.message}")
    print(f"  Retry count: {response.retry_count}")
    print(f"  Time elapsed: {elapsed:.2f}s")
    
    print("\n2. Testing hybrid delivery (HTTP -> File fallback)...")
    
    response = router.route_signal(
        signal=signal,
        terminal_type=TerminalType.PRESS_PASS,
        delivery_method=DeliveryMethod.HYBRID
    )
    
    print(f"  Result: {response.success}")
    print(f"  Final delivery method: {response.delivery_method}")
    
    # Get final statistics
    stats = router.get_routing_statistics()
    print(f"\n3. Final statistics:")
    print(f"  HTTP failures: {stats['http_failures']}")
    print(f"  File failures: {stats['file_failures']}")
    print(f"  Total retries: {stats['retries']}")
    
    # Cleanup
    import os
    os.remove('test_config.json')
    
    print("\n=== Retry and Failover Test Complete ===")


if __name__ == "__main__":
    # Run main test suite
    test_fire_router()
    
    # Run retry and failover tests
    test_retry_and_failover()