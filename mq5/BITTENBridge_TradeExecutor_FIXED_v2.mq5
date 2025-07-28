//+------------------------------------------------------------------+
//|                         BITTENBridge_TradeExecutor_FIXED_v2.mq5   |
//|                 Fixed Version - Better HTTP Error Handling        |
//+------------------------------------------------------------------+
#property strict
#property copyright "BITTEN Trading System"
#property version   "3.1"
#property description "Fixed EA with improved HTTP error handling"

#include <Trade/Trade.mqh>
CTrade trade;

// Input parameters
input string SignalFile = "fire.txt";                // Signal file to monitor
input string ResultFile = "trade_result.txt";        // Result file for feedback
input string UUIDFile = "uuid.txt";                  // UUID file for identification
input string MarketDataURL = "http://127.0.0.1:8001/market-data"; // Market data endpoint
input int StreamInterval = 5;                        // Stream market data every 5 seconds
input int CheckInterval = 1;                         // Check for signals every 1 second
input bool EnableTickFiles = true;                  // Write individual tick files for VENOM
input bool DebugMode = false;                        // Enable detailed debug logging
input bool EnableHTTPStream = true;                 // Enable HTTP streaming (can disable if errors)

// Global variables
string uuid = "unknown";
ulong last_ticket = 0;
string last_signal_id = "";
datetime last_stream_time = 0;
datetime last_check_time = 0;
datetime last_tick_write = 0;
int check_counter = 0;
bool market_open_logged = false;
int http_error_count = 0;
datetime last_http_error = 0;

// 15 currency pairs (XAUUSD REMOVED - CRITICAL)
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
    Print("======================================================");
    Print("🔧 BITTENBridge FIXED v3.1 Starting");
    Print("✅ Features: HTTP error handling, size check, market streaming");
    Print("======================================================");
    
    // Load UUID
    LoadUUID();
    
    // Set timer for frequent checks
    EventSetTimer(1);
    
    // Initialize files and check directories
    InitializeFiles();
    
    // Test HTTP connection
    if(EnableHTTPStream)
    {
        Print("🌐 Testing HTTP connection to: ", MarketDataURL);
        TestHTTPConnection();
    }
    
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Test HTTP connection                                             |
//+------------------------------------------------------------------+
void TestHTTPConnection()
{
    // Try a simple GET request first
    char post[];
    char result[];
    string headers = "User-Agent: BITTENBridge/3.1\r\n";
    
    string test_url = "http://127.0.0.1:8001/market-data/health";
    
    ResetLastError();
    int res = WebRequest("GET", test_url, headers, 5000, post, result, headers);
    
    if(res == 200)
    {
        Print("✅ HTTP connection test successful");
        string response = CharArrayToString(result);
        Print("📡 Response: ", response);
    }
    else if(res == -1)
    {
        int error = GetLastError();
        Print("❌ HTTP test failed. Error code: ", error);
        
        if(error == 4014)
        {
            Print("🚨 CRITICAL: WebRequest not allowed!");
            Print("💡 Solution:");
            Print("   1. Go to Tools → Options → Expert Advisors");
            Print("   2. Check 'Allow WebRequest for listed URL'");
            Print("   3. Add these URLs:");
            Print("      - http://127.0.0.1:8001");
            Print("      - http://localhost:8001");
            Print("   4. Click OK and restart EA");
            EnableHTTPStream = false;
        }
        else if(error == 5200)
        {
            Print("❌ Connection failed - Is market data receiver running?");
            Print("💡 Check if service is running on port 8001");
        }
        else
        {
            Print("❌ Unknown error: ", error);
        }
    }
    else
    {
        Print("⚠️ HTTP error: ", res);
    }
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
        Print("⚠️ UUID file not found, generating default");
        uuid = "mt5_" + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN));
        
        // Save generated UUID
        h = FileOpen(UUIDFile, FILE_WRITE | FILE_TXT);
        if(h != INVALID_HANDLE)
        {
            FileWriteString(h, uuid);
            FileClose(h);
        }
    }
}

