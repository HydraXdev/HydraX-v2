# config_manager.py
# BITTEN Centralized Configuration Manager
# Single source of truth for all trading pairs and system configuration

import yaml
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class PairCategory(Enum):
    """Trading pair categories"""
    MAJOR = "major"
    MINOR = "minor"
    CROSS = "cross"

@dataclass
class TradingPairSpec:
    """Complete specification for a trading pair"""
    symbol: str
    pip_value: float
    min_volume: float
    max_volume: float
    spread_limit: float
    session_hours: List[str]
    volatility_filter: bool
    contract_size: int
    min_lot: float
    max_lot: float
    tcs_requirement: Optional[int]
    category: PairCategory
    description: str
    is_core_pair: bool = False
    is_extra_pair: bool = False

@dataclass
class StrategyConfig:
    """Strategy-specific configuration"""
    name: str
    description: str
    allowed_pairs: List[str]
    min_tcs: int

@dataclass
class SessionConfig:
    """Trading session configuration"""
    name: str
    hours: str
    timezone: str
    optimal_pairs: List[str]
    bonus_multiplier: Optional[float] = None

class TradingPairsConfig:
    """
    Centralized configuration manager for trading pairs
    
    This class provides a single source of truth for all trading pair
    configurations, eliminating scattered definitions across the codebase.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager"""
        if config_path is None:
            # Default path relative to this file
            config_path = Path(__file__).parent.parent.parent / "config" / "trading_pairs.yml"
        
        # Security: Validate and sanitize config path
        self.config_path = self._validate_config_path(config_path)
        self._config_data: Dict[str, Any] = {}
        self._trading_pairs: Dict[str, TradingPairSpec] = {}
        self._strategies: Dict[str, StrategyConfig] = {}
        self._sessions: Dict[str, SessionConfig] = {}
        self._loaded = False
        
        # Load configuration on initialization
        self.load_config()
    
    def _validate_config_path(self, config_path: str) -> Path:
        """Validate and sanitize configuration file path for security"""
        try:
            path = Path(config_path).resolve()
            
            # Security: Ensure path is within allowed directories
            allowed_base = Path(__file__).parent.parent.parent.resolve()
            if not str(path).startswith(str(allowed_base)):
                raise ValueError(f"Configuration path outside allowed directory: {path}")
            
            # Security: Ensure it's a .yml or .yaml file
            if path.suffix.lower() not in ['.yml', '.yaml']:
                raise ValueError(f"Invalid configuration file type: {path.suffix}")
            
            # Security: Check if file exists and is readable
            if not path.exists():
                raise FileNotFoundError(f"Configuration file not found: {path}")
            
            if not path.is_file():
                raise ValueError(f"Configuration path is not a file: {path}")
            
            # Security: Check file permissions (readable but not world-writable)
            import stat
            file_stat = path.stat()
            if file_stat.st_mode & stat.S_IWOTH:
                logger.warning(f"Configuration file is world-writable: {path}")
            
            return path
            
        except Exception as e:
            logger.error(f"Configuration path validation failed")
            raise ValueError("Invalid configuration path") from None
    
    def load_config(self) -> None:
        """Load configuration from YAML file with security validation"""
        try:
            # Security: Additional validation before loading
            if not self.config_path.exists():
                raise FileNotFoundError("Configuration file not found")
            
            # Security: Load with size limit to prevent DoS
            MAX_CONFIG_SIZE = 1024 * 1024  # 1MB limit
            if self.config_path.stat().st_size > MAX_CONFIG_SIZE:
                raise ValueError("Configuration file too large")
            
            with open(self.config_path, 'r', encoding='utf-8') as file:
                # Security: Use safe_load and validate content
                content = file.read()
                if len(content.strip()) == 0:
                    raise ValueError("Configuration file is empty")
                
                self._config_data = yaml.safe_load(content)
                
                # Security: Validate loaded data structure
                if not isinstance(self._config_data, dict):
                    raise ValueError("Invalid configuration structure")
                
                self._validate_config_schema()
            
            self._parse_trading_pairs()
            self._parse_strategies()
            self._parse_sessions()
            self._loaded = True
            
            logger.info("Trading configuration loaded successfully")
            logger.info(f"Total pairs: {len(self._trading_pairs)}")
            
        except Exception as e:
            logger.error("Failed to load trading configuration")
            raise ValueError("Configuration loading failed") from None
    
    def _validate_config_schema(self) -> None:
        """Validate configuration schema for security"""
        required_sections = ['trading_pairs', 'strategy_assignments', 'sessions', 'mt5_mappings']
        
        for section in required_sections:
            if section not in self._config_data:
                raise ValueError(f"Missing required configuration section: {section}")
        
        # Validate trading_pairs structure
        trading_pairs = self._config_data.get('trading_pairs', {})
        if not isinstance(trading_pairs, dict):
            raise ValueError("Invalid trading_pairs structure")
        
        required_subsections = ['core_pairs', 'extra_pairs']
        for subsection in required_subsections:
            if subsection not in trading_pairs:
                raise ValueError(f"Missing required subsection: {subsection}")
            
            if not isinstance(trading_pairs[subsection], dict):
                raise ValueError(f"Invalid {subsection} structure")
        
        # Validate pair specifications
        for category in ['core_pairs', 'extra_pairs']:
            for pair_symbol, pair_config in trading_pairs[category].items():
                self._validate_pair_config(pair_symbol, pair_config)
    
    def _validate_pair_config(self, symbol: str, config: dict) -> None:
        """Validate individual pair configuration for security"""
        # Security: Validate symbol format (prevent injection)
        if not isinstance(symbol, str) or not symbol.isalnum():
            raise ValueError(f"Invalid pair symbol format: {symbol}")
        
        if len(symbol) < 3 or len(symbol) > 8:
            raise ValueError(f"Invalid pair symbol length: {symbol}")
        
        # Security: Validate required fields and types
        required_fields = {
            'pip_value': (float, int),
            'min_volume': (float, int),
            'max_volume': (float, int),
            'spread_limit': (float, int),
            'session_hours': list,
            'volatility_filter': bool,
            'contract_size': int,
            'min_lot': (float, int),
            'max_lot': (float, int),
            'category': str,
            'description': str
        }
        
        for field, expected_type in required_fields.items():
            if field not in config:
                raise ValueError(f"Missing required field '{field}' for pair {symbol}")
            
            if not isinstance(config[field], expected_type):
                raise ValueError(f"Invalid type for field '{field}' in pair {symbol}")
        
        # Security: Validate numeric ranges
        numeric_validations = {
            'pip_value': (0.0001, 100.0),
            'min_volume': (0.001, 1000.0),
            'max_volume': (0.01, 10000.0),
            'spread_limit': (0.1, 100.0),
            'min_lot': (0.001, 1000.0),
            'max_lot': (0.01, 10000.0),
            'contract_size': (1, 1000000)
        }
        
        for field, (min_val, max_val) in numeric_validations.items():
            value = config[field]
            if not (min_val <= value <= max_val):
                raise ValueError(f"Value out of range for '{field}' in pair {symbol}: {value}")
        
        # Security: Validate TCS requirement if present
        if 'tcs_requirement' in config:
            tcs = config['tcs_requirement']
            if tcs is not None and (not isinstance(tcs, int) or not (0 <= tcs <= 100)):
                raise ValueError(f"Invalid TCS requirement for pair {symbol}: {tcs}")
    
    def _parse_trading_pairs(self) -> None:
        """Parse trading pairs from configuration"""
        pairs_data = self._config_data.get('trading_pairs', {})
        
        # Parse core pairs
        for symbol, spec in pairs_data.get('core_pairs', {}).items():
            pair_spec = TradingPairSpec(
                symbol=symbol,
                pip_value=spec['pip_value'],
                min_volume=spec['min_volume'],
                max_volume=spec['max_volume'],
                spread_limit=spec['spread_limit'],
                session_hours=spec['session_hours'],
                volatility_filter=spec['volatility_filter'],
                contract_size=spec['contract_size'],
                min_lot=spec['min_lot'],
                max_lot=spec['max_lot'],
                tcs_requirement=spec['tcs_requirement'],
                category=PairCategory(spec['category']),
                description=spec['description'],
                is_core_pair=True
            )
            self._trading_pairs[symbol] = pair_spec
        
        # Parse extra pairs
        for symbol, spec in pairs_data.get('extra_pairs', {}).items():
            pair_spec = TradingPairSpec(
                symbol=symbol,
                pip_value=spec['pip_value'],
                min_volume=spec['min_volume'],
                max_volume=spec['max_volume'],
                spread_limit=spec['spread_limit'],
                session_hours=spec['session_hours'],
                volatility_filter=spec['volatility_filter'],
                contract_size=spec['contract_size'],
                min_lot=spec['min_lot'],
                max_lot=spec['max_lot'],
                tcs_requirement=spec['tcs_requirement'],
                category=PairCategory(spec['category']),
                description=spec['description'],
                is_extra_pair=True
            )
            self._trading_pairs[symbol] = pair_spec
    
    def _parse_strategies(self) -> None:
        """Parse strategy configurations"""
        strategies_data = self._config_data.get('strategy_assignments', {})
        
        for strategy_name, config in strategies_data.items():
            strategy_config = StrategyConfig(
                name=strategy_name,
                description=config['description'],
                allowed_pairs=config['allowed_pairs'],
                min_tcs=config['min_tcs']
            )
            self._strategies[strategy_name] = strategy_config
    
    def _parse_sessions(self) -> None:
        """Parse session configurations"""
        sessions_data = self._config_data.get('sessions', {})
        
        for session_name, config in sessions_data.items():
            session_config = SessionConfig(
                name=session_name,
                hours=config['hours'],
                timezone=config['timezone'],
                optimal_pairs=config['optimal_pairs'],
                bonus_multiplier=config.get('bonus_multiplier')
            )
            self._sessions[session_name] = session_config
    
    # Trading Pairs Access Methods
    def get_all_pairs(self) -> Dict[str, TradingPairSpec]:
        """Get all trading pairs"""
        return self._trading_pairs.copy()
    
    def get_core_pairs(self) -> Dict[str, TradingPairSpec]:
        """Get core trading pairs only"""
        return {k: v for k, v in self._trading_pairs.items() if v.is_core_pair}
    
    def get_extra_pairs(self) -> Dict[str, TradingPairSpec]:
        """Get extra trading pairs only"""
        return {k: v for k, v in self._trading_pairs.items() if v.is_extra_pair}
    
    def get_pair_spec(self, symbol: str) -> Optional[TradingPairSpec]:
        """Get specification for a specific pair"""
        return self._trading_pairs.get(symbol)
    
    def get_supported_symbols(self) -> List[str]:
        """Get list of all supported symbols"""
        return list(self._trading_pairs.keys())
    
    def is_supported_pair(self, symbol: str) -> bool:
        """Check if a symbol is supported"""
        return symbol in self._trading_pairs
    
    def get_pair_tcs_requirement(self, symbol: str) -> Optional[int]:
        """Get TCS requirement for a specific pair"""
        pair_spec = self.get_pair_spec(symbol)
        return pair_spec.tcs_requirement if pair_spec else None
    
    # Strategy Access Methods
    def get_strategy_config(self, strategy_name: str) -> Optional[StrategyConfig]:
        """Get configuration for a specific strategy"""
        return self._strategies.get(strategy_name)
    
    def get_strategy_pairs(self, strategy_name: str) -> List[str]:
        """Get allowed pairs for a strategy"""
        strategy = self.get_strategy_config(strategy_name)
        return strategy.allowed_pairs if strategy else []
    
    def get_all_strategies(self) -> Dict[str, StrategyConfig]:
        """Get all strategy configurations"""
        return self._strategies.copy()
    
    # Session Access Methods
    def get_session_config(self, session_name: str) -> Optional[SessionConfig]:
        """Get configuration for a trading session"""
        return self._sessions.get(session_name)
    
    def get_session_pairs(self, session_name: str) -> List[str]:
        """Get optimal pairs for a trading session"""
        session = self.get_session_config(session_name)
        return session.optimal_pairs if session else []
    
    def get_all_sessions(self) -> Dict[str, SessionConfig]:
        """Get all session configurations"""
        return self._sessions.copy()
    
    # MT5 Integration Methods
    def get_mt5_mappings(self) -> Dict[str, str]:
        """Get MT5 symbol mappings"""
        return self._config_data.get('mt5_mappings', {})
    
    def get_mt5_symbol(self, internal_symbol: str) -> Optional[str]:
        """Get MT5 symbol for internal symbol"""
        return self.get_mt5_mappings().get(internal_symbol)
    
    # Heat Map Methods
    def get_heat_map_pairs(self) -> List[str]:
        """Get pairs for heat map tracking"""
        heat_map_config = self._config_data.get('heat_map_config', {})
        return heat_map_config.get('tracked_pairs', [])
    
    # Validation Methods
    def validate_pair_for_strategy(self, symbol: str, strategy_name: str) -> Tuple[bool, str]:
        """Validate if a pair is allowed for a strategy"""
        if not self.is_supported_pair(symbol):
            return False, f"Unsupported pair: {symbol}"
        
        strategy = self.get_strategy_config(strategy_name)
        if not strategy:
            return False, f"Unknown strategy: {strategy_name}"
        
        if symbol not in strategy.allowed_pairs:
            return False, f"Pair {symbol} not allowed for strategy {strategy_name}"
        
        return True, "Valid"
    
    def validate_tcs_for_pair(self, symbol: str, tcs_score: int) -> Tuple[bool, str]:
        """Validate TCS score against pair requirements"""
        pair_spec = self.get_pair_spec(symbol)
        if not pair_spec:
            return False, f"Unknown pair: {symbol}"
        
        if pair_spec.tcs_requirement and tcs_score < pair_spec.tcs_requirement:
            return False, f"TCS too low for {symbol}: {tcs_score} < {pair_spec.tcs_requirement}"
        
        return True, "Valid"
    
    # Legacy Compatibility Methods (for gradual migration)
    def get_fire_router_pairs(self) -> Dict[str, Dict]:
        """Get pairs in fire_router format for compatibility"""
        pairs_dict = {}
        for symbol, spec in self._trading_pairs.items():
            pairs_dict[symbol] = {
                'pip_value': spec.pip_value,
                'min_volume': spec.min_volume,
                'max_volume': spec.max_volume,
                'spread_limit': spec.spread_limit,
                'session_hours': spec.session_hours,
                'volatility_filter': spec.volatility_filter
            }
        return pairs_dict
    
    def get_pair_specific_tcs(self) -> Dict[str, Optional[int]]:
        """Get pair-specific TCS requirements in fire_modes format"""
        tcs_dict = {}
        for symbol, spec in self._trading_pairs.items():
            tcs_dict[symbol] = spec.tcs_requirement
        return tcs_dict
    
    def get_risk_management_specs(self) -> Dict[str, Dict]:
        """Get pairs in risk_management format for compatibility"""
        specs_dict = {}
        for symbol, spec in self._trading_pairs.items():
            specs_dict[symbol] = {
                'pip_value': spec.pip_value,
                'contract_size': spec.contract_size,
                'min_lot': spec.min_lot,
                'max_lot': spec.max_lot
            }
        return specs_dict
    
    # Configuration Info Methods
    def get_config_info(self) -> Dict[str, Any]:
        """Get configuration metadata"""
        return self._config_data.get('metadata', {})
    
    def get_total_pairs_count(self) -> int:
        """Get total number of supported pairs"""
        return len(self._trading_pairs)
    
    def get_core_pairs_count(self) -> int:
        """Get number of core pairs"""
        return len(self.get_core_pairs())
    
    def get_extra_pairs_count(self) -> int:
        """Get number of extra pairs"""
        return len(self.get_extra_pairs())
    
    def is_loaded(self) -> bool:
        """Check if configuration is loaded"""
        return self._loaded

