# SystemIntelligence.psm1 - System Monitoring and Intelligence Module

class SystemMonitor {
    [string]$UserUUID
    [hashtable]$Metrics
    [datetime]$LastReport
    [object]$AlertSystem
    [string]$MT5ProcessName = "terminal64"
    [string]$EALogPath = "C:\Program Files\MetaTrader 5\MQL5\Logs"
    
    SystemMonitor([string]$uuid) {
        $this.UserUUID = $uuid
        $this.Metrics = @{}
        $this.LastReport = Get-Date
        $this.InitializeMonitor()
    }
    
    [void] InitializeMonitor() {
        # Initialize baseline metrics
        $this.Metrics = @{
            EA_Status = "INITIALIZING"
            MT5_Status = "CHECKING"
            Signal_Processing = @{
                Processed = 0
                Failed = 0
                SuccessRate = 100
                LastSignal = $null
            }
            HTTP_Streaming = @{
                Status = "CHECKING"
                LastStream = $null
                ErrorCount = 0
            }
            System_Resources = @{
                CPU = 0
                Memory = 0
                DiskFree = 100
            }
        }
    }
    
    # Monitor EA and MT5 performance
    [hashtable] MonitorEAPerformance() {
        return @{
            EA_Status = $this.CheckEAHealth()
            MT5_Status = $this.CheckMT5Connectivity()
            Signal_Processing = $this.CheckSignalFlow()
            HTTP_Streaming = $this.CheckMarketDataFlow()
            File_Communication = $this.CheckFileOperations()
            System_Resources = $this.CheckSystemResources()
        }
    }
    
    # Check EA health status
    [string] CheckEAHealth() {
        try {
            # Check if MT5 process is running
            $mt5Process = Get-Process -Name $this.MT5ProcessName -ErrorAction SilentlyContinue
            if (-not $mt5Process) {
                return "MT5_NOT_RUNNING"
            }
            
            # Check EA log for recent activity
            $latestLog = Get-ChildItem -Path $this.EALogPath -Filter "*.log" | 
                         Sort-Object LastWriteTime -Descending | 
                         Select-Object -First 1
            
            if ($latestLog -and (Get-Date) - $latestLog.LastWriteTime -lt [TimeSpan]::FromMinutes(5)) {
                # Check for EA-specific log entries
                $content = Get-Content $latestLog.FullName -Tail 50
                
                if ($content -match "BITTENBridge.*initialized") {
                    return "HEALTHY"
                }
                elseif ($content -match "error|failed|exception") {
                    return "ERROR_DETECTED"
                }
                else {
                    return "RUNNING"
                }
            }
            else {
                return "NO_RECENT_ACTIVITY"
            }
        }
        catch {
            return "CHECK_FAILED"
        }
    }
    
    # Check MT5 connectivity
    [string] CheckMT5Connectivity() {
        try {
            # Check if terminal.ini exists and is recent
            $terminalConfig = "C:\Program Files\MetaTrader 5\config\terminal.ini"
            if (Test-Path $terminalConfig) {
                $config = Get-Item $terminalConfig
                if ((Get-Date) - $config.LastWriteTime -lt [TimeSpan]::FromMinutes(10)) {
                    return "CONNECTED"
                }
            }
            
            # Check network connectivity
            $testConnection = Test-NetConnection -ComputerName "api.metaquotes.net" -Port 443 -WarningAction SilentlyContinue
            if ($testConnection.TcpTestSucceeded) {
                return "NETWORK_OK"
            }
            else {
                return "NETWORK_ISSUE"
            }
        }
        catch {
            return "CHECK_FAILED"
        }
    }
    
