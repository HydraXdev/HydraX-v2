# FileManager.psm1 - Intelligent File Management Module

class IntelligentFileManager {
    [string]$WorkingDirectory
    [string]$ArchiveDirectory
    [hashtable]$FilePatterns
    [object]$Logger
    [datetime]$LastOptimization
    
    IntelligentFileManager([string]$mt5Path) {
        $this.WorkingDirectory = Join-Path $mt5Path "BITTEN"
        $this.ArchiveDirectory = Join-Path $this.WorkingDirectory "archive"
        $this.InitializeFileManager()
    }
    
    [void] InitializeFileManager() {
        # Create necessary directories
        @($this.WorkingDirectory, $this.ArchiveDirectory, 
          (Join-Path $this.WorkingDirectory "processed"),
          (Join-Path $this.WorkingDirectory "failed")) | ForEach-Object {
            if (-not (Test-Path $_)) {
                New-Item -ItemType Directory -Path $_ -Force | Out-Null
            }
        }
        
        # Define file patterns
        $this.FilePatterns = @{
            SignalFiles = @("fire.txt", "trade_signal.json", "signal_*.json")
            ResultFiles = @("trade_result.txt", "result_*.json", "confirmation_*.json")
            TickDataFiles = @("tick_data_*.json")
            LogFiles = @("*.log", "*.txt")
        }
    }
    
    # Monitor and manage signal files
    [void] ManageSignalFiles() {
        try {
            # Check for new signal files
            $newSignals = $this.DetectNewSignalFiles()
            
            foreach ($signal in $newSignals) {
                # Validate signal file
                if ($this.ValidateSignalFile($signal)) {
                    $this.LogSignalProcessing($signal)
                    
                    # Check if signal was processed (file should be empty or have result)
                    Start-Sleep -Seconds 2
                    if ($this.IsSignalProcessed($signal)) {
                        $this.ArchiveSignalFile($signal)
                    }
                }
                else {
                    # Move invalid signals to failed directory
                    $this.MoveToFailed($signal)
                }
            }
            
            # Clean up processed signals
            $this.CleanupProcessedSignals()
            
        }
        catch {
            Write-Warning "Error managing signal files: $_"
        }
    }
    
    # Detect new signal files
    [array] DetectNewSignalFiles() {
        $signals = @()
        
        # Check fire.txt
        $fireFile = Join-Path $this.WorkingDirectory "fire.txt"
        if (Test-Path $fireFile) {
            $content = Get-Content $fireFile -Raw
            if ($content -and $content.Trim().Length -gt 0) {
                $signals += [PSCustomObject]@{
                    Path = $fireFile
                    Content = $content
                    Type = "fire"
                    Timestamp = (Get-Item $fireFile).LastWriteTime
                }
            }
        }
        
        # Check for other signal files
        Get-ChildItem -Path $this.WorkingDirectory -Filter "signal_*.json" | ForEach-Object {
            $signals += [PSCustomObject]@{
                Path = $_.FullName
                Content = Get-Content $_.FullName -Raw
                Type = "signal"
                Timestamp = $_.LastWriteTime
            }
        }
        
        return $signals
    }
    
    # Validate signal file format
    [bool] ValidateSignalFile([object]$signal) {
        try {
            # Attempt to parse as JSON
            $json = $signal.Content | ConvertFrom-Json
            
            # Check required fields for trade signals
            $requiredFields = @("symbol", "type", "lot")
            $hasRequiredFields = $true
            
            foreach ($field in $requiredFields) {
                if (-not $json.PSObject.Properties[$field]) {
                    $hasRequiredFields = $false
                    break
                }
            }
            
            # Validate field values
            if ($hasRequiredFields) {
                # Check symbol is valid (15 pairs without XAUUSD)
                $validSymbols = @("EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD",
                                  "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY",
                                  "GBPNZD", "GBPAUD", "EURAUD", "GBPCHF", "AUDJPY")
                
                if ($json.symbol -notin $validSymbols) {
                    Write-Warning "Invalid symbol: $($json.symbol)"
                    return $false
                }
                
                # Check type is valid
                if ($json.type -notin @("buy", "sell", "close")) {
                    Write-Warning "Invalid trade type: $($json.type)"
                    return $false
                }
                
                # Check lot size is reasonable
                if ($json.lot -le 0 -or $json.lot -gt 100) {
                    Write-Warning "Invalid lot size: $($json.lot)"
                    return $false
                }
            }
            
            return $hasRequiredFields
        }
        catch {
            Write-Warning "Failed to validate signal file: $_"
            return $false
        }
    }
    
