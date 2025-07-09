#!/usr/bin/env python3
"""
BITTEN Health Check System
Comprehensive health monitoring for all BITTEN services with endpoints
for external monitoring systems.
"""

import asyncio
import json
import logging
import time
import psutil
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
from pathlib import Path
import socket
import subprocess
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, jsonify, request
import redis

from .logging_config import setup_service_logging

class HealthStatus(Enum):
    """Health check status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class HealthCheckResult:
    """Result of a health check"""
    service: str
    status: HealthStatus
    message: str
    timestamp: datetime
    response_time_ms: float
    details: Optional[Dict[str, Any]] = None

@dataclass
class ServiceHealth:
    """Overall service health"""
    service_name: str
    status: HealthStatus
    uptime_seconds: float
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    active_connections: int
    last_error: Optional[str]
    error_count: int
    response_time_ms: float
    timestamp: datetime

class HealthChecker:
    """Base class for health checkers"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = setup_service_logging(f"health-{service_name}")
        self.start_time = time.time()
        self.error_count = 0
        self.last_error = None
    
    async def check_health(self) -> HealthCheckResult:
        """Perform health check - to be implemented by subclasses"""
        raise NotImplementedError
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get system resource metrics"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage_percent': psutil.disk_usage('/').percent,
            'active_connections': len(psutil.net_connections()),
            'uptime_seconds': time.time() - self.start_time
        }

class DatabaseHealthChecker(HealthChecker):
    """Health checker for database connections"""
    
    def __init__(self, service_name: str, db_config: Dict[str, Any]):
        super().__init__(service_name)
        self.db_config = db_config
    
    async def check_health(self) -> HealthCheckResult:
        """Check database connectivity and performance"""
        start_time = time.time()
        
        try:
            if self.db_config.get('type') == 'postgresql':
                await self._check_postgresql()
            elif self.db_config.get('type') == 'sqlite':
                await self._check_sqlite()
            else:
                raise ValueError(f"Unknown database type: {self.db_config.get('type')}")
            
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                service=self.service_name,
                status=HealthStatus.HEALTHY,
                message="Database connection successful",
                timestamp=datetime.now(),
                response_time_ms=response_time,
                details=self._get_system_metrics()
            )
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                service=self.service_name,
                status=HealthStatus.CRITICAL,
                message=f"Database connection failed: {str(e)}",
                timestamp=datetime.now(),
                response_time_ms=response_time,
                details=self._get_system_metrics()
            )
    
    async def _check_postgresql(self):
        """Check PostgreSQL connection"""
        import asyncpg
        
        conn = await asyncpg.connect(
            host=self.db_config.get('host', 'localhost'),
            port=self.db_config.get('port', 5432),
            user=self.db_config.get('user'),
            password=self.db_config.get('password'),
            database=self.db_config.get('database')
        )
        
        # Test query
        result = await conn.fetchval('SELECT 1')
        await conn.close()
        
        if result != 1:
            raise Exception("Test query failed")
    
    async def _check_sqlite(self):
        """Check SQLite connection"""
        db_path = self.db_config.get('path', '/var/log/bitten/bitten.db')
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute('SELECT 1')
            result = cursor.fetchone()
            
            if result[0] != 1:
                raise Exception("Test query failed")

class RedisHealthChecker(HealthChecker):
    """Health checker for Redis connection"""
    
    def __init__(self, service_name: str, redis_config: Dict[str, Any]):
        super().__init__(service_name)
        self.redis_config = redis_config
    
    async def check_health(self) -> HealthCheckResult:
        """Check Redis connectivity and performance"""
        start_time = time.time()
        
        try:
            redis_client = redis.Redis(
                host=self.redis_config.get('host', 'localhost'),
                port=self.redis_config.get('port', 6379),
                db=self.redis_config.get('db', 0),
                decode_responses=True
            )
            
            # Test ping
            redis_client.ping()
            
            # Test set/get
            test_key = f"health_check_{int(time.time())}"
            redis_client.set(test_key, "test_value", ex=10)
            result = redis_client.get(test_key)
            redis_client.delete(test_key)
            
            if result != "test_value":
                raise Exception("Redis set/get test failed")
            
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                service=self.service_name,
                status=HealthStatus.HEALTHY,
                message="Redis connection successful",
                timestamp=datetime.now(),
                response_time_ms=response_time,
                details=self._get_system_metrics()
            )
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                service=self.service_name,
                status=HealthStatus.CRITICAL,
                message=f"Redis connection failed: {str(e)}",
                timestamp=datetime.now(),
                response_time_ms=response_time,
                details=self._get_system_metrics()
            )