//+------------------------------------------------------------------+
//| Initialize required files and directories                        |
//+------------------------------------------------------------------+
void InitializeFiles()
{
    // Try to create BITTEN directory by creating a file in it
    string bittenDir = "BITTEN\\";
    
    // Create empty fire.txt in BITTEN directory (properly empty)
    string filepath = bittenDir + SignalFile;
    int h = FileOpen(filepath, FILE_WRITE | FILE_TXT);
    if(h != INVALID_HANDLE)
    {
        // Don't write anything - keep it truly empty
        FileClose(h);
        Print("✅ Created empty: ", filepath);
    }
    else
    {
        Print("❌ Failed to create: ", filepath);
    }
    
    // Also create in root for testing
    h = FileOpen(SignalFile, FILE_WRITE | FILE_TXT);
    if(h != INVALID_HANDLE)
    {
        FileClose(h);
        Print("✅ Created empty: ", SignalFile, " (root)");
    }
    
    // Create result file
    h = FileOpen(bittenDir + ResultFile, FILE_WRITE | FILE_TXT);
    if(h != INVALID_HANDLE)
    {
        FileClose(h);
        Print("✅ Created: ", bittenDir + ResultFile);
    }
}

//+------------------------------------------------------------------+
//| Timer function - handles all periodic tasks                      |
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
    
    // Stream market data every 5 seconds (if market is open and HTTP enabled)
    if(EnableHTTPStream && current_time - last_stream_time >= StreamInterval)
    {
        if(IsMarketOpen())
        {
            // Check if we should retry after errors
            if(http_error_count > 0 && (current_time - last_http_error) > 60)
            {
                Print("🔄 Retrying HTTP after error timeout");
                http_error_count = 0;  // Reset error count after 1 minute
            }
            
            if(http_error_count < 3)  // Stop after 3 consecutive errors
            {
                StreamMarketData();
            }
            
            if(!market_open_logged)
            {
                Print("🟢 Market is OPEN - Ready to stream");
                market_open_logged = true;
            }
        }
        else
        {
            if(market_open_logged)
            {
                Print("🔴 Market is CLOSED - Pausing streams");
                market_open_logged = false;
            }
        }
        last_stream_time = current_time;
    }
    
    // Write tick files for VENOM (if enabled and market open)
    if(EnableTickFiles && current_time - last_tick_write >= StreamInterval)
    {
        if(IsMarketOpen())
        {
            WriteTickDataFiles();
        }
        last_tick_write = current_time;
    }
}

//+------------------------------------------------------------------+
//| Check if market is open                                         |
//+------------------------------------------------------------------+
bool IsMarketOpen()
{
    MqlTick tick;
    if(SymbolInfoTick("EURUSD", tick))
    {
        // Check if tick time is recent (within last minute)
        datetime current = TimeCurrent();
        datetime tick_age = current - tick.time;
        
        // More lenient check - within 5 minutes
        if(tick_age < 300)
        {
            return true;
        }
        
        if(DebugMode && check_counter % 30 == 0)
        {
            Print("⏰ Market closed? Tick age: ", tick_age, " seconds");
        }
    }
    return false;
}

//+------------------------------------------------------------------+
//| Check for trade signals in fire.txt (with size check)          |
//+------------------------------------------------------------------+
void CheckFireSignal()
{
    check_counter++;
    
    // Try multiple locations
    string locations[] = {
        "BITTEN\\" + SignalFile,
        SignalFile
    };
    
    for(int i = 0; i < ArraySize(locations); i++)
    {
        if(FileIsExist(locations[i]))
        {
            // Open file to check size
            int h = FileOpen(locations[i], FILE_READ | FILE_TXT);
            if(h != INVALID_HANDLE)
            {
                // Get file size
                ulong size = FileSize(h);
                
                // CRITICAL FIX: Skip files that are too small
                if(size < 20)  // Minimum valid JSON is larger than 20 bytes
                {
                    FileClose(h);
                    
                    // Clear the junk file
                    if(size > 0 && size < 20)
                    {
                        if(DebugMode || check_counter % 30 == 0)
                        {
                            Print("⚠️ Clearing junk fire.txt (", size, " bytes) at ", locations[i]);
                        }
                        ClearSignalFile(locations[i]);
                    }
                    continue;
                }
                
                // Read content if file is large enough
                string content = "";
                while(!FileIsEnding(h))
                {
                    content += FileReadString(h);
                }
                FileClose(h);
                
                // Additional validation - must have basic JSON structure
                if(StringFind(content, "{") >= 0 && StringFind(content, "}") >= 0)
                {
                    Print("📨 Valid signal found at ", locations[i], "!");
                    Print("📄 Size: ", size, " bytes");
                    if(DebugMode)
                    {
                        Print("📄 Content: ", content);
                    }
                    
                    // Process the signal
                    ProcessSignal(content, locations[i]);
                    return;
                }
                else
                {
                    // Invalid content - clear it
                    Print("❌ Invalid signal format - clearing file");
                    ClearSignalFile(locations[i]);
                }
            }
        }
    }
    
    // Periodic status update
    if(DebugMode && check_counter % 60 == 0)
    {
        Print("👀 Waiting for signals... (Check #", check_counter, ")");
        if(EnableHTTPStream && http_error_count >= 3)
        {
            Print("⚠️ HTTP streaming disabled due to errors");
        }
    }
}

