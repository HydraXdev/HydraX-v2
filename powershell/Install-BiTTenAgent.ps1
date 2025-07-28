# Install-BiTTenAgent.ps1 - Installation Script for BiTTen Dual Agent

param(
    [Parameter(Mandatory=$true)]
    [string]$UserUUID,
    
    [string]$BrokerType = "auto-detect",
    [string]$InstallPath = "C:\BiTTen\Agent"
)

Write-Host @"
╔═══════════════════════════════════════════════════════════╗
║            BiTTen Dual Agent Installation                 ║
║         Windows VPS Guardian & Intelligence System        ║
╚═══════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

# Check if running as administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error "This script must be run as Administrator. Please restart PowerShell as Administrator and try again."
    exit 1
}

# Create installation directory structure
Write-Host "`n📁 Creating directory structure..." -ForegroundColor Yellow
$directories = @(
    $InstallPath,
    "$InstallPath\Modules",
    "$InstallPath\Logs",
    "$InstallPath\Config",
    "$InstallPath\Tools"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "   ✓ Created: $dir" -ForegroundColor Gray
    }
}

# Copy agent files
Write-Host "`n📄 Copying agent files..." -ForegroundColor Yellow
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

# Copy main script
Copy-Item "$scriptRoot\BiTTenDualAgent.ps1" "$InstallPath\" -Force
Write-Host "   ✓ Copied main agent script" -ForegroundColor Gray

# Copy modules
Get-ChildItem "$scriptRoot\Modules" -Filter "*.psm1" | ForEach-Object {
    Copy-Item $_.FullName "$InstallPath\Modules\" -Force
    Write-Host "   ✓ Copied module: $($_.Name)" -ForegroundColor Gray
}

# Copy this installer for future use
Copy-Item $MyInvocation.MyCommand.Path "$InstallPath\" -Force

# Create configuration file
Write-Host "`n⚙️ Creating configuration..." -ForegroundColor Yellow
$config = @{
    UserUUID = $UserUUID
    BrokerType = $BrokerType
    InstallPath = $InstallPath
    LogPath = "$InstallPath\Logs"
    MT5Path = "C:\Program Files\MetaTrader 5\MQL5\Files"
    MonitorInterval = 10
    MaintenanceHour = 3
    EnableAutoRecovery = $true
    EnableMetricsReporting = $true
    MetricsEndpoint = "https://terminus.joinbitten.com/metrics"
    HealthCheckInterval = 60
    FileCleanupDays = 7
    MaxLogSizeMB = 100
    InstalledAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Version = "1.0.0"
}

$config | ConvertTo-Json -Depth 5 | Set-Content "$InstallPath\Config\agent_config.json"
Write-Host "   ✓ Configuration created" -ForegroundColor Gray

# Download and install NSSM (Non-Sucking Service Manager)
Write-Host "`n🔧 Installing service manager..." -ForegroundColor Yellow
$nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
$nssmZip = "$InstallPath\Tools\nssm.zip"
$nssmPath = "$InstallPath\Tools\nssm.exe"

if (-not (Test-Path $nssmPath)) {
    try {
        # Download NSSM
        Write-Host "   Downloading NSSM..." -ForegroundColor Gray
        Invoke-WebRequest -Uri $nssmUrl -OutFile $nssmZip -UseBasicParsing
        
        # Extract NSSM
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [System.IO.Compression.ZipFile]::ExtractToDirectory($nssmZip, "$InstallPath\Tools\nssm_temp")
        
        # Copy the appropriate version
        if ([Environment]::Is64BitOperatingSystem) {
            Copy-Item "$InstallPath\Tools\nssm_temp\nssm-2.24\win64\nssm.exe" $nssmPath -Force
        } else {
            Copy-Item "$InstallPath\Tools\nssm_temp\nssm-2.24\win32\nssm.exe" $nssmPath -Force
        }
        
        # Cleanup
        Remove-Item "$InstallPath\Tools\nssm_temp" -Recurse -Force
        Remove-Item $nssmZip -Force
        
        Write-Host "   ✓ NSSM installed successfully" -ForegroundColor Gray
    }
    catch {
        Write-Warning "Failed to download NSSM. Manual service installation may be required."
        Write-Warning "Error: $_"
    }
}

