"""
BITTEN Tactical Mission Integration
Seamlessly integrates the tactical mission framework with existing BITTEN signal and trading systems
Converts live trading signals into compelling military operations while maintaining all functionality
"""

import json
import time
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

# Import existing BITTEN systems
try:
    from .tactical_mission_framework import (
        TacticalMissionFramework, OperationType, MissionPhase, 
        OperationalStatus, create_first_live_trade_mission
    )
    from .mission_progression_system import (
        MissionProgressionSystem, mission_progression_system,
        get_available_missions_for_user, process_mission_completion
    )
    from .norman_story_integration import norman_story_engine
    from .signal_fusion import SignalFusionEngine
    from .telegram_router import TelegramRouter
    from .web_app import WebAppRouter
    from .fire_router import FireRouter
    from .trade_manager import TradeManager
except ImportError:
    # Fallback for testing
    class SignalFusionEngine:
        def create_signal(self, data): return data
    class TelegramRouter:
        def send_mission_alert(self, data): pass
    class WebAppRouter:
        def broadcast_mission_update(self, data): pass
    class FireRouter:
        def execute_mission_trade(self, data): return {'success': True}
    class TradeManager:
        def monitor_mission_trade(self, data): return {'status': 'active'}

@dataclass
class MissionSignalMapping:
    """Maps signal data to mission parameters"""
    signal_id: str
    mission_id: str
    operation_type: OperationType
    user_id: str
    callsign: str
    
    # Signal data preservation
    original_signal: Dict
    mission_overlay: Dict
    
    # Integration tracking
    created_at: int
    expires_at: int
    status: str
    participants: List[str]

