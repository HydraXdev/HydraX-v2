# EMERGENCY MT5 MASTER TERMINAL CLEANUP AGENT
# Target: Windows Server 3.145.84.187
# Terminal ID: 173477FF1060D99CE79296FC73108719
# CRITICAL: Execute with administrator privileges

Write-Host "🚨 EMERGENCY MT5 MASTER CLEANUP INITIATED" -ForegroundColor Red
Write-Host "Timestamp: $(Get-Date)" -ForegroundColor Yellow

# PHASE 1: IMMEDIATE SHUTDOWN
Write-Host "`n=== PHASE 1: IMMEDIATE SHUTDOWN ===" -ForegroundColor Cyan

# Check for running MT5 processes
$mt5Processes = Get-Process -Name "terminal64" -ErrorAction SilentlyContinue
if ($mt5Processes) {
    Write-Host "⚠️ ACTIVE MT5 PROCESSES DETECTED:" -ForegroundColor Red
    $mt5Processes | Format-Table Id, ProcessName, StartTime
    
    Write-Host "🛑 TERMINATING MT5 PROCESSES..." -ForegroundColor Red
    $mt5Processes | Stop-Process -Force
    Start-Sleep -Seconds 3
    
    # Verify termination
    $remainingProcesses = Get-Process -Name "terminal64" -ErrorAction SilentlyContinue
    if ($remainingProcesses) {
        Write-Host "❌ FAILED TO TERMINATE ALL PROCESSES" -ForegroundColor Red
        exit 1
    } else {
        Write-Host "✅ ALL MT5 PROCESSES TERMINATED" -ForegroundColor Green
    }
} else {
    Write-Host "✅ NO ACTIVE MT5 PROCESSES FOUND" -ForegroundColor Green
}

# Locate master terminal directory
$commonPaths = @(
    "C:\Program Files\MetaTrader 5",
    "C:\Users\Administrator\AppData\Roaming\MetaQuotes\Terminal\173477FF1060D99CE79296FC73108719",
    "C:\Users\Administrator\AppData\Roaming\MetaQuotes\Terminal\*"
)

$masterTerminalPath = $null
foreach ($path in $commonPaths) {
    if (Test-Path $path) {
        if ($path -like "*173477FF1060D99CE79296FC73108719*") {
            $masterTerminalPath = $path
            break
        } elseif ($path -like "*Terminal\*") {
            # Search for terminal with specific ID
            $terminals = Get-ChildItem $path -Directory | Where-Object { $_.Name -eq "173477FF1060D99CE79296FC73108719" }
            if ($terminals) {
                $masterTerminalPath = $terminals[0].FullName
                break
            }
        }
    }
}

if (-not $masterTerminalPath) {
    Write-Host "❌ MASTER TERMINAL DIRECTORY NOT FOUND" -ForegroundColor Red
    Write-Host "Searching all Terminal directories..." -ForegroundColor Yellow
    $allTerminals = Get-ChildItem "C:\Users\*\AppData\Roaming\MetaQuotes\Terminal\*" -Directory -ErrorAction SilentlyContinue
    $allTerminals | Format-Table Name, FullName
    exit 1
}

Write-Host "✅ MASTER TERMINAL LOCATED: $masterTerminalPath" -ForegroundColor Green

# PHASE 2: DECONTAMINATION
Write-Host "`n=== PHASE 2: DECONTAMINATION ===" -ForegroundColor Cyan

$mql5FilesPath = Join-Path $masterTerminalPath "MQL5\Files"
$logsPath = Join-Path $masterTerminalPath "Logs"

# Clean MQL5\Files directory
if (Test-Path $mql5FilesPath) {
    Write-Host "🧹 CLEANING MQL5\Files DIRECTORY..." -ForegroundColor Yellow
    
    # Count contaminated files before cleanup
    $jsonFiles = Get-ChildItem $mql5FilesPath -Filter "*.json" -File
    $txtFiles = Get-ChildItem $mql5FilesPath -Filter "*.txt" -File
    $logFiles = Get-ChildItem $mql5FilesPath -Filter "*.log" -File
    
    $totalContaminated = $jsonFiles.Count + $txtFiles.Count + $logFiles.Count
    Write-Host "📊 CONTAMINATED FILES DETECTED: $totalContaminated" -ForegroundColor Red
    
    if ($totalContaminated -gt 0) {
        # Backup contaminated files before deletion
        $backupPath = Join-Path $masterTerminalPath "CONTAMINATION_BACKUP_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        New-Item -ItemType Directory -Path $backupPath -Force | Out-Null
        
        # Move contaminated files to backup
        $jsonFiles | Move-Item -Destination $backupPath -Force
        $txtFiles | Move-Item -Destination $backupPath -Force
        $logFiles | Move-Item -Destination $backupPath -Force
        
        Write-Host "✅ CONTAMINATED FILES QUARANTINED TO: $backupPath" -ForegroundColor Green
    } else {
        Write-Host "✅ MQL5\Files DIRECTORY ALREADY CLEAN" -ForegroundColor Green
    }
} else {
    Write-Host "⚠️ MQL5\Files DIRECTORY NOT FOUND" -ForegroundColor Yellow
}

