# 🎯 MASTER CLONE DEPLOYMENT GUIDE

## ⚠️ CRITICAL: Master Clone Architecture

This guide creates a **MASTER CLONE** that will be replicated for all users. The master must be configured perfectly because cloned containers will be **headless** with no GUI access.

### Architecture Overview:
1. **Master Clone**: Fully configured with EA compiled and attached to all 15 charts
2. **User Clones**: Copied from master, credentials injected, no GUI access
3. **Agent Behavior**: Must NOT modify EA files or require recompilation

---

## 📋 MASTER CLONE PREPARATION

### Phase 1: Initial Windows VPS Setup

1. **Install MT5** on Windows VPS
2. **Open PowerShell as Administrator**
3. **Install BiTTen Agent** (master configuration):

```powershell
# MASTER CLONE INSTALLATION
# Use a generic UUID for master
$url = "https://raw.githubusercontent.com/HydraX/HydraX-v2/main/powershell/Deploy-BiTTenAgent-OneClick.ps1"
$script = "$env:TEMP\deploy_bitten.ps1"
Invoke-WebRequest -Uri $url -OutFile $script -UseBasicParsing
Set-ExecutionPolicy Bypass -Scope Process -Force
& $script -UserUUID "MASTER_TEMPLATE"
```

### Phase 2: MT5 Configuration

1. **Compile EA Once** (this is critical):
   - Open MT5
   - Press F4 for MetaEditor
   - Open `Experts\BITTENBridge_TradeExecutor.mq5`
   - Press F7 to compile
   - Verify "0 errors, 0 warnings"
   - Close MetaEditor

2. **Create Profile with 15 Charts**:
   - File → Profiles → Save Profile As → "BITTENProfile"
   - Open 15 charts (one for each currency pair):
     ```
     EURUSD, GBPUSD, USDJPY, USDCAD, AUDUSD,
     USDCHF, NZDUSD, EURGBP, EURJPY, GBPJPY,
     GBPNZD, GBPAUD, EURAUD, GBPCHF, AUDJPY
     ```
   - Drag EA to EACH chart
   - Click OK on settings (keep defaults)
   - Verify smiley face on all charts

3. **Configure WebRequest**:
   - Tools → Options → Expert Advisors
   - Check "Allow WebRequest for listed URL"
   - Add: `http://localhost:8001/market-data`
   - Check "Allow DLL imports" (if needed)
   - Click OK

4. **Save and Set Default Profile**:
   - File → Profiles → Save Profile As → "Default"
   - This ensures clones auto-load with EA attached

### Phase 3: Agent Configuration for Cloning

**IMPORTANT**: Configure agent to be clone-friendly:

```powershell
# Disable EA modification in agent config
$configPath = "C:\BiTTen\Agent\Config\agent_config.json"
$config = Get-Content $configPath | ConvertFrom-Json
$config | Add-Member -NotePropertyName "CloneMode" -NotePropertyValue $true -Force
$config | Add-Member -NotePropertyName "DisableEAModification" -NotePropertyValue $true -Force
$config | Add-Member -NotePropertyName "DisableFileCleanup" -NotePropertyValue $true -Force
$config | ConvertTo-Json | Set-Content $configPath
```

### Phase 4: Verify Master State

Run these checks before cloning:

```powershell
# 1. Check EA is compiled
Test-Path "C:\Program Files\MetaTrader 5\MQL5\Experts\BITTENBridge_TradeExecutor.ex5"

# 2. Check profile exists
Test-Path "C:\Program Files\MetaTrader 5\Profiles\Default\*"

# 3. Check BITTEN directory
Test-Path "C:\Program Files\MetaTrader 5\MQL5\Files\BITTEN\fire.txt"

# 4. Test EA communication
$testSignal = @{symbol="EURUSD";type="buy";lot=0.01} | ConvertTo-Json
$testSignal | Set-Content "C:\Program Files\MetaTrader 5\MQL5\Files\BITTEN\fire.txt"
Start-Sleep -Seconds 2
$content = Get-Content "C:\Program Files\MetaTrader 5\MQL5\Files\BITTEN\fire.txt"
if ($content -eq "") { "✅ EA is processing signals" } else { "❌ EA not working" }
```

### Phase 5: Prepare for Cloning

1. **Stop all services**:
   ```powershell
   Stop-Service BiTTenDualAgent
   Stop-Process -Name "terminal64" -Force -ErrorAction SilentlyContinue
   ```

2. **Clean user-specific data**:
   ```powershell
   # Remove any test trades or logs
   Remove-Item "C:\Program Files\MetaTrader 5\MQL5\Logs\*" -Force
   Remove-Item "C:\BiTTen\Agent\Logs\*" -Force
   ```

3. **Create clone marker**:
   ```powershell
   "MASTER_CLONE_READY" | Set-Content "C:\BiTTen\CLONE_READY.txt"
   ```

---

## 🔄 USER CLONE PROCESS

When creating user clones:

1. **Clone from master image**
2. **Inject credentials** (terminal.ini)
3. **Update agent UUID**:
   ```powershell
   $config = Get-Content "C:\BiTTen\Agent\Config\agent_config.json" | ConvertFrom-Json
   $config.UserUUID = "ACTUAL_USER_ID"
   $config | ConvertTo-Json | Set-Content "C:\BiTTen\Agent\Config\agent_config.json"
   ```
4. **Start services** (agent will NOT modify EA)

---

## ⚡ AGENT BEHAVIOR IN CLONE MODE

When `CloneMode` is enabled, the agent will:

### ✅ WILL DO:
- Monitor EA health and performance
- Create/manage fire.txt signals
- Read trade results
- Clean old signal files (in BITTEN folder only)
- Monitor system resources
- Report metrics to BITTEN servers
- Handle broker symbol translation

### ❌ WILL NOT DO:
- Modify or redeploy EA files
- Change MT5 configuration
- Clean EA compiled files
- Modify profiles
- Require GUI access
- Attempt to recompile EA

---

## 🎯 HANDOVER FOR CHATGPT

### For Walking Through Deployment:

1. **Start with Phase 1** - Basic installation
2. **Critical in Phase 2** - EA must be compiled and attached to ALL 15 charts
3. **Phase 3 is essential** - Set CloneMode=true to prevent EA modifications
4. **Phase 4 verification** - All tests must pass before cloning
5. **Phase 5 cleanup** - Remove any user-specific data

### Key Points to Emphasize:
- EA compilation happens ONCE on master
- Profile with 15 charts + EA is critical
- Agent must be in CloneMode
- No GUI access after cloning
- fire.txt location is standardized

### Common Issues:
- If EA not on all charts → signals won't execute
- If CloneMode not set → agent might try to modify EA
- If WebRequest not configured → no market data streaming

---

## 📞 POST-DEPLOYMENT TESTING

After deployment, test with me (Claude) using:

```powershell
# 1. Check agent status
Get-Service BiTTenDualAgent

# 2. Test fire signal
$signal = @{symbol="EURUSD";type="buy";lot=0.01} | ConvertTo-Json
$signal | Set-Content "C:\Program Files\MetaTrader 5\MQL5\Files\BITTEN\fire.txt"

# 3. Check logs
Get-Content "C:\BiTTen\Agent\Logs\*.log" -Tail 50

# 4. Verify market data streaming
netstat -an | findstr "8001"
```

---

**REMEMBER**: This master will be cloned 5000+ times. Get it right once!