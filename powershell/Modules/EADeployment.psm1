# EADeployment.psm1 - EA Deployment and Fire.txt Management Module

class EADeploymentManager {
    [string]$MT5Path
    [string]$ExpertsPath
    [string]$FilesPath
    [string]$BittenPath
    [hashtable]$CurrencyPairs
    
    EADeploymentManager() {
        $this.InitializeManager()
    }
    
    [void] InitializeManager() {
        # Auto-detect MT5 installation
        $this.MT5Path = $this.FindMT5Installation()
        
        if ($this.MT5Path) {
            $this.ExpertsPath = Join-Path $this.MT5Path "MQL5\Experts"
            $this.FilesPath = Join-Path $this.MT5Path "MQL5\Files"
            $this.BittenPath = Join-Path $this.FilesPath "BITTEN"
        }
        
        # Define the official 15 currency pairs (NO XAUUSD)
        $this.CurrencyPairs = @{
            1  = "EURUSD"
            2  = "GBPUSD"
            3  = "USDJPY"
            4  = "USDCAD"
            5  = "AUDUSD"
            6  = "USDCHF"
            7  = "NZDUSD"
            8  = "EURGBP"
            9  = "EURJPY"
            10 = "GBPJPY"
            11 = "GBPNZD"
            12 = "GBPAUD"
            13 = "EURAUD"
            14 = "GBPCHF"
            15 = "AUDJPY"
        }
    }
    
    # Find MT5 installation path
    [string] FindMT5Installation() {
        $possiblePaths = @(
            "C:\Program Files\MetaTrader 5",
            "C:\Program Files (x86)\MetaTrader 5",
            "$env:APPDATA\MetaQuotes\Terminal\*\",
            "D:\Program Files\MetaTrader 5",
            "D:\MetaTrader 5"
        )
        
        foreach ($path in $possiblePaths) {
            if ($path -match '\*') {
                # Handle wildcard paths
                $terminals = Get-ChildItem -Path $path -Directory -ErrorAction SilentlyContinue
                foreach ($terminal in $terminals) {
                    if (Test-Path (Join-Path $terminal.FullName "terminal64.exe")) {
                        Write-Host "✅ Found MT5 at: $($terminal.FullName)" -ForegroundColor Green
                        return $terminal.FullName
                    }
                }
            }
            elseif (Test-Path (Join-Path $path "terminal64.exe")) {
                Write-Host "✅ Found MT5 at: $path" -ForegroundColor Green
                return $path
            }
        }
        
        Write-Warning "MT5 installation not found automatically"
        return $null
    }
    
    # Deploy EA to MT5
    [bool] DeployEA() {
        Write-Host "`n🤖 Deploying BITTENBridge EA..." -ForegroundColor Cyan
        
        if (-not $this.ExpertsPath) {
            Write-Error "MT5 path not found. Please install MT5 first."
            return $false
        }
        
        # Create Experts directory if it doesn't exist
        if (-not (Test-Path $this.ExpertsPath)) {
            New-Item -ItemType Directory -Path $this.ExpertsPath -Force | Out-Null
        }
        
        # EA source code
        $eaCode = @'
//+------------------------------------------------------------------+
//|                                 BITTENBridge_TradeExecutor_v2.mq5 |
//|       Enhanced EA with HTTP Market Data Streaming (No XAUUSD)    |
//+------------------------------------------------------------------+
#property strict

#include <Trade/Trade.mqh>
CTrade trade;

// Input parameters
input string SignalFile = "fire.txt";
input string ResultFile = "trade_result.txt";
input string UUIDFile = "uuid.txt";
input string MarketDataURL = "http://localhost:8001/market-data"; // Local endpoint
input int StreamInterval = 5; // Stream market data every 5 seconds
input int CheckInterval = 1;  // Check for signals every 1 second

// Global variables
string uuid = "unknown";
ulong last_ticket = 0;
string last_signal_id = "";
datetime last_stream_time = 0;
datetime last_check_time = 0;

// 15 currency pairs (XAUUSD removed)
string symbols[] = {
    "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD",
    "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY",
    "GBPNZD", "GBPAUD", "EURAUD", "GBPCHF", "AUDJPY"
};

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("🟢 BITTENBridge v2 initialized (No XAUUSD, HTTP Streaming)");
    
    // Load UUID
    LoadUUID();
    
    // Set timer for frequent checks
    EventSetTimer(1);
    
    // Initialize files
    InitializeFiles();
    
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Load UUID from file                                              |
//+------------------------------------------------------------------+
void LoadUUID()
{
    int h = FileOpen(UUIDFile, FILE_READ | FILE_TXT);
    if(h != INVALID_HANDLE)
    {
        uuid = FileReadString(h);
        FileClose(h);
        Print("📌 UUID loaded: ", uuid);
    }
    else
    {
        Print("⚠️ UUID file not found, using default");
        uuid = "mt5_" + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN));
    }
}

