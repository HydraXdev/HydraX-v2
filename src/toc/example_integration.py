"""
Example integration of Terminal Assignment Manager with MT5 Bridge System

This example shows how to integrate the terminal assignment system with
the existing MT5 bridge infrastructure.
"""

import asyncio
import json
from typing import Dict, Optional
from terminal_assignment import TerminalAssignment, TerminalType, TerminalStatus


class BridgeConnectionManager:
    """Manages bridge connections using the terminal assignment system"""
    
    def __init__(self, db_path: str = "production_terminals.db"):
        self.terminal_manager = TerminalAssignment(db_path)
        self.active_connections = {}
        
    async def connect_user_to_terminal(self, user_id: str, terminal_type: TerminalType) -> Optional[Dict]:
        """
        Connect a user to an available terminal
        
        Args:
            user_id: User identifier
            terminal_type: Type of terminal needed
            
        Returns:
            Connection details or None if no terminal available
        """
        # Get terminal assignment
        assignment = self.terminal_manager.assign_terminal(
            user_id=user_id,
            terminal_type=terminal_type,
            metadata={
                "connection_timestamp": asyncio.get_event_loop().time(),
                "client_version": "2.0"
            }
        )
        
        if not assignment:
            print(f"No available {terminal_type.value} terminal for user {user_id}")
            return None
            
        # Simulate establishing bridge connection
        connection_key = f"{user_id}:{assignment['terminal_id']}"
        self.active_connections[connection_key] = {
            "assignment": assignment,
            "connected_at": asyncio.get_event_loop().time(),
            "status": "connected"
        }
        
        print(f"Connected {user_id} to {assignment['terminal_name']} "
              f"at {assignment['ip_address']}:{assignment['port']}")
        
        return {
            "success": True,
            "terminal_name": assignment['terminal_name'],
            "bridge_address": f"{assignment['ip_address']}:{assignment['port']}",
            "folder_path": assignment['folder_path'],
            "connection_id": connection_key
        }
    
    async def disconnect_user(self, user_id: str, terminal_id: Optional[int] = None) -> bool:
        """
        Disconnect a user from their terminal
        
        Args:
            user_id: User identifier
            terminal_id: Optional specific terminal to disconnect from
            
        Returns:
            True if successfully disconnected
        """
        # Find and remove active connections
        keys_to_remove = []
        for key, conn in self.active_connections.items():
            if key.startswith(f"{user_id}:"):
                if terminal_id is None or str(terminal_id) in key:
                    keys_to_remove.append(key)
                    
        for key in keys_to_remove:
            del self.active_connections[key]
            
        # Release terminal assignment
        released = self.terminal_manager.release_terminal(user_id, terminal_id)
        
        if released:
            print(f"Disconnected {user_id} from terminal")
            
        return released
    
    async def handle_terminal_failure(self, terminal_id: int):
        """
        Handle a terminal failure by reassigning affected users
        
        Args:
            terminal_id: ID of the failed terminal
        """
        print(f"Handling failure for terminal {terminal_id}")
        
        # Mark terminal as error state
        self.terminal_manager.update_terminal_status(terminal_id, TerminalStatus.ERROR)
        
        # Get all affected users
        assignments = self.terminal_manager.get_terminal_assignments(terminal_id)
        
        for assignment in assignments:
            user_id = assignment['user_id']
            terminal_type = TerminalType(assignment['terminal_type'])
            
            # Release the failed assignment
            self.terminal_manager.release_terminal(user_id, terminal_id)
            
            # Try to reassign to another terminal
            print(f"Attempting to reassign {user_id}...")
            new_connection = await self.connect_user_to_terminal(user_id, terminal_type)
            
            if new_connection:
                print(f"Successfully reassigned {user_id}")
            else:
                print(f"Failed to reassign {user_id} - no terminals available")
                # Here you would notify the user or queue for retry
    
    def get_user_connection_info(self, user_id: str) -> Dict:
        """Get current connection information for a user"""
        assignments = self.terminal_manager.get_user_assignments(user_id)
        connections = []
        
        for assignment in assignments:
            connection_key = f"{user_id}:{assignment['terminal_id']}"
            if connection_key in self.active_connections:
                connections.append({
                    "terminal": assignment['terminal_name'],
                    "type": assignment['terminal_type'],
                    "bridge": f"{assignment['ip_address']}:{assignment['port']}",
                    "status": self.active_connections[connection_key]['status']
                })
                
        return {
            "user_id": user_id,
            "connections": connections,
            "connection_count": len(connections)
        }
    
    def initialize_production_terminals(self):
        """Initialize production terminals - run once during setup"""
        
        # Press Pass Terminals (High Capacity)
        terminals = [
            {
                "name": "PP-NYC-01",
                "type": TerminalType.PRESS_PASS,
                "ip": "10.10.1.10",
                "port": 5000,
                "path": "/mt5/production/press_pass/nyc_01",
                "capacity": 50,
                "meta": {"datacenter": "NYC", "provider": "AWS", "tier": "premium"}
            },
            {
                "name": "PP-NYC-02",
                "type": TerminalType.PRESS_PASS,
                "ip": "10.10.1.11",
                "port": 5001,
                "path": "/mt5/production/press_pass/nyc_02",
                "capacity": 50,
                "meta": {"datacenter": "NYC", "provider": "AWS", "tier": "premium"}
            },
            {
                "name": "PP-LON-01",
                "type": TerminalType.PRESS_PASS,
                "ip": "10.20.1.10",
                "port": 5000,
                "path": "/mt5/production/press_pass/lon_01",
                "capacity": 40,
                "meta": {"datacenter": "London", "provider": "AWS", "tier": "premium"}
            },
            
            # Demo Terminals (Medium Capacity)
            {
                "name": "DEMO-NYC-01",
                "type": TerminalType.DEMO,
                "ip": "10.10.2.10",
                "port": 6000,
                "path": "/mt5/production/demo/nyc_01",
                "capacity": 30,
                "meta": {"datacenter": "NYC", "provider": "AWS", "tier": "standard"}
            },
            {
                "name": "DEMO-LON-01",
                "type": TerminalType.DEMO,
                "ip": "10.20.2.10",
                "port": 6000,
                "path": "/mt5/production/demo/lon_01",
                "capacity": 25,
                "meta": {"datacenter": "London", "provider": "AWS", "tier": "standard"}
            },
            
            # Live Terminals (Low Capacity, High Security)
            {
                "name": "LIVE-NYC-01",
                "type": TerminalType.LIVE,
                "ip": "10.10.3.10",
                "port": 7000,
                "path": "/mt5/production/live/nyc_01",
                "capacity": 10,
                "meta": {"datacenter": "NYC", "provider": "AWS", "tier": "ultra", "security": "enhanced"}
            },
            {
                "name": "LIVE-NYC-02",
                "type": TerminalType.LIVE,
                "ip": "10.10.3.11",
                "port": 7001,
                "path": "/mt5/production/live/nyc_02",
                "capacity": 10,
                "meta": {"datacenter": "NYC", "provider": "AWS", "tier": "ultra", "security": "enhanced"}
            }
        ]
        
        for terminal in terminals:
            try:
                terminal_id = self.terminal_manager.add_terminal(
                    terminal_name=terminal["name"],
                    terminal_type=terminal["type"],
                    ip_address=terminal["ip"],
                    port=terminal["port"],
                    folder_path=terminal["path"],
                    max_users=terminal["capacity"],
                    metadata=terminal["meta"]
                )
                print(f"✓ Added terminal: {terminal['name']} (ID: {terminal_id})")
            except Exception as e:
                print(f"✗ Failed to add terminal {terminal['name']}: {e}")


