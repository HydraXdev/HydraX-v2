"""
Security Audit Logger - Usage Examples

This file demonstrates how to integrate the audit logger into different
components of the BITTEN system.
"""

from audit_logger import get_audit_logger

# Get singleton instance
audit = get_audit_logger()


# ============================================================
# EXAMPLE 1: Mission Session Management
# ============================================================


def create_mission_session(user_id: str, alert_id: str) -> dict:
    """
    Example: Creating a mission session from an alert
    """
    import uuid
    from datetime import datetime, timedelta

    # Generate session ID
    session_id = f"ms_{uuid.uuid4().hex[:12]}"

    # Session TTL (5 minutes)
    ttl_seconds = 300

    # Log session creation
    audit.log_session_created(
        sub=user_id,
        ms=session_id,
        aid=alert_id,
        ttl=ttl_seconds,
        created_via="telegram_bot",  # Extra context
        session_type="fire_mission",
    )

    return {"session_id": session_id, "expires_at": datetime.utcnow() + timedelta(seconds=ttl_seconds)}


def validate_mission_session(user_id: str, session_id: str) -> bool:
    """
    Example: Validating a mission session before fire execution
    """
    # Simulated validation logic
    is_valid = True  # Replace with actual validation
    reason = None

    if not is_valid:
        reason = "Session expired"

    # Log validation attempt
    audit.log_session_validated(
        sub=user_id, ms=session_id, result=is_valid, reason=reason, validation_method="jwt_claim_check"
    )

    return is_valid


def execute_mission_session(user_id: str, session_id: str) -> str:
    """
    Example: Executing a mission session
    """
    import uuid

    # Generate operation ID (fire ID)
    operation_id = f"fire_{uuid.uuid4().hex[:12]}"

    # Log session execution
    audit.log_session_executed(sub=user_id, ms=session_id, op_id=operation_id, execution_method="auto_fire")

    return operation_id


# ============================================================
# EXAMPLE 2: Fire Command Execution with Guardrails
# ============================================================


def execute_fire_command(
    user_id: str, session_id: str, alert_id: str, risk_pct: float, client_request_id: str = None
) -> dict:
    """
    Example: Fire command with risk checks and idempotency
    """
    import uuid

    # Generate fire ID
    fire_id = f"fire_{uuid.uuid4().hex[:12]}"

    # Check idempotency
    if client_request_id:
        cached_fire_id = check_idempotency_cache(client_request_id)
        if cached_fire_id:
            audit.log_fire_idempotent_hit(
                sub=user_id, ms=session_id, client_request_id=client_request_id, cached_op_id=cached_fire_id
            )
            return {"fire_id": cached_fire_id, "cached": True}

    # Check risk guardrails
    max_risk = get_max_risk_for_user(user_id)
    if risk_pct > max_risk:
        audit.log_fire_risk_violation(
            sub=user_id, ms=session_id, requested_risk=risk_pct, max_risk=max_risk, alert_id=alert_id
        )
        raise ValueError(f"Risk {risk_pct}% exceeds maximum {max_risk}%")

    # Check scopes
    user_scopes = get_user_scopes(user_id)
    required_scope = "fire:execute"
    if required_scope not in user_scopes:
        audit.log_fire_scope_violation(
            sub=user_id, ms=session_id, required_scope=required_scope, had_scopes=user_scopes
        )
        raise PermissionError(f"User lacks required scope: {required_scope}")

    # Log fire request
    audit.log_fire_requested(
        sub=user_id, ms=session_id, aid=alert_id, op_id=fire_id, risk_pct=risk_pct, client_request_id=client_request_id
    )

    # Execute fire command (simulated)
    # ... actual fire logic here ...

    return {"fire_id": fire_id, "cached": False}


def check_idempotency_cache(request_id: str) -> str:
    """Simulated idempotency check"""
    # Replace with actual cache lookup
    return None


def get_max_risk_for_user(user_id: str) -> float:
    """Get maximum allowed risk for user tier"""
    # Replace with actual tier-based logic
    return 5.0  # 5% for COMMANDER tier


def get_user_scopes(user_id: str) -> list:
    """Get user's permission scopes"""
    # Replace with actual permission lookup
    return ["fire:view", "fire:execute", "signals:subscribe"]


# ============================================================
# EXAMPLE 3: WebSocket Connection Management
# ============================================================


