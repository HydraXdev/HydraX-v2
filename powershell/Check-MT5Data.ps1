# PowerShell script to check MT5 data files and EA activity

Write-Host "`n🔍 CHECKING MT5 EA ACTIVITY" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# Find MT5 data folder
$mt5DataPath = "$env:APPDATA\MetaQuotes\Terminal"

if (Test-Path $mt5DataPath) {
    $terminals = Get-ChildItem -Path $mt5DataPath -Directory
    
    foreach ($terminal in $terminals) {
        Write-Host "`n📂 Terminal: $($terminal.Name)" -ForegroundColor Yellow
        
        $filesPath = Join-Path $terminal.FullName "MQL5\Files"
        
        # Check for tick data files
        Write-Host "`n📊 Checking for tick data files:" -ForegroundColor Green
        $tickFiles = Get-ChildItem -Path $filesPath -Filter "tick_data_*.json" -ErrorAction SilentlyContinue
        
        if ($tickFiles) {
            Write-Host "  ✅ Found $($tickFiles.Count) tick data files:" -ForegroundColor Green
            foreach ($file in $tickFiles | Select-Object -First 3) {
                $content = Get-Content $file.FullName -Raw
                Write-Host "  📄 $($file.Name):" -ForegroundColor Gray
                Write-Host "     $content" -ForegroundColor DarkGray
            }
        } else {
            Write-Host "  ❌ No tick data files found" -ForegroundColor Red
        }
        
        # Check BITTEN folder
        $bittenPath = Join-Path $filesPath "BITTEN"
        Write-Host "`n📁 Checking BITTEN folder:" -ForegroundColor Green
        
        if (Test-Path $bittenPath) {
            Write-Host "  ✅ BITTEN folder exists" -ForegroundColor Green
            
            # Check fire.txt
            $firePath = Join-Path $bittenPath "fire.txt"
            if (Test-Path $firePath) {
                $size = (Get-Item $firePath).Length
                Write-Host "  📄 fire.txt exists (size: $size bytes)" -ForegroundColor Cyan
                if ($size -gt 0) {
                    $content = Get-Content $firePath -Raw
                    Write-Host "     Content: $content" -ForegroundColor Yellow
                }
            } else {
                Write-Host "  ❌ fire.txt not found" -ForegroundColor Red
            }
            
            # Check trade_result.txt
            $resultPath = Join-Path $bittenPath "trade_result.txt"
            if (Test-Path $resultPath) {
                $content = Get-Content $resultPath -Raw
                Write-Host "  📄 trade_result.txt: $content" -ForegroundColor Cyan
            }
        } else {
            Write-Host "  ❌ BITTEN folder not found" -ForegroundColor Red
        }
        
        # Check uuid.txt
        $uuidPath = Join-Path $filesPath "uuid.txt"
        if (Test-Path $uuidPath) {
            $uuid = Get-Content $uuidPath -Raw
            Write-Host "`n🆔 UUID: $uuid" -ForegroundColor Magenta
        }
    }
    
} else {
    Write-Host "❌ MetaQuotes folder not found" -ForegroundColor Red
}

Write-Host "`n💡 Debug Tips:" -ForegroundColor Yellow
Write-Host "1. Check MT5 Experts tab for EA messages" -ForegroundColor Gray
Write-Host "2. Look for '✅ Market data sent successfully' messages" -ForegroundColor Gray
Write-Host "3. Check for '❌ WebRequest failed' errors" -ForegroundColor Gray
Write-Host "4. Verify EA shows smiley face on chart" -ForegroundColor Gray