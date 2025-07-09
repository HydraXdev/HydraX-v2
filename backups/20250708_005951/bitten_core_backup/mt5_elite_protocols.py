"""
MT5 Elite Protocol Commands for BITTEN
Extends MT5 bridge to support XP-purchased trading features
"""

import json
import logging
from typing import Dict, Optional, Tuple, Any, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ProtocolCommand(Enum):
    """Elite protocol MT5 commands"""
    TRAIL_STOP = "TRAIL_STOP"
    PARTIAL_CLOSE = "PARTIAL_CLOSE"
    MOVE_TO_BREAKEVEN = "MOVE_TO_BE"
    PLACE_PENDING = "PLACE_PENDING"
    MODIFY_RISK = "MODIFY_RISK"
    CHECK_POSITION = "CHECK_POSITION"


@dataclass
class ProtocolInstruction:
    """Protocol instruction for MT5"""
    command: ProtocolCommand
    ticket: int
    params: Dict[str, Any]
    protocol_id: str
    
    def to_json(self) -> str:
        """Convert to JSON for MT5"""
        return json.dumps({
            "command": self.command.value,
            "ticket": self.ticket,
            "params": self.params,
            "protocol_id": self.protocol_id,
            "timestamp": datetime.now().isoformat()
        })


class MT5EliteProtocolBridge:
    """Bridge for executing elite protocol commands in MT5"""
    
    def __init__(self, bridge_adapter):
        """
        Initialize with existing MT5 bridge adapter
        
        Args:
            bridge_adapter: MT5BridgeAdapter instance
        """
        self.bridge = bridge_adapter
        self.protocol_file = "bitten_protocols.json"
        self.protocol_result_file = "bitten_protocol_results.json"
    
    def execute_trailing_guard(
        self,
        ticket: int,
        current_profit_pips: float,
        new_sl_distance_pips: float,
        symbol: str
    ) -> Tuple[bool, str]:
        """
        Execute trailing stop modification
        
        Args:
            ticket: Position ticket number
            current_profit_pips: Current profit in pips
            new_sl_distance_pips: New SL distance from current price
            symbol: Trading symbol
        """
        instruction = ProtocolInstruction(
            command=ProtocolCommand.TRAIL_STOP,
            ticket=ticket,
            params={
                "current_profit_pips": current_profit_pips,
                "trail_distance_pips": new_sl_distance_pips,
                "symbol": symbol
            },
            protocol_id=f"TG_{ticket}_{datetime.now().timestamp()}"
        )
        
        # Write instruction
        instruction_path = f"{self.bridge.mt5_files_path}/{self.protocol_file}"
        try:
            with open(instruction_path, 'w') as f:
                f.write(instruction.to_json())
            
            logger.info(f"Trailing guard instruction sent for ticket {ticket}")
            
            # Wait for result
            result = self._wait_for_protocol_result(instruction.protocol_id)
            
            if result and result.get("success"):
                return True, f"Stop loss trailed to {result.get('new_sl')}"
            else:
                return False, result.get("error", "Failed to trail stop loss")
                
        except Exception as e:
            logger.error(f"Error executing trailing guard: {e}")
            return False, str(e)
    
    def execute_split_command(
        self,
        ticket: int,
        close_percent: float,
        move_to_breakeven: bool,
        new_tp_pips: float,
        symbol: str
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Execute partial close with optional breakeven
        
        Args:
            ticket: Position ticket number
            close_percent: Percentage to close (0.5 = 50%)
            move_to_breakeven: Whether to move SL to breakeven
            new_tp_pips: New TP for remaining position
            symbol: Trading symbol
        """
        instruction = ProtocolInstruction(
            command=ProtocolCommand.PARTIAL_CLOSE,
            ticket=ticket,
            params={
                "close_percent": close_percent,
                "move_to_breakeven": move_to_breakeven,
                "new_tp_pips": new_tp_pips,
                "symbol": symbol
            },
            protocol_id=f"SC_{ticket}_{datetime.now().timestamp()}"
        )
        
        # Write instruction
        instruction_path = f"{self.bridge.mt5_files_path}/{self.protocol_file}"
        try:
            with open(instruction_path, 'w') as f:
                f.write(instruction.to_json())
            
            logger.info(f"Split command instruction sent for ticket {ticket}")
            
            # Wait for result
            result = self._wait_for_protocol_result(instruction.protocol_id)
            
            if result and result.get("success"):
                return True, "Split command executed", {
                    "closed_volume": result.get("closed_volume"),
                    "remaining_volume": result.get("remaining_volume"),
                    "profit_closed": result.get("profit_closed"),
                    "new_sl": result.get("new_sl"),
                    "new_tp": result.get("new_tp")
                }
            else:
                return False, result.get("error", "Failed to execute split command"), None
                
        except Exception as e:
            logger.error(f"Error executing split command: {e}")
            return False, str(e), None
    
    def place_stealth_orders(
        self,
        symbol: str,
        orders: List[Dict[str, Any]]
    ) -> Tuple[bool, str, List[int]]:
        """
        Place stealth entry orders
        
        Args:
            symbol: Trading symbol
            orders: List of order configurations
        """
        order_tickets = []
        
        for order in orders:
            instruction = ProtocolInstruction(
                command=ProtocolCommand.PLACE_PENDING,
                ticket=0,  # No existing ticket for new orders
                params={
                    "symbol": symbol,
                    "type": order["type"],
                    "price": order["price"],
                    "volume": order.get("volume", 0.01),
                    "sl": order.get("sl", 0),
                    "tp": order.get("tp", 0),
                    "expiration": order["expiration"].isoformat() if order.get("expiration") else None,
                    "comment": "BITTEN_STEALTH"
                },
                protocol_id=f"SE_{symbol}_{datetime.now().timestamp()}"
            )
            
            # Write instruction
            instruction_path = f"{self.bridge.mt5_files_path}/{self.protocol_file}"
            try:
                with open(instruction_path, 'w') as f:
                    f.write(instruction.to_json())
                
                # Wait for result
                result = self._wait_for_protocol_result(instruction.protocol_id)
                
                if result and result.get("success"):
                    order_tickets.append(result.get("ticket"))
                else:
                    logger.error(f"Failed to place stealth order: {result.get('error')}")
                    
            except Exception as e:
                logger.error(f"Error placing stealth order: {e}")
        
        if order_tickets:
            return True, f"Placed {len(order_tickets)} stealth orders", order_tickets
        else:
            return False, "Failed to place any stealth orders", []
    
    def modify_position_risk(
        self,
        ticket: int,
        new_risk_percent: float,
        symbol: str,
        account_balance: float
    ) -> Tuple[bool, str]:
        """
        Modify position size based on new risk percentage
        Used for special ammo (3% risk)
        """
        instruction = ProtocolInstruction(
            command=ProtocolCommand.MODIFY_RISK,
            ticket=ticket,
            params={
                "new_risk_percent": new_risk_percent,
                "symbol": symbol,
                "account_balance": account_balance
            },
            protocol_id=f"MR_{ticket}_{datetime.now().timestamp()}"
        )
        
        # Write instruction
        instruction_path = f"{self.bridge.mt5_files_path}/{self.protocol_file}"
        try:
            with open(instruction_path, 'w') as f:
                f.write(instruction.to_json())
            
            logger.info(f"Risk modification sent for ticket {ticket}: {new_risk_percent}%")
            
            # Wait for result
            result = self._wait_for_protocol_result(instruction.protocol_id)
            
            if result and result.get("success"):
                return True, f"Risk modified to {new_risk_percent}%"
            else:
                return False, result.get("error", "Failed to modify risk")
                
        except Exception as e:
            logger.error(f"Error modifying risk: {e}")
            return False, str(e)
    
    def check_position_status(
        self,
        ticket: int
    ) -> Optional[Dict[str, Any]]:
        """
        Check current status of a position
        """
        instruction = ProtocolInstruction(
            command=ProtocolCommand.CHECK_POSITION,
            ticket=ticket,
            params={},
            protocol_id=f"CP_{ticket}_{datetime.now().timestamp()}"
        )
        
        # Write instruction
        instruction_path = f"{self.bridge.mt5_files_path}/{self.protocol_file}"
        try:
            with open(instruction_path, 'w') as f:
                f.write(instruction.to_json())
            
            # Wait for result
            result = self._wait_for_protocol_result(instruction.protocol_id)
            
            if result and result.get("success"):
                return result.get("position")
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error checking position: {e}")
            return None
    
    def _wait_for_protocol_result(
        self,
        protocol_id: str,
        timeout: int = 10
    ) -> Optional[Dict[str, Any]]:
        """Wait for protocol execution result"""
        import time
        result_path = f"{self.bridge.mt5_files_path}/{self.protocol_result_file}"
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                if os.path.exists(result_path):
                    with open(result_path, 'r') as f:
                        results = json.load(f)
                    
                    # Check if our protocol result is there
                    if protocol_id in results:
                        result = results[protocol_id]
                        
                        # Remove our result and rewrite file
                        del results[protocol_id]
                        if results:
                            with open(result_path, 'w') as f:
                                json.dump(results, f)
                        else:
                            os.remove(result_path)
                        
                        return result
                        
            except Exception as e:
                logger.error(f"Error reading protocol result: {e}")
            
            time.sleep(0.5)
        
        logger.warning(f"Timeout waiting for protocol result: {protocol_id}")
        return None


# Protocol execution wrapper for integration
class ProtocolExecutor:
    """High-level protocol executor that integrates with XP system"""
    
    def __init__(self, bridge_adapter, xp_integration, elite_protocols):
        self.mt5_protocols = MT5EliteProtocolBridge(bridge_adapter)
        self.xp_integration = xp_integration
        self.elite_protocols = elite_protocols
    
    def execute_user_protocols(
        self,
        user_id: str,
        position_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute all applicable protocols for a user's position
        
        Args:
            user_id: User ID
            position_data: Current position data including:
                - ticket: MT5 ticket number
                - symbol: Trading symbol
                - profit_pips: Current profit in pips
                - sl_pips: Current SL distance
                - tp_pips: TP distance
                - trade_id: Internal trade ID
        """
        results = {}
        
        ticket = position_data["ticket"]
        symbol = position_data["symbol"]
        profit_pips = position_data["profit_pips"]
        
        # Check trailing guard
        new_sl = self.elite_protocols.check_trailing_guard(
            user_id,
            position_data["trade_id"],
            profit_pips,
            position_data["sl_pips"]
        )
        
        if new_sl:
            success, message = self.mt5_protocols.execute_trailing_guard(
                ticket,
                profit_pips,
                new_sl,
                symbol
            )
            results["trailing_guard"] = {
                "executed": success,
                "message": message
            }
        
        # Check split command
        split_action = self.elite_protocols.check_split_command(
            user_id,
            position_data["trade_id"],
            profit_pips,
            position_data["tp_pips"]
        )
        
        if split_action:
            success, message, details = self.mt5_protocols.execute_split_command(
                ticket,
                split_action["close_percent"],
                split_action["move_sl_to_breakeven"],
                split_action["new_tp"],
                symbol
            )
            results["split_command"] = {
                "executed": success,
                "message": message,
                "details": details
            }
        
        return results
    
    def prepare_special_ammo_trade(
        self,
        user_id: str,
        base_volume: float,
        symbol: str,
        account_balance: float
    ) -> Tuple[bool, float]:
        """
        Prepare trade with special ammo (3% risk)
        
        Returns:
            Tuple of (can_use, adjusted_volume)
        """
        # Check if user has special ammo
        can_use, message, risk_percent = self.xp_integration.ammunition_manager.can_use_special_ammo(
            user_id,
            91.0  # Assume high TCS for special ammo
        )
        
        if can_use and risk_percent:
            # Calculate volume for 3% risk
            # This is simplified - real calculation would consider pip value
            adjusted_volume = base_volume * (risk_percent / 2.0)  # 3% / 2% = 1.5x
            return True, adjusted_volume
        
        return False, base_volume


# Example MT5 script additions needed in EA
MT5_PROTOCOL_HANDLER = """
// Add to BITTENBridge EA for protocol support

void ProcessProtocolInstruction() {
    string filename = "bitten_protocols.json";
    if(!FileIsExist(filename)) return;
    
    string content = ReadFile(filename);
    if(content == "") return;
    
    // Parse JSON protocol instruction
    JSONParser parser;
    if(!parser.Parse(content)) {
        WriteProtocolResult("", false, "Invalid JSON");
        return;
    }
    
    string command = parser.GetString("command");
    int ticket = parser.GetInt("ticket");
    string protocol_id = parser.GetString("protocol_id");
    
    bool success = false;
    string error = "";
    JSONObject result;
    
    if(command == "TRAIL_STOP") {
        double trail_pips = parser.GetDouble("params.trail_distance_pips");
        success = TrailStopLoss(ticket, trail_pips, result);
    }
    else if(command == "PARTIAL_CLOSE") {
        double close_percent = parser.GetDouble("params.close_percent");
        bool move_be = parser.GetBool("params.move_to_breakeven");
        success = PartialClose(ticket, close_percent, move_be, result);
    }
    else if(command == "PLACE_PENDING") {
        success = PlacePendingOrder(parser, result);
    }
    
    WriteProtocolResult(protocol_id, success, error, result);
    FileDelete(filename);
}
"""


if __name__ == "__main__":
    # Example usage
    from mt5_bridge_adapter import MT5BridgeAdapter
    
    bridge = MT5BridgeAdapter()
    protocol_bridge = MT5EliteProtocolBridge(bridge)
    
    # Execute trailing guard
    success, message = protocol_bridge.execute_trailing_guard(
        ticket=12345,
        current_profit_pips=25,
        new_sl_distance_pips=15,
        symbol="XAUUSD"
    )
    print(f"Trailing guard: {message}")