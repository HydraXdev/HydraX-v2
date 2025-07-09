#!/usr/bin/env python3
"""
Main script to run the Press Pass Monitoring System

This script initializes and runs all monitoring components including:
- Real-time metric monitoring
- Anomaly detection
- Automated reporting
- Alert management
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
import redis
import asyncpg
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.analytics.dashboards.press_pass_metrics import PressPassMetricsDashboard
from src.analytics.monitoring.realtime_monitor import RealtimeMonitor
from src.analytics.monitoring.anomaly_detector import (
    AnomalyDetector, AlertManager, log_alert_handler, webhook_alert_handler
)
from src.analytics.reporting.report_generator import ReportGenerator, ReportScheduler
from src.analytics.visualization.funnel_visualizer import FunnelVisualizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('press_pass_monitoring.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class MonitoringSystem:
    """Main monitoring system coordinator"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_pool = None
        self.redis_client = None
        self.components = {}
        
    async def initialize(self):
        """Initialize all monitoring components"""
        logger.info("Initializing Press Pass Monitoring System...")
        
        # Initialize database connection pool
        self.db_pool = await asyncpg.create_pool(
            host=self.config['database']['host'],
            port=self.config['database']['port'],
            user=self.config['database']['user'],
            password=self.config['database']['password'],
            database=self.config['database']['name'],
            min_size=10,
            max_size=20
        )
        
        # Initialize Redis client
        self.redis_client = redis.Redis(
            host=self.config['redis']['host'],
            port=self.config['redis']['port'],
            db=self.config['redis']['db'],
            decode_responses=True
        )
        
        # Initialize components
        self.components['dashboard'] = PressPassMetricsDashboard(self.db_pool)
        self.components['monitor'] = RealtimeMonitor(self.db_pool, self.redis_client)
        self.components['anomaly_detector'] = AnomalyDetector(
            sensitivity=self.config.get('anomaly_sensitivity', 2.5)
        )
        self.components['alert_manager'] = AlertManager(self.components['anomaly_detector'])
        self.components['report_generator'] = ReportGenerator(self.components['dashboard'])
        self.components['report_scheduler'] = ReportScheduler(self.components['report_generator'])
        self.components['visualizer'] = FunnelVisualizer()
        
        # Set up alert handlers
        self._setup_alert_handlers()
        
        logger.info("Monitoring System initialized successfully")
        
    def _setup_alert_handlers(self):
        """Configure alert handlers"""
        # Add log handler
        self.components['alert_manager'].add_handler(log_alert_handler)
        
        # Add webhook handler if configured
        if 'webhook_url' in self.config.get('alerts', {}):
            webhook_url = self.config['alerts']['webhook_url']
            async def webhook_handler(alert):
                await webhook_alert_handler(alert, webhook_url)
            self.components['alert_manager'].add_handler(webhook_handler)
        
        # Add email handler if configured
        if 'email' in self.config.get('alerts', {}):
            self._setup_email_alerts()
        
        # Configure suppression rules
        suppression_rules = self.config.get('alerts', {}).get('suppression_rules', {})
        for metric, interval in suppression_rules.items():
            self.components['alert_manager'].add_suppression_rule(metric, interval)
    
    def _setup_email_alerts(self):
        """Set up email alert handler"""
        # This would integrate with your email service
        pass
    
    async def start(self):
        """Start all monitoring services"""
        logger.info("Starting monitoring services...")
        
        try:
            # Start all monitoring tasks
            tasks = [
                self.components['monitor'].start_monitoring(),
                self.components['report_scheduler'].start(),
                self._run_anomaly_detection(),
                self._generate_hourly_dashboard()
            ]
            
            # Add health check task
            tasks.append(self._health_check())
            
            # Run all tasks concurrently
            await asyncio.gather(*tasks)
            
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
            await self.shutdown()
        except Exception as e:
            logger.error(f"Error in monitoring system: {e}")
            await self.shutdown()
            raise
    
    async def shutdown(self):
        """Gracefully shutdown all components"""
        logger.info("Shutting down monitoring system...")
        
        # Stop monitoring components
        if 'monitor' in self.components:
            await self.components['monitor'].stop_monitoring()
        
        if 'report_scheduler' in self.components:
            await self.components['report_scheduler'].stop()
        
        # Close connections
        if self.db_pool:
            await self.db_pool.close()
        
        if self.redis_client:
            self.redis_client.close()
        
        logger.info("Monitoring system shutdown complete")
    
    async def _run_anomaly_detection(self):
        """Run continuous anomaly detection"""
        while True:
            try:
                # Get current metrics
                metrics = await self.components['monitor'].get_current_metrics()
                
                # Check each metric for anomalies
                for metric_name, metric_data in metrics.items():
                    if isinstance(metric_data, dict) and 'value' in metric_data:
                        await self.components['alert_manager'].check_and_alert(
                            metric_name,
                            metric_data['value'],
                            datetime.utcnow()
                        )
                
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in anomaly detection: {e}")
                await asyncio.sleep(60)
    
    async def _generate_hourly_dashboard(self):
        """Generate hourly dashboard snapshot"""
        while True:
            try:
                # Wait for next hour
                now = datetime.utcnow()
                next_hour = now.replace(minute=0, second=0, microsecond=0)
                if now.minute > 0:
                    next_hour = next_hour.replace(hour=now.hour + 1)
                
                wait_seconds = (next_hour - now).total_seconds()
                await asyncio.sleep(wait_seconds)
                
                # Generate dashboard
                logger.info("Generating hourly dashboard snapshot...")
                
                # Get current metrics
                metrics = await self.components['monitor'].get_current_metrics()
                
                # Create dashboard
                fig = self.components['visualizer'].create_real_time_dashboard(metrics)
                
                # Export to HTML
                filename = f"dashboard_{next_hour.strftime('%Y%m%d_%H')}.html"
                output_path = os.path.join(self.config.get('output_dir', '/tmp'), filename)
                self.components['visualizer'].export_dashboard_html(fig, output_path)
                
                logger.info(f"Dashboard snapshot saved to {output_path}")
                
            except Exception as e:
                logger.error(f"Error generating dashboard: {e}")
                await asyncio.sleep(3600)
    
    async def _health_check(self):
        """Periodic health check of the monitoring system"""
        while True:
            try:
                # Check database connection
                async with self.db_pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                
                # Check Redis connection
                self.redis_client.ping()
                
                # Log system status
                logger.info("Health check: All systems operational")
                
                # Store health status in Redis
                self.redis_client.setex(
                    "monitoring:health:status",
                    300,  # 5 minute TTL
                    "healthy"
                )
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                self.redis_client.setex(
                    "monitoring:health:status",
                    300,
                    f"unhealthy: {str(e)}"
                )
                await asyncio.sleep(60)  # Retry in 1 minute