class TacticalMissionIntegrator:
    """Main integration class that bridges missions with existing BITTEN systems"""
    
    def __init__(self):
        self.mission_framework = TacticalMissionFramework()
        self.progression_system = mission_progression_system
        
        # Initialize existing BITTEN components
        self.signal_fusion = SignalFusionEngine()
        self.telegram_router = TelegramRouter()
        self.webapp_router = WebAppRouter()
        self.fire_router = FireRouter()
        self.trade_manager = TradeManager()
        
        # Mission tracking
        self.active_missions: Dict[str, MissionSignalMapping] = {}
        self.signal_to_mission: Dict[str, str] = {}
        
        # Event handlers
        self.mission_handlers: Dict[str, List[Callable]] = {
            'mission_created': [],
            'mission_started': [],
            'mission_completed': [],
            'mission_failed': [],
            'signal_converted': []
        }
        
        self.logger = logging.getLogger(__name__)
    
    def convert_signal_to_mission(self, signal_data: Dict, user_id: str, user_tier: str = "RECRUIT") -> Dict:
        """Convert a BITTEN trading signal into a tactical mission"""
        
        try:
            # Determine mission type based on signal characteristics
            operation_type = self._determine_operation_type(signal_data)
            
            # Check if user has access to this operation type
            if not self._user_has_access(user_id, operation_type):
                return {
                    'error': 'insufficient_clearance',
                    'message': f'Operator clearance required for {operation_type.value} operations',
                    'required_rank': self._get_required_rank(operation_type),
                    'alternative_missions': self._get_alternative_missions(user_id)
                }
            
            # Create the tactical mission
            mission = create_first_live_trade_mission(user_id, signal_data, user_tier)
            
            # Create mission-signal mapping
            mapping = MissionSignalMapping(
                signal_id=signal_data.get('signal_id', f"SIG_{int(time.time())}"),
                mission_id=mission.mission_id,
                operation_type=operation_type,
                user_id=user_id,
                callsign=mission.operator_callsign,
                original_signal=signal_data.copy(),
                mission_overlay=self._create_mission_overlay(signal_data, mission),
                created_at=int(time.time()),
                expires_at=signal_data.get('expires_at', int(time.time()) + 1800),
                status='briefing',
                participants=[user_id]
            )
            
            # Store mappings
            self.active_missions[mission.mission_id] = mapping
            self.signal_to_mission[mapping.signal_id] = mission.mission_id
            
            # Generate mission briefing using existing framework
            briefing = self.mission_framework.generate_pre_mission_briefing(mission)
            
            # Trigger mission creation events
            self._trigger_event('mission_created', {
                'mission': mission,
                'mapping': mapping,
                'briefing': briefing
            })
            
            # Send tactical alert via existing Telegram system
            self._send_tactical_alert(mission, signal_data, user_id)
            
            # Update webapp with mission briefing
            self._update_webapp_mission(mission, briefing)
            
            return {
                'success': True,
                'mission': {
                    'mission_id': mission.mission_id,
                    'operation_type': operation_type.value,
                    'callsign': mission.operator_callsign,
                    'briefing': briefing,
                    'webapp_url': f'/mission/briefing/{mission.mission_id}',
                    'telegram_alert_sent': True
                },
                'signal_preserved': True,
                'original_signal_id': mapping.signal_id
            }
            
        except Exception as e:
            self.logger.error(f"Error converting signal to mission: {str(e)}")
            return {
                'error': 'conversion_failed',
                'message': str(e),
                'fallback_signal': signal_data  # Preserve original signal as fallback
            }
    
    def execute_mission_trade(self, mission_id: str, user_id: str, execution_params: Dict = None) -> Dict:
        """Execute the actual trade for a mission using existing BITTEN trading systems"""
        
        mapping = self.active_missions.get(mission_id)
        if not mapping:
            return {'error': 'mission_not_found'}
        
        if mapping.user_id != user_id:
            return {'error': 'unauthorized_operator'}
        
        try:
            # Prepare trading parameters from original signal
            signal_data = mapping.original_signal
            
            # Add mission context to trade execution
            enhanced_trade_params = {
                **signal_data,
                'mission_id': mission_id,
                'operator_callsign': mapping.callsign,
                'operation_type': mapping.operation_type.value,
                'tactical_context': True,
                **(execution_params or {})
            }
            
            # Execute trade through existing BITTEN fire router
            trade_result = self.fire_router.execute_mission_trade(enhanced_trade_params)
            
            if trade_result.get('success'):
                # Update mission status
                mapping.status = 'executing'
                
                # Start mission monitoring
                self._start_mission_monitoring(mission_id, trade_result)
                
                # Update progression tracking
                self._track_mission_execution(mapping, trade_result)
                
                # Send execution confirmation
                self._send_execution_confirmation(mapping, trade_result)
                
                # Trigger mission started events
                self._trigger_event('mission_started', {
                    'mission_id': mission_id,
                    'trade_result': trade_result,
                    'operator': mapping.callsign
                })
                
                return {
                    'success': True,
                    'mission_status': 'active',
                    'trade_id': trade_result.get('trade_id'),
                    'execution_price': trade_result.get('execution_price'),
                    'position_size': trade_result.get('position_size'),
                    'monitoring_active': True,
                    'mission_guidance_url': f'/mission/execute/{mission_id}'
                }
            else:
                # Execution failed
                mapping.status = 'failed'
                self._handle_mission_failure(mapping, trade_result)
                
                return {
                    'success': False,
                    'error': trade_result.get('error', 'execution_failed'),
                    'message': 'Mission execution failed - returning to briefing',
                    'retry_available': True
                }
                
        except Exception as e:
            self.logger.error(f"Error executing mission trade: {str(e)}")
            mapping.status = 'error'
            return {
                'success': False,
                'error': 'execution_error',
                'message': str(e)
            }
    
    def monitor_mission_progress(self, mission_id: str) -> Dict:
        """Monitor ongoing mission progress using existing trade monitoring"""
        
        mapping = self.active_missions.get(mission_id)
        if not mapping:
            return {'error': 'mission_not_found'}
        
        # Get trade status from existing trade manager
        trade_status = self.trade_manager.monitor_mission_trade({
            'mission_id': mission_id,
            'signal_id': mapping.signal_id,
            'user_id': mapping.user_id
        })
        
        # Convert trade status to mission status
        mission_status = self._convert_trade_status_to_mission(trade_status)
        
        # Generate mission guidance based on current status
        if mission_status.get('status') == 'active':
            guidance = self.mission_framework.generate_during_mission_guidance(
                self.mission_framework.get_active_operation(mission_id),
                MissionPhase.MONITORING
            )
            mission_status['guidance'] = guidance
        
        # Update webapp with real-time status
        self._update_webapp_status(mission_id, mission_status)
        
        return mission_status
    
    def complete_mission(self, mission_id: str, completion_data: Dict) -> Dict:
        """Complete a mission and extract learning outcomes"""
        
        mapping = self.active_missions.get(mission_id)
        if not mapping:
            return {'error': 'mission_not_found'}
        
        try:
            # Get final trade results
            final_trade_data = completion_data.get('trade_results', {})
            
            # Convert trade results to mission performance metrics
            mission_results = self._convert_trade_to_mission_results(final_trade_data, mapping)
            
            # Generate mission debrief using framework
            debrief = self.mission_framework.complete_operation(mission_id, mission_results)
            
            # Process progression updates
            progression_update = process_mission_completion(
                mapping.user_id, 
                'normandy_echo',  # For now, all first missions are Normandy Echo
                mission_results
            )
            
            # Update mission status
            mapping.status = 'completed'
            
            # Send completion notifications
            self._send_completion_notifications(mapping, debrief, progression_update)
            
            # Archive mission
            self._archive_mission(mapping)
            
            # Trigger completion events
            self._trigger_event('mission_completed', {
                'mission_id': mission_id,
                'debrief': debrief,
                'progression': progression_update,
                'operator': mapping.callsign
            })
            
            return {
                'success': True,
                'mission_status': 'completed',
                'debrief': debrief,
                'progression_update': progression_update,
                'debrief_url': f'/mission/debrief/{mission_id}',
                'next_available_missions': progression_update.get('next_available_missions', [])
            }
            
        except Exception as e:
            self.logger.error(f"Error completing mission: {str(e)}")
            return {
                'success': False,
                'error': 'completion_error',
                'message': str(e)
            }
    
    def _determine_operation_type(self, signal_data: Dict) -> OperationType:
        """Determine mission operation type based on signal characteristics"""
        
        signal_type = signal_data.get('type', 'standard').lower()
        tcs_score = signal_data.get('tcs_score', 75)
        duration = signal_data.get('expected_duration', 30)
        
        # Map signal types to operation types
        if signal_type in ['sniper', 'precision']:
            return OperationType.PRECISION_STRIKE
        elif signal_type in ['scalp', 'quick']:
            return OperationType.INFILTRATION
        elif signal_type in ['swing', 'position']:
            return OperationType.EXTRACTION
        elif tcs_score >= 90 and duration > 60:
            return OperationType.JOINT_OPERATION
        elif signal_type in ['support', 'hedge']:
            return OperationType.SUPPORT_MISSION
        else:
            return OperationType.RECONNAISSANCE  # Default for new traders
    
    def _user_has_access(self, user_id: str, operation_type: OperationType) -> bool:
        """Check if user has access to this operation type"""
        profile = self.progression_system.get_operator_profile(user_id)
        return operation_type in profile.unlocked_mission_types
    
    def _get_required_rank(self, operation_type: OperationType) -> str:
        """Get required rank for operation type"""
        rank_requirements = {
            OperationType.RECONNAISSANCE: "RECRUIT",
            OperationType.INFILTRATION: "PRIVATE",
            OperationType.PRECISION_STRIKE: "CORPORAL",
            OperationType.EXTRACTION: "SERGEANT",
            OperationType.SUPPORT_MISSION: "LIEUTENANT",
            OperationType.JOINT_OPERATION: "CAPTAIN"
        }
        return rank_requirements.get(operation_type, "RECRUIT")
    
    def _get_alternative_missions(self, user_id: str) -> List[str]:
        """Get alternative missions available to user"""
        available_missions = get_available_missions_for_user(user_id)
        return [m['mission_id'] for m in available_missions[:3]]  # Return top 3
    
    def _create_mission_overlay(self, signal_data: Dict, mission) -> Dict:
        """Create mission overlay that enhances signal with tactical elements"""
        return {
            'military_terminology': {
                'entry_price': 'deployment_coordinates',
                'stop_loss': 'extraction_point',
                'take_profit': 'objective_coordinates',
                'position_size': 'force_deployment',
                'symbol': 'target_zone'
            },
            'tactical_enhancements': {
                'threat_level': self._calculate_threat_level(signal_data),
                'mission_complexity': self._calculate_complexity(signal_data),
                'support_available': self._get_mission_support(signal_data),
                'intel_confidence': signal_data.get('tcs_score', 75)
            },
            'narrative_elements': {
                'operation_name': mission.mission_id,
                'callsign': mission.operator_callsign,
                'mission_type': mission.operation_type.value,
                'background_story': mission.background_story
            }
        }
    
    def _calculate_threat_level(self, signal_data: Dict) -> str:
        """Calculate mission threat level based on signal risk"""
        risk_pips = signal_data.get('risk_pips', 20)
        volatility = signal_data.get('volatility', 'NORMAL')
        
        if risk_pips <= 10 and volatility == 'LOW':
            return "MINIMAL"
        elif risk_pips <= 20 and volatility in ['LOW', 'NORMAL']:
            return "MODERATE"
        elif risk_pips <= 30:
            return "ELEVATED"
        else:
            return "HIGH"
    
    def _calculate_complexity(self, signal_data: Dict) -> int:
        """Calculate mission complexity (1-10 scale)"""
        base_complexity = 3
        
        # Adjust based on signal characteristics
        if signal_data.get('type') == 'sniper':
            base_complexity += 2
        if signal_data.get('correlation_risk'):
            base_complexity += 1
        if signal_data.get('news_pending'):
            base_complexity += 2
        if signal_data.get('tcs_score', 75) >= 90:
            base_complexity += 1
        
        return min(10, base_complexity)
    
    def _get_mission_support(self, signal_data: Dict) -> List[str]:
        """Get available mission support based on signal data"""
        support = [
            "Real-time intel updates",
            "Risk monitoring systems",
            "Emergency extraction protocols"
        ]
        
        if signal_data.get('tcs_score', 75) >= 80:
            support.append("Enhanced tactical guidance")
        
        if signal_data.get('type') == 'sniper':
            support.append("Precision targeting systems")
        
        return support
    
    def _send_tactical_alert(self, mission, signal_data: Dict, user_id: str) -> None:
        """Send tactical mission alert through existing Telegram system"""
        
        # Create tactical alert message
        alert_data = {
            'type': 'mission_alert',
            'mission_id': mission.mission_id,
            'operation_type': mission.operation_type.value,
            'callsign': mission.operator_callsign,
            'target_symbol': mission.target_symbol,
            'intel_confidence': mission.intel_confidence,
            'time_sensitive': mission.time_sensitive,
            'estimated_duration': mission.estimated_duration,
            'threat_level': self._calculate_threat_level(signal_data),
            'user_id': user_id,
            'original_signal': signal_data
        }
        
        # Send through existing Telegram router with tactical formatting
        self.telegram_router.send_mission_alert(alert_data)
    
    def _update_webapp_mission(self, mission, briefing: Dict) -> None:
        """Update webapp with mission briefing"""
        
        webapp_data = {
            'type': 'mission_briefing',
            'mission_id': mission.mission_id,
            'briefing': briefing,
            'url': f'/mission/briefing/{mission.mission_id}',
            'action_required': True
        }
        
        self.webapp_router.broadcast_mission_update(webapp_data)
    
    def _start_mission_monitoring(self, mission_id: str, trade_result: Dict) -> None:
        """Start monitoring mission progress"""
        
        # Initialize monitoring through existing trade manager
        monitoring_config = {
            'mission_id': mission_id,
            'trade_id': trade_result.get('trade_id'),
            'update_frequency': 5,  # seconds
            'tactical_mode': True
        }
        
        # Start monitoring task
        asyncio.create_task(self._mission_monitoring_loop(mission_id, monitoring_config))
    
    async def _mission_monitoring_loop(self, mission_id: str, config: Dict) -> None:
        """Async loop for mission monitoring"""
        
        while True:
            try:
                # Check if mission is still active
                mapping = self.active_missions.get(mission_id)
                if not mapping or mapping.status not in ['executing', 'monitoring']:
                    break
                
                # Get mission status update
                status_update = self.monitor_mission_progress(mission_id)
                
                # Check for completion conditions
                if status_update.get('trade_completed'):
                    await self._handle_mission_completion(mission_id, status_update)
                    break
                
                # Wait before next update
                await asyncio.sleep(config.get('update_frequency', 5))
                
            except Exception as e:
                self.logger.error(f"Error in mission monitoring loop: {str(e)}")
                await asyncio.sleep(10)  # Wait longer on error
    
    async def _handle_mission_completion(self, mission_id: str, final_status: Dict) -> None:
        """Handle automatic mission completion"""
        
        completion_data = {
            'trade_results': final_status.get('trade_results', {}),
            'automatic_completion': True,
            'completion_reason': final_status.get('completion_reason', 'target_reached')
        }
        
        self.complete_mission(mission_id, completion_data)
    
    def _track_mission_execution(self, mapping: MissionSignalMapping, trade_result: Dict) -> None:
        """Track mission execution for progression system"""
        
        # Update progression system with mission start
        profile = self.progression_system.get_operator_profile(mapping.user_id)
        profile.last_active = int(time.time())
        
        # Log mission execution event
        self.logger.info(f"Mission {mapping.mission_id} executed by {mapping.callsign}")
    
    def _send_execution_confirmation(self, mapping: MissionSignalMapping, trade_result: Dict) -> None:
        """Send mission execution confirmation"""
        
        confirmation_data = {
            'type': 'mission_execution',
            'mission_id': mapping.mission_id,
            'callsign': mapping.callsign,
            'execution_price': trade_result.get('execution_price'),
            'position_size': trade_result.get('position_size'),
            'status': 'MISSION ACTIVE - Position established',
            'monitoring_url': f'/mission/execute/{mapping.mission_id}'
        }
        
        self.telegram_router.send_mission_alert(confirmation_data)
    
    def _convert_trade_status_to_mission(self, trade_status: Dict) -> Dict:
        """Convert trade monitoring data to mission status"""
        
        return {
            'status': 'active' if trade_status.get('position_open') else 'completed',
            'current_pnl': trade_status.get('unrealized_pnl', 0),
            'current_price': trade_status.get('current_price'),
            'time_in_position': trade_status.get('duration_minutes', 0),
            'distance_to_target': trade_status.get('distance_to_tp'),
            'distance_to_stop': trade_status.get('distance_to_sl'),
            'mission_health': self._calculate_mission_health(trade_status),
            'tactical_status': self._get_tactical_status(trade_status)
        }
    
    def _calculate_mission_health(self, trade_status: Dict) -> str:
        """Calculate overall mission health"""
        pnl = trade_status.get('unrealized_pnl', 0)
        
        if pnl > 0:
            return "POSITIVE"
        elif pnl > -10:  # Small drawdown
            return "STABLE"
        elif pnl > -25:  # Moderate drawdown
            return "CAUTION"
        else:
            return "CRITICAL"
    
    def _get_tactical_status(self, trade_status: Dict) -> str:
        """Get tactical mission status description"""
        
        if trade_status.get('near_take_profit'):
            return "APPROACHING OBJECTIVE - Prepare for extraction"
        elif trade_status.get('near_stop_loss'):
            return "APPROACHING EXTRACTION POINT - Mission may abort"
        elif trade_status.get('unrealized_pnl', 0) > 0:
            return "MISSION PROGRESSING - Maintain position"
        else:
            return "HOLDING POSITION - Monitor for developments"
    
    def _update_webapp_status(self, mission_id: str, status: Dict) -> None:
        """Update webapp with real-time mission status"""
        
        webapp_update = {
            'type': 'mission_status_update',
            'mission_id': mission_id,
            'status': status,
            'timestamp': int(time.time())
        }
        
        self.webapp_router.broadcast_mission_update(webapp_update)
    
    def _convert_trade_to_mission_results(self, trade_data: Dict, mapping: MissionSignalMapping) -> Dict:
        """Convert final trade results to mission performance metrics"""
        
        return {
            'success': trade_data.get('profit', 0) > 0,
            'profit_loss': trade_data.get('profit', 0),
            'duration_minutes': trade_data.get('duration_minutes', 0),
            'risk_management_followed': trade_data.get('stop_loss_hit', False) or trade_data.get('target_hit', False),
            'execution_quality': trade_data.get('execution_quality', 0.8),
            'emotional_deviations': trade_data.get('manual_interventions', 0),
            'analysis_accuracy': trade_data.get('signal_accuracy', 0.7),
            'mission_complexity': mapping.mission_overlay.get('tactical_enhancements', {}).get('mission_complexity', 5),
            'threat_level': mapping.mission_overlay.get('tactical_enhancements', {}).get('threat_level', 'MODERATE')
        }
    
    def _send_completion_notifications(self, mapping: MissionSignalMapping, debrief: Dict, progression: Dict) -> None:
        """Send mission completion notifications"""
        
        # Telegram notification
        completion_alert = {
            'type': 'mission_complete',
            'mission_id': mapping.mission_id,
            'callsign': mapping.callsign,
            'status': debrief.get('mission_summary', {}).get('mission_status', 'COMPLETED'),
            'grade': debrief.get('performance_assessment', {}).get('overall_grade', 'B'),
            'experience_gained': progression.get('experience_gained', 0),
            'debrief_url': f'/mission/debrief/{mapping.mission_id}'
        }
        
        self.telegram_router.send_mission_alert(completion_alert)
        
        # Webapp notification
        webapp_completion = {
            'type': 'mission_completed',
            'mission_id': mapping.mission_id,
            'debrief': debrief,
            'progression': progression,
            'action_required': True
        }
        
        self.webapp_router.broadcast_mission_update(webapp_completion)
    
    def _archive_mission(self, mapping: MissionSignalMapping) -> None:
        """Archive completed mission"""
        
        # Remove from active missions
        self.active_missions.pop(mapping.mission_id, None)
        self.signal_to_mission.pop(mapping.signal_id, None)
        
        # Archive for historical reference (would save to database in production)
        self.logger.info(f"Mission {mapping.mission_id} archived - Operator {mapping.callsign}")
    
    def _handle_mission_failure(self, mapping: MissionSignalMapping, trade_result: Dict) -> None:
        """Handle mission execution failure"""
        
        failure_alert = {
            'type': 'mission_failed',
            'mission_id': mapping.mission_id,
            'callsign': mapping.callsign,
            'error': trade_result.get('error', 'Unknown error'),
            'retry_available': True,
            'support_contact': '/support/tactical'
        }
        
        self.telegram_router.send_mission_alert(failure_alert)
        
        # Trigger failure event
        self._trigger_event('mission_failed', {
            'mission_id': mapping.mission_id,
            'error': trade_result.get('error'),
            'operator': mapping.callsign
        })
    
    def _trigger_event(self, event_type: str, data: Dict) -> None:
        """Trigger registered event handlers"""
        
        handlers = self.mission_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                self.logger.error(f"Error in event handler for {event_type}: {str(e)}")
    
    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """Register event handler for mission events"""
        
        if event_type not in self.mission_handlers:
            self.mission_handlers[event_type] = []
        
        self.mission_handlers[event_type].append(handler)
    
    def get_active_missions(self, user_id: str = None) -> List[Dict]:
        """Get active missions, optionally filtered by user"""
        
        missions = []
        for mapping in self.active_missions.values():
            if user_id is None or mapping.user_id == user_id:
                missions.append({
                    'mission_id': mapping.mission_id,
                    'signal_id': mapping.signal_id,
                    'operation_type': mapping.operation_type.value,
                    'callsign': mapping.callsign,
                    'status': mapping.status,
                    'created_at': mapping.created_at,
                    'expires_at': mapping.expires_at
                })
        
        return missions
    
    def get_mission_by_signal(self, signal_id: str) -> Optional[str]:
        """Get mission ID by signal ID"""
        return self.signal_to_mission.get(signal_id)
    
    def emergency_abort_mission(self, mission_id: str, user_id: str, reason: str = "Operator initiated") -> Dict:
        """Emergency abort mission and close positions"""
        
        mapping = self.active_missions.get(mission_id)
        if not mapping:
            return {'error': 'mission_not_found'}
        
        if mapping.user_id != user_id:
            return {'error': 'unauthorized_operator'}
        
        try:
            # Emergency close through existing trade manager
            close_result = self.trade_manager.emergency_close({
                'mission_id': mission_id,
                'signal_id': mapping.signal_id,
                'reason': reason
            })
            
            # Update mission status
            mapping.status = 'aborted'
            
            # Send abort notifications
            abort_alert = {
                'type': 'mission_aborted',
                'mission_id': mission_id,
                'callsign': mapping.callsign,
                'reason': reason,
                'close_result': close_result
            }
            
            self.telegram_router.send_mission_alert(abort_alert)
            
            # Trigger abort event
            self._trigger_event('mission_aborted', {
                'mission_id': mission_id,
                'reason': reason,
                'operator': mapping.callsign
            })
            
            return {
                'success': True,
                'mission_status': 'aborted',
                'close_result': close_result,
                'message': f'Mission {mission_id} successfully aborted'
            }
            
        except Exception as e:
            self.logger.error(f"Error aborting mission: {str(e)}")
            return {
                'success': False,
                'error': 'abort_failed',
                'message': str(e)
            }