async def example_usage():
    """Example usage of the bridge connection manager"""
    
    # Initialize manager
    manager = BridgeConnectionManager("example_terminals.db")
    
    # Initialize production terminals (run once)
    print("=== Initializing Production Terminals ===")
    manager.initialize_production_terminals()
    
    # Simulate user connections
    print("\n=== Simulating User Connections ===")
    
    # Press Pass users
    pp_users = ["trader_001", "trader_002", "trader_003", "trader_004", "trader_005"]
    for user in pp_users:
        result = await manager.connect_user_to_terminal(user, TerminalType.PRESS_PASS)
        if result:
            print(f"  ✓ {user}: Connected to {result['terminal_name']}")
    
    # Demo users
    demo_users = ["demo_user_01", "demo_user_02"]
    for user in demo_users:
        result = await manager.connect_user_to_terminal(user, TerminalType.DEMO)
        if result:
            print(f"  ✓ {user}: Connected to {result['terminal_name']}")
    
    # Live user
    live_result = await manager.connect_user_to_terminal("live_trader_vip", TerminalType.LIVE)
    if live_result:
        print(f"  ✓ live_trader_vip: Connected to {live_result['terminal_name']}")
    
    # Check connection info
    print("\n=== User Connection Info ===")
    info = manager.get_user_connection_info("trader_001")
    print(f"User: {info['user_id']}")
    for conn in info['connections']:
        print(f"  - {conn['terminal']} ({conn['type']}): {conn['bridge']}")
    
    # Get statistics
    print("\n=== System Statistics ===")
    stats = manager.terminal_manager.get_statistics()
    print(f"Terminals: {stats['terminals_by_type']}")
    print(f"Active Assignments: {stats['active_assignments_by_type']}")
    utilization = stats['utilization']
    print(f"Overall Utilization: {utilization['used_capacity']}/{utilization['total_capacity']} "
          f"({utilization['used_capacity']/utilization['total_capacity']*100:.1f}%)")
    
    # Simulate terminal failure
    print("\n=== Simulating Terminal Failure ===")
    # Get NYC Press Pass terminal ID
    terminals = manager.terminal_manager.get_available_terminals(TerminalType.PRESS_PASS)
    if terminals:
        failed_terminal = next((t for t in terminals if "NYC-01" in t['terminal_name']), None)
        if failed_terminal:
            await manager.handle_terminal_failure(failed_terminal['terminal_id'])
    
    # Disconnect a user
    print("\n=== Disconnecting User ===")
    await manager.disconnect_user("trader_001")
    
    # Cleanup stale assignments (24+ hours old)
    print("\n=== Cleanup Stale Assignments ===")
    cleaned = manager.terminal_manager.cleanup_stale_assignments(hours=24)
    print(f"Cleaned up {cleaned} stale assignments")
    
    print("\n✓ Example completed successfully!")


if __name__ == "__main__":
    # Run the example
    asyncio.run(example_usage())