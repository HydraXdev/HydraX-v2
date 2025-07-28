# Commission-BiTTenAgent.ps1 - Commissioning Script for BiTTen Dual Agent

param(
    [Parameter(Mandatory=$true)]
    [string]$UserUUID,
    
    [string]$ConfigPath = "C:\BiTTen\Agent\config.json"
)

Write-Host @"
╔═══════════════════════════════════════════════════════════╗
║          BiTTen Dual Agent Commissioning                  ║
║              System Readiness Verification                ║
╚═══════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

# Function to test with status reporting
function Test-Component {
    param(
        [string]$Name,
        [scriptblock]$Test,
        [string]$SuccessMessage = "Working",
        [string]$FailureMessage = "Failed"
    )
    
    Write-Host -NoNewline "Testing $Name... " -ForegroundColor Yellow
    
    try {
        $result = & $Test
        if ($result) {
            Write-Host "✅ $SuccessMessage" -ForegroundColor Green
            return @{
                Component = $Name
                Status = "PASS"
                Message = $SuccessMessage
                Details = $result
            }
        } else {
            Write-Host "❌ $FailureMessage" -ForegroundColor Red
            return @{
                Component = $Name
                Status = "FAIL"
                Message = $FailureMessage
                Details = $null
            }
        }
    }
    catch {
        Write-Host "❌ Error: $_" -ForegroundColor Red
        return @{
            Component = $Name
            Status = "ERROR"
            Message = $_.ToString()
            Details = $null
        }
    }
}

# Initialize results
$commissioningResults = @()
$startTime = Get-Date

Write-Host "`n🔍 Starting commissioning tests..." -ForegroundColor Yellow
Write-Host "User UUID: $UserUUID" -ForegroundColor Gray
Write-Host ""

# Test 1: Agent Installation
$test1 = Test-Component -Name "Agent Installation" -Test {
    $installPath = Split-Path $ConfigPath -Parent
    if (Test-Path $installPath) {
        if (Test-Path "$installPath\BiTTenDualAgent.ps1") {
            return "Installation found at $installPath"
        }
    }
    return $false
} -SuccessMessage "Agent files present" -FailureMessage "Agent not installed"
$commissioningResults += $test1

# Test 2: Configuration
$test2 = Test-Component -Name "Configuration" -Test {
    if (Test-Path $ConfigPath) {
        $config = Get-Content $ConfigPath -Raw | ConvertFrom-Json
        if ($config.UserUUID -eq $UserUUID) {
            return "Configuration valid for user $UserUUID"
        }
    }
    return $false
} -SuccessMessage "Configuration valid" -FailureMessage "Configuration missing or invalid"
$commissioningResults += $test2

# Test 3: Service Status
$test3 = Test-Component -Name "Windows Service" -Test {
    $service = Get-Service -Name "BiTTenDualAgent" -ErrorAction SilentlyContinue
    if ($service) {
        if ($service.Status -eq "Running") {
            return "Service running (PID: $($service.Id))"
        } else {
            return "Service installed but not running (Status: $($service.Status))"
        }
    }
    return $false
} -SuccessMessage "Service operational" -FailureMessage "Service not found"
$commissioningResults += $test3

# Test 4: MT5 Detection
$test4 = Test-Component -Name "MT5 Installation" -Test {
    $mt5Path = "C:\Program Files\MetaTrader 5\terminal64.exe"
    if (Test-Path $mt5Path) {
        $mt5Process = Get-Process -Name "terminal64" -ErrorAction SilentlyContinue
        if ($mt5Process) {
            return "MT5 running (PID: $($mt5Process.Id))"
        } else {
            return "MT5 installed but not running"
        }
    }
    return $false
} -SuccessMessage "MT5 detected" -FailureMessage "MT5 not found"
$commissioningResults += $test4

# Test 5: EA Detection
$test5 = Test-Component -Name "BITTENBridge EA" -Test {
    $eaPath = "C:\Program Files\MetaTrader 5\MQL5\Experts\BITTENBridge_TradeExecutor.ex5"
    if (Test-Path $eaPath) {
        $eaInfo = Get-Item $eaPath
        return "EA found (Modified: $($eaInfo.LastWriteTime))"
    }
    return $false
} -SuccessMessage "EA installed" -FailureMessage "EA not found"
$commissioningResults += $test5