# Global instance
tactical_mission_integrator = TacticalMissionIntegrator()

# Main integration functions for easy use
def convert_bitten_signal_to_mission(signal_data: Dict, user_id: str, user_tier: str = "RECRUIT") -> Dict:
    """Convert BITTEN signal to tactical mission - main entry point"""
    return tactical_mission_integrator.convert_signal_to_mission(signal_data, user_id, user_tier)

def execute_tactical_mission(mission_id: str, user_id: str, params: Dict = None) -> Dict:
    """Execute tactical mission trade"""
    return tactical_mission_integrator.execute_mission_trade(mission_id, user_id, params)

def get_mission_status(mission_id: str) -> Dict:
    """Get current mission status"""
    return tactical_mission_integrator.monitor_mission_progress(mission_id)

def complete_tactical_mission(mission_id: str, completion_data: Dict) -> Dict:
    """Complete tactical mission and get debrief"""
    return tactical_mission_integrator.complete_mission(mission_id, completion_data)

def abort_tactical_mission(mission_id: str, user_id: str, reason: str = "Operator decision") -> Dict:
    """Emergency abort tactical mission"""
    return tactical_mission_integrator.emergency_abort_mission(mission_id, user_id, reason)

def get_active_tactical_missions(user_id: str = None) -> List[Dict]:
    """Get active tactical missions"""
    return tactical_mission_integrator.get_active_missions(user_id)

