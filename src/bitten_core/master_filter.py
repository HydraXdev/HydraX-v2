# master_filter.py
# BITTEN Master Filter - The Complete Trading Brain

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from .arcade_filter import ArcadeFilter, ArcadeSignal
from .sniper_filter import SniperFilter, SniperSignal
from .position_manager import PositionManager, DrawdownProtection, OpenPosition
from .fire_modes import TierLevel, FireModeValidator, FireMode
import logging

logger = logging.getLogger(__name__)

@dataclass
class FilteredSignal:
    """Unified signal format for display"""
    signal_type: str  # 'arcade' or 'sniper'
    display_type: str  # 'DAWN RAID' or 'SNIPER SHOT'
    symbol: str
    direction: str
    entry_price: float
    stop_loss: float
    take_profit: float
    tcs_score: int
    expected_pips: int
    expected_duration: int
    can_execute: bool
    restriction_reason: str
    visual_card: str

class MasterFilter:
    """
    BITTEN MASTER FILTERING ENGINE
    
    Coordinates all filters, manages positions, enforces THE LAW.
    This is the brain that makes everything work together.
    """
    
    def __init__(self):
        # Initialize all subsystems
        self.arcade_filter = ArcadeFilter()
        self.sniper_filter = SniperFilter()
        self.position_manager = PositionManager()
        self.drawdown_protection = DrawdownProtection()
        self.fire_validator = FireModeValidator()
        
        # Signal tracking
        self.active_signals: Dict[str, FilteredSignal] = {}  # signal_id -> signal
        self.signal_history: List[FilteredSignal] = []
        
        # User state tracking
        self.user_states: Dict[int, Dict] = {}  # user_id -> state info
        
    def process_market_update(self, market_data: Dict[str, Dict]) -> Dict[str, List[FilteredSignal]]:
        """
        Main processing loop - runs all filters and generates signals
        
        Returns:
        {
            'arcade': [signals],
            'sniper': [signals],
            'special': [signals]
        }
        """
        results = {
            'arcade': [],
            'sniper': [],
            'special': []
        }
        
        # Run arcade filter (65%+ TCS)
        arcade_signals = self.arcade_filter.scan_all_pairs(market_data)
        for signal in arcade_signals:
            filtered = self._process_arcade_signal(signal)
            if filtered:
                results['arcade'].append(filtered)
        
        # Run sniper filter (75%+ TCS)
        sniper_signals = self.sniper_filter.scan_for_snipers(market_data)
        for signal in sniper_signals:
            filtered = self._process_sniper_signal(signal)
            if filtered:
                results['sniper'].append(filtered)
        
        # Check for special events
        special = self._check_special_events(market_data)
        if special:
            results['special'].extend(special)
        
        # Log summary
        logger.info(f"Signals generated - Arcade: {len(results['arcade'])}, "
                   f"Sniper: {len(results['sniper'])}, Special: {len(results['special'])}")
        
        return results
    
    def validate_shot(self, user_id: int, signal_id: str, tier: TierLevel, 
                     balance: float) -> Tuple[bool, str, Optional[Dict]]:
        """
        Validate if user can execute a specific signal
        
        Returns: (authorized, message, execution_params)
        """
        
        # Get signal
        signal = self.active_signals.get(signal_id)
        if not signal:
            return False, "Signal not found or expired", None
        
        # Update user state
        if user_id not in self.user_states:
            self.user_states[user_id] = {
                'tier': tier,
                'balance': balance,
                'last_update': datetime.now()
            }
        
        # 1. Check drawdown protection
        dd_ok, dd_msg = self.drawdown_protection.check_drawdown_status(user_id, balance)
        if not dd_ok:
            return False, dd_msg, None
        
        # 2. Check position limits
        pos_ok, pos_msg = self.position_manager.can_open_position(
            user_id, tier, balance, signal.signal_type
        )
        if not pos_ok:
            return False, pos_msg, None
        
        # 3. Check fire mode authorization
        fire_mode = FireMode.SINGLE_SHOT  # Default
        fire_ok, fire_msg = self.fire_validator.can_fire(
            user_id, tier, fire_mode, signal.tcs_score
        )
        if not fire_ok:
            return False, fire_msg, None
        
        # 4. Calculate position size based on risk
        position_size = self._calculate_position_size(balance, signal)
        
        # 5. Create execution parameters
        execution_params = {
            'signal': signal,
            'position_size': position_size,
            'risk_amount': balance * 0.02,  # 2% risk
            'fire_mode': fire_mode,
            'timestamp': datetime.now()
        }
        
        return True, "SHOT AUTHORIZED", execution_params
    
    def execute_shot(self, user_id: int, execution_params: Dict) -> Dict:
        """Execute the trade and update all tracking"""
        
        signal = execution_params['signal']
        
        # Create position record
        position = OpenPosition(
            position_id=f"POS_{user_id}_{datetime.now().timestamp()}",
            symbol=signal.symbol,
            direction=signal.direction,
            volume=execution_params['position_size'],
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            open_time=datetime.now(),
            position_type=signal.signal_type,
            risk_amount=execution_params['risk_amount']
        )
        
        # Record position
        self.position_manager.open_position(user_id, position)
        
        # Record shot fired
        self.fire_validator.record_shot(user_id, execution_params['fire_mode'])
        
        # Move signal to history
        self.signal_history.append(signal)
        
        return {
            'success': True,
            'position_id': position.position_id,
            'message': self._format_execution_message(signal, position)
        }
    
    def _process_arcade_signal(self, signal: ArcadeSignal) -> Optional[FilteredSignal]:
        """Process arcade signal into filtered format"""
        
        # Create display card
        visual_card = self.arcade_filter.format_signal_card(signal)
        
        # Strategy display names
        display_names = {
            'dawn_raid': 'DAWN RAID',
            'wall_defender': 'WALL DEFENDER',
            'rocket_ride': 'ROCKET RIDE',
            'rubber_band': 'RUBBER BAND'
        }
        
        filtered = FilteredSignal(
            signal_type='arcade',
            display_type=display_names.get(signal.strategy.value, 'ARCADE'),
            symbol=signal.symbol,
            direction=signal.direction,
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            tcs_score=signal.tcs_score,
            expected_pips=int(abs(signal.take_profit - signal.entry_price) / 
                             (0.0001 if not signal.symbol.endswith('JPY') else 0.01)),
            expected_duration=signal.expected_duration,
            can_execute=True,  # Will be validated per user
            restriction_reason='',
            visual_card=visual_card
        )
        
        # Store in active signals
        signal_id = f"ARC_{signal.symbol}_{datetime.now().timestamp()}"
        self.active_signals[signal_id] = filtered
        
        return filtered
    
    def _process_sniper_signal(self, signal: SniperSignal) -> Optional[FilteredSignal]:
        """Process sniper signal - NEVER reveal strategy"""
        
        # Create classified display card
        visual_card = self.sniper_filter.format_sniper_card(signal)
        
        filtered = FilteredSignal(
            signal_type='sniper',
            display_type='🎯 SNIPER SHOT',  # ALWAYS this name
            symbol=signal.symbol,
            direction=signal.direction,
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            tcs_score=signal.tcs_score,
            expected_pips=signal.expected_pips,
            expected_duration=signal.max_duration,
            can_execute=True,
            restriction_reason='',
            visual_card=visual_card
        )
        
        # Store with hash
        signal_id = f"SNP_{signal.signal_hash}"
        self.active_signals[signal_id] = filtered
        
        return filtered
    
    def _check_special_events(self, market_data: Dict) -> List[FilteredSignal]:
        """Check for special events like MIDNIGHT HAMMER"""
        
        special_signals = []
        
        # Check MIDNIGHT HAMMER conditions
        if self._check_midnight_hammer_conditions(market_data):
            hammer = self._create_midnight_hammer_signal(market_data)
            if hammer:
                special_signals.append(hammer)
        
        return special_signals
    
    def _check_midnight_hammer_conditions(self, market_data: Dict) -> bool:
        """Check if MIDNIGHT HAMMER should trigger"""
        
        # Check time (around midnight EST)
        current_hour = datetime.now().hour
        if not (23 <= current_hour or current_hour <= 1):
            return False
        
        # Check for ultra-high TCS signal
        for pair_data in market_data.values():
            if pair_data.get('best_tcs', 0) >= 95:
                # Check user participation (would need active user count)
                # For now, random chance to simulate
                import random
                if random.random() < 0.05:  # 5% chance when conditions met
                    return True
        
        return False
    
    def _create_midnight_hammer_signal(self, market_data: Dict) -> Optional[FilteredSignal]:
        """Create MIDNIGHT HAMMER event signal"""
        
        # Find the best signal
        best_signal = None
        best_tcs = 0
        
        for symbol, data in market_data.items():
            if data.get('best_tcs', 0) > best_tcs:
                best_tcs = data['best_tcs']
                best_signal = {
                    'symbol': symbol,
                    'direction': data.get('signal_direction', 'buy'),
                    'entry': data.get('current_price', 0)
                }
        
        if not best_signal:
            return None
        
        visual_card = """🔨🔨🔨 MIDNIGHT HAMMER EVENT 🔨🔨🔨
      COMMUNITY SHOT READY!
         TCS: 96%
      5% RISK = 50+ PIPS
    [JOIN THE HAMMER!]
🔨🔨🔨🔨🔨🔨🔨🔨🔨🔨🔨🔨🔨🔨"""
        
        return FilteredSignal(
            signal_type='special',
            display_type='MIDNIGHT HAMMER',
            symbol=best_signal['symbol'],
            direction=best_signal['direction'],
            entry_price=best_signal['entry'],
            stop_loss=0,  # Will be calculated
            take_profit=0,  # Will be calculated
            tcs_score=best_tcs,
            expected_pips=50,
            expected_duration=120,
            can_execute=True,
            restriction_reason='',
            visual_card=visual_card
        )
    
    def _calculate_position_size(self, balance: float, signal: FilteredSignal) -> float:
        """Calculate position size based on 2% risk"""
        
        pip_value = 0.0001 if not signal.symbol.endswith('JPY') else 0.01
        stop_pips = abs(signal.entry_price - signal.stop_loss) / pip_value
        
        # Risk 2% of balance
        risk_amount = balance * 0.02
        
        # Calculate lot size
        # Assuming $10 per pip for 1 standard lot
        pip_dollar_value = 10  # Simplified
        
        lot_size = risk_amount / (stop_pips * pip_dollar_value)
        
        # Round to 2 decimal places
        return round(lot_size, 2)
    
    def _format_execution_message(self, signal: FilteredSignal, position: OpenPosition) -> str:
        """Format execution confirmation message"""
        
        return f"""🔫 **SHOT FIRED!**

📍 {signal.display_type} - {signal.symbol}
🎯 Direction: {signal.direction.upper()}
💰 Entry: {position.entry_price:.5f}
🛡️ Stop: {position.stop_loss:.5f}
🎖️ Target: {position.take_profit:.5f}
📊 Size: {position.volume} lots
⚡ Risk: ${position.risk_amount:.2f}

Position ID: {position.position_id}
Good hunting, soldier! 🎖️"""
    
    def get_user_dashboard(self, user_id: int) -> Dict:
        """Get complete user dashboard data"""
        
        # Get all subsystem data
        position_status = self.position_manager.get_user_status(user_id)
        fire_stats = self.fire_validator.get_user_stats(user_id)
        dd_status = self.drawdown_protection.check_drawdown_status(
            user_id, 
            self.user_states.get(user_id, {}).get('balance', 1000)
        )
        
        return {
            'positions': position_status,
            'fire_stats': fire_stats,
            'drawdown_status': dd_status,
            'active_signals': len([s for s in self.active_signals.values() 
                                 if s.can_execute]),
            'last_update': datetime.now()
        }
    
    def close_position(self, user_id: int, position_id: str, 
                      result: str, pnl: float) -> bool:
        """Close position and update all systems"""
        
        # Close in position manager
        success = self.position_manager.close_position(user_id, position_id, result, pnl)
        
        if success:
            # Update drawdown protection
            balance = self.user_states.get(user_id, {}).get('balance', 1000)
            self.drawdown_protection.record_trade_result(user_id, pnl, balance)
        
        return success
    
    def reset_daily_systems(self):
        """Reset all daily counters (run at midnight)"""
        self.position_manager.reset_daily_risk()
        self.drawdown_protection.reset_daily_stats()
        self.fire_validator.reset_daily_counters()
        self.active_signals.clear()  # Clear old signals