    # Log signal processing
    [void] LogSignalProcessing([object]$signal) {
        $logEntry = @{
            Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            SignalType = $signal.Type
            FilePath = $signal.Path
            Status = "Processing"
        }
        
        $logFile = Join-Path $this.WorkingDirectory "signal_log.json"
        
        # Append to log file
        try {
            $logs = @()
            if (Test-Path $logFile) {
                $logs = Get-Content $logFile -Raw | ConvertFrom-Json
            }
            $logs += $logEntry
            
            # Keep only last 1000 entries
            if ($logs.Count -gt 1000) {
                $logs = $logs[-1000..-1]
            }
            
            $logs | ConvertTo-Json -Depth 5 | Set-Content $logFile
        }
        catch {
            Write-Warning "Failed to log signal processing: $_"
        }
    }
    
    # Check if signal was processed
    [bool] IsSignalProcessed([object]$signal) {
        if ($signal.Type -eq "fire") {
            # For fire.txt, check if file is empty (EA clears it after processing)
            $content = Get-Content $signal.Path -Raw
            return (-not $content -or $content.Trim().Length -eq 0)
        }
        else {
            # For other signals, check for corresponding result file
            $resultFile = $signal.Path -replace "signal_", "result_"
            return (Test-Path $resultFile)
        }
    }
    
    # Archive processed signal file
    [void] ArchiveSignalFile([object]$signal) {
        try {
            $archiveDate = Get-Date -Format "yyyyMMdd"
            $archivePath = Join-Path $this.ArchiveDirectory $archiveDate
            
            if (-not (Test-Path $archivePath)) {
                New-Item -ItemType Directory -Path $archivePath -Force | Out-Null
            }
            
            # Generate unique archive name
            $baseName = [System.IO.Path]::GetFileNameWithoutExtension($signal.Path)
            $extension = [System.IO.Path]::GetExtension($signal.Path)
            $timestamp = Get-Date -Format "HHmmss"
            $archiveName = "${baseName}_${timestamp}${extension}"
            $archiveFullPath = Join-Path $archivePath $archiveName
            
            # Move to archive
            Move-Item -Path $signal.Path -Destination $archiveFullPath -Force
            
            # Also move to processed folder for immediate reference
            $processedPath = Join-Path $this.WorkingDirectory "processed"
            Copy-Item -Path $archiveFullPath -Destination (Join-Path $processedPath $archiveName) -Force
        }
        catch {
            Write-Warning "Failed to archive signal file: $_"
        }
    }
    
    # Move invalid signals to failed directory
    [void] MoveToFailed([object]$signal) {
        try {
            $failedPath = Join-Path $this.WorkingDirectory "failed"
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            $failedName = "failed_${timestamp}_$([System.IO.Path]::GetFileName($signal.Path))"
            
            Move-Item -Path $signal.Path -Destination (Join-Path $failedPath $failedName) -Force
        }
        catch {
            Write-Warning "Failed to move invalid signal: $_"
        }
    }
    
    # Clean up processed signals
    [void] CleanupProcessedSignals() {
        $processedPath = Join-Path $this.WorkingDirectory "processed"
        
        if (Test-Path $processedPath) {
            # Remove files older than 24 hours
            Get-ChildItem -Path $processedPath -File | 
                Where-Object { $_.LastWriteTime -lt (Get-Date).AddHours(-24) } |
                Remove-Item -Force
        }
    }
    
    # Organize files for optimal cloning
    [void] OptimizeForCloning() {
        Write-Host "Optimizing file structure for cloning..." -ForegroundColor Yellow
        
        try {
            # Ensure standard folder structure
            $this.CreateStandardFolders()
            
            # Set proper permissions
            $this.SetOptimalPermissions()
            
            # Clean up temporary files
            $this.CleanupTempFiles()
            
            # Prepare configuration templates
            $this.PrepareConfigTemplates()
            
            $this.LastOptimization = Get-Date
            
            Write-Host "✅ File structure optimized for cloning" -ForegroundColor Green
        }
        catch {
            Write-Warning "Error optimizing for cloning: $_"
        }
    }
    