# Global configuration instance with thread safety
import threading
_global_config: Optional[TradingPairsConfig] = None
_config_lock = threading.Lock()

def get_trading_config() -> TradingPairsConfig:
    """Get global trading configuration instance (thread-safe)"""
    global _global_config
    
    # Security: Thread-safe singleton pattern
    if _global_config is None:
        with _config_lock:
            # Double-check locking pattern
            if _global_config is None:
                _global_config = TradingPairsConfig()
    
    return _global_config

def reload_trading_config() -> TradingPairsConfig:
    """Reload global trading configuration (thread-safe)"""
    global _global_config
    
    with _config_lock:
        _global_config = TradingPairsConfig()
    
    return _global_config

# Convenience functions for common operations
def get_all_supported_pairs() -> List[str]:
    """Get list of all supported trading pairs"""
    return get_trading_config().get_supported_symbols()

def is_pair_supported(symbol: str) -> bool:
    """Check if a trading pair is supported"""
    return get_trading_config().is_supported_pair(symbol)

def get_pair_tcs_requirement(symbol: str) -> Optional[int]:
    """Get TCS requirement for a trading pair"""
    return get_trading_config().get_pair_tcs_requirement(symbol)

def validate_pair_tcs(symbol: str, tcs_score: int) -> Tuple[bool, str]:
    """Validate TCS score for a trading pair"""
    return get_trading_config().validate_tcs_for_pair(symbol, tcs_score)

