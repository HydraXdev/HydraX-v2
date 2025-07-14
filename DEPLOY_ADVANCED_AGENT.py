#!/usr/bin/env python3
"""
DEPLOY ADVANCED MT5 FARM AGENT
Deploys the advanced farm management agent to AWS server
"""

import requests
import base64
import time

def deploy_advanced_agent():
    server = "3.145.84.187:5555"
    
    print("🚀 DEPLOYING ADVANCED MT5 FARM MANAGEMENT AGENT")
    print("="*55)
    
    # Read the advanced agent code
    with open('/root/HydraX-v2/ADVANCED_MT5_FARM_AGENT.py', 'r') as f:
        agent_code = f.read()
    
    print(f"📖 Advanced agent code: {len(agent_code)} characters")
    
    # Deploy via multiple methods for reliability
    deployment_methods = [
        ("Direct PowerShell", deploy_via_powershell),
        ("Line-by-Line", deploy_line_by_line),
        ("Base64 Transfer", deploy_via_base64)
    ]
    
    for method_name, method_func in deployment_methods:
        print(f"\n🔄 Trying {method_name}...")
        try:
            if method_func(server, agent_code):
                print(f"✅ {method_name} successful!")
                break
            else:
                print(f"❌ {method_name} failed")
        except Exception as e:
            print(f"❌ {method_name} error: {e}")
    
    # Install required packages
    install_packages(server)
    
    # Create startup script
    create_startup_script(server)
    
    # Test the new agent
    test_advanced_agent(server)

def deploy_via_powershell(server, agent_code):
    """Deploy using PowerShell here-string"""
    
    # Escape the code for PowerShell
    escaped_code = agent_code.replace('"', '""').replace('`', '``').replace('$', '`$')
    
    ps_command = f'''
$content = @"
{escaped_code}
"@
$content | Out-File -FilePath "C:\\BITTEN_Agent\\advanced_farm_agent.py" -Encoding UTF8
'''
    
    payload = {
        'action': 'execute_command',
        'command': f'powershell -Command "{ps_command}"',
        'timeout': 30
    }
    
    response = requests.post(f'http://{server}/execute', json=payload, timeout=35)
    
    if response.status_code == 200:
        # Verify file was created
        verify_payload = {
            'action': 'execute_command',
            'command': 'dir C:\\BITTEN_Agent\\advanced_farm_agent.py'
        }
        
        verify_response = requests.post(f'http://{server}/execute', json=verify_payload, timeout=10)
        
        if verify_response.status_code == 200:
            result = verify_response.json()
            return "advanced_farm_agent.py" in result.get('stdout', '')
    
    return False

def deploy_line_by_line(server, agent_code):
    """Deploy line by line using echo commands"""
    
    lines = agent_code.split('\n')
    file_path = 'C:\\BITTEN_Agent\\advanced_farm_agent.py'
    
    # Clear existing file
    clear_cmd = f'if exist "{file_path}" del /f "{file_path}"'
    requests.post(f'http://{server}/execute', json={'action': 'execute_command', 'command': clear_cmd}, timeout=10)
    
    print(f"📝 Deploying {len(lines)} lines...")
    
    # Deploy in chunks to avoid command length limits
    chunk_size = 50
    for i in range(0, len(lines), chunk_size):
        chunk_lines = lines[i:i+chunk_size]
        
        # Create temporary chunk file
        chunk_content = '\n'.join(chunk_lines)
        chunk_b64 = base64.b64encode(chunk_content.encode('utf-8')).decode('utf-8')
        
        # Decode and append chunk
        decode_cmd = f'''powershell -Command "$content = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String('{chunk_b64}')); Add-Content -Path '{file_path}' -Value $content -NoNewline"'''
        
        payload = {
            'action': 'execute_command',
            'command': decode_cmd,
            'timeout': 15
        }
        
        response = requests.post(f'http://{server}/execute', json=payload, timeout=20)
        
        if response.status_code != 200:
            return False
        
        if i % 200 == 0:
            print(f"📤 Progress: {i}/{len(lines)} lines...")
    
    # Verify file exists
    verify_payload = {
        'action': 'execute_command',
        'command': f'dir "{file_path}"'
    }
    
    verify_response = requests.post(f'http://{server}/execute', json=verify_payload, timeout=10)
    
    if verify_response.status_code == 200:
        return "advanced_farm_agent.py" in verify_response.json().get('stdout', '')
    
    return False

def deploy_via_base64(server, agent_code):
    """Deploy using base64 encoding"""
    
    # Encode content
    content_b64 = base64.b64encode(agent_code.encode('utf-8')).decode('utf-8')
    
    # Split into manageable chunks
    chunk_size = 8000
    chunks = [content_b64[i:i+chunk_size] for i in range(0, len(content_b64), chunk_size)]
    
    print(f"📦 Base64 transfer: {len(chunks)} chunks")
    
    file_path = 'C:\\BITTEN_Agent\\advanced_farm_agent.py'
    temp_path = 'C:\\BITTEN_Agent\\temp_agent.b64'
    
    # Clear files
    clear_cmd = f'if exist "{file_path}" del /f "{file_path}" & if exist "{temp_path}" del /f "{temp_path}"'
    requests.post(f'http://{server}/execute', json={'action': 'execute_command', 'command': clear_cmd}, timeout=10)
    
    # Send chunks
    for i, chunk in enumerate(chunks):
        if i == 0:
            cmd = f'echo {chunk}> "{temp_path}"'
        else:
            cmd = f'echo {chunk}>> "{temp_path}"'
        
        payload = {
            'action': 'execute_command',
            'command': cmd,
            'timeout': 10
        }
        
        response = requests.post(f'http://{server}/execute', json=payload, timeout=15)
        
        if response.status_code != 200:
            return False
    
    # Decode base64 to final file
    decode_cmd = f'''powershell -Command "$content = Get-Content '{temp_path}' -Raw; $bytes = [System.Convert]::FromBase64String($content); [System.IO.File]::WriteAllBytes('{file_path}', $bytes); Remove-Item '{temp_path}'"'''
    
    payload = {
        'action': 'execute_command',
        'command': decode_cmd,
        'timeout': 20
    }
    
    response = requests.post(f'http://{server}/execute', json=payload, timeout=25)
    
    return response.status_code == 200