//+------------------------------------------------------------------+
//| Initialize required files                                        |
//+------------------------------------------------------------------+
void InitializeFiles()
{
    // Ensure BITTEN directory exists
    string bittenDir = "BITTEN\\";
    
    // Create empty fire.txt if it doesn't exist
    int h = FileOpen(bittenDir + SignalFile, FILE_WRITE | FILE_TXT);
    if(h != INVALID_HANDLE)
    {
        FileClose(h);
    }
    
    // Create empty result file
    h = FileOpen(bittenDir + ResultFile, FILE_WRITE | FILE_TXT);
    if(h != INVALID_HANDLE)
    {
        FileClose(h);
    }
}

//+------------------------------------------------------------------+
//| Timer function - handles both signal checking and data streaming |
//+------------------------------------------------------------------+
void OnTimer()
{
    datetime current_time = TimeCurrent();
    
    // Check for trade signals every second
    if(current_time - last_check_time >= CheckInterval)
    {
        CheckFireSignal();
        last_check_time = current_time;
    }
    
    // Stream market data every 5 seconds
    if(current_time - last_stream_time >= StreamInterval)
    {
        StreamMarketData();
        last_stream_time = current_time;
    }
}

//+------------------------------------------------------------------+
//| Check for trade signals                                         |
//+------------------------------------------------------------------+
void CheckFireSignal()
{
    string filepath = "BITTEN\\" + SignalFile;
    
    // Check if file exists and has content
    if(!FileIsExist(filepath))
        return;
        
    int handle = FileOpen(filepath, FILE_READ | FILE_TXT);
    if(handle == INVALID_HANDLE)
        return;
    
    // Read content
    string content = "";
    while(!FileIsEnding(handle))
    {
        content += FileReadString(handle);
    }
    FileClose(handle);
    
    // Skip if empty
    if(StringLen(content) == 0)
        return;
    
    // Parse JSON signal
    string signal_id = GetJSONValue(content, "signal_id");
    string action = GetJSONValue(content, "action");
    string symbol = GetJSONValue(content, "symbol");
    string type = GetJSONValue(content, "type");
    double lot = StringToDouble(GetJSONValue(content, "lot"));
    double sl = StringToDouble(GetJSONValue(content, "sl"));
    double tp = StringToDouble(GetJSONValue(content, "tp"));
    string comment = GetJSONValue(content, "comment");
    
    // Prevent duplicate processing
    if(signal_id != "" && signal_id == last_signal_id)
    {
        Print("⏱ Duplicate signal: ", signal_id, ". Skipping.");
        return;
    }
    
    // Validate symbol
    if(symbol == "")
    {
        Print("❌ No symbol specified");
        ClearSignalFile();
        return;
    }
    
    // Ensure symbol is selected
    if(!SymbolSelect(symbol, true))
    {
        Print("❌ Symbol not found: ", symbol);
        WriteResult(signal_id, "error", 0, "Symbol not found: " + symbol);
        ClearSignalFile();
        return;
    }
    
    // Handle close action
    if(action == "close")
    {
        ClosePositionsBySymbol(symbol);
        last_signal_id = signal_id;
        ClearSignalFile();
        return;
    }
    
    // Validate trade type
    if(type != "buy" && type != "sell")
    {
        Print("❌ Invalid trade type: ", type);
        WriteResult(signal_id, "error", 0, "Invalid trade type: " + type);
        ClearSignalFile();
        return;
    }
    
    // Execute trade
    ExecuteTrade(signal_id, symbol, type, lot, sl, tp, comment);
    
    // Update last signal ID
    last_signal_id = signal_id;
    
    // Clear the signal file
    ClearSignalFile();
}