//+------------------------------------------------------------------+
//| Process the signal content                                      |
//+------------------------------------------------------------------+
void ProcessSignal(string content, string filepath)
{
    Print("🎯 Processing signal from: ", filepath);
    
    // Parse JSON signal
    string signal_id = GetJSONValue(content, "signal_id");
    string action = GetJSONValue(content, "action");
    string symbol = GetJSONValue(content, "symbol");
    string type = GetJSONValue(content, "type");
    double lot = StringToDouble(GetJSONValue(content, "lot"));
    double sl = StringToDouble(GetJSONValue(content, "sl"));
    double tp = StringToDouble(GetJSONValue(content, "tp"));
    string comment = GetJSONValue(content, "comment");
    
    // Validate minimum required fields
    if(symbol == "" || (type == "" && action == ""))
    {
        Print("❌ Missing required fields (symbol/type)");
        WriteResult(signal_id, "error", 0, "Missing required fields");
        ClearSignalFile(filepath);
        return;
    }
    
    // Default values if missing
    if(lot == 0) lot = 0.01;
    if(comment == "") comment = "BITTEN_" + signal_id;
    
    // Prevent duplicate processing
    if(signal_id != "" && signal_id == last_signal_id)
    {
        Print("⏱️ Duplicate signal: ", signal_id, ". Skipping.");
        ClearSignalFile(filepath);
        return;
    }
    
    // CRITICAL: Block XAUUSD
    if(symbol == "XAUUSD" || StringFind(symbol, "XAU") >= 0 || StringFind(symbol, "GOLD") >= 0)
    {
        Print("🚫 BLOCKED: XAUUSD trade attempt rejected");
        WriteResult(signal_id, "error", 0, "XAUUSD is not supported");
        ClearSignalFile(filepath);
        return;
    }
    
    // Validate symbol is in allowed list
    bool symbolAllowed = false;
    for(int i = 0; i < ArraySize(symbols); i++)
    {
        if(symbols[i] == symbol)
        {
            symbolAllowed = true;
            break;
        }
    }
    
    if(!symbolAllowed)
    {
        Print("❌ Symbol not allowed: ", symbol);
        WriteResult(signal_id, "error", 0, "Symbol not in allowed list: " + symbol);
        ClearSignalFile(filepath);
        return;
    }
    
    // Ensure symbol is selected in Market Watch
    if(!SymbolSelect(symbol, true))
    {
        Print("❌ Failed to select symbol: ", symbol);
        WriteResult(signal_id, "error", 0, "Failed to select symbol: " + symbol);
        ClearSignalFile(filepath);
        return;
    }
    
    // Handle close action
    if(action == "close")
    {
        Print("🔄 Processing close command for ", symbol);
        ClosePositionsBySymbol(symbol);
        last_signal_id = signal_id;
        ClearSignalFile(filepath);
        return;
    }
    
    // Validate trade type
    if(type != "buy" && type != "sell")
    {
        Print("❌ Invalid trade type: ", type);
        WriteResult(signal_id, "error", 0, "Invalid trade type: " + type);
        ClearSignalFile(filepath);
        return;
    }
    
    // Execute trade
    Print("✅ Signal validated, executing ", type, " trade on ", symbol);
    ExecuteTrade(signal_id, symbol, type, lot, sl, tp, comment);
    
    // Update last signal ID
    last_signal_id = signal_id;
    
    // Clear the signal file
    ClearSignalFile(filepath);
}