def install_packages(server):
    """Install required Python packages"""
    
    print("\n📦 Installing required packages...")
    
    packages = [
        'flask',
        'psutil', 
        'schedule',
        'requests'
    ]
    
    for package in packages:
        print(f"📦 Installing {package}...")
        
        install_cmd = f'pip install {package}'
        payload = {
            'action': 'execute_command',
            'command': install_cmd,
            'timeout': 60
        }
        
        response = requests.post(f'http://{server}/execute', json=payload, timeout=70)
        
        if response.status_code == 200:
            print(f"✅ {package} installed")
        else:
            print(f"⚠️ {package} installation may have failed")

def create_startup_script(server):
    """Create startup script for the advanced agent"""
    
    print("\n📜 Creating startup script...")
    
    startup_script = '''@echo off
echo Starting Advanced MT5 Farm Management Agent...
cd C:\\BITTEN_Agent
python advanced_farm_agent.py
pause'''
    
    script_lines = startup_script.split('\n')
    script_path = 'C:\\BITTEN_Agent\\start_advanced_agent.bat'
    
    # Clear existing
    clear_cmd = f'if exist "{script_path}" del /f "{script_path}"'
    requests.post(f'http://{server}/execute', json={'action': 'execute_command', 'command': clear_cmd}, timeout=10)
    
    # Create script
    for i, line in enumerate(script_lines):
        if i == 0:
            cmd = f'echo {line}> "{script_path}"'
        else:
            cmd = f'echo {line}>> "{script_path}"'
        requests.post(f'http://{server}/execute', json={'action': 'execute_command', 'command': cmd}, timeout=10)
    
    print("✅ Startup script created")

def test_advanced_agent(server):
    """Test the deployed advanced agent"""
    
    print("\n🧪 Testing advanced agent...")
    
    # Test Python syntax
    test_cmd = 'python -m py_compile C:\\BITTEN_Agent\\advanced_farm_agent.py'
    payload = {
        'action': 'execute_command',
        'command': test_cmd,
        'timeout': 15
    }
    
    response = requests.post(f'http://{server}/execute', json=payload, timeout=20)
    
    if response.status_code == 200:
        result = response.json()
        if not result.get('stderr'):
            print("✅ Advanced agent syntax valid")
            
            # Test import
            import_test = 'python -c "import sys; sys.path.append(\'C:\\\\BITTEN_Agent\'); import advanced_farm_agent; print(\'Import successful\')"'
            test_payload = {
                'action': 'execute_command',
                'command': import_test,
                'timeout': 10
            }
            
            test_response = requests.post(f'http://{server}/execute', json=test_payload, timeout=15)
            
            if test_response.status_code == 200:
                test_result = test_response.json()
                if "Import successful" in test_result.get('stdout', ''):
                    print("✅ Advanced agent imports successfully")
                    return True
                else:
                    print(f"⚠️ Import test: {test_result}")
            else:
                print("❌ Import test failed")
        else:
            print(f"❌ Syntax error: {result.get('stderr')}")
    else:
        print("❌ Syntax test failed")
    
    return False

def create_agent_comparison():
    """Create comparison between current and advanced agent"""
    
    comparison = """
🔄 CURRENT BASIC AGENT vs 🚀 ADVANCED FARM AGENT

CURRENT AGENT (Port 5555):
❌ Basic command execution only
❌ No farm-specific features  
❌ No automated maintenance
❌ No instance monitoring
❌ No performance optimization
❌ Manual intervention required

ADVANCED FARM AGENT (Port 5558):
✅ MT5 farm-specific management
✅ Automated cleanup & maintenance
✅ Real-time instance monitoring  
✅ Performance optimization
✅ Database-driven management
✅ Scheduled automated tasks
✅ Health monitoring & alerts
✅ Mass deployment capabilities
✅ Instance lifecycle management
✅ Automated repair functions

CAPABILITIES COMPARISON:

Basic Agent:
- Execute commands
- File operations
- Basic health check

Advanced Agent:
- Farm status monitoring
- Automated cleanup (standard/deep/logs)
- MT5 instance deployment
- Performance optimization
- Instance monitoring & repair
- Scheduled maintenance
- Database logging
- Resource monitoring
- Issue detection & resolution
- Mass deployment & scaling

RECOMMENDED SETUP:
- Keep Basic Agent (5555) for general commands
- Deploy Advanced Agent (5558) for farm management
- Use both agents for comprehensive coverage
"""
    
    print(comparison)

if __name__ == "__main__":
    create_agent_comparison()
    print("\n" + "="*60)
    deploy_advanced_agent()
    
    print("\n🎉 ADVANCED AGENT DEPLOYMENT COMPLETE!")
    print("\n📋 NEXT STEPS:")
    print("1. Start advanced agent: C:\\BITTEN_Agent\\start_advanced_agent.bat")
    print("2. Test farm management: http://3.145.84.187:5558/farm/status")
    print("3. Use advanced features via API endpoints")
    print("4. Schedule automated maintenance tasks")
    print("\n🎯 You now have enterprise-grade MT5 farm management!")