//+------------------------------------------------------------------+
//| Execute trade                                                    |
//+------------------------------------------------------------------+
void ExecuteTrade(string signal_id, string symbol, string type, double lot, double sl, double tp, string comment)
{
    // Set trade parameters
    trade.SetExpertMagicNumber(777001);
    if(comment != "")
        trade.SetComment(comment);
    
    bool result = false;
    ulong ticket = 0;
    
    // Execute based on type
    if(type == "buy")
        result = trade.Buy(lot, symbol, 0, sl, tp);
    else if(type == "sell")
        result = trade.Sell(lot, symbol, 0, sl, tp);
    
    // Process result
    if(result)
    {
        ticket = trade.ResultOrder();
        last_ticket = ticket;
        Print("✅ Trade executed. Ticket: ", ticket);
        WriteResult(signal_id, "success", ticket, "Trade executed successfully");
    }
    else
    {
        string error = trade.ResultRetcodeDescription();
        int error_code = trade.ResultRetcode();
        Print("❌ Trade failed: ", error);
        WriteResult(signal_id, "error", 0, error);
    }
}

//+------------------------------------------------------------------+
//| Close all positions for a symbol                                |
//+------------------------------------------------------------------+
void ClosePositionsBySymbol(string sym)
{
    int total = PositionsTotal();
    int closed = 0;
    
    for(int i = total - 1; i >= 0; i--)
    {
        ulong ticket = PositionGetTicket(i);
        if(PositionSelectByTicket(ticket))
        {
            if(PositionGetString(POSITION_SYMBOL) == sym)
            {
                if(trade.PositionClose(ticket))
                {
                    Print("✅ Closed position: ", ticket);
                    closed++;
                }
                else
                {
                    Print("❌ Failed to close: ", ticket);
                }
            }
        }
    }
    
    if(closed > 0)
        WriteResult("", "closed", 0, IntegerToString(closed) + " positions closed for " + sym);
    else
        Print("ℹ️ No open positions for ", sym);
}

//+------------------------------------------------------------------+
//| Write trade result                                              |
//+------------------------------------------------------------------+
void WriteResult(string signal_id, string status, ulong ticket, string message)
{
    string filepath = "BITTEN\\" + ResultFile;
    int handle = FileOpen(filepath, FILE_WRITE | FILE_TXT);
    
    if(handle != INVALID_HANDLE)
    {
        // Build JSON result
        string json = "{";
        json += "\"signal_id\": \"" + signal_id + "\",";
        json += "\"status\": \"" + status + "\",";
        json += "\"ticket\": " + IntegerToString(ticket) + ",";
        json += "\"message\": \"" + message + "\",";
        json += "\"timestamp\": \"" + TimeToString(TimeCurrent()) + "\",";
        
        // Add account info
        json += "\"account\": {";
        json += "\"balance\": " + DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2) + ",";
        json += "\"equity\": " + DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2) + ",";
        json += "\"margin\": " + DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN), 2) + ",";
        json += "\"free_margin\": " + DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN_FREE), 2) + ",";
        json += "\"profit\": " + DoubleToString(AccountInfoDouble(ACCOUNT_PROFIT), 2);
        json += "}";
        
        json += "}";
        
        FileWriteString(handle, json);
        FileClose(handle);
        
        Print("📝 Result written: ", status);
    }
    else
    {
        Print("❌ Failed to write result file");
    }
}

//+------------------------------------------------------------------+
//| Clear signal file                                               |
//+------------------------------------------------------------------+
void ClearSignalFile()
{
    string filepath = "BITTEN\\" + SignalFile;
    int handle = FileOpen(filepath, FILE_WRITE | FILE_TXT);
    if(handle != INVALID_HANDLE)
    {
        FileClose(handle);
    }
}

