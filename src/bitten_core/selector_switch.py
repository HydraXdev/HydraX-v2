# selector_switch.py
# BITTEN Commander Selector Switch - SAFE / SEMI / FULL AUTO Control

from enum import Enum
from typing import Dict, Optional, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
import logging

logger = logging.getLogger(__name__)

class SelectorMode(Enum):
    """Commander selector switch positions"""
    SAFE = "safe"      # Manual only - just display signals
    SEMI = "semi"      # Ask for confirmation on each shot
    FULL = "full"      # Full autonomous 24/7 operation

@dataclass
class AutoFireConfig:
    """Configuration for AUTO-FIRE mode"""
    min_tcs: int = 91              # Minimum TCS for auto execution
    max_positions: int = 3          # Maximum concurrent positions
    max_daily_risk: float = 0.10    # 10% daily risk maximum
    news_blackout: bool = True      # Pause for news events
    session_filter: bool = False    # Trade all sessions
    arcade_enabled: bool = True     # Auto-fire arcade signals
    sniper_enabled: bool = True     # Auto-fire sniper signals
    
@dataclass
class SemiAutoConfig:
    """Configuration for SEMI-AUTO mode"""
    confirmation_timeout: int = 60  # Seconds to wait for confirmation
    auto_reject_on_timeout: bool = True
    show_analysis: bool = True      # Show detailed analysis in popup
    
class CommanderSelector:
    """
    COMMANDER TIER SELECTOR SWITCH
    
    Controls execution mode for advanced traders.
    SAFE / SEMI / FULL AUTO operation modes.
    """
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.mode = SelectorMode.SAFE  # Default to safe
        self.auto_config = AutoFireConfig()
        self.semi_config = SemiAutoConfig()
        
        # Tracking
        self.mode_changed_at = datetime.now()
        self.auto_executions_today = 0
        self.pending_confirmations: Dict[str, Dict] = {}
        
        # Callbacks for UI integration
        self.confirmation_callback: Optional[Callable] = None
        self.execution_callback: Optional[Callable] = None
        
    def set_mode(self, mode: SelectorMode) -> Tuple[bool, str]:
        """Change selector mode with validation"""
        
        old_mode = self.mode
        
        # Validate mode change
        if mode == SelectorMode.FULL:
            # Additional checks for FULL AUTO
            if not self._validate_auto_requirements():
                return False, "Account requirements not met for FULL AUTO"
        
        self.mode = mode
        self.mode_changed_at = datetime.now()
        
        logger.info(f"User {self.user_id} switched from {old_mode.value} to {mode.value}")
        
        # Reset relevant counters
        if mode == SelectorMode.SAFE:
            self.pending_confirmations.clear()
        
        return True, f"Selector switched to {mode.value.upper()} mode"
    
    def process_signal(self, signal: Dict, can_execute: bool) -> Dict:
        """
        Process signal based on current selector mode
        
        Returns action to take
        """
        
        if not can_execute:
            # Just display, regardless of mode
            return {
                'action': 'display_only',
                'reason': signal.get('restriction_reason', 'Cannot execute'),
                'mode': self.mode.value
            }
        
        # Process based on mode
        if self.mode == SelectorMode.SAFE:
            return self._process_safe_mode(signal)
        
        elif self.mode == SelectorMode.SEMI:
            return self._process_semi_mode(signal)
            
        elif self.mode == SelectorMode.FULL:
            return self._process_full_auto(signal)
    
    def _process_safe_mode(self, signal: Dict) -> Dict:
        """SAFE mode - manual only"""
        
        return {
            'action': 'display_only',
            'message': 'SAFE MODE - Manual execution required',
            'signal': signal,
            'show_fire_button': True
        }
    
    def _process_semi_mode(self, signal: Dict) -> Dict:
        """SEMI mode - request confirmation"""
        
        # Create confirmation request
        confirmation_id = f"CONF_{signal['symbol']}_{datetime.now().timestamp()}"
        
        self.pending_confirmations[confirmation_id] = {
            'signal': signal,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(seconds=self.semi_config.confirmation_timeout)
        }
        
        # Build confirmation popup data
        analysis = self._build_signal_analysis(signal) if self.semi_config.show_analysis else ""
        
        return {
            'action': 'request_confirmation',
            'confirmation_id': confirmation_id,
            'timeout': self.semi_config.confirmation_timeout,
            'popup_data': {
                'title': f"Execute {signal['display_type']}?",
                'signal': signal,
                'analysis': analysis,
                'buttons': [
                    {'text': '🔫 FIRE', 'action': 'confirm'},
                    {'text': '❌ SKIP', 'action': 'reject'}
                ]
            }
        }
    
    def _process_full_auto(self, signal: Dict) -> Dict:
        """FULL AUTO mode - autonomous execution"""
        
        # Check auto-fire criteria
        if signal['tcs_score'] < self.auto_config.min_tcs:
            return {
                'action': 'auto_rejected',
                'reason': f"TCS {signal['tcs_score']} < {self.auto_config.min_tcs} minimum"
            }
        
        # Check signal type filters
        if signal['signal_type'] == 'arcade' and not self.auto_config.arcade_enabled:
            return {
                'action': 'auto_rejected',
                'reason': 'Arcade signals disabled in AUTO mode'
            }
        
        if signal['signal_type'] == 'sniper' and not self.auto_config.sniper_enabled:
            return {
                'action': 'auto_rejected',
                'reason': 'Sniper signals disabled in AUTO mode'
            }
        
        # All checks passed - execute
        self.auto_executions_today += 1
        
        return {
            'action': 'auto_execute',
            'message': f"AUTO-FIRE ENGAGED - TCS {signal['tcs_score']}%",
            'execution_delay': 0,  # Immediate
            'log_entry': self._create_auto_log(signal)
        }
    
    def handle_confirmation(self, confirmation_id: str, decision: str) -> Dict:
        """Handle user confirmation response"""
        
        if confirmation_id not in self.pending_confirmations:
            return {
                'success': False,
                'message': 'Confirmation expired or not found'
            }
        
        confirmation = self.pending_confirmations.pop(confirmation_id)
        
        # Check expiry
        if datetime.now() > confirmation['expires_at']:
            return {
                'success': False,
                'message': 'Confirmation timeout'
            }
        
        if decision == 'confirm':
            return {
                'success': True,
                'action': 'execute',
                'signal': confirmation['signal'],
                'message': 'SEMI-AUTO execution confirmed'
            }
        else:
            return {
                'success': True,
                'action': 'rejected',
                'message': 'Signal rejected by user'
            }
    
    def _validate_auto_requirements(self) -> bool:
        """Validate requirements for FULL AUTO mode"""
        
        # In production, would check:
        # - Account balance >= $1000
        # - Account age >= 30 days
        # - Win rate >= 50%
        # - Completed tutorial
        
        return True  # Simplified for now
    
    def _build_signal_analysis(self, signal: Dict) -> str:
        """Build detailed analysis for SEMI mode popup"""
        
        return f"""📊 **Signal Analysis**

Type: {signal['display_type']}
Confidence: {signal['tcs_score']}%
Expected: {signal['expected_pips']} pips
Duration: {signal['expected_duration']} min

Risk/Reward: {signal.get('risk_reward', '1:2')}
Session: {signal.get('session', 'Active')}

⚠️ Confirm within {self.semi_config.confirmation_timeout} seconds"""
    
    def _create_auto_log(self, signal: Dict) -> Dict:
        """Create log entry for auto execution"""
        
        return {
            'timestamp': datetime.now(),
            'mode': 'FULL_AUTO',
            'signal_type': signal['signal_type'],
            'symbol': signal['symbol'],
            'direction': signal['direction'],
            'tcs': signal['tcs_score'],
            'auto_execution_number': self.auto_executions_today
        }
    
    def get_mode_status(self) -> Dict:
        """Get current selector status"""
        
        uptime = datetime.now() - self.mode_changed_at
        
        status = {
            'current_mode': self.mode.value.upper(),
            'mode_uptime': str(uptime).split('.')[0],
            'pending_confirmations': len(self.pending_confirmations),
            'auto_executions_today': self.auto_executions_today
        }
        
        # Add mode-specific info
        if self.mode == SelectorMode.FULL:
            status.update({
                'auto_config': {
                    'min_tcs': self.auto_config.min_tcs,
                    'max_positions': self.auto_config.max_positions,
                    'arcade_enabled': self.auto_config.arcade_enabled,
                    'sniper_enabled': self.auto_config.sniper_enabled
                }
            })
        elif self.mode == SelectorMode.SEMI:
            status.update({
                'confirmation_timeout': self.semi_config.confirmation_timeout,
                'active_confirmations': list(self.pending_confirmations.keys())
            })
        
        return status
    
    def configure_auto_mode(self, **kwargs) -> bool:
        """Update AUTO mode configuration"""
        
        for key, value in kwargs.items():
            if hasattr(self.auto_config, key):
                setattr(self.auto_config, key, value)
                
        logger.info(f"AUTO config updated: {kwargs}")
        return True
    
    def emergency_stop(self) -> Dict:
        """Emergency switch to SAFE mode"""
        
        old_mode = self.mode
        self.mode = SelectorMode.SAFE
        self.pending_confirmations.clear()
        
        return {
            'success': True,
            'message': f"EMERGENCY STOP - Switched from {old_mode.value} to SAFE",
            'timestamp': datetime.now()
        }

