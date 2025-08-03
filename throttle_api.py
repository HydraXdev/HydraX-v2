#!/usr/bin/env python3
"""
🎛️ Throttle Controller API
Flask API endpoints for monitoring and controlling the VENOM throttle system
"""

from flask import Flask, jsonify, request
import json
import time
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - THROTTLE_API - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Global throttle controller reference
throttle_controller = None

def initialize_throttle_controller():
    """Initialize the global throttle controller"""
    global throttle_controller
    
    if throttle_controller is None:
        try:
            from throttle_controller import get_throttle_controller
            throttle_controller = get_throttle_controller()
            logger.info("🎛️ Throttle controller initialized for API")
        except Exception as e:
            logger.error(f"❌ Failed to initialize throttle controller: {e}")
            throttle_controller = None
    
    return throttle_controller

@app.route('/throttle/status', methods=['GET'])
def get_throttle_status():
    """Get current throttle controller status"""
    try:
        controller = initialize_throttle_controller()
        
        if not controller:
            return jsonify({
                "error": "Throttle controller not available",
                "status": "disabled"
            }), 503
        
        # Get comprehensive status report
        status = controller.get_status_report()
        
        # Add API metadata
        api_response = {
            "status": "active",
            "timestamp": time.time(),
            "controller": status,
            "api_version": "1.0"
        }
        
        return jsonify(api_response), 200
        
    except Exception as e:
        logger.error(f"❌ Status endpoint error: {e}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@app.route('/throttle/override', methods=['POST'])
def commander_override():
    """Commander override endpoint"""
    try:
        controller = initialize_throttle_controller()
        
        if not controller:
            return jsonify({
                "error": "Throttle controller not available"
            }), 503
        
        # Parse request data
        data = request.get_json()
        if not data:
            return jsonify({
                "error": "No JSON data provided"
            }), 400
        
        new_state = data.get('state')
        duration_minutes = data.get('duration_minutes')
        
        if not new_state:
            return jsonify({
                "error": "State parameter required"
            }), 400
        
        # Valid states
        valid_states = ['cruise', 'nitrous', 'throttle_hold', 'lockdown']
        if new_state not in valid_states:
            return jsonify({
                "error": f"Invalid state. Must be one of: {valid_states}"
            }), 400
        
        # Apply override
        controller.commander_override(new_state, duration_minutes)
        
        return jsonify({
            "success": True,
            "message": f"Override applied: {new_state}",
            "duration_minutes": duration_minutes,
            "timestamp": time.time()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Override endpoint error: {e}")
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/throttle/thresholds', methods=['GET'])
def get_current_thresholds():
    """Get current TCS and ML thresholds"""
    try:
        controller = initialize_throttle_controller()
        
        if not controller:
            return jsonify({
                "error": "Throttle controller not available"
            }), 503
        
        tcs_threshold, ml_threshold = controller.get_current_thresholds()
        
        return jsonify({
            "tcs_threshold": tcs_threshold,
            "ml_threshold": ml_threshold,
            "timestamp": time.time()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Thresholds endpoint error: {e}")
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/throttle/signals/recent', methods=['GET'])
def get_recent_signals():
    """Get recent signal activity"""
    try:
        controller = initialize_throttle_controller()
        
        if not controller:
            return jsonify({
                "error": "Throttle controller not available"
            }), 503
        
        # Get limit from query parameter
        limit = request.args.get('limit', default=10, type=int)
        limit = min(max(limit, 1), 100)  # Clamp between 1 and 100
        
        # Get recent signals (last N from deque)
        recent_signals = list(controller.recent_signals)[-limit:]
        
        # Convert to serializable format
        signals_data = []
        for signal in recent_signals:
            signals_data.append({
                "signal_id": signal.signal_id,
                "timestamp": signal.timestamp,
                "symbol": signal.symbol,
                "direction": signal.direction,
                "tcs_score": signal.tcs_score,
                "ml_score": signal.ml_score,
                "result": signal.result,
                "pips": signal.pips
            })
        
        return jsonify({
            "signals": signals_data,
            "count": len(signals_data),
            "timestamp": time.time()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Recent signals endpoint error: {e}")
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/throttle/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    try:
        controller = initialize_throttle_controller()
        
        if controller:
            # Get basic status
            status = controller.get_status_report()
            is_healthy = True
        else:
            status = {"error": "Controller not available"}
            is_healthy = False
        
        return jsonify({
            "healthy": is_healthy,
            "timestamp": time.time(),
            "status": status.get("governor_state", "unknown") if is_healthy else "error"
        }), 200 if is_healthy else 503
        
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        return jsonify({
            "healthy": False,
            "error": str(e),
            "timestamp": time.time()
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": [
            "/throttle/status",
            "/throttle/override",
            "/throttle/thresholds", 
            "/throttle/signals/recent",
            "/throttle/health"
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        "error": "Internal server error",
        "timestamp": time.time()
    }), 500

if __name__ == "__main__":
    """Run the throttle API server"""
    print("🎛️ Starting Throttle Controller API")
    print("Available endpoints:")
    print("  GET  /throttle/status - Get throttle status")
    print("  POST /throttle/override - Commander override")
    print("  GET  /throttle/thresholds - Current thresholds")
    print("  GET  /throttle/signals/recent - Recent signals")
    print("  GET  /throttle/health - Health check")
    
    # Initialize controller
    initialize_throttle_controller()
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=8002,
        debug=False
    )