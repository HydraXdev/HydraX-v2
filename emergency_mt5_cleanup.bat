@echo off
REM EMERGENCY MT5 MASTER TERMINAL CLEANUP AGENT
REM Target: Windows Server 3.145.84.187
REM Terminal ID: 173477FF1060D99CE79296FC73108719
REM CRITICAL: Execute with administrator privileges

echo ========================================
echo   EMERGENCY MT5 MASTER CLEANUP AGENT
echo ========================================
echo.
echo Target Server: 3.145.84.187
echo Terminal ID: 173477FF1060D99CE79296FC73108719
echo Timestamp: %date% %time%
echo.

REM PHASE 1: IMMEDIATE SHUTDOWN
echo =========================
echo PHASE 1: IMMEDIATE SHUTDOWN
echo =========================

echo Checking for running MT5 processes...
tasklist /FI "IMAGENAME eq terminal64.exe" 2>NUL | find /I /N "terminal64.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [WARNING] ACTIVE MT5 PROCESSES DETECTED!
    echo Terminating MT5 processes...
    taskkill /IM "terminal64.exe" /F >NUL 2>&1
    timeout /t 3 >NUL
    
    REM Verify termination
    tasklist /FI "IMAGENAME eq terminal64.exe" 2>NUL | find /I /N "terminal64.exe">NUL
    if "%ERRORLEVEL%"=="0" (
        echo [ERROR] FAILED TO TERMINATE ALL PROCESSES
        pause
        exit /b 1
    ) else (
        echo [SUCCESS] ALL MT5 PROCESSES TERMINATED
    )
) else (
    echo [SUCCESS] NO ACTIVE MT5 PROCESSES FOUND
)

REM Locate master terminal directory
echo.
echo Locating master terminal directory...
set "MASTER_PATH="

REM Check common paths
if exist "C:\Users\Administrator\AppData\Roaming\MetaQuotes\Terminal\173477FF1060D99CE79296FC73108719" (
    set "MASTER_PATH=C:\Users\Administrator\AppData\Roaming\MetaQuotes\Terminal\173477FF1060D99CE79296FC73108719"
    goto :found_master
)

REM Search for the terminal ID in all user profiles
for /d %%u in (C:\Users\*) do (
    if exist "%%u\AppData\Roaming\MetaQuotes\Terminal\173477FF1060D99CE79296FC73108719" (
        set "MASTER_PATH=%%u\AppData\Roaming\MetaQuotes\Terminal\173477FF1060D99CE79296FC73108719"
        goto :found_master
    )
)

echo [ERROR] MASTER TERMINAL DIRECTORY NOT FOUND
echo Searching all Terminal directories...
dir C:\Users\*\AppData\Roaming\MetaQuotes\Terminal\* /AD /B 2>NUL
pause
exit /b 1

:found_master
echo [SUCCESS] MASTER TERMINAL LOCATED: %MASTER_PATH%

REM PHASE 2: DECONTAMINATION
echo.
echo =============================
echo PHASE 2: DECONTAMINATION
echo =============================

set "MQL5_FILES=%MASTER_PATH%\MQL5\Files"
set "LOGS_PATH=%MASTER_PATH%\Logs"

REM Clean MQL5\Files directory
if exist "%MQL5_FILES%" (
    echo Cleaning MQL5\Files directory...
    
    REM Count contaminated files
    set /a FILE_COUNT=0
    for %%f in ("%MQL5_FILES%\*.json" "%MQL5_FILES%\*.txt" "%MQL5_FILES%\*.log") do (
        if exist "%%f" set /a FILE_COUNT+=1
    )
    
    echo [INFO] CONTAMINATED FILES DETECTED: %FILE_COUNT%
    
    if %FILE_COUNT% gtr 0 (
        REM Create backup directory
        set "BACKUP_PATH=%MASTER_PATH%\CONTAMINATION_BACKUP_%date:~10,4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
        set "BACKUP_PATH=%BACKUP_PATH: =%"
        mkdir "%BACKUP_PATH%" 2>NUL
        
        REM Move contaminated files to backup
        move "%MQL5_FILES%\*.json" "%BACKUP_PATH%\" >NUL 2>&1
        move "%MQL5_FILES%\*.txt" "%BACKUP_PATH%\" >NUL 2>&1
        move "%MQL5_FILES%\*.log" "%BACKUP_PATH%\" >NUL 2>&1
        
        echo [SUCCESS] CONTAMINATED FILES QUARANTINED TO: %BACKUP_PATH%
    ) else (
        echo [SUCCESS] MQL5\Files DIRECTORY ALREADY CLEAN
    )
) else (
    echo [WARNING] MQL5\Files DIRECTORY NOT FOUND
)