# Install as Windows Service
if (Test-Path $nssmPath) {
    Write-Host "`n🚀 Installing Windows service..." -ForegroundColor Yellow
    
    $serviceName = "BiTTenDualAgent"
    $serviceDisplayName = "BiTTen Dual Agent - $UserUUID"
    $serviceDescription = "BiTTen Windows VPS Guardian Agent for user $UserUUID"
    
    # Remove existing service if present
    $existingService = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
    if ($existingService) {
        Write-Host "   Removing existing service..." -ForegroundColor Gray
        & $nssmPath stop $serviceName | Out-Null
        & $nssmPath remove $serviceName confirm | Out-Null
    }
    
    # Install new service
    Write-Host "   Installing service..." -ForegroundColor Gray
    & $nssmPath install $serviceName powershell.exe | Out-Null
    
    # Configure service
    & $nssmPath set $serviceName Application powershell.exe | Out-Null
    & $nssmPath set $serviceName AppParameters "-ExecutionPolicy Bypass -NoProfile -File `"$InstallPath\BiTTenDualAgent.ps1`" -Action run -UserUUID $UserUUID -BrokerType $BrokerType" | Out-Null
    & $nssmPath set $serviceName AppDirectory $InstallPath | Out-Null
    & $nssmPath set $serviceName DisplayName "$serviceDisplayName" | Out-Null
    & $nssmPath set $serviceName Description "$serviceDescription" | Out-Null
    & $nssmPath set $serviceName Start SERVICE_AUTO_START | Out-Null
    
    # Configure service recovery
    & $nssmPath set $serviceName AppExit Default Restart | Out-Null
    & $nssmPath set $serviceName AppRestartDelay 30000 | Out-Null
    
    # Configure logging
    & $nssmPath set $serviceName AppStdout "$InstallPath\Logs\service_stdout.log" | Out-Null
    & $nssmPath set $serviceName AppStderr "$InstallPath\Logs\service_stderr.log" | Out-Null
    & $nssmPath set $serviceName AppStdoutCreationDisposition 2 | Out-Null
    & $nssmPath set $serviceName AppStderrCreationDisposition 2 | Out-Null
    & $nssmPath set $serviceName AppRotateFiles 1 | Out-Null
    & $nssmPath set $serviceName AppRotateOnline 1 | Out-Null
    & $nssmPath set $serviceName AppRotateBytes 10485760 | Out-Null
    
    Write-Host "   ✓ Service installed successfully" -ForegroundColor Gray
    
    # Set service to run as SYSTEM
    Write-Host "   Setting service permissions..." -ForegroundColor Gray
    sc.exe config $serviceName obj= "LocalSystem" | Out-Null
    
    Write-Host "   ✓ Service configured" -ForegroundColor Gray
}

# Create scheduled task for manual runs (backup)
Write-Host "`n📅 Creating scheduled task..." -ForegroundColor Yellow
$taskName = "BiTTenDualAgent_$UserUUID"
$taskPath = "\BiTTen\"

# Remove existing task if present
Unregister-ScheduledTask -TaskName $taskName -TaskPath $taskPath -Confirm:$false -ErrorAction SilentlyContinue

# Create new task
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -File `"$InstallPath\BiTTenDualAgent.ps1`" -Action run -UserUUID $UserUUID -BrokerType $BrokerType"

$trigger = New-ScheduledTaskTrigger -AtStartup -RandomDelay (New-TimeSpan -Minutes 1)

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0)

$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName $taskName `
    -TaskPath $taskPath `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "BiTTen Dual Agent for user $UserUUID" | Out-Null

Write-Host "   ✓ Scheduled task created" -ForegroundColor Gray

# Create desktop shortcut
Write-Host "`n🔗 Creating shortcuts..." -ForegroundColor Yellow
$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = "$desktopPath\BiTTen Agent Console.lnk"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "powershell.exe"
$shortcut.Arguments = "-ExecutionPolicy Bypass -NoExit -File `"$InstallPath\BiTTenDualAgent.ps1`" -Action run -UserUUID $UserUUID -BrokerType $BrokerType"
$shortcut.WorkingDirectory = $InstallPath
$shortcut.IconLocation = "powershell.exe,0"
$shortcut.Description = "BiTTen Dual Agent Console"
$shortcut.Save()

Write-Host "   ✓ Desktop shortcut created" -ForegroundColor Gray

# Create start menu shortcut
$startMenuPath = [Environment]::GetFolderPath("CommonPrograms")
$bittenFolder = "$startMenuPath\BiTTen"
if (-not (Test-Path $bittenFolder)) {
    New-Item -ItemType Directory -Path $bittenFolder -Force | Out-Null
}

$startShortcut = "$bittenFolder\BiTTen Agent.lnk"
$shortcut = $shell.CreateShortcut($startShortcut)
$shortcut.TargetPath = "powershell.exe"
$shortcut.Arguments = "-ExecutionPolicy Bypass -NoExit -File `"$InstallPath\BiTTenDualAgent.ps1`" -Action run -UserUUID $UserUUID -BrokerType $BrokerType"
$shortcut.WorkingDirectory = $InstallPath
$shortcut.IconLocation = "powershell.exe,0"
$shortcut.Description = "BiTTen Dual Agent"
$shortcut.Save()

