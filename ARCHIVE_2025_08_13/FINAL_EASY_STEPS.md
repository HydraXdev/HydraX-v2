# 🚀 EASIEST WINDOWS SETUP - 3 MINUTES TOTAL

## What This Does
I'll take control of your Windows VPS and set up everything automatically:
- Find your MT5 installations
- Create the farm structure  
- Deploy the EA
- Set up trade routing
- Scale to 200 MT5 instances

## 🎯 THE EASIEST WAY (For Tablet/RDP)

### Option 1: Four Lines in PowerShell
```powershell
cd \
iwr http://134.199.204.67:9999/QUICK_AGENT_SETUP.ps1 -o s.ps1
powershell -ep bypass .\s.ps1
python C:\BITTEN_Agent\agent.py
```

### Option 2: Even Easier - Use Notepad
1. Open Notepad
2. Copy these 4 lines:
```
@echo off
curl http://134.199.204.67:9999/QUICK_AGENT_SETUP.ps1 -o s.ps1
powershell -ep bypass .\s.ps1
pause
```
3. Save as `setup.bat` on Desktop
4. Double-click `setup.bat`
5. When done, type: `python C:\BITTEN_Agent\agent.py`

### Option 3: Absolute Minimum Typing
In PowerShell:
```powershell
iwr 134.199.204.67:9999/QUICK_AGENT_SETUP.ps1|iex
```
Then:
```powershell
cd C:\BITTEN_Agent && python agent.py
```

## 📊 What Happens Next

1. **You'll see**: "BITTEN Windows Agent Starting..."
2. **You'll see**: "Access from Linux: http://YOUR_IP:5555"
3. **Tell me**: Your Windows IP address
4. **I'll do**: Everything else automatically!

## 🎮 What I'll Set Up For You

```
C:\MT5_Farm\
├── Masters\
│   ├── Forex_Demo\     (Your Forex.com)
│   └── Coinexx_Live\   (Your Coinexx)
├── Clones\
│   ├── Instance_1\     (Ready for users)
│   ├── Instance_2\
│   └── ... up to 200
├── EA\                 (BITTEN EA deployed)
└── Trade Router        (Automatic routing)
```

## 🔧 Troubleshooting

**Can't download?**
- Make sure you typed the IP correctly: `134.199.204.67`
- Try `curl` instead of `iwr`

**Python error?**
- The script auto-installs Python, just wait 2 minutes

**Firewall warning?**
- Click "Allow" when Windows asks

**Need to find your IP?**
```powershell
ipconfig | findstr IPv4
```

## 🏃 Quick Test

After agent starts, you'll see something like:
```
BITTEN Windows Agent Starting...
Access from Linux: http://192.168.1.100:5555
```

Just tell me that IP (192.168.1.100 in this example) and I'll handle everything!

## 💡 Pro Tip

Once the agent is running, you never need to use slow RDP again. I can:
- Upload files instantly
- Run any command
- Configure MT5s
- Monitor everything
- Fix any issues

The HTTP server is running at http://134.199.204.67:9999 - ready for you!