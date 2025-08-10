#!/usr/bin/env python3
"""
SYSTEM OFFLINE MANAGER
Manages system offline states when real data is unavailable
CRITICAL: Better to be offline and honest than online with fake data
"""

import json
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from enum import Enum
from dataclasses import dataclass
import sys

# Add project root to path
sys.path.append('/root/HydraX-v2')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - OFFLINE_MANAGER - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/logs/system_offline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OfflineReason(Enum):
    """Reasons why system components go offline"""
    NO_REAL_DATA = "no_real_data"
    BROKER_CONNECTIONS_FAILED = "broker_connections_failed"
    MARKET_DATA_STALE = "market_data_stale"
    API_CREDENTIALS_MISSING = "api_credentials_missing"
    VALIDATION_FAILURES = "validation_failures"
    MANUAL_SHUTDOWN = "manual_shutdown"
    SYSTEM_ERROR = "system_error"

@dataclass
class OfflineStatus:
    """Status of an offline component"""
    component: str
    reason: OfflineReason
    offline_since: float
    last_attempt: float
    attempt_count: int
    max_attempts: int
    auto_recovery: bool
    user_message: str
    technical_details: str

class SystemOfflineManager:
    """
    Manages system offline states with graceful degradation
    PRINCIPLE: Better offline with truth than online with lies
    """
    
    def __init__(self):
        self.offline_components: Dict[str, OfflineStatus] = {}
        self.monitoring_thread = None
        self.running = False
        self.recovery_attempts = {}
        
        # Component definitions
        self.critical_components = {
            'market_data': {
                'name': 'Market Data Feed',
                'max_stale_seconds': 60,
                'auto_recovery': True,
                'max_attempts': 5,
                'retry_interval': 30
            },
            'broker_apis': {
                'name': 'Broker API Connections',
                'max_stale_seconds': 300,  # 5 minutes
                'auto_recovery': True,
                'max_attempts': 3,
                'retry_interval': 60
            },
            'truth_tracker': {
                'name': 'Truth Tracking System',
                'max_stale_seconds': 120,
                'auto_recovery': True,
                'max_attempts': 3,
                'retry_interval': 45
            },
            'position_tracker': {
                'name': 'Position Tracking',
                'max_stale_seconds': 90,
                'auto_recovery': True,
                'max_attempts': 3,
                'retry_interval': 30
            },
            'citadel_shield': {
                'name': 'CITADEL Shield System',
                'max_stale_seconds': 180,
                'auto_recovery': True,
                'max_attempts': 3,
                'retry_interval': 60
            },
            'signal_generation': {
                'name': 'Signal Generation Engine',
                'max_stale_seconds': 600,  # 10 minutes
                'auto_recovery': False,  # Manual intervention required
                'max_attempts': 1,
                'retry_interval': 300
            }
        }
        
        self.offline_messages = {
            OfflineReason.NO_REAL_DATA: {
                'user': "⚠️ System temporarily offline - ensuring data accuracy",
                'technical': "No verified real market data available"
            },
            OfflineReason.BROKER_CONNECTIONS_FAILED: {
                'user': "🔌 Connection issues - protecting your capital",
                'technical': "Real broker API connections failed"
            },
            OfflineReason.MARKET_DATA_STALE: {
                'user': "📊 Market data updating - please wait",
                'technical': "Market data feed is stale or interrupted"
            },
            OfflineReason.API_CREDENTIALS_MISSING: {
                'user': "🔑 Configuration required - contact support",
                'technical': "Missing API credentials for real data sources"
            },
            OfflineReason.VALIDATION_FAILURES: {
                'user': "🛡️ Security checks active - ensuring data integrity",
                'technical': "Real data validation failures detected"
            },
            OfflineReason.MANUAL_SHUTDOWN: {
                'user': "🔧 Maintenance mode - system will return shortly",
                'technical': "Manual shutdown for maintenance"
            },
            OfflineReason.SYSTEM_ERROR: {
                'user': "⚠️ Technical issue - engineers are investigating",
                'technical': "Unexpected system error occurred"
            }
        }
        
        logger.info("🔧 System Offline Manager initialized")
        
    def take_component_offline(self, component: str, reason: OfflineReason, details: str = ""):
        """
        Take a system component offline with proper messaging
        """
        try:
            now = time.time()
            
            if component in self.offline_components:
                # Component already offline - update reason if different
                existing = self.offline_components[component]
                if existing.reason != reason:
                    logger.warning(f"📝 {component} offline reason changed: {existing.reason.value} -> {reason.value}")
                    existing.reason = reason
                    existing.last_attempt = now
                    existing.technical_details = details
                return
                
            # Get component config
            config = self.critical_components.get(component, {})
            
            # Create offline status
            messages = self.offline_messages.get(reason, {
                'user': "⚠️ System component temporarily unavailable",
                'technical': "Component offline for unknown reason"
            })
            
            offline_status = OfflineStatus(
                component=component,
                reason=reason,
                offline_since=now,
                last_attempt=now,
                attempt_count=0,
                max_attempts=config.get('max_attempts', 3),
                auto_recovery=config.get('auto_recovery', True),
                user_message=messages['user'],
                technical_details=details or messages['technical']
            )
            
            self.offline_components[component] = offline_status
            
            component_name = config.get('name', component)
            logger.critical(f"🚨 {component_name} OFFLINE: {reason.value}")
            logger.critical(f"🚨 User Message: {offline_status.user_message}")
            logger.critical(f"🚨 Technical: {offline_status.technical_details}")
            
            # Log to separate offline events file
            self._log_offline_event(component, reason, details)
            
            # Notify dependent components
            self._notify_dependencies(component, "OFFLINE")
            
        except Exception as e:
            logger.error(f"❌ Error taking {component} offline: {str(e)}")
            
    def bring_component_online(self, component: str, verification_passed: bool = True):
        """
        Bring a system component back online after verification
        """
        try:
            if component not in self.offline_components:
                logger.info(f"✅ {component} already online")
                return True
                
            offline_status = self.offline_components[component]
            config = self.critical_components.get(component, {})
            component_name = config.get('name', component)
            
            if not verification_passed:
                logger.error(f"❌ {component_name} failed verification - keeping offline")
                offline_status.attempt_count += 1
                offline_status.last_attempt = time.time()
                return False
                
            # Remove from offline components
            offline_duration = time.time() - offline_status.offline_since
            del self.offline_components[component]
            
            logger.info(f"✅ {component_name} ONLINE after {offline_duration:.1f}s")
            logger.info(f"✅ Reason resolved: {offline_status.reason.value}")
            
            # Log recovery
            self._log_recovery_event(component, offline_duration)
            
            # Notify dependent components
            self._notify_dependencies(component, "ONLINE")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error bringing {component} online: {str(e)}")
            return False
            
    def get_system_status(self) -> Dict:
        """Get comprehensive system offline status"""
        try:
            now = time.time()
            
            # Calculate component statuses
            component_statuses = {}
            for comp_id, config in self.critical_components.items():
                if comp_id in self.offline_components:
                    offline_status = self.offline_components[comp_id]
                    offline_duration = now - offline_status.offline_since
                    
                    component_statuses[comp_id] = {
                        'status': 'OFFLINE',
                        'reason': offline_status.reason.value,
                        'offline_duration': offline_duration,
                        'user_message': offline_status.user_message,
                        'auto_recovery': offline_status.auto_recovery,
                        'attempts': offline_status.attempt_count,
                        'max_attempts': offline_status.max_attempts
                    }
                else:
                    component_statuses[comp_id] = {
                        'status': 'ONLINE',
                        'reason': None,
                        'offline_duration': 0,
                        'user_message': '✅ Operating normally',
                        'auto_recovery': True,
                        'attempts': 0,
                        'max_attempts': 0
                    }
                    
            # Calculate overall system health
            total_components = len(self.critical_components)
            offline_components = len(self.offline_components)
            online_components = total_components - offline_components
            
            system_health = (online_components / total_components) * 100 if total_components > 0 else 0
            
            # Determine system state
            if offline_components == 0:
                system_state = "FULLY_OPERATIONAL"
            elif system_health >= 80:
                system_state = "DEGRADED"
            elif system_health >= 50:
                system_state = "LIMITED"
            else:
                system_state = "CRITICAL"
                
            return {
                'system_state': system_state,
                'system_health': system_health,
                'total_components': total_components,
                'online_components': online_components,
                'offline_components': offline_components,
                'component_statuses': component_statuses,
                'offline_since_longest': min([s.offline_since for s in self.offline_components.values()]) if self.offline_components else None,
                'fake_data_allowed': False,  # NEVER
                'real_data_only': True,
                'last_check': now
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting system status: {str(e)}")
            return {
                'system_state': 'ERROR',
                'system_health': 0,
                'error': str(e)
            }
            
    def start_monitoring(self):
        """Start the offline monitoring system"""
        if self.running:
            logger.warning("⚠️ Offline monitoring already running")
            return
            
        self.running = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        logger.info("🚀 System offline monitoring started")
        
    def stop_monitoring(self):
        """Stop the offline monitoring system"""
        logger.info("🛑 Stopping system offline monitoring...")
        self.running = False
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)
            
        logger.info("✅ System offline monitoring stopped")
        
    def _monitoring_loop(self):
        """Main monitoring loop for auto-recovery"""
        while self.running:
            try:
                now = time.time()
                
                # Check for auto-recovery opportunities
                for component, offline_status in list(self.offline_components.items()):
                    if not offline_status.auto_recovery:
                        continue
                        
                    config = self.critical_components.get(component, {})
                    retry_interval = config.get('retry_interval', 60)
                    
                    # Check if it's time for retry
                    if now - offline_status.last_attempt >= retry_interval:
                        if offline_status.attempt_count < offline_status.max_attempts:
                            logger.info(f"🔄 Attempting auto-recovery for {component}")
                            self._attempt_recovery(component, offline_status)
                        else:
                            logger.error(f"❌ Max recovery attempts reached for {component}")
                            offline_status.auto_recovery = False  # Stop trying
                            
                # Sleep for monitoring interval
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"❌ Monitoring loop error: {str(e)}")
                time.sleep(60)
                
    def _attempt_recovery(self, component: str, offline_status: OfflineStatus):
        """Attempt to recover an offline component"""
        try:
            offline_status.attempt_count += 1
            offline_status.last_attempt = time.time()
            
            config = self.critical_components.get(component, {})
            component_name = config.get('name', component)
            
            logger.info(f"🔄 Recovery attempt {offline_status.attempt_count}/{offline_status.max_attempts} for {component_name}")
            
            # Component-specific recovery logic
            recovery_success = False
            
            if component == 'market_data':
                recovery_success = self._recover_market_data()
            elif component == 'broker_apis':
                recovery_success = self._recover_broker_apis()
            elif component == 'truth_tracker':
                recovery_success = self._recover_truth_tracker()
            elif component == 'position_tracker':
                recovery_success = self._recover_position_tracker()
            elif component == 'citadel_shield':
                recovery_success = self._recover_citadel_shield()
                
            if recovery_success:
                self.bring_component_online(component, verification_passed=True)
            else:
                logger.warning(f"⚠️ Recovery attempt failed for {component_name}")
                
        except Exception as e:
            logger.error(f"❌ Recovery attempt error for {component}: {str(e)}")
            
    def _recover_market_data(self) -> bool:
        """Attempt to recover market data feed"""
        try:
            # Check if market data receiver is responding
            import requests
            response = requests.get("http://localhost:8001/health", timeout=5)
            return response.status_code == 200
        except:
            return False
            
    def _recover_broker_apis(self) -> bool:
        """Attempt to recover broker API connections"""
        try:
            from citadel_shield_real_data_only import CitadelShieldRealDataOnly
            shield = CitadelShieldRealDataOnly()
            return shield.system_state == "ONLINE"
        except:
            return False
            
    def _recover_truth_tracker(self) -> bool:
        """Attempt to recover truth tracker"""
        try:
            from black_box_complete_truth_system import get_truth_system
            truth_system = get_truth_system()
            return truth_system is not None
        except:
            return False
            
    def _recover_position_tracker(self) -> bool:
        """Attempt to recover position tracker"""
        try:
            from position_tracker import PositionTrackerAPI
            tracker = PositionTrackerAPI()
            return tracker.health_check().get('status') == 'healthy'
        except:
            return False
            
    def _recover_citadel_shield(self) -> bool:
        """Attempt to recover CITADEL shield"""
        try:
            from citadel_shield_real_data_only import CitadelShieldRealDataOnly
            shield = CitadelShieldRealDataOnly()
            return shield.system_state != "OFFLINE"
        except:
            return False
            
    def _log_offline_event(self, component: str, reason: OfflineReason, details: str):
        """Log offline event to audit file"""
        try:
            event = {
                'timestamp': time.time(),
                'datetime': datetime.now().isoformat(),
                'event_type': 'COMPONENT_OFFLINE',
                'component': component,
                'reason': reason.value,
                'details': details,
                'real_data_enforcement': True
            }
            
            with open('/root/HydraX-v2/logs/offline_events.jsonl', 'a') as f:
                f.write(json.dumps(event) + '\n')
                
        except Exception as e:
            logger.error(f"❌ Error logging offline event: {str(e)}")
            
    def _log_recovery_event(self, component: str, offline_duration: float):
        """Log recovery event to audit file"""
        try:
            event = {
                'timestamp': time.time(),
                'datetime': datetime.now().isoformat(),
                'event_type': 'COMPONENT_RECOVERY',
                'component': component,
                'offline_duration': offline_duration,
                'offline_duration_minutes': offline_duration / 60,
                'real_data_enforcement': True
            }
            
            with open('/root/HydraX-v2/logs/offline_events.jsonl', 'a') as f:
                f.write(json.dumps(event) + '\n')
                
        except Exception as e:
            logger.error(f"❌ Error logging recovery event: {str(e)}")
            
    def _notify_dependencies(self, component: str, status: str):
        """Notify dependent components of status change"""
        try:
            # Component dependency mapping
            dependencies = {
                'market_data': ['signal_generation', 'citadel_shield'],
                'broker_apis': ['citadel_shield', 'position_tracker'],
                'truth_tracker': ['signal_generation'],
                'position_tracker': ['truth_tracker'],
                'citadel_shield': ['signal_generation'],
                'signal_generation': []
            }
            
            dependents = dependencies.get(component, [])
            if dependents:
                logger.info(f"📡 Notifying dependents of {component}: {dependents}")
                
                if status == "OFFLINE":
                    # Take dependents offline too
                    for dependent in dependents:
                        if dependent not in self.offline_components:
                            self.take_component_offline(
                                dependent, 
                                OfflineReason.NO_REAL_DATA,
                                f"Dependency {component} is offline"
                            )
                            
        except Exception as e:
            logger.error(f"❌ Error notifying dependencies: {str(e)}")

# Global instance
_offline_manager = None

def get_offline_manager() -> SystemOfflineManager:
    """Get or create singleton offline manager"""
    global _offline_manager
    if not _offline_manager:
        _offline_manager = SystemOfflineManager()
    return _offline_manager

if __name__ == "__main__":
    # Run offline manager service
    manager = get_offline_manager()
    
    try:
        manager.start_monitoring()
        
        logger.info("=" * 60)
        logger.info("🔧 SYSTEM OFFLINE MANAGER SERVICE")
        logger.info("=" * 60)
        logger.info("🚨 REAL DATA ENFORCEMENT: Active")
        logger.info("⚠️ Better offline and honest than online with fake data")
        logger.info("🔄 Auto-recovery monitoring active")
        logger.info("=" * 60)
        
        # Run forever
        while True:
            status = manager.get_system_status()
            logger.info(f"📊 System Health: {status['system_health']:.1f}% ({status['system_state']})")
            time.sleep(300)  # Report every 5 minutes
            
    except KeyboardInterrupt:
        logger.info("🛑 Shutdown signal received")
        manager.stop_monitoring()