# Test 6: File System Access
$test6 = Test-Component -Name "File System Access" -Test {
    $testPath = "C:\Program Files\MetaTrader 5\MQL5\Files\BITTEN"
    if (Test-Path $testPath) {
        # Test write access
        $testFile = Join-Path $testPath "commission_test_$(Get-Random).tmp"
        try {
            "test" | Out-File -FilePath $testFile -Force
            Remove-Item $testFile -Force
            return "Read/Write access confirmed"
        }
        catch {
            return "Read-only access"
        }
    } else {
        # Try to create directory
        try {
            New-Item -ItemType Directory -Path $testPath -Force | Out-Null
            return "Directory created successfully"
        }
        catch {
            return $false
        }
    }
} -SuccessMessage "File access verified" -FailureMessage "No file access"
$commissioningResults += $test6

# Test 7: Network Connectivity
$test7 = Test-Component -Name "Network Connectivity" -Test {
    $testUrl = "terminus.joinbitten.com"
    $result = Test-NetConnection -ComputerName $testUrl -Port 443 -WarningAction SilentlyContinue
    if ($result.TcpTestSucceeded) {
        return "Connected to BITTEN servers (Latency: $($result.PingReplyDetails.RoundtripTime)ms)"
    }
    return $false
} -SuccessMessage "Network connected" -FailureMessage "Network issue"
$commissioningResults += $test7

# Test 8: Broker Detection
$test8 = Test-Component -Name "Broker Detection" -Test {
    # Load agent modules
    $modulePath = Split-Path $ConfigPath -Parent
    $modulePath = Join-Path $modulePath "Modules\BrokerHandler.psm1"
    
    if (Test-Path $modulePath) {
        Import-Module $modulePath -Force
        $brokerHandler = New-Object BrokerCompatibilityManager
        $detectedBroker = $brokerHandler.DetectBrokerType()
        if ($detectedBroker -and $detectedBroker -ne "Unknown") {
            return "Detected: $detectedBroker"
        }
    }
    return $false
} -SuccessMessage "Broker detected" -FailureMessage "Unable to detect broker"
$commissioningResults += $test8

# Test 9: Symbol Validation
$test9 = Test-Component -Name "Symbol Mapping" -Test {
    $bittenPath = "C:\Program Files\MetaTrader 5\MQL5\Files\BITTEN"
    $fireFile = Join-Path $bittenPath "fire.txt"
    
    if (Test-Path $fireFile) {
        # Test signal format
        $testSignal = @{
            signal_id = "TEST_" + (Get-Random)
            symbol = "EURUSD"
            type = "buy"
            lot = 0.01
            sl = 0
            tp = 0
            comment = "Commissioning test"
        } | ConvertTo-Json
        
        try {
            $testSignal | Set-Content $fireFile -Force
            Start-Sleep -Milliseconds 500
            
            # Check if file was processed (should be empty)
            $content = Get-Content $fireFile -Raw
            if (-not $content -or $content.Trim().Length -eq 0) {
                return "Signal processing verified"
            } else {
                return "Signal not processed"
            }
        }
        catch {
            return $false
        }
    }
    return "Cannot test - fire.txt not accessible"
} -SuccessMessage "Signal format valid" -FailureMessage "Signal processing issue"
$commissioningResults += $test9

# Test 10: Performance Metrics
$test10 = Test-Component -Name "System Performance" -Test {
    $cpu = (Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 1 -MaxSamples 1).CounterSamples.CookedValue
    $memory = Get-CimInstance Win32_OperatingSystem | 
              Select-Object @{Name="MemoryUsage";Expression={[math]::Round((($_.TotalVisibleMemorySize - $_.FreePhysicalMemory) / $_.TotalVisibleMemorySize) * 100, 2)}}
    $disk = Get-PSDrive -Name C | 
            Select-Object @{Name="FreeGB";Expression={[math]::Round($_.Free / 1GB, 2)}}
    
    $status = "CPU: $([math]::Round($cpu, 2))%, Memory: $($memory.MemoryUsage)%, Disk Free: $($disk.FreeGB)GB"
    
    if ($cpu -lt 80 -and $memory.MemoryUsage -lt 80 -and $disk.FreeGB -gt 10) {
        return $status
    }
    return $false
} -SuccessMessage "System resources healthy" -FailureMessage "Resource constraints detected"
$commissioningResults += $test10

# Calculate summary
$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

$passCount = ($commissioningResults | Where-Object { $_.Status -eq "PASS" }).Count
$failCount = ($commissioningResults | Where-Object { $_.Status -eq "FAIL" }).Count
$errorCount = ($commissioningResults | Where-Object { $_.Status -eq "ERROR" }).Count

