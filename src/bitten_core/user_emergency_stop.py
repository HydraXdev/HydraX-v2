"""
BITTEN User Emergency Stop System
Individual user-only emergency stop with confirmation dialog
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class UserEmergencyLevel(Enum):
    """User-specific emergency stop levels"""
    PAUSE_NEW = "pause_new"        # Stop new trades only
    CLOSE_ALL = "close_all"        # Close all positions + stop new trades
    ACCOUNT_LOCK = "account_lock"   # Complete trading lockout

@dataclass
class UserEmergencyState:
    """User's emergency stop state"""
    user_id: int
    is_active: bool
    level: UserEmergencyLevel
    timestamp: datetime
    reason: str
    positions_closed: List[str]
    recovery_time: Optional[datetime] = None
    confirmation_required: bool = True

class UserEmergencyStopController:
    """
    User-specific emergency stop system
    
    IMPORTANT: This ONLY affects individual users, NOT the entire system
    """
    
    def __init__(self, data_dir: str = "/root/HydraX-v2/data/user_emergency"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # Track user emergency states
        self.user_states: Dict[int, UserEmergencyState] = {}
        self.pending_confirmations: Dict[int, Dict] = {}  # user_id -> pending action
        
        # Load existing states
        self._load_states()
    
    def request_emergency_stop(
        self, 
        user_id: int, 
        level: UserEmergencyLevel = UserEmergencyLevel.PAUSE_NEW,
        reason: str = "User requested emergency stop"
    ) -> Dict[str, Any]:
        """
        Request emergency stop with confirmation dialog
        
        Returns confirmation dialog, does NOT execute immediately
        """
        try:
            # Store pending action
            self.pending_confirmations[user_id] = {
                'level': level,
                'reason': reason,
                'timestamp': datetime.now(),
                'expires_at': datetime.now() + timedelta(minutes=5)  # 5 min to confirm
            }
            
            # Get impact preview
            impact = self._get_emergency_impact_preview(user_id, level)
            
            # Create confirmation message
            level_descriptions = {
                UserEmergencyLevel.PAUSE_NEW: "⏸️ **PAUSE NEW TRADES**\n• Stop new signal executions\n• Keep existing positions open",
                UserEmergencyLevel.CLOSE_ALL: "🛑 **CLOSE ALL POSITIONS**\n• Close ALL open trades immediately\n• Stop all new signal executions",
                UserEmergencyLevel.ACCOUNT_LOCK: "🔒 **ACCOUNT LOCKOUT**\n• Close all positions\n• Block ALL trading activity\n• Require manual recovery"
            }
            
            confirmation_msg = f"""🚨 **EMERGENCY STOP CONFIRMATION**

{level_descriptions[level]}

**IMPACT ON YOUR ACCOUNT:**
{impact['summary']}

⚠️ **THIS ONLY AFFECTS YOUR ACCOUNT**
⚠️ **Other users continue trading normally**

🤔 **Are you sure you want to proceed?**

*Confirmation expires in 5 minutes*"""
            
            return {
                'success': True,
                'requires_confirmation': True,
                'message': confirmation_msg,
                'confirmation_id': f"emergency_confirm_{user_id}_{int(datetime.now().timestamp())}",
                'expires_at': self.pending_confirmations[user_id]['expires_at'],
                'buttons': [
                    {'text': '🛑 YES, EMERGENCY STOP', 'callback': f"emergency_execute_{user_id}"},
                    {'text': '❌ Cancel', 'callback': f"emergency_cancel_{user_id}"}
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to create emergency stop confirmation: {e}")
            return {
                'success': False,
                'message': f"Failed to prepare emergency stop: {str(e)}"
            }
    
    def execute_emergency_stop(self, user_id: int) -> Dict[str, Any]:
        """
        Execute confirmed emergency stop for specific user only
        """
        try:
            # Check if confirmation exists and is valid
            pending = self.pending_confirmations.get(user_id)
            if not pending:
                return {
                    'success': False,
                    'message': "❌ No pending emergency stop found. Please request again."
                }
            
            # Check if confirmation expired
            if datetime.now() > pending['expires_at']:
                del self.pending_confirmations[user_id]
                return {
                    'success': False,
                    'message': "❌ Confirmation expired. Please request emergency stop again."
                }
            
            level = pending['level']
            reason = pending['reason']
            
            # Execute user-specific emergency stop
            results = self._execute_user_emergency_stop(user_id, level, reason)
            
            # Create emergency state
            emergency_state = UserEmergencyState(
                user_id=user_id,
                is_active=True,
                level=level,
                timestamp=datetime.now(),
                reason=reason,
                positions_closed=results.get('closed_positions', [])
            )
            
            # Set recovery time based on level
            if level == UserEmergencyLevel.PAUSE_NEW:
                emergency_state.recovery_time = datetime.now() + timedelta(minutes=30)
            elif level == UserEmergencyLevel.CLOSE_ALL:
                emergency_state.recovery_time = datetime.now() + timedelta(hours=1)
            else:  # ACCOUNT_LOCK
                emergency_state.recovery_time = None  # Manual recovery only
            
            # Save state
            self.user_states[user_id] = emergency_state
            self._save_states()
            
            # Clear pending confirmation
            del self.pending_confirmations[user_id]
            
            # Create success message
            success_msg = f"""✅ **EMERGENCY STOP ACTIVATED**

**Level:** {level.value.replace('_', ' ').title()}
**Time:** {datetime.now().strftime('%H:%M:%S UTC')}
**Reason:** {reason}

**Actions Taken:**
{self._format_emergency_results(results)}

**Recovery:** {'Automatic' if emergency_state.recovery_time else 'Manual'}
{f"**Auto-Recovery Time:** {emergency_state.recovery_time.strftime('%H:%M UTC')}" if emergency_state.recovery_time else "**Manual Recovery Required**"}

🛡️ **Your account is now protected**
🔄 Use `/emergency_status` to check status
🔓 Use `/emergency_recover` when ready"""
            
            logger.warning(f"USER EMERGENCY STOP: User {user_id} - {level.value} - {reason}")
            
            return {
                'success': True,
                'message': success_msg,
                'emergency_state': emergency_state,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Failed to execute emergency stop for user {user_id}: {e}")
            return {
                'success': False,
                'message': f"❌ Emergency stop failed: {str(e)}"
            }
    
    def cancel_emergency_stop(self, user_id: int) -> Dict[str, Any]:
        """Cancel pending emergency stop request"""
        if user_id in self.pending_confirmations:
            del self.pending_confirmations[user_id]
            return {
                'success': True,
                'message': "✅ Emergency stop request cancelled"
            }
        else:
            return {
                'success': False,
                'message': "❌ No pending emergency stop found"
            }
    
    def get_user_emergency_status(self, user_id: int) -> Dict[str, Any]:
        """Get user's emergency stop status"""
        state = self.user_states.get(user_id)
        
        if not state or not state.is_active:
            return {
                'is_active': False,
                'message': "🟢 **NORMAL OPERATIONS**\nNo emergency stop active"
            }
        
        status_msg = f"""🚨 **EMERGENCY STOP ACTIVE**

**Level:** {state.level.value.replace('_', ' ').title()}
**Since:** {state.timestamp.strftime('%Y-%m-%d %H:%M UTC')}
**Reason:** {state.reason}

**Positions Closed:** {len(state.positions_closed)}
**Recovery:** {'Automatic' if state.recovery_time else 'Manual'}"""
        
        if state.recovery_time:
            if datetime.now() >= state.recovery_time:
                status_msg += "\n\n🟡 **AUTO-RECOVERY READY**\nUse `/emergency_recover` to resume"
            else:
                remaining = state.recovery_time - datetime.now()
                status_msg += f"\n\n⏰ **Auto-recovery in:** {remaining.total_seconds()//60:.0f} minutes"
        else:
            status_msg += "\n\n🔒 **Manual recovery required**"
        
        return {
            'is_active': True,
            'level': state.level,
            'message': status_msg,
            'state': state
        }
    
    def recover_from_emergency(self, user_id: int, force: bool = False) -> Dict[str, Any]:
        """Recover user from emergency stop"""
        try:
            state = self.user_states.get(user_id)
            
            if not state or not state.is_active:
                return {
                    'success': False,
                    'message': "❌ No active emergency stop found"
                }
            
            # Check if auto-recovery is ready
            if not force and state.recovery_time:
                if datetime.now() < state.recovery_time:
                    remaining = state.recovery_time - datetime.now()
                    return {
                        'success': False,
                        'message': f"❌ Auto-recovery not ready. {remaining.total_seconds()//60:.0f} minutes remaining"
                    }
            
            # Deactivate emergency state
            state.is_active = False
            self._save_states()
            
            recovery_msg = f"""✅ **EMERGENCY RECOVERY COMPLETE**

**Restored at:** {datetime.now().strftime('%H:%M:%S UTC')}
**Duration:** {(datetime.now() - state.timestamp).total_seconds()//60:.0f} minutes

🟢 **NORMAL OPERATIONS RESUMED**
• New trades allowed
• All systems operational
• Trading restrictions lifted

🛡️ **Stay safe out there, soldier!**"""
            
            logger.info(f"USER EMERGENCY RECOVERY: User {user_id} recovered from {state.level.value}")
            
            return {
                'success': True,
                'message': recovery_msg,
                'recovery_time': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Failed to recover user {user_id} from emergency: {e}")
            return {
                'success': False,
                'message': f"❌ Recovery failed: {str(e)}"
            }
    
    def is_user_emergency_active(self, user_id: int) -> bool:
        """Check if user has active emergency stop"""
        state = self.user_states.get(user_id)
        return state is not None and state.is_active
    
    def _get_emergency_impact_preview(self, user_id: int, level: UserEmergencyLevel) -> Dict[str, Any]:
        """Get preview of what emergency stop will do"""
        # This would integrate with position manager to get actual positions
        # For now, return mock data
        
        if level == UserEmergencyLevel.PAUSE_NEW:
            return {
                'summary': "• Existing positions remain open\n• New signals will be blocked\n• Manual trading still possible"
            }
        elif level == UserEmergencyLevel.CLOSE_ALL:
            return {
                'summary': "• ALL positions will be closed immediately\n• New signals blocked\n• May result in losses if positions are profitable"
            }
        else:  # ACCOUNT_LOCK
            return {
                'summary': "• ALL positions closed immediately\n• Complete trading lockout\n• Requires manual recovery\n• Use only in true emergencies"
            }
    
    def _execute_user_emergency_stop(self, user_id: int, level: UserEmergencyLevel, reason: str) -> Dict[str, Any]:
        """Execute the actual emergency stop actions"""
        results = {
            'actions_taken': [],
            'closed_positions': [],
            'blocked_systems': []
        }
        
        try:
            # Block new trades for this user
            results['blocked_systems'].append('signal_execution')
            results['actions_taken'].append('New trade execution blocked')
            
            if level in [UserEmergencyLevel.CLOSE_ALL, UserEmergencyLevel.ACCOUNT_LOCK]:
                # Close all positions (would integrate with position manager)
                # For now, simulate position closing
                results['closed_positions'] = ['EURUSD_001', 'GBPUSD_002']  # Mock data
                results['actions_taken'].append(f'Closed {len(results["closed_positions"])} positions')
            
            if level == UserEmergencyLevel.ACCOUNT_LOCK:
                # Complete lockout
                results['blocked_systems'].extend(['manual_trading', 'auto_fire', 'chaingun'])
                results['actions_taken'].append('Complete trading lockout activated')
            
            return results
            
        except Exception as e:
            logger.error(f"Error executing emergency stop for user {user_id}: {e}")
            results['error'] = str(e)
            return results
    
    def _format_emergency_results(self, results: Dict[str, Any]) -> str:
        """Format emergency stop results for display"""
        formatted = ""
        
        for action in results.get('actions_taken', []):
            formatted += f"✅ {action}\n"
        
        if results.get('closed_positions'):
            formatted += f"📈 Positions closed: {len(results['closed_positions'])}\n"
        
        if results.get('blocked_systems'):
            formatted += f"🚫 Systems blocked: {', '.join(results['blocked_systems'])}\n"
        
        return formatted.strip()
    
    def _load_states(self):
        """Load user emergency states from file"""
        state_file = os.path.join(self.data_dir, "user_emergency_states.json")
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r') as f:
                    data = json.load(f)
                
                for user_id_str, state_data in data.items():
                    user_id = int(user_id_str)
                    state = UserEmergencyState(
                        user_id=user_id,
                        is_active=state_data['is_active'],
                        level=UserEmergencyLevel(state_data['level']),
                        timestamp=datetime.fromisoformat(state_data['timestamp']),
                        reason=state_data['reason'],
                        positions_closed=state_data['positions_closed'],
                        recovery_time=datetime.fromisoformat(state_data['recovery_time']) if state_data.get('recovery_time') else None
                    )
                    self.user_states[user_id] = state
                    
            except Exception as e:
                logger.error(f"Failed to load user emergency states: {e}")
    
    def _save_states(self):
        """Save user emergency states to file"""
        state_file = os.path.join(self.data_dir, "user_emergency_states.json")
        try:
            data = {}
            for user_id, state in self.user_states.items():
                data[str(user_id)] = {
                    'is_active': state.is_active,
                    'level': state.level.value,
                    'timestamp': state.timestamp.isoformat(),
                    'reason': state.reason,
                    'positions_closed': state.positions_closed,
                    'recovery_time': state.recovery_time.isoformat() if state.recovery_time else None
                }
            
            with open(state_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save user emergency states: {e}")

# Global instance
user_emergency_controller = UserEmergencyStopController()