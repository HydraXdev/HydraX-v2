# BiTTen Dual Agent - Windows VPS Guardian & Intelligence System
# Version: 1.0.0
# Purpose: Intelligent Windows-side guardian for BITTEN ecosystem

param(
    [string]$Action = "run",
    [string]$UserUUID = "",
    [string]$BrokerType = "auto-detect",
    [string]$ConfigPath = "C:\BiTTen\Agent\config.json"
)

# Import required modules
$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module "$PSScriptRoot\Modules\SystemIntelligence.psm1" -Force
Import-Module "$PSScriptRoot\Modules\FileManager.psm1" -Force
Import-Module "$PSScriptRoot\Modules\BrokerHandler.psm1" -Force
Import-Module "$PSScriptRoot\Modules\MaintenanceManager.psm1" -Force

# Main Agent Class
class BiTTenDualAgent {
    [string]$AgentID
    [string]$UserUUID
    [string]$BrokerType
    [hashtable]$Configuration
    [object]$Logger
    [object]$HealthMonitor
    [object]$FileManager
    [object]$BrokerHandler
    [object]$MaintenanceManager
    [bool]$Running = $false
    
    # Constructor
    BiTTenDualAgent([string]$uuid, [string]$broker) {
        $this.AgentID = "AGENT_" + (Get-Date -Format "yyyyMMdd_HHmmss")
        $this.UserUUID = $uuid
        $this.BrokerType = $broker
        $this.InitializeAgent()
    }
    
    # Initialize all agent components
    [void] InitializeAgent() {
        Write-Host "🚀 Initializing BiTTen Dual Agent..." -ForegroundColor Cyan
        
        # Load configuration
        $this.LoadConfiguration()
        
        # Initialize components
        $this.Logger = New-Object Logger -ArgumentList $this.Configuration.LogPath
        $this.HealthMonitor = New-Object SystemMonitor -ArgumentList $this.UserUUID
        $this.FileManager = New-Object IntelligentFileManager -ArgumentList $this.Configuration.MT5Path
        $this.BrokerHandler = New-Object BrokerCompatibilityManager
        $this.MaintenanceManager = New-Object SystemMaintenanceManager
        
        # Auto-detect broker if needed
        if ($this.BrokerType -eq "auto-detect") {
            $this.BrokerType = $this.BrokerHandler.DetectBrokerType()
            Write-Host "✅ Detected broker: $($this.BrokerType)" -ForegroundColor Green
        }
        
        # Build symbol mappings
        $this.BrokerHandler.BuildSymbolMappings()
        
        Write-Host "✅ BiTTen Dual Agent initialized successfully" -ForegroundColor Green
        Write-Host "   Agent ID: $($this.AgentID)" -ForegroundColor Gray
        Write-Host "   User UUID: $($this.UserUUID)" -ForegroundColor Gray
        Write-Host "   Broker: $($this.BrokerType)" -ForegroundColor Gray
    }
    
    # Load or create configuration
    [void] LoadConfiguration() {
        $defaultConfig = @{
            Running = $true
            LogPath = "C:\BiTTen\Agent\Logs"
            MT5Path = "C:\Program Files\MetaTrader 5\MQL5\Files"
            MonitorInterval = 10
            MaintenanceHour = 3
            EnableAutoRecovery = $true
            EnableMetricsReporting = $true
            MetricsEndpoint = "https://terminus.joinbitten.com/metrics"
            HealthCheckInterval = 60
            FileCleanupDays = 7
            MaxLogSizeMB = 100
        }
        
        # Load existing config if available
        if (Test-Path $this.ConfigPath) {
            try {
                $loaded = Get-Content $this.ConfigPath -Raw | ConvertFrom-Json
                foreach ($key in $loaded.PSObject.Properties.Name) {
                    $defaultConfig[$key] = $loaded.$key
                }
            }
            catch {
                Write-Warning "Failed to load config, using defaults"
            }
        }
        
        $this.Configuration = $defaultConfig
        
        # Ensure directories exist
        @($this.Configuration.LogPath, (Split-Path $this.ConfigPath -Parent)) | ForEach-Object {
            if (-not (Test-Path $_)) {
                New-Item -ItemType Directory -Path $_ -Force | Out-Null
            }
        }
    }
    