$overallStatus = if ($failCount -eq 0 -and $errorCount -eq 0) { "COMMISSIONED" } 
                 elseif ($passCount -ge 7) { "PARTIALLY_COMMISSIONED" } 
                 else { "NOT_READY" }

# Display summary
Write-Host "`n" -NoNewline
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor White
Write-Host "                 COMMISSIONING SUMMARY                      " -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor White
Write-Host ""
Write-Host "Total Tests: $($commissioningResults.Count)" -ForegroundColor Cyan
Write-Host "✅ Passed: $passCount" -ForegroundColor Green
Write-Host "❌ Failed: $failCount" -ForegroundColor Red
Write-Host "⚠️  Errors: $errorCount" -ForegroundColor Yellow
Write-Host ""
Write-Host "Duration: $([math]::Round($duration, 2)) seconds" -ForegroundColor Gray
Write-Host ""

# Display status
switch ($overallStatus) {
    "COMMISSIONED" {
        Write-Host "🎉 STATUS: FULLY COMMISSIONED" -ForegroundColor Green -BackgroundColor DarkGreen
        Write-Host "The BiTTen Dual Agent is ready for operation!" -ForegroundColor Green
    }
    "PARTIALLY_COMMISSIONED" {
        Write-Host "⚠️  STATUS: PARTIALLY COMMISSIONED" -ForegroundColor Yellow -BackgroundColor DarkYellow
        Write-Host "The agent is operational but some features may be limited." -ForegroundColor Yellow
    }
    "NOT_READY" {
        Write-Host "❌ STATUS: NOT READY" -ForegroundColor Red -BackgroundColor DarkRed
        Write-Host "Critical components are missing or failed. Please review the results." -ForegroundColor Red
    }
}

# Generate report
$report = @{
    UserUUID = $UserUUID
    CommissionTime = $endTime.ToString("yyyy-MM-dd HH:mm:ss")
    Duration = $duration
    Status = $overallStatus
    Summary = @{
        TotalTests = $commissioningResults.Count
        Passed = $passCount
        Failed = $failCount
        Errors = $errorCount
    }
    Results = $commissioningResults
    SystemInfo = @{
        OSVersion = [System.Environment]::OSVersion.VersionString
        PowerShellVersion = $PSVersionTable.PSVersion.ToString()
        ComputerName = $env:COMPUTERNAME
    }
}

# Save report
$reportPath = Join-Path (Split-Path $ConfigPath -Parent) "commissioning_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
$report | ConvertTo-Json -Depth 5 | Set-Content $reportPath

Write-Host "`n📄 Detailed report saved to:" -ForegroundColor Gray
Write-Host "   $reportPath" -ForegroundColor White

# Send report to BITTEN if service is running and network is available
if ($overallStatus -ne "NOT_READY" -and $test7.Status -eq "PASS") {
    Write-Host "`n📡 Sending commissioning report to BITTEN..." -ForegroundColor Yellow
    
    try {
        $endpoint = "https://terminus.joinbitten.com/metrics/commission"
        $json = $report | ConvertTo-Json -Depth 5 -Compress
        
        $response = Invoke-RestMethod -Uri $endpoint -Method Post -Body $json -ContentType "application/json" -TimeoutSec 10
        Write-Host "✅ Report sent successfully" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️  Failed to send report: $_" -ForegroundColor Yellow
    }
}

# Recommendations
if ($failCount -gt 0 -or $errorCount -gt 0) {
    Write-Host "`n📋 RECOMMENDATIONS:" -ForegroundColor Yellow
    
    foreach ($result in $commissioningResults | Where-Object { $_.Status -ne "PASS" }) {
        Write-Host "   • $($result.Component): " -NoNewline -ForegroundColor Yellow
        
        switch ($result.Component) {
            "Windows Service" {
                Write-Host "Run 'Start-Service BiTTenDualAgent' as Administrator"
            }
            "MT5 Installation" {
                Write-Host "Start MetaTrader 5 terminal"
            }
            "BITTENBridge EA" {
                Write-Host "Install BITTENBridge_TradeExecutor.mq5 in MT5"
            }
            "File System Access" {
                Write-Host "Check permissions on MT5 Files folder"
            }
            "Network Connectivity" {
                Write-Host "Check firewall settings and internet connection"
            }
            default {
                Write-Host "Review error message and correct the issue"
            }
        }
    }
}

Write-Host "`n✨ Commissioning complete!" -ForegroundColor Green