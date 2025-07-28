"""
🎯 Trade Result Model
Structured data model for MT5 trade results with database integration
"""

from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal
from dataclasses import dataclass, field, asdict
from enum import Enum
import json

from src.database.models import Trade, TradeStatus as DBTradeStatus, OrderType as DBOrderType

@dataclass
class TradeResult:
    """
    Structured trade result from MT5
    Can be converted to database model
    """
    
    # Core fields
    ticket: int
    symbol: str
    order_type: str
    status: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Trade details
    volume: Optional[float] = None
    open_price: Optional[float] = None
    close_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    # Financial results
    profit: Optional[float] = None
    commission: Optional[float] = None
    swap: Optional[float] = None
    net_profit: Optional[float] = None
    
    # Timing
    open_time: Optional[datetime] = None
    close_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    
    # Risk metrics
    risk_amount: Optional[float] = None
    risk_percentage: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    
    # MT5 specific
    magic_number: Optional[int] = None
    comment: Optional[str] = None
    
    # Error info
    error_code: Optional[int] = None
    error_message: Optional[str] = None
    
    # Metadata
    mt5_server: Optional[str] = None
    account_number: Optional[int] = None
    
    def __post_init__(self):
        """Calculate derived fields"""
        # Calculate net profit if components available
        if self.profit is not None and self.commission is not None and self.swap is not None:
            self.net_profit = self.profit + self.swap + self.commission
            
        # Calculate duration if times available
        if self.open_time and self.close_time:
            self.duration_seconds = int((self.close_time - self.open_time).total_seconds())
            
        # Calculate risk/reward ratio
        if self.open_price and self.stop_loss and self.take_profit:
            if 'BUY' in self.order_type:
                risk = self.open_price - self.stop_loss
                reward = self.take_profit - self.open_price
            else:
                risk = self.stop_loss - self.open_price
                reward = self.open_price - self.take_profit
                
            if risk > 0:
                self.risk_reward_ratio = round(reward / risk, 2)
    
    @classmethod
    def from_parser_result(cls, parsed_result: Dict[str, Any]) -> 'TradeResult':
        """
        Create TradeResult from MT5ResultParser output
        
        Args:
            parsed_result: Dictionary from MT5ResultParser
            
        Returns:
            TradeResult instance
        """
        result_type = parsed_result.get('type', '')
        
        # Base fields
        kwargs = {
            'ticket': parsed_result.get('ticket', 0),
            'symbol': parsed_result.get('symbol', 'UNKNOWN'),
            'order_type': parsed_result.get('order_type', 'UNKNOWN'),
            'status': parsed_result.get('status', 'UNKNOWN'),
            'comment': parsed_result.get('comment')
        }
        
        # Handle different result types
        if result_type == 'trade_opened':
            kwargs.update({
                'volume': parsed_result.get('volume'),
                'open_price': parsed_result.get('price'),
                'stop_loss': parsed_result.get('stop_loss'),
                'take_profit': parsed_result.get('take_profit'),
                'open_time': datetime.utcnow()
            })
            
        elif result_type == 'trade_closed':
            kwargs.update({
                'close_price': parsed_result.get('close_price'),
                'profit': parsed_result.get('profit'),
                'commission': parsed_result.get('commission'),
                'swap': parsed_result.get('swap'),
                'net_profit': parsed_result.get('net_profit'),
                'close_time': datetime.fromisoformat(parsed_result.get('close_time', datetime.utcnow().isoformat()))
            })
            
        elif result_type == 'error':
            kwargs.update({
                'status': 'ERROR',
                'error_code': parsed_result.get('error_code'),
                'error_message': parsed_result.get('error_message')
            })
        
        return cls(**kwargs)
    
    def to_database_model(self, user_id: int, fire_mode: str = None) -> Trade:
        """
        Convert to database Trade model
        
        Args:
            user_id: User ID for the trade
            fire_mode: Fire mode used (optional)
            
        Returns:
            Trade model instance
        """
        # Map status
        status_map = {
            'OPEN': DBTradeStatus.open,
            'CLOSED': DBTradeStatus.closed,
            'PENDING': DBTradeStatus.pending,
            'CANCELLED': DBTradeStatus.cancelled,
            'ERROR': DBTradeStatus.cancelled
        }
        db_status = status_map.get(self.status, DBTradeStatus.pending)
        
        # Map order type
        order_map = {
            'BUY': DBOrderType.buy,
            'SELL': DBOrderType.sell,
            'BUY_LIMIT': DBOrderType.buy_limit,
            'SELL_LIMIT': DBOrderType.sell_limit,
            'BUY_STOP': DBOrderType.buy_stop,
            'SELL_STOP': DBOrderType.sell_stop
        }
        db_order_type = order_map.get(self.order_type, DBOrderType.buy)
        
        # Create metadata
        metadata = {
            'mt5_ticket': self.ticket,
            'mt5_server': self.mt5_server,
            'account_number': self.account_number,
            'magic_number': self.magic_number,
            'risk_reward_ratio': self.risk_reward_ratio,
            'duration_seconds': self.duration_seconds,
            'comment': self.comment,
            'fire_mode': fire_mode
        }
        
        # Create trade model
        trade = Trade(
            user_id=user_id,
            mt5_ticket=self.ticket,
            symbol=self.symbol,
            order_type=db_order_type,
            status=db_status,
            volume=Decimal(str(self.volume)) if self.volume else Decimal('0'),
            open_price=Decimal(str(self.open_price)) if self.open_price else None,
            close_price=Decimal(str(self.close_price)) if self.close_price else None,
            stop_loss=Decimal(str(self.stop_loss)) if self.stop_loss else None,
            take_profit=Decimal(str(self.take_profit)) if self.take_profit else None,
            profit=Decimal(str(self.profit)) if self.profit else Decimal('0'),
            commission=Decimal(str(self.commission)) if self.commission else Decimal('0'),
            swap=Decimal(str(self.swap)) if self.swap else Decimal('0'),
            open_time=self.open_time,
            close_time=self.close_time,
            fire_mode=fire_mode,
            metadata=metadata
        )
        
        return trade
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        
        # Convert datetime objects to ISO format
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
                
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    def is_successful(self) -> bool:
        """Check if trade was successful"""
        if self.status == 'ERROR':
            return False
        if self.status == 'CLOSED' and self.net_profit is not None:
            return self.net_profit > 0
        return self.status in ['OPEN', 'PENDING']
    
    def get_pips(self) -> Optional[float]:
        """Calculate profit/loss in pips"""
        if not all([self.open_price, self.close_price]):
            return None
            
        if 'JPY' in self.symbol:
            multiplier = 100  # 3-digit pairs
        else:
            multiplier = 10000  # 5-digit pairs
            
        if 'BUY' in self.order_type:
            pips = (self.close_price - self.open_price) * multiplier
        else:
            pips = (self.open_price - self.close_price) * multiplier
            
        return round(pips, 1)
    
    def get_risk_amount(self, account_balance: float) -> float:
        """Calculate risk amount based on stop loss"""
        if not all([self.open_price, self.stop_loss, self.volume]):
            return 0.0
            
        if 'BUY' in self.order_type:
            risk_pips = self.open_price - self.stop_loss
        else:
            risk_pips = self.stop_loss - self.open_price
            
        # Simple calculation (would need pip value for accuracy)
        risk_amount = risk_pips * self.volume * 100000  # Assuming standard lot
        
        return abs(risk_amount)
    
    def format_summary(self) -> str:
        """Format human-readable summary"""
        if self.status == 'OPEN':
            return (
                f"📈 Trade Opened: {self.symbol} {self.order_type} "
                f"{self.volume} @ {self.open_price} "
                f"(SL: {self.stop_loss}, TP: {self.take_profit})"
            )
        elif self.status == 'CLOSED':
            profit_emoji = "✅" if self.net_profit > 0 else "❌"
            return (
                f"{profit_emoji} Trade Closed: {self.symbol} "
                f"P/L: ${self.net_profit:.2f} ({self.get_pips()} pips)"
            )
        elif self.status == 'ERROR':
            return f"⚠️ Trade Error: {self.error_message} (Code: {self.error_code})"
        else:
            return f"Trade {self.ticket}: {self.status}"

