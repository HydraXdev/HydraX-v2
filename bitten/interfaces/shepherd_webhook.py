#!/usr/bin/env python3
"""
Shepherd Webhook API Interface for HydraX-v2
RESTful API endpoints for validating logic, tracing connections, testing changes, and monitoring system health.
"""

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from functools import wraps
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import os
import sys
import hashlib
import hmac

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
SECRET_KEY = os.environ.get('SHEPHERD_SECRET_KEY', 'development-secret-key')
API_VERSION = 'v1'
MAX_REQUEST_SIZE = 1024 * 1024  # 1MB

class ShepherdWebhook:
    """Webhook API handler for the Shepherd system."""
    
    def __init__(self):
        self.state_file = "/root/HydraX-v2/bitten/data/shepherd/state.json"
        self.metrics_file = "/root/HydraX-v2/bitten/data/shepherd/metrics.json"
        self._ensure_directories()
        self._load_system_state()
    
    def _ensure_directories(self):
        """Ensure required directories exist."""
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
    
    def _load_system_state(self):
        """Load current system state."""
        try:
            with open(self.state_file, 'r') as f:
                self.system_state = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.system_state = {
                "status": "active",
                "version": "1.0.0",
                "modules": {},
                "last_updated": datetime.now().isoformat()
            }
    
    def validate_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate trading logic or system configuration.
        
        Args:
            data: Logic configuration to validate
            
        Returns:
            Validation results
        """
        validation_results = {
            "timestamp": datetime.now().isoformat(),
            "valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        # Validate required fields
        required_fields = ['module', 'logic_type', 'configuration']
        for field in required_fields:
            if field not in data:
                validation_results['valid'] = False
                validation_results['errors'].append(f"Missing required field: {field}")
        
        if not validation_results['valid']:
            return validation_results
        
        # Mock validation logic - replace with actual implementation
        module = data.get('module')
        logic_type = data.get('logic_type')
        config = data.get('configuration', {})
        
        # Example validations
        if logic_type == 'risk_management':
            if config.get('max_risk', 0) > 0.1:
                validation_results['warnings'].append("Risk level above 10% is considered high")
            if 'stop_loss' not in config:
                validation_results['errors'].append("Stop loss configuration is required")
                validation_results['valid'] = False
        
        elif logic_type == 'signal_generation':
            if config.get('threshold', 0) < 0.5:
                validation_results['warnings'].append("Signal threshold below 0.5 may generate many false positives")
            validation_results['suggestions'].append("Consider implementing confirmation signals")
        
        # Add performance impact estimate
        validation_results['performance_impact'] = {
            "cpu_usage": "Low",
            "memory_usage": "Medium",
            "latency_impact": "+1-2ms"
        }
        
        return validation_results
    
    def get_module_trace(self, module: str) -> Dict[str, Any]:
        """
        Get connection trace for a specific module.
        
        Args:
            module: Module name to trace
            
        Returns:
            Module connection information
        """
        # Mock implementation - replace with actual logic
        trace_data = {
            "module": module,
            "timestamp": datetime.now().isoformat(),
            "exists": True,
            "connections": {
                "inbound": [
                    {
                        "source": "market_data_feed",
                        "protocol": "websocket",
                        "frequency": "realtime",
                        "data_type": "price_ticks"
                    },
                    {
                        "source": "risk_controller",
                        "protocol": "internal",
                        "frequency": "on_demand",
                        "data_type": "risk_limits"
                    }
                ],
                "outbound": [
                    {
                        "destination": "signal_processor",
                        "protocol": "internal",
                        "frequency": "event_driven",
                        "data_type": "trading_signals"
                    },
                    {
                        "destination": "monitoring_system",
                        "protocol": "http",
                        "frequency": "periodic",
                        "data_type": "metrics"
                    }
                ]
            },
            "dependencies": {
                "required": ["database", "config_manager"],
                "optional": ["cache_service", "notification_service"]
            },
            "metrics": {
                "uptime": "99.8%",
                "avg_latency": "12ms",
                "error_rate": "0.02%",
                "throughput": "1250 req/min"
            }
        }
        
        return trace_data
    
    def simulate_changes(self, simulation_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate the impact of proposed changes.
        
        Args:
            simulation_request: Simulation parameters
            
        Returns:
            Simulation results
        """
        # Extract simulation parameters
        change_type = simulation_request.get('change_type', 'configuration')
        changes = simulation_request.get('changes', {})
        duration = simulation_request.get('duration', '1h')
        
        # Mock simulation - replace with actual implementation
        simulation_results = {
            "simulation_id": hashlib.md5(
                json.dumps(simulation_request, sort_keys=True).encode()
            ).hexdigest()[:8],
            "timestamp": datetime.now().isoformat(),
            "parameters": {
                "change_type": change_type,
                "changes": changes,
                "duration": duration
            },
            "results": {
                "system_impact": {
                    "affected_modules": self._get_affected_modules(changes),
                    "downtime_required": False,
                    "rollback_possible": True
                },
                "performance_projection": {
                    "latency_change": "+5%",
                    "throughput_change": "-2%",
                    "resource_usage_change": {
                        "cpu": "+10%",
                        "memory": "+50MB",
                        "network": "No change"
                    }
                },
                "risk_analysis": {
                    "risk_level": "medium",
                    "main_risks": [
                        "Potential signal delay during transition",
                        "Configuration sync issues across modules"
                    ],
                    "mitigation_strategies": [
                        "Implement gradual rollout",
                        "Keep previous configuration for quick rollback"
                    ]
                }
            },
            "recommendations": [
                "Test in staging environment first",
                "Monitor key metrics closely during rollout",
                "Have support team on standby"
            ]
        }
        
        return simulation_results
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        Get current system health status.
        
        Returns:
            System health information
        """
        # Mock health check - replace with actual implementation
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "version": API_VERSION,
            "uptime": self._calculate_uptime(),
            "components": {
                "api_server": {
                    "status": "healthy",
                    "latency": "5ms",
                    "error_rate": "0.01%"
                },
                "database": {
                    "status": "healthy",
                    "connections": 45,
                    "query_time": "2ms"
                },
                "message_queue": {
                    "status": "healthy",
                    "queue_depth": 123,
                    "processing_rate": "1000/min"
                },
                "cache": {
                    "status": "healthy",
                    "hit_rate": "92%",
                    "memory_usage": "234MB"
                }
            },
            "metrics": {
                "requests_per_minute": 850,
                "active_connections": 234,
                "cpu_usage": "35%",
                "memory_usage": "2.1GB",
                "disk_usage": "45%"
            },
            "alerts": [],
            "last_incident": {
                "timestamp": "2025-07-10T15:30:00Z",
                "severity": "minor",
                "description": "Temporary database slowdown",
                "resolution_time": "5 minutes"
            }
        }
        
        # Check for any unhealthy components
        unhealthy_components = [
            name for name, comp in health_status["components"].items()
            if comp["status"] != "healthy"
        ]
        
        if unhealthy_components:
            health_status["overall_status"] = "degraded"
            health_status["alerts"].append({
                "level": "warning",
                "message": f"Components unhealthy: {', '.join(unhealthy_components)}"
            })
        
        return health_status
    
    def _get_affected_modules(self, changes: Dict[str, Any]) -> List[Dict[str, str]]:
        """Determine which modules would be affected by changes."""
        # Mock implementation
        affected = []
        
        if 'risk_limits' in changes:
            affected.append({
                "module": "risk_controller",
                "impact": "high",
                "reason": "Core risk parameters modified"
            })
            affected.append({
                "module": "position_manager",
                "impact": "medium",
                "reason": "Position sizing calculations affected"
            })
        
        if 'signal_threshold' in changes:
            affected.append({
                "module": "signal_processor",
                "impact": "high",
                "reason": "Signal generation logic modified"
            })
        
        return affected
    
    def _calculate_uptime(self) -> str:
        """Calculate system uptime."""
        # Mock implementation
        return "15d 7h 23m"

# Initialize webhook handler
webhook_handler = ShepherdWebhook()

def require_auth(f):
    """Decorator to require authentication for endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid authorization header"}), 401
        
        # In production, validate the token properly
        # For now, just check if it exists
        token = auth_header.split(' ')[1]
        if not token:
            return jsonify({"error": "Invalid token"}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

def validate_request_size():
    """Validate request size to prevent abuse."""
    if request.content_length and request.content_length > MAX_REQUEST_SIZE:
        return jsonify({"error": "Request too large"}), 413
    return None

# API Routes

@app.route('/api/v1/validate', methods=['POST'])
@require_auth
def validate_endpoint():
    """POST /validate - Validate logic configuration."""
    size_error = validate_request_size()
    if size_error:
        return size_error
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        result = webhook_handler.validate_logic(data)
        return jsonify(result), 200 if result['valid'] else 400
        
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/v1/trace/<module>', methods=['GET'])
@require_auth
def trace_endpoint(module: str):
    """GET /trace/:module - Get module connections."""
    try:
        result = webhook_handler.get_module_trace(module)
        
        if not result['exists']:
            return jsonify({"error": f"Module '{module}' not found"}), 404
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Trace error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/v1/simulate', methods=['POST'])
@require_auth
def simulate_endpoint():
    """POST /simulate - Test changes."""
    size_error = validate_request_size()
    if size_error:
        return size_error
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No simulation parameters provided"}), 400
        
        result = webhook_handler.simulate_changes(data)
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Simulation error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/v1/status', methods=['GET'])
def status_endpoint():
    """GET /status - System health (no auth required for health checks)."""
    try:
        result = webhook_handler.get_system_health()
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return jsonify({
            "overall_status": "error",
            "error": "Unable to determine system health"
        }), 500

@app.route('/api/v1/webhook', methods=['POST'])
def webhook_receiver():
    """POST /webhook - Receive external webhooks."""
    try:
        # Verify webhook signature if provided
        signature = request.headers.get('X-Webhook-Signature')
        if signature:
            expected_signature = hmac.new(
                SECRET_KEY.encode(),
                request.data,
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return jsonify({"error": "Invalid signature"}), 401
        
        data = request.get_json()
        logger.info(f"Webhook received: {data.get('event_type', 'unknown')}")
        
        # Process webhook based on event type
        # This is a placeholder for actual webhook processing
        
        return jsonify({"status": "received"}), 200
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return jsonify({"error": "Webhook processing failed"}), 500

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API information."""
    return jsonify({
        "service": "Shepherd Webhook API",
        "version": API_VERSION,
        "endpoints": {
            "POST /api/v1/validate": "Validate logic configuration",
            "GET /api/v1/trace/:module": "Get module connections",
            "POST /api/v1/simulate": "Test changes",
            "GET /api/v1/status": "System health check",
            "POST /api/v1/webhook": "Receive external webhooks"
        },
        "documentation": "https://github.com/HydraX-v2/shepherd-api-docs",
        "health": "/api/v1/status"
    }), 200

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Development server
    print("Starting Shepherd Webhook API...")
    print(f"API Version: {API_VERSION}")
    print("Available endpoints:")
    print("  POST /api/v1/validate     - Validate logic")
    print("  GET  /api/v1/trace/:module - Get connections")
    print("  POST /api/v1/simulate     - Test changes")
    print("  GET  /api/v1/status       - System health")
    print("\nAuthentication: Bearer token required (except /status)")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )