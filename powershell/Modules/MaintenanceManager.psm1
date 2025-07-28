# MaintenanceManager.psm1 - System Maintenance and Recovery Module

class SystemMaintenanceManager {
    [object]$ServiceMonitor
    [object]$PerformanceOptimizer
    [object]$RecoverySystem
    [string]$MT5Path = "C:\Program Files\MetaTrader 5"
    [string]$LogPath = "C:\BiTTen\Agent\Logs"
    [hashtable]$MaintenanceHistory
    
    SystemMaintenanceManager() {
        $this.InitializeManager()
    }
    
    [void] InitializeManager() {
        $this.MaintenanceHistory = @{}
        
        # Ensure log directory exists
        if (-not (Test-Path $this.LogPath)) {
            New-Item -ItemType Directory -Path $this.LogPath -Force | Out-Null
        }
    }
    
    # Perform daily maintenance
    [hashtable] PerformDailyMaintenance() {
        $report = @{
            StartTime = Get-Date
            Tasks = @()
            Errors = @()
            Warnings = @()
            Status = "SUCCESS"
        }
        
        try {
            # 1. Clean up old log files
            Write-Host "🧹 Cleaning up old logs..." -ForegroundColor Gray
            $logCleanup = $this.CleanupLogs()
            $report.Tasks += @{
                Task = "Log Cleanup"
                Result = $logCleanup
                Status = "Completed"
            }
            
            # 2. Optimize disk space
            Write-Host "💾 Optimizing disk space..." -ForegroundColor Gray
            $diskOpt = $this.OptimizeDiskSpace()
            $report.Tasks += @{
                Task = "Disk Optimization"
                Result = $diskOpt
                Status = "Completed"
            }
            
            # 3. Check and repair file permissions
            Write-Host "🔐 Checking file permissions..." -ForegroundColor Gray
            $permCheck = $this.CheckAndRepairPermissions()
            $report.Tasks += @{
                Task = "Permission Check"
                Result = $permCheck
                Status = "Completed"
            }
            
            # 4. Collect performance metrics
            Write-Host "📊 Collecting performance metrics..." -ForegroundColor Gray
            $perfMetrics = $this.CollectPerformanceMetrics()
            $report.Tasks += @{
                Task = "Performance Collection"
                Result = $perfMetrics
                Status = "Completed"
            }
            
            # 5. Verify MT5 integrity
            Write-Host "🔍 Verifying MT5 integrity..." -ForegroundColor Gray
            $mt5Check = $this.VerifyMT5Integrity()
            $report.Tasks += @{
                Task = "MT5 Integrity Check"
                Result = $mt5Check
                Status = if ($mt5Check.IsHealthy) {"Healthy"} else {"Issues Found"}
            }
            
            # 6. Prepare for cloning
            Write-Host "📦 Preparing system for cloning..." -ForegroundColor Gray
            $clonePrep = $this.PrepareForCloning()
            $report.Tasks += @{
                Task = "Clone Preparation"
                Result = $clonePrep
                Status = "Completed"
            }
            
            # 7. Generate health report
            $healthReport = $this.GenerateHealthReport()
            $report.HealthReport = $healthReport
            
        }
        catch {
            $report.Status = "FAILED"
            $report.Errors += $_.ToString()
        }
        
        $report.EndTime = Get-Date
        $report.Duration = ($report.EndTime - $report.StartTime).TotalMinutes
        
        # Save maintenance history
        $this.MaintenanceHistory[(Get-Date -Format "yyyyMMdd")] = $report
        
        return $report
    }
    
    # Clean up old log files
    [hashtable] CleanupLogs() {
        $result = @{
            FilesRemoved = 0
            SpaceFreed = 0
            OldestKept = $null
        }
        
        try {
            # Clean MT5 logs older than 7 days
            $mt5LogPath = Join-Path $this.MT5Path "MQL5\Logs"
            if (Test-Path $mt5LogPath) {
                $oldLogs = Get-ChildItem -Path $mt5LogPath -Filter "*.log" |
                          Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) }
                
                foreach ($log in $oldLogs) {
                    $result.SpaceFreed += $log.Length
                    Remove-Item $log.FullName -Force
                    $result.FilesRemoved++
                }
            }
            