//+------------------------------------------------------------------+
//| Stream market data via HTTP                                     |
//+------------------------------------------------------------------+
void StreamMarketData()
{
    // Build JSON with tick data for all 15 pairs
    string json = "{";
    json += "\"uuid\": \"" + uuid + "\",";
    json += "\"timestamp\": " + IntegerToString(TimeCurrent()) + ",";
    json += "\"ticks\": [";
    
    bool first = true;
    for(int i = 0; i < ArraySize(symbols); i++)
    {
        MqlTick tick;
        if(SymbolInfoTick(symbols[i], tick))
        {
            if(!first) json += ",";
            first = false;
            
            json += "{";
            json += "\"symbol\": \"" + symbols[i] + "\",";
            json += "\"bid\": " + DoubleToString(tick.bid, (int)SymbolInfoInteger(symbols[i], SYMBOL_DIGITS)) + ",";
            json += "\"ask\": " + DoubleToString(tick.ask, (int)SymbolInfoInteger(symbols[i], SYMBOL_DIGITS)) + ",";
            json += "\"spread\": " + DoubleToString((tick.ask - tick.bid) / SymbolInfoDouble(symbols[i], SYMBOL_POINT), 1) + ",";
            json += "\"volume\": " + IntegerToString(tick.volume) + ",";
            json += "\"time\": " + IntegerToString(tick.time);
            json += "}";
        }
    }
    
    json += "]}";
    
    // Send HTTP POST request
    SendHTTPPost(MarketDataURL, json);
}

//+------------------------------------------------------------------+
//| Send HTTP POST request                                          |
//+------------------------------------------------------------------+
void SendHTTPPost(string url, string json_data)
{
    char post[];
    char result[];
    string headers;
    
    // Convert string to char array
    StringToCharArray(json_data, post, 0, StringLen(json_data));
    
    // Set headers
    headers = "Content-Type: application/json\r\n";
    
    // Send request
    int res = WebRequest("POST", url, headers, 5000, post, result, headers);
    
    if(res == 200)
    {
        Print("📡 Market data streamed successfully");
    }
    else if(res == -1)
    {
        Print("❌ WebRequest failed. Error: ", GetLastError());
        Print("💡 Make sure to add ", url, " to allowed URLs in MT5 settings");
    }
    else
    {
        Print("⚠️ HTTP error: ", res);
    }
}

//+------------------------------------------------------------------+
//| Parse JSON value                                                |
//+------------------------------------------------------------------+
string GetJSONValue(string json, string key)
{
    // Simple JSON parser for string values
    int key_pos = StringFind(json, "\"" + key + "\"");
    if(key_pos < 0) return "";
    
    int colon_pos = StringFind(json, ":", key_pos);
    if(colon_pos < 0) return "";
    
    // Check if value is a string (starts with quote)
    int value_start = colon_pos + 1;
    while(value_start < StringLen(json) && 
          (StringGetCharacter(json, value_start) == ' ' || 
           StringGetCharacter(json, value_start) == '\t' || 
           StringGetCharacter(json, value_start) == '\n'))
    {
        value_start++;
    }
    
    if(value_start >= StringLen(json)) return "";
    
    // String value
    if(StringGetCharacter(json, value_start) == '"')
    {
        int quote_start = value_start + 1;
        int quote_end = StringFind(json, "\"", quote_start);
        if(quote_end < 0) return "";
        return StringSubstr(json, quote_start, quote_end - quote_start);
    }
    // Numeric value
    else
    {
        int value_end = value_start;
        while(value_end < StringLen(json))
        {
            ushort ch = StringGetCharacter(json, value_end);
            if(ch == ',' || ch == '}' || ch == ' ' || ch == '\n' || ch == '\r')
                break;
            value_end++;
        }
        return StringSubstr(json, value_start, value_end - value_start);
    }
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    EventKillTimer();
    Print("🛑 BITTENBridge v2 stopped. Reason: ", reason);
}

