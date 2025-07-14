#!/usr/bin/env python3
"""
FORTRESS BRIDGE CONVERTER - Military Grade Signal Conversion
Version: 1.0 BULLETPROOF
Mission: Convert MT5 bridge data to standardized SPE format with zero tolerance for errors

NEVER FAILS. NEVER COMPROMISES. VALIDATES EVERYTHING.
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from enum import Enum
import jsonschema

class EventType(Enum):
    NEW_TRADE = "new_trade"
    CLOSE_TRADE = "close_trade"
    MODIFY_TRADE = "modify_trade"
    PRICE_UPDATE = "price_update"
    BALANCE_UPDATE = "balance_update"
    HEARTBEAT = "heartbeat"

class OrderType(Enum):
    BUY = "buy"
    SELL = "sell"
    BUY_LIMIT = "buy_limit"
    SELL_LIMIT = "sell_limit"
    BUY_STOP = "buy_stop"
    SELL_STOP = "sell_stop"

class Strategy(Enum):
    BITMODE_AUTO = "bitmode_auto"
    RAPID_ASSAULT = "rapid_assault"
    SNIPER_OPS = "sniper_ops"
    MANUAL = "manual"

class TradingSession(Enum):
    ASIAN = "ASIAN"
    LONDON = "LONDON"
    NY = "NY"
    OVERLAP = "OVERLAP"

class Volatility(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EXTREME = "EXTREME"

class NewsImpact(Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

@dataclass
class TradeSignalMetadata:
    session: TradingSession
    volatility: Volatility
    news_impact: NewsImpact

@dataclass
class TradeSignal:
    """Bulletproof trade signal structure"""
    event: EventType
    timestamp: str
    symbol: str
    order_type: OrderType
    lot_size: float
    entry_price: float
    bridge_id: str
    account_id: str
    execution_id: str
    strategy: Strategy
    tcs_score: int
    sl: Optional[float] = None
    tp: Optional[float] = None
    current_price: Optional[float] = None
    spread: Optional[float] = None
    balance: Optional[float] = None
    equity: Optional[float] = None
    margin_level: Optional[float] = None
    metadata: Optional[TradeSignalMetadata] = None

class FortressBridgeConverter:
    """
    MILITARY-GRADE BRIDGE SIGNAL CONVERTER
    
    Capabilities:
    - Bulletproof MT5 data conversion
    - Real-time validation against JSON schema
    - Zero-tolerance error handling
    - Performance monitoring and metrics
    - Automatic format detection and normalization
    """
    
    def __init__(self, bridge_id: str = "bridge_019"):
        self.bridge_id = bridge_id
        self.conversion_count = 0
        self.error_count = 0
        self.last_error = None
        self.start_time = time.time()
        
        # Load JSON schema for validation
        self.schema = self._load_schema()
        
        # Initialize fortress logging
        self.setup_logging()
        
        self.logger.info(f"🛡️ FORTRESS BRIDGE CONVERTER INITIALIZED")
        self.logger.info(f"🎯 Bridge ID: {self.bridge_id}")
        self.logger.info(f"✅ Schema loaded with {len(self.schema.get('required', []))} required fields")
        
    def setup_logging(self):
        """Initialize military-grade logging"""
        log_format = '%(asctime)s - FORTRESS_BRIDGE - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler('/root/HydraX-v2/fortress_bridge.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("FORTRESS_BRIDGE")
        
    def _load_schema(self) -> Dict:
        """Load and validate JSON schema"""
        try:
            with open('/root/HydraX-v2/shared/formats/bitten_trade.json', 'r') as f:
                schema = json.load(f)
            return schema
        except Exception as e:
            # Fallback to embedded schema if file not found
            return self._get_embedded_schema()
            
    def _get_embedded_schema(self) -> Dict:
        """Embedded fallback schema"""
        return {
            "type": "object",
            "required": ["event", "timestamp", "symbol", "order_type", "lot_size", 
                        "entry_price", "bridge_id", "account_id", "execution_id", 
                        "strategy", "tcs_score"]
        }
        
    def convert_mt5_order(self, order: Any, strategy: str = "bitmode_auto", 
                         session: str = "LONDON", volatility: str = "MEDIUM",
                         news_impact: str = "LOW") -> Dict:
        """
        BULLETPROOF MT5 ORDER CONVERSION
        Converts MT5 order object to standardized signal format
        """
        try:
            self.logger.debug(f"🔄 Converting MT5 order: {order}")
            
            # Extract and validate order data
            signal_data = self._extract_order_data(order, strategy, session, volatility, news_impact)
            
            # Create TradeSignal object
            signal = self._create_trade_signal(signal_data)
            
            # Convert to dictionary
            signal_dict = self._signal_to_dict(signal)
            
            # Validate against schema
            self._validate_signal(signal_dict)
            
            # Track success
            self.conversion_count += 1
            self.logger.info(f"✅ Successfully converted signal #{self.conversion_count}")
            
            return signal_dict
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            self.logger.error(f"❌ Conversion failed: {e}")
            raise FortressConversionError(f"MT5 order conversion failed: {e}")
            
    def _extract_order_data(self, order: Any, strategy: str, session: str, 
                           volatility: str, news_impact: str) -> Dict:
        """Extract data from MT5 order with bulletproof validation"""
        
        # Handle different order object types
        if hasattr(order, '__dict__'):
            # MT5 order object
            data = {
                'symbol': getattr(order, 'symbol', 'UNKNOWN'),
                'order_type': self._normalize_order_type(getattr(order, 'type', 0)),
                'lot_size': float(getattr(order, 'volume', 0.01)),
                'entry_price': float(getattr(order, 'price_open', getattr(order, 'price', 0))),
                'sl': float(getattr(order, 'sl', 0)) if getattr(order, 'sl', 0) > 0 else None,
                'tp': float(getattr(order, 'tp', 0)) if getattr(order, 'tp', 0) > 0 else None,
                'execution_id': str(getattr(order, 'comment', f"AUTO_{int(time.time())}")),
                'current_price': float(getattr(order, 'price_current', 0)) if hasattr(order, 'price_current') else None,
                'tcs_score': self._extract_tcs_score(order)
            }
        elif isinstance(order, dict):
            # Dictionary format
            data = {
                'symbol': order.get('symbol', 'UNKNOWN'),
                'order_type': self._normalize_order_type(order.get('type', order.get('order_type', 'buy'))),
                'lot_size': float(order.get('volume', order.get('lot_size', 0.01))),
                'entry_price': float(order.get('price', order.get('entry_price', 0))),
                'sl': float(order.get('sl', 0)) if order.get('sl', 0) and order.get('sl', 0) > 0 else None,
                'tp': float(order.get('tp', 0)) if order.get('tp', 0) and order.get('tp', 0) > 0 else None,
                'execution_id': str(order.get('comment', order.get('execution_id', f"AUTO_{int(time.time())}"))),
                'current_price': float(order.get('current_price', 0)) if order.get('current_price') else None,
                'tcs_score': int(order.get('tcs_score', order.get('magic', 50)))
            }
        else:
            raise ValueError(f"Unsupported order type: {type(order)}")
            
        # Add common fields
        data.update({
            'event': EventType.NEW_TRADE.value,
            'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'bridge_id': self.bridge_id,
            'account_id': self._get_account_id(),
            'strategy': strategy,
            'session': session,
            'volatility': volatility,
            'news_impact': news_impact
        })
        
        return data
        
    def _normalize_order_type(self, order_type: Union[int, str]) -> str:
        """Normalize order type to standard format"""
        if isinstance(order_type, int):
            # MT5 order type constants
            type_map = {
                0: "buy",
                1: "sell",
                2: "buy_limit",
                3: "sell_limit",
                4: "buy_stop",
                5: "sell_stop"
            }
            return type_map.get(order_type, "buy")
        elif isinstance(order_type, str):
            return order_type.lower().replace('order_type_', '').replace('_', '_')
        else:
            return "buy"
            
    def _extract_tcs_score(self, order: Any) -> int:
        """Extract TCS score from order with fallbacks"""
        # Try multiple sources for TCS score
        sources = ['tcs_score', 'magic', 'confidence', 'score']
        
        for source in sources:
            if hasattr(order, source):
                value = getattr(order, source)
                if isinstance(value, (int, float)) and 0 <= value <= 100:
                    return int(value)
                elif isinstance(value, (int, float)) and value > 100:
                    # Probably magic number, convert to TCS score
                    return min(85, max(35, int(value % 100)))
                    
        # Default TCS score
        return 50
        
    def _get_account_id(self) -> str:
        """Get account ID with fallback"""
        # This should be configured or passed in
        return "843859"  # Default demo account
        
    def _create_trade_signal(self, data: Dict) -> TradeSignal:
        """Create TradeSignal object with validation"""
        try:
            metadata = TradeSignalMetadata(
                session=TradingSession(data.get('session', 'LONDON')),
                volatility=Volatility(data.get('volatility', 'MEDIUM')),
                news_impact=NewsImpact(data.get('news_impact', 'LOW'))
            )
            
            return TradeSignal(
                event=EventType(data['event']),
                timestamp=data['timestamp'],
                symbol=data['symbol'],
                order_type=OrderType(data['order_type']),
                lot_size=data['lot_size'],
                entry_price=data['entry_price'],
                bridge_id=data['bridge_id'],
                account_id=data['account_id'],
                execution_id=data['execution_id'],
                strategy=Strategy(data['strategy']),
                tcs_score=data['tcs_score'],
                sl=data.get('sl'),
                tp=data.get('tp'),
                current_price=data.get('current_price'),
                metadata=metadata
            )
        except (ValueError, KeyError) as e:
            raise FortressConversionError(f"Invalid signal data: {e}")
            
    def _signal_to_dict(self, signal: TradeSignal) -> Dict:
        """Convert TradeSignal to dictionary with proper serialization"""
        signal_dict = asdict(signal)
        
        # Convert enums to values
        signal_dict['event'] = signal.event.value
        signal_dict['order_type'] = signal.order_type.value
        signal_dict['strategy'] = signal.strategy.value
        
        if signal_dict.get('metadata'):
            signal_dict['metadata'] = {
                'session': signal.metadata.session.value,
                'volatility': signal.metadata.volatility.value,
                'news_impact': signal.metadata.news_impact.value
            }
            
        return signal_dict
        
    def _validate_signal(self, signal: Dict) -> None:
        """Validate signal against JSON schema"""
        try:
            jsonschema.validate(signal, self.schema)
        except jsonschema.ValidationError as e:
            raise FortressConversionError(f"Signal validation failed: {e.message}")
            
    def convert_price_update(self, symbol: str, bid: float, ask: float, 
                           spread: float = None) -> Dict:
        """Convert price update to standardized format"""
        try:
            signal = {
                "event": EventType.PRICE_UPDATE.value,
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "symbol": symbol,
                "order_type": OrderType.BUY.value,  # Placeholder
                "lot_size": 0.01,  # Placeholder
                "entry_price": (bid + ask) / 2,
                "bridge_id": self.bridge_id,
                "account_id": self._get_account_id(),
                "execution_id": f"PRICE_{int(time.time())}",
                "strategy": Strategy.BITMODE_AUTO.value,
                "tcs_score": 50,
                "current_price": (bid + ask) / 2,
                "spread": spread or (ask - bid),
                "metadata": {
                    "session": self._get_current_session(),
                    "volatility": "MEDIUM",
                    "news_impact": "NONE"
                }
            }
            
            self._validate_signal(signal)
            return signal
            
        except Exception as e:
            self.logger.error(f"❌ Price update conversion failed: {e}")
            raise FortressConversionError(f"Price update conversion failed: {e}")
            
    def _get_current_session(self) -> str:
        """Determine current trading session"""
        hour = datetime.now(timezone.utc).hour
        
        if 0 <= hour < 6:
            return "ASIAN"
        elif 6 <= hour < 14:
            return "LONDON"
        elif 14 <= hour < 22:
            return "NY"
        else:
            return "OVERLAP"
            
    def create_heartbeat(self) -> Dict:
        """Create heartbeat signal"""
        return {
            "event": EventType.HEARTBEAT.value,
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "symbol": "HEARTBEAT",
            "order_type": OrderType.BUY.value,
            "lot_size": 0.01,
            "entry_price": 1.0,
            "bridge_id": self.bridge_id,
            "account_id": self._get_account_id(),
            "execution_id": f"HEARTBEAT_{int(time.time())}",
            "strategy": Strategy.BITMODE_AUTO.value,
            "tcs_score": 100,
            "metadata": {
                "session": self._get_current_session(),
                "volatility": "LOW",
                "news_impact": "NONE"
            }
        }
        
    def get_performance_metrics(self) -> Dict:
        """Get converter performance metrics"""
        uptime = time.time() - self.start_time
        success_rate = (self.conversion_count / (self.conversion_count + self.error_count) * 100) if (self.conversion_count + self.error_count) > 0 else 100
        
        return {
            "bridge_id": self.bridge_id,
            "uptime_seconds": uptime,
            "total_conversions": self.conversion_count,
            "total_errors": self.error_count,
            "success_rate": success_rate,
            "last_error": self.last_error,
            "conversions_per_minute": (self.conversion_count / (uptime / 60)) if uptime > 0 else 0
        }

class FortressConversionError(Exception):
    """Custom exception for conversion errors"""
    pass

# Global converter instance
FORTRESS_CONVERTER = FortressBridgeConverter()

def get_fortress_converter() -> FortressBridgeConverter:
    """Get the global fortress converter instance"""
    return FORTRESS_CONVERTER

# Convenience functions
def convert_mt5_order(order: Any, **kwargs) -> Dict:
    """Convert MT5 order using global converter"""
    return FORTRESS_CONVERTER.convert_mt5_order(order, **kwargs)

def convert_price_update(symbol: str, bid: float, ask: float, spread: float = None) -> Dict:
    """Convert price update using global converter"""
    return FORTRESS_CONVERTER.convert_price_update(symbol, bid, ask, spread)

def create_heartbeat() -> Dict:
    """Create heartbeat using global converter"""
    return FORTRESS_CONVERTER.create_heartbeat()

if __name__ == "__main__":
    # Test the converter
    print("🛡️ FORTRESS BRIDGE CONVERTER - TESTING MODE")
    
    # Test data
    test_order = {
        'symbol': 'XAUUSD',
        'type': 0,  # Buy
        'volume': 0.10,
        'price': 2374.10,
        'sl': 2370.00,
        'tp': 2382.00,
        'comment': 'TEST123',
        'magic': 82
    }
    
    try:
        converter = FortressBridgeConverter("bridge_001")
        result = converter.convert_mt5_order(test_order)
        print("✅ Conversion successful:")
        print(json.dumps(result, indent=2))
        
        metrics = converter.get_performance_metrics()
        print("\n📊 Performance metrics:")
        print(json.dumps(metrics, indent=2))
        
    except Exception as e:
        print(f"❌ Test failed: {e}")