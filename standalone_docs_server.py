#!/usr/bin/env python3
"""
Standalone HydraSocket docs and health server for validation
"""

from flask import Flask, jsonify, send_file
import hashlib
import pathlib
import time
import json

app = Flask(__name__)

OPENAPI_PATH = pathlib.Path("/root/HydraX-v2/openapi/openapi.yaml")

@app.route('/healthz')
def healthz():
    """Basic health check"""
    return jsonify({
        "service": "hydrasocket-v1",
        "status": "OK",
        "timestamp": time.time()
    })

@app.route('/api/health')
def api_health():
    """Detailed health with schema hash"""
    schema_hash = ""
    if OPENAPI_PATH.exists():
        schema_hash = hashlib.sha256(OPENAPI_PATH.read_bytes()).hexdigest()

    return jsonify({
        "service": "hydrasocket-v1",
        "status": "healthy",
        "timestamp": time.time(),
        "schema_sha256": schema_hash,
        "ws_clients": 0,  # Placeholder for validation
        "event_lag_ms_p95": None
    })

@app.route('/openapi.yaml')
def openapi_yaml():
    """Serve OpenAPI spec"""
    if OPENAPI_PATH.exists():
        return send_file(OPENAPI_PATH, mimetype="application/yaml")
    else:
        return "OpenAPI spec not found", 404

@app.route('/docs')
def swagger_ui():
    """Swagger UI documentation"""
    swagger_html = '''
<!DOCTYPE html>
<html>
<head>
    <title>HydraSocket API v1</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui.css" />
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-bundle.js"></script>
    <script>
        SwaggerUIBundle({
            url: '/openapi.yaml',
            dom_id: '#swagger-ui',
            deepLinking: true,
            presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.presets.standalone],
            layout: "StandaloneLayout"
        });
    </script>
</body>
</html>
    '''
    return swagger_html

# Minimal API endpoints for testing
@app.route('/v1/trades/open', methods=['POST'])
def trades_open():
    return jsonify({"error": "RBAC test endpoint", "code": "E_RBAC_TEST"}), 403

@app.route('/v1/events')
def events():
    return jsonify({"events": [], "next_from_seq": 1, "has_more": False})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=False)