# Example usage and testing
if __name__ == "__main__":
    # Test the configuration system
    config = TradingPairsConfig()
    
    print("=== BITTEN Trading Configuration Test ===")
    print(f"Total pairs: {config.get_total_pairs_count()}")
    print(f"Core pairs: {config.get_core_pairs_count()}")
    print(f"Extra pairs: {config.get_extra_pairs_count()}")
    
    print("\nCore pairs:")
    for symbol in config.get_core_pairs():
        print(f"  {symbol}")
    
    print("\nExtra pairs (85% TCS required):")
    for symbol in config.get_extra_pairs():
        print(f"  {symbol}")
    
    print("\nStrategy configurations:")
    for strategy_name, strategy in config.get_all_strategies().items():
        print(f"  {strategy_name}: {len(strategy.allowed_pairs)} pairs")
    
    print("\nValidation tests:")
    print(f"GBPUSD supported: {config.is_supported_pair('GBPUSD')}")
    print(f"XAUUSD supported: {config.is_supported_pair('XAUUSD')}")  # Should be False
    print(f"AUDUSD TCS requirement: {config.get_pair_tcs_requirement('AUDUSD')}")
    
    is_valid, msg = config.validate_tcs_for_pair('AUDUSD', 80)
    print(f"AUDUSD with 80% TCS: {is_valid} - {msg}")
    
    is_valid, msg = config.validate_tcs_for_pair('AUDUSD', 90)
    print(f"AUDUSD with 90% TCS: {is_valid} - {msg}")