Write-Host "   ✓ Start menu shortcut created" -ForegroundColor Gray

# Create uninstaller
Write-Host "`n📝 Creating uninstaller..." -ForegroundColor Yellow
$uninstaller = @'
# Uninstall-BiTTenAgent.ps1
param([switch]$Force)

$serviceName = "BiTTenDualAgent"
$installPath = $PSScriptRoot

Write-Host "Uninstalling BiTTen Dual Agent..." -ForegroundColor Yellow

# Stop and remove service
$service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
if ($service) {
    Write-Host "Stopping service..." -ForegroundColor Gray
    Stop-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
    
    $nssmPath = "$installPath\Tools\nssm.exe"
    if (Test-Path $nssmPath) {
        & $nssmPath remove $serviceName confirm
    } else {
        sc.exe delete $serviceName
    }
}

# Remove scheduled task
$taskName = "BiTTenDualAgent_*"
Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false

# Remove shortcuts
Remove-Item "$([Environment]::GetFolderPath('Desktop'))\BiTTen Agent Console.lnk" -Force -ErrorAction SilentlyContinue
Remove-Item "$([Environment]::GetFolderPath('CommonPrograms'))\BiTTen" -Recurse -Force -ErrorAction SilentlyContinue

if ($Force) {
    # Remove installation directory
    Remove-Item $installPath -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "BiTTen Dual Agent completely removed." -ForegroundColor Green
} else {
    Write-Host "BiTTen Dual Agent uninstalled. Configuration and logs preserved in: $installPath" -ForegroundColor Green
    Write-Host "Use -Force parameter to completely remove all files." -ForegroundColor Gray
}
'@

$uninstaller | Set-Content "$InstallPath\Uninstall-BiTTenAgent.ps1"
Write-Host "   ✓ Uninstaller created" -ForegroundColor Gray

# Display installation summary
Write-Host "`n" -NoNewline
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "       BiTTen Dual Agent Installation Complete!             " -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Installation Path: $InstallPath" -ForegroundColor Cyan
Write-Host "👤 User UUID: $UserUUID" -ForegroundColor Cyan
Write-Host "🏢 Broker Type: $BrokerType" -ForegroundColor Cyan
Write-Host ""
Write-Host "🚀 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Start the service: " -NoNewline
Write-Host "Start-Service BiTTenDualAgent" -ForegroundColor White
Write-Host "   2. Check service status: " -NoNewline
Write-Host "Get-Service BiTTenDualAgent" -ForegroundColor White
Write-Host "   3. View logs: " -NoNewline
Write-Host "Get-Content '$InstallPath\Logs\*.log' -Tail 50" -ForegroundColor White
Write-Host "   4. Run commissioning: " -NoNewline
Write-Host "& '$InstallPath\BiTTenDualAgent.ps1' -Action commission -UserUUID $UserUUID" -ForegroundColor White
Write-Host ""
Write-Host "📖 For manual operation, use the desktop shortcut or run:" -ForegroundColor Gray
Write-Host "   & '$InstallPath\BiTTenDualAgent.ps1' -Action run -UserUUID $UserUUID" -ForegroundColor White
Write-Host ""

# Ask if user wants to start the service now
$response = Read-Host "Would you like to start the BiTTen Dual Agent service now? (Y/N)"
if ($response -eq 'Y' -or $response -eq 'y') {
    Write-Host "`nStarting service..." -ForegroundColor Yellow
    Start-Service -Name "BiTTenDualAgent" -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    
    $service = Get-Service -Name "BiTTenDualAgent" -ErrorAction SilentlyContinue
    if ($service -and $service.Status -eq "Running") {
        Write-Host "✅ Service started successfully!" -ForegroundColor Green
    } else {
        Write-Warning "Service failed to start. Please check the logs at: $InstallPath\Logs\"
    }
}

Write-Host "`n✨ Installation complete!" -ForegroundColor Green