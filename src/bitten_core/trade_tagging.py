# trade_tagging.py
# BITTEN Trade Tagging System - Complete Trade Metadata

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import hashlib

class ExecutionType(Enum):
    LIVE = "live"          # Real-time execution on live account
    DEMO = "demo"          # Demo account execution
    GHOST = "ghost"        # Simulated/Paper trade for tracking
    REPLAY = "replay"      # Historical signal being reviewed

class EntryMethod(Enum):
    INSTANT = "instant"    # Fired immediately on signal
    STEALTH = "stealth"    # Delayed entry (2-5 min randomization)
    MANUAL = "manual"      # User triggered despite auto-mode
    CHAINGUN = "chaingun"  # Part of CHAINGUN sequence

class SignalSource(Enum):
    RAPID_ASSAULT_SCAN = "arcade_scan"        # From arcade filter system
    SNIPER_SCAN = "sniper_scan"        # From sniper filter system
    MIDNIGHT_HAMMER = "midnight_hammer" # Special event signal
    ALPHA_OVERRIDE = "alpha_override"   # Manually forced by user
    TEST_MODULE = "test_module"         # Test signals

class QualityMarker(Enum):
    PERFECT_SETUP = "perfect"      # 95%+ TCS score
    HIGH_CONFIDENCE = "high"       # 85-94% TCS
    STANDARD = "standard"          # 70-84% TCS
    MARGINAL = "marginal"          # 65-69% TCS (arcade minimum)

@dataclass
class TradeTags:
    """Complete trade tag structure"""
    trade_id: str
    timestamp: datetime
    user_tier: str
    user_badge: str
    
    # Execution tags
    execution_type: ExecutionType
    entry_method: EntryMethod
    signal_source: SignalSource
    quality_marker: QualityMarker
    
    # Context tags
    session: str
    shadow_index: int
    xp_eligible: bool
    replay_available: bool
    
    # Risk tags
    risk_percent: float
    position_size: float
    concurrent_positions: int
    
    # Special flags
    is_revenge_trade: bool
    cooldown_override: bool
    special_event: Optional[str]

