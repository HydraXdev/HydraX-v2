#!/usr/bin/env python3
"""
🛡️ CITADEL Throttle API
Flask API endpoints for monitoring CITADEL adaptive TCS throttling system
"""

from flask import Flask, jsonify, request
import json
import time
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - CITADEL_API - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Global adaptive throttle reference
adaptive_throttle = None

def initialize_adaptive_throttle():
    """Initialize the global adaptive throttle system"""
    global adaptive_throttle
    
    if adaptive_throttle is None:
        try:
            from citadel_adaptive_throttle import get_adaptive_throttle
            adaptive_throttle = get_adaptive_throttle()
            logger.info("🛡️ CITADEL adaptive throttle initialized for API")
        except Exception as e:
            logger.error(f"❌ Failed to initialize adaptive throttle: {e}")
            adaptive_throttle = None
    
    return adaptive_throttle

@app.route('/citadel/api/threshold_status', methods=['GET'])
def get_threshold_status():
    """Get current CITADEL TCS threshold status"""
    try:
        throttle = initialize_adaptive_throttle()
        
        if not throttle:
            return jsonify({
                "error": "CITADEL adaptive throttle not available",
                "status": "disabled"
            }), 503
        
        # Get comprehensive status
        status = throttle.get_current_status()
        
        # Add API metadata
        api_response = {
            "status": "active",
            "timestamp": time.time(),
            "citadel_throttle": status,
            "api_version": "1.0",
            "endpoint": "/citadel/api/threshold_status"
        }
        
        return jsonify(api_response), 200
        
    except Exception as e:
        logger.error(f"❌ Threshold status endpoint error: {e}")
        return jsonify({
            "error": str(e),
            "status": "error",
            "timestamp": time.time()
        }), 500

