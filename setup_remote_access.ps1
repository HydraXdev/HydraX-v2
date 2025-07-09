# Enable PowerShell Remoting on Windows AWS Instance
# Run this ON THE WINDOWS SERVER as Administrator

# 1. Enable WinRM
Enable-PSRemoting -Force

# 2. Set trusted hosts (from this Linux server)
Set-Item WSMan:\localhost\Client\TrustedHosts -Value "134.199.204.67" -Force

# 3. Configure firewall
New-NetFirewallRule -DisplayName "WinRM HTTPS" -Direction Inbound -LocalPort 5986 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "WinRM HTTP" -Direction Inbound -LocalPort 5985 -Protocol TCP -Action Allow

# 4. Create a quick listener
winrm quickconfig -quiet

# 5. Allow unencrypted (for testing only)
winrm set winrm/config/service '@{AllowUnencrypted="true"}'

Write-Host "Remote PowerShell enabled!" -ForegroundColor Green
Write-Host "From Linux, connect with:" -ForegroundColor Yellow
Write-Host 'Enter-PSSession -ComputerName YOUR_WINDOWS_IP -Credential (Get-Credential)'