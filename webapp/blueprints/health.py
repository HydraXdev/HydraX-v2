"""
Health and monitoring endpoints
"""

from flask import Blueprint, jsonify
import psutil
import logging

logger = logging.getLogger(__name__)

health_bp = Blueprint('health', __name__)

@health_bp.route('/healthz')
def healthz():
    """Kubernetes health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

@health_bp.route('/api/health')
def api_health():
    """Detailed health check"""
    try:
        # Get memory usage
        memory = psutil.virtual_memory()
        
        return jsonify({
            'status': 'healthy',
            'memory': {
                'percent': memory.percent,
                'available': memory.available // 1024 // 1024,  # MB
                'total': memory.total // 1024 // 1024  # MB
            },
            'cpu_percent': psutil.cpu_percent(interval=0.1)
        })
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@health_bp.route('/api/ping', methods=['POST'])
def api_ping():
    """Simple ping endpoint for connection testing"""
    return jsonify({'pong': True}), 200