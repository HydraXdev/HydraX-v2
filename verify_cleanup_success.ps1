# MT5 MASTER CLEANUP VERIFICATION SCRIPT
# Confirms successful decontamination and sterile state

Write-Host "🔍 MT5 MASTER CLEANUP VERIFICATION" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Timestamp: $(Get-Date)" -ForegroundColor Yellow
Write-Host ""

$script:issues = @()
$script:warnings = @()
$script:successes = @()

function Add-Issue($message) {
    $script:issues += $message
    Write-Host "❌ ISSUE: $message" -ForegroundColor Red
}

function Add-Warning($message) {
    $script:warnings += $message
    Write-Host "⚠️ WARNING: $message" -ForegroundColor Yellow
}

function Add-Success($message) {
    $script:successes += $message
    Write-Host "✅ SUCCESS: $message" -ForegroundColor Green
}

# VERIFICATION 1: No MT5 Processes Running
Write-Host "1. Checking for running MT5 processes..." -ForegroundColor White
$mt5Processes = Get-Process -Name "terminal64" -ErrorAction SilentlyContinue
if ($mt5Processes) {
    Add-Issue "MT5 processes still running: $($mt5Processes.Count) instances"
    $mt5Processes | Format-Table Id, ProcessName, StartTime
} else {
    Add-Success "No MT5 processes detected"
}

# VERIFICATION 2: Locate Master Terminal
Write-Host "`n2. Locating master terminal directory..." -ForegroundColor White
$terminalId = "173477FF1060D99CE79296FC73108719"
$commonPaths = @(
    "C:\Users\Administrator\AppData\Roaming\MetaQuotes\Terminal\$terminalId",
    "C:\Users\*\AppData\Roaming\MetaQuotes\Terminal\$terminalId"
)

$masterPath = $null
foreach ($path in $commonPaths) {
    $resolved = Get-ChildItem $path -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($resolved) {
        $masterPath = $resolved.FullName
        break
    }
}

if (-not $masterPath) {
    Add-Issue "Master terminal directory not found for ID: $terminalId"
    Write-Host "Searching all terminals..." -ForegroundColor Yellow
    Get-ChildItem "C:\Users\*\AppData\Roaming\MetaQuotes\Terminal\*" -Directory -ErrorAction SilentlyContinue | 
        Format-Table Name, FullName
} else {
    Add-Success "Master terminal located: $masterPath"
}

