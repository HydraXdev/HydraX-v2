#!/usr/bin/env python3
"""
BITTEN v2.1 - Admin Endpoints for User Management
Date: 2025-09-16
Purpose: REST API endpoints for admin control of user settings and monitoring

Integration: Add these routes to webapp_server_optimized.py
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, Optional

from flask import jsonify, render_template_string, request

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:
    psycopg = None

logger = logging.getLogger(__name__)


class AdminService:
    """Service class for admin operations with Postgres integration"""

    def __init__(self):
        self.dsn = os.getenv("POSTGRES_DSN", "postgresql://bitten:password@localhost:5432/bitten")
        self.conn = None
        self._connect()

    def _connect(self):
        """Establish database connection"""
        if psycopg is None:
            logger.warning("⚠️ psycopg not available, admin features disabled")
            return False

        try:
            self.conn = psycopg.connect(self.dsn, row_factory=dict_row)
            return True
        except Exception as e:
            logger.error(f"❌ Admin database connection failed: {e}")
            return False

    def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get complete user profile from user_profile_v"""
        if not self.conn:
            return None

        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT * FROM user_profile_v WHERE user_id = %s", (user_id,))
                return cur.fetchone()
        except Exception as e:
            logger.error(f"❌ Error fetching user profile {user_id}: {e}")
            return None

    def get_user_by_telegram(self, telegram_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by telegram_id"""
        if not self.conn:
            return None

        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT * FROM user_profile_v WHERE telegram_id = %s", (int(telegram_id),))
                return cur.fetchone()
        except Exception as e:
            logger.error(f"❌ Error fetching user by telegram {telegram_id}: {e}")
            return None

    def update_user_settings(self, user_id: int, settings: Dict[str, Any], actor: str = "admin") -> bool:
        """Update user settings with audit trail"""
        if not self.conn:
            return False

        try:
            with self.conn.cursor() as cur:
                # Get current settings for audit
                cur.execute("SELECT row_to_json(s.*) as before FROM user_settings s WHERE user_id = %s", (user_id,))
                before_result = cur.fetchone()
                before = before_result["before"] if before_result else {}

                # Upsert new settings
                cur.execute(
                    """
                    INSERT INTO user_settings
                    (user_id, tier, risk_mode, risk_per_trade_bp, max_concurrent, daily_dd_cap_bp,
                     slots, auto_fire_enabled, confidence_min, confidence_max, flags)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        tier = EXCLUDED.tier,
                        risk_mode = EXCLUDED.risk_mode,
                        risk_per_trade_bp = EXCLUDED.risk_per_trade_bp,
                        max_concurrent = EXCLUDED.max_concurrent,
                        daily_dd_cap_bp = EXCLUDED.daily_dd_cap_bp,
                        slots = EXCLUDED.slots,
                        auto_fire_enabled = EXCLUDED.auto_fire_enabled,
                        confidence_min = EXCLUDED.confidence_min,
                        confidence_max = EXCLUDED.confidence_max,
                        flags = EXCLUDED.flags
                    RETURNING row_to_json(user_settings.*) as after
                """,
                    (
                        user_id,
                        settings.get("tier"),
                        settings.get("risk_mode"),
                        settings.get("risk_per_trade_bp"),
                        settings.get("max_concurrent"),
                        settings.get("daily_dd_cap_bp"),
                        settings.get("slots"),
                        settings.get("auto_fire_enabled", True),
                        settings.get("confidence_min", 80.0),
                        settings.get("confidence_max", 89.0),
                        json.dumps(settings.get("flags", {})),
                    ),
                )

                after_result = cur.fetchone()
                after = after_result["after"] if after_result else {}

                # Create audit record
                cur.execute(
                    """
                    INSERT INTO admin_audit (actor, user_id, action, table_name, before, after)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """,
                    (actor, user_id, "update_settings", "user_settings", json.dumps(before), json.dumps(after)),
                )

                self.conn.commit()
                logger.info(f"✅ Updated settings for user {user_id} by {actor}")
                return True

        except Exception as e:
            logger.error(f"❌ Error updating user settings {user_id}: {e}")
            self.conn.rollback()
            return False

    def add_user_override(
        self, user_id: int, key: str, value: Any, expires_at: Optional[datetime] = None, actor: str = "admin"
    ) -> bool:
        """Add or update user override with audit trail"""
        if not self.conn:
            return False

        try:
            with self.conn.cursor() as cur:
                # Get current override for audit
                cur.execute("SELECT value FROM user_overrides WHERE user_id = %s AND key = %s", (user_id, key))
                before_result = cur.fetchone()
                before = before_result["value"] if before_result else None

                # Upsert override
                cur.execute(
                    """
                    INSERT INTO user_overrides (user_id, key, value, expires_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (user_id, key) DO UPDATE SET
                        value = EXCLUDED.value,
                        expires_at = EXCLUDED.expires_at,
                        created_at = now()
                """,
                    (user_id, key, json.dumps(value), expires_at),
                )

                # Create audit record
                cur.execute(
                    """
                    INSERT INTO admin_audit (actor, user_id, action, table_name, before, after)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """,
                    (
                        actor,
                        user_id,
                        "add_override",
                        "user_overrides",
                        json.dumps({"key": key, "value": before}),
                        json.dumps(
                            {"key": key, "value": value, "expires_at": expires_at.isoformat() if expires_at else None}
                        ),
                    ),
                )

                self.conn.commit()
                logger.info(f"✅ Added override {key} for user {user_id} by {actor}")
                return True

        except Exception as e:
            logger.error(f"❌ Error adding override for user {user_id}: {e}")
            self.conn.rollback()
            return False

    def get_pattern_performance(self, user_id: Optional[int] = None, days: int = 90) -> list:
        """Get pattern performance statistics"""
        if not self.conn:
            return []

        try:
            with self.conn.cursor() as cur:
                if user_id:
                    cur.execute(
                        """
                        SELECT pattern, trades, wins, pips_total, pnl_total, win_rate_pct
                        FROM user_pattern_perf_mv
                        WHERE user_id = %s AND trades > 0
                        ORDER BY trades DESC
                    """,
                        (user_id,),
                    )
                else:
                    cur.execute(
                        """
                        SELECT pattern,
                               sum(trades) as trades,
                               sum(wins) as wins,
                               sum(pips_total) as pips_total,
                               sum(pnl_total) as pnl_total,
                               100.0 * sum(wins) / nullif(sum(trades), 0) as win_rate_pct
                        FROM user_pattern_perf_mv
                        WHERE trades > 0
                        GROUP BY pattern
                        ORDER BY sum(trades) DESC
                    """
                    )

                return cur.fetchall()
        except Exception as e:
            logger.error(f"❌ Error fetching pattern performance: {e}")
            return []

    def get_audit_trail(self, user_id: Optional[int] = None, limit: int = 50) -> list:
        """Get admin audit trail"""
        if not self.conn:
            return []

        try:
            with self.conn.cursor() as cur:
                if user_id:
                    cur.execute(
                        """
                        SELECT ts, actor, action, table_name, before, after
                        FROM admin_audit
                        WHERE user_id = %s
                        ORDER BY ts DESC
                        LIMIT %s
                    """,
                        (user_id, limit),
                    )
                else:
                    cur.execute(
                        """
                        SELECT ts, actor, user_id, action, table_name, before, after
                        FROM admin_audit
                        ORDER BY ts DESC
                        LIMIT %s
                    """,
                        (limit,),
                    )

                return cur.fetchall()
        except Exception as e:
            logger.error(f"❌ Error fetching audit trail: {e}")
            return []


# Global admin service instance
admin_service = AdminService()


def register_admin_routes(app):
    """Register admin routes with Flask app"""

    @app.route("/admin/users/<int:user_id>", methods=["GET"])
    def get_user_admin(user_id):
        """Get complete user profile for admin interface"""
        try:
            profile = admin_service.get_user_profile(user_id)
            if not profile:
                return jsonify({"error": "User not found"}), 404

            return jsonify({"success": True, "user": dict(profile)})
        except Exception as e:
            logger.error(f"❌ Admin get user error: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route("/admin/users/telegram/<telegram_id>", methods=["GET"])
    def get_user_by_telegram_admin(telegram_id):
        """Get user profile by telegram ID"""
        try:
            profile = admin_service.get_user_by_telegram(telegram_id)
            if not profile:
                return jsonify({"error": "User not found"}), 404

            return jsonify({"success": True, "user": dict(profile)})
        except Exception as e:
            logger.error(f"❌ Admin get user by telegram error: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route("/admin/users/<int:user_id>/settings", methods=["POST"])
    def update_user_settings_admin(user_id):
        """Update user settings with validation"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400

            # Validate required fields and types
            settings = {}

            if "tier" in data:
                settings["tier"] = str(data["tier"])

            if "risk_per_trade_bp" in data:
                risk_bp = int(data["risk_per_trade_bp"])
                if not 50 <= risk_bp <= 2000:  # 0.5% to 20%
                    return jsonify({"error": "Risk per trade must be between 50-2000 basis points"}), 400
                settings["risk_per_trade_bp"] = risk_bp

            if "max_concurrent" in data:
                max_concurrent = int(data["max_concurrent"])
                if not 1 <= max_concurrent <= 50:
                    return jsonify({"error": "Max concurrent must be between 1-50"}), 400
                settings["max_concurrent"] = max_concurrent

            if "slots" in data:
                slots = int(data["slots"])
                if not 1 <= slots <= 100:
                    return jsonify({"error": "Slots must be between 1-100"}), 400
                settings["slots"] = slots

            if "auto_fire_enabled" in data:
                settings["auto_fire_enabled"] = bool(data["auto_fire_enabled"])

            if "confidence_min" in data:
                conf_min = float(data["confidence_min"])
                if not 50.0 <= conf_min <= 99.0:
                    return jsonify({"error": "Confidence min must be between 50-99"}), 400
                settings["confidence_min"] = conf_min

            if "confidence_max" in data:
                conf_max = float(data["confidence_max"])
                if not 50.0 <= conf_max <= 99.0:
                    return jsonify({"error": "Confidence max must be between 50-99"}), 400
                settings["confidence_max"] = conf_max

            if "flags" in data:
                settings["flags"] = data["flags"]

            # Update settings
            actor = request.headers.get("X-Admin-User", "unknown")
            success = admin_service.update_user_settings(user_id, settings, actor)

            if success:
                return jsonify({"success": True, "message": "User settings updated successfully"})
            else:
                return jsonify({"error": "Failed to update settings"}), 500

        except ValueError as e:
            return jsonify({"error": f"Invalid data type: {e}"}), 400
        except Exception as e:
            logger.error(f"❌ Admin update settings error: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route("/admin/users/<int:user_id>/overrides", methods=["POST"])
    def add_user_override_admin(user_id):
        """Add temporary user override"""
        try:
            data = request.get_json()
            if not data or "key" not in data or "value" not in data:
                return jsonify({"error": "Key and value required"}), 400

            key = str(data["key"])
            value = data["value"]
            expires_at = None

            if "expires_at" in data:
                try:
                    expires_at = datetime.fromisoformat(data["expires_at"])
                except ValueError:
                    return jsonify({"error": "Invalid expires_at format (use ISO format)"}), 400

            actor = request.headers.get("X-Admin-User", "unknown")
            success = admin_service.add_user_override(user_id, key, value, expires_at, actor)

            if success:
                return jsonify({"success": True, "message": "User override added successfully"})
            else:
                return jsonify({"error": "Failed to add override"}), 500

        except Exception as e:
            logger.error(f"❌ Admin add override error: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route("/admin/patterns/performance", methods=["GET"])
    def get_pattern_performance_admin():
        """Get pattern performance statistics"""
        try:
            user_id = request.args.get("user_id", type=int)
            days = request.args.get("days", 90, type=int)

            performance = admin_service.get_pattern_performance(user_id, days)

            return jsonify({"success": True, "patterns": [dict(row) for row in performance]})
        except Exception as e:
            logger.error(f"❌ Admin pattern performance error: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route("/admin/audit", methods=["GET"])
    def get_audit_trail_admin():
        """Get admin audit trail"""
        try:
            user_id = request.args.get("user_id", type=int)
            limit = request.args.get("limit", 50, type=int)

            audit_trail = admin_service.get_audit_trail(user_id, limit)

            return jsonify({"success": True, "audit_trail": [dict(row) for row in audit_trail]})
        except Exception as e:
            logger.error(f"❌ Admin audit trail error: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route("/admin/dashboard")
    def admin_dashboard():
        """Admin dashboard interface"""
        try:
            # Get current user (7176191872) profile
            profile = admin_service.get_user_by_telegram("7176191872")
            pattern_performance = admin_service.get_pattern_performance()
            recent_audit = admin_service.get_audit_trail(limit=20)

            dashboard_data = {
                "user_profile": dict(profile) if profile else None,
                "pattern_performance": [dict(row) for row in pattern_performance],
                "recent_audit": [dict(row) for row in recent_audit],
                "timestamp": datetime.now().isoformat(),
            }

            return render_template_string(ADMIN_DASHBOARD_TEMPLATE, data=dashboard_data)
        except Exception as e:
            logger.error(f"❌ Admin dashboard error: {e}")
            return f"Admin dashboard error: {e}", 500


# Simple admin dashboard template
ADMIN_DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>BITTEN Admin Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #fff; }
        .container { max-width: 1200px; margin: 0 auto; }
        .card { background: #2a2a2a; padding: 20px; margin: 20px 0; border-radius: 8px; }
        .metric { display: inline-block; margin: 10px 20px; }
        .metric-value { font-size: 24px; font-weight: bold; color: #4CAF50; }
        .metric-label { font-size: 14px; color: #ccc; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { border: 1px solid #444; padding: 8px; text-align: left; }
        th { background: #333; }
        .win { color: #4CAF50; }
        .loss { color: #f44336; }
        .status-active { color: #4CAF50; }
        .json-display { background: #1a1a1a; padding: 10px; border-radius: 4px; font-family: monospace; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 BITTEN Admin Dashboard</h1>
        <p>Generated: {{ data.timestamp }}</p>

        {% if data.user_profile %}
        <div class="card">
            <h2>👤 Current User Profile</h2>
            <div class="metric">
                <div class="metric-value">{{ data.user_profile.telegram_id }}</div>
                <div class="metric-label">Telegram ID</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ data.user_profile.tier or 'N/A' }}</div>
                <div class="metric-label">Tier</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ data.user_profile.risk_per_trade_bp or 'N/A' }}bp</div>
                <div class="metric-label">Risk per Trade</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ data.user_profile.slots or 'N/A' }}</div>
                <div class="metric-label">Slots</div>
            </div>
            <div class="metric">
                <div class="metric-value {{ 'status-active' if data.user_profile.auto_fire_enabled else '' }}">
                    {{ 'ENABLED' if data.user_profile.auto_fire_enabled else 'DISABLED' }}
                </div>
                <div class="metric-label">Auto-Fire</div>
            </div>

            <h3>📊 Performance Metrics</h3>
            <div class="metric">
                <div class="metric-value">{{ data.user_profile.trades or 0 }}</div>
                <div class="metric-label">Total Trades</div>
            </div>
            <div class="metric">
                <div class="metric-value win">{{ data.user_profile.wins or 0 }}</div>
                <div class="metric-label">Wins</div>
            </div>
            <div class="metric">
                <div class="metric-value loss">{{ data.user_profile.losses or 0 }}</div>
                <div class="metric-label">Losses</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ "%.1f"|format(data.user_profile.win_rate_pct or 0) }}%</div>
                <div class="metric-label">Win Rate</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ "%.1f"|format(data.user_profile.pips_total or 0) }}</div>
                <div class="metric-label">Total Pips</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ data.user_profile.xp_total or 0 }}</div>
                <div class="metric-label">XP Total</div>
            </div>
        </div>
        {% endif %}

        <div class="card">
            <h2>📈 Pattern Performance</h2>
            <table>
                <tr>
                    <th>Pattern</th>
                    <th>Trades</th>
                    <th>Wins</th>
                    <th>Win Rate</th>
                    <th>Total Pips</th>
                    <th>Total P&L</th>
                </tr>
                {% for pattern in data.pattern_performance %}
                <tr>
                    <td>{{ pattern.pattern }}</td>
                    <td>{{ pattern.trades }}</td>
                    <td class="win">{{ pattern.wins }}</td>
                    <td>{{ "%.1f"|format(pattern.win_rate_pct or 0) }}%</td>
                    <td>{{ "%.1f"|format(pattern.pips_total or 0) }}</td>
                    <td>{{ "%.2f"|format(pattern.pnl_total or 0) }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>

        <div class="card">
            <h2>📋 Recent Admin Actions</h2>
            <table>
                <tr>
                    <th>Timestamp</th>
                    <th>Actor</th>
                    <th>User ID</th>
                    <th>Action</th>
                    <th>Table</th>
                </tr>
                {% for audit in data.recent_audit %}
                <tr>
                    <td>{{ audit.ts }}</td>
                    <td>{{ audit.actor }}</td>
                    <td>{{ audit.user_id or 'N/A' }}</td>
                    <td>{{ audit.action }}</td>
                    <td>{{ audit.table_name or 'N/A' }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>
</body>
</html>
"""