    # Main execution loop
    [void] RunAgent() {
        Write-Host "`n🔄 Starting BiTTen Dual Agent main loop..." -ForegroundColor Yellow
        $this.Running = $true
        
        $lastHealthCheck = Get-Date
        $lastMaintenance = Get-Date
        
        while ($this.Running -and $this.Configuration.Running) {
            try {
                # Core monitoring
                $this.MonitorSystem()
                
                # File management
                $this.ManageFiles()
                
                # Broker compatibility checks
                $this.CheckBrokerCompatibility()
                
                # Health reporting (every minute)
                if ((Get-Date) - $lastHealthCheck -gt [TimeSpan]::FromSeconds($this.Configuration.HealthCheckInterval)) {
                    $this.ReportHealth()
                    $lastHealthCheck = Get-Date
                }
                
                # Daily maintenance (at configured hour)
                if ((Get-Date).Hour -eq $this.Configuration.MaintenanceHour -and 
                    (Get-Date) - $lastMaintenance -gt [TimeSpan]::FromHours(23)) {
                    $this.PerformMaintenance()
                    $lastMaintenance = Get-Date
                }
                
            }
            catch {
                $this.Logger.LogError("Agent loop error: $_")
                if ($this.Configuration.EnableAutoRecovery) {
                    $this.AttemptRecovery($_)
                }
            }
            
            Start-Sleep -Seconds $this.Configuration.MonitorInterval
        }
        
        Write-Host "`n🛑 BiTTen Dual Agent stopped" -ForegroundColor Red
    }
    
    # Monitor system health and performance
    [void] MonitorSystem() {
        $metrics = $this.HealthMonitor.MonitorEAPerformance()
        
        # Check for critical issues
        if ($metrics.EA_Status -ne "HEALTHY") {
            $this.Logger.LogWarning("EA health issue detected: $($metrics.EA_Status)")
            if ($this.Configuration.EnableAutoRecovery) {
                $this.MaintenanceManager.AttemptSystemRecovery("EA_Issue")
            }
        }
        
        # Check signal processing
        if ($metrics.Signal_Processing.SuccessRate -lt 80) {
            $this.Logger.LogWarning("Low signal success rate: $($metrics.Signal_Processing.SuccessRate)%")
        }
        
        # Report metrics if enabled
        if ($this.Configuration.EnableMetricsReporting) {
            $this.SendMetrics($metrics)
        }
    }
    
    # Manage signal and result files
    [void] ManageFiles() {
        # Monitor signal files
        $this.FileManager.ManageSignalFiles()
        
        # Clean up old files
        $this.FileManager.CleanupOldFiles($this.Configuration.FileCleanupDays)
        
        # Optimize for cloning if needed
        if ($this.ShouldOptimizeForCloning()) {
            $this.FileManager.OptimizeForCloning()
        }
    }
    
    # Check broker compatibility
    [void] CheckBrokerCompatibility() {
        # Verify symbol mappings are still valid
        $invalidSymbols = $this.BrokerHandler.ValidateSymbolMappings()
        
        if ($invalidSymbols.Count -gt 0) {
            $this.Logger.LogWarning("Invalid symbol mappings detected: $($invalidSymbols -join ', ')")
            $this.BrokerHandler.BuildSymbolMappings()
        }
    }
    
    # Perform daily maintenance
    [void] PerformMaintenance() {
        Write-Host "`n🔧 Performing daily maintenance..." -ForegroundColor Yellow
        
        $report = $this.MaintenanceManager.PerformDailyMaintenance()
        
        # Send maintenance report
        $this.SendMaintenanceReport($report)
        
        Write-Host "✅ Daily maintenance completed" -ForegroundColor Green
    }
    
    # Report health status to BITTEN
    [void] ReportHealth() {
        $health = @{
            AgentID = $this.AgentID
            UserUUID = $this.UserUUID
            Timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
            Status = $this.HealthMonitor.GetOverallStatus()
            Metrics = $this.HealthMonitor.GetCurrentMetrics()
            BrokerType = $this.BrokerType
            SymbolMappings = $this.BrokerHandler.GetSymbolMappings()
        }
        
        try {
            $json = $health | ConvertTo-Json -Depth 5
            Invoke-RestMethod -Uri "$($this.Configuration.MetricsEndpoint)/health" `
                -Method Post -Body $json -ContentType "application/json" | Out-Null
        }
        catch {
            $this.Logger.LogError("Failed to report health: $_")
        }
    }
    
    # Send metrics to BITTEN
    [void] SendMetrics([hashtable]$metrics) {
        $payload = @{
            AgentID = $this.AgentID
            UserUUID = $this.UserUUID
            Timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
            Metrics = $metrics
        }
        
        try {
            $json = $payload | ConvertTo-Json -Depth 5
            Invoke-RestMethod -Uri $this.Configuration.MetricsEndpoint `
                -Method Post -Body $json -ContentType "application/json" | Out-Null
        }
        catch {
            # Silently fail metrics reporting to avoid disrupting operations
        }
    }
    