            # Clean agent logs older than 30 days
            $oldAgentLogs = Get-ChildItem -Path $this.LogPath -Filter "*.log" |
                           Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) }
            
            foreach ($log in $oldAgentLogs) {
                $result.SpaceFreed += $log.Length
                Remove-Item $log.FullName -Force
                $result.FilesRemoved++
            }
            
            # Get oldest remaining log
            $remainingLogs = Get-ChildItem -Path $this.LogPath -Filter "*.log" |
                            Sort-Object LastWriteTime
            
            if ($remainingLogs) {
                $result.OldestKept = $remainingLogs[0].LastWriteTime
            }
            
            $result.SpaceFreedMB = [math]::Round($result.SpaceFreed / 1MB, 2)
        }
        catch {
            Write-Warning "Error during log cleanup: $_"
        }
        
        return $result
    }
    
    # Optimize disk space
    [hashtable] OptimizeDiskSpace() {
        $result = @{
            InitialFreeSpace = 0
            FinalFreeSpace = 0
            SpaceRecovered = 0
            Actions = @()
        }
        
        try {
            # Get initial free space
            $drive = Get-PSDrive -Name C
            $result.InitialFreeSpace = [math]::Round($drive.Free / 1GB, 2)
            
            # Clean Windows temp files
            $tempPaths = @(
                $env:TEMP,
                "$env:WINDIR\Temp",
                "$env:LOCALAPPDATA\Temp"
            )
            
            foreach ($tempPath in $tempPaths) {
                if (Test-Path $tempPath) {
                    try {
                        Get-ChildItem -Path $tempPath -Recurse -Force -ErrorAction SilentlyContinue |
                            Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-1) } |
                            Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
                        
                        $result.Actions += "Cleaned temp files in $tempPath"
                    }
                    catch {
                        # Ignore errors for locked files
                    }
                }
            }
            
            # Clean old tick data files
            $tickDataPath = Join-Path $this.MT5Path "MQL5\Files"
            $oldTickFiles = Get-ChildItem -Path $tickDataPath -Filter "tick_data_*.json" -ErrorAction SilentlyContinue |
                           Where-Object { $_.LastWriteTime -lt (Get-Date).AddHours(-24) }
            
            $tickSpaceFreed = 0
            foreach ($file in $oldTickFiles) {
                $tickSpaceFreed += $file.Length
                Remove-Item $file.FullName -Force
            }
            
            if ($tickSpaceFreed -gt 0) {
                $result.Actions += "Removed old tick data files (freed $([math]::Round($tickSpaceFreed / 1MB, 2)) MB)"
            }
            
            # Run Windows Disk Cleanup if space is low
            if ($result.InitialFreeSpace -lt 20) {
                Write-Host "   Running Windows Disk Cleanup..." -ForegroundColor Yellow
                Start-Process -FilePath "cleanmgr.exe" -ArgumentList "/sagerun:1" -Wait -WindowStyle Hidden
                $result.Actions += "Ran Windows Disk Cleanup"
            }
            
            # Get final free space
            $drive = Get-PSDrive -Name C
            $result.FinalFreeSpace = [math]::Round($drive.Free / 1GB, 2)
            $result.SpaceRecovered = $result.FinalFreeSpace - $result.InitialFreeSpace
            
        }
        catch {
            Write-Warning "Error during disk optimization: $_"
        }
        
        return $result
    }
    
    # Check and repair file permissions
    [hashtable] CheckAndRepairPermissions() {
        $result = @{
            IssuesFound = 0
            IssuesFixed = 0
            Details = @()
        }
        
        try {
            # Critical paths to check
            $criticalPaths = @(
                (Join-Path $this.MT5Path "MQL5\Files\BITTEN"),
                (Join-Path $this.MT5Path "MQL5\Files\BITTEN\fire.txt"),
                (Join-Path $this.MT5Path "MQL5\Files\BITTEN\trade_result.txt"),
                $this.LogPath
            )
            
            foreach ($path in $criticalPaths) {
                if (Test-Path $path) {
                    try {
                        # Test write access
                        $testFile = Join-Path (Split-Path $path -Parent) "permission_test_$(Get-Random).tmp"
                        "test" | Out-File -FilePath $testFile -Force -ErrorAction Stop
                        Remove-Item $testFile -Force
                    }
                    catch {
                        $result.IssuesFound++
                        
                        # Attempt to fix permissions
                        try {
                            $acl = Get-Acl $path
                            $permission = "$env:USERNAME", "FullControl", "Allow"
                            $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule $permission
                            $acl.SetAccessRule($accessRule)
                            Set-Acl $path $acl
                            
                            $result.IssuesFixed++
                            $result.Details += "Fixed permissions for: $path"
                        }
                        catch {
                            $result.Details += "Failed to fix permissions for: $path"
                        }
                    }
                }
                else {
                    # Create missing path
                    if ($path -notmatch "\.txt$") {
                        New-Item -ItemType Directory -Path $path -Force | Out-Null
                        $result.Details += "Created missing directory: $path"
                    }
                    else {
                        New-Item -ItemType File -Path $path -Force | Out-Null
                        $result.Details += "Created missing file: $path"
                    }
                }
            }
        }
        catch {
            Write-Warning "Error checking permissions: $_"
        }
        
        return $result
    }
    
    # Collect performance metrics
    [hashtable] CollectPerformanceMetrics() {
        $metrics = @{
            Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            System = @{}
            MT5 = @{}
            Trading = @{}
        }
        
        try {
            # System metrics
            $metrics.System = @{
                CPUUsage = (Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 1 -MaxSamples 3 | 
                           Select-Object -ExpandProperty CounterSamples | 
                           Measure-Object -Property CookedValue -Average).Average
                MemoryUsagePercent = 100 - (Get-Counter '\Memory\Available MBytes' | 
                                          Select-Object -ExpandProperty CounterSamples | 
                                          ForEach-Object { $_.CookedValue / ((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1MB) * 100 })
                DiskIOps = (Get-Counter '\PhysicalDisk(_Total)\Disk Transfers/sec' | 
                           Select-Object -ExpandProperty CounterSamples).CookedValue
                NetworkBandwidth = (Get-Counter '\Network Interface(*)\Bytes Total/sec' | 
                                   Select-Object -ExpandProperty CounterSamples | 
                                   Measure-Object -Property CookedValue -Sum).Sum
            }
            
            # MT5 specific metrics
            $mt5Process = Get-Process -Name "terminal64" -ErrorAction SilentlyContinue
            if ($mt5Process) {
                $metrics.MT5 = @{
                    ProcessId = $mt5Process.Id
                    WorkingSetMB = [math]::Round($mt5Process.WorkingSet64 / 1MB, 2)
                    CPUTime = $mt5Process.TotalProcessorTime.TotalSeconds
                    ThreadCount = $mt5Process.Threads.Count
                    HandleCount = $mt5Process.HandleCount
                    Uptime = ((Get-Date) - $mt5Process.StartTime).TotalHours
                }
            }
            
            # Trading metrics (from files)
            $bittenPath = Join-Path $this.MT5Path "MQL5\Files\BITTEN"
            if (Test-Path $bittenPath) {
                $signalFiles = Get-ChildItem -Path $bittenPath -Filter "signal_*.json" -ErrorAction SilentlyContinue
                $resultFiles = Get-ChildItem -Path $bittenPath -Filter "result_*.json" -ErrorAction SilentlyContinue
                
                $metrics.Trading = @{
                    PendingSignals = $signalFiles.Count
                    ProcessedResults = $resultFiles.Count
                    LastSignalTime = if ($signalFiles) { ($signalFiles | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime } else { $null }
                    LastResultTime = if ($resultFiles) { ($resultFiles | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime } else { $null }
                }
            }
        }
        catch {
            Write-Warning "Error collecting metrics: $_"
        }
        
        return $metrics
    }
    
    # Verify MT5 integrity
    [hashtable] VerifyMT5Integrity() {
        $result = @{
            IsHealthy = $true
            Issues = @()
            Checks = @{}
        }
        
        try {
            # Check 1: MT5 executable exists
            $mt5Exe = Join-Path $this.MT5Path "terminal64.exe"
            $result.Checks.ExecutableExists = Test-Path $mt5Exe
            if (-not $result.Checks.ExecutableExists) {
                $result.IsHealthy = $false
                $result.Issues += "MT5 executable not found"
            }
            
            # Check 2: EA file exists
            $eaPath = Join-Path $this.MT5Path "MQL5\Experts\BITTENBridge_TradeExecutor.ex5"
            $result.Checks.EAExists = Test-Path $eaPath
            if (-not $result.Checks.EAExists) {
                $result.IsHealthy = $false
                $result.Issues += "BITTENBridge EA not found"
            }
            
            # Check 3: Critical directories exist
            $criticalDirs = @(
                "MQL5\Files\BITTEN",
                "MQL5\Logs",
                "config",
                "profiles\default"
            )
            
            foreach ($dir in $criticalDirs) {
                $fullPath = Join-Path $this.MT5Path $dir
                if (-not (Test-Path $fullPath)) {
                    $result.IsHealthy = $false
                    $result.Issues += "Missing directory: $dir"
                }
            }
            
            # Check 4: MT5 process health
            $mt5Process = Get-Process -Name "terminal64" -ErrorAction SilentlyContinue
            if ($mt5Process) {
                $result.Checks.ProcessRunning = $true
                $result.Checks.ProcessResponding = $mt5Process.Responding
                
                if (-not $mt5Process.Responding) {
                    $result.IsHealthy = $false
                    $result.Issues += "MT5 process not responding"
                }
            }
            else {
                $result.Checks.ProcessRunning = $false
                $result.Checks.ProcessResponding = $false
            }
            
            # Check 5: Configuration files
            $configFiles = @("terminal.ini", "common.ini")
            foreach ($config in $configFiles) {
                $configPath = Join-Path $this.MT5Path "config\$config"
                if (-not (Test-Path $configPath)) {
                    $result.Issues += "Missing config file: $config"
                }
            }
        }
        catch {
            $result.IsHealthy = $false
            $result.Issues += "Error during integrity check: $_"
        }
        
        return $result
    }
    
    # Prepare system for cloning
    [hashtable] PrepareForCloning() {
        $result = @{
            Status = "SUCCESS"
            Actions = @()
            ReadyForCloning = $true
        }
        
        try {
            # 1. Standardize configuration files
            Write-Host "   • Standardizing configurations..." -ForegroundColor Gray
            $this.StandardizeConfigurations()
            $result.Actions += "Standardized configuration files"
            
            # 2. Clear user-specific data
            Write-Host "   • Clearing user-specific data..." -ForegroundColor Gray
            $this.ClearPersonalData()
            $result.Actions += "Cleared personal data"
            
            # 3. Reset counters and logs
            Write-Host "   • Resetting system counters..." -ForegroundColor Gray
            $this.ResetSystemCounters()
            $result.Actions += "Reset system counters"
            
            # 4. Create clone readiness marker
            $markerPath = Join-Path $this.MT5Path "clone_ready.txt"
            @{
                PreparedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                AgentVersion = "1.0.0"
                SystemStatus = "Ready for cloning"
            } | ConvertTo-Json | Set-Content $markerPath
            $result.Actions += "Created clone readiness marker"
            
            # 5. Verify all services are properly configured
            $serviceCheck = $this.VerifyCloneReadiness()
            if (-not $serviceCheck.IsReady) {
                $result.ReadyForCloning = $false
                $result.Status = "ISSUES_FOUND"
                $result.Actions += "Clone readiness check failed: $($serviceCheck.Issues -join ', ')"
            }
        }
        catch {
            $result.Status = "FAILED"
            $result.ReadyForCloning = $false
            $result.Actions += "Error: $_"
        }
        
        return $result
    }
    
    # Standardize configurations
    [void] StandardizeConfigurations() {
        # Remove machine-specific entries from terminal.ini
        $terminalIni = Join-Path $this.MT5Path "config\terminal.ini"
        if (Test-Path $terminalIni) {
            $content = Get-Content $terminalIni
            $standardized = $content | Where-Object { 
                $_ -notmatch "Login=|Password=|Server=|Certificate"
            }
            $standardized | Set-Content $terminalIni
        }
    }
    
    # Clear personal data
    [void] ClearPersonalData() {
        # Clear saved passwords
        $paths = @(
            (Join-Path $this.MT5Path "config\accounts.dat"),
            (Join-Path $this.MT5Path "bases\*\*.dat")
        )
        
        foreach ($path in $paths) {
            if (Test-Path $path) {
                Remove-Item $path -Force -ErrorAction SilentlyContinue
            }
        }
    }
    
    # Reset system counters
    [void] ResetSystemCounters() {
        # Clear logs
        $logPath = Join-Path $this.MT5Path "MQL5\Logs"
        if (Test-Path $logPath) {
            Get-ChildItem -Path $logPath -Filter "*.log" | 
                Where-Object { $_.Name -ne "BITTENBridge.log" } |
                Remove-Item -Force -ErrorAction SilentlyContinue
        }
        
        # Reset signal counters
        $bittenPath = Join-Path $this.MT5Path "MQL5\Files\BITTEN"
        if (Test-Path $bittenPath) {
            @("processed", "failed", "archive") | ForEach-Object {
                $subPath = Join-Path $bittenPath $_
                if (Test-Path $subPath) {
                    Get-ChildItem -Path $subPath | Remove-Item -Force -ErrorAction SilentlyContinue
                }
            }
        }
    }
    
    # Verify clone readiness
    [hashtable] VerifyCloneReadiness() {
        $result = @{
            IsReady = $true
            Issues = @()
        }
        
        # Check for personal data
        if (Test-Path (Join-Path $this.MT5Path "config\accounts.dat")) {
            $result.IsReady = $false
            $result.Issues += "Personal account data still present"
        }
        
        # Check for active connections
        $mt5Process = Get-Process -Name "terminal64" -ErrorAction SilentlyContinue
        if ($mt5Process) {
            $connections = Get-NetTCPConnection -OwningProcess $mt5Process.Id -ErrorAction SilentlyContinue
            if ($connections | Where-Object { $_.State -eq "Established" }) {
                $result.IsReady = $false
                $result.Issues += "Active MT5 connections detected"
            }
        }
        
        return $result
    }
    
    # Generate health report
    [hashtable] GenerateHealthReport() {
        return @{
            Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            SystemHealth = $this.AssessSystemHealth()
            MT5Status = $this.CheckMT5Status()
            DiskHealth = $this.CheckDiskHealth()
            NetworkHealth = $this.CheckNetworkHealth()
            RecommendedActions = $this.GetRecommendedActions()
        }
    }
    
    # Assess overall system health
    [string] AssessSystemHealth() {
        $issues = 0
        
        # Check CPU
        $cpu = (Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 1 -MaxSamples 1).CounterSamples.CookedValue
        if ($cpu -gt 80) { $issues++ }
        
        # Check memory
        $memoryFree = (Get-Counter '\Memory\Available MBytes').CounterSamples.CookedValue
        if ($memoryFree -lt 1024) { $issues++ }
        
        # Check disk
        $diskFree = (Get-PSDrive -Name C).Free / 1GB
        if ($diskFree -lt 10) { $issues++ }
        
        if ($issues -eq 0) { return "HEALTHY" }
        elseif ($issues -eq 1) { return "WARNING" }
        else { return "CRITICAL" }
    }
    
    # Check MT5 status
    [hashtable] CheckMT5Status() {
        $status = @{
            IsRunning = $false
            Uptime = 0
            MemoryUsage = 0
            Status = "NOT_RUNNING"
        }
        
        $mt5Process = Get-Process -Name "terminal64" -ErrorAction SilentlyContinue
        if ($mt5Process) {
            $status.IsRunning = $true
            $status.Uptime = ((Get-Date) - $mt5Process.StartTime).TotalHours
            $status.MemoryUsage = [math]::Round($mt5Process.WorkingSet64 / 1MB, 2)
            $status.Status = if ($mt5Process.Responding) {"RUNNING"} else {"NOT_RESPONDING"}
        }
        
        return $status
    }
    
    # Check disk health
    [hashtable] CheckDiskHealth() {
        $drive = Get-PSDrive -Name C
        
        return @{
            FreeSpaceGB = [math]::Round($drive.Free / 1GB, 2)
            UsedSpaceGB = [math]::Round($drive.Used / 1GB, 2)
            PercentFree = [math]::Round(($drive.Free / ($drive.Used + $drive.Free)) * 100, 2)
            Status = if ($drive.Free / 1GB -gt 20) {"HEALTHY"} elseif ($drive.Free / 1GB -gt 10) {"WARNING"} else {"CRITICAL"}
        }
    }
    
    # Check network health
    [hashtable] CheckNetworkHealth() {
        $result = @{
            InternetConnectivity = $false
            BrokerConnectivity = $false
            Latency = 0
            Status = "UNKNOWN"
        }
        
        try {
            # Test internet connectivity
            $ping = Test-Connection -ComputerName "8.8.8.8" -Count 1 -Quiet
            $result.InternetConnectivity = $ping
            
            # Test broker connectivity (MetaQuotes)
            $brokerTest = Test-NetConnection -ComputerName "api.metaquotes.net" -Port 443 -WarningAction SilentlyContinue
            $result.BrokerConnectivity = $brokerTest.TcpTestSucceeded
            
            # Measure latency
            if ($ping) {
                $latencyTest = Test-Connection -ComputerName "8.8.8.8" -Count 3
                $result.Latency = ($latencyTest | Measure-Object -Property ResponseTime -Average).Average
            }
            
            if ($result.InternetConnectivity -and $result.BrokerConnectivity) {
                $result.Status = "HEALTHY"
            }
            elseif ($result.InternetConnectivity) {
                $result.Status = "BROKER_ISSUE"
            }
            else {
                $result.Status = "NO_INTERNET"
            }
        }
        catch {
            $result.Status = "ERROR"
        }
        
        return $result
    }
    
    # Get recommended actions based on health
    [array] GetRecommendedActions() {
        $actions = @()
        
        # Check disk space
        $diskFree = (Get-PSDrive -Name C).Free / 1GB
        if ($diskFree -lt 10) {
            $actions += "Free up disk space (less than 10GB available)"
        }
        
        # Check memory
        $memoryFree = (Get-Counter '\Memory\Available MBytes').CounterSamples.CookedValue
        if ($memoryFree -lt 1024) {
            $actions += "Close unnecessary applications (low memory)"
        }
        
        # Check MT5
        $mt5Process = Get-Process -Name "terminal64" -ErrorAction SilentlyContinue
        if (-not $mt5Process) {
            $actions += "Start MT5 terminal"
        }
        elseif (-not $mt5Process.Responding) {
            $actions += "Restart MT5 terminal (not responding)"
        }
        
        return $actions
    }
    
    # Attempt system recovery
    [bool] AttemptSystemRecovery([string]$issueType) {
        Write-Host "🔧 Attempting recovery for: $issueType" -ForegroundColor Yellow
        
        switch ($issueType) {
            "EA_Stopped" {
                return $this.RestartEA()
            }
            "EA_Issue" {
                return $this.RestartEA()
            }
            "MT5_Disconnected" {
                return $this.ReconnectMT5()
            }
            "File_Permission_Error" {
                return $this.FixFilePermissions()
            }
            "Disk_Space_Low" {
                return $this.FreeDiskSpace()
            }
            default {
                Write-Warning "Unknown issue type: $issueType"
                return $false
            }
        }
    }
    
    # Restart EA
    [bool] RestartEA() {
        try {
            # First try to restart just MT5
            $mt5Process = Get-Process -Name "terminal64" -ErrorAction SilentlyContinue
            
            if ($mt5Process) {
                Write-Host "   Stopping MT5..." -ForegroundColor Gray
                Stop-Process -Name "terminal64" -Force
                Start-Sleep -Seconds 5
            }
            
            # Start MT5
            Write-Host "   Starting MT5..." -ForegroundColor Gray
            $mt5Exe = Join-Path $this.MT5Path "terminal64.exe"
            if (Test-Path $mt5Exe) {
                Start-Process -FilePath $mt5Exe -WindowStyle Minimized
                Start-Sleep -Seconds 10
                
                # Verify it started
                $newProcess = Get-Process -Name "terminal64" -ErrorAction SilentlyContinue
                if ($newProcess -and $newProcess.Responding) {
                    Write-Host "✅ MT5 restarted successfully" -ForegroundColor Green
                    return $true
                }
            }
        }
        catch {
            Write-Error "Failed to restart EA: $_"
        }
        
        return $false
    }
    
    # Reconnect MT5
    [bool] ReconnectMT5() {
        # MT5 usually reconnects automatically, but we can try to help
        try {
            # Check network first
            $networkTest = Test-NetConnection -ComputerName "api.metaquotes.net" -Port 443 -WarningAction SilentlyContinue
            
            if (-not $networkTest.TcpTestSucceeded) {
                Write-Warning "Network connectivity issue detected"
                
                # Try to reset network adapter
                Write-Host "   Resetting network adapter..." -ForegroundColor Gray
                Get-NetAdapter | Where-Object {$_.Status -eq "Up"} | Restart-NetAdapter
                Start-Sleep -Seconds 5
            }
            
            # If MT5 is running but disconnected, try sending reconnect command
            $mt5Process = Get-Process -Name "terminal64" -ErrorAction SilentlyContinue
            if ($mt5Process) {
                # MT5 doesn't have a direct reconnect API, but restarting usually helps
                return $this.RestartEA()
            }
            
            return $true
        }
        catch {
            Write-Error "Failed to reconnect MT5: $_"
            return $false
        }
    }
    
    # Fix file permissions
    [bool] FixFilePermissions() {
        try {
            $bittenPath = Join-Path $this.MT5Path "MQL5\Files\BITTEN"
            
            # Take ownership and grant full control
            $acl = Get-Acl $bittenPath
            $permission = "$env:USERNAME", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow"
            $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule $permission
            $acl.SetAccessRule($accessRule)
            
            # Also add SYSTEM
            $permission = "SYSTEM", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow"
            $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule $permission
            $acl.SetAccessRule($accessRule)
            
            Set-Acl $bittenPath $acl -ErrorAction Stop
            
            Write-Host "✅ File permissions fixed" -ForegroundColor Green
            return $true
        }
        catch {
            Write-Error "Failed to fix permissions: $_"
            return $false
        }
    }
    
    # Free disk space
    [bool] FreeDiskSpace() {
        try {
            Write-Host "   Running emergency disk cleanup..." -ForegroundColor Yellow
            
            # Clean temp files aggressively
            @($env:TEMP, "$env:WINDIR\Temp") | ForEach-Object {
                if (Test-Path $_) {
                    Get-ChildItem -Path $_ -Recurse -Force -ErrorAction SilentlyContinue |
                        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
                }
            }
            
            # Clean old Windows updates
            if (Test-Path "$env:WINDIR\SoftwareDistribution\Download") {
                Get-ChildItem -Path "$env:WINDIR\SoftwareDistribution\Download" -Recurse |
                    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
            }
            
            # Run disk cleanup
            Start-Process -FilePath "cleanmgr.exe" -ArgumentList "/sagerun:1" -Wait -WindowStyle Hidden
            
            # Check if we freed enough space
            $freeSpace = (Get-PSDrive -Name C).Free / 1GB
            if ($freeSpace -gt 5) {
                Write-Host "✅ Freed disk space (now $([math]::Round($freeSpace, 2)) GB free)" -ForegroundColor Green
                return $true
            }
        }
        catch {
            Write-Error "Failed to free disk space: $_"
        }
        
        return $false
    }
}

# Export the class
Export-ModuleMember -Function * -Cmdlet * -Variable * -Alias *