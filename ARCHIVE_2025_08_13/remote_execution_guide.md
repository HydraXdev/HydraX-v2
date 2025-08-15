# 🌐 REMOTE EXECUTION GUIDE - MT5 MASTER CLEANUP

## TARGET: Windows Server 3.145.84.187

### 🔑 CONNECTION METHODS

#### Method 1: RDP (Recommended)
```bash
# From Linux/Mac
rdesktop -u Administrator -p [PASSWORD] 3.145.84.187:3389
# OR
xfreerdp /u:Administrator /p:[PASSWORD] /v:3.145.84.187:3389

# From Windows
mstsc /v:3.145.84.187
```

#### Method 2: PowerShell Remoting
```powershell
# Enable PS Remoting (if not already enabled)
Enable-PSRemoting -Force

# Connect
$session = New-PSSession -ComputerName 3.145.84.187 -Credential (Get-Credential)
Enter-PSSession $session

# Copy and execute cleanup script
Copy-Item -Path ".\emergency_mt5_cleanup.ps1" -Destination "C:\temp\" -ToSession $session
Invoke-Command -Session $session -FilePath "C:\temp\emergency_mt5_cleanup.ps1"
```

#### Method 3: WinRM/WinRS
```cmd
# From Windows command line
winrs -r:3.145.84.187 -u:Administrator -p:[PASSWORD] cmd

# Execute cleanup
winrs -r:3.145.84.187 -u:Administrator "powershell -ExecutionPolicy Bypass -File C:\path\to\emergency_mt5_cleanup.ps1"
```

### 🛠️ BRIDGE TROLL AGENT PORTS (5555-5557)

If using bulletproof agent ports for command execution:

```python
import socket
import json

def execute_remote_command(host, port, command):
    """Execute command via Bridge Troll Agent"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        
        request = {
            "action": "execute",
            "command": command,
            "target": "mt5_master_cleanup"
        }
        
        sock.send(json.dumps(request).encode())
        response = sock.recv(4096).decode()
        sock.close()
        
        return json.loads(response)
    except Exception as e:
        return {"error": str(e)}

# Example usage
commands = [
    "tasklist /FI \"IMAGENAME eq terminal64.exe\"",
    "taskkill /IM terminal64.exe /F",
    "powershell -ExecutionPolicy Bypass -File C:\\temp\\emergency_mt5_cleanup.ps1"
]

for cmd in commands:
    result = execute_remote_command("3.145.84.187", 5555, cmd)
    print(f"Command: {cmd}")
    print(f"Result: {result}")
    print("-" * 50)
```

### 📁 FILE TRANSFER METHODS

#### SCP/SFTP (if SSH enabled)
```bash
# Copy cleanup scripts to server
scp emergency_mt5_cleanup.ps1 administrator@3.145.84.187:C:/temp/
scp emergency_mt5_cleanup.bat administrator@3.145.84.187:C:/temp/
```

#### SMB/CIFS Share
```bash
# Mount Windows share
sudo mount -t cifs //3.145.84.187/C$ /mnt/windows -o username=Administrator

# Copy files
cp emergency_mt5_cleanup.* /mnt/windows/temp/
```

#### PowerShell Copy (from local to remote)
```powershell
$session = New-PSSession -ComputerName 3.145.84.187 -Credential (Get-Credential)
Copy-Item -Path "emergency_mt5_cleanup.ps1" -Destination "C:\temp\" -ToSession $session
```

---

## 🚀 EXECUTION STEPS

### Step 1: Upload Scripts
```bash
# Choose your method above to copy these files to the server:
# - emergency_mt5_cleanup.ps1
# - emergency_mt5_cleanup.bat
# - mt5_cleanup_checklist.md

# Recommended location: C:\temp\
```

### Step 2: Execute Cleanup
```cmd
# Connect to server via RDP/SSH/WinRS
# Navigate to script location
cd C:\temp

# Run PowerShell script (preferred)
powershell -ExecutionPolicy Bypass -File emergency_mt5_cleanup.ps1

# OR run batch script
emergency_mt5_cleanup.bat
```

### Step 3: Manual Configuration
```
After automated cleanup, manually:
1. Start MT5 terminal
2. Tools > Options > Expert Advisors
3. Disable all Algo Trading options
4. Save profile as BITTEN_MASTER_TEMPLATE
5. Close terminal
```

### Step 4: Verification
```cmd
# Verify no MT5 processes
tasklist | findstr terminal64

# Verify clean files
dir "C:\Users\Administrator\AppData\Roaming\MetaQuotes\Terminal\173477FF1060D99CE79296FC73108719\MQL5\Files\*.json"

# Should return "File Not Found"
```

---

## 🔧 TROUBLESHOOTING

### Cannot Connect to Server
- Verify server is online: `ping 3.145.84.187`
- Check firewall rules for RDP (3389) or WinRM (5985/5986)
- Confirm credentials are correct
- Try alternative connection methods

### PowerShell Execution Policy
```powershell
# If script won't run due to execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# OR
powershell -ExecutionPolicy Bypass -File script.ps1
```

### Access Denied Errors
- Ensure running with Administrator privileges
- Right-click > "Run as Administrator"
- Check UAC settings
- Verify file permissions

### MT5 Process Won't Terminate
```cmd
# Force kill with more aggressive approach
taskkill /IM terminal64.exe /F /T
wmic process where "name='terminal64.exe'" delete

# If still running, check for services
sc query | findstr -i meta
```

### Files Won't Delete/Move
```cmd
# Check file locks
handle.exe "C:\path\to\file"

# Force delete if needed
del /F /Q "C:\path\to\file"
```

---

## 📊 SUCCESS CRITERIA

✅ **Phase 1:** All MT5 processes terminated  
✅ **Phase 2:** Contaminated files quarantined (not lost)  
✅ **Phase 3:** Algo Trading disabled globally  
✅ **Phase 4:** Clean master template archived  
✅ **Verification:** No contamination remains  

**Result:** Master template ready for clean cloning