    # Send maintenance report
    [void] SendMaintenanceReport([hashtable]$report) {
        $payload = @{
            AgentID = $this.AgentID
            UserUUID = $this.UserUUID
            Timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
            Report = $report
        }
        
        try {
            $json = $payload | ConvertTo-Json -Depth 5
            Invoke-RestMethod -Uri "$($this.Configuration.MetricsEndpoint)/maintenance" `
                -Method Post -Body $json -ContentType "application/json" | Out-Null
        }
        catch {
            $this.Logger.LogError("Failed to send maintenance report: $_")
        }
    }
    
    # Attempt recovery from errors
    [void] AttemptRecovery([object]$error) {
        $this.Logger.LogInfo("Attempting automatic recovery...")
        
        # Determine recovery strategy based on error
        if ($error.ToString() -match "EA|MT5|MetaTrader") {
            $this.MaintenanceManager.AttemptSystemRecovery("EA_Issue")
        }
        elseif ($error.ToString() -match "file|permission|access") {
            $this.MaintenanceManager.AttemptSystemRecovery("File_Permission_Error")
        }
        else {
            $this.Logger.LogWarning("No specific recovery strategy for error: $error")
        }
    }
    
    # Check if we should optimize for cloning
    [bool] ShouldOptimizeForCloning() {
        # Optimize once per day or on demand
        $lastOptimization = $this.FileManager.GetLastOptimizationTime()
        return ($lastOptimization -eq $null -or (Get-Date) - $lastOptimization -gt [TimeSpan]::FromHours(24))
    }
    
    # Stop the agent gracefully
    [void] Stop() {
        Write-Host "`n⏹️ Stopping BiTTen Dual Agent..." -ForegroundColor Yellow
        $this.Running = $false
        $this.Configuration.Running = $false
        
        # Save current configuration
        $this.Configuration | ConvertTo-Json | Set-Content $this.ConfigPath
        
        # Final health report
        $this.ReportHealth()
        
        Write-Host "✅ Agent stopped gracefully" -ForegroundColor Green
    }
}

# Simple logger class
class Logger {
    [string]$LogPath
    [string]$LogFile
    
    Logger([string]$path) {
        $this.LogPath = $path
        $this.LogFile = Join-Path $path "bitten_agent_$(Get-Date -Format 'yyyyMMdd').log"
        
        if (-not (Test-Path $this.LogPath)) {
            New-Item -ItemType Directory -Path $this.LogPath -Force | Out-Null
        }
    }
    
    [void] Log([string]$level, [string]$message) {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $logEntry = "[$timestamp] [$level] $message"
        Add-Content -Path $this.LogFile -Value $logEntry
        
        # Also output to console with color
        switch ($level) {
            "ERROR" { Write-Host $logEntry -ForegroundColor Red }
            "WARNING" { Write-Host $logEntry -ForegroundColor Yellow }
            "INFO" { Write-Host $logEntry -ForegroundColor Gray }
            default { Write-Host $logEntry }
        }
    }
    
    [void] LogError([string]$message) { $this.Log("ERROR", $message) }
    [void] LogWarning([string]$message) { $this.Log("WARNING", $message) }
    [void] LogInfo([string]$message) { $this.Log("INFO", $message) }
}

# Main execution
switch ($Action) {
    "run" {
        if (-not $UserUUID) {
            Write-Error "UserUUID is required to run the agent"
            exit 1
        }
        
        $agent = [BiTTenDualAgent]::new($UserUUID, $BrokerType)
        
        # Handle Ctrl+C gracefully
        [Console]::TreatControlCAsInput = $false
        Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action {
            $agent.Stop()
        } | Out-Null
        
        $agent.RunAgent()
    }
    
    "install" {
        & "$PSScriptRoot\Install-BiTTenAgent.ps1" -UserUUID $UserUUID -BrokerType $BrokerType
    }
    
    "commission" {
        & "$PSScriptRoot\Commission-BiTTenAgent.ps1" -UserUUID $UserUUID
    }
    
    default {
        Write-Host "Usage: BiTTenDualAgent.ps1 -Action <run|install|commission> -UserUUID <uuid> [-BrokerType <type>]"
    }
}