class SelectorUI:
    """UI components for selector switch"""
    
    @staticmethod
    def format_mode_display(mode: SelectorMode, status: Dict) -> str:
        """Format selector display for Telegram"""
        
        if mode == SelectorMode.SAFE:
            icon = "🟢"
            desc = "Manual execution only"
        elif mode == SelectorMode.SEMI:
            icon = "🟡"
            desc = "Confirmation required"
        else:  # FULL
            icon = "🔴"
            desc = "24/7 Autonomous"
        
        return f"""🎚️ **SELECTOR SWITCH**
{icon} Mode: {mode.value.upper()}
📝 {desc}

⏱️ Uptime: {status['mode_uptime']}
🔫 Auto-fires today: {status.get('auto_executions_today', 0)}

[SAFE] [SEMI] [FULL]"""
    
    @staticmethod
    def format_confirmation_popup(popup_data: Dict) -> str:
        """Format confirmation popup for SEMI mode"""
        
        signal = popup_data['signal']
        
        return f"""⚡ **CONFIRMATION REQUIRED** ⚡

{popup_data['title']}

📍 {signal['symbol']} - {signal['direction'].upper()}
🎯 TCS: {signal['tcs_score']}%
💰 Expected: {signal['expected_pips']} pips

{popup_data.get('analysis', '')}

━━━━━━━━━━━━━━━━━━━━
🔫 [FIRE] ❌ [SKIP]
━━━━━━━━━━━━━━━━━━━━"""
    
    @staticmethod
    def format_auto_notification(action_result: Dict) -> str:
        """Format AUTO mode notification"""
        
        if action_result['action'] == 'auto_execute':
            return f"""🤖 **AUTO-FIRE EXECUTED**

{action_result['message']}
Time: {datetime.now().strftime('%H:%M:%S')}

Your COMMANDER is working 24/7! 🎖️"""
        
        else:  # auto_rejected
            return f"""🤖 **AUTO-FIRE SKIPPED**

Reason: {action_result['reason']}

Waiting for better opportunities..."""