class HTTPHealthChecker(HealthChecker):
    """Health checker for HTTP endpoints"""
    
    def __init__(self, service_name: str, endpoint_config: Dict[str, Any]):
        super().__init__(service_name)
        self.endpoint_config = endpoint_config
        self.timeout = endpoint_config.get('timeout', 5)
    
    async def check_health(self) -> HealthCheckResult:
        """Check HTTP endpoint health"""
        start_time = time.time()
        
        try:
            url = self.endpoint_config.get('url')
            method = self.endpoint_config.get('method', 'GET')
            headers = self.endpoint_config.get('headers', {})
            expected_status = self.endpoint_config.get('expected_status', 200)
            
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                timeout=self.timeout
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code != expected_status:
                raise Exception(f"Expected status {expected_status}, got {response.status_code}")
            
            return HealthCheckResult(
                service=self.service_name,
                status=HealthStatus.HEALTHY,
                message=f"HTTP endpoint responding (status: {response.status_code})",
                timestamp=datetime.now(),
                response_time_ms=response_time,
                details={
                    'status_code': response.status_code,
                    'response_size': len(response.content),
                    **self._get_system_metrics()
                }
            )
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                service=self.service_name,
                status=HealthStatus.CRITICAL,
                message=f"HTTP endpoint failed: {str(e)}",
                timestamp=datetime.now(),
                response_time_ms=response_time,
                details=self._get_system_metrics()
            )

class ProcessHealthChecker(HealthChecker):
    """Health checker for system processes"""
    
    def __init__(self, service_name: str, process_config: Dict[str, Any]):
        super().__init__(service_name)
        self.process_config = process_config
    
    async def check_health(self) -> HealthCheckResult:
        """Check process health"""
        start_time = time.time()
        
        try:
            process_name = self.process_config.get('name')
            pid_file = self.process_config.get('pid_file')
            
            if pid_file and os.path.exists(pid_file):
                # Check via PID file
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                if not psutil.pid_exists(pid):
                    raise Exception(f"Process with PID {pid} not found")
                
                process = psutil.Process(pid)
                cpu_percent = process.cpu_percent(interval=1)
                memory_percent = process.memory_percent()
                
            else:
                # Check via process name
                processes = [p for p in psutil.process_iter(['pid', 'name']) 
                           if p.info['name'] == process_name]
                
                if not processes:
                    raise Exception(f"Process '{process_name}' not found")
                
                process = processes[0]
                cpu_percent = process.cpu_percent(interval=1)
                memory_percent = process.memory_percent()
            
            response_time = (time.time() - start_time) * 1000
            
            # Check if resource usage is concerning
            status = HealthStatus.HEALTHY
            if cpu_percent > 80 or memory_percent > 80:
                status = HealthStatus.WARNING
            
            return HealthCheckResult(
                service=self.service_name,
                status=status,
                message=f"Process running (CPU: {cpu_percent:.1f}%, Memory: {memory_percent:.1f}%)",
                timestamp=datetime.now(),
                response_time_ms=response_time,
                details={
                    'pid': process.pid,
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory_percent,
                    **self._get_system_metrics()
                }
            )
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                service=self.service_name,
                status=HealthStatus.CRITICAL,
                message=f"Process check failed: {str(e)}",
                timestamp=datetime.now(),
                response_time_ms=response_time,
                details=self._get_system_metrics()
            )

class MT5HealthChecker(HealthChecker):
    """Health checker for MT5 farm connection"""
    
    def __init__(self, service_name: str, mt5_config: Dict[str, Any]):
        super().__init__(service_name)
        self.mt5_config = mt5_config
    
    async def check_health(self) -> HealthCheckResult:
        """Check MT5 farm health"""
        start_time = time.time()
        
        try:
            farm_url = self.mt5_config.get('url', 'http://129.212.185.102:8001')
            
            # Check basic connectivity
            response = requests.get(f"{farm_url}/status", timeout=10)
            
            if response.status_code != 200:
                raise Exception(f"MT5 farm returned status {response.status_code}")
            
            # Check account connectivity
            accounts_response = requests.get(f"{farm_url}/accounts", timeout=10)
            
            if accounts_response.status_code != 200:
                raise Exception(f"MT5 accounts check failed: {accounts_response.status_code}")
            
            accounts_data = accounts_response.json()
            active_accounts = accounts_data.get('active_accounts', 0)
            
            response_time = (time.time() - start_time) * 1000
            
            status = HealthStatus.HEALTHY
            if active_accounts < 3:
                status = HealthStatus.WARNING
            
            return HealthCheckResult(
                service=self.service_name,
                status=status,
                message=f"MT5 farm operational ({active_accounts} active accounts)",
                timestamp=datetime.now(),
                response_time_ms=response_time,
                details={
                    'active_accounts': active_accounts,
                    'farm_url': farm_url,
                    **self._get_system_metrics()
                }
            )
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                service=self.service_name,
                status=HealthStatus.CRITICAL,
                message=f"MT5 farm check failed: {str(e)}",
                timestamp=datetime.now(),
                response_time_ms=response_time,
                details=self._get_system_metrics()
            )