class TradeTaggingSystem:
    """
    Tags every trade with metadata for analysis and user display
    """
    
    def __init__(self):
        self.ghost_log: List[Dict] = []  # Track missed opportunities
        self.tag_history: Dict[str, TradeTags] = {}
        
    def tag_trade(self, signal: Dict, user: Dict, 
                  execution_context: Dict) -> TradeTags:
        """Generate complete trade tags"""
        
        # Generate unique trade ID
        trade_id = self._generate_trade_id(signal, user['id'])
        
        # Determine quality marker based on TCS
        quality_marker = self._calculate_quality_tier(signal.get('tcs_score', 0))
        
        # Create tags
        tags = TradeTags(
            trade_id=trade_id,
            timestamp=datetime.now(),
            user_tier=user.get('tier', 'unknown'),
            user_badge=user.get('badge', 'recruit'),
            
            # Execution tags
            execution_type=self._determine_execution_type(user, signal),
            entry_method=self._determine_entry_method(user, execution_context),
            signal_source=self._determine_signal_source(signal),
            quality_marker=quality_marker,
            
            # Context tags
            session=self._get_market_session(),
            shadow_index=signal.get('shadow_index', 0),
            xp_eligible=self._check_xp_eligibility(signal, user),
            replay_available=True,  # All trades can be replayed
            
            # Risk tags
            risk_percent=execution_context.get('risk_percent', 2.0),
            position_size=execution_context.get('position_size', 0.01),
            concurrent_positions=user.get('open_positions_count', 0),
            
            # Special flags
            is_revenge_trade=self._check_revenge_trade(user),
            cooldown_override=execution_context.get('cooldown_override', False),
            special_event=signal.get('special_event', None)
        )
        
        # Store tags
        self.tag_history[trade_id] = tags
        
        return tags
    
    def _generate_trade_id(self, signal: Dict, user_id: int) -> str:
        """Generate unique trade ID"""
        unique_string = f"{user_id}_{signal.get('symbol')}_{datetime.now().timestamp()}"
        return f"TRD_{hashlib.md5(unique_string.encode()).hexdigest()[:8]}"
    
    def _determine_execution_type(self, user: Dict, signal: Dict) -> ExecutionType:
        """Determine execution type"""
        if signal.get('is_test', False):
            return ExecutionType.GHOST
        elif signal.get('is_replay', False):
            return ExecutionType.REPLAY
        elif user.get('account_type') == 'demo':
            return ExecutionType.DEMO
        else:
            return ExecutionType.LIVE
    
    def _determine_entry_method(self, user: Dict, context: Dict) -> EntryMethod:
        """Determine entry method"""
        if context.get('chaingun_sequence'):
            return EntryMethod.CHAINGUN
        elif context.get('stealth_mode'):
            return EntryMethod.STEALTH
        elif context.get('manual_override'):
            return EntryMethod.MANUAL
        else:
            return EntryMethod.INSTANT
    
    def _determine_signal_source(self, signal: Dict) -> SignalSource:
        """Determine signal source"""
        source = signal.get('triggered_by', 'RAPID_ASSAULT_SCAN')
        
        if 'MIDNIGHT' in source:
            return SignalSource.MIDNIGHT_HAMMER
        elif 'SNIPER' in source or signal.get('signal_type') == 'sniper':
            return SignalSource.SNIPER_SCAN
        elif 'ALPHA' in source:
            return SignalSource.ALPHA_OVERRIDE
        elif 'TEST' in source:
            return SignalSource.TEST_MODULE
        else:
            return SignalSource.RAPID_ASSAULT_SCAN
    
    def _calculate_quality_tier(self, tcs: int) -> QualityMarker:
        """Calculate quality marker from TCS"""
        if tcs >= 95:
            return QualityMarker.PERFECT_SETUP
        elif tcs >= 85:
            return QualityMarker.HIGH_CONFIDENCE
        elif tcs >= 70:
            return QualityMarker.STANDARD
        else:
            return QualityMarker.MARGINAL
    
    def _get_market_session(self) -> str:
        """Get current market session"""
        # This would integrate with market analyzer
        hour = datetime.now().hour
        
        if 3 <= hour < 11:
            if 8 <= hour < 11:
                return "OVERLAP"
            return "LONDON"
        elif 8 <= hour < 17:
            return "NY"
        elif 19 <= hour or hour < 3:
            return "ASIAN"
        else:
            return "DEAD"
    
    def _check_xp_eligibility(self, signal: Dict, user: Dict) -> bool:
        """Check if trade is XP eligible"""
        # Ghost trades don't earn XP
        if signal.get('is_test') or signal.get('execution_type') == 'ghost':
            return False
        
        # Check daily XP limit
        daily_xp = user.get('daily_xp_earned', 0)
        if daily_xp >= 500:  # Daily cap
            return False
            
        return True
    
    def _check_revenge_trade(self, user: Dict) -> bool:
        """Check if this might be a revenge trade"""
        # Look for recent losses
        recent_trades = user.get('recent_trades', [])
        if len(recent_trades) >= 2:
            # Check last 2 trades
            if all(t.get('result') == 'loss' for t in recent_trades[-2:]):
                # Quick succession after losses
                last_trade_time = recent_trades[-1].get('timestamp')
                if last_trade_time:
                    time_since = datetime.now() - last_trade_time
                    if time_since < timedelta(minutes=5):
                        return True
        return False
    
    def display_tags_to_user(self, tags: TradeTags) -> str:
        """User-friendly tag display"""
        quality_emojis = {
            QualityMarker.PERFECT_SETUP: "🔥",
            QualityMarker.HIGH_CONFIDENCE: "⚡",
            QualityMarker.STANDARD: "✅",
            QualityMarker.MARGINAL: "⚠️"
        }
        
        return f"""🏷️ **TRADE TAGS**
• Type: {tags.execution_type.value.upper()} | {tags.entry_method.value.upper()}
• Quality: {quality_emojis.get(tags.quality_marker, '')} {tags.quality_marker.value.upper()} ({tags.shadow_index}% Shadow)
• Session: {tags.session} Market
• Source: {tags.signal_source.value.replace('_', ' ').title()}
• Risk: {tags.risk_percent}% | Positions: {tags.concurrent_positions}
{f'⚠️ Revenge Trade Detected' if tags.is_revenge_trade else ''}"""
    
    def log_ghost_trade(self, signal: Dict, user: Dict, reason: str):
        """Log trades that would have been taken"""
        
        # Only log high quality ghosts
        if signal.get('tcs_score', 0) >= 75:
            ghost_entry = {
                'timestamp': datetime.now(),
                'user_id': user['id'],
                'symbol': signal['symbol'],
                'tcs': signal['tcs_score'],
                'reason_missed': reason,
                'potential_pips': self._calculate_potential_pips(signal),
                'missed_xp': self._calculate_missed_xp(signal),
                'session': self._get_market_session()
            }
            
            self.ghost_log.append(ghost_entry)
            
            # Keep only last 100 ghost trades
            if len(self.ghost_log) > 100:
                self.ghost_log = self.ghost_log[-100:]
    
    def _calculate_potential_pips(self, signal: Dict) -> float:
        """Calculate what trade would have made"""
        # Simplified - in production would check actual price movement
        return signal.get('expected_pips', 15)
    
    def _calculate_missed_xp(self, signal: Dict) -> int:
        """Calculate XP that was missed"""
        base_xp = 10
        tcs_bonus = (signal.get('tcs_score', 70) - 70) * 2
        return int(base_xp + tcs_bonus)
    
    def get_ghost_trades(self, user_id: int, limit: int = 5) -> List[Dict]:
        """Get recent ghost trades for user"""
        user_ghosts = [g for g in self.ghost_log if g['user_id'] == user_id]
        return user_ghosts[-limit:]
    
    def get_trade_by_id(self, trade_id: str) -> Optional[TradeTags]:
        """Retrieve trade tags by ID"""
        return self.tag_history.get(trade_id)