# BrokerHandler.psm1 - Broker Compatibility and Symbol Translation Module

class BrokerCompatibilityManager {
    [hashtable]$SymbolMappings
    [string]$DetectedBroker
    [hashtable]$BrokerProfiles
    [string]$MT5TerminalPath = "C:\Program Files\MetaTrader 5"
    
    BrokerCompatibilityManager() {
        $this.InitializeBrokerProfiles()
        $this.SymbolMappings = @{}
    }
    
    [void] InitializeBrokerProfiles() {
        # Define known broker profiles with their characteristics
        $this.BrokerProfiles = @{
            "MetaQuotes-Demo" = @{
                SymbolSuffix = ""
                SymbolPrefix = ""
                HasMicroLots = $true
                MinLotSize = 0.01
                SpecialSymbols = @{}
            }
            "Coinexx" = @{
                SymbolSuffix = ""
                SymbolPrefix = ""
                HasMicroLots = $true
                MinLotSize = 0.01
                SpecialSymbols = @{}
            }
            "IC_Markets" = @{
                SymbolSuffix = ""
                SymbolPrefix = ""
                HasMicroLots = $true
                MinLotSize = 0.01
                SpecialSymbols = @{
                    "XAUUSD" = "GOLD"
                    "XAGUSD" = "SILVER"
                }
            }
            "Pepperstone" = @{
                SymbolSuffix = "_"
                SymbolPrefix = ""
                HasMicroLots = $true
                MinLotSize = 0.01
                SpecialSymbols = @{}
            }
            "OANDA" = @{
                SymbolSuffix = ""
                SymbolPrefix = ""
                HasMicroLots = $true
                MinLotSize = 0.01
                SpecialSymbols = @{
                    "EURUSD" = "EUR_USD"
                    "GBPUSD" = "GBP_USD"
                    "USDJPY" = "USD_JPY"
                }
            }
            "FOREX.com" = @{
                SymbolSuffix = ".a"
                SymbolPrefix = ""
                HasMicroLots = $true
                MinLotSize = 0.01
                SpecialSymbols = @{}
            }
            "Eightcap" = @{
                SymbolSuffix = ""
                SymbolPrefix = ""
                HasMicroLots = $true
                MinLotSize = 0.01
                SpecialSymbols = @{}
            }
            "HugosWay" = @{
                SymbolSuffix = ""
                SymbolPrefix = ""
                HasMicroLots = $true
                MinLotSize = 0.01
                SpecialSymbols = @{}
            }
        }
    }
    
    # Auto-detect broker type
    [string] DetectBrokerType() {
        Write-Host "🔍 Detecting broker type..." -ForegroundColor Cyan
        
        try {
            # Method 1: Check server configuration
            $serverConfig = $this.GetMT5ServerConfig()
            if ($serverConfig) {
                foreach ($brokerName in $this.BrokerProfiles.Keys) {
                    if ($serverConfig -match $brokerName) {
                        $this.DetectedBroker = $brokerName
                        return $brokerName
                    }
                }
            }
            
            # Method 2: Check available symbols
            $symbols = $this.GetAvailableSymbols()
            $detectedBroker = $this.AnalyzeSymbolPatterns($symbols)
            
            if ($detectedBroker) {
                $this.DetectedBroker = $detectedBroker
                return $detectedBroker
            }
            
            # Method 3: Check terminal.ini for broker info
            $terminalInfo = $this.GetTerminalInfo()
            if ($terminalInfo.Server) {
                foreach ($brokerName in $this.BrokerProfiles.Keys) {
                    if ($terminalInfo.Server -match $brokerName) {
                        $this.DetectedBroker = $brokerName
                        return $brokerName
                    }
                }
            }
            
            # Default to generic broker
            Write-Warning "Could not auto-detect broker, using generic profile"
            $this.DetectedBroker = "Generic"
            return "Generic"
        }
        catch {
            Write-Error "Error detecting broker: $_"
            return "Unknown"
        }
    }
    
