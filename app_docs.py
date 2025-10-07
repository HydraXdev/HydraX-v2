#!/usr/bin/env python3
"""
HydraSocket API Documentation Blueprint
Provides OpenAPI schema and health endpoints with schema hash
"""

import hashlib
import json
import pathlib
import time

from flask import Blueprint, jsonify, render_template_string, send_file

bp_docs = Blueprint("docs", __name__)

OPENAPI_PATH = pathlib.Path("/root/HydraX-v2/openapi/openapi.yaml")


def get_ws_client_count():
    """Get current WebSocket client count"""
    try:
        from src.hydrasocket.websocket_handler import get_client_count

        return get_client_count()
    except ImportError:
        return 0


def get_metrics_collector():
    """Get metrics collector instance"""
    try:
        from src.hydrasocket.metrics import get_metrics_collector

        return get_metrics_collector()
    except ImportError:
        return None


@bp_docs.route("/openapi.yaml")
def openapi_yaml():
    """Serve OpenAPI YAML schema"""
    return send_file(OPENAPI_PATH, mimetype="application/yaml")


@bp_docs.route("/api/health")
def api_health():
    """Detailed health check with schema hash and metrics"""
    data = {
        "service": "hydrasocket-v1",
        "status": "healthy",
        "timestamp": time.time(),
        "schema_sha256": hashlib.sha256(OPENAPI_PATH.read_bytes()).hexdigest(),
        "ws_clients": get_ws_client_count(),
    }

    # Add metrics if available
    metrics = get_metrics_collector()
    if metrics:
        try:
            data["event_lag_ms_p95"] = metrics.get_p95_latency()
        except:
            data["event_lag_ms_p95"] = None

    return jsonify(data), 200


@bp_docs.route("/docs")
def swagger_ui():
    """Serve Swagger UI for API documentation"""
    swagger_html = """
<!DOCTYPE html>
<html>
<head>
    <title>HydraSocket API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui.css" />
    <style>
        html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
        *, *:before, *:after { box-sizing: inherit; }
        body { margin:0; background: #fafafa; }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {
            const ui = SwaggerUIBundle({
                url: '/openapi.yaml',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout"
            });
        };
    </script>
</body>
</html>
    """
    return swagger_html