def load_config() -> Dict[str, Any]:
    """Load configuration from environment or config file"""
    config = {
        'database': {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'name': os.getenv('DB_NAME', 'bitten_db')
        },
        'redis': {
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': int(os.getenv('REDIS_PORT', 6379)),
            'db': int(os.getenv('REDIS_DB', 0))
        },
        'alerts': {
            'webhook_url': os.getenv('ALERT_WEBHOOK_URL'),
            'email': {
                'enabled': os.getenv('EMAIL_ALERTS_ENABLED', 'false').lower() == 'true',
                'recipients': os.getenv('ALERT_EMAIL_RECIPIENTS', '').split(',')
            },
            'suppression_rules': {
                'press_pass_conversions': 30,  # minutes
                'activation_rate': 60,
                'error_rate': 15
            }
        },
        'anomaly_sensitivity': float(os.getenv('ANOMALY_SENSITIVITY', 2.5)),
        'output_dir': os.getenv('OUTPUT_DIR', '/var/www/html/analytics')
    }
    
    return config

async def main():
    """Main entry point"""
    logger.info("Starting Press Pass Monitoring System")
    
    # Load configuration
    config = load_config()
    
    # Create monitoring system
    monitoring_system = MonitoringSystem(config)
    
    try:
        # Initialize components
        await monitoring_system.initialize()
        
        # Start monitoring
        await monitoring_system.start()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        await monitoring_system.shutdown()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())