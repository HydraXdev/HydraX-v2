"""
Security Audit Logger for BITTEN System

Logs all security-relevant events with strict PII/sensitive data protection.
Designed for compliance, forensics, and security monitoring.

SECURITY REQUIREMENTS:
- NEVER log PII (balances, account numbers, full tokens)
- NEVER log sensitive data (passwords, keys, nonces)
- Log only IDs: sub (user_id), ms (session_id), aid (alert_id), opId
- Use structured logging (JSON format)
- Include timestamps (UTC)
"""

import json
import logging
import logging.handlers
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from enum import Enum


class AuditEventType(Enum):
    """Audit event types for filtering and analysis"""

    # Mission Session Events
    SESSION_CREATED = "session.created"
    SESSION_VALIDATED = "session.validated"
    SESSION_EXECUTED = "session.executed"
    SESSION_EXPIRED = "session.expired"

    # Fire Events
    FIRE_REQUESTED = "fire.requested"
    FIRE_IDEMPOTENT_HIT = "fire.idempotent_hit"
    FIRE_RISK_VIOLATION = "fire.risk_violation"
    FIRE_SCOPE_VIOLATION = "fire.scope_violation"

    # WebSocket Events
    WS_CONNECTED = "ws.connected"
    WS_AUTH_FAILED = "ws.auth_failed"
    WS_SUBSCRIBED = "ws.subscribed"
    WS_DISCONNECTED = "ws.disconnected"

    # General Security Events
    AUTH_SUCCESS = "auth.success"
    AUTH_FAILED = "auth.failed"
    AUTHORIZATION_DENIED = "authz.denied"
    RATE_LIMIT_EXCEEDED = "rate_limit.exceeded"


