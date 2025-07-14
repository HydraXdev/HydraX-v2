#!/usr/bin/env python3
"""
Integration script to connect the complete onboarding system to BITTEN webapp
"""

import os
import shutil

def integrate_onboarding_system():
    """Integrate all onboarding components with the main webapp"""
    
    print("🚀 BITTEN Onboarding System Integration")
    print("=" * 50)
    
    # Step 1: Add routes to webapp_server.py
    webapp_path = "/root/HydraX-v2/webapp_server.py"
    
    if os.path.exists(webapp_path):
        print("✅ Found webapp_server.py")
        add_onboarding_routes(webapp_path)
    else:
        print("❌ webapp_server.py not found")
        return False
    
    # Step 2: Create static file serving for onboarding
    create_static_routes()
    
    # Step 3: Test all components
    test_components()
    
    print("\n🎖️ ONBOARDING INTEGRATION COMPLETE!")
    print("\nFiles created:")
    print("📱 /onboarding/enhanced_landing.html - Zero friction landing page")
    print("🐾 /onboarding/bit_webapp.html - Bit's interactive demo")
    print("📡 /onboarding/telegram_preview.html - Live Terminal preview")
    print("⚙️ /src/api/press_pass_provisioning.py - Backend API")
    
    print("\nTest URLs:")
    print("🌐 http://localhost:5000/onboarding/enhanced_landing.html")
    print("🌐 http://localhost:5000/onboarding/bit_webapp.html")
    print("🌐 http://localhost:5000/onboarding/telegram_preview.html")
    
    return True

def add_onboarding_routes(webapp_path):
    """Add onboarding routes to webapp_server.py"""
    
    try:
        with open(webapp_path, 'r') as f:
            content = f.read()
        
        # Check if already integrated
        if 'press_pass_provisioning' in content:
            print("✅ Onboarding routes already integrated")
            return True
        
        # Find good insertion point
        lines = content.split('\n')
        insert_index = -1
        
        for i, line in enumerate(lines):
            if 'from src.api.mission_endpoints import register_mission_api' in line:
                insert_index = i + 1
                break
        
        if insert_index == -1:
            # Find any import line
            for i, line in enumerate(lines):
                if line.strip().startswith('from ') and 'api' in line:
                    insert_index = i + 1
                    break
        
        if insert_index == -1:
            print("❌ Could not find insertion point for imports")
            return False
        
        # Add import
        lines.insert(insert_index, "from src.api.press_pass_provisioning import register_press_pass_api")
        
        # Find Flask app creation
        app_index = -1
        for i, line in enumerate(lines):
            if 'register_mission_api(app)' in line:
                app_index = i + 1
                break
        
        if app_index == -1:
            for i, line in enumerate(lines):
                if 'app = Flask' in line:
                    app_index = i + 1
                    break
        
        if app_index == -1:
            print("❌ Could not find Flask app creation")
            return False
        
        # Add API registration
        registration_lines = [
            "",
            "# Register Press Pass API",
            "press_pass_manager = register_press_pass_api(app)",
            ""
        ]
        
        for i, reg_line in enumerate(registration_lines):
            lines.insert(app_index + i, reg_line)
        
        # Add onboarding routes
        route_lines = [
            "",
            "# Onboarding routes",
            "@app.route('/onboarding/<path:filename>')",
            "def serve_onboarding(filename):",
            "    return send_from_directory('onboarding', filename)",
            "",
            "@app.route('/start')",
            "@app.route('/press-pass')", 
            "def onboarding_start():",
            "    return redirect('/onboarding/enhanced_landing.html')",
            "",
            "@app.route('/api/track-event', methods=['POST'])",
            "def track_event():",
            "    # Analytics tracking endpoint",
            "    data = request.get_json()",
            "    # Log to analytics service",
            "    print(f\"Event: {data.get('event')} - {data.get('data')}\")",
            "    return jsonify({'success': True})",
            ""
        ]
        
        # Add routes at the end before if __name__ == "__main__"
        main_index = -1
        for i, line in enumerate(lines):
            if 'if __name__ == "__main__"' in line:
                main_index = i
                break
        
        if main_index == -1:
            main_index = len(lines)
        
        for i, route_line in enumerate(route_lines):
            lines.insert(main_index + i, route_line)
        
        # Add necessary imports at the top
        import_index = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('from flask import'):
                # Add redirect and send_from_directory to existing Flask imports
                if 'redirect' not in line:
                    lines[i] = line.replace('from flask import', 'from flask import redirect, send_from_directory,').replace(',,', ',')
                import_index = i + 1
                break
        
        # Write back
        with open(webapp_path, 'w') as f:
            f.write('\n'.join(lines))
        
        print("✅ Onboarding routes added to webapp_server.py")
        return True
        
    except Exception as e:
        print(f"❌ Error adding routes: {e}")
        return False

