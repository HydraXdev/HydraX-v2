"""
Test script for Terminal Assignment Manager
"""

import os
import tempfile
from terminal_assignment import TerminalAssignment, TerminalType, TerminalStatus


def test_terminal_assignment():
    """Test the terminal assignment functionality"""
    
    # Create a temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Initialize manager
        manager = TerminalAssignment(db_path)
        print("✓ Terminal Assignment Manager initialized")
        
        # Add terminals
        print("\n--- Adding Terminals ---")
        
        # Press Pass terminals
        pp1_id = manager.add_terminal(
            terminal_name="PP-Bridge-01",
            terminal_type=TerminalType.PRESS_PASS,
            ip_address="10.0.1.10",
            port=5000,
            folder_path="/mt5/press_pass/terminal_01",
            max_users=20,
            metadata={"server": "PressPassServer", "datacenter": "NY"}
        )
        print(f"✓ Added Press Pass terminal (ID: {pp1_id})")
        
        pp2_id = manager.add_terminal(
            terminal_name="PP-Bridge-02",
            terminal_type=TerminalType.PRESS_PASS,
            ip_address="10.0.1.11",
            port=5001,
            folder_path="/mt5/press_pass/terminal_02",
            max_users=20,
            metadata={"server": "PressPassServer", "datacenter": "London"}
        )
        print(f"✓ Added Press Pass terminal (ID: {pp2_id})")
        
        # Demo terminals
        demo_id = manager.add_terminal(
            terminal_name="Demo-Bridge-01",
            terminal_type=TerminalType.DEMO,
            ip_address="10.0.2.10",
            port=6000,
            folder_path="/mt5/demo/terminal_01",
            max_users=10,
            metadata={"server": "DemoServer", "datacenter": "NY"}
        )
        print(f"✓ Added Demo terminal (ID: {demo_id})")
        
        # Live terminal
        live_id = manager.add_terminal(
            terminal_name="Live-Bridge-01",
            terminal_type=TerminalType.LIVE,
            ip_address="10.0.3.10",
            port=7000,
            folder_path="/mt5/live/terminal_01",
            max_users=5,
            metadata={"server": "LiveServer", "datacenter": "NY", "security": "enhanced"}
        )
        print(f"✓ Added Live terminal (ID: {live_id})")
        
        # Test assignments
        print("\n--- Testing Assignments ---")
        
        # Assign press pass terminal to users
        users = ["alice123", "bob456", "charlie789"]
        for user in users:
            assignment = manager.assign_terminal(
                user_id=user,
                terminal_type=TerminalType.PRESS_PASS,
                metadata={"subscription": "premium", "trading_style": "scalping"}
            )
            if assignment:
                print(f"✓ Assigned {user} to {assignment['terminal_name']} "
                      f"(IP: {assignment['ip_address']}:{assignment['port']})")
        
        # Try to assign demo terminal
        demo_assignment = manager.assign_terminal(
            user_id="demo_user",
            terminal_type=TerminalType.DEMO,
            metadata={"trial_days": 30}
        )
        if demo_assignment:
            print(f"✓ Assigned demo_user to {demo_assignment['terminal_name']}")
        
        # Check user assignments
        print("\n--- User Assignments ---")
        alice_assignments = manager.get_user_assignments("alice123")
        for assign in alice_assignments:
            print(f"User alice123: {assign['terminal_name']} ({assign['terminal_type']})")
        
        # Check available terminals
        print("\n--- Available Terminals ---")
        available = manager.get_available_terminals()
        for terminal in available:
            print(f"{terminal['terminal_name']}: {terminal['available_slots']} slots available")
        
        # Get statistics
        print("\n--- Statistics ---")
        stats = manager.get_statistics()
        print(f"Terminals by type: {stats['terminals_by_type']}")
        print(f"Active assignments by type: {stats['active_assignments_by_type']}")
        print(f"Utilization: {stats['utilization']['used_capacity']}/{stats['utilization']['total_capacity']} "
              f"({stats['utilization']['used_capacity']/stats['utilization']['total_capacity']*100:.1f}%)")
        
        # Test release
        print("\n--- Testing Release ---")
        released = manager.release_terminal("alice123", terminal_type=TerminalType.PRESS_PASS)
        if released:
            print("✓ Released alice123's press pass terminal")
        
        # Check assignment history
        print("\n--- Assignment History ---")
        history = manager.get_assignment_history(user_id="alice123", limit=5)
        for record in history:
            print(f"{record['timestamp']}: {record['user_id']} - {record['action']} - {record['terminal_name']}")
        
        # Test terminal status update
        print("\n--- Terminal Status Update ---")
        manager.update_terminal_status(demo_id, TerminalStatus.MAINTENANCE)
        print(f"✓ Set Demo-Bridge-01 to maintenance mode")
        
        # Try to assign to maintenance terminal
        maintenance_assign = manager.assign_terminal(
            user_id="test_user",
            terminal_type=TerminalType.DEMO
        )
        if not maintenance_assign:
            print("✓ Correctly prevented assignment to maintenance terminal")
        
        # Get terminal info
        print("\n--- Terminal Information ---")
        terminal_info = manager.get_terminal_info(pp1_id)
        if terminal_info:
            print(f"Terminal: {terminal_info['terminal_name']}")
            print(f"  Type: {terminal_info['terminal_type']}")
            print(f"  Status: {terminal_info['status']}")
            print(f"  Active Users: {terminal_info['active_users']}/{terminal_info['max_users']}")
            print(f"  Bridge: {terminal_info['ip_address']}:{terminal_info['port']}")
            print(f"  Path: {terminal_info['folder_path']}")
        
        print("\n✓ All tests completed successfully!")
        
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)
            print("\n✓ Cleaned up test database")


if __name__ == "__main__":
    test_terminal_assignment()