//+------------------------------------------------------------------+
//| Execute trade with full validation                               |
//+------------------------------------------------------------------+
void ExecuteTrade(string signal_id, string symbol, string type, double lot, double sl, double tp, string trade_comment)
{
    // Validate lot size
    double minLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
    double maxLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
    double lotStep = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
    
    // Normalize lot size
    lot = MathMax(minLot, lot);
    lot = MathMin(maxLot, lot);
    lot = NormalizeDouble(lot / lotStep, 0) * lotStep;
    
    // Set trade parameters
    trade.SetExpertMagicNumber(777001);
    trade.SetComment(trade_comment);
    trade.SetDeviationInPoints(10);
    
    bool result = false;
    ulong ticket = 0;
    
    // Get current price
    double price = 0;
    if(type == "buy")
        price = SymbolInfoDouble(symbol, SYMBOL_ASK);
    else
        price = SymbolInfoDouble(symbol, SYMBOL_BID);
    
    // Calculate SL/TP if provided in pips
    double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
    double sl_price = 0;
    double tp_price = 0;
    
    if(sl > 0)
    {
        if(type == "buy")
            sl_price = price - sl * point;
        else
            sl_price = price + sl * point;
    }
    
    if(tp > 0)
    {
        if(type == "buy")
            tp_price = price + tp * point;
        else
            tp_price = price - tp * point;
    }
    
    // Execute based on type
    if(type == "buy")
        result = trade.Buy(lot, symbol, price, sl_price, tp_price, trade_comment);
    else if(type == "sell")
        result = trade.Sell(lot, symbol, price, sl_price, tp_price, trade_comment);
    
    // Process result
    if(result)
    {
        ticket = trade.ResultOrder();
        last_ticket = ticket;
        Print("✅ Trade executed successfully");
        Print("   Ticket: ", ticket);
        Print("   Symbol: ", symbol);
        Print("   Type: ", type);
        Print("   Lot: ", lot);
        Print("   Price: ", price);
        if(sl_price > 0) Print("   SL: ", sl_price);
        if(tp_price > 0) Print("   TP: ", tp_price);
        
        WriteResult(signal_id, "success", ticket, "Trade executed successfully");
    }
    else
    {
        string error = trade.ResultRetcodeDescription();
        int error_code = trade.ResultRetcode();
        Print("❌ Trade failed: ", error, " (Code: ", error_code, ")");
        WriteResult(signal_id, "error", 0, error + " (Code: " + IntegerToString(error_code) + ")");
    }
}

//+------------------------------------------------------------------+
//| Close all positions for a symbol                                |
//+------------------------------------------------------------------+
void ClosePositionsBySymbol(string sym)
{
    int total = PositionsTotal();
    int closed = 0;
    
    Print("🔍 Checking ", total, " positions for ", sym);
    
    for(int i = total - 1; i >= 0; i--)
    {
        ulong ticket = PositionGetTicket(i);
        if(PositionSelectByTicket(ticket))
        {
            if(PositionGetString(POSITION_SYMBOL) == sym)
            {
                Print("📌 Found position to close: ", ticket);
                if(trade.PositionClose(ticket))
                {
                    Print("✅ Closed position: ", ticket);
                    closed++;
                }
                else
                {
                    Print("❌ Failed to close position: ", ticket);
                    Print("   Error: ", trade.ResultRetcodeDescription());
                }
            }
        }
    }
    
    if(closed > 0)
    {
        WriteResult("", "closed", 0, IntegerToString(closed) + " positions closed for " + sym);
        Print("✅ Total closed: ", closed, " positions");
    }
    else
    {
        Print("ℹ️ No open positions found for ", sym);
        WriteResult("", "info", 0, "No positions to close for " + sym);
    }
}

//+------------------------------------------------------------------+
//| Clear signal file after processing (properly)                   |
//+------------------------------------------------------------------+
void ClearSignalFile(string filepath)
{
    // Delete and recreate to ensure it's truly empty
    if(FileDelete(filepath))
    {
        // Recreate as empty
        int handle = FileOpen(filepath, FILE_WRITE | FILE_TXT);
        if(handle != INVALID_HANDLE)
        {
            FileClose(handle);
            if(DebugMode)
            {
                Print("🧹 Signal file cleared: ", filepath);
            }
        }
    }
    else
    {
        // If delete fails, just truncate
        int handle = FileOpen(filepath, FILE_WRITE | FILE_TXT);
        if(handle != INVALID_HANDLE)
        {
            FileClose(handle);
        }
    }
}

