# PowerShell script to test fire.txt in MT5
# This script creates a test signal in the correct location

# Find MT5 data folder
$mt5DataPath = "$env:APPDATA\MetaQuotes\Terminal"

if (Test-Path $mt5DataPath) {
    Write-Host "✅ Found MetaQuotes folder" -ForegroundColor Green
    
    # List all terminal folders
    $terminals = Get-ChildItem -Path $mt5DataPath -Directory
    
    if ($terminals.Count -eq 0) {
        Write-Host "❌ No MT5 terminals found" -ForegroundColor Red
        exit
    }
    
    Write-Host "`n📂 Found MT5 terminals:" -ForegroundColor Cyan
    $terminals | ForEach-Object { Write-Host "  - $($_.Name)" }
    
    # For each terminal, create test signal
    foreach ($terminal in $terminals) {
        $filesPath = Join-Path $terminal.FullName "MQL5\Files"
        $bittenPath = Join-Path $filesPath "BITTEN"
        $firePath = Join-Path $bittenPath "fire.txt"
        
        Write-Host "`n🔧 Processing terminal: $($terminal.Name)" -ForegroundColor Yellow
        
        # Create BITTEN directory if it doesn't exist
        if (-not (Test-Path $bittenPath)) {
            New-Item -ItemType Directory -Path $bittenPath -Force | Out-Null
            Write-Host "  ✅ Created BITTEN folder" -ForegroundColor Green
        } else {
            Write-Host "  ✅ BITTEN folder exists" -ForegroundColor Green
        }
        
        # Create test signal
        $testSignal = @{
            signal_id = "TEST_$(Get-Date -Format 'yyyyMMddHHmmss')"
            symbol = "EURUSD"
            type = "buy"
            lot = 0.01
            sl = 50
            tp = 100
            comment = "PowerShell test signal"
        } | ConvertTo-Json -Compress
        
        # Write to fire.txt
        $testSignal | Set-Content -Path $firePath -Encoding UTF8
        Write-Host "  ✅ Created fire.txt with test signal" -ForegroundColor Green
        Write-Host "  📄 Path: $firePath" -ForegroundColor Gray
        Write-Host "  📄 Content: $testSignal" -ForegroundColor Gray
        
        # Also try root Files folder (without BITTEN)
        $rootFirePath = Join-Path $filesPath "fire.txt"
        $testSignal | Set-Content -Path $rootFirePath -Encoding UTF8
        Write-Host "  ✅ Also created in root: $rootFirePath" -ForegroundColor Green
    }
    
    Write-Host "`n✅ Test signals created!" -ForegroundColor Green
    Write-Host "👀 Now check the Experts tab in MT5" -ForegroundColor Cyan
    Write-Host "🔍 Look for 'SIGNAL FOUND' message" -ForegroundColor Cyan
    
} else {
    Write-Host "❌ MetaQuotes folder not found at: $mt5DataPath" -ForegroundColor Red
    Write-Host "Make sure MT5 is installed and has been run at least once" -ForegroundColor Yellow
}