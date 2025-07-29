"""
BITTEN Monitoring & Observability System
Performance metrics, health checks, and system monitoring
"""
import time
import psutil
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import aioredis
from sqlalchemy import func

from database.models import get_db, User, Trade, Signal, SystemLog
from forexvps.client import ForexVPSClient
from logging.logger import app_logger, performance_logger

@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    uptime_seconds: int
    active_connections: int
    timestamp: datetime

@dataclass
class DatabaseMetrics:
    """Database performance metrics"""
    total_users: int
    active_users_24h: int
    total_trades: int
    trades_24h: int
    successful_trades_24h: int
    win_rate_24h: float
    avg_response_time: float
    timestamp: datetime

@dataclass
class ForexVPSMetrics:
    """ForexVPS integration metrics"""
    api_health: str
    avg_response_time: float
    successful_requests_24h: int
    failed_requests_24h: int
    success_rate: float
    last_error: Optional[str]
    timestamp: datetime

class MetricsCollector:
    """Collect system, database, and ForexVPS metrics"""
    
    def __init__(self):
        self.redis_client = None
        self.collection_interval = 60  # seconds
        self.metrics_retention = 24 * 60 * 60  # 24 hours
    
    async def initialize(self, redis_url: str):
        """Initialize metrics collector"""
        try:
            self.redis_client = aioredis.from_url(redis_url)
            await self.redis_client.ping()
            app_logger.info("✅ Metrics collector initialized with Redis")
        except Exception as e:
            app_logger.warning(f"⚠️ Metrics collector Redis connection failed: {e}")
            self.redis_client = None
    
    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect system performance metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # System uptime
            boot_time = psutil.boot_time()
            uptime_seconds = int(time.time() - boot_time)
            
            # Network connections (approximate active connections)
            connections = len(psutil.net_connections(kind='inet'))
            
            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                uptime_seconds=uptime_seconds,
                active_connections=connections,
                timestamp=datetime.utcnow()
            )
            
            app_logger.debug(f"System metrics collected: CPU {cpu_percent}%, Memory {memory_percent}%, Disk {disk_percent}%")
            return metrics
            
        except Exception as e:
            app_logger.error(f"Failed to collect system metrics: {e}")
            raise
    
    async def collect_database_metrics(self) -> DatabaseMetrics:
        """Collect database performance metrics"""
        try:
            db = next(get_db())
            now = datetime.utcnow()
            yesterday = now - timedelta(days=1)
            
            # Total users
            total_users = db.query(User).count()
            
            # Active users in last 24h (users with trades)
            active_users_24h = db.query(User.id).join(Trade).filter(
                Trade.created_at >= yesterday
            ).distinct().count()
            
            # Total trades
            total_trades = db.query(Trade).count()
            
            # Trades in last 24h
            trades_24h = db.query(Trade).filter(Trade.created_at >= yesterday).count()
            
            # Successful trades in last 24h
            successful_trades_24h = db.query(Trade).filter(
                Trade.created_at >= yesterday,
                Trade.status == "executed"
            ).count()
            
            # Win rate calculation
            win_rate_24h = (successful_trades_24h / trades_24h * 100) if trades_24h > 0 else 0
            
            # Average response time (placeholder - implement query timing)
            avg_response_time = 0.05  # 50ms placeholder
            
            db.close()
            
            metrics = DatabaseMetrics(
                total_users=total_users,
                active_users_24h=active_users_24h,
                total_trades=total_trades,
                trades_24h=trades_24h,
                successful_trades_24h=successful_trades_24h,
                win_rate_24h=round(win_rate_24h, 2),
                avg_response_time=avg_response_time,
                timestamp=datetime.utcnow()
            )
            
            app_logger.debug(f"Database metrics collected: {total_users} users, {trades_24h} trades/24h, {win_rate_24h}% win rate")
            return metrics
            
        except Exception as e:
            app_logger.error(f"Failed to collect database metrics: {e}")
            raise
    
    async def collect_forexvps_metrics(self) -> ForexVPSMetrics:
        """Collect ForexVPS integration metrics"""
        try:
            start_time = time.time()
            
            # Test ForexVPS health
            async with ForexVPSClient() as client:
                health_result = await client.health_check()
            
            response_time = time.time() - start_time
            api_health = health_result.get("status", "unknown")
            
            # Get success/failure rates from Redis if available
            successful_requests_24h = 0
            failed_requests_24h = 0
            last_error = None
            
            if self.redis_client:
                try:
                    # Get request counts from Redis
                    successful_requests_24h = await self.redis_client.get("forexvps:success:24h") or 0
                    failed_requests_24h = await self.redis_client.get("forexvps:failed:24h") or 0
                    last_error = await self.redis_client.get("forexvps:last_error")
                    
                    successful_requests_24h = int(successful_requests_24h)
                    failed_requests_24h = int(failed_requests_24h)
                except Exception as e:
                    app_logger.warning(f"Failed to get ForexVPS metrics from Redis: {e}")
            
            # Calculate success rate
            total_requests = successful_requests_24h + failed_requests_24h
            success_rate = (successful_requests_24h / total_requests * 100) if total_requests > 0 else 100
            
            metrics = ForexVPSMetrics(
                api_health=api_health,
                avg_response_time=response_time,
                successful_requests_24h=successful_requests_24h,
                failed_requests_24h=failed_requests_24h,
                success_rate=round(success_rate, 2),
                last_error=last_error,
                timestamp=datetime.utcnow()
            )
            
            app_logger.debug(f"ForexVPS metrics collected: {api_health} health, {response_time:.3f}s response time")
            return metrics
            
        except Exception as e:
            app_logger.error(f"Failed to collect ForexVPS metrics: {e}")
            # Return default metrics on failure
            return ForexVPSMetrics(
                api_health="unhealthy",
                avg_response_time=0.0,
                successful_requests_24h=0,
                failed_requests_24h=1,
                success_rate=0.0,
                last_error=str(e),
                timestamp=datetime.utcnow()
            )
    
    async def store_metrics(self, metrics: Dict[str, Any]):
        """Store metrics in Redis for historical data"""
        if not self.redis_client:
            return
        
        try:
            timestamp = int(time.time())
            
            # Store with timestamp key
            for metric_type, metric_data in metrics.items():
                key = f"metrics:{metric_type}:{timestamp}"
                await self.redis_client.setex(
                    key, 
                    self.metrics_retention, 
                    str(metric_data.__dict__ if hasattr(metric_data, '__dict__') else metric_data)
                )
            
            # Store latest metrics
            for metric_type, metric_data in metrics.items():
                latest_key = f"metrics:{metric_type}:latest"
                await self.redis_client.set(
                    latest_key,
                    str(metric_data.__dict__ if hasattr(metric_data, '__dict__') else metric_data)
                )
            
            app_logger.debug(f"Metrics stored in Redis: {list(metrics.keys())}")
            
        except Exception as e:
            app_logger.error(f"Failed to store metrics in Redis: {e}")
    
    async def get_historical_metrics(self, metric_type: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get historical metrics from Redis"""
        if not self.redis_client:
            return []
        
        try:
            now = int(time.time())
            start_time = now - (hours * 3600)
            
            # Get all metric keys in time range
            pattern = f"metrics:{metric_type}:*"
            keys = await self.redis_client.keys(pattern)
            
            # Filter keys by timestamp
            historical_data = []
            for key in keys:
                key_str = key.decode() if isinstance(key, bytes) else key
                timestamp_str = key_str.split(':')[-1]
                
                if timestamp_str.isdigit():
                    timestamp = int(timestamp_str)
                    if start_time <= timestamp <= now:
                        data = await self.redis_client.get(key)
                        if data:
                            historical_data.append({
                                "timestamp": timestamp,
                                "data": data.decode() if isinstance(data, bytes) else data
                            })
            
            # Sort by timestamp
            historical_data.sort(key=lambda x: x["timestamp"])
            return historical_data
            
        except Exception as e:
            app_logger.error(f"Failed to get historical metrics: {e}")
            return []

class HealthChecker:
    """System health monitoring"""
    
    def __init__(self):
        self.critical_thresholds = {
            "cpu_percent": 90.0,
            "memory_percent": 90.0,
            "disk_percent": 85.0,
            "forexvps_response_time": 5.0,
            "database_response_time": 1.0
        }
    
    def evaluate_system_health(self, system_metrics: SystemMetrics) -> Dict[str, Any]:
        """Evaluate system health based on metrics"""
        health_status = {
            "overall": "healthy",
            "issues": [],
            "warnings": []
        }
        
        # Check CPU usage
        if system_metrics.cpu_percent > self.critical_thresholds["cpu_percent"]:
            health_status["overall"] = "critical"
            health_status["issues"].append(f"High CPU usage: {system_metrics.cpu_percent}%")
        elif system_metrics.cpu_percent > 70:
            health_status["warnings"].append(f"Elevated CPU usage: {system_metrics.cpu_percent}%")
        
        # Check memory usage
        if system_metrics.memory_percent > self.critical_thresholds["memory_percent"]:
            health_status["overall"] = "critical"
            health_status["issues"].append(f"High memory usage: {system_metrics.memory_percent}%")
        elif system_metrics.memory_percent > 75:
            health_status["warnings"].append(f"Elevated memory usage: {system_metrics.memory_percent}%")
        
        # Check disk usage
        if system_metrics.disk_percent > self.critical_thresholds["disk_percent"]:
            health_status["overall"] = "critical"
            health_status["issues"].append(f"High disk usage: {system_metrics.disk_percent}%")
        elif system_metrics.disk_percent > 70:
            health_status["warnings"].append(f"Elevated disk usage: {system_metrics.disk_percent}%")
        
        # Set status based on issues
        if health_status["issues"]:
            health_status["overall"] = "critical"
        elif health_status["warnings"]:
            health_status["overall"] = "warning"
        
        return health_status
    
    def evaluate_forexvps_health(self, forexvps_metrics: ForexVPSMetrics) -> Dict[str, Any]:
        """Evaluate ForexVPS health"""
        health_status = {
            "overall": "healthy",
            "issues": [],
            "warnings": []
        }
        
        # Check API health status
        if forexvps_metrics.api_health != "healthy":
            health_status["overall"] = "critical"
            health_status["issues"].append(f"ForexVPS API unhealthy: {forexvps_metrics.api_health}")
        
        # Check response time
        if forexvps_metrics.avg_response_time > self.critical_thresholds["forexvps_response_time"]:
            health_status["overall"] = "critical"
            health_status["issues"].append(f"Slow ForexVPS response: {forexvps_metrics.avg_response_time:.3f}s")
        elif forexvps_metrics.avg_response_time > 2.0:
            health_status["warnings"].append(f"Elevated ForexVPS response time: {forexvps_metrics.avg_response_time:.3f}s")
        
        # Check success rate
        if forexvps_metrics.success_rate < 95.0:
            health_status["overall"] = "critical"
            health_status["issues"].append(f"Low ForexVPS success rate: {forexvps_metrics.success_rate}%")
        elif forexvps_metrics.success_rate < 98.0:
            health_status["warnings"].append(f"Reduced ForexVPS success rate: {forexvps_metrics.success_rate}%")
        
        return health_status

class AlertManager:
    """Alert management system"""
    
    def __init__(self):
        self.alert_history = []
        self.max_history = 1000
    
    async def check_and_alert(self, health_status: Dict[str, Any], metric_type: str):
        """Check health status and send alerts if needed"""
        if health_status["overall"] == "critical":
            await self.send_critical_alert(health_status, metric_type)
        elif health_status["overall"] == "warning":
            await self.send_warning_alert(health_status, metric_type)
    
    async def send_critical_alert(self, health_status: Dict[str, Any], metric_type: str):
        """Send critical alert"""
        alert = {
            "level": "critical",
            "type": metric_type,
            "issues": health_status["issues"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        app_logger.critical(f"CRITICAL ALERT - {metric_type}: {', '.join(health_status['issues'])}")
        
        # Store alert
        self.alert_history.append(alert)
        if len(self.alert_history) > self.max_history:
            self.alert_history.pop(0)
        
        # TODO: Implement actual alerting (email, Telegram, etc.)
    
    async def send_warning_alert(self, health_status: Dict[str, Any], metric_type: str):
        """Send warning alert"""
        alert = {
            "level": "warning",
            "type": metric_type,
            "warnings": health_status["warnings"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        app_logger.warning(f"WARNING ALERT - {metric_type}: {', '.join(health_status['warnings'])}")
        
        # Store alert
        self.alert_history.append(alert)
        if len(self.alert_history) > self.max_history:
            self.alert_history.pop(0)

# Global instances
metrics_collector = MetricsCollector()
health_checker = HealthChecker()
alert_manager = AlertManager()

async def start_monitoring(redis_url: str):
    """Start monitoring system"""
    await metrics_collector.initialize(redis_url)
    app_logger.info("🔍 Monitoring system started")

async def collect_all_metrics() -> Dict[str, Any]:
    """Collect all system metrics"""
    try:
        system_metrics = await metrics_collector.collect_system_metrics()
        database_metrics = await metrics_collector.collect_database_metrics()
        forexvps_metrics = await metrics_collector.collect_forexvps_metrics()
        
        all_metrics = {
            "system": system_metrics,
            "database": database_metrics,
            "forexvps": forexvps_metrics
        }
        
        # Store metrics
        await metrics_collector.store_metrics(all_metrics)
        
        # Check health and alert
        system_health = health_checker.evaluate_system_health(system_metrics)
        forexvps_health = health_checker.evaluate_forexvps_health(forexvps_metrics)
        
        await alert_manager.check_and_alert(system_health, "system")
        await alert_manager.check_and_alert(forexvps_health, "forexvps")
        
        return all_metrics
        
    except Exception as e:
        app_logger.error(f"Failed to collect metrics: {e}")
        raise