//+------------------------------------------------------------------+
//| Write trade result with full account info                       |
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
        json += "\"uuid\": \"" + uuid + "\",";
        
        // Add account info
        json += "\"account\": {";
        json += "\"balance\": " + DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2) + ",";
        json += "\"equity\": " + DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2) + ",";
        json += "\"margin\": " + DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN), 2) + ",";
        json += "\"free_margin\": " + DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN_FREE), 2) + ",";
        json += "\"profit\": " + DoubleToString(AccountInfoDouble(ACCOUNT_PROFIT), 2) + ",";
        json += "\"leverage\": " + IntegerToString(AccountInfoInteger(ACCOUNT_LEVERAGE)) + ",";
        json += "\"currency\": \"" + AccountInfoString(ACCOUNT_CURRENCY) + "\",";
        json += "\"server\": \"" + AccountInfoString(ACCOUNT_SERVER) + "\",";
        json += "\"company\": \"" + AccountInfoString(ACCOUNT_COMPANY) + "\"";
        json += "}";
        
        json += "}";
        
        FileWriteString(handle, json);
        FileClose(handle);
        
        if(DebugMode)
        {
            Print("📝 Result written: ", status, " (", filepath, ")");
        }
    }
    else
    {
        Print("❌ Failed to write result file: ", filepath);
    }
}

//+------------------------------------------------------------------+
//| Stream market data via HTTP POST                                |
//+------------------------------------------------------------------+
void StreamMarketData()
{
    // Build JSON with tick data for all 15 pairs
    string json = "{";
    json += "\"uuid\": \"" + uuid + "\",";
    json += "\"timestamp\": " + IntegerToString(TimeCurrent()) + ",";
    json += "\"account_balance\": " + DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2) + ",";
    json += "\"ticks\": [";
    
    bool first = true;
    int validTicks = 0;
    
    for(int i = 0; i < ArraySize(symbols); i++)
    {
        MqlTick tick;
        if(SymbolInfoTick(symbols[i], tick))
        {
            if(!first) json += ",";
            first = false;
            
            double spread = (tick.ask - tick.bid) / SymbolInfoDouble(symbols[i], SYMBOL_POINT);
            
            json += "{";
            json += "\"symbol\": \"" + symbols[i] + "\",";
            json += "\"bid\": " + DoubleToString(tick.bid, (int)SymbolInfoInteger(symbols[i], SYMBOL_DIGITS)) + ",";
            json += "\"ask\": " + DoubleToString(tick.ask, (int)SymbolInfoInteger(symbols[i], SYMBOL_DIGITS)) + ",";
            json += "\"spread\": " + DoubleToString(spread, 1) + ",";
            json += "\"volume\": " + IntegerToString(tick.volume) + ",";
            json += "\"time\": " + IntegerToString(tick.time);
            json += "}";
            
            validTicks++;
        }
    }
    
    json += "]}";
    
    // Send HTTP POST request
    if(validTicks > 0)
    {
        if(DebugMode || http_error_count == 0)
        {
            Print("📡 Streaming ", validTicks, " ticks to ", MarketDataURL);
        }
        SendHTTPPost(MarketDataURL, json);
    }
}