//+------------------------------------------------------------------+
//| Write tick data to files (backup method)                        |
//+------------------------------------------------------------------+
void WriteTickDataFiles()
{
    // Also write to individual files as backup
    for(int i = 0; i < ArraySize(symbols); i++)
    {
        MqlTick tick;
        if(SymbolInfoTick(symbols[i], tick))
        {
            string filename = "tick_data_" + symbols[i] + ".json";
            int fileHandle = FileOpen(filename, FILE_WRITE | FILE_TXT | FILE_ANSI);
            
            if(fileHandle != INVALID_HANDLE)
            {
                string data = "{";
                data += "\"symbol\": \"" + symbols[i] + "\",";
                data += "\"bid\": " + DoubleToString(tick.bid, (int)SymbolInfoInteger(symbols[i], SYMBOL_DIGITS)) + ",";
                data += "\"ask\": " + DoubleToString(tick.ask, (int)SymbolInfoInteger(symbols[i], SYMBOL_DIGITS)) + ",";
                data += "\"spread\": " + DoubleToString((tick.ask - tick.bid) / SymbolInfoDouble(symbols[i], SYMBOL_POINT), 1) + ",";
                data += "\"volume\": " + IntegerToString(tick.volume) + ",";
                data += "\"time\": " + IntegerToString(tick.time) + "}";
                
                FileWriteString(fileHandle, data);
                FileClose(fileHandle);
            }
        }
    }
}
'@
        
        # Write EA to file
        $eaPath = Join-Path $this.ExpertsPath "BITTENBridge_TradeExecutor.mq5"
        
        # Backup existing EA if present
        if (Test-Path $eaPath) {
            $backupPath = $eaPath -replace '\.mq5$', "_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').mq5"
            Copy-Item $eaPath $backupPath -Force
            Write-Host "   📋 Backed up existing EA to: $([System.IO.Path]::GetFileName($backupPath))" -ForegroundColor Gray
        }
        
        # Write new EA
        $eaCode | Set-Content $eaPath -Encoding UTF8
        Write-Host "   ✅ EA deployed to: $eaPath" -ForegroundColor Green
        
        # Create BITTEN directory structure
        $this.SetupBittenDirectory()
        
        Write-Host "`n   ⚠️ IMPORTANT: You must compile the EA in MetaEditor:" -ForegroundColor Yellow
        Write-Host "      1. Open MT5 Terminal" -ForegroundColor Gray
        Write-Host "      2. Press F4 or Tools → MetaQuotes Language Editor" -ForegroundColor Gray
        Write-Host "      3. Navigate to Experts folder" -ForegroundColor Gray
        Write-Host "      4. Open BITTENBridge_TradeExecutor.mq5" -ForegroundColor Gray
        Write-Host "      5. Press F7 or click Compile button" -ForegroundColor Gray
        Write-Host "      6. Drag EA to a chart to activate" -ForegroundColor Gray
        
        return $true
    }
    
    # Setup BITTEN directory structure
    [void] SetupBittenDirectory() {
        if (-not $this.BittenPath) {
            Write-Warning "MT5 Files path not found"
            return
        }
        
        # Create BITTEN directory
        if (-not (Test-Path $this.BittenPath)) {
            New-Item -ItemType Directory -Path $this.BittenPath -Force | Out-Null
            Write-Host "   📁 Created BITTEN directory" -ForegroundColor Gray
        }
        
        # Create subdirectories
        @("processed", "failed", "archive", "logs") | ForEach-Object {
            $subPath = Join-Path $this.BittenPath $_
            if (-not (Test-Path $subPath)) {
                New-Item -ItemType Directory -Path $subPath -Force | Out-Null
            }
        }
        
        # Create empty fire.txt and trade_result.txt
        @("fire.txt", "trade_result.txt") | ForEach-Object {
            $filePath = Join-Path $this.BittenPath $_
            if (-not (Test-Path $filePath)) {
                "" | Set-Content $filePath -Force
            }
        }
        
        # Create UUID file with machine identifier
        $uuidPath = Join-Path $this.FilesPath "uuid.txt"
        if (-not (Test-Path $uuidPath)) {
            $uuid = "VPS_" + (Get-Random -Maximum 999999)
            $uuid | Set-Content $uuidPath -Force
            Write-Host "   🆔 Created UUID: $uuid" -ForegroundColor Gray
        }
        
        Write-Host "   ✅ BITTEN directory structure ready" -ForegroundColor Green
    }
    
    # Create fire signal
    [bool] CreateFireSignal([hashtable]$signal) {
        if (-not $this.BittenPath) {
            Write-Error "BITTEN path not configured"
            return $false
        }
        
        # Validate signal
        if (-not $signal.symbol -or -not $signal.type) {
            Write-Error "Invalid signal: missing symbol or type"
            return $false
        }
        
        # Check if symbol is in our 15 pairs
        if ($signal.symbol -notin $this.CurrencyPairs.Values) {
            Write-Error "Invalid symbol: $($signal.symbol). Must be one of the 15 currency pairs."
            return $false
        }
        
        # Block XAUUSD explicitly
        if ($signal.symbol -eq "XAUUSD" -or $signal.symbol -match "GOLD|XAU") {
            Write-Error "BLOCKED: XAUUSD/GOLD trading is not allowed"
            return $false
        }
        
        # Generate signal ID
        if (-not $signal.signal_id) {
            $signal.signal_id = "S" + [math]::Round((Get-Date).ToFileTimeUtc() / 10000)
        }
        
        # Build fire.txt content
        $fireContent = @{
            signal_id = $signal.signal_id
            action = $signal.action ?? "trade"
            symbol = $signal.symbol
            type = $signal.type.ToLower()
            lot = $signal.lot ?? 0.01
            sl = $signal.sl ?? 0
            tp = $signal.tp ?? 0
            comment = $signal.comment ?? "BiTTen Signal"
        } | ConvertTo-Json -Compress
        
        # Write to fire.txt
        $firePath = Join-Path $this.BittenPath "fire.txt"
        
        try {
            $fireContent | Set-Content $firePath -Force
            Write-Host "🔥 Fire signal created: $($signal.signal_id)" -ForegroundColor Green
            Write-Host "   Symbol: $($signal.symbol) | Type: $($signal.type) | Lot: $($signal.lot)" -ForegroundColor Gray
            return $true
        }
        catch {
            Write-Error "Failed to create fire signal: $_"
            return $false
        }
    }
    
    # Monitor trade result
    [hashtable] MonitorTradeResult([string]$signalId, [int]$timeoutSeconds = 30) {
        $resultPath = Join-Path $this.BittenPath "trade_result.txt"
        $startTime = Get-Date
        
        Write-Host "⏳ Waiting for trade result..." -ForegroundColor Yellow
        
        while ((Get-Date) - $startTime -lt [TimeSpan]::FromSeconds($timeoutSeconds)) {
            if (Test-Path $resultPath) {
                $content = Get-Content $resultPath -Raw
                if ($content) {
                    try {
                        $result = $content | ConvertFrom-Json
                        if ($result.signal_id -eq $signalId) {
                            Write-Host "✅ Trade result received: $($result.status)" -ForegroundColor Green
                            
                            # Clear result file
                            "" | Set-Content $resultPath -Force
                            
                            return $result
                        }
                    }
                    catch {
                        # Invalid JSON, wait for valid result
                    }
                }
            }
            
            Start-Sleep -Milliseconds 500
        }
        
        Write-Warning "Trade result timeout after $timeoutSeconds seconds"
        return @{
            signal_id = $signalId
            status = "timeout"
            message = "No response from EA within timeout period"
        }
    }
    
    # Test EA communication
    [bool] TestEACommunication() {
        Write-Host "`n🧪 Testing EA communication..." -ForegroundColor Cyan
        
        # Create test signal
        $testSignal = @{
            symbol = "EURUSD"
            type = "buy"
            lot = 0.01
            sl = 0
            tp = 0
            comment = "BiTTen Communication Test"
        }
        
        if ($this.CreateFireSignal($testSignal)) {
            # Wait a moment for EA to process
            Start-Sleep -Seconds 2
            
            # Check if fire.txt was cleared (EA read it)
            $firePath = Join-Path $this.BittenPath "fire.txt"
            $content = Get-Content $firePath -Raw
            
            if (-not $content -or $content.Trim().Length -eq 0) {
                Write-Host "✅ EA communication test passed" -ForegroundColor Green
                return $true
            }
            else {
                Write-Warning "EA did not process test signal (fire.txt not cleared)"
                return $false
            }
        }
        
        return $false
    }
    
    # Get currency pairs list
    [array] GetCurrencyPairs() {
        return $this.CurrencyPairs.Values | Sort-Object
    }
    
    # Validate all pairs available
    [hashtable] ValidatePairsAvailable() {
        $validation = @{}
        
        foreach ($pair in $this.CurrencyPairs.Values) {
            # This would need actual MT5 API to check, for now assume all valid
            $validation[$pair] = $true
        }
        
        # Explicitly mark XAUUSD as invalid
        $validation["XAUUSD"] = $false
        
        return $validation
    }
}

# Export the class
Export-ModuleMember -Function * -Cmdlet * -Variable * -Alias *