    # Get MT5 server configuration
    [string] GetMT5ServerConfig() {
        try {
            $configPath = Join-Path $this.MT5TerminalPath "config\servers.dat"
            if (Test-Path $configPath) {
                # Read binary file and look for server strings
                $content = [System.IO.File]::ReadAllBytes($configPath)
                $text = [System.Text.Encoding]::ASCII.GetString($content)
                
                # Extract server names
                if ($text -match "Server=([^\r\n]+)") {
                    return $matches[1]
                }
            }
            
            # Alternative: Check recent server files
            $serversPath = Join-Path $this.MT5TerminalPath "config\servers"
            if (Test-Path $serversPath) {
                $latestServer = Get-ChildItem -Path $serversPath -Filter "*.srv" | 
                                Sort-Object LastWriteTime -Descending | 
                                Select-Object -First 1
                
                if ($latestServer) {
                    return $latestServer.BaseName
                }
            }
        }
        catch {
            Write-Warning "Failed to get MT5 server config: $_"
        }
        
        return $null
    }
    
    # Get available symbols from MT5
    [array] GetAvailableSymbols() {
        $symbols = @()
        
        try {
            # Method 1: Read from symbols file
            $symbolsPath = Join-Path $this.MT5TerminalPath "config\symbols.sel"
            if (Test-Path $symbolsPath) {
                $content = Get-Content $symbolsPath -Raw
                
                # Extract symbol names (basic pattern matching)
                $matches = [regex]::Matches($content, '[A-Z]{6}[._]?[a-zA-Z]*')
                foreach ($match in $matches) {
                    $symbols += $match.Value
                }
            }
            
            # Method 2: Check market watch file
            $marketWatchPath = Join-Path $this.MT5TerminalPath "profiles\default\marketwatch.dat"
            if (Test-Path $marketWatchPath) {
                # This is a binary file, so we do basic string extraction
                $content = [System.IO.File]::ReadAllBytes($marketWatchPath)
                $text = [System.Text.Encoding]::Unicode.GetString($content)
                
                # Look for common forex pairs
                $commonPairs = @("EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD", 
                                "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY")
                
                foreach ($pair in $commonPairs) {
                    if ($text -match "$pair[._]?[a-zA-Z]*") {
                        $symbols += $matches[0]
                    }
                }
            }
            
            # Remove duplicates
            $symbols = $symbols | Select-Object -Unique
        }
        catch {
            Write-Warning "Failed to get available symbols: $_"
        }
        
        # If no symbols found, return standard list
        if ($symbols.Count -eq 0) {
            $symbols = @("EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD",
                        "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY",
                        "GBPNZD", "GBPAUD", "EURAUD", "GBPCHF", "AUDJPY")
        }
        
        return $symbols
    }
    
    # Analyze symbol patterns to detect broker
    [string] AnalyzeSymbolPatterns([array]$symbols) {
        # Check for common broker-specific patterns
        
        # FOREX.com uses .a suffix
        if ($symbols | Where-Object { $_ -match "\.a$" }) {
            return "FOREX.com"
        }
        
        # Pepperstone uses _ suffix
        if ($symbols | Where-Object { $_ -match "_$" }) {
            return "Pepperstone"
        }
        
        # OANDA uses underscore format
        if ($symbols | Where-Object { $_ -match "^[A-Z]{3}_[A-Z]{3}$" }) {
            return "OANDA"
        }
        
        # IC Markets might have GOLD instead of XAUUSD
        if ($symbols -contains "GOLD" -and $symbols -notcontains "XAUUSD") {
            return "IC_Markets"
        }
        
        # Check for exact matches with known brokers
        foreach ($broker in $this.BrokerProfiles.Keys) {
            $profile = $this.BrokerProfiles[$broker]
            $suffix = $profile.SymbolSuffix
            
            if ($suffix -and ($symbols | Where-Object { $_ -match "$suffix$" })) {
                return $broker
            }
        }
        
        return $null
    }
    