class WebSocketConnectionHandler:
    """Example: WebSocket connection with authentication and authorization"""

    def __init__(self):
        self.connections = {}  # sid -> {'user_id': str, 'connected_at': float}

    def on_connect(self, sid: str, environ: dict):
        """Handle new WebSocket connection"""
        import time

        # Log connection attempt (no user yet)
        audit.log_ws_connected(sid=sid, ip=environ.get("REMOTE_ADDR"), user_agent=environ.get("HTTP_USER_AGENT"))

        self.connections[sid] = {"user_id": None, "connected_at": time.time()}

    def authenticate_connection(self, sid: str, token: str) -> bool:
        """Authenticate WebSocket connection via JWT"""
        try:
            # Validate token (simulated)
            user_id = validate_jwt_token(token)

            if user_id:
                # Log successful auth
                audit.log_auth_success(sub=user_id, method="jwt", connection_type="websocket")

                # Update connection
                self.connections[sid]["user_id"] = user_id

                # Re-log connection with user
                audit.log_ws_connected(sid=sid, sub=user_id)

                return True
            else:
                raise ValueError("Invalid token")

        except Exception as e:
            # Log auth failure
            audit.log_ws_auth_failed(sid=sid, reason=str(e))
            return False

    def subscribe_to_topic(self, sid: str, topic: str) -> bool:
        """Subscribe WebSocket to a topic with authorization"""
        user_id = self.connections.get(sid, {}).get("user_id")

        if not user_id:
            audit.log_ws_auth_failed(sid=sid, reason="Not authenticated")
            return False

        # Check authorization
        authorized = is_user_authorized_for_topic(user_id, topic)

        # Log subscription attempt
        audit.log_ws_subscribed(sid=sid, sub=user_id, topic=topic, authorized=authorized)

        return authorized

    def on_disconnect(self, sid: str):
        """Handle WebSocket disconnection"""
        import time

        connection = self.connections.get(sid, {})
        user_id = connection.get("user_id")
        connected_at = connection.get("connected_at", time.time())

        duration = time.time() - connected_at

        # Log disconnection
        audit.log_ws_disconnected(sid=sid, sub=user_id, duration=duration)

        # Cleanup
        self.connections.pop(sid, None)


def validate_jwt_token(token: str) -> str:
    """Simulated JWT validation"""
    # Replace with actual JWT validation
    return "7176191872"


def is_user_authorized_for_topic(user_id: str, topic: str) -> bool:
    """Check if user can subscribe to topic"""
    # Replace with actual authorization logic
    # Example: Only COMMANDER+ can subscribe to premium signals
    return True


# ============================================================
# EXAMPLE 4: Rate Limiting with Audit Logs
# ============================================================


def check_rate_limit(user_id: str, endpoint: str, limit: int = 10) -> bool:
    """
    Example: Rate limiting with audit logging
    """
    # Simulated rate limit check
    current_requests = get_request_count(user_id, endpoint)

    if current_requests >= limit:
        # Log rate limit violation
        audit.log_rate_limit_exceeded(sub=user_id, endpoint=endpoint, limit=limit, current_requests=current_requests)
        return False

    return True


def get_request_count(user_id: str, endpoint: str) -> int:
    """Simulated request counter"""
    # Replace with actual rate limiter (Redis, etc.)
    return 5


# ============================================================
# EXAMPLE 5: Session Expiration Monitoring
# ============================================================


def monitor_session_expiration(session_id: str, expires_at: str):
    """
    Example: Background task monitoring session expiration
    """
    from datetime import datetime

    # Check if expired
    expiry = datetime.fromisoformat(expires_at)
    now = datetime.utcnow()

    if now >= expiry:
        # Log expiration
        audit.log_session_expired(ms=session_id, expired_at=expires_at, cleanup_performed=True)

        # Cleanup session
        cleanup_expired_session(session_id)


def cleanup_expired_session(session_id: str):
    """Cleanup expired session from database"""
    # Replace with actual cleanup logic
    pass


# ============================================================
# EXAMPLE 6: Authentication Flow
# ============================================================


def login_user(username: str, password: str) -> dict:
    """
    Example: User login with audit logging
    """
    # Validate credentials (simulated)
    user = validate_credentials(username, password)

    if user:
        # Log successful authentication
        audit.log_auth_success(sub=user["id"], method="password", username=username)  # Username is OK, password is NOT

        return {"token": generate_jwt(user["id"]), "user_id": user["id"]}
    else:
        # Log failed authentication
        audit.log_auth_failed(reason="Invalid credentials", username=username)  # No user ID available

        raise ValueError("Invalid credentials")


def validate_credentials(username: str, password: str) -> dict:
    """Simulated credential validation"""
    # Replace with actual user lookup
    if username == "commander" and password == "correct":
        return {"id": "7176191872", "tier": "COMMANDER"}
    return None


def generate_jwt(user_id: str) -> str:
    """Simulated JWT generation"""
    # Replace with actual JWT generation
    return "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."


# ============================================================
# EXAMPLE 7: Data Sanitization Before Logging
# ============================================================

from audit_logger import sanitize_data