    # Create standard folder structure
    [void] CreateStandardFolders() {
        $folders = @(
            $this.WorkingDirectory,
            (Join-Path $this.WorkingDirectory "processed"),
            (Join-Path $this.WorkingDirectory "failed"),
            (Join-Path $this.WorkingDirectory "archive"),
            (Join-Path $this.WorkingDirectory "logs"),
            (Join-Path $this.WorkingDirectory "config")
        )
        
        foreach ($folder in $folders) {
            if (-not (Test-Path $folder)) {
                New-Item -ItemType Directory -Path $folder -Force | Out-Null
            }
        }
    }
    
    # Set optimal permissions
    [void] SetOptimalPermissions() {
        try {
            # Grant full control to SYSTEM and current user
            $acl = Get-Acl $this.WorkingDirectory
            $permission = "SYSTEM", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow"
            $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule $permission
            $acl.SetAccessRule($accessRule)
            
            $permission = "$env:USERNAME", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow"
            $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule $permission
            $acl.SetAccessRule($accessRule)
            
            Set-Acl $this.WorkingDirectory $acl
        }
        catch {
            Write-Warning "Failed to set optimal permissions: $_"
        }
    }
    
    # Clean up temporary files
    [void] CleanupTempFiles() {
        # Remove temporary files
        Get-ChildItem -Path $this.WorkingDirectory -Include "*.tmp", "*.temp", "~*" -Recurse | 
            Remove-Item -Force -ErrorAction SilentlyContinue
        
        # Clean up old log files
        Get-ChildItem -Path (Join-Path $this.WorkingDirectory "logs") -Filter "*.log" |
            Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) } |
            Remove-Item -Force -ErrorAction SilentlyContinue
    }
    
    # Prepare configuration templates
    [void] PrepareConfigTemplates() {
        $configPath = Join-Path $this.WorkingDirectory "config"
        
        # Create signal format template
        $signalTemplate = @{
            symbol = "EURUSD"
            type = "buy"
            lot = 0.01
            sl = 0
            tp = 0
            comment = "BITTEN Signal"
            magic = 777001
        }
        
        $signalTemplate | ConvertTo-Json | Set-Content (Join-Path $configPath "signal_template.json")
        
        # Create broker mapping template
        $brokerMapping = @{
            standard = @{
                EURUSD = "EURUSD"
                GBPUSD = "GBPUSD"
                USDJPY = "USDJPY"
            }
            suffixed = @{
                EURUSD = "EURUSD.a"
                GBPUSD = "GBPUSD.a"
                USDJPY = "USDJPY.a"
            }
        }
        
        $brokerMapping | ConvertTo-Json -Depth 3 | Set-Content (Join-Path $configPath "broker_mappings.json")
    }
    
    # Clean up old files based on retention policy
    [void] CleanupOldFiles([int]$retentionDays) {
        $cutoffDate = (Get-Date).AddDays(-$retentionDays)
        
        # Clean up archive
        Get-ChildItem -Path $this.ArchiveDirectory -Directory |
            Where-Object { $_.CreationTime -lt $cutoffDate } |
            Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
            
        # Clean up old tick data files
        Get-ChildItem -Path $this.WorkingDirectory -Filter "tick_data_*.json" |
            Where-Object { $_.LastWriteTime -lt (Get-Date).AddHours(-1) } |
            Remove-Item -Force -ErrorAction SilentlyContinue
    }
    
    # Handle file corruption recovery
    [bool] RecoverCorruptedFile([string]$filepath) {
        try {
            # Attempt to read and validate file
            $content = Get-Content $filepath -Raw -ErrorAction Stop
            $json = $content | ConvertFrom-Json -ErrorAction Stop
            return $true
        }
        catch {
            Write-Warning "Corrupted file detected: $filepath"
            
            # Try backup recovery
            $backupPath = "$filepath.backup"
            if (Test-Path $backupPath) {
                try {
                    Copy-Item -Path $backupPath -Destination $filepath -Force
                    Write-Host "File recovered from backup: $filepath" -ForegroundColor Green
                    return $true
                }
                catch {
                    Write-Error "Failed to recover from backup: $_"
                }
            }
            
            # If no backup, create empty file
            try {
                "" | Set-Content $filepath -Force
                Write-Host "Created new empty file: $filepath" -ForegroundColor Yellow
                return $true
            }
            catch {
                Write-Error "Failed to create new file: $_"
                return $false
            }
        }
    }
    
    # Get last optimization time
    [datetime] GetLastOptimizationTime() {
        return $this.LastOptimization
    }
}

# Export the class
Export-ModuleMember -Function * -Cmdlet * -Variable * -Alias *