class HealthCheckManager:
    """Manages all health checks"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = setup_service_logging("health-check-manager")
        self.checkers: Dict[str, HealthChecker] = {}
        self.results: Dict[str, HealthCheckResult] = {}
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Initialize checkers
        self._initialize_checkers()
    
    def _initialize_checkers(self):
        """Initialize all health checkers"""
        # Database checkers
        for db_name, db_config in self.config.get('databases', {}).items():
            self.checkers[f"database-{db_name}"] = DatabaseHealthChecker(
                f"database-{db_name}", db_config
            )
        
        # Redis checkers
        redis_config = self.config.get('redis')
        if redis_config:
            self.checkers['redis'] = RedisHealthChecker('redis', redis_config)
        
        # HTTP endpoint checkers
        for endpoint_name, endpoint_config in self.config.get('endpoints', {}).items():
            self.checkers[f"endpoint-{endpoint_name}"] = HTTPHealthChecker(
                f"endpoint-{endpoint_name}", endpoint_config
            )
        
        # Process checkers
        for process_name, process_config in self.config.get('processes', {}).items():
            self.checkers[f"process-{process_name}"] = ProcessHealthChecker(
                f"process-{process_name}", process_config
            )
        
        # MT5 farm checker
        mt5_config = self.config.get('mt5_farm')
        if mt5_config:
            self.checkers['mt5-farm'] = MT5HealthChecker('mt5-farm', mt5_config)
    
    async def run_health_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all health checks"""
        results = {}
        
        # Run checks concurrently
        tasks = []
        for name, checker in self.checkers.items():
            task = asyncio.create_task(checker.check_health())
            tasks.append((name, task))
        
        # Wait for all checks to complete
        for name, task in tasks:
            try:
                result = await task
                results[name] = result
            except Exception as e:
                self.logger.error(f"Health check {name} failed: {e}")
                results[name] = HealthCheckResult(
                    service=name,
                    status=HealthStatus.CRITICAL,
                    message=f"Health check failed: {str(e)}",
                    timestamp=datetime.now(),
                    response_time_ms=0
                )
        
        self.results = results
        return results
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        if not self.results:
            return {
                'status': 'unknown',
                'message': 'No health checks run yet',
                'timestamp': datetime.now().isoformat()
            }
        
        # Determine overall status
        statuses = [result.status for result in self.results.values()]
        
        if any(status == HealthStatus.CRITICAL for status in statuses):
            overall_status = HealthStatus.CRITICAL
        elif any(status == HealthStatus.WARNING for status in statuses):
            overall_status = HealthStatus.WARNING
        else:
            overall_status = HealthStatus.HEALTHY
        
        # Calculate service counts
        healthy_count = sum(1 for s in statuses if s == HealthStatus.HEALTHY)
        warning_count = sum(1 for s in statuses if s == HealthStatus.WARNING)
        critical_count = sum(1 for s in statuses if s == HealthStatus.CRITICAL)
        
        return {
            'status': overall_status.value,
            'services_total': len(self.results),
            'services_healthy': healthy_count,
            'services_warning': warning_count,
            'services_critical': critical_count,
            'timestamp': datetime.now().isoformat(),
            'details': {name: asdict(result) for name, result in self.results.items()}
        }
    
    def start_monitoring(self):
        """Start continuous health monitoring"""
        self.running = True
        self.executor.submit(self._monitoring_loop)
        self.logger.info("Health monitoring started")
    
    def stop_monitoring(self):
        """Stop continuous health monitoring"""
        self.running = False
        self.executor.shutdown(wait=True)
        self.logger.info("Health monitoring stopped")
    
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.running:
            try:
                # Run health checks
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                results = loop.run_until_complete(self.run_health_checks())
                loop.close()
                
                # Log critical issues
                for name, result in results.items():
                    if result.status == HealthStatus.CRITICAL:
                        self.logger.error(f"Critical health issue: {name} - {result.message}")
                    elif result.status == HealthStatus.WARNING:
                        self.logger.warning(f"Health warning: {name} - {result.message}")
                
                # Sleep before next check
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in health monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute before retry

