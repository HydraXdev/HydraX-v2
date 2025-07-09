
@echo off
title BULLETPROOF AGENT SYSTEM
echo Starting Bulletproof Agent System...

REM Kill any existing agents
taskkill /F /IM python.exe /T 2>nul

REM Create agent directory
mkdir C:\BITTEN_Agent 2>nul

REM Start Primary Agent (Port 5555)
echo Starting Primary Agent on port 5555...
start "Primary Agent" /min python C:\BITTEN_Agent\primary_agent.py

REM Wait 3 seconds
timeout /t 3 /nobreak > nul

REM Start Backup Agent (Port 5556)  
echo Starting Backup Agent on port 5556...
start "Backup Agent" /min python C:\BITTEN_Agent\backup_agent.py

REM Wait 3 seconds
timeout /t 3 /nobreak > nul

REM Start WebSocket Agent (Port 5557)
echo Starting WebSocket Agent on port 5557...
start "WebSocket Agent" /min python C:\BITTEN_Agent\websocket_agent.py

REM Wait 3 seconds
timeout /t 3 /nobreak > nul

REM Start Bridge Monitor
echo Starting Bridge Monitor...
start "Bridge Monitor" /min python C:\BITTEN_Bridge\bridge_monitor.py

REM Create auto-restart task
echo Creating auto-restart task...
schtasks /create /tn "BITTEN_Agent_Restart" /tr "C:\BITTEN_Agent\START_AGENTS.bat" /sc minute /mo 5 /f 2>nul

echo.
echo ========================================
echo BULLETPROOF AGENT SYSTEM STARTED
echo ========================================
echo Primary Agent: http://localhost:5555
echo Backup Agent: http://localhost:5556  
echo WebSocket Agent: ws://localhost:5557
echo Bridge Monitor: Running
echo Auto-restart: Every 5 minutes
echo ========================================
echo.
echo Press any key to close this window...
pause > nul
