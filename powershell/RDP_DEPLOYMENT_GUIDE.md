# 🚀 BiTTen Agent RDP Deployment Guide

## Quick Deploy (Copy & Paste)

### Step 1: Open PowerShell as Administrator
1. Right-click Windows Start button
2. Click "Windows PowerShell (Admin)"
3. Click "Yes" when prompted

### Step 2: Download and Run (ONE COMMAND)
Copy and paste this entire block:

```powershell
# Download and run deployment script
$url = "https://raw.githubusercontent.com/HydraX/HydraX-v2/main/powershell/Deploy-BiTTenAgent-OneClick.ps1"
$script = "$env:TEMP\deploy_bitten.ps1"
Invoke-WebRequest -Uri $url -OutFile $script -UseBasicParsing
Set-ExecutionPolicy Bypass -Scope Process -Force
& $script
```

### Step 3: Enter Your User UUID
- When prompted, enter your Telegram User ID
- Example: `123456789`

### Step 4: Wait for Installation
The script will automatically:
- ✅ Download all components
- ✅ Install BiTTen Agent service  
- ✅ Deploy MT5 Expert Advisor
- ✅ Configure file permissions
- ✅ Create desktop shortcuts

### Step 5: MT5 Setup (Manual)
After installation completes:

1. **Open MT5 Terminal**
2. **Press F4** to open MetaEditor
3. **Navigate to**: Experts folder
4. **Open**: BITTENBridge_TradeExecutor.mq5
5. **Press F7** to compile (should see "0 errors")
6. **Drag EA** to a chart and click OK

### Step 6: Configure WebRequest
In MT5:
1. Tools → Options → Expert Advisors
2. Check "Allow WebRequest for listed URL"  
3. Add: `http://localhost:8001/market-data`
4. Click OK

## ✅ Verification

Check if everything is working:

```powershell
# Check service status
Get-Service BiTTenDualAgent

# Check EA communication
Get-Content "C:\Program Files\MetaTrader 5\MQL5\Files\BITTEN\fire.txt"

# View agent logs
Get-Content "C:\BiTTen\Agent\Logs\*.log" -Tail 20
```

## 🆘 Troubleshooting

### Agent Not Starting
```powershell
# Start manually
Start-Service BiTTenDualAgent

# Check logs
Get-EventLog -LogName Application -Source BiTTenDualAgent -Newest 10
```

### EA Not Working
- Ensure EA is compiled (no errors)
- Check smiley face on chart
- Verify WebRequest URL is added
- Check Experts tab for initialization message

### No Market Data
- Ensure EA is attached to chart
- Check Journal tab for streaming messages
- Verify localhost:8001 is accessible

## 📱 Currency Pairs

The system trades these 15 pairs ONLY:
- EURUSD, GBPUSD, USDJPY, USDCAD, AUDUSD
- USDCHF, NZDUSD, EURGBP, EURJPY, GBPJPY  
- GBPNZD, GBPAUD, EURAUD, GBPCHF, AUDJPY

**⚠️ IMPORTANT: XAUUSD (GOLD) is BLOCKED**

## 🔥 Manual Fire Test

To test signal execution:

```powershell
# Create test signal
$signal = @{
    symbol = "EURUSD"
    type = "buy"
    lot = 0.01
    sl = 0
    tp = 0
    comment = "Test Signal"
} | ConvertTo-Json

# Write to fire.txt
$signal | Set-Content "C:\Program Files\MetaTrader 5\MQL5\Files\BITTEN\fire.txt"
```

## 📞 Support

If you encounter issues:
1. Check desktop file: `BiTTen_MT5_Setup.txt`
2. Review logs: `C:\BiTTen\Agent\Logs\`
3. Run commissioning: 
   ```powershell
   & "C:\BiTTen\Agent\Commission-BiTTenAgent.ps1" -UserUUID YOUR_UUID
   ```

---

**One-Click Deploy Summary:**
1. Run PowerShell as Admin
2. Paste deployment command
3. Enter User UUID
4. Setup MT5 manually
5. Done! 🎉