    # Get terminal information
    [hashtable] GetTerminalInfo() {
        $info = @{
            Server = ""
            Login = ""
            Path = $this.MT5TerminalPath
        }
        
        try {
            $terminalIni = Join-Path $this.MT5TerminalPath "config\terminal.ini"
            if (Test-Path $terminalIni) {
                $content = Get-Content $terminalIni
                
                foreach ($line in $content) {
                    if ($line -match "Server=(.+)") {
                        $info.Server = $matches[1]
                    }
                    elseif ($line -match "Login=(.+)") {
                        $info.Login = $matches[1]
                    }
                }
            }
        }
        catch {
            Write-Warning "Failed to read terminal info: $_"
        }
        
        return $info
    }
    
    # Build symbol translation mappings
    [hashtable] BuildSymbolMappings() {
        Write-Host "📊 Building symbol mappings for $($this.DetectedBroker)..." -ForegroundColor Cyan
        
        $mappings = @{}
        
        # BITTEN standard symbols (15 pairs without XAUUSD)
        $bittenSymbols = @("EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD",
                          "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY",
                          "GBPNZD", "GBPAUD", "EURAUD", "GBPCHF", "AUDJPY")
        
        # Get broker profile
        $profile = $this.BrokerProfiles[$this.DetectedBroker]
        if (-not $profile) {
            # Create generic profile
            $profile = @{
                SymbolSuffix = ""
                SymbolPrefix = ""
                SpecialSymbols = @{}
            }
        }
        
        # Build mappings based on broker profile
        foreach ($symbol in $bittenSymbols) {
            # Check for special mapping first
            if ($profile.SpecialSymbols.ContainsKey($symbol)) {
                $mappings[$symbol] = $profile.SpecialSymbols[$symbol]
            }
            else {
                # Apply standard prefix/suffix
                $brokerSymbol = $profile.SymbolPrefix + $symbol + $profile.SymbolSuffix
                $mappings[$symbol] = $brokerSymbol
            }
        }
        
        # Verify mappings against available symbols
        $availableSymbols = $this.GetAvailableSymbols()
        $validatedMappings = @{}
        
        foreach ($key in $mappings.Keys) {
            $brokerSymbol = $mappings[$key]
            
            # Check if broker symbol exists
            if ($brokerSymbol -in $availableSymbols) {
                $validatedMappings[$key] = $brokerSymbol
            }
            else {
                # Try to find a match
                $found = $availableSymbols | Where-Object { $_ -like "*$key*" } | Select-Object -First 1
                if ($found) {
                    $validatedMappings[$key] = $found
                    Write-Warning "Mapped $key to $found (auto-detected)"
                }
                else {
                    # Use original if no match found
                    $validatedMappings[$key] = $key
                    Write-Warning "No broker symbol found for $key, using standard"
                }
            }
        }
        
        $this.SymbolMappings = $validatedMappings
        
        Write-Host "✅ Symbol mappings created for $($validatedMappings.Count) pairs" -ForegroundColor Green
        
        return $validatedMappings
    }
    
    # Validate symbol mappings
    [array] ValidateSymbolMappings() {
        $invalidSymbols = @()
        $availableSymbols = $this.GetAvailableSymbols()
        
        foreach ($key in $this.SymbolMappings.Keys) {
            $brokerSymbol = $this.SymbolMappings[$key]
            
            if ($brokerSymbol -notin $availableSymbols) {
                $invalidSymbols += $key
            }
        }
        
        return $invalidSymbols
    }
    
    # Get symbol mappings
    [hashtable] GetSymbolMappings() {
        if ($this.SymbolMappings.Count -eq 0) {
            $this.BuildSymbolMappings()
        }
        return $this.SymbolMappings
    }
    
    # Translate BITTEN symbol to broker symbol
    [string] TranslateSymbol([string]$bittenSymbol) {
        if ($this.SymbolMappings.ContainsKey($bittenSymbol)) {
            return $this.SymbolMappings[$bittenSymbol]
        }
        
        # If no mapping exists, return original
        Write-Warning "No mapping found for symbol: $bittenSymbol"
        return $bittenSymbol
    }
    