def log_user_action_safely(user_id: str, action: str, data: dict):
    """
    Example: Logging arbitrary data with automatic sanitization
    """
    # Data might contain sensitive info
    user_data = {
        "user_id": user_id,
        "action": action,
        "account_balance": 10000.50,  # Will be redacted
        "account_number": "12345678",  # Will be redacted
        "tier": "COMMANDER",  # Safe
        "timestamp": "2025-10-05T12:00:00Z",  # Safe
    }

    # Sanitize before logging
    safe_data = sanitize_data(user_data)

    # Now safe to log
    audit.logger.info(f"User action: {action}", extra={"extra_data": safe_data})


# ============================================================
# EXAMPLE 8: Integration with Existing BITTEN Components
# ============================================================


def integrate_with_webapp_server():
    """
    Example: How to integrate into webapp_server_optimized.py
    """
    # In /api/fire endpoint:
    # from src.security.audit_logger import get_audit_logger
    # audit = get_audit_logger()
    #
    # @app.route('/api/fire', methods=['POST'])
    # def api_fire():
    #     user_id = get_current_user_id()
    #     session_id = request.json.get('session_id')
    #     alert_id = request.json.get('alert_id')
    #
    #     # Validate session
    #     if not validate_session(session_id):
    #         audit.log_session_validated(
    #             sub=user_id,
    #             ms=session_id,
    #             result=False,
    #             reason="Invalid session"
    #         )
    #         return jsonify({'error': 'Invalid session'}), 401
    #
    #     # Execute fire
    #     fire_id = execute_fire(user_id, session_id, alert_id)
    #
    #     audit.log_fire_requested(
    #         sub=user_id,
    #         ms=session_id,
    #         aid=alert_id,
    #         op_id=fire_id
    #     )
    #
    #     return jsonify({'fire_id': fire_id})
    pass


def integrate_with_metasocket():
    """
    Example: How to integrate into metasocket WebSocket server
    """
    # In metasocket connection handler:
    # from src.security.audit_logger import get_audit_logger
    # audit = get_audit_logger()
    #
    # @socketio.on('connect')
    # def on_connect(auth):
    #     sid = request.sid
    #     audit.log_ws_connected(sid=sid)
    #
    # @socketio.on('authenticate')
    # def on_authenticate(data):
    #     sid = request.sid
    #     token = data.get('token')
    #
    #     try:
    #         user_id = validate_token(token)
    #         audit.log_auth_success(sub=user_id, method='jwt')
    #         audit.log_ws_connected(sid=sid, sub=user_id)
    #     except Exception as e:
    #         audit.log_ws_auth_failed(sid=sid, reason=str(e))
    pass


# ============================================================
# EXAMPLE 9: Querying Audit Logs
# ============================================================


def query_audit_logs_example():
    """
    Example: How to query audit logs for security analysis
    """
    import json
    from pathlib import Path

    log_file = Path("/var/log/bitten/audit.log")

    # Find all failed authentication attempts
    failed_auths = []
    with open(log_file, "r") as f:
        for line in f:
            data = json.loads(line)
            if data["event_type"] == "auth.failed":
                failed_auths.append(data)

    # Analyze patterns
    print(f"Found {len(failed_auths)} failed authentication attempts")

    # Find all fire requests by specific user
    user_id = "7176191872"
    user_fires = []
    with open(log_file, "r") as f:
        for line in f:
            data = json.loads(line)
            if data["event_type"] == "fire.requested" and data.get("sub") == user_id:
                user_fires.append(data)

    print(f"User {user_id} made {len(user_fires)} fire requests")


# ============================================================
# RUN EXAMPLES
# ============================================================

if __name__ == "__main__":
    print("Security Audit Logger - Usage Examples")
    print("=" * 60)

    # Example 1: Mission session flow
    print("\n1. Creating mission session...")
    session = create_mission_session("7176191872", "alert_xyz789")
    print(f"   Session ID: {session['session_id']}")

    # Example 2: Fire command
    print("\n2. Executing fire command...")
    try:
        result = execute_fire_command(
            user_id="7176191872", session_id=session["session_id"], alert_id="alert_xyz789", risk_pct=2.0
        )
        print(f"   Fire ID: {result['fire_id']}")
    except Exception as e:
        print(f"   Error: {e}")

    # Example 3: WebSocket connection
    print("\n3. Handling WebSocket connection...")
    ws_handler = WebSocketConnectionHandler()
    ws_handler.on_connect("socket_123", {"REMOTE_ADDR": "192.168.1.100"})
    ws_handler.authenticate_connection("socket_123", "fake_token")
    ws_handler.subscribe_to_topic("socket_123", "signals:EURUSD")
    ws_handler.on_disconnect("socket_123")

    # Example 4: Data sanitization
    print("\n4. Sanitizing data before logging...")
    log_user_action_safely(user_id="7176191872", action="view_balance", data={"balance": 10000.50})

    print("\n" + "=" * 60)
    print("All examples completed. Check /var/log/bitten/audit.log")
    print("=" * 60)
