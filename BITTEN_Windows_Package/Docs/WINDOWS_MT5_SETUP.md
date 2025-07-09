# BITTEN MT5 Windows Setup Guide

## Overview

This guide will help you set up a complete MT5 trading farm on Windows Server (AWS or any Windows machine) with 3 MT5 instances running the enhanced BITTEN EA.

## Prerequisites

- Windows Server 2019/2022 (or Windows 10/11)
- Python 3.8+ installed
- Administrator access
- Broker account credentials (3 accounts recommended)
- At least 4GB RAM and 20GB disk space

## Quick Start

### 1. Download Setup Package

```powershell
# Create base directory
New-Item -Path "C:\BITTEN" -ItemType Directory -Force

# Download setup files (or copy from your source)
# All files are in /root/HydraX-v2/
```

### 2. Run Initial Setup

```powershell
# Open PowerShell as Administrator
Set-ExecutionPolicy Bypass -Scope Process -Force

# Navigate to BITTEN directory
cd C:\BITTEN

# Run setup script
.\setup_mt5_windows.ps1
```

### 3. Install MT5 Instances

For each broker (1, 2, 3):

```powershell
# Run installation batch file
.\install_mt5_broker1.bat
.\install_mt5_broker2.bat
.\install_mt5_broker3.bat
```

### 4. Configure Each MT5

1. Start MT5: `C:\BITTEN\Broker1\terminal64.exe`
2. Login to your broker account
3. Open MetaEditor (F4)
4. Navigate to Experts folder
5. Find `BITTENBridge_v3_ENHANCED.mq5`
6. Compile (F7)
7. Attach to EURUSD chart
8. Enable AutoTrading

### 5. Start the Farm

```powershell
# Start all MT5 instances and API
.\start_bitten_farm.ps1
```

## Detailed Configuration

### EA Settings

For each MT5 instance, configure the EA with these inputs:

```
InstructionFile: bitten_instructions_secure.txt
CommandFile: bitten_commands_secure.txt
ResultFile: bitten_results_secure.txt
StatusFile: bitten_status_secure.txt
PositionsFile: bitten_positions_secure.txt
AccountFile: bitten_account_secure.txt
MarketFile: bitten_market_secure.txt
CheckIntervalMs: 100
MagicNumber: 20250626
EnableTrailing: true
EnablePartialClose: true
EnableBreakEven: true
EnableMultiTP: true
```

### API Configuration

The Python API runs on port 8001 and provides:

- `GET /health` - Check system health
- `POST /execute` - Execute trades
- `GET /positions` - Get all positions
- `GET /account/{broker}` - Get account data

### Firewall Rules

Run as Administrator:

```powershell
.\configure_firewall.ps1
```

This opens:
- Port 8001 for API access
- Port 443 for MT5 broker connections

### Auto-Start on Boot

To start the farm automatically:

```powershell
.\create_scheduled_task.ps1
```

## File Structure

```
C:\BITTEN\
├── Broker1\
│   ├── MQL5\
│   │   ├── Experts\
│   │   │   └── BITTENBridge_v3_ENHANCED.mq5
│   │   └── Files\
│   │       └── BITTEN\
│   │           ├── bitten_account_secure.txt
│   │           ├── bitten_positions_secure.txt
│   │           └── bitten_market_secure.txt
│   └── terminal64.exe
├── Broker2\ (same structure)
├── Broker3\ (same structure)
├── API\
│   ├── bitten_api.py
│   └── requirements.txt
├── Logs\
└── Scripts\
```

## Testing

### 1. Check API Health

```powershell
# From PowerShell
Invoke-RestMethod -Uri "http://localhost:8001/health"
```

### 2. Check Account Data

```powershell
# Check Broker 1 account
Invoke-RestMethod -Uri "http://localhost:8001/account/broker1"
```

### 3. Test Trade Execution

```powershell
$trade = @{
    symbol = "EURUSD"
    direction = "BUY"
    risk_percent = 2.0
    sl = 1.0900
    tp = 1.1100
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8001/execute" -Method POST -Body $trade -ContentType "application/json"
```

## Monitoring

### PowerShell Monitoring Script

```powershell
# Monitor all accounts
while ($true) {
    Clear-Host
    Write-Host "BITTEN MT5 Farm Status" -ForegroundColor Green
    Write-Host "=====================" -ForegroundColor Green
    
    for ($i = 1; $i -le 3; $i++) {
        try {
            $account = Invoke-RestMethod -Uri "http://localhost:8001/account/broker$i"
            Write-Host "`nBroker $i:" -ForegroundColor Yellow
            Write-Host "  Balance: $" -NoNewline
            Write-Host ("{0:N2}" -f $account.balance) -ForegroundColor Cyan
            Write-Host "  Equity: $" -NoNewline
            Write-Host ("{0:N2}" -f $account.equity) -ForegroundColor Cyan
            Write-Host "  Positions: " -NoNewline
            Write-Host $account.positions.total -ForegroundColor Cyan
        } catch {
            Write-Host "`nBroker $i: Not connected" -ForegroundColor Red
        }
    }
    
    Start-Sleep -Seconds 5
}
```

## Troubleshooting

### MT5 Won't Start
- Check Windows Event Viewer
- Ensure Visual C++ Redistributables are installed
- Try running as Administrator

### EA Not Loading
- Check Experts tab for errors
- Ensure AutoTrading is enabled
- Check file permissions on BITTEN folder

### API Connection Issues
- Check firewall rules
- Verify Python is installed
- Check port 8001 is not in use

### No Account Data
- Ensure EA is attached and running
- Check Files\BITTEN folder exists
- Verify EA has file write permissions

## Security Considerations

1. **Firewall**: Only allow API access from trusted IPs
2. **Credentials**: Store broker passwords securely
3. **Updates**: Keep Windows and MT5 updated
4. **Monitoring**: Set up alerts for unusual activity
5. **Backups**: Regular backup of configuration files

## Performance Tuning

### For VPS/AWS:
- Use at least t3.medium instance
- Enable Enhanced Networking
- Use SSD storage
- Consider dedicated CPU for production

### Windows Optimization:
- Disable Windows Updates during trading hours
- Disable unnecessary services
- Set Power Plan to High Performance
- Disable Windows Defender real-time scanning for BITTEN folder

## Integration with Main Server

From your Linux server, connect to the Windows farm:

```python
# In your Python code
MT5_FARM_URL = "http://your-windows-server:8001"

# Execute trades
response = requests.post(f"{MT5_FARM_URL}/execute", json=trade_params)

# Get positions
positions = requests.get(f"{MT5_FARM_URL}/positions").json()
```

## Next Steps

1. Test with demo accounts first
2. Monitor for 24 hours before going live
3. Set up proper logging and alerts
4. Implement backup MT5 instances
5. Consider load balancing for high volume

## Support

For issues:
1. Check EA logs in Experts tab
2. Review Windows Event Viewer
3. Check C:\BITTEN\Logs\
4. Test API endpoints individually