class TradeResultBatch:
    """
    Container for multiple trade results
    Used for batch processing and reporting
    """
    
    def __init__(self):
        self.results: List[TradeResult] = []
        self.timestamp = datetime.utcnow()
        
    def add_result(self, result: TradeResult):
        """Add a trade result"""
        self.results.append(result)
        
    def get_summary(self) -> Dict[str, Any]:
        """Get batch summary statistics"""
        total_trades = len(self.results)
        successful_trades = sum(1 for r in self.results if r.is_successful())
        failed_trades = sum(1 for r in self.results if r.status == 'ERROR')
        
        total_profit = sum(r.net_profit or 0 for r in self.results)
        total_volume = sum(r.volume or 0 for r in self.results)
        
        return {
            'timestamp': self.timestamp.isoformat(),
            'total_trades': total_trades,
            'successful_trades': successful_trades,
            'failed_trades': failed_trades,
            'success_rate': successful_trades / total_trades * 100 if total_trades > 0 else 0,
            'total_profit': round(total_profit, 2),
            'total_volume': round(total_volume, 2),
            'average_profit': round(total_profit / total_trades, 2) if total_trades > 0 else 0
        }
    
    def get_by_status(self, status: str) -> List[TradeResult]:
        """Get results by status"""
        return [r for r in self.results if r.status == status]
    
    def get_profitable_trades(self) -> List[TradeResult]:
        """Get profitable trades"""
        return [r for r in self.results if r.net_profit and r.net_profit > 0]
    
    def get_losing_trades(self) -> List[TradeResult]:
        """Get losing trades"""
        return [r for r in self.results if r.net_profit and r.net_profit < 0]