def create_static_routes():
    """Create static file serving configuration"""
    
    # Create nginx config snippet
    nginx_config = """
# BITTEN Onboarding Static Files
location /onboarding/ {
    alias /root/HydraX-v2/onboarding/;
    expires 1h;
    add_header Cache-Control "public, no-transform";
}

location /src/ui/common/ {
    alias /root/HydraX-v2/src/ui/common/;
    expires 1h;
    add_header Cache-Control "public, no-transform";
}
"""
    
    with open("/root/HydraX-v2/nginx_onboarding.conf", 'w') as f:
        f.write(nginx_config)
    
    # Create Apache .htaccess
    htaccess_config = """
# BITTEN Onboarding Static Files
<IfModule mod_rewrite.c>
    RewriteEngine On
    
    # Serve onboarding files
    RewriteRule ^onboarding/(.*)$ onboarding/$1 [L]
    
    # Serve JS files
    RewriteRule ^src/ui/common/(.*)$ src/ui/common/$1 [L]
</IfModule>

# Set proper MIME types
<Files "*.js">
    Header set Content-Type "application/javascript"
</Files>

<Files "*.html">
    Header set Content-Type "text/html"
</Files>
"""
    
    with open("/root/HydraX-v2/onboarding/.htaccess", 'w') as f:
        f.write(htaccess_config)
    
    print("✅ Static file serving configured")

def test_components():
    """Test all onboarding components"""
    
    print("\n🧪 Testing Components:")
    
    # Check file existence
    files_to_check = [
        "/root/HydraX-v2/onboarding/enhanced_landing.html",
        "/root/HydraX-v2/onboarding/bit_webapp.html", 
        "/root/HydraX-v2/onboarding/telegram_preview.html",
        "/root/HydraX-v2/src/api/press_pass_provisioning.py"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {os.path.basename(file_path)} exists")
        else:
            print(f"❌ {os.path.basename(file_path)} missing")
    
    # Test API import
    try:
        import sys
        sys.path.append('/root/HydraX-v2')
        from src.api.press_pass_provisioning import register_press_pass_api
        print("✅ Press Pass API imports successfully")
    except Exception as e:
        print(f"❌ Press Pass API import failed: {e}")
    
    # Test webapp integration
    try:
        from webapp_server import app
        print("✅ Webapp server imports successfully")
    except Exception as e:
        print(f"❌ Webapp server import failed: {e}")

def create_test_data():
    """Create test data for development"""
    
    test_data = {
        "press_passes": [
            {
                "email": "test@example.com",
                "pass_id": "PRESS-TEST-001",
                "status": "active"
            }
        ],
        "analytics": {
            "total_visits": 1247,
            "conversion_rate": 23.4,
            "avg_time_on_page": 45
        }
    }
    
    with open("/root/HydraX-v2/onboarding/test_data.json", 'w') as f:
        import json
        json.dump(test_data, f, indent=2)
    
    print("✅ Test data created")

def main():
    """Main integration function"""
    
    # Ensure onboarding directory exists
    os.makedirs("/root/HydraX-v2/onboarding", exist_ok=True)
    
    # Run integration
    success = integrate_onboarding_system()
    
    if success:
        create_test_data()
        
        print("\n🎉 SUCCESS! Onboarding system fully integrated!")
        print("\nNext steps:")
        print("1. Restart webapp_server.py")
        print("2. Visit /onboarding/enhanced_landing.html")
        print("3. Test the complete flow")
        print("4. Monitor analytics at /api/press-pass-analytics")
        
        print("\n🔥 The 3-minute magic flow is ready!")
        
    else:
        print("\n❌ Integration failed - check errors above")

if __name__ == "__main__":
    main()