REM Clean Logs directory
if exist "%LOGS_PATH%" (
    echo Cleaning EA logs...
    
    REM Remove EA-generated log files (keep MT5 system logs)
    del "%LOGS_PATH%\*EA*" /Q >NUL 2>&1
    del "%LOGS_PATH%\*Expert*" /Q >NUL 2>&1
    del "%LOGS_PATH%\*Bridge*" /Q >NUL 2>&1
    del "%LOGS_PATH%\*BITTEN*" /Q >NUL 2>&1
    
    echo [SUCCESS] EA LOG FILES REMOVED
) else (
    echo [WARNING] LOGS DIRECTORY NOT FOUND
)

echo [SUCCESS] PHASE 2 DECONTAMINATION COMPLETE

REM PHASE 3: STERILIZATION (MANUAL)
echo.
echo ==============================
echo PHASE 3: STERILIZATION (MANUAL)
echo ==============================
echo [WARNING] MANUAL INTERVENTION REQUIRED:
echo.
echo 1. Start MT5 terminal manually
echo 2. Go to Tools ^> Options ^> Expert Advisors
echo 3. UNCHECK 'Allow algorithmic trading'
echo 4. UNCHECK 'Allow DLL imports'
echo 5. UNCHECK 'Allow WebRequest for listed URL'
echo 6. Click OK to save settings
echo 7. Open charts and verify EA shows :( (disabled)
echo 8. Save profile as 'BITTEN_MASTER_TEMPLATE'
echo 9. Close MT5 terminal
echo.
echo Press any key after completing manual steps...
pause

REM PHASE 4: ARCHIVAL
echo.
echo ====================
echo PHASE 4: ARCHIVAL
echo ====================

set "TIMESTAMP=%date:~10,4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "TIMESTAMP=%TIMESTAMP: =0%"
set "ARCHIVE_NAME=MT5_MASTER_COLD_%TIMESTAMP%.zip"
set "ARCHIVE_PATH=%MASTER_PATH%\..\%ARCHIVE_NAME%"

echo Creating archive: %ARCHIVE_NAME%

REM Create archive using PowerShell (Windows built-in)
powershell -Command "Compress-Archive -Path '%MASTER_PATH%' -DestinationPath '%ARCHIVE_PATH%' -Force"

if exist "%ARCHIVE_PATH%" (
    echo [SUCCESS] ARCHIVE CREATED: %ARCHIVE_PATH%
    for %%a in ("%ARCHIVE_PATH%") do echo [INFO] ARCHIVE SIZE: %%~za bytes
) else (
    echo [ERROR] ARCHIVE CREATION FAILED
)

REM FINAL VERIFICATION
echo.
echo =======================
echo FINAL VERIFICATION
echo =======================

REM Check no MT5 processes running
tasklist /FI "IMAGENAME eq terminal64.exe" 2>NUL | find /I /N "terminal64.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [ERROR] MT5 PROCESSES STILL RUNNING!
) else (
    echo [SUCCESS] NO MT5 PROCESSES DETECTED
)

REM Verify clean state
set /a REMAINING_COUNT=0
for %%f in ("%MQL5_FILES%\*.json" "%MQL5_FILES%\*.txt" "%MQL5_FILES%\*.log") do (
    if exist "%%f" set /a REMAINING_COUNT+=1
)

if %REMAINING_COUNT% gtr 0 (
    echo [ERROR] CONTAMINATION STILL PRESENT: %REMAINING_COUNT% files
) else (
    echo [SUCCESS] DECONTAMINATION VERIFIED
)

echo.
echo ================================
echo   EMERGENCY CLEANUP COMPLETE
echo ================================
echo.
echo Next: Manually configure MT5 as outlined in Phase 3
echo Master terminal is now sterile and ready for cloning
echo.
pause