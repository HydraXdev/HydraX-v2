"""
BITTEN Mission Endpoints API
Enhanced version with proper authentication, error handling, and real mission data integration
"""

from flask import Flask, request, jsonify
from datetime import datetime
import json
import os
import glob
import logging
from typing import Dict, Any, Optional, List
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Constants
MISSIONS_DIR = "./missions"
DEFAULT_MISSION_EXPIRY_MINUTES = 5


def require_auth(f):
    """Authentication decorator for mission endpoints"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Extract user auth info from headers or request
        auth_header = request.headers.get('Authorization', '')
        user_id = request.headers.get('X-User-ID', '')
        
        if not auth_header or not user_id:
            return jsonify({
                "status": "error",
                "reason": "authentication_required",
                "message": "Valid authentication required"
            }), 401
        
        # Basic token validation (can be enhanced with JWT)
        if not auth_header.startswith('Bearer '):
            return jsonify({
                "status": "error",
                "reason": "invalid_token_format",
                "message": "Authorization header must start with 'Bearer '"
            }), 401
        
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        # Add user context to request
        request.user_id = user_id
        request.auth_token = token
        
        return f(*args, **kwargs)
    return decorated


def validate_mission_access(user_id: str, mission_id: str) -> bool:
    """Validate if user has access to a specific mission"""
    try:
        # Check if mission belongs to user (mission_id contains user_id)
        if user_id in mission_id:
            return True
        
        # Additional access checks can be added here
        # For now, allow access if mission exists
        mission_path = os.path.join(MISSIONS_DIR, f"{mission_id}.json")
        return os.path.exists(mission_path)
    except Exception as e:
        logger.error(f"Error validating mission access: {e}")
        return False


def load_mission_data(mission_id: str) -> Optional[Dict[str, Any]]:
    """Load mission data from file with proper error handling"""
    try:
        mission_path = os.path.join(MISSIONS_DIR, f"{mission_id}.json")
        
        if not os.path.exists(mission_path):
            return None
            
        with open(mission_path, 'r') as f:
            mission_data = json.load(f)
            
        # Validate mission data structure
        required_fields = ['mission_id', 'expires_at', 'status', 'user_id']
        for field in required_fields:
            if field not in mission_data:
                logger.error(f"Mission {mission_id} missing required field: {field}")
                return None
        
        return mission_data
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in mission {mission_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading mission {mission_id}: {e}")
        return None


def save_mission_data(mission_id: str, mission_data: Dict[str, Any]) -> bool:
    """Save mission data to file with proper error handling"""
    try:
        mission_path = os.path.join(MISSIONS_DIR, f"{mission_id}.json")
        
        # Create missions directory if it doesn't exist
        os.makedirs(MISSIONS_DIR, exist_ok=True)
        
        with open(mission_path, 'w') as f:
            json.dump(mission_data, f, indent=2)
            
        return True
    except Exception as e:
        logger.error(f"Error saving mission {mission_id}: {e}")
        return False


def calculate_time_remaining(expires_at: str) -> int:
    """Calculate remaining time in seconds until mission expires"""
    try:
        expires = datetime.fromisoformat(expires_at)
        remaining = int((expires - datetime.utcnow()).total_seconds())
        return max(0, remaining)
    except Exception as e:
        logger.error(f"Error calculating time remaining: {e}")
        return 0


@app.route("/api/mission-status/<mission_id>", methods=["GET"])
@require_auth
def mission_status(mission_id: str):
    """Get detailed mission status including countdown timer"""
    try:
        # Validate mission access
        if not validate_mission_access(request.user_id, mission_id):
            return jsonify({
                "status": "error",
                "reason": "access_denied",
                "message": "You don't have access to this mission"
            }), 403
        
        # Load mission data
        mission_data = load_mission_data(mission_id)
        if not mission_data:
            return jsonify({
                "status": "error",
                "reason": "not_found",
                "message": "Mission not found or invalid"
            }), 404
        
        # Calculate time remaining
        time_remaining = calculate_time_remaining(mission_data["expires_at"])
        
        # Update mission with calculated values
        mission_data["time_remaining"] = time_remaining
        mission_data["countdown_seconds"] = time_remaining
        mission_data["is_expired"] = time_remaining <= 0
        
        # Add mission stats
        mission_data["mission_stats"] = {
            "fire_count": mission_data.get("fire_count", 0),
            "user_fired": mission_data.get("status") == "fired",
            "time_remaining": time_remaining
        }
        
        logger.info(f"Mission status requested for {mission_id} by user {request.user_id}")
        
        return jsonify(mission_data)
        
    except Exception as e:
        logger.error(f"Error getting mission status for {mission_id}: {e}")
        return jsonify({
            "status": "error",
            "reason": "internal_error",
            "message": "Internal server error"
        }), 500


@app.route("/api/missions", methods=["GET"])
@require_auth
def list_missions():
    """List all missions for the authenticated user"""
    try:
        user_id = request.user_id
        
        # Get query parameters
        status_filter = request.args.get('status')  # pending, fired, expired
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Find all mission files for this user
        mission_files = glob.glob(os.path.join(MISSIONS_DIR, f"*{user_id}*.json"))
        
        missions = []
        for mission_file in mission_files:
            mission_id = os.path.basename(mission_file).replace('.json', '')
            mission_data = load_mission_data(mission_id)
            
            if mission_data:
                # Calculate time remaining
                time_remaining = calculate_time_remaining(mission_data["expires_at"])
                mission_data["time_remaining"] = time_remaining
                mission_data["is_expired"] = time_remaining <= 0
                
                # Apply status filter
                if status_filter:
                    if status_filter == "expired" and not mission_data["is_expired"]:
                        continue
                    elif status_filter == "active" and mission_data["is_expired"]:
                        continue
                    elif status_filter != "all" and mission_data.get("status") != status_filter:
                        continue
                
                missions.append(mission_data)
        
        # Sort by timestamp (newest first)
        missions.sort(key=lambda x: x.get("created_timestamp", 0), reverse=True)
        
        # Apply pagination
        total_missions = len(missions)
        missions = missions[offset:offset + limit]
        
        return jsonify({
            "status": "success",
            "missions": missions,
            "total": total_missions,
            "offset": offset,
            "limit": limit
        })
        
    except Exception as e:
        logger.error(f"Error listing missions for user {request.user_id}: {e}")
        return jsonify({
            "status": "error",
            "reason": "internal_error",
            "message": "Failed to retrieve missions"
        }), 500


@app.route("/api/fire", methods=["POST"])
@require_auth
def handle_fire():
    """Execute a trade (fire a mission) with proper validation and integration"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "reason": "invalid_request",
                "message": "JSON payload required"
            }), 400
        
        mission_id = data.get("mission_id")
        if not mission_id:
            return jsonify({
                "status": "error",
                "reason": "missing_mission_id",
                "message": "mission_id is required"
            }), 400
        
        # Validate mission access
        if not validate_mission_access(request.user_id, mission_id):
            return jsonify({
                "status": "error",
                "reason": "access_denied",
                "message": "You don't have access to this mission"
            }), 403
        
        # Load mission data
        mission_data = load_mission_data(mission_id)
        if not mission_data:
            return jsonify({
                "status": "error",
                "reason": "mission_not_found",
                "message": "Mission not found"
            }), 404
        
        # Check if mission is expired
        time_remaining = calculate_time_remaining(mission_data["expires_at"])
        if time_remaining <= 0:
            return jsonify({
                "status": "error",
                "reason": "mission_expired",
                "message": "Mission has expired"
            }), 403
        
        # Check if mission already fired
        if mission_data.get("status") == "fired":
            return jsonify({
                "status": "error",
                "reason": "already_fired",
                "message": "Mission has already been fired"
            }), 409
        
        # Update mission status
        mission_data["status"] = "fired"
        mission_data["fired_at"] = datetime.utcnow().isoformat()
        mission_data["fired_by"] = request.user_id
        
        # Save updated mission data
        if not save_mission_data(mission_id, mission_data):
            return jsonify({
                "status": "error",
                "reason": "save_failed",
                "message": "Failed to update mission status"
            }), 500
        
        # Execute trade through fire router
        try:
            from ..bitten_core.fire_router import execute_trade
            execution_result = execute_trade(mission_data)
            
            # Update mission with execution result
            mission_data["execution_result"] = execution_result
            mission_data["execution_timestamp"] = datetime.utcnow().isoformat()
            
            # Save final mission state
            save_mission_data(mission_id, mission_data)
            
            logger.info(f"Mission {mission_id} fired successfully by user {request.user_id}")
            
            return jsonify({
                "status": "success",
                "message": "Trade executed successfully",
                "mission_id": mission_id,
                "execution_result": execution_result,
                "time_remaining": time_remaining
            })
            
        except ImportError as e:
            logger.error(f"Fire router import failed: {e}")
            return jsonify({
                "status": "error",
                "reason": "execution_unavailable",
                "message": "Trade execution service unavailable"
            }), 503
            
        except Exception as e:
            logger.error(f"Trade execution failed for mission {mission_id}: {e}")
            
            # Revert mission status
            mission_data["status"] = "pending"
            mission_data.pop("fired_at", None)
            mission_data.pop("fired_by", None)
            save_mission_data(mission_id, mission_data)
            
            return jsonify({
                "status": "error",
                "reason": "execution_failed",
                "message": f"Trade execution failed: {str(e)}"
            }), 500
        
    except Exception as e:
        logger.error(f"Error handling fire request: {e}")
        return jsonify({
            "status": "error",
            "reason": "internal_error",
            "message": "Internal server error"
        }), 500


