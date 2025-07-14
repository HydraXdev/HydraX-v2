#!/usr/bin/env python3
"""
Shepherd CLI Interface for HydraX-v2
Command-line interface for tracing connections, explaining triggers, and managing system state.
"""

import argparse
import json
import sys
from typing import Optional, Dict, Any, List
from datetime import datetime
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class ShepherdCLI:
    """Command-line interface for the Shepherd system."""
    
    def __init__(self):
        self.state_file = "/root/HydraX-v2/bitten/data/shepherd/state.json"
        self.checkpoint_dir = "/root/HydraX-v2/bitten/data/shepherd/checkpoints"
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure required directories exist."""
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        os.makedirs(self.checkpoint_dir, exist_ok=True)
    
    def trace(self, module: str) -> Dict[str, Any]:
        """
        Show connections for a specific module.
        
        Args:
            module: Module name to trace
            
        Returns:
            Dictionary containing module connections and dependencies
        """
        print(f"\n🔍 Tracing connections for module: {module}")
        
        # Mock implementation - replace with actual logic
        connections = {
            "module": module,
            "timestamp": datetime.now().isoformat(),
            "inbound_connections": [
                {"from": "risk_controller", "type": "validation", "priority": "high"},
                {"from": "signal_processor", "type": "data", "priority": "medium"}
            ],
            "outbound_connections": [
                {"to": "trade_executor", "type": "command", "priority": "high"},
                {"to": "notification_handler", "type": "event", "priority": "low"}
            ],
            "dependencies": [
                "config_manager",
                "database_connection",
                "logging_system"
            ],
            "status": "active",
            "health": "healthy"
        }
        
        self._display_connections(connections)
        return connections
    
    def why(self, trigger: str) -> Dict[str, Any]:
        """
        Explain the trigger chain for a specific event.
        
        Args:
            trigger: Trigger event to explain
            
        Returns:
            Dictionary containing trigger chain explanation
        """
        print(f"\n❓ Explaining trigger chain for: {trigger}")
        
        # Mock implementation - replace with actual logic
        chain = {
            "trigger": trigger,
            "timestamp": datetime.now().isoformat(),
            "chain": [
                {
                    "step": 1,
                    "component": "market_scanner",
                    "action": "Detected price movement > 2%",
                    "output": "price_alert"
                },
                {
                    "step": 2,
                    "component": "risk_filter",
                    "action": "Validated against risk parameters",
                    "output": "risk_approved"
                },
                {
                    "step": 3,
                    "component": "signal_generator",
                    "action": "Generated trading signal",
                    "output": trigger
                }
            ],
            "root_cause": "Market volatility spike",
            "impact": "High priority trading signal generated"
        }
        
        self._display_trigger_chain(chain)
        return chain
    
    def doc(self, function: str) -> Dict[str, Any]:
        """
        Get documentation for a specific function.
        
        Args:
            function: Function name to document
            
        Returns:
            Dictionary containing function documentation
        """
        print(f"\n📚 Documentation for function: {function}")
        
        # Mock implementation - replace with actual logic
        documentation = {
            "function": function,
            "module": "bitten.core.signal_processor",
            "signature": f"def {function}(data: Dict[str, Any], config: Optional[Dict] = None) -> Dict[str, Any]",
            "description": "Process incoming market data and generate trading signals based on configured strategies.",
            "parameters": {
                "data": "Dictionary containing market data with keys: symbol, price, volume, timestamp",
                "config": "Optional configuration dictionary for custom processing parameters"
            },
            "returns": "Dictionary containing processed signal with keys: action, confidence, metadata",
            "raises": [
                "ValueError: If data is missing required fields",
                "ConnectionError: If unable to connect to data source"
            ],
            "example": """
