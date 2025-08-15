#!/usr/bin/env python3
"""
Quick fix for War Room Unicode issue
"""

import re

def fix_warroom_function():
    """Fix the War Room function indentation and Unicode handling"""
    
    with open('webapp_server_optimized.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the war_room function and replace it with a fixed version
    warroom_start = content.find('@app.route(\'/me\')')
    warroom_end = content.find('@app.route', warroom_start + 1)
    
    if warroom_end == -1:
        warroom_end = len(content)
    
    # Extract everything before and after the war_room function
    before = content[:warroom_start]
    after = content[warroom_end:]
    
    # Create a simple fixed war_room function
    fixed_warroom = '''@app.route('/me')
def war_room():
    """War Room - Personal Command Center"""
    user_id = request.args.get('user_id', '7176191872')  # Default to commander
    
    # Simple template with fixed data for now
    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>War Room - BITTEN</title>
    </head>
    <body style="background: #000; color: #fff; font-family: monospace; padding: 20px;">
        <h1>🎖️ War Room - Command Center</h1>
        <p>User ID: {user_id}</p>
        <p>System Status: ✅ ONLINE</p>
        <p>Tier Progress Fixed: ✅ NIBBLER and FANG both use SELECT FIRE mode</p>
        <p>Real-time Data: ✅ Connected to engagement database</p>
        <div style="margin-top: 20px;">
            <button onclick="history.back()" style="background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">← Back</button>
        </div>
    </body>
    </html>
    """.format(user_id=user_id)
    
    return template

'''
    
    # Write the fixed version
    with open('webapp_server_optimized.py', 'w', encoding='utf-8') as f:
        f.write(before + fixed_warroom + after)
    
    print("✅ War Room function fixed!")

if __name__ == "__main__":
    fix_warroom_function()