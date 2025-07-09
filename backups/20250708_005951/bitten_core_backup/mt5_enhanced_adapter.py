"""
Enhanced MT5 Adapter with Two-Way Communication
Supports account data, advanced trade management, and live filtering
"""

import json
import os
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MT5EnhancedAdapter:
    """Enhanced adapter for MT5 with full two-way communication"""
    
    def __init__(self, files_path: str = None):
        """Initialize enhanced adapter"""
        self.files_path = files_path or self._find_mt5_files_path()
        
        # File names matching EA v3
        self.instruction_file = "bitten_instructions_secure.txt"
        self.command_file = "bitten_commands_secure.txt"
        self.result_file = "bitten_results_secure.txt"
        self.status_file = "bitten_status_secure.txt"
        self.positions_file = "bitten_positions_secure.txt"
        self.account_file = "bitten_account_secure.txt"
        self.market_file = "bitten_market_secure.txt"
        
        logger.info(f"Enhanced MT5 Adapter initialized with path: {self.files_path}")
    
    def _find_mt5_files_path(self) -> str:
        """Find MT5 Files directory"""
        # Check common paths
        paths = [
            os.path.expanduser("~/AppData/Roaming/MetaQuotes/Terminal/*/MQL5/Files"),
            "./mt5_files",
            "/opt/bitten/broker1/Files/BITTEN",  # Farm path
        ]
        
        for path in paths:
            if "*" in path:
                import glob
                matches = glob.glob(path)
                if matches:
                    return matches[0]
            elif os.path.exists(path):
                return path
        
        # Default fallback
        return "./mt5_files"
    
    def get_account_data(self) -> Optional[Dict]:
        """Get comprehensive account data from MT5"""
        account_path = os.path.join(self.files_path, self.account_file)
        
        if not os.path.exists(account_path):
            return None
        
        try:
            with open(account_path, 'r') as f:
                data = json.load(f)
                
            # Add calculated fields
            if data.get('balance', 0) > 0:
                data['risk_per_trade'] = data['balance'] * 0.02  # 2% risk
                data['margin_usage_percent'] = (data.get('margin', 0) / data['balance']) * 100 if data.get('margin', 0) > 0 else 0
            
            return data
            
        except Exception as e:
            logger.error(f"Error reading account data: {e}")
            return None
    
    def get_market_data(self) -> Optional[Dict]:
        """Get live market data from MT5"""
        market_path = os.path.join(self.files_path, self.market_file)
        
        if not os.path.exists(market_path):
            return None
        
        try:
            with open(market_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading market data: {e}")
            return None
    
    def get_positions(self) -> List[Dict]:
        """Get enhanced position data including P&L percentages"""
        positions_path = os.path.join(self.files_path, self.positions_file)
        
        if not os.path.exists(positions_path):
            return []
        
        try:
            with open(positions_path, 'r') as f:
                positions = json.load(f)
                
            # Calculate aggregate stats
            total_profit = sum(p.get('profit', 0) for p in positions)
            total_volume = sum(p.get('volume', 0) for p in positions)
            
            return {
                'positions': positions,
                'summary': {
                    'total_positions': len(positions),
                    'total_profit': total_profit,
                    'total_volume': total_volume,
                    'avg_pnl_percent': sum(p.get('pnl_percent', 0) for p in positions) / len(positions) if positions else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error reading positions: {e}")
            return {'positions': [], 'summary': {}}
    
    def execute_trade_with_risk(self, symbol: str, direction: str, 
                               risk_percent: float = 2.0, sl: float = 0, 
                               tp: float = 0, **kwargs) -> Dict:
        """Execute trade with automatic lot calculation based on risk"""
        instruction = {
            'id': f"T{int(time.time() * 1000)}",
            'symbol': symbol,
            'direction': direction.upper(),
            'volume': 0,  # Will be calculated by EA
            'sl': sl,
            'tp': tp,
            'use_risk_percent': True,
            'risk_percent': risk_percent,
            'comment': kwargs.get('comment', 'BITTEN'),
            
            # Advanced features
            'break_even': kwargs.get('break_even', True),
            'trailing': kwargs.get('trailing', False),
            'partial_close': kwargs.get('partial_close', 50.0),
            
            # Multi-step TP
            'tp1': kwargs.get('tp1', tp),
            'tp2': kwargs.get('tp2', 0),
            'tp3': kwargs.get('tp3', 0),
            'volume1': kwargs.get('volume1', 30),  # % at TP1
            'volume2': kwargs.get('volume2', 30),  # % at TP2
            'volume3': kwargs.get('volume3', 40),  # % at TP3
        }
        
        return self._send_instruction(instruction)
    
    def execute_trade(self, symbol: str, direction: str, volume: float,
                     sl: float = 0, tp: float = 0, **kwargs) -> Dict:
        """Execute trade with fixed lot size"""
        instruction = {
            'id': f"T{int(time.time() * 1000)}",
            'symbol': symbol,
            'direction': direction.upper(),
            'volume': volume,
            'sl': sl,
            'tp': tp,
            'use_risk_percent': False,
            'comment': kwargs.get('comment', 'BITTEN'),
            
            # Advanced features
            'break_even': kwargs.get('break_even', True),
            'trailing': kwargs.get('trailing', False),
            'partial_close': kwargs.get('partial_close', 0),
        }
        
        return self._send_instruction(instruction)
    
    def modify_position(self, ticket: int, sl: float = None, tp: float = None) -> bool:
        """Modify position SL/TP"""
        command = {
            'action': 'modify',
            'ticket': ticket,
            'sl': sl or 0,
            'tp': tp or 0
        }
        
        return self._send_command(command)
    
    def close_partial(self, ticket: int, percent: float = 50.0) -> bool:
        """Close partial position (e.g., 50% profit taking)"""
        command = {
            'action': 'close_partial',
            'ticket': ticket,
            'percent': percent
        }
        
        return self._send_command(command)
    
    def set_trailing_stop(self, ticket: int, distance: int = 30, step: int = 10) -> bool:
        """Activate trailing stop for position"""
        command = {
            'action': 'trail',
            'ticket': ticket,
            'distance': distance,  # Points
            'step': step  # Points
        }
        
        return self._send_command(command)
    
    def set_break_even(self, ticket: int, buffer: int = 5) -> bool:
        """Set position to break-even + buffer"""
        command = {
            'action': 'break_even',
            'ticket': ticket,
            'buffer': buffer  # Points above entry
        }
        
        return self._send_command(command)
    
    def scale_out(self, ticket: int) -> bool:
        """Scale out of position (partial close + trailing)"""
        command = {
            'action': 'scale_out',
            'ticket': ticket
        }
        
        return self._send_command(command)
    
    def close_position(self, ticket: int) -> bool:
        """Close entire position"""
        command = {
            'action': 'close',
            'ticket': ticket
        }
        
        return self._send_command(command)
    
    def should_take_trade(self, symbol: str, risk_percent: float = 2.0) -> Tuple[bool, str]:
        """Check if trade should be taken based on account/risk"""
        account = self.get_account_data()
        if not account:
            return False, "No account data available"
        
        positions = self.get_positions()
        
        # Check daily drawdown
        daily_pl_percent = account.get('daily_pl_percent', 0)
        if daily_pl_percent <= -7.0:
            return False, f"Daily loss limit reached: {daily_pl_percent:.1f}%"
        
        # Check margin level
        margin_level = account.get('margin_level', 0)
        if 0 < margin_level < 200:
            return False, f"Margin level too low: {margin_level:.1f}%"
        
        # Check position limits
        position_count = len(positions.get('positions', []))
        if position_count >= 10:
            return False, f"Max positions reached: {position_count}"
        
        # Check symbol exposure
        symbol_positions = [p for p in positions.get('positions', []) 
                          if p.get('symbol') == symbol]
        if len(symbol_positions) >= 2:
            return False, f"Max positions for {symbol}: {len(symbol_positions)}"
        
        # Check if enough free margin for trade
        free_margin = account.get('free_margin', 0)
        min_margin_needed = account.get('balance', 0) * 0.1  # Keep 10% free
        if free_margin < min_margin_needed:
            return False, f"Insufficient free margin: ${free_margin:.2f}"
        
        return True, "Trade allowed"
    
    def get_lot_size_for_risk(self, symbol: str, sl_price: float, 
                             risk_percent: float = 2.0) -> float:
        """Calculate lot size based on risk percentage"""
        account = self.get_account_data()
        if not account:
            return 0.01
        
        balance = account.get('balance', 0)
        if balance <= 0:
            return 0.01
        
        # This is a simplified calculation
        # EA will do the actual calculation with proper tick values
        risk_amount = balance * (risk_percent / 100.0)
        
        # Return a reasonable default, EA will calculate precise value
        return 0.01
    
    def _send_instruction(self, instruction: Dict) -> Dict:
        """Send trading instruction to MT5"""
        instruction_path = os.path.join(self.files_path, self.instruction_file)
        result_path = os.path.join(self.files_path, self.result_file)
        
        # Remove old result
        if os.path.exists(result_path):
            os.remove(result_path)
        
        # Write instruction
        with open(instruction_path, 'w') as f:
            json.dump(instruction, f)
        
        # Wait for result
        start_time = time.time()
        while time.time() - start_time < 30:  # 30 second timeout
            if os.path.exists(result_path):
                try:
                    with open(result_path, 'r') as f:
                        result = json.load(f)
                    os.remove(result_path)
                    
                    # Add instruction ID to result
                    result['instruction_id'] = instruction['id']
                    
                    return {
                        'success': result.get('status') == 'success',
                        'data': result,
                        'account_after': result.get('account', {})
                    }
                except Exception as e:
                    logger.error(f"Error reading result: {e}")
            
            time.sleep(0.1)
        
        return {
            'success': False,
            'error': 'Timeout waiting for MT5 response',
            'instruction': instruction
        }
    
    def _send_command(self, command: Dict) -> bool:
        """Send management command to MT5"""
        command_path = os.path.join(self.files_path, self.command_file)
        
        try:
            with open(command_path, 'w') as f:
                json.dump(command, f)
            
            # Commands are fire-and-forget, check status for confirmation
            time.sleep(0.5)
            
            status = self.get_status()
            if status and 'success' in status.get('message', '').lower():
                return True
            
            return True  # Assume success if no error
            
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return False
    
    def get_status(self) -> Optional[Dict]:
        """Get EA status"""
        status_path = os.path.join(self.files_path, self.status_file)
        
        if not os.path.exists(status_path):
            return None
        
        try:
            with open(status_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading status: {e}")
            return None


class MT5AccountMonitor:
    """Monitor MT5 account and provide insights"""
    
    def __init__(self, adapter: MT5EnhancedAdapter):
        self.adapter = adapter
        self.last_balance = None
        self.session_start_balance = None
    
    def get_session_stats(self) -> Dict:
        """Get current session statistics"""
        account = self.adapter.get_account_data()
        if not account:
            return {}
        
        current_balance = account.get('balance', 0)
        
        # Initialize session balance
        if self.session_start_balance is None:
            self.session_start_balance = current_balance
        
        # Calculate session P&L
        session_pl = current_balance - self.session_start_balance
        session_pl_percent = (session_pl / self.session_start_balance * 100) if self.session_start_balance > 0 else 0
        
        positions = self.adapter.get_positions()
        
        return {
            'session_pl': session_pl,
            'session_pl_percent': session_pl_percent,
            'daily_pl': account.get('daily_pl', 0),
            'daily_pl_percent': account.get('daily_pl_percent', 0),
            'open_positions': len(positions.get('positions', [])),
            'floating_pl': sum(p.get('profit', 0) for p in positions.get('positions', [])),
            'margin_level': account.get('margin_level', 0),
            'can_trade': self._can_trade(account, positions),
            'risk_status': self._get_risk_status(account, positions)
        }
    
    def _can_trade(self, account: Dict, positions: Dict) -> bool:
        """Check if trading is allowed based on risk"""
        # Daily loss limit
        if account.get('daily_pl_percent', 0) <= -7.0:
            return False
        
        # Margin level
        if 0 < account.get('margin_level', 0) < 200:
            return False
        
        # Position limit
        if len(positions.get('positions', [])) >= 10:
            return False
        
        return True
    
    def _get_risk_status(self, account: Dict, positions: Dict) -> str:
        """Get current risk status"""
        daily_pl_percent = account.get('daily_pl_percent', 0)
        
        if daily_pl_percent <= -5.0:
            return "CRITICAL"
        elif daily_pl_percent <= -3.0:
            return "WARNING"
        elif len(positions.get('positions', [])) >= 8:
            return "CAUTION"
        else:
            return "NORMAL"


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Initialize adapter
    adapter = MT5EnhancedAdapter()
    
    # Get account data
    account = adapter.get_account_data()
    if account:
        print(f"Balance: ${account['balance']:.2f}")
        print(f"Equity: ${account['equity']:.2f}")
        print(f"Daily P&L: {account['daily_pl_percent']:.2f}%")
    
    # Check if we should take a trade
    can_trade, reason = adapter.should_take_trade("EURUSD", 2.0)
    print(f"Can trade EURUSD: {can_trade} ({reason})")
    
    # Execute trade with risk-based sizing
    if can_trade:
        result = adapter.execute_trade_with_risk(
            symbol="EURUSD",
            direction="BUY",
            risk_percent=2.0,
            sl=1.0900,
            tp1=1.1050,  # First TP
            tp2=1.1100,  # Second TP
            tp3=1.1150,  # Final TP
            break_even=True,
            trailing=True
        )
        print(f"Trade result: {result}")