if ($masterPath) {
    # VERIFICATION 3: Check MQL5\Files Contamination
    Write-Host "`n3. Checking MQL5\Files for contamination..." -ForegroundColor White
    $mql5FilesPath = Join-Path $masterPath "MQL5\Files"
    
    if (Test-Path $mql5FilesPath) {
        $contaminatedFiles = @()
        $contaminatedFiles += Get-ChildItem $mql5FilesPath -Filter "*.json" -File -ErrorAction SilentlyContinue
        $contaminatedFiles += Get-ChildItem $mql5FilesPath -Filter "*.txt" -File -ErrorAction SilentlyContinue
        $contaminatedFiles += Get-ChildItem $mql5FilesPath -Filter "*.log" -File -ErrorAction SilentlyContinue
        
        if ($contaminatedFiles.Count -gt 0) {
            Add-Issue "Contaminated files still present: $($contaminatedFiles.Count) files"
            $contaminatedFiles | Format-Table Name, Length, LastWriteTime
        } else {
            Add-Success "MQL5\Files directory is clean"
        }
    } else {
        Add-Warning "MQL5\Files directory not found"
    }
    
    # VERIFICATION 4: Check Logs Directory
    Write-Host "`n4. Checking Logs directory..." -ForegroundColor White
    $logsPath = Join-Path $masterPath "Logs"
    
    if (Test-Path $logsPath) {
        $eaLogPattern = "*EA*", "*Expert*", "*Bridge*", "*BITTEN*"
        $eaLogs = Get-ChildItem $logsPath -File | Where-Object { 
            $name = $_.Name
            $eaLogPattern | ForEach-Object { if ($name -like $_) { return $true } }
        }
        
        if ($eaLogs) {
            Add-Warning "EA log files still present: $($eaLogs.Count) files"
            $eaLogs | Format-Table Name, Length, LastWriteTime
        } else {
            Add-Success "No EA log files found"
        }
    } else {
        Add-Warning "Logs directory not found"
    }
    
    # VERIFICATION 5: Check for Backup Directory
    Write-Host "`n5. Checking for contamination backup..." -ForegroundColor White
    $backupDirs = Get-ChildItem $masterPath -Directory | Where-Object { $_.Name -like "CONTAMINATION_BACKUP_*" }
    
    if ($backupDirs) {
        Add-Success "Contamination backup found: $($backupDirs.Count) backup(s)"
        $backupDirs | ForEach-Object {
            $backupSize = (Get-ChildItem $_.FullName -Recurse -File | Measure-Object -Property Length -Sum).Sum
            Write-Host "  📦 $($_.Name) - Size: $([math]::Round($backupSize / 1KB, 2)) KB" -ForegroundColor Cyan
        }
    } else {
        Add-Warning "No contamination backup found (files may have been deleted instead of moved)"
    }
    
    # VERIFICATION 6: Check for Archive
    Write-Host "`n6. Checking for master template archive..." -ForegroundColor White
    $parentPath = Split-Path $masterPath -Parent
    $archives = Get-ChildItem $parentPath -Filter "MT5_MASTER_COLD_*.zip" -File -ErrorAction SilentlyContinue
    
    if ($archives) {
        Add-Success "Master template archive found: $($archives.Count) archive(s)"
        $archives | ForEach-Object {
            Write-Host "  📦 $($_.Name) - Size: $([math]::Round($_.Length / 1MB, 2)) MB - Created: $($_.CreationTime)" -ForegroundColor Cyan
        }
    } else {
        Add-Warning "No master template archive found"
    }
    
    # VERIFICATION 7: Configuration Check (Requires Manual Verification)
    Write-Host "`n7. Configuration verification (manual check required)..." -ForegroundColor White
    Write-Host "  Manual verification needed:" -ForegroundColor Yellow
    Write-Host "  - Start MT5 terminal" -ForegroundColor Yellow
    Write-Host "  - Check Tools > Options > Expert Advisors" -ForegroundColor Yellow
    Write-Host "  - Verify 'Allow algorithmic trading' is UNCHECKED" -ForegroundColor Yellow
    Write-Host "  - Verify EAs show 😞 (disabled) on charts" -ForegroundColor Yellow
    Write-Host "  - Verify profile saved as 'BITTEN_MASTER_TEMPLATE'" -ForegroundColor Yellow
}

# FINAL REPORT
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "           VERIFICATION REPORT" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`n✅ SUCCESSES ($($script:successes.Count)):" -ForegroundColor Green
$script:successes | ForEach-Object { Write-Host "  • $_" -ForegroundColor Green }

if ($script:warnings.Count -gt 0) {
    Write-Host "`n⚠️ WARNINGS ($($script:warnings.Count)):" -ForegroundColor Yellow
    $script:warnings | ForEach-Object { Write-Host "  • $_" -ForegroundColor Yellow }
}

if ($script:issues.Count -gt 0) {
    Write-Host "`n❌ CRITICAL ISSUES ($($script:issues.Count)):" -ForegroundColor Red
    $script:issues | ForEach-Object { Write-Host "  • $_" -ForegroundColor Red }
    Write-Host "`n🚨 CLEANUP INCOMPLETE - REMEDIATION REQUIRED" -ForegroundColor Red
    exit 1
} else {
    Write-Host "`n🎯 CLEANUP VERIFICATION: SUCCESSFUL" -ForegroundColor Green
    Write-Host "Master terminal is sterile and ready for cloning" -ForegroundColor Green
    
    if ($script:warnings.Count -eq 0) {
        Write-Host "🏆 PERFECT CLEANUP - NO ISSUES DETECTED" -ForegroundColor Green
    } else {
        Write-Host "✅ CLEANUP SUCCESSFUL - MINOR WARNINGS NOTED" -ForegroundColor Yellow
    }
}

Write-Host "`nVerification completed at: $(Get-Date)" -ForegroundColor Cyan