@app.route('/citadel/api/threshold_history', methods=['GET'])
def get_threshold_history():
    """Get recent threshold change history from throttle log"""
    try:
        throttle = initialize_adaptive_throttle()
        
        if not throttle:
            return jsonify({
                "error": "CITADEL adaptive throttle not available"
            }), 503
        
        # Get limit from query parameter
        limit = request.args.get('limit', default=20, type=int)
        limit = min(max(limit, 1), 100)  # Clamp between 1 and 100
        
        # Read recent entries from throttle log
        history = []
        try:
            with open(throttle.throttle_log_path, 'r') as f:
                lines = f.readlines()
                
            # Get last N lines and parse them
            recent_lines = lines[-limit:] if len(lines) > limit else lines
            
            for line in recent_lines:
                line = line.strip()
                if 'TCS_CHANGE' in line or 'SIGNAL_RESET' in line or 'PRESSURE_OVERRIDE' in line:
                    # Parse log line (timestamp - level - message)
                    parts = line.split(' - ', 2)
                    if len(parts) >= 3:
                        timestamp_str, level, message = parts
                        history.append({
                            "timestamp": timestamp_str,
                            "level": level,
                            "message": message,
                            "log_entry": line
                        })
        
        except FileNotFoundError:
            history = []
        except Exception as e:
            logger.error(f"❌ Error reading throttle log: {e}")
            history = []
        
        return jsonify({
            "history": history,
            "count": len(history),
            "timestamp": time.time()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Threshold history endpoint error: {e}")
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/citadel/api/force_reset', methods=['POST'])
def force_threshold_reset():
    """Force reset TCS threshold to baseline (emergency override)"""
    try:
        throttle = initialize_adaptive_throttle()
        
        if not throttle:
            return jsonify({
                "error": "CITADEL adaptive throttle not available"
            }), 503
        
        # Parse request data
        data = request.get_json() or {}
        reason = data.get('reason', 'MANUAL_OVERRIDE')
        
        # Force signal completion to reset threshold
        throttle.on_signal_completed(f"FORCE_RESET_{int(time.time())}", time.time())
        
        # Log the manual override
        throttle.throttle_logger.info(f"MANUAL_OVERRIDE - Force reset triggered | Reason: {reason}")
        
        return jsonify({
            "success": True,
            "message": "TCS threshold force reset to baseline",
            "new_threshold": throttle.current_state.current_tcs,
            "reason": reason,
            "timestamp": time.time()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Force reset endpoint error: {e}")
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/citadel/api/signal_completed', methods=['POST'])
def signal_completed_webhook():
    """Webhook endpoint for external systems to report signal completion"""
    try:
        throttle = initialize_adaptive_throttle()
        
        if not throttle:
            return jsonify({
                "error": "CITADEL adaptive throttle not available"
            }), 503
        
        # Parse request data
        data = request.get_json()
        if not data:
            return jsonify({
                "error": "No JSON data provided"
            }), 400
        
        signal_id = data.get('signal_id')
        timestamp = data.get('timestamp', time.time())
        
        if not signal_id:
            return jsonify({
                "error": "signal_id parameter required"
            }), 400
        
        # Process signal completion
        throttle.on_signal_completed(signal_id, timestamp)
        
        return jsonify({
            "success": True,
            "message": "Signal completion processed",
            "signal_id": signal_id,
            "new_threshold": throttle.current_state.current_tcs,
            "timestamp": time.time()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Signal completed webhook error: {e}")
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/citadel/api/config', methods=['GET'])
def get_throttle_config():
    """Get CITADEL throttle configuration"""
    try:
        throttle = initialize_adaptive_throttle()
        
        if not throttle:
            return jsonify({
                "error": "CITADEL adaptive throttle not available"
            }), 503
        
        config_data = {
            "baseline_tcs": throttle.config.baseline,
            "tier_1_tcs": throttle.config.tier_1,
            "tier_2_tcs": throttle.config.tier_2,
            "tier_3_tcs": throttle.config.tier_3,
            "reset_after_minutes": throttle.config.reset_after_minutes,
            "monitoring_interval_seconds": throttle.monitoring_interval,
            "decay_schedule": [
                {
                    "minutes": minutes,
                    "tcs_threshold": tcs,
                    "reason_code": reason
                }
                for minutes, tcs, reason in throttle.decay_schedule
            ]
        }
        
        return jsonify({
            "config": config_data,
            "timestamp": time.time()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Config endpoint error: {e}")
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/citadel/api/health', methods=['GET'])
def health_check():
    """CITADEL throttle system health check"""
    try:
        throttle = initialize_adaptive_throttle()
        
        if throttle:
            status = throttle.get_current_status()
            is_healthy = throttle.monitoring_active
            
            health_data = {
                "healthy": is_healthy,
                "monitoring_active": throttle.monitoring_active,
                "current_tcs": status.get("tcs_threshold"),
                "tier_level": status.get("tier_level"),
                "reason_code": status.get("reason_code"),
                "minutes_since_signal": status.get("minutes_since_signal"),
                "pressure_override_active": status.get("pressure_override_active")
            }
        else:
            is_healthy = False
            health_data = {"error": "Throttle system not available"}
        
        return jsonify({
            "healthy": is_healthy,
            "timestamp": time.time(),
            "system": "citadel_adaptive_throttle",
            "data": health_data
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
            "/citadel/api/threshold_status",
            "/citadel/api/threshold_history",
            "/citadel/api/force_reset",
            "/citadel/api/signal_completed",
            "/citadel/api/config",
            "/citadel/api/health"
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
    """Run the CITADEL throttle API server"""
    print("🛡️ Starting CITADEL Throttle API Server")
    print("Available endpoints:")
    print("  GET  /citadel/api/threshold_status - Current TCS threshold status")
    print("  GET  /citadel/api/threshold_history - Recent threshold changes")
    print("  POST /citadel/api/force_reset - Force reset to baseline")
    print("  POST /citadel/api/signal_completed - Signal completion webhook")
    print("  GET  /citadel/api/config - Throttle configuration")
    print("  GET  /citadel/api/health - System health check")
    
    # Initialize throttle system
    initialize_adaptive_throttle()
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=8003,
        debug=False
    )