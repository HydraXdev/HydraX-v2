@echo off
REM BITTEN Agent Keep-Alive Script
REM This script ensures agents stay running 24/7

:MAIN_LOOP
echo ============================================
echo BITTEN AGENT KEEP-ALIVE MONITOR
echo Time: %date% %time%
echo ============================================

REM Check if agents are running
echo Checking agent status...
curl -s http://localhost:5555/health >nul 2>&1
if %errorlevel% neq 0 (
    echo Agent 5555 is DOWN - Restarting...
    goto RESTART_ALL
)

curl -s http://localhost:5556/health >nul 2>&1
if %errorlevel% neq 0 (
    echo Agent 5556 is DOWN - Restarting...
    goto RESTART_ALL
)

curl -s http://localhost:5557/health >nul 2>&1
if %errorlevel% neq 0 (
    echo Agent 5557 is DOWN - Restarting...
    goto RESTART_ALL
)

echo All agents are RUNNING
goto WAIT

:RESTART_ALL
echo Killing any existing Python processes...
taskkill /F /IM python.exe /T >nul 2>&1
timeout /t 3 >nul

echo Starting agents...
cd C:\BITTEN_Agent
start /B python primary_agent.py
timeout /t 2 >nul
start /B python backup_agent.py
timeout /t 2 >nul
start /B python websocket_agent.py

echo Agents restarted!

:WAIT
echo Waiting 60 seconds before next check...
timeout /t 60 >nul
goto MAIN_LOOP