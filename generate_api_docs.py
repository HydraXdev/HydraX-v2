#!/usr/bin/env python3
"""
OpenAPI Documentation Generator for HydraX Backend
Scans Flask routes and generates OpenAPI 3.0 compatible documentation
"""

import os
import re
import ast
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

class OpenAPIGenerator:
    """Generate OpenAPI documentation from Flask applications."""
    
    def __init__(self):
        self.openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "HydraX BITTEN Trading API",
                "description": "Production-ready trading signal API with rate limiting and authentication",
                "version": "1.0.0",
                "contact": {
                    "name": "HydraX Support",
                    "url": "https://joinbitten.com"
                }
            },
            "servers": [
                {
                    "url": "https://joinbitten.com",
                    "description": "Production server"
                },
                {
                    "url": "http://localhost:8888",
                    "description": "Development server"
                }
            ],
            "paths": {},
            "components": {
                "schemas": {},
                "securitySchemes": {
                    "BearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT"
                    },
                    "ApiKeyAuth": {
                        "type": "apiKey",
                        "in": "header",
                        "name": "X-API-Key"
                    }
                }
            }
        }
    
    def extract_route_info(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract Flask route information from a Python file."""
        routes = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Find @app.route decorators with their functions
            route_pattern = r'@app\.route\([\'"]([^\'"]+)[\'"](?:,\s*methods\s*=\s*\[([^\]]+)\])?\)\s*\ndef\s+(\w+)\([^)]*\):\s*(?:"""([^"]+)""")?'
            matches = re.finditer(route_pattern, content, re.MULTILINE | re.DOTALL)
            
            for match in matches:
                path = match.group(1)
                methods_str = match.group(2)
                function_name = match.group(3)
                docstring = match.group(4)
                
                methods = ['GET']  # Default method
                if methods_str:
                    methods = [m.strip().strip('\'"') for m in methods_str.split(',')]
                
                route_info = {
                    'path': path,
                    'methods': methods,
                    'function': function_name,
                    'docstring': docstring.strip() if docstring else None,
                    'file': os.path.basename(file_path)
                }
                routes.append(route_info)
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
        
        return routes
    
    def generate_path_spec(self, route: Dict[str, Any]) -> Dict[str, Any]:
        """Generate OpenAPI path specification for a route."""
        path_spec = {}
        
        for method in route['methods']:
            method_lower = method.lower()
            
            operation = {
                "summary": route['docstring'] or f"{method} {route['path']}",
                "description": f"Function: {route['function']} (from {route['file']})",
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        }
                    },
                    "400": {
                        "description": "Bad request"
                    },
                    "401": {
                        "description": "Unauthorized"
                    },
                    "429": {
                        "description": "Rate limit exceeded"
                    },
                    "500": {
                        "description": "Internal server error"
                    }
                }
            }
            
            # Add security based on path
            if '/api/' in route['path'] or 'admin' in route['path']:
                operation["security"] = [{"BearerAuth": []}, {"ApiKeyAuth": []}]
            
            # Add parameters for path variables
            path_params = re.findall(r'<(\w+)>', route['path'])
            if path_params:
                operation["parameters"] = []
                for param in path_params:
                    operation["parameters"].append({
                        "name": param,
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    })
            
            # Add request body for POST/PUT/PATCH
            if method_lower in ['post', 'put', 'patch']:
                operation["requestBody"] = {
                    "content": {
                        "application/json": {
                            "schema": {"type": "object"}
                        }
                    }
                }
            
            path_spec[method_lower] = operation
        
        return path_spec
    
    def scan_flask_files(self, directory: str) -> None:
        """Scan directory for Flask application files."""
        flask_files = [
            'webapp_server_optimized.py',
            'webapp_server.py',
            'commander_throne.py',
            'src/api/mission_endpoints.py',
            'src/api/press_pass_provisioning.py',
            'src/bitten_core/web_app.py'
        ]
        
        all_routes = []
        
        for file_pattern in flask_files:
            file_path = os.path.join(directory, file_pattern)
            if os.path.exists(file_path):
                routes = self.extract_route_info(file_path)
                all_routes.extend(routes)
                print(f"Found {len(routes)} routes in {file_pattern}")
        
        # Process routes into OpenAPI spec
        for route in all_routes:
            # Convert Flask path to OpenAPI path
            openapi_path = re.sub(r'<(\w+)>', r'{\1}', route['path'])
            
            if openapi_path not in self.openapi_spec['paths']:
                self.openapi_spec['paths'][openapi_path] = {}
            
            path_spec = self.generate_path_spec(route)
            self.openapi_spec['paths'][openapi_path].update(path_spec)
        
        print(f"Generated documentation for {len(self.openapi_spec['paths'])} unique paths")
    
    def add_common_schemas(self):
        """Add common data schemas to the specification."""
        self.openapi_spec['components']['schemas'].update({
            "TradingSignal": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "symbol": {"type": "string", "example": "EURUSD"},
                    "direction": {"type": "string", "enum": ["BUY", "SELL"]},
                    "entry": {"type": "number", "format": "float"},
                    "stop_loss": {"type": "number", "format": "float"},
                    "take_profit": {"type": "number", "format": "float"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 100},
                    "timestamp": {"type": "string", "format": "date-time"}
                },
                "required": ["symbol", "direction", "entry", "stop_loss", "take_profit"]
            },
            "UserProfile": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "tier": {"type": "string", "enum": ["PRESS_PASS", "NIBBLER", "FANG", "COMMANDER"]},
                    "balance": {"type": "number", "format": "float"},
                    "win_rate": {"type": "number", "format": "float"},
                    "total_trades": {"type": "integer"}
                }
            },
            "ApiResponse": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "message": {"type": "string"},
                    "data": {"type": "object"}
                }
            },
            "RateLimitResponse": {
                "type": "object",
                "properties": {
                    "error": {"type": "string"},
                    "remaining": {"type": "integer"},
                    "reset_time": {"type": "number"},
                    "retry_after": {"type": "number"}
                }
            }
        })
    
    def generate_documentation(self, output_file: str) -> None:
        """Generate complete OpenAPI documentation."""
        self.add_common_schemas()
        
        # Write OpenAPI spec to file
        with open(output_file, 'w') as f:
            json.dump(self.openapi_spec, f, indent=2)
        
        print(f"OpenAPI documentation generated: {output_file}")
        
        # Generate simple HTML documentation
        html_file = output_file.replace('.json', '.html')
        html_content = f'''
<!DOCTYPE html>
<html>
<head>
    <title>HydraX BITTEN API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui.css" />
    <style>
        .swagger-ui .topbar {{ display: none; }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui-bundle.js"></script>
    <script>
        SwaggerUIBundle({{
            url: '{os.path.basename(output_file)}',
            dom_id: '#swagger-ui',
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIBundle.presets.standalone
            ]
        }});
    </script>
</body>
</html>
'''
        
        with open(html_file, 'w') as f:
            f.write(html_content)
        
        print(f"HTML documentation generated: {html_file}")

def main():
    """Generate API documentation for HydraX backend."""
    generator = OpenAPIGenerator()
    project_root = "/root/HydraX-v2"
    
    print("🚀 Generating OpenAPI documentation for HydraX backend...")
    generator.scan_flask_files(project_root)
    
    output_file = os.path.join(project_root, "docs", "api_documentation.json")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    generator.generate_documentation(output_file)
    
    print("✅ API documentation generation complete!")
    print(f"📖 View documentation: docs/api_documentation.html")

if __name__ == "__main__":
    main()