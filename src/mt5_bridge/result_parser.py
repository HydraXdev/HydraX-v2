"""
🎯 MT5 Bridge Result Parser
Parses trade results from MT5 EA back to Python for processing
Handles various MT5 result formats and error conditions
"""

import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Union, Tuple
from decimal import Decimal
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class OrderType(Enum):
    """MT5 order types"""
    BUY = "BUY"
    SELL = "SELL"
    BUY_LIMIT = "BUY_LIMIT"
    SELL_LIMIT = "SELL_LIMIT"
    BUY_STOP = "BUY_STOP"
    SELL_STOP = "SELL_STOP"

class TradeStatus(Enum):
    """Trade execution status"""
    PENDING = "PENDING"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    ERROR = "ERROR"
    PARTIAL = "PARTIAL"

class MT5ResultParser:
    """
    Parses various MT5 result formats into structured data
    
    Handles formats:
    - Trade execution results
    - Order placement confirmations
    - Position updates
    - Error messages
    - Account status updates
    """
    
    # Common MT5 result patterns
    PATTERNS = {
        # Trade opened: "TRADE_OPENED|ticket:12345|symbol:EURUSD|type:BUY|volume:0.01|price:1.12345|sl:1.11345|tp:1.13345|comment:BITTEN"
        'trade_opened': re.compile(
            r'TRADE_OPENED\|ticket:(\d+)\|symbol:(\w+)\|type:(\w+)\|'
            r'volume:([\d.]+)\|price:([\d.]+)\|sl:([\d.]+)\|tp:([\d.]+)'
            r'(?:\|comment:(.+))?'
        ),
        
        # Trade closed: "TRADE_CLOSED|ticket:12345|close_price:1.12445|profit:10.50|swap:0|commission:-0.20|close_time:2024-01-07 15:30:45"
        'trade_closed': re.compile(
            r'TRADE_CLOSED\|ticket:(\d+)\|close_price:([\d.]+)\|'
            r'profit:([-\d.]+)\|swap:([-\d.]+)\|commission:([-\d.]+)\|'
            r'close_time:([^|]+)'
        ),
        
        # Order placed: "ORDER_PLACED|ticket:12346|symbol:GBPUSD|type:BUY_LIMIT|volume:0.02|price:1.26500|sl:1.25500|tp:1.27500"
        'order_placed': re.compile(
            r'ORDER_PLACED\|ticket:(\d+)\|symbol:(\w+)\|type:(\w+)\|'
            r'volume:([\d.]+)\|price:([\d.]+)\|sl:([\d.]+)\|tp:([\d.]+)'
        ),
        
        # Position modified: "POSITION_MODIFIED|ticket:12345|sl:1.11845|tp:1.12845|success:true"
        'position_modified': re.compile(
            r'POSITION_MODIFIED\|ticket:(\d+)\|sl:([\d.]+)\|tp:([\d.]+)\|'
            r'success:(true|false)'
        ),
        
        # Error: "ERROR|code:10006|message:Request rejected|context:TRADE_OPEN"
        'error': re.compile(
            r'ERROR\|code:(\d+)\|message:([^|]+)(?:\|context:(.+))?'
        ),
        
        # Account update: "ACCOUNT_UPDATE|balance:10500.25|equity:10450.75|margin:250.00|free_margin:10200.75"
        'account_update': re.compile(
            r'ACCOUNT_UPDATE\|balance:([\d.]+)\|equity:([\d.]+)\|'
            r'margin:([\d.]+)\|free_margin:([\d.]+)'
        ),
        
        # Simple JSON format (alternative)
        'json_format': re.compile(r'^\{.*\}$', re.DOTALL)
    }
    
    # MT5 error codes
    ERROR_CODES = {
        10004: "Requote",
        10006: "Request rejected", 
        10007: "Request cancelled by trader",
        10008: "Order placed",
        10009: "Request completed",
        10010: "Only part of request completed",
        10011: "Request processing error",
        10012: "Request cancelled by timeout",
        10013: "Invalid request",
        10014: "Invalid volume",
        10015: "Invalid price",
        10016: "Invalid stops",
        10017: "Trade disabled",
        10018: "Market closed",
        10019: "Insufficient funds",
        10020: "Prices changed",
        10021: "No quotes to process request",
        10022: "Invalid order expiration",
        10023: "Order state changed",
        10024: "Too frequent requests",
        10025: "No changes in request",
        10026: "Autotrading disabled by server",
        10027: "Autotrading disabled by client",
        10028: "Request locked for processing",
        10029: "Order or position frozen",
        10030: "Invalid order filling type"
    }
    
    def __init__(self):
        self.last_parse_time = None
        self.parse_count = 0
        
    def parse(self, result_string: str) -> Dict[str, any]:
        """
        Parse MT5 result string into structured data
        
        Args:
            result_string: Raw result from MT5
            
        Returns:
            Parsed result dictionary
        """
        if not result_string:
            return self._error_result("Empty result string")
            
        result_string = result_string.strip()
        self.last_parse_time = datetime.utcnow()
        self.parse_count += 1
        
        # Try JSON format first
        if self.PATTERNS['json_format'].match(result_string):
            return self._parse_json(result_string)
        
        # Try each pattern
        for result_type, pattern in self.PATTERNS.items():
            if result_type == 'json_format':
                continue
                
            match = pattern.match(result_string)
            if match:
                parser_method = getattr(self, f'_parse_{result_type}')
                return parser_method(match)
        
        # Unknown format
        logger.warning(f"Unknown MT5 result format: {result_string}")
        return self._error_result(f"Unknown format: {result_string}")
    
    def _parse_trade_opened(self, match: re.Match) -> Dict[str, any]:
        """Parse trade opened result"""
        ticket, symbol, order_type, volume, price, sl, tp = match.groups()[:7]
        comment = match.group(8) if len(match.groups()) >= 8 else None
        
        return {
            'type': 'trade_opened',
            'success': True,
            'ticket': int(ticket),
            'symbol': symbol,
            'order_type': order_type,
            'volume': float(volume),
            'price': float(price),
            'stop_loss': float(sl),
            'take_profit': float(tp),
            'comment': comment,
            'timestamp': datetime.utcnow().isoformat(),
            'status': TradeStatus.OPEN.value
        }
    
    def _parse_trade_closed(self, match: re.Match) -> Dict[str, any]:
        """Parse trade closed result"""
        ticket, close_price, profit, swap, commission, close_time = match.groups()
        
        # Parse close time
        try:
            close_dt = datetime.strptime(close_time, '%Y-%m-%d %H:%M:%S')
        except:
            close_dt = datetime.utcnow()
        
        return {
            'type': 'trade_closed',
            'success': True,
            'ticket': int(ticket),
            'close_price': float(close_price),
            'profit': float(profit),
            'swap': float(swap),
            'commission': float(commission),
            'close_time': close_dt.isoformat(),
            'net_profit': float(profit) + float(swap) + float(commission),
            'timestamp': datetime.utcnow().isoformat(),
            'status': TradeStatus.CLOSED.value
        }
    
    def _parse_order_placed(self, match: re.Match) -> Dict[str, any]:
        """Parse pending order placed result"""
        ticket, symbol, order_type, volume, price, sl, tp = match.groups()
        
        return {
            'type': 'order_placed',
            'success': True,
            'ticket': int(ticket),
            'symbol': symbol,
            'order_type': order_type,
            'volume': float(volume),
            'price': float(price),
            'stop_loss': float(sl),
            'take_profit': float(tp),
            'timestamp': datetime.utcnow().isoformat(),
            'status': TradeStatus.PENDING.value
        }
    
    def _parse_position_modified(self, match: re.Match) -> Dict[str, any]:
        """Parse position modification result"""
        ticket, sl, tp, success = match.groups()
        
        return {
            'type': 'position_modified',
            'success': success.lower() == 'true',
            'ticket': int(ticket),
            'new_stop_loss': float(sl),
            'new_take_profit': float(tp),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _parse_error(self, match: re.Match) -> Dict[str, any]:
        """Parse error result"""
        code, message = match.groups()[:2]
        context = match.group(3) if len(match.groups()) >= 3 else None
        
        error_code = int(code)
        
        return {
            'type': 'error',
            'success': False,
            'error_code': error_code,
            'error_message': message,
            'error_description': self.ERROR_CODES.get(error_code, 'Unknown error'),
            'context': context,
            'timestamp': datetime.utcnow().isoformat(),
            'status': TradeStatus.ERROR.value
        }
    
    def _parse_account_update(self, match: re.Match) -> Dict[str, any]:
        """Parse account update result"""
        balance, equity, margin, free_margin = match.groups()
        
        return {
            'type': 'account_update',
            'success': True,
            'balance': float(balance),
            'equity': float(equity),
            'margin': float(margin),
            'free_margin': float(free_margin),
            'margin_level': float(equity) / float(margin) * 100 if float(margin) > 0 else 0,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _parse_json(self, result_string: str) -> Dict[str, any]:
        """Parse JSON format result"""
        try:
            data = json.loads(result_string)
            
            # Ensure required fields
            if 'type' not in data:
                data['type'] = 'json_result'
            if 'success' not in data:
                data['success'] = True
            if 'timestamp' not in data:
                data['timestamp'] = datetime.utcnow().isoformat()
                
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return self._error_result(f"Invalid JSON: {str(e)}")
    
    def _error_result(self, message: str) -> Dict[str, any]:
        """Create error result"""
        return {
            'type': 'parse_error',
            'success': False,
            'error_message': message,
            'timestamp': datetime.utcnow().isoformat(),
            'status': TradeStatus.ERROR.value
        }
    
    def parse_batch(self, results: List[str]) -> List[Dict[str, any]]:
        """
        Parse multiple MT5 results
        
        Args:
            results: List of result strings
            
        Returns:
            List of parsed results
        """
        parsed_results = []
        
        for result in results:
            parsed = self.parse(result)
            parsed_results.append(parsed)
            
        return parsed_results
    
    def extract_trade_summary(self, result: Dict[str, any]) -> Optional[Dict[str, any]]:
        """
        Extract simplified trade summary from parsed result
        
        Args:
            result: Parsed result dictionary
            
        Returns:
            Simplified trade summary or None
        """
        if result.get('type') == 'trade_opened':
            return {
                'action': 'opened',
                'ticket': result['ticket'],
                'symbol': result['symbol'],
                'direction': 'BUY' if 'BUY' in result['order_type'] else 'SELL',
                'volume': result['volume'],
                'price': result['price'],
                'risk': self._calculate_risk(result),
                'potential_reward': self._calculate_reward(result)
            }
            
        elif result.get('type') == 'trade_closed':
            return {
                'action': 'closed',
                'ticket': result['ticket'],
                'profit': result['net_profit'],
                'profit_percentage': None,  # Would need account size
                'duration': None  # Would need open time
            }
            
        return None
    
    def _calculate_risk(self, trade: Dict[str, any]) -> float:
        """Calculate risk in pips"""
        if trade.get('order_type', '').startswith('BUY'):
            risk_pips = trade['price'] - trade['stop_loss']
        else:
            risk_pips = trade['stop_loss'] - trade['price']
            
        # Convert to pips (assuming 5-digit broker)
        return round(risk_pips * 10000, 1)
    
    def _calculate_reward(self, trade: Dict[str, any]) -> float:
        """Calculate potential reward in pips"""
        if trade.get('order_type', '').startswith('BUY'):
            reward_pips = trade['take_profit'] - trade['price']
        else:
            reward_pips = trade['price'] - trade['take_profit']
            
        # Convert to pips (assuming 5-digit broker)
        return round(reward_pips * 10000, 1)
    
    def validate_result(self, result: Dict[str, any]) -> Tuple[bool, Optional[str]]:
        """
        Validate parsed result for required fields
        
        Args:
            result: Parsed result
            
        Returns:
            (is_valid, error_message)
        """
        if not isinstance(result, dict):
            return False, "Result must be a dictionary"
            
        if 'type' not in result:
            return False, "Missing 'type' field"
            
        if 'success' not in result:
            return False, "Missing 'success' field"
            
        # Type-specific validation
        if result['type'] == 'trade_opened':
            required = ['ticket', 'symbol', 'order_type', 'volume', 'price']
            for field in required:
                if field not in result:
                    return False, f"Missing required field: {field}"
                    
        elif result['type'] == 'trade_closed':
            required = ['ticket', 'close_price', 'profit']
            for field in required:
                if field not in result:
                    return False, f"Missing required field: {field}"
        
        return True, None

class MT5ResultAggregator:
    """
    Aggregates multiple MT5 results for summary reporting
    """
    
    def __init__(self):
        self.parser = MT5ResultParser()
        self.results = []
        
    def add_result(self, result_string: str):
        """Add and parse a result"""
        parsed = self.parser.parse(result_string)
        self.results.append(parsed)
        return parsed
        
    def get_summary(self) -> Dict[str, any]:
        """Get aggregated summary of all results"""
        total_trades = 0
        successful_trades = 0
        failed_trades = 0
        total_profit = 0.0
        errors = []
        
        for result in self.results:
            if result['type'] == 'trade_closed':
                total_trades += 1
                if result.get('net_profit', 0) > 0:
                    successful_trades += 1
                else:
                    failed_trades += 1
                total_profit += result.get('net_profit', 0)
                
            elif result['type'] == 'error':
                errors.append({
                    'code': result.get('error_code'),
                    'message': result.get('error_message')
                })
        
        return {
            'total_results': len(self.results),
            'total_trades': total_trades,
            'successful_trades': successful_trades,
            'failed_trades': failed_trades,
            'win_rate': successful_trades / total_trades * 100 if total_trades > 0 else 0,
            'total_profit': round(total_profit, 2),
            'errors': errors,
            'last_update': datetime.utcnow().isoformat()
        }
    
    def clear(self):
        """Clear all results"""
        self.results = []

# Convenience function
def parse_mt5_result(result_string: str) -> Dict[str, any]:
    """Quick parse function"""
    parser = MT5ResultParser()
    return parser.parse(result_string)