class SanitizedJSONFormatter(logging.Formatter):
    """Custom JSON formatter that ensures no sensitive data leaks"""

    SENSITIVE_KEYS = {
        'password', 'token', 'secret', 'key', 'nonce',
        'balance', 'account_number', 'email', 'phone',
        'equity', 'pnl', 'profit', 'loss', 'amount'
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as sanitized JSON"""
        log_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'event_type': getattr(record, 'event_type', 'unknown'),
            'message': record.getMessage(),
        }

        # Add extra fields from record, sanitizing as needed
        if hasattr(record, 'extra_data'):
            log_data.update(self._sanitize_dict(record.extra_data))

        return json.dumps(log_data, sort_keys=True)

    def _sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive keys from dictionary"""
        sanitized = {}
        for key, value in data.items():
            # Skip sensitive keys entirely
            if any(sensitive in key.lower() for sensitive in self.SENSITIVE_KEYS):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized


class AuditLogger:
    """
    Security audit logger for BITTEN system.

    Provides methods for logging all security-relevant events with
    automatic PII sanitization and log rotation.
    """

    def __init__(
        self,
        log_dir: str = "/var/log/bitten",
        log_file: str = "audit.log",
        max_bytes: int = 100 * 1024 * 1024,  # 100MB
        backup_count: int = 30,  # 30 days of daily logs
        compression: bool = True
    ):
        """
        Initialize audit logger with rotation.

        Args:
            log_dir: Directory for log files
            log_file: Name of log file
            max_bytes: Maximum size before rotation
            backup_count: Number of backup files to keep
            compression: Whether to compress rotated logs
        """
        self.log_dir = Path(log_dir)
        self.log_file = self.log_dir / log_file

        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Set restrictive permissions on log directory (owner read/write only)
        os.chmod(self.log_dir, 0o700)

        # Create logger
        self.logger = logging.getLogger('bitten.audit')
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False  # Don't propagate to root logger

        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Create rotating file handler
        if compression:
            # Use TimedRotatingFileHandler for daily rotation with compression
            handler = logging.handlers.TimedRotatingFileHandler(
                filename=str(self.log_file),
                when='midnight',
                interval=1,
                backupCount=backup_count,
                encoding='utf-8',
                utc=True
            )
            handler.namer = lambda name: name + ".gz"
            handler.rotator = self._compress_rotated_log
        else:
            # Use size-based rotation
            handler = logging.handlers.RotatingFileHandler(
                filename=str(self.log_file),
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )

        # Set formatter
        handler.setFormatter(SanitizedJSONFormatter())

        # Set restrictive permissions on log file
        if self.log_file.exists():
            os.chmod(self.log_file, 0o600)

        self.logger.addHandler(handler)

    @staticmethod
    def _compress_rotated_log(source: str, dest: str):
        """Compress rotated log file using gzip"""
        import gzip
        import shutil

        with open(source, 'rb') as f_in:
            with gzip.open(dest, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        os.remove(source)

    def _log(
        self,
        level: int,
        event_type: AuditEventType,
        message: str,
        **extra_data
    ):
        """Internal logging method with sanitization"""
        extra = {
            'event_type': event_type.value,
            'extra_data': extra_data
        }
        self.logger.log(level, message, extra=extra)

    # ============================================================
    # MISSION SESSION EVENTS
    # ============================================================

    def log_session_created(
        self,
        sub: str,
        ms: str,
        aid: str,
        ttl: int,
        **extra
    ):
        """
        Log mission session creation.

        Args:
            sub: User ID (subject)
            ms: Mission session ID
            aid: Alert ID
            ttl: Time-to-live in seconds
        """
        self._log(
            logging.INFO,
            AuditEventType.SESSION_CREATED,
            f"Mission session created for user {sub}",
            sub=sub,
            ms=ms,
            aid=aid,
            ttl=ttl,
            **extra
        )

    def log_session_validated(
        self,
        sub: str,
        ms: str,
        result: bool,
        reason: Optional[str] = None,
        **extra
    ):
        """
        Log mission session validation attempt.

        Args:
            sub: User ID
            ms: Mission session ID
            result: Whether validation succeeded
            reason: Reason for failure (if applicable)
        """
        level = logging.INFO if result else logging.WARNING
        message = (
            f"Session validation {'succeeded' if result else 'failed'} for user {sub}"
        )

        data = {
            'sub': sub,
            'ms': ms,
            'result': result,
            **extra
        }

        if reason:
            data['reason'] = reason

        self._log(
            level,
            AuditEventType.SESSION_VALIDATED,
            message,
            **data
        )

    def log_session_executed(
        self,
        sub: str,
        ms: str,
        op_id: str,
        **extra
    ):
        """
        Log mission session execution.

        Args:
            sub: User ID
            ms: Mission session ID
            op_id: Operation ID (fire ID)
        """
        self._log(
            logging.INFO,
            AuditEventType.SESSION_EXECUTED,
            f"Mission session executed by user {sub}",
            sub=sub,
            ms=ms,
            op_id=op_id,
            **extra
        )

    def log_session_expired(
        self,
        ms: str,
        expired_at: str,
        **extra
    ):
        """
        Log mission session expiration.

        Args:
            ms: Mission session ID
            expired_at: ISO timestamp of expiration
        """
        self._log(
            logging.WARNING,
            AuditEventType.SESSION_EXPIRED,
            f"Mission session {ms} expired",
            ms=ms,
            expired_at=expired_at,
            **extra
        )

    # ============================================================
    # FIRE EVENTS
    # ============================================================

    def log_fire_requested(
        self,
        sub: str,
        ms: str,
        aid: str,
        op_id: str,
        **extra
    ):
        """
        Log fire execution request.

        Args:
            sub: User ID
            ms: Mission session ID
            aid: Alert ID
            op_id: Operation ID (fire ID)
        """
        self._log(
            logging.INFO,
            AuditEventType.FIRE_REQUESTED,
            f"Fire requested by user {sub}",
            sub=sub,
            ms=ms,
            aid=aid,
            op_id=op_id,
            **extra
        )

    def log_fire_idempotent_hit(
        self,
        sub: str,
        ms: str,
        client_request_id: str,
        cached_op_id: str,
        **extra
    ):
        """
        Log idempotency cache hit.

        Args:
            sub: User ID
            ms: Mission session ID
            client_request_id: Client's request ID
            cached_op_id: Previously executed operation ID
        """
        self._log(
            logging.INFO,
            AuditEventType.FIRE_IDEMPOTENT_HIT,
            f"Idempotent fire request from user {sub}",
            sub=sub,
            ms=ms,
            client_request_id=client_request_id,
            cached_op_id=cached_op_id,
            **extra
        )

    def log_fire_risk_violation(
        self,
        sub: str,
        ms: str,
        requested_risk: float,
        max_risk: float,
        **extra
    ):
        """
        Log risk guardrail violation.

        Args:
            sub: User ID
            ms: Mission session ID
            requested_risk: Requested risk percentage
            max_risk: Maximum allowed risk percentage
        """
        self._log(
            logging.WARNING,
            AuditEventType.FIRE_RISK_VIOLATION,
            f"Risk violation: user {sub} requested {requested_risk}% (max: {max_risk}%)",
            sub=sub,
            ms=ms,
            requested_risk=requested_risk,
            max_risk=max_risk,
            **extra
        )

    def log_fire_scope_violation(
        self,
        sub: str,
        ms: str,
        required_scope: str,
        had_scopes: list,
        **extra
    ):
        """
        Log scope/permission violation.

        Args:
            sub: User ID
            ms: Mission session ID
            required_scope: Required scope/permission
            had_scopes: Scopes user actually had
        """
        self._log(
            logging.WARNING,
            AuditEventType.FIRE_SCOPE_VIOLATION,
            f"Scope violation: user {sub} lacks '{required_scope}'",
            sub=sub,
            ms=ms,
            required_scope=required_scope,
            had_scopes=had_scopes,
            **extra
        )

    # ============================================================
    # WEBSOCKET EVENTS
    # ============================================================

    def log_ws_connected(
        self,
        sid: str,
        sub: Optional[str] = None,
        **extra
    ):
        """
        Log WebSocket connection attempt.

        Args:
            sid: Socket ID
            sub: User ID (if authenticated)
        """
        message = f"WebSocket connected: {sid}"
        if sub:
            message += f" (user: {sub})"

        self._log(
            logging.INFO,
            AuditEventType.WS_CONNECTED,
            message,
            sid=sid,
            sub=sub,
            **extra
        )

    def log_ws_auth_failed(
        self,
        sid: str,
        reason: str,
        **extra
    ):
        """
        Log WebSocket authentication failure.

        Args:
            sid: Socket ID
            reason: Reason for failure
        """
        self._log(
            logging.WARNING,
            AuditEventType.WS_AUTH_FAILED,
            f"WebSocket auth failed for {sid}: {reason}",
            sid=sid,
            reason=reason,
            **extra
        )

    def log_ws_subscribed(
        self,
        sid: str,
        sub: str,
        topic: str,
        authorized: bool,
        **extra
    ):
        """
        Log WebSocket topic subscription attempt.

        Args:
            sid: Socket ID
            sub: User ID
            topic: Topic being subscribed to
            authorized: Whether subscription was authorized
        """
        level = logging.INFO if authorized else logging.WARNING
        message = (
            f"WebSocket subscription {'authorized' if authorized else 'denied'}: "
            f"user {sub} -> topic {topic}"
        )

        self._log(
            level,
            AuditEventType.WS_SUBSCRIBED,
            message,
            sid=sid,
            sub=sub,
            topic=topic,
            authorized=authorized,
            **extra
        )

    def log_ws_disconnected(
        self,
        sid: str,
        sub: Optional[str],
        duration: float,
        **extra
    ):
        """
        Log WebSocket disconnection.

        Args:
            sid: Socket ID
            sub: User ID (if was authenticated)
            duration: Connection duration in seconds
        """
        message = f"WebSocket disconnected: {sid}"
        if sub:
            message += f" (user: {sub})"
        message += f" after {duration:.2f}s"

        self._log(
            logging.INFO,
            AuditEventType.WS_DISCONNECTED,
            message,
            sid=sid,
            sub=sub,
            duration=duration,
            **extra
        )

    # ============================================================
    # GENERAL SECURITY EVENTS
    # ============================================================

    def log_auth_success(
        self,
        sub: str,
        method: str = "jwt",
        **extra
    ):
        """
        Log successful authentication.

        Args:
            sub: User ID
            method: Authentication method used
        """
        self._log(
            logging.INFO,
            AuditEventType.AUTH_SUCCESS,
            f"User {sub} authenticated via {method}",
            sub=sub,
            method=method,
            **extra
        )

    def log_auth_failed(
        self,
        reason: str,
        sub: Optional[str] = None,
        **extra
    ):
        """
        Log failed authentication attempt.

        Args:
            reason: Reason for failure
            sub: User ID (if available)
        """
        message = f"Authentication failed: {reason}"
        if sub:
            message += f" (user: {sub})"

        self._log(
            logging.WARNING,
            AuditEventType.AUTH_FAILED,
            message,
            reason=reason,
            sub=sub,
            **extra
        )

    def log_authorization_denied(
        self,
        sub: str,
        resource: str,
        action: str,
        **extra
    ):
        """
        Log authorization denial.

        Args:
            sub: User ID
            resource: Resource being accessed
            action: Action being attempted
        """
        self._log(
            logging.WARNING,
            AuditEventType.AUTHORIZATION_DENIED,
            f"Authorization denied: user {sub} cannot {action} {resource}",
            sub=sub,
            resource=resource,
            action=action,
            **extra
        )

    def log_rate_limit_exceeded(
        self,
        sub: str,
        endpoint: str,
        limit: int,
        **extra
    ):
        """
        Log rate limit violation.

        Args:
            sub: User ID
            endpoint: Endpoint being rate limited
            limit: Rate limit that was exceeded
        """
        self._log(
            logging.WARNING,
            AuditEventType.RATE_LIMIT_EXCEEDED,
            f"Rate limit exceeded: user {sub} on {endpoint} (limit: {limit})",
            sub=sub,
            endpoint=endpoint,
            limit=limit,
            **extra
        )


# Singleton instance for easy import
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create singleton audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def sanitize_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Utility function to sanitize data before logging.

    Removes or redacts sensitive fields like balances, tokens, etc.

    Args:
        data: Dictionary to sanitize

    Returns:
        Sanitized dictionary safe for logging
    """
    formatter = SanitizedJSONFormatter()
    return formatter._sanitize_dict(data)


# Example usage
if __name__ == "__main__":
    # Initialize logger
    logger = get_audit_logger()

    # Log various events
    logger.log_session_created(
        sub="7176191872",
        ms="ms_abc123",
        aid="alert_xyz789",
        ttl=300
    )

    logger.log_fire_requested(
        sub="7176191872",
        ms="ms_abc123",
        aid="alert_xyz789",
        op_id="fire_def456"
    )

    logger.log_fire_risk_violation(
        sub="7176191872",
        ms="ms_abc123",
        requested_risk=10.0,
        max_risk=5.0
    )

    logger.log_ws_connected(
        sid="socket_123",
        sub="7176191872",
        ip="192.168.1.100"
    )

    print("Audit logs written to /var/log/bitten/audit.log")