class HealthCheckAPI:
    """Flask API for health check endpoints"""
    
    def __init__(self, health_manager: HealthCheckManager, port: int = 8080):
        self.health_manager = health_manager
        self.port = port
        self.app = Flask(__name__)
        self.logger = setup_service_logging("health-check-api")
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Basic health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'service': 'bitten-health-api'
            })
        
        @self.app.route('/health/detailed', methods=['GET'])
        def detailed_health():
            """Detailed health check endpoint"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                results = loop.run_until_complete(self.health_manager.run_health_checks())
                loop.close()
                
                overall_health = self.health_manager.get_overall_health()
                return jsonify(overall_health)
                
            except Exception as e:
                self.logger.error(f"Error in detailed health check: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/health/service/<service_name>', methods=['GET'])
        def service_health(service_name):
            """Individual service health check"""
            if service_name not in self.health_manager.results:
                return jsonify({
                    'error': f'Service {service_name} not found'
                }), 404
            
            result = self.health_manager.results[service_name]
            return jsonify(asdict(result))
        
        @self.app.route('/health/metrics', methods=['GET'])
        def health_metrics():
            """Prometheus-style metrics endpoint"""
            metrics = []
            
            for name, result in self.health_manager.results.items():
                status_value = {
                    HealthStatus.HEALTHY: 1,
                    HealthStatus.WARNING: 0.5,
                    HealthStatus.CRITICAL: 0,
                    HealthStatus.UNKNOWN: -1
                }.get(result.status, -1)
                
                metrics.append(f'bitten_service_health{{service="{name}"}} {status_value}')
                metrics.append(f'bitten_service_response_time{{service="{name}"}} {result.response_time_ms}')
            
            return '\n'.join(metrics), 200, {'Content-Type': 'text/plain'}
        
        @self.app.route('/health/ready', methods=['GET'])
        def readiness_check():
            """Kubernetes readiness probe endpoint"""
            overall_health = self.health_manager.get_overall_health()
            
            if overall_health['status'] == 'critical':
                return jsonify({
                    'status': 'not_ready',
                    'reason': 'Critical services failing'
                }), 503
            
            return jsonify({
                'status': 'ready',
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/health/live', methods=['GET'])
        def liveness_check():
            """Kubernetes liveness probe endpoint"""
            return jsonify({
                'status': 'alive',
                'timestamp': datetime.now().isoformat()
            })
    
    def run(self):
        """Run the health check API"""
        self.logger.info(f"Starting health check API on port {self.port}")
        self.app.run(host='0.0.0.0', port=self.port, debug=False)

def create_health_check_system(config: Dict[str, Any]) -> Tuple[HealthCheckManager, HealthCheckAPI]:
    """Create complete health check system"""
    health_manager = HealthCheckManager(config)
    health_api = HealthCheckAPI(health_manager, config.get('api_port', 8080))
    
    return health_manager, health_api

# Example configuration
def get_default_config() -> Dict[str, Any]:
    """Get default health check configuration"""
    return {
        'databases': {
            'main': {
                'type': 'postgresql',
                'host': 'localhost',
                'port': 5432,
                'user': 'bitten_user',
                'password': 'password',
                'database': 'bitten_db'
            },
            'performance': {
                'type': 'sqlite',
                'path': '/var/log/bitten/performance.db'
            }
        },
        'redis': {
            'host': 'localhost',
            'port': 6379,
            'db': 0
        },
        'endpoints': {
            'webapp': {
                'url': 'http://localhost:9001/health',
                'method': 'GET',
                'timeout': 5,
                'expected_status': 200
            },
            'telegram-webhook': {
                'url': 'http://localhost:9001/status',
                'method': 'GET',
                'timeout': 5,
                'expected_status': 200
            }
        },
        'processes': {
            'bitten-core': {
                'name': 'python',
                'pid_file': '/var/run/bitten/bitten-core.pid'
            }
        },
        'mt5_farm': {
            'url': 'http://129.212.185.102:8001'
        },
        'api_port': 8080
    }

# Example usage
if __name__ == "__main__":
    # Create health check system
    config = get_default_config()
    health_manager, health_api = create_health_check_system(config)
    
    # Start monitoring
    health_manager.start_monitoring()
    
    # Run API (in production, use a proper WSGI server)
    try:
        health_api.run()
    except KeyboardInterrupt:
        print("Shutting down...")
        health_manager.stop_monitoring()