//+------------------------------------------------------------------+
//| Send HTTP POST request with better error handling               |
//+------------------------------------------------------------------+
void SendHTTPPost(string url, string json_data)
{
    char post[];
    char result[];
    string headers;
    
    // Convert string to char array
    StringToCharArray(json_data, post, 0, StringLen(json_data), CP_UTF8);
    ArrayResize(post, ArraySize(post) - 1);  // Remove null terminator
    
    // Set headers
    headers = "Content-Type: application/json\r\n";
    headers += "User-Agent: BITTENBridge/3.1\r\n";
    headers += "Accept: */*\r\n";
    
    // Send request with 5 second timeout
    ResetLastError();
    int res = WebRequest("POST", url, headers, 5000, post, result, headers);
    
    if(res == 200)
    {
        if(http_error_count > 0)
        {
            Print("✅ HTTP connection restored!");
            http_error_count = 0;
        }
        else if(DebugMode)
        {
            Print("✅ Market data sent successfully");
        }
    }
    else if(res == -1)
    {
        int error = GetLastError();
        http_error_count++;
        last_http_error = TimeCurrent();
        
        if(http_error_count == 1)  // Only log first error in detail
        {
            Print("❌ WebRequest failed. Error code: ", error);
            
            if(error == 4014)
            {
                Print("🚨 WebRequest not allowed for URL: ", url);
                Print("💡 Add to allowed URLs in MT5 settings");
            }
            else if(error == 5200 || error == 5201)
            {
                Print("❌ Connection failed to ", url);
                Print("💡 Check if market data receiver is running");
            }
            else if(error == 5203)
            {
                Print("❌ HTTP request failed");
                Print("💡 Check server is accepting connections");
            }
        }
        
        if(http_error_count >= 3)
        {
            Print("⚠️ Disabling HTTP after 3 errors. Will retry in 1 minute.");
        }
    }
    else
    {
        http_error_count++;
        last_http_error = TimeCurrent();
        
        if(http_error_count == 1)
        {
            Print("⚠️ HTTP error: ", res);
            if(res == 1001)
            {
                Print("❌ HTTP Error 1001 - General HTTP error");
                Print("💡 Possible causes:");
                Print("   - Server not running on ", url);
                Print("   - Firewall blocking connection");
                Print("   - Invalid response from server");
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Write tick data to individual files for VENOM                   |
//+------------------------------------------------------------------+
void WriteTickDataFiles()
{
    int written = 0;
    
    for(int i = 0; i < ArraySize(symbols); i++)
    {
        MqlTick tick;
        if(SymbolInfoTick(symbols[i], tick))
        {
            string filename = "tick_data_" + symbols[i] + ".json";
            int fileHandle = FileOpen(filename, FILE_WRITE | FILE_TXT | FILE_ANSI);
            
            if(fileHandle != INVALID_HANDLE)
            {
                double spread = (tick.ask - tick.bid) / SymbolInfoDouble(symbols[i], SYMBOL_POINT);
                
                string data = "{";
                data += "\"symbol\": \"" + symbols[i] + "\",";
                data += "\"bid\": " + DoubleToString(tick.bid, (int)SymbolInfoInteger(symbols[i], SYMBOL_DIGITS)) + ",";
                data += "\"ask\": " + DoubleToString(tick.ask, (int)SymbolInfoInteger(symbols[i], SYMBOL_DIGITS)) + ",";
                data += "\"spread\": " + DoubleToString(spread, 1) + ",";
                data += "\"volume\": " + IntegerToString(tick.volume) + ",";
                data += "\"time\": " + IntegerToString(tick.time) + ",";
                data += "\"time_msc\": " + IntegerToString(tick.time_msc) + ",";
                data += "\"is_real\": true";
                data += "}";
                
                FileWriteString(fileHandle, data);
                FileClose(fileHandle);
                written++;
            }
        }
    }
    
    if(written > 0 && DebugMode)
    {
        Print("💾 Tick files written: ", written, " pairs");
    }
}

//+------------------------------------------------------------------+
//| Parse JSON value (handles strings and numbers)                  |
//+------------------------------------------------------------------+
string GetJSONValue(string json, string key)
{
    // Look for key
    int key_pos = StringFind(json, "\"" + key + "\"");
    if(key_pos < 0) return "";
    
    // Find colon after key
    int colon_pos = StringFind(json, ":", key_pos);
    if(colon_pos < 0) return "";
    
    // Skip whitespace after colon
    int value_start = colon_pos + 1;
    while(value_start < StringLen(json) && 
          (StringGetCharacter(json, value_start) == ' ' || 
           StringGetCharacter(json, value_start) == '\t' || 
           StringGetCharacter(json, value_start) == '\n' || 
           StringGetCharacter(json, value_start) == '\r'))
    {
        value_start++;
    }
    
    if(value_start >= StringLen(json)) return "";
    
    // Check if value is a string (starts with quote)
    if(StringGetCharacter(json, value_start) == '"')
    {
        // String value - find closing quote
        int quote_start = value_start + 1;
        int quote_end = quote_start;
        
        // Handle escaped quotes
        while(quote_end < StringLen(json))
        {
            if(StringGetCharacter(json, quote_end) == '"' && 
               StringGetCharacter(json, quote_end - 1) != '\\')
                break;
            quote_end++;
        }
        
        if(quote_end >= StringLen(json)) return "";
        return StringSubstr(json, quote_start, quote_end - quote_start);
    }
    else
    {
        // Numeric/boolean value - find end
        int value_end = value_start;
        while(value_end < StringLen(json))
        {
            ushort ch = StringGetCharacter(json, value_end);
            if(ch == ',' || ch == '}' || ch == ']' || ch == ' ' || 
               ch == '\n' || ch == '\r' || ch == '\t')
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
    Print("======================================================");
    Print("🛑 BITTENBridge FIXED v3.1 stopped. Reason: ", reason);
    Print("📊 Total checks performed: ", check_counter);
    Print("📋 Last signal: ", last_signal_id);
    if(http_error_count > 0)
    {
        Print("⚠️ HTTP errors encountered: ", http_error_count);
    }
    Print("======================================================");
}

//+------------------------------------------------------------------+
//| Expert tick function (not used, timer handles everything)        |
//+------------------------------------------------------------------+
void OnTick()
{
    // All work done in OnTimer for consistent timing
}