    # Translate broker symbol back to BITTEN symbol
    [string] ReverseTranslateSymbol([string]$brokerSymbol) {
        foreach ($key in $this.SymbolMappings.Keys) {
            if ($this.SymbolMappings[$key] -eq $brokerSymbol) {
                return $key
            }
        }
        
        # Try to extract base symbol
        $baseSymbol = $brokerSymbol -replace '[._-].*$', ''
        if ($baseSymbol -match '^[A-Z]{6}$') {
            return $baseSymbol
        }
        
        return $brokerSymbol
    }
    
    # Apply broker-specific optimizations
    [void] OptimizeForBroker() {
        Write-Host "⚙️ Applying optimizations for $($this.DetectedBroker)..." -ForegroundColor Cyan
        
        switch ($this.DetectedBroker) {
            "IC_Markets" {
                $this.SetICMarketsOptimizations()
            }
            "Pepperstone" {
                $this.SetPepperstoneOptimizations()
            }
            "OANDA" {
                $this.SetOANDAOptimizations()
            }
            "FOREX.com" {
                $this.SetForexComOptimizations()
            }
            default {
                $this.SetGenericOptimizations()
            }
        }
    }
    
    # IC Markets specific optimizations
    [void] SetICMarketsOptimizations() {
        # IC Markets has good execution, optimize for speed
        Write-Host "   • Optimizing for IC Markets fast execution" -ForegroundColor Gray
        
        # Set environment variables for EA
        [Environment]::SetEnvironmentVariable("BROKER_EXECUTION_MODE", "FAST", "Process")
        [Environment]::SetEnvironmentVariable("BROKER_SLIPPAGE_MAX", "2", "Process")
    }
    
    # Pepperstone specific optimizations  
    [void] SetPepperstoneOptimizations() {
        Write-Host "   • Optimizing for Pepperstone symbol format" -ForegroundColor Gray
        
        [Environment]::SetEnvironmentVariable("BROKER_SYMBOL_SUFFIX", "_", "Process")
        [Environment]::SetEnvironmentVariable("BROKER_EXECUTION_MODE", "STANDARD", "Process")
    }
    
    # OANDA specific optimizations
    [void] SetOANDAOptimizations() {
        Write-Host "   • Optimizing for OANDA underscore format" -ForegroundColor Gray
        
        [Environment]::SetEnvironmentVariable("BROKER_SYMBOL_FORMAT", "UNDERSCORE", "Process")
        [Environment]::SetEnvironmentVariable("BROKER_PRECISION_MODE", "HIGH", "Process")
    }
    
    # FOREX.com specific optimizations
    [void] SetForexComOptimizations() {
        Write-Host "   • Optimizing for FOREX.com suffix symbols" -ForegroundColor Gray
        
        [Environment]::SetEnvironmentVariable("BROKER_SYMBOL_SUFFIX", ".a", "Process")
        [Environment]::SetEnvironmentVariable("BROKER_EXECUTION_MODE", "STANDARD", "Process")
    }
    
    # Generic broker optimizations
    [void] SetGenericOptimizations() {
        Write-Host "   • Applying generic broker optimizations" -ForegroundColor Gray
        
        [Environment]::SetEnvironmentVariable("BROKER_EXECUTION_MODE", "STANDARD", "Process")
        [Environment]::SetEnvironmentVariable("BROKER_SLIPPAGE_MAX", "3", "Process")
    }
    
    # Export broker configuration
    [void] ExportBrokerConfig([string]$path) {
        $config = @{
            DetectedBroker = $this.DetectedBroker
            SymbolMappings = $this.SymbolMappings
            BrokerProfile = $this.BrokerProfiles[$this.DetectedBroker]
            Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        }
        
        $config | ConvertTo-Json -Depth 5 | Set-Content $path
    }
}

# Export the class
Export-ModuleMember -Function * -Cmdlet * -Variable * -Alias *