# Testing
if __name__ == "__main__":
    # Test signal to mission conversion
    test_signal = {
        'signal_id': 'SIG_TEST_123',
        'type': 'standard',
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'entry_price': 1.0850,
        'stop_loss': 1.0820,
        'take_profit': 1.0890,
        'tcs_score': 82,
        'expected_duration': 45,
        'expires_at': int(time.time()) + 1800
    }
    
    test_user = "test_operator_456"
    
    print("=== SIGNAL TO MISSION CONVERSION TEST ===")
    conversion_result = convert_bitten_signal_to_mission(test_signal, test_user, "RECRUIT")
    
    if conversion_result.get('success'):
        print(f"✅ Signal converted to mission: {conversion_result['mission']['mission_id']}")
        print(f"Operation Type: {conversion_result['mission']['operation_type']}")
        print(f"Callsign: {conversion_result['mission']['callsign']}")
        print(f"Webapp URL: {conversion_result['mission']['webapp_url']}")
        
        # Test mission execution
        mission_id = conversion_result['mission']['mission_id']
        print(f"\n=== MISSION EXECUTION TEST ===")
        execution_result = execute_tactical_mission(mission_id, test_user)
        
        if execution_result.get('success'):
            print(f"✅ Mission executing: {execution_result['mission_status']}")
            print(f"Trade ID: {execution_result.get('trade_id', 'N/A')}")
            print(f"Monitoring URL: {execution_result.get('mission_guidance_url', 'N/A')}")
        else:
            print(f"❌ Mission execution failed: {execution_result.get('error')}")
    else:
        print(f"❌ Signal conversion failed: {conversion_result.get('error')}")
        print(f"Message: {conversion_result.get('message')}")
    
    print("\n=== TACTICAL MISSION INTEGRATION READY ===")