# Clean Logs directory
if (Test-Path $logsPath) {
    Write-Host "🧹 CLEANING LOGS DIRECTORY..." -ForegroundColor Yellow
    
    # Remove EA-generated log files (keep MT5 system logs)
    $eaLogPattern = "*EA*", "*Expert*", "*Bridge*", "*BITTEN*"
    $eaLogs = Get-ChildItem $logsPath -File | Where-Object { 
        $name = $_.Name
        $eaLogPattern | ForEach-Object { if ($name -like $_) { return $true } }
    }
    
    if ($eaLogs) {
        $eaLogs | Remove-Item -Force
        Write-Host "✅ EA LOG FILES REMOVED: $($eaLogs.Count)" -ForegroundColor Green
    } else {
        Write-Host "✅ NO EA LOG FILES FOUND" -ForegroundColor Green
    }
} else {
    Write-Host "⚠️ LOGS DIRECTORY NOT FOUND" -ForegroundColor Yellow
}

Write-Host "✅ PHASE 2 DECONTAMINATION COMPLETE" -ForegroundColor Green

# PHASE 3: STERILIZATION
Write-Host "`n=== PHASE 3: STERILIZATION ===" -ForegroundColor Cyan
Write-Host "⚠️ MANUAL INTERVENTION REQUIRED:" -ForegroundColor Yellow
Write-Host "1. Start MT5 terminal manually" -ForegroundColor White
Write-Host "2. Go to Tools > Options > Expert Advisors" -ForegroundColor White
Write-Host "3. UNCHECK 'Allow algorithmic trading'" -ForegroundColor White
Write-Host "4. UNCHECK 'Allow DLL imports'" -ForegroundColor White
Write-Host "5. UNCHECK 'Allow WebRequest for listed URL'" -ForegroundColor White
Write-Host "6. Click OK to save settings" -ForegroundColor White
Write-Host "7. Open charts and verify EA shows 😞 (disabled)" -ForegroundColor White
Write-Host "8. Save profile as 'BITTEN_MASTER_TEMPLATE'" -ForegroundColor White
Write-Host "9. Close MT5 terminal" -ForegroundColor White

# PHASE 4: ARCHIVAL
Write-Host "`n=== PHASE 4: ARCHIVAL ===" -ForegroundColor Cyan

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$archiveName = "MT5_MASTER_COLD_$timestamp.zip"
$archivePath = Join-Path (Split-Path $masterTerminalPath -Parent) $archiveName

Write-Host "📦 CREATING ARCHIVE: $archiveName" -ForegroundColor Yellow

try {
    # Create archive of cleaned master terminal
    Compress-Archive -Path $masterTerminalPath -DestinationPath $archivePath -Force
    Write-Host "✅ ARCHIVE CREATED: $archivePath" -ForegroundColor Green
    
    # Verify archive
    $archiveInfo = Get-Item $archivePath
    Write-Host "📊 ARCHIVE SIZE: $([math]::Round($archiveInfo.Length / 1MB, 2)) MB" -ForegroundColor Green
    
} catch {
    Write-Host "❌ ARCHIVE CREATION FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# FINAL VERIFICATION
Write-Host "`n=== FINAL VERIFICATION ===" -ForegroundColor Cyan

# Check no MT5 processes running
$finalCheck = Get-Process -Name "terminal64" -ErrorAction SilentlyContinue
if ($finalCheck) {
    Write-Host "❌ MT5 PROCESSES STILL RUNNING!" -ForegroundColor Red
} else {
    Write-Host "✅ NO MT5 PROCESSES DETECTED" -ForegroundColor Green
}

# Verify clean state
$remainingContamination = Get-ChildItem $mql5FilesPath -Include "*.json", "*.txt", "*.log" -File -ErrorAction SilentlyContinue
if ($remainingContamination) {
    Write-Host "❌ CONTAMINATION STILL PRESENT: $($remainingContamination.Count) files" -ForegroundColor Red
} else {
    Write-Host "✅ DECONTAMINATION VERIFIED" -ForegroundColor Green
}

Write-Host "`n🎯 EMERGENCY CLEANUP COMPLETE" -ForegroundColor Green
Write-Host "Next: Manually configure MT5 as outlined in Phase 3" -ForegroundColor Yellow
Write-Host "Master terminal is now sterile and ready for cloning" -ForegroundColor Green