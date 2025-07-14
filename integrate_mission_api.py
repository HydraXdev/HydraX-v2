#!/usr/bin/env python3
"""
Integration script to add Mission API to existing BITTEN webapp
"""

import os
import sys

def integrate_mission_api():
    """Add mission API integration to webapp_server.py"""
    
    webapp_server_path = "/root/HydraX-v2/webapp_server.py"
    
    if not os.path.exists(webapp_server_path):
        print("❌ webapp_server.py not found")
        return False
    
    # Read existing webapp_server.py
    with open(webapp_server_path, 'r') as f:
        content = f.read()
    
    # Check if already integrated
    if 'mission_endpoints' in content:
        print("✅ Mission API already integrated")
        return True
    
    # Add mission API import after existing imports
    import_line = "from src.api.mission_endpoints import register_mission_api"
    
    # Find a good place to add the import
    lines = content.split('\n')
    insert_index = 0
    
    for i, line in enumerate(lines):
        if line.strip().startswith('from ') or line.strip().startswith('import '):
            insert_index = i + 1
        elif line.strip() == '' and insert_index > 0:
            break
    
    # Insert the import
    lines.insert(insert_index, import_line)
    
    # Find where Flask app is created and add mission API registration
    app_creation_index = -1
    for i, line in enumerate(lines):
        if 'app = Flask' in line or 'Flask(__name__)' in line:
            app_creation_index = i
            break
    
    if app_creation_index == -1:
        print("❌ Could not find Flask app creation")
        return False
    
    # Add mission API registration after app creation
    registration_lines = [
        "",
        "# Register Mission API endpoints",
        "mission_api = register_mission_api(app)",
        ""
    ]
    
    # Insert after app creation
    for i, reg_line in enumerate(registration_lines):
        lines.insert(app_creation_index + 1 + i, reg_line)
    
    # Write back to file
    with open(webapp_server_path, 'w') as f:
        f.write('\n'.join(lines))
    
    print("✅ Mission API integrated into webapp_server.py")
    return True

def create_static_routes():
    """Ensure static routes for JavaScript files work"""
    
    # Create .htaccess for Apache or nginx config suggestion
    htaccess_content = """
# BITTEN Static File Configuration
<IfModule mod_rewrite.c>
    RewriteEngine On
    
    # Serve JavaScript files with correct MIME type
    <Files "*.js">
        Header set Content-Type "application/javascript"
    </Files>
    
    # Allow access to common UI files
    RewriteRule ^src/ui/common/(.*)$ src/ui/common/$1 [L]
</IfModule>
"""
    
    with open("/root/HydraX-v2/.htaccess", 'w') as f:
        f.write(htaccess_content)
    
    print("✅ Static file configuration created")

def test_integration():
    """Test if the integration works"""
    
    try:
        # Try to import the mission endpoints
        sys.path.append('/root/HydraX-v2')
        from src.api.mission_endpoints import register_mission_api
        print("✅ Mission API import successful")
        
        # Check if JavaScript files exist
        js_files = [
            "/root/HydraX-v2/src/ui/common/mission_functions.js",
            "/root/HydraX-v2/src/ui/common/webapp_functions.js"
        ]
        
        for js_file in js_files:
            if os.path.exists(js_file):
                print(f"✅ {os.path.basename(js_file)} exists")
            else:
                print(f"❌ {os.path.basename(js_file)} missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def main():
    print("🚀 BITTEN Mission API Integration")
    print("=" * 40)
    
    # Step 1: Integrate Mission API
    if integrate_mission_api():
        print("✅ Step 1: Mission API integrated")
    else:
        print("❌ Step 1: Failed to integrate Mission API")
        return
    
    # Step 2: Create static file routes
    create_static_routes()
    print("✅ Step 2: Static routes configured")
    
    # Step 3: Test integration
    if test_integration():
        print("✅ Step 3: Integration test passed")
    else:
        print("❌ Step 3: Integration test failed")
        return
    
    print("\n🎖️ INTEGRATION COMPLETE!")
    print("\nNext steps:")
    print("1. Restart webapp_server.py")
    print("2. Test menu buttons in browser")
    print("3. Check browser console for any errors")
    print("4. Verify API endpoints at /api/fire, /api/execute-operation, etc.")

if __name__ == "__main__":
    main()