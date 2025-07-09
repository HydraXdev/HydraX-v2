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

@dataclass
class TierConfig:
    """Tier-specific configuration"""
    name: str
    monthly_price: int
    # Fire settings
    daily_shots: int
    min_tcs: int
    risk_per_shot: float
    # Risk control
    default_risk: float
    boost_risk: float
    boost_min_balance: float
    max_trades_per_day: int
    max_open_trades: int
    drawdown_cap: float
    cooldown_mode: str
    cooldown_hours: int
    cooldown_max_trades: int
    cooldown_risk: float
    # Features
    has_chaingun: bool
    has_autofire: bool
    has_stealth: bool
    has_sniper_access: bool
    has_midnight_hammer: bool
    fire_type: str
    # Position management
    min_balance: float
    max_concurrent_positions: int

@dataclass 
class TradeSizeValidation:
    """Trade size validation configuration"""
    enabled: bool
    max_risk_per_trade: float
    safety_multiplier: float
    min_lot_size: float
    max_lot_size: float

class TradingPairsConfig:
    """
    Centralized configuration manager for trading pairs and tier settings
    
    This class provides a single source of truth for all trading pair
    configurations and tier settings, eliminating scattered definitions across the codebase.
    """
    
    def __init__(self, config_path: Optional[str] = None, tier_config_path: Optional[str] = None):
        """Initialize configuration manager"""
        if config_path is None:
            # Default path relative to this file
            config_path = Path(__file__).parent.parent.parent / "config" / "trading_pairs.yml"
            
        if tier_config_path is None:
            # Default tier config path
            tier_config_path = Path(__file__).parent.parent.parent / "config" / "tier_settings.yml"
        
        # Security: Validate and sanitize config paths
        self.config_path = self._validate_config_path(config_path)
        self.tier_config_path = self._validate_config_path(tier_config_path)
        self._config_data: Dict[str, Any] = {}
        self._tier_config_data: Dict[str, Any] = {}
        self._trading_pairs: Dict[str, TradingPairSpec] = {}
        self._strategies: Dict[str, StrategyConfig] = {}
        self._sessions: Dict[str, SessionConfig] = {}
        self._tiers: Dict[str, TierConfig] = {}
        self._position_limits: Dict[float, int] = {}
        self._trade_size_validation: Optional[TradeSizeValidation] = None
        self._global_safety: Dict[str, Any] = {}
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
        """Load configuration from YAML files with security validation"""
        try:
            # Load trading pairs configuration
            # Security: Additional validation before loading
            if not self.config_path.exists():
                raise FileNotFoundError("Trading pairs configuration file not found")
            
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
            
            # Load tier settings configuration
            if self.tier_config_path.exists():
                if self.tier_config_path.stat().st_size > MAX_CONFIG_SIZE:
                    raise ValueError("Tier configuration file too large")
                
                with open(self.tier_config_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    if len(content.strip()) == 0:
                        raise ValueError("Tier configuration file is empty")
                    
                    self._tier_config_data = yaml.safe_load(content)
                    
                    if not isinstance(self._tier_config_data, dict):
                        raise ValueError("Invalid tier configuration structure")
                    
                    self._validate_tier_config_schema()
                    self._parse_tier_settings()
            else:
                logger.warning("Tier configuration file not found, using defaults")
            
            self._parse_trading_pairs()
            self._parse_strategies()
            self._parse_sessions()
            self._loaded = True
            
            logger.info("Configuration loaded successfully")
            logger.info(f"Total pairs: {len(self._trading_pairs)}")
            logger.info(f"Total tiers: {len(self._tiers)}")
            
        except Exception as e:
            logger.error("Failed to load configuration")
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
    
    def _validate_tier_config_schema(self) -> None:
        """Validate tier configuration schema"""
        required_sections = ['position_limits', 'tiers', 'global_safety']
        
        for section in required_sections:
            if section not in self._tier_config_data:
                raise ValueError(f"Missing required tier configuration section: {section}")
        
        # Validate tier structure
        tiers = self._tier_config_data.get('tiers', {})
        if not isinstance(tiers, dict):
            raise ValueError("Invalid tiers structure")
        
        required_tiers = ['NIBBLER', 'FANG', 'COMMANDER', 'APEX']
        for tier_name in required_tiers:
            if tier_name not in tiers:
                raise ValueError(f"Missing required tier: {tier_name}")
            
            self._validate_tier_config(tier_name, tiers[tier_name])
    
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
    
    def _validate_tier_config(self, tier_name: str, config: dict) -> None:
        """Validate individual tier configuration"""
        # Validate required sections
        required_sections = ['pricing', 'fire_settings', 'risk_control', 'features', 'position_management']
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required section '{section}' for tier {tier_name}")
        
        # Validate fire settings
        fire_settings = config['fire_settings']
        required_fire = ['daily_shots', 'min_tcs', 'risk_per_shot']
        for field in required_fire:
            if field not in fire_settings:
                raise ValueError(f"Missing required fire setting '{field}' for tier {tier_name}")
        
        # Validate risk control
        risk_control = config['risk_control']
        required_risk = ['default_risk', 'boost_risk', 'max_trades_per_day', 'drawdown_cap']
        for field in required_risk:
            if field not in risk_control:
                raise ValueError(f"Missing required risk control '{field}' for tier {tier_name}")
        
        # Validate numeric ranges
        if not (0 <= fire_settings['min_tcs'] <= 100):
            raise ValueError(f"Invalid min_tcs for tier {tier_name}")
        
        if not (0 < fire_settings['risk_per_shot'] <= 10):
            raise ValueError(f"Invalid risk_per_shot for tier {tier_name}")
        
        if not (0 < risk_control['drawdown_cap'] <= 20):
            raise ValueError(f"Invalid drawdown_cap for tier {tier_name}")
    
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
    
    def _parse_tier_settings(self) -> None:
        """Parse tier settings from configuration"""
        # Parse position limits
        position_limits = self._tier_config_data.get('position_limits', {}).get('balance_thresholds', {})
        self._position_limits = {float(k): v for k, v in position_limits.items()}
        
        # Parse global safety settings
        self._global_safety = self._tier_config_data.get('global_safety', {})
        
        # Parse trade size validation
        trade_validation = self._global_safety.get('trade_size_validation', {})
        if trade_validation:
            self._trade_size_validation = TradeSizeValidation(
                enabled=trade_validation.get('enabled', True),
                max_risk_per_trade=trade_validation.get('max_risk_per_trade', 2.0),
                safety_multiplier=trade_validation.get('safety_multiplier', 0.95),
                min_lot_size=trade_validation.get('min_lot_size', 0.01),
                max_lot_size=trade_validation.get('max_lot_size', 100.0)
            )
        
        # Parse tier configurations
        tiers_data = self._tier_config_data.get('tiers', {})
        for tier_name, tier_config in tiers_data.items():
            pricing = tier_config['pricing']
            fire_settings = tier_config['fire_settings']
            risk_control = tier_config['risk_control']
            features = tier_config['features']
            position_mgmt = tier_config['position_management']
            
            tier = TierConfig(
                name=tier_name,
                monthly_price=pricing['monthly_price'],
                # Fire settings
                daily_shots=fire_settings['daily_shots'],
                min_tcs=fire_settings['min_tcs'],
                risk_per_shot=fire_settings['risk_per_shot'],
                # Risk control
                default_risk=risk_control['default_risk'],
                boost_risk=risk_control['boost_risk'],
                boost_min_balance=risk_control.get('boost_min_balance', 500),
                max_trades_per_day=risk_control['max_trades_per_day'],
                max_open_trades=risk_control.get('max_open_trades', 1),
                drawdown_cap=risk_control['drawdown_cap'],
                cooldown_mode=risk_control.get('cooldown_mode', 'time_based'),
                cooldown_hours=risk_control.get('cooldown_hours', 0),
                cooldown_max_trades=risk_control.get('cooldown_max_trades', 6),
                cooldown_risk=risk_control.get('cooldown_risk', 1.0),
                # Features
                has_chaingun=features.get('has_chaingun', False),
                has_autofire=features.get('has_autofire', False),
                has_stealth=features.get('has_stealth', False),
                has_sniper_access=features.get('has_sniper_access', False),
                has_midnight_hammer=features.get('has_midnight_hammer', False),
                fire_type=features.get('fire_type', 'manual'),
                # Position management
                min_balance=position_mgmt['min_balance'],
                max_concurrent_positions=position_mgmt['max_concurrent_positions']
            )
            self._tiers[tier_name] = tier
    
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
    
    # Tier Configuration Access Methods
    def get_tier_config(self, tier_name: str) -> Optional[TierConfig]:
        """Get configuration for a specific tier"""
        return self._tiers.get(tier_name.upper())
    
    def get_all_tiers(self) -> Dict[str, TierConfig]:
        """Get all tier configurations"""
        return self._tiers.copy()
    
    def get_tier_names(self) -> List[str]:
        """Get list of tier names"""
        return list(self._tiers.keys())
    
    def get_position_limits(self) -> Dict[float, int]:
        """Get position limits by balance"""
        return self._position_limits.copy()
    
    def get_position_limit_for_balance(self, balance: float) -> int:
        """Get position limit for a specific balance"""
        # Find the highest threshold <= balance
        applicable_limits = [(threshold, limit) for threshold, limit in self._position_limits.items() if threshold <= balance]
        if not applicable_limits:
            return 1  # Default to 1 position if balance is below all thresholds
        
        # Return the limit for the highest applicable threshold
        return max(applicable_limits, key=lambda x: x[0])[1]
    
    def get_trade_size_validation(self) -> Optional[TradeSizeValidation]:
        """Get trade size validation configuration"""
        return self._trade_size_validation
    
    def get_global_safety_setting(self, setting_name: str) -> Any:
        """Get a specific global safety setting"""
        return self._global_safety.get(setting_name)
    
    def validate_trade_size(self, lot_size: float, stop_loss_pips: float, pip_value: float, 
                          account_balance: float, tier_name: str) -> Tuple[bool, str]:
        """Validate if a trade size is within safety limits"""
        if not self._trade_size_validation or not self._trade_size_validation.enabled:
            return True, "Trade size validation disabled"
        
        # Calculate risk amount
        risk_amount = lot_size * stop_loss_pips * pip_value
        risk_percentage = (risk_amount / account_balance) * 100
        
        # Check against max risk per trade
        max_risk = self._trade_size_validation.max_risk_per_trade
        if risk_percentage > max_risk:
            return False, f"Trade risk {risk_percentage:.2f}% exceeds maximum {max_risk}%"
        
        # Check lot size limits
        if lot_size < self._trade_size_validation.min_lot_size:
            return False, f"Lot size {lot_size} below minimum {self._trade_size_validation.min_lot_size}"
        
        if lot_size > self._trade_size_validation.max_lot_size:
            return False, f"Lot size {lot_size} exceeds maximum {self._trade_size_validation.max_lot_size}"
        
        # Check against tier drawdown cap
        tier_config = self.get_tier_config(tier_name)
        if tier_config and risk_percentage > tier_config.drawdown_cap:
            return False, f"Trade risk exceeds tier daily drawdown cap of {tier_config.drawdown_cap}%"
        
        return True, "Trade size validated"
    
    def calculate_safe_lot_size(self, stop_loss_pips: float, pip_value: float, 
                               account_balance: float, tier_name: str) -> float:
        """Calculate the maximum safe lot size for a trade"""
        if not self._trade_size_validation:
            return 0.01  # Default minimum
        
        tier_config = self.get_tier_config(tier_name)
        if not tier_config:
            return 0.01
        
        # Use the lower of: trade validation max risk or tier default risk
        max_risk_pct = min(
            self._trade_size_validation.max_risk_per_trade,
            tier_config.default_risk
        )
        
        # Calculate maximum risk amount
        max_risk_amount = account_balance * (max_risk_pct / 100)
        
        # Calculate lot size
        if stop_loss_pips > 0 and pip_value > 0:
            lot_size = max_risk_amount / (stop_loss_pips * pip_value)
            
            # Apply safety multiplier
            lot_size *= self._trade_size_validation.safety_multiplier
            
            # Enforce lot size limits
            lot_size = max(lot_size, self._trade_size_validation.min_lot_size)
            lot_size = min(lot_size, self._trade_size_validation.max_lot_size)
            
            # Round to 2 decimal places
            return round(lot_size, 2)
        
        return self._trade_size_validation.min_lot_size

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