# Example usage
data = {"symbol": "EURUSD", "price": 1.1234, "volume": 1000, "timestamp": "2025-07-11T10:00:00Z"}
result = process_signal(data, config={"threshold": 0.02})
print(result)  # {"action": "BUY", "confidence": 0.85, "metadata": {...}}
            """.strip()
        }
        
        self._display_documentation(documentation)
        return documentation
    
    def simulate(self, change: str) -> Dict[str, Any]:
        """
        Test impact of a proposed change.
        
        Args:
            change: Description of the change to simulate
            
        Returns:
            Dictionary containing simulation results
        """
        print(f"\n🧪 Simulating change: {change}")
        
        # Mock implementation - replace with actual logic
        simulation = {
            "change": change,
            "timestamp": datetime.now().isoformat(),
            "impact_analysis": {
                "affected_modules": [
                    {"module": "risk_controller", "impact": "medium", "description": "Risk thresholds will need adjustment"},
                    {"module": "signal_processor", "impact": "high", "description": "Signal generation logic will be modified"},
                    {"module": "notification_handler", "impact": "low", "description": "New notification type may be needed"}
                ],
                "performance_impact": {
                    "latency": "+2ms average",
                    "throughput": "No significant change",
                    "resource_usage": "+5% CPU during peak"
                },
                "risk_assessment": {
                    "level": "medium",
                    "factors": [
                        "Change affects core trading logic",
                        "Backward compatibility maintained",
                        "Rollback strategy available"
                    ]
                }
            },
            "recommendations": [
                "Run comprehensive test suite before deployment",
                "Monitor system closely for first 24 hours",
                "Keep rollback plan ready"
            ],
            "simulation_status": "completed"
        }
        
        self._display_simulation_results(simulation)
        return simulation
    
    def checkpoint(self, label: str) -> Dict[str, Any]:
        """
        Save current system state with a label.
        
        Args:
            label: Label for the checkpoint
            
        Returns:
            Dictionary containing checkpoint information
        """
        print(f"\n💾 Creating checkpoint: {label}")
        
        timestamp = datetime.now()
        checkpoint_id = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{label.replace(' ', '_')}"
        checkpoint_file = os.path.join(self.checkpoint_dir, f"{checkpoint_id}.json")
        
        # Mock implementation - replace with actual state capture
        checkpoint_data = {
            "id": checkpoint_id,
            "label": label,
            "timestamp": timestamp.isoformat(),
            "system_state": {
                "active_modules": ["risk_controller", "signal_processor", "trade_executor"],
                "configuration": {
                    "risk_level": "medium",
                    "signal_threshold": 0.75,
                    "max_positions": 5
                },
                "performance_metrics": {
                    "uptime": "48h 23m",
                    "signals_processed": 1543,
                    "success_rate": 0.67
                }
            },
            "metadata": {
                "created_by": "shepherd_cli",
                "version": "1.0.0",
                "environment": "production"
            }
        }
        
        # Save checkpoint
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        print(f"✅ Checkpoint saved: {checkpoint_file}")
        
        # Update list of checkpoints
        self._update_checkpoint_index(checkpoint_id, label)
        
        return checkpoint_data
    
    def _display_connections(self, connections: Dict[str, Any]):
        """Display module connections in a formatted way."""
        print(f"\nModule: {connections['module']}")
        print(f"Status: {connections['status']} | Health: {connections['health']}")
        
        print("\n📥 Inbound Connections:")
        for conn in connections['inbound_connections']:
            print(f"  ← {conn['from']} ({conn['type']}) - Priority: {conn['priority']}")
        
        print("\n📤 Outbound Connections:")
        for conn in connections['outbound_connections']:
            print(f"  → {conn['to']} ({conn['type']}) - Priority: {conn['priority']}")
        
        print("\n🔗 Dependencies:")
        for dep in connections['dependencies']:
            print(f"  • {dep}")
    
    def _display_trigger_chain(self, chain: Dict[str, Any]):
        """Display trigger chain in a formatted way."""
        print(f"\n🔗 Trigger Chain Analysis")
        print(f"Root Cause: {chain['root_cause']}")
        print(f"Impact: {chain['impact']}")
        
        print("\n📊 Chain of Events:")
        for step in chain['chain']:
            print(f"\n  Step {step['step']}: {step['component']}")
            print(f"  Action: {step['action']}")
            print(f"  Output: {step['output']}")
    
    def _display_documentation(self, doc: Dict[str, Any]):
        """Display function documentation in a formatted way."""
        print(f"\nFunction: {doc['function']}")
        print(f"Module: {doc['module']}")
        print(f"\nSignature:\n  {doc['signature']}")
        print(f"\nDescription:\n  {doc['description']}")
        
        print("\nParameters:")
        for param, desc in doc['parameters'].items():
            print(f"  {param}: {desc}")
        
        print(f"\nReturns:\n  {doc['returns']}")
        
        if doc['raises']:
            print("\nRaises:")
            for exc in doc['raises']:
                print(f"  {exc}")
        
        print(f"\nExample:\n{doc['example']}")
    
    def _display_simulation_results(self, simulation: Dict[str, Any]):
        """Display simulation results in a formatted way."""
        impact = simulation['impact_analysis']
        
        print("\n🎯 Affected Modules:")
        for module in impact['affected_modules']:
            print(f"  • {module['module']} - Impact: {module['impact']}")
            print(f"    {module['description']}")
        
        print("\n⚡ Performance Impact:")
        for metric, value in impact['performance_impact'].items():
            print(f"  • {metric}: {value}")
        
        print(f"\n⚠️  Risk Level: {impact['risk_assessment']['level']}")
        print("Risk Factors:")
        for factor in impact['risk_assessment']['factors']:
            print(f"  • {factor}")
        
        print("\n💡 Recommendations:")
        for rec in simulation['recommendations']:
            print(f"  • {rec}")
    
    def _update_checkpoint_index(self, checkpoint_id: str, label: str):
        """Update the checkpoint index file."""
        index_file = os.path.join(self.checkpoint_dir, "index.json")
        
        try:
            with open(index_file, 'r') as f:
                index = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            index = {"checkpoints": []}
        
        index["checkpoints"].append({
            "id": checkpoint_id,
            "label": label,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 50 checkpoints
        index["checkpoints"] = index["checkpoints"][-50:]
        
        with open(index_file, 'w') as f:
            json.dump(index, f, indent=2)


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Shepherd CLI - HydraX-v2 System Management Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  shepherd trace risk_controller          # Show connections for risk_controller module
  shepherd why "high_volatility_signal"   # Explain what triggered high_volatility_signal
  shepherd doc process_signal             # Get documentation for process_signal function
  shepherd simulate "increase risk limit" # Test impact of increasing risk limit
  shepherd checkpoint "before upgrade"    # Save current state before system upgrade
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Trace command
    trace_parser = subparsers.add_parser('trace', help='Show connections for a module')
    trace_parser.add_argument('module', help='Module name to trace')
    
    # Why command
    why_parser = subparsers.add_parser('why', help='Explain trigger chain')
    why_parser.add_argument('trigger', help='Trigger event to explain')
    
    # Doc command
    doc_parser = subparsers.add_parser('doc', help='Get function documentation')
    doc_parser.add_argument('function', help='Function name to document')
    
    # Simulate command
    simulate_parser = subparsers.add_parser('simulate', help='Test impact of changes')
    simulate_parser.add_argument('change', help='Description of change to simulate')
    
    # Checkpoint command
    checkpoint_parser = subparsers.add_parser('checkpoint', help='Save system state')
    checkpoint_parser.add_argument('label', help='Label for the checkpoint')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    cli = ShepherdCLI()
    
    try:
        if args.command == 'trace':
            cli.trace(args.module)
        elif args.command == 'why':
            cli.why(args.trigger)
        elif args.command == 'doc':
            cli.doc(args.function)
        elif args.command == 'simulate':
            cli.simulate(args.change)
        elif args.command == 'checkpoint':
            cli.checkpoint(args.label)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()