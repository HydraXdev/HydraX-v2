#!/usr/bin/env python3
"""
BITTEN Monitoring System Integrator
Integrates monitoring components with the main BITTEN system.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import threading
import time

from .logging_config import setup_service_logging
from .performance_monitor import get_performance_monitor
from .health_check import create_health_check_system, get_default_config
from .alert_system import get_alert_manager
from .win_rate_monitor import get_win_rate_monitor
from .log_manager import get_log_manager

class BittenMonitoringIntegrator:
    """Integrates monitoring system with main BITTEN components"""
    
    def __init__(self, bitten_core=None, config: Optional[Dict[str, Any]] = None):
        self.bitten_core = bitten_core
        self.config = config or {}
        self.logger = setup_service_logging("monitoring-integrator")
        
        # Initialize monitoring components
        self.performance_monitor = get_performance_monitor()
        self.health_manager, _ = create_health_check_system(get_default_config())
        self.alert_manager = get_alert_manager()
        self.win_rate_monitor = get_win_rate_monitor(self.alert_manager)
        self.log_manager = get_log_manager()
        
        # Integration state
        self.running = False
        self.integration_thread = None
        
        # Hook into BITTEN core if available
        if self.bitten_core:
            self._setup_core_integration()
    
    def _setup_core_integration(self):
        """Setup integration with BITTEN core"""
        try:
            # Hook into signal generation
            if hasattr(self.bitten_core, 'signal_router'):
                self._hook_signal_generation()
            
            # Hook into trade execution
            if hasattr(self.bitten_core, 'fire_router'):
                self._hook_trade_execution()
            
            # Hook into user sessions
            if hasattr(self.bitten_core, 'user_sessions'):
                self._hook_user_sessions()
            
            self.logger.info("BITTEN core integration setup complete")
            
        except Exception as e:
            self.logger.error(f"Error setting up core integration: {e}")
    
    def _hook_signal_generation(self):
        """Hook into signal generation for monitoring"""
        original_generate_signal = getattr(self.bitten_core, 'generate_signal', None)
        
        if original_generate_signal:
            def monitored_generate_signal(*args, **kwargs):
                start_time = datetime.now()
                
                try:
                    result = original_generate_signal(*args, **kwargs)
                    
                    # Record signal generation metrics
                    generation_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    # Extract signal information
                    signal_count = len(result) if isinstance(result, list) else 1
                    
                    # Record metrics
                    self.performance_monitor.signal_monitor.record_signal_generation(
                        signal_count=signal_count,
                        pairs_active=len(set(s.get('symbol', '') for s in result)) if isinstance(result, list) else 1,
                        generation_time_ms=generation_time,
                        tcs_threshold=getattr(self.bitten_core, 'current_tcs_threshold', 70.0),
                        market_conditions='normal',  # Could be enhanced
                        success_rate=0.85,  # Could be calculated
                        avg_confidence=0.75  # Could be calculated
                    )
                    
                    return result
                    
                except Exception as e:
                    self.logger.error(f"Error in signal generation monitoring: {e}")
                    raise
            
            # Replace original method
            setattr(self.bitten_core, 'generate_signal', monitored_generate_signal)
            self.logger.info("Signal generation monitoring hooked")
    
    def _hook_trade_execution(self):
        """Hook into trade execution for monitoring"""
        original_execute_trade = getattr(self.bitten_core.fire_router, 'execute_trade', None)
        
        if original_execute_trade:
            def monitored_execute_trade(*args, **kwargs):
                start_time = datetime.now()
                
                try:
                    result = original_execute_trade(*args, **kwargs)
                    
                    # Record trade execution metrics
                    execution_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    # Extract trade information
                    trade_id = result.get('trade_id', 'unknown')
                    symbol = result.get('symbol', 'unknown')
                    direction = result.get('direction', 'unknown')
                    entry_price = result.get('entry_price', 0.0)
                    lot_size = result.get('lot_size', 0.0)
                    success = result.get('success', False)
                    error_message = result.get('error_message')
                    
                    # Record metrics
                    self.performance_monitor.trade_monitor.record_trade_execution(
                        trade_id=trade_id,
                        symbol=symbol,
                        direction=direction,
                        entry_price=entry_price,
                        lot_size=lot_size,
                        execution_time_ms=execution_time,
                        success=success,
                        error_message=error_message
                    )
                    
                    return result
                    
                except Exception as e:
                    self.logger.error(f"Error in trade execution monitoring: {e}")
                    raise
            
            # Replace original method
            setattr(self.bitten_core.fire_router, 'execute_trade', monitored_execute_trade)
            self.logger.info("Trade execution monitoring hooked")
    
    def _hook_user_sessions(self):
        """Hook into user session management"""
        # This would monitor user activity, session duration, etc.
        # Implementation depends on BITTEN core structure
        pass
    
    def start_monitoring(self):
        """Start all monitoring components"""
        if self.running:
            return
        
        self.running = True
        
        try:
            # Start monitoring components
            self.performance_monitor.start()
            self.health_manager.start_monitoring()
            self.win_rate_monitor.start()
            self.log_manager.start()
            
            # Start integration thread
            self.integration_thread = threading.Thread(target=self._integration_loop)
            self.integration_thread.daemon = True
            self.integration_thread.start()
            
            self.logger.info("Monitoring system started successfully")
            
        except Exception as e:
            self.logger.error(f"Error starting monitoring system: {e}")
            raise
    
    def stop_monitoring(self):
        """Stop all monitoring components"""
        if not self.running:
            return
        
        self.running = False
        
        try:
            # Stop monitoring components
            self.performance_monitor.stop()
            self.health_manager.stop_monitoring()
            self.win_rate_monitor.stop()
            self.log_manager.stop()
            
            # Wait for integration thread
            if self.integration_thread:
                self.integration_thread.join(timeout=5)
            
            self.logger.info("Monitoring system stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping monitoring system: {e}")
    
    def _integration_loop(self):
        """Main integration loop"""
        while self.running:
            try:
                # Periodic health checks
                self._check_system_health()
                
                # Update metrics
                self._update_system_metrics()
                
                # Sleep for 30 seconds
                time.sleep(30)
                
            except Exception as e:
                self.logger.error(f"Error in integration loop: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _check_system_health(self):
        """Check system health and trigger alerts if needed"""
        try:
            # Get current performance
            performance = self.performance_monitor.get_current_status()
            
            # Check signal generation
            signal_perf = performance.get('signal_performance', {})
            if signal_perf.get('signals_today', 0) < 52:  # 80% of target
                self.alert_manager.check_metric(
                    service="signal-generator",
                    metric="signals_today",
                    value=signal_perf.get('signals_today', 0)
                )
            
            # Check win rate
            trade_perf = performance.get('trade_performance', {})
            if trade_perf.get('win_rate', 0) < 80:  # Below warning threshold
                self.alert_manager.check_metric(
                    service="trade-executor",
                    metric="win_rate",
                    value=trade_perf.get('win_rate', 0)
                )
            
        except Exception as e:
            self.logger.error(f"Error checking system health: {e}")
    
    def _update_system_metrics(self):
        """Update system metrics"""
        try:
            # Update system resource metrics
            import psutil
            
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_usage = psutil.virtual_memory().percent
            
            # Record system metrics
            self.performance_monitor.health_monitor.record_system_metrics(
                service_name="bitten-core",
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                active_connections=len(psutil.net_connections()),
                response_time_ms=0.0,  # Would be calculated from actual requests
                error_rate=0.0  # Would be calculated from logs
            )
            
        except Exception as e:
            self.logger.error(f"Error updating system metrics: {e}")
    
    def record_trade_close(self, trade_id: str, symbol: str, direction: str,
                          entry_price: float, exit_price: float,
                          entry_time: datetime, exit_time: datetime,
                          lot_size: float, pnl: float, strategy: str = None):
        """Record a completed trade for win rate monitoring"""
        try:
            # Record in performance monitor
            self.performance_monitor.trade_monitor.record_trade_close(
                trade_id=trade_id,
                exit_price=exit_price,
                pnl=pnl
            )
            
            # Record in win rate monitor
            self.win_rate_monitor.record_trade(
                trade_id=trade_id,
                symbol=symbol,
                direction=direction,
                entry_price=entry_price,
                exit_price=exit_price,
                entry_time=entry_time,
                exit_time=exit_time,
                lot_size=lot_size,
                pnl=pnl,
                strategy=strategy
            )
            
        except Exception as e:
            self.logger.error(f"Error recording trade close: {e}")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get comprehensive monitoring status"""
        try:
            return {
                'performance': self.performance_monitor.get_current_status(),
                'health': self.health_manager.get_overall_health(),
                'alerts': self.alert_manager.get_alert_summary(),
                'win_rate': self.win_rate_monitor.get_current_status(),
                'logs': self.log_manager.get_status(),
                'integration': {
                    'running': self.running,
                    'core_integrated': self.bitten_core is not None,
                    'timestamp': datetime.now().isoformat()
                }
            }
        except Exception as e:
            self.logger.error(f"Error getting monitoring status: {e}")
            return {'error': str(e)}

# Global monitoring integrator
_monitoring_integrator = None

def get_monitoring_integrator(bitten_core=None, config: Optional[Dict[str, Any]] = None) -> BittenMonitoringIntegrator:
    """Get global monitoring integrator instance"""
    global _monitoring_integrator
    if _monitoring_integrator is None:
        _monitoring_integrator = BittenMonitoringIntegrator(bitten_core, config)
    return _monitoring_integrator

def setup_bitten_monitoring(bitten_core, config: Optional[Dict[str, Any]] = None):
    """Setup monitoring for BITTEN system"""
    integrator = get_monitoring_integrator(bitten_core, config)
    integrator.start_monitoring()
    return integrator

# Example usage
if __name__ == "__main__":
    # Test monitoring integrator
    integrator = get_monitoring_integrator()
    integrator.start_monitoring()
    
    # Simulate some activity
    import time
    time.sleep(5)
    
    # Get status
    status = integrator.get_monitoring_status()
    print("Monitoring Status:")
    import json
    print(json.dumps(status, indent=2, default=str))
    
    # Stop monitoring
    integrator.stop_monitoring()