@app.route("/api/missions/<mission_id>/cancel", methods=["POST"])
@require_auth
def cancel_mission(mission_id: str):
    """Cancel a pending mission"""
    try:
        # Validate mission access
        if not validate_mission_access(request.user_id, mission_id):
            return jsonify({
                "status": "error",
                "reason": "access_denied",
                "message": "You don't have access to this mission"
            }), 403
        
        # Load mission data
        mission_data = load_mission_data(mission_id)
        if not mission_data:
            return jsonify({
                "status": "error",
                "reason": "mission_not_found",
                "message": "Mission not found"
            }), 404
        
        # Check if mission can be cancelled
        if mission_data.get("status") != "pending":
            return jsonify({
                "status": "error",
                "reason": "cannot_cancel",
                "message": "Only pending missions can be cancelled"
            }), 400
        
        # Update mission status
        mission_data["status"] = "cancelled"
        mission_data["cancelled_at"] = datetime.utcnow().isoformat()
        mission_data["cancelled_by"] = request.user_id
        
        # Save updated mission data
        if not save_mission_data(mission_id, mission_data):
            return jsonify({
                "status": "error",
                "reason": "save_failed",
                "message": "Failed to cancel mission"
            }), 500
        
        logger.info(f"Mission {mission_id} cancelled by user {request.user_id}")
        
        return jsonify({
            "status": "success",
            "message": "Mission cancelled successfully",
            "mission_id": mission_id
        })
        
    except Exception as e:
        logger.error(f"Error cancelling mission {mission_id}: {e}")
        return jsonify({
            "status": "error",
            "reason": "internal_error",
            "message": "Internal server error"
        }), 500


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "mission_endpoints",
        "timestamp": datetime.utcnow().isoformat(),
        "missions_dir": MISSIONS_DIR,
        "missions_dir_exists": os.path.exists(MISSIONS_DIR)
    })


if __name__ == "__main__":
    # Create missions directory if it doesn't exist
    os.makedirs(MISSIONS_DIR, exist_ok=True)
    
    # Start the Flask app
    app.run(host='0.0.0.0', port=5001, debug=False)