    # Check signal file processing
    [hashtable] CheckSignalFlow() {
        try {
            $signalPath = "C:\Program Files\MetaTrader 5\MQL5\Files\BITTEN"
            $processedPath = Join-Path $signalPath "processed"
            $failedPath = Join-Path $signalPath "failed"
            
            # Count processed signals
            $processedCount = 0
            if (Test-Path $processedPath) {
                $processedCount = (Get-ChildItem -Path $processedPath -Filter "*.json" | Measure-Object).Count
            }
            
            # Count failed signals
            $failedCount = 0
            if (Test-Path $failedPath) {
                $failedCount = (Get-ChildItem -Path $failedPath -Filter "*.json" | Measure-Object).Count
            }
            
            # Get last signal time
            $lastSignal = $null
            $fireFile = Join-Path $signalPath "fire.txt"
            if (Test-Path $fireFile) {
                $lastSignal = (Get-Item $fireFile).LastWriteTime
            }
            
            # Calculate success rate
            $totalSignals = $processedCount + $failedCount
            $successRate = if ($totalSignals -gt 0) { 
                [math]::Round(($processedCount / $totalSignals) * 100, 2) 
            } else { 100 }
            
            return @{
                Processed = $processedCount
                Failed = $failedCount
                SuccessRate = $successRate
                LastSignal = $lastSignal
                Status = if ($successRate -gt 90) {"HEALTHY"} elseif ($successRate -gt 70) {"DEGRADED"} else {"CRITICAL"}
            }
        }
        catch {
            return @{
                Processed = 0
                Failed = 0
                SuccessRate = 0
                LastSignal = $null
                Status = "ERROR"
            }
        }
    }
    
    # Check HTTP market data streaming
    [hashtable] CheckMarketDataFlow() {
        try {
            # Check for tick data files
            $tickDataPath = "C:\Program Files\MetaTrader 5\MQL5\Files"
            $tickFiles = Get-ChildItem -Path $tickDataPath -Filter "tick_data_*.json" -ErrorAction SilentlyContinue
            
            if ($tickFiles) {
                # Get most recent tick file
                $latestTick = $tickFiles | Sort-Object LastWriteTime -Descending | Select-Object -First 1
                $lastStreamTime = $latestTick.LastWriteTime
                
                # Check if streaming is current (within last 10 seconds)
                $isStreaming = (Get-Date) - $lastStreamTime -lt [TimeSpan]::FromSeconds(10)
                
                # Check data quality by parsing a tick file
                try {
                    $tickContent = Get-Content $latestTick.FullName -Raw | ConvertFrom-Json
                    $dataQuality = if ($tickContent.bid -and $tickContent.ask -and $tickContent.symbol) {
                        "GOOD"
                    } else {
                        "INCOMPLETE"
                    }
                }
                catch {
                    $dataQuality = "PARSE_ERROR"
                }
                
                return @{
                    StreamingStatus = if ($isStreaming) {"ACTIVE"} else {"INACTIVE"}
                    LastStreamTime = $lastStreamTime
                    DataQuality = $dataQuality
                    ErrorRate = 0
                }
            }
            else {
                return @{
                    StreamingStatus = "NO_DATA"
                    LastStreamTime = $null
                    DataQuality = "NO_FILES"
                    ErrorRate = 100
                }
            }
        }
        catch {
            return @{
                StreamingStatus = "ERROR"
                LastStreamTime = $null
                DataQuality = "CHECK_FAILED"
                ErrorRate = 100
            }
        }
    }
    
    # Check file operations
    [hashtable] CheckFileOperations() {
        try {
            $bittenPath = "C:\Program Files\MetaTrader 5\MQL5\Files\BITTEN"
            
            # Test write permissions
            $testFile = Join-Path $bittenPath "test_write_$(Get-Random).tmp"
            try {
                "test" | Out-File -FilePath $testFile -Force
                Remove-Item $testFile -Force
                $writePermission = $true
            }
            catch {
                $writePermission = $false
            }
            
            # Check fire.txt accessibility
            $fireFile = Join-Path $bittenPath "fire.txt"
            $fireAccessible = Test-Path $fireFile
            
            # Check result file
            $resultFile = Join-Path $bittenPath "trade_result.txt"
            $resultAccessible = Test-Path $resultFile
            
            return @{
                WritePermission = $writePermission
                FireFileAccessible = $fireAccessible
                ResultFileAccessible = $resultAccessible
                Status = if ($writePermission) {"OK"} else {"PERMISSION_ERROR"}
            }
        }
        catch {
            return @{
                WritePermission = $false
                FireFileAccessible = $false
                ResultFileAccessible = $false
                Status = "ERROR"
            }
        }
    }
    
