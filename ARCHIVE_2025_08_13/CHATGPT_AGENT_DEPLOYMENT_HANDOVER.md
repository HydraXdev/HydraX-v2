# 🎯 ChatGPT Agent Deployment Handover

## Overview
This document provides step-by-step instructions for deploying the PowerShell BiTTen Dual Agent system on Windows VPS for MT5 integration. The agent manages trade execution, market data streaming, and system monitoring.

---

## 📋 Quick Deployment Steps

### 1. Prerequisites
- Windows VPS with Administrator access
- MT5 Terminal installed
- PowerShell 5.1 or higher
- Internet connection

### 2. One-Click Agent Deployment

Open PowerShell as Administrator and run:

```powershell
# Download and execute deployment script
$url = "https://raw.githubusercontent.com/HydraX/HydraX-v2/main/powershell/Deploy-BiTTenAgent-OneClick.ps1"
$script = "$env:TEMP\deploy_bitten.ps1"
Invoke-WebRequest -Uri $url -OutFile $script -UseBasicParsing
Set-ExecutionPolicy Bypass -Scope Process -Force
& $script -UserUUID "YOUR_USER_ID_HERE"
```

Replace `YOUR_USER_ID_HERE` with the actual user's Telegram ID or UUID.

### 3. Deploy Expert Advisor

The agent will attempt to deploy the EA automatically. If manual deployment is needed:

1. Copy `BITTENBridge_TradeExecutor_PRODUCTION.mq5` to:
   ```
   C:\Program Files\MetaTrader 5\MQL5\Experts\
   ```

2. In MT5:
   - Press F4 to open MetaEditor
   - Navigate to Experts folder
   - Open `BITTENBridge_TradeExecutor_PRODUCTION.mq5`
   - Press F7 to compile (must see "0 errors, 0 warnings")

3. Configure WebRequest:
   - Tools → Options → Expert Advisors
   - Check "Allow WebRequest for listed URL"
   - Add: `http://localhost:8001/market-data`
   - Click OK

4. Attach EA to charts:
   - Open charts for desired pairs (15 supported, NO XAUUSD)
   - Drag EA from Navigator to each chart
   - Click OK (keep default settings)
   - Verify smiley face appears

### 4. Verify Installation

```powershell
# Check agent service
Get-Service BiTTenDualAgent

# Test EA communication
Get-Content "C:\Program Files\MetaTrader 5\MQL5\Files\BITTEN\fire.txt"

# View agent logs
Get-Content "C:\BiTTen\Agent\Logs\*.log" -Tail 20
```

---

## 🤖 Agent Features

### Core Capabilities
- **Automated EA deployment** and management
- **Fire signal creation** via fire.txt protocol
- **Market data monitoring** for 15 currency pairs
- **System health checks** and reporting
- **Broker compatibility** detection
- **Automatic maintenance** and cleanup

### Currency Pairs Supported
```
EURUSD, GBPUSD, USDJPY, USDCAD, AUDUSD,
USDCHF, NZDUSD, EURGBP, EURJPY, GBPJPY,
GBPNZD, GBPAUD, EURAUD, GBPCHF, AUDJPY
```
⚠️ **XAUUSD is BLOCKED at all levels**

### File Locations
- **Agent**: `C:\BiTTen\Agent\`
- **Config**: `C:\BiTTen\Agent\Config\agent_config.json`
- **Logs**: `C:\BiTTen\Agent\Logs\`
- **EA Files**: `C:\Program Files\MetaTrader 5\MQL5\`
- **Signal Files**: `C:\Program Files\MetaTrader 5\MQL5\Files\BITTEN\`

---

## 🔧 Troubleshooting

### Agent Not Starting
```powershell
# Start manually
Start-Service BiTTenDualAgent

# Check event logs
Get-EventLog -LogName Application -Source BiTTenDualAgent -Newest 10
```

### EA Not Working
1. Ensure EA is compiled (no errors)
2. Check smiley face on chart
3. Verify WebRequest URL is added
4. Check Experts tab for errors

### Fire Signals Not Processing
```powershell
# Test signal creation
Import-Module "C:\BiTTen\Agent\Modules\EADeployment.psm1"
$eaManager = New-Object EADeploymentManager
$signal = @{
    symbol = "EURUSD"
    type = "buy"
    lot = 0.01
}
$eaManager.CreateFireSignal($signal)
```

### No Market Data
1. Ensure EA is attached to charts
2. Check MT5 is logged in
3. Verify localhost:8001 is accessible
4. Look for HTTP errors in MT5 Journal

---

## 📊 Testing Commands

### Create Test Signal
```powershell
$signal = @{
    symbol = "EURUSD"
    type = "buy"
    lot = 0.01
    sl = 0
    tp = 0
    comment = "Test"
} | ConvertTo-Json

$signal | Set-Content "C:\Program Files\MetaTrader 5\MQL5\Files\BITTEN\fire.txt"
```

### Check Trade Result
```powershell
Get-Content "C:\Program Files\MetaTrader 5\MQL5\Files\BITTEN\trade_result.txt"
```

### Monitor Agent Health
```powershell
# Service status
Get-Service BiTTenDualAgent | Select-Object Name, Status, StartType

# Recent logs
Get-Content "C:\BiTTen\Agent\Logs\*.log" -Tail 50 | Select-String "ERROR|WARNING"

# EA detection
Test-Path "C:\Program Files\MetaTrader 5\MQL5\Experts\BITTENBridge_TradeExecutor.ex5"
```

---

## 🚨 Important Notes

### For Master Clone Setup
If setting up a master clone for replication:

1. Use UUID: `"MASTER_TEMPLATE"` during installation
2. After setup, configure clone mode:
   ```powershell
   $config = Get-Content "C:\BiTTen\Agent\Config\agent_config.json" | ConvertFrom-Json
   $config | Add-Member -NotePropertyName "CloneMode" -NotePropertyValue $true -Force
   $config | ConvertTo-Json | Set-Content "C:\BiTTen\Agent\Config\agent_config.json"
   ```
3. This prevents the agent from modifying EA files in cloned environments

### Security Considerations
- Agent runs as Windows Service with appropriate permissions
- No credentials are stored in plain text
- All communication is local (no external connections)
- Fire signals are validated before execution

### Performance Tips
- Agent checks for signals every second
- Market data streams every 5 seconds
- Keep MT5 charts clean (minimal indicators)
- Monitor CPU usage if running multiple instances

---

## 📞 Support Information

### Log Locations for Debugging
- **Agent Logs**: `C:\BiTTen\Agent\Logs\bitten_agent_*.log`
- **MT5 Logs**: `C:\Program Files\MetaTrader 5\MQL5\Logs\`
- **Windows Event Log**: Application log, source "BiTTenDualAgent"

### Common Error Codes
- **1001**: MT5 not found
- **1002**: EA deployment failed
- **1003**: File permission error
- **1004**: Service registration failed

### Quick Health Check
```powershell
# Run comprehensive check
& "C:\BiTTen\Agent\Commission-BiTTenAgent.ps1" -UserUUID YOUR_UUID
```

---

## ✅ Deployment Checklist

Before considering deployment complete:
- [ ] Agent service is running
- [ ] EA is compiled and attached to charts
- [ ] WebRequest URL is configured
- [ ] Test signal executes successfully
- [ ] Market data endpoint is accessible
- [ ] Logs show no errors
- [ ] fire.txt is being monitored
- [ ] trade_result.txt is being written

---

**Deployment Time**: Approximately 5-10 minutes
**Required Access**: Administrator privileges on Windows VPS
**Support**: Check logs first, then escalate if needed