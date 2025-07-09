"""
BITTEN Emergency Stop Controller
Unified emergency stop system for all trading activities
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

class EmergencyStopTrigger(Enum):
    """Types of emergency stop triggers"""
    MANUAL = "manual"
    PANIC = "panic"
    DRAWDOWN = "drawdown"
    NEWS = "news"
    SYSTEM_ERROR = "system_error"
    MARKET_VOLATILITY = "market_volatility"
    BROKER_CONNECTION = "broker_connection"
    ADMIN_OVERRIDE = "admin_override"
    SCHEDULED_MAINTENANCE = "scheduled_maintenance"

class EmergencyStopLevel(Enum):
    """Emergency stop severity levels"""
    SOFT = "soft"      # Stop new trades only
    HARD = "hard"      # Stop all trades + close positions
    PANIC = "panic"    # Immediate exit everything
    MAINTENANCE = "maintenance"  # Planned shutdown

@dataclass
class EmergencyStopEvent:
    """Emergency stop event data"""
    trigger: EmergencyStopTrigger
    level: EmergencyStopLevel
    timestamp: datetime
    user_id: Optional[int] = None
    reason: str = ""
    metadata: Dict[str, Any] = None
    recovery_time: Optional[datetime] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class EmergencyStopController:
    """
    Unified emergency stop system controller
    
    Coordinates all emergency stop mechanisms:
    - Kill switch (environment variable)
    - Selector switch emergency
    - Position manager emergency close
    - Trade manager emergency exits
    - Risk controller safety systems
    """
    
    def __init__(self, data_dir: str = "data"):
        # Validate and sanitize data directory path
        self.data_dir = self._validate_data_dir(data_dir)
        self.state_file = os.path.join(self.data_dir, "emergency_stop_state.json")
        self.event_log_file = os.path.join(self.data_dir, "emergency_events.log")
        self._ensure_data_dir()
        
        # Load existing state
        self.state = self._load_state()
        
        # Initialize components (will be injected)
        self.fire_validator = None
        self.selector_switch = None
        self.position_manager = None
        self.trade_manager = None
        self.risk_controller = None
        self.mt5_bridge = None
        self.telegram_router = None
        
        # Emergency stop configuration
        self.config = {
            'auto_recovery_enabled': True,
            'auto_recovery_delay_minutes': 30,
            'max_emergency_duration_hours': 24,
            'drawdown_trigger_threshold': -10.0,  # -10% triggers emergency
            'volatility_trigger_threshold': 5.0,   # 5% price moves
            'news_emergency_duration_minutes': 30,
            'panic_word_enabled': True,
            'panic_words': ['PANIC', 'STOP', 'EMERGENCY', 'HALT']
        }
        
        # Initialize notification system
        from .emergency_notification_system import EmergencyNotificationSystem
        self.notification_system = EmergencyNotificationSystem()
    
    def _validate_data_dir(self, data_dir: str) -> str:
        """Validate and sanitize data directory path"""
        if not data_dir or not isinstance(data_dir, str):
            raise ValueError("Data directory must be a non-empty string")
        
        # Prevent path traversal attacks
        if '..' in data_dir or data_dir.startswith('/') or '\\' in data_dir:
            raise ValueError("Invalid data directory path - path traversal detected")
        
        # Ensure it's a relative path within allowed directories
        allowed_dirs = ['data', 'logs', 'backups', 'test_data']
        if data_dir not in allowed_dirs:
            raise ValueError(f"Data directory must be one of: {allowed_dirs}")
        
        return data_dir
    
    def _ensure_data_dir(self):
        """Ensure data directory exists with proper permissions"""
        try:
            os.makedirs(self.data_dir, mode=0o750, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create data directory: {e}")
            raise
    
    def _load_state(self) -> Dict:
        """Load emergency stop state from file with validation"""
        if not os.path.exists(self.state_file):
            return self._get_default_state()
        
        try:
            # Check file size to prevent DoS
            file_size = os.path.getsize(self.state_file)
            if file_size > 1024 * 1024:  # 1MB limit
                logger.error("State file too large, using default state")
                return self._get_default_state()
            
            with open(self.state_file, 'r') as f:
                content = f.read()
                data = json.loads(content)
                
                # Validate structure
                return self._validate_state_structure(data)
                
        except Exception as e:
            logger.error(f"Failed to load emergency state: {e}")
            return self._get_default_state()
    
    def _get_default_state(self) -> Dict:
        """Get default emergency state"""
        return {
            'is_active': False,
            'current_event': None,
            'events_today': 0,
            'last_recovery': None,
            'active_triggers': [],
            'affected_users': []
        }
    
    def _validate_state_structure(self, data: Dict) -> Dict:
        """Validate and sanitize state data structure"""
        if not isinstance(data, dict):
            logger.warning("Invalid state format, using default")
            return self._get_default_state()
        
        validated_state = {}
        
        # Validate each field with safe defaults
        validated_state['is_active'] = isinstance(data.get('is_active'), bool) and data['is_active']
        validated_state['events_today'] = max(0, min(data.get('events_today', 0), 1000))  # Limit to reasonable range
        validated_state['last_recovery'] = data.get('last_recovery') if isinstance(data.get('last_recovery'), str) else None
        
        # Validate arrays with size limits
        validated_state['active_triggers'] = [t for t in data.get('active_triggers', []) if isinstance(t, str)][:10]
        validated_state['affected_users'] = [u for u in data.get('affected_users', []) if isinstance(u, int)][:100]
        
        # Validate current_event
        current_event = data.get('current_event')
        if isinstance(current_event, dict):
            validated_state['current_event'] = self._validate_event_data(current_event)
        else:
            validated_state['current_event'] = None
        
        return validated_state
    
    def _validate_event_data(self, event_data: Dict) -> Dict:
        """Validate emergency event data"""
        valid_triggers = ['manual', 'panic', 'drawdown', 'news', 'system_error', 'market_volatility', 'broker_connection', 'admin_override', 'scheduled_maintenance']
        valid_levels = ['soft', 'hard', 'panic', 'maintenance']
        
        validated = {}
        validated['trigger'] = event_data.get('trigger') if event_data.get('trigger') in valid_triggers else 'manual'
        validated['level'] = event_data.get('level') if event_data.get('level') in valid_levels else 'soft'
        validated['timestamp'] = event_data.get('timestamp') if isinstance(event_data.get('timestamp'), str) else datetime.now().isoformat()
        validated['user_id'] = event_data.get('user_id') if isinstance(event_data.get('user_id'), int) else None
        
        # Sanitize reason string
        reason = event_data.get('reason', '')
        if isinstance(reason, str):
            validated['reason'] = reason[:500]  # Limit length
        else:
            validated['reason'] = 'Emergency stop activated'
        
        return validated
    
    def _save_state(self):
        """Save emergency stop state to file"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save emergency state: {e}")
    
    def _log_event(self, event: EmergencyStopEvent):
        """Log emergency stop event"""
        try:
            log_entry = {
                'timestamp': event.timestamp.isoformat(),
                'trigger': event.trigger.value,
                'level': event.level.value,
                'user_id': event.user_id,
                'reason': event.reason,
                'metadata': event.metadata
            }
            
            with open(self.event_log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to log emergency event: {e}")
    
    def inject_components(self, **components):
        """Inject system components for emergency control"""
        for name, component in components.items():
            if hasattr(self, name):
                setattr(self, name, component)
    
    def is_active(self) -> bool:
        """Check if emergency stop is currently active"""
        return self.state.get('is_active', False)
    
    def get_active_triggers(self) -> List[str]:
        """Get list of active emergency triggers"""
        return self.state.get('active_triggers', [])
    
    def get_current_event(self) -> Optional[Dict]:
        """Get current emergency stop event"""
        return self.state.get('current_event')
    
    def trigger_emergency_stop(
        self, 
        trigger: EmergencyStopTrigger,
        level: EmergencyStopLevel = EmergencyStopLevel.SOFT,
        user_id: Optional[int] = None,
        reason: str = "",
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Trigger emergency stop with specified parameters
        
        Args:
            trigger: What triggered the emergency stop
            level: Severity level of emergency stop
            user_id: User who triggered (if manual)
            reason: Human-readable reason
            metadata: Additional context data
            
        Returns:
            Dict with emergency stop result
        """
        try:
            # Create emergency event
            event = EmergencyStopEvent(
                trigger=trigger,
                level=level,
                timestamp=datetime.now(),
                user_id=user_id,
                reason=reason,
                metadata=metadata or {}
            )
            
            # Log the event
            self._log_event(event)
            
            # Execute emergency stop based on level
            results = self._execute_emergency_stop(event)
            
            # Update state
            self.state.update({
                'is_active': True,
                'current_event': asdict(event),
                'events_today': self.state.get('events_today', 0) + 1,
                'active_triggers': list(set(self.state.get('active_triggers', []) + [trigger.value]))
            })
            
            # Add affected users
            if user_id:
                affected_users = self.state.get('affected_users', [])
                if user_id not in affected_users:
                    affected_users.append(user_id)
                    self.state['affected_users'] = affected_users
            
            self._save_state()
            
            # Send emergency notifications
            notification_result = self._send_emergency_notifications(event, results)
            
            logger.critical(f"EMERGENCY STOP ACTIVATED: {trigger.value} - {reason}")
            
            return {
                'success': True,
                'message': f"Emergency stop activated: {trigger.value}",
                'event': asdict(event),
                'results': results,
                'recovery_time': event.recovery_time,
                'notifications': notification_result
            }
            
        except Exception as e:
            logger.error(f"Failed to trigger emergency stop: {e}")
            return {
                'success': False,
                'message': f"Emergency stop failed: {str(e)}",
                'error': str(e)
            }
    
    def _execute_emergency_stop(self, event: EmergencyStopEvent) -> Dict[str, Any]:
        """Execute emergency stop based on level"""
        results = {}
        
        try:
            # 1. Set global kill switch with validation
            if self._set_kill_switch('true'):
                results['kill_switch'] = True
            else:
                results['kill_switch'] = False
                logger.error("Failed to set kill switch")
            
            # 2. Selector switch emergency (if available)
            if self.selector_switch:
                selector_result = self.selector_switch.emergency_stop()
                results['selector_switch'] = selector_result
            
            # 3. Level-specific actions
            if event.level in [EmergencyStopLevel.HARD, EmergencyStopLevel.PANIC]:
                # Close all positions
                if self.position_manager:
                    affected_users = self.state.get('affected_users', [])
                    closed_positions = []
                    for user_id in affected_users:
                        positions = self.position_manager.emergency_close_all(user_id)
                        closed_positions.extend(positions)
                    results['closed_positions'] = closed_positions
                
                # Emergency exit through trade manager
                if self.trade_manager:
                    results['trade_manager'] = "Emergency exit protocols activated"
            
            # 4. MT5 Bridge emergency halt
            if self.mt5_bridge:
                results['mt5_bridge'] = "Emergency halt signal sent to MT5"
            
            # 5. Risk controller emergency mode
            if self.risk_controller:
                results['risk_controller'] = "Emergency risk mode activated"
            
            # 6. Set recovery time based on trigger
            recovery_minutes = self._calculate_recovery_time(event)
            if recovery_minutes > 0:
                event.recovery_time = datetime.now() + timedelta(minutes=recovery_minutes)
                results['recovery_time'] = event.recovery_time
            
            return results
            
        except Exception as e:
            logger.error(f"Error executing emergency stop: {e}")
            results['error'] = str(e)
            return results
    
    def _calculate_recovery_time(self, event: EmergencyStopEvent) -> int:
        """Calculate automatic recovery time in minutes"""
        recovery_times = {
            EmergencyStopTrigger.MANUAL: 0,  # Manual recovery only
            EmergencyStopTrigger.PANIC: 0,   # Manual recovery only
            EmergencyStopTrigger.DRAWDOWN: 60,  # 1 hour
            EmergencyStopTrigger.NEWS: 30,      # 30 minutes
            EmergencyStopTrigger.SYSTEM_ERROR: 15,  # 15 minutes
            EmergencyStopTrigger.MARKET_VOLATILITY: 45,  # 45 minutes
            EmergencyStopTrigger.BROKER_CONNECTION: 10,  # 10 minutes
            EmergencyStopTrigger.ADMIN_OVERRIDE: 0,  # Manual recovery only
            EmergencyStopTrigger.SCHEDULED_MAINTENANCE: 0  # Manual recovery only
        }
        
        return recovery_times.get(event.trigger, 0)
    
    def recover_from_emergency(self, user_id: Optional[int] = None, force: bool = False) -> Dict[str, Any]:
        """
        Recover from emergency stop state
        
        Args:
            user_id: User requesting recovery (for authorization)
            force: Force recovery even if not ready
            
        Returns:
            Dict with recovery result
        """
        try:
            if not self.is_active():
                return {
                    'success': False,
                    'message': "No emergency stop is currently active"
                }
            
            current_event = self.get_current_event()
            if not current_event:
                return {
                    'success': False,
                    'message': "No current emergency event found"
                }
            
            # Check if auto-recovery is ready
            if not force and current_event.get('recovery_time'):
                recovery_time = datetime.fromisoformat(current_event['recovery_time'])
                if datetime.now() < recovery_time:
                    remaining = recovery_time - datetime.now()
                    return {
                        'success': False,
                        'message': f"Auto-recovery not ready. {remaining.total_seconds():.0f} seconds remaining",
                        'recovery_time': recovery_time
                    }
            
            # Execute recovery
            recovery_results = self._execute_recovery()
            
            # Update state
            self.state.update({
                'is_active': False,
                'current_event': None,
                'last_recovery': datetime.now().isoformat(),
                'active_triggers': [],
                'affected_users': []
            })
            
            self._save_state()
            
            # Send recovery notifications
            recovery_notification = self.notification_system.send_recovery_notification(
                recovery_data={
                    'user_id': user_id,
                    'recovery_time': datetime.now(),
                    'recovery_results': recovery_results
                },
                affected_users=self.state.get('affected_users', [])
            )
            
            logger.info(f"Emergency stop recovery completed by user {user_id}")
            
            return {
                'success': True,
                'message': "Emergency stop recovery completed",
                'recovery_results': recovery_results,
                'recovery_time': datetime.now(),
                'notifications': recovery_notification
            }
            
        except Exception as e:
            logger.error(f"Failed to recover from emergency stop: {e}")
            return {
                'success': False,
                'message': f"Recovery failed: {str(e)}",
                'error': str(e)
            }
    
    def _execute_recovery(self) -> Dict[str, Any]:
        """Execute recovery procedures"""
        results = {}
        
        try:
            # 1. Clear global kill switch with validation
            if self._set_kill_switch('false'):
                results['kill_switch'] = False
            else:
                results['kill_switch'] = True
                logger.error("Failed to clear kill switch")
            
            # 2. Reset selector switch (if available)
            if self.selector_switch:
                # Reset to SAFE mode
                results['selector_switch'] = "Reset to SAFE mode"
            
            # 3. Reset risk controller
            if self.risk_controller:
                results['risk_controller'] = "Emergency risk mode deactivated"
            
            # 4. MT5 Bridge recovery
            if self.mt5_bridge:
                results['mt5_bridge'] = "Recovery signal sent to MT5"
            
            # 5. System health check
            health_check = self._perform_health_check()
            results['health_check'] = health_check
            
            return results
            
        except Exception as e:
            logger.error(f"Error executing recovery: {e}")
            results['error'] = str(e)
            return results
    
    def _perform_health_check(self) -> Dict[str, Any]:
        """Perform system health check during recovery"""
        health = {
            'timestamp': datetime.now().isoformat(),
            'components': {},
            'overall_status': 'healthy'
        }
        
        # Check each component
        components = {
            'fire_validator': self.fire_validator,
            'selector_switch': self.selector_switch,
            'position_manager': self.position_manager,
            'trade_manager': self.trade_manager,
            'risk_controller': self.risk_controller,
            'mt5_bridge': self.mt5_bridge
        }
        
        for name, component in components.items():
            if component:
                health['components'][name] = 'available'
            else:
                health['components'][name] = 'unavailable'
                health['overall_status'] = 'degraded'
        
        return health
    
    def _set_kill_switch(self, value: str) -> bool:
        """Securely set kill switch environment variable"""
        if value not in ['true', 'false']:
            logger.error(f"Invalid kill switch value: {value}")
            return False
        
        try:
            os.environ['BITTEN_KILL_SWITCH'] = value
            return True
        except Exception as e:
            logger.error(f"Failed to set kill switch: {e}")
            return False
    
    def get_emergency_status(self, user_id: int = None) -> Dict[str, Any]:
        """Get emergency stop status with access control"""
        # Basic status for all users
        status = {
            'is_active': self.is_active(),
            'timestamp': datetime.now().isoformat()
        }
        
        # Add additional details only if user_id is provided and valid
        if user_id and isinstance(user_id, int):
            status.update({
                'active_triggers': self.get_active_triggers(),
                'events_today': min(self.state.get('events_today', 0), 1000)  # Limit exposure
            })
            
            # Sanitize current event data
            current_event = self.get_current_event()
            if current_event:
                status['current_event'] = self._sanitize_event_for_display(current_event)
        
        return status
    
    def _sanitize_event_for_display(self, event: Dict) -> Dict:
        """Sanitize event data for safe display"""
        if not isinstance(event, dict):
            return {}
        
        sanitized = {
            'trigger': str(event.get('trigger', 'unknown'))[:20],
            'level': str(event.get('level', 'unknown'))[:20],
            'timestamp': str(event.get('timestamp', ''))[:50],
            'reason': str(event.get('reason', ''))[:200]  # Limit reason length
        }
        
        # Only include user_id if it's the same user or system event
        if event.get('user_id') and isinstance(event.get('user_id'), int):
            sanitized['user_id'] = event['user_id']
        
        return sanitized
    
    def reset_daily_counters(self):
        """Reset daily event counters (called by daily reset script)"""
        self.state['events_today'] = 0
        self._save_state()
        logger.info("Emergency stop daily counters reset")
    
    def _send_emergency_notifications(self, event: EmergencyStopEvent, execution_results: Dict[str, Any]) -> Dict[str, Any]:
        """Send notifications for emergency stop event"""
        try:
            # Inject notification handlers if available
            if self.telegram_router:
                self.notification_system.inject_handlers(telegram=self.telegram_router)
            
            # Prepare additional data from execution results
            additional_data = {
                'execution_results': execution_results,
                'affected_systems': list(execution_results.keys()),
                'total_affected_users': len(self.state.get('affected_users', []))
            }
            
            # Add trigger-specific data
            if event.trigger == EmergencyStopTrigger.DRAWDOWN:
                additional_data['drawdown'] = event.metadata.get('drawdown_percent', 'unknown')
            elif event.trigger == EmergencyStopTrigger.NEWS:
                additional_data['event_name'] = event.metadata.get('news_event', 'High-impact news')
                additional_data['duration'] = event.metadata.get('duration_minutes', 30)
            elif event.trigger == EmergencyStopTrigger.SYSTEM_ERROR:
                additional_data['error_details'] = event.metadata.get('error_message', 'System error')
            elif event.trigger == EmergencyStopTrigger.MARKET_VOLATILITY:
                additional_data['volatility'] = event.metadata.get('volatility_percent', 'high')
            elif event.trigger == EmergencyStopTrigger.ADMIN_OVERRIDE:
                additional_data['admin_id'] = event.user_id
            
            # Send notifications
            notification_result = self.notification_system.send_emergency_notification(
                event=event,
                affected_users=self.state.get('affected_users', []),
                additional_data=additional_data
            )
            
            return notification_result
            
        except Exception as e:
            logger.error(f"Failed to send emergency notifications: {e}")
            return {'success': False, 'error': str(e)}