    # Check system resources
    [hashtable] CheckSystemResources() {
        try {
            # CPU usage
            $cpu = (Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 1 -MaxSamples 1).CounterSamples.CookedValue
            
            # Memory usage
            $totalMemory = (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory
            $freeMemory = (Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory * 1KB
            $memoryUsage = [math]::Round((($totalMemory - $freeMemory) / $totalMemory) * 100, 2)
            
            # Disk space
            $drive = Get-PSDrive -Name C
            $diskFreeGB = [math]::Round($drive.Free / 1GB, 2)
            $diskUsagePercent = [math]::Round((($drive.Used) / ($drive.Used + $drive.Free)) * 100, 2)
            
            return @{
                CPU = [math]::Round($cpu, 2)
                Memory = $memoryUsage
                DiskFreeGB = $diskFreeGB
                DiskUsagePercent = $diskUsagePercent
                Status = if ($cpu -lt 80 -and $memoryUsage -lt 80 -and $diskFreeGB -gt 10) {"HEALTHY"} else {"WARNING"}
            }
        }
        catch {
            return @{
                CPU = 0
                Memory = 0
                DiskFreeGB = 0
                DiskUsagePercent = 0
                Status = "ERROR"
            }
        }
    }
    
    # Get overall system status
    [string] GetOverallStatus() {
        $metrics = $this.MonitorEAPerformance()
        
        # Determine overall status based on individual components
        $criticalCount = 0
        $warningCount = 0
        
        foreach ($component in $metrics.Values) {
            if ($component -is [hashtable] -and $component.Status) {
                switch ($component.Status) {
                    "CRITICAL" { $criticalCount++ }
                    "ERROR" { $criticalCount++ }
                    "DEGRADED" { $warningCount++ }
                    "WARNING" { $warningCount++ }
                }
            }
            elseif ($component -is [string]) {
                if ($component -match "ERROR|FAILED|NOT_RUNNING") {
                    $criticalCount++
                }
                elseif ($component -match "DEGRADED|WARNING|ISSUE") {
                    $warningCount++
                }
            }
        }
        
        if ($criticalCount -gt 0) {
            return "CRITICAL"
        }
        elseif ($warningCount -gt 0) {
            return "WARNING"
        }
        else {
            return "HEALTHY"
        }
    }
    
    # Get current metrics snapshot
    [hashtable] GetCurrentMetrics() {
        return $this.MonitorEAPerformance()
    }
    
    # Detect system anomalies
    [hashtable] DetectSystemAnomalies() {
        $anomalies = @{
            Critical = @()
            Warning = @()
            Info = @()
        }
        
        $metrics = $this.MonitorEAPerformance()
        
        # Check for critical issues
        if ($metrics.EA_Status -eq "MT5_NOT_RUNNING") {
            $anomalies.Critical += "MT5 terminal is not running"
        }
        
        if ($metrics.Signal_Processing.SuccessRate -lt 50) {
            $anomalies.Critical += "Signal processing success rate below 50%"
        }
        
        if ($metrics.System_Resources.DiskFreeGB -lt 5) {
            $anomalies.Critical += "Disk space critically low"
        }
        
        # Check for warnings
        if ($metrics.Signal_Processing.SuccessRate -lt 80) {
            $anomalies.Warning += "Signal processing success rate below 80%"
        }
        
        if ($metrics.HTTP_Streaming.StreamingStatus -ne "ACTIVE") {
            $anomalies.Warning += "Market data streaming is not active"
        }
        
        if ($metrics.System_Resources.CPU -gt 80) {
            $anomalies.Warning += "High CPU usage detected"
        }
        
        return $anomalies
    }
}

# Export the class
Export-ModuleMember -Function * -Cmdlet * -Variable * -Alias *