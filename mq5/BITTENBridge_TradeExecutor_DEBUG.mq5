//+------------------------------------------------------------------+
//|                           BITTENBridge_TradeExecutor_DEBUG.mq5    |
//|                 Debug Version to Diagnose fire.txt Issues         |
//+------------------------------------------------------------------+
#property strict
#property copyright "BITTEN Trading System"
#property version   "2.0"
#property description "Debug EA to diagnose fire.txt reading issues"

#include <Trade/Trade.mqh>
CTrade trade;

// Input parameters
input string SignalFile = "fire.txt";                // Signal file to monitor
input string ResultFile = "trade_result.txt";        // Result file for feedback
input string UUIDFile = "uuid.txt";                  // UUID file for identification
input string MarketDataURL = "http://localhost:8001/market-data"; // Market data endpoint
input int StreamInterval = 5;                        // Stream market data every 5 seconds
input int CheckInterval = 1;                         // Check for signals every 1 second
input bool EnableTickFiles = true;                  // Write individual tick files for VENOM
input bool DebugMode = true;                        // Enable detailed debug logging

// Global variables
string uuid = "unknown";
ulong last_ticket = 0;
string last_signal_id = "";
datetime last_stream_time = 0;
datetime last_check_time = 0;
datetime last_tick_write = 0;
int check_counter = 0;

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
    Print("🔍 BITTENBridge DEBUG EA v2.0 Starting");
    Print("📋 Debug Mode: ENABLED - Verbose logging active");
    Print("======================================================");
    
    // Show file paths
    Print("📂 Terminal Data Path: ", TerminalInfoString(TERMINAL_DATA_PATH));
    Print("📂 MQL5 Path: ", TerminalInfoString(TERMINAL_DATA_PATH), "\\MQL5");
    Print("📂 Files Path: ", TerminalInfoString(TERMINAL_DATA_PATH), "\\MQL5\\Files");
    Print("📂 BITTEN Path: ", TerminalInfoString(TERMINAL_DATA_PATH), "\\MQL5\\Files\\BITTEN");
    
    // Load UUID
    LoadUUID();
    
    // Set timer for frequent checks
    EventSetTimer(1);
    
    // Initialize files and check directories
    InitializeFiles();
    
    // Test file operations
    TestFileOperations();
    
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Test file operations to diagnose issues                         |
//+------------------------------------------------------------------+
void TestFileOperations()
{
    Print("\n🧪 TESTING FILE OPERATIONS:");
    
    // Test 1: Check if BITTEN directory exists
    string bittenDir = "BITTEN\\";
    string testFile = bittenDir + "test_write.txt";
    
    Print("📝 Test 1: Writing to BITTEN directory");
    int h = FileOpen(testFile, FILE_WRITE | FILE_TXT);
    if(h != INVALID_HANDLE)
    {
        FileWriteString(h, "Test write successful");
        FileClose(h);
        Print("   ✅ Can write to BITTEN directory");
        
        // Try to read it back
        h = FileOpen(testFile, FILE_READ | FILE_TXT);
        if(h != INVALID_HANDLE)
        {
            string content = FileReadString(h);
            FileClose(h);
            Print("   ✅ Can read from BITTEN directory: ", content);
            FileDelete(testFile);
        }
    }
    else
    {
        Print("   ❌ Cannot write to BITTEN directory");
    }
    
    // Test 2: List all files in MQL5\Files
    Print("\n📝 Test 2: Listing all files in MQL5\\Files:");
    string search_pattern = "*.*";
    string filename;
    long search_handle = FileFindFirst(search_pattern, filename);
    
    if(search_handle != INVALID_HANDLE)
    {
        int count = 0;
        do
        {
            Print("   📄 Found: ", filename);
            count++;
            if(count > 20) 
            {
                Print("   ... (more files exist)");
                break;
            }
        }
        while(FileFindNext(search_handle, filename));
        FileFindClose(search_handle);
    }
    else
    {
        Print("   ❌ No files found or cannot list");
    }
    
    // Test 3: Check for fire.txt in various locations
    Print("\n📝 Test 3: Searching for fire.txt:");
    string locations[] = {
        "fire.txt",
        "BITTEN\\fire.txt",
        "bitten\\fire.txt",
        "Fire.txt",
        "FIRE.TXT"
    };
    
    for(int i = 0; i < ArraySize(locations); i++)
    {
        if(FileIsExist(locations[i]))
        {
            Print("   ✅ Found at: ", locations[i]);
            
            // Try to read it
            h = FileOpen(locations[i], FILE_READ | FILE_TXT);
            if(h != INVALID_HANDLE)
            {
                string content = "";
                while(!FileIsEnding(h))
                {
                    content += FileReadString(h);
                }
                FileClose(h);
                Print("   📄 Content: ", content);
            }
        }
        else
        {
            Print("   ❌ Not found at: ", locations[i]);
        }
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
    
    // Create empty fire.txt in BITTEN directory
    string filepath = bittenDir + SignalFile;
    int h = FileOpen(filepath, FILE_WRITE | FILE_TXT);
    if(h != INVALID_HANDLE)
    {
        FileClose(h);
        Print("✅ Created: ", filepath);
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
        Print("✅ Created: ", SignalFile, " (root)");
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
    
    // Stream market data every 5 seconds (if market is open)
    if(current_time - last_stream_time >= StreamInterval)
    {
        if(IsMarketOpen())
        {
            StreamMarketData();
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
        if(current - tick.time < 60)
        {
            return true;
        }
    }
    return false;
}

//+------------------------------------------------------------------+
//| Check for trade signals in fire.txt (with debug)               |
//+------------------------------------------------------------------+
void CheckFireSignal()
{
    check_counter++;
    
    // Debug logging every 10 checks
    if(DebugMode && check_counter % 10 == 0)
    {
        Print("🔍 Check #", check_counter, " at ", TimeToString(TimeCurrent()));
    }
    
    // Try multiple locations
    string locations[] = {
        "BITTEN\\" + SignalFile,
        SignalFile,
        "bitten\\" + SignalFile
    };
    
    bool found_file = false;
    string found_location = "";
    
    for(int i = 0; i < ArraySize(locations); i++)
    {
        if(FileIsExist(locations[i]))
        {
            found_file = true;
            found_location = locations[i];
            
            // Check file size
            int h = FileOpen(locations[i], FILE_READ | FILE_TXT);
            if(h != INVALID_HANDLE)
            {
                // Get file size
                ulong size = FileSize(h);
                
                if(size > 0)
                {
                    // Read content
                    string content = "";
                    while(!FileIsEnding(h))
                    {
                        content += FileReadString(h);
                    }
                    FileClose(h);
                    
                    Print("📨 SIGNAL FOUND at ", locations[i], "!");
                    Print("📄 Size: ", size, " bytes");
                    Print("📄 Content: ", content);
                    
                    // Process the signal
                    ProcessSignal(content, locations[i]);
                    return;
                }
                else
                {
                    FileClose(h);
                    if(DebugMode && check_counter % 10 == 0)
                    {
                        Print("   📄 ", locations[i], " exists but is empty");
                    }
                }
            }
        }
    }
    
    if(!found_file && DebugMode && check_counter % 30 == 0)
    {
        Print("   ❌ fire.txt not found in any location");
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
    
    // Debug parsed values
    Print("📊 Parsed values:");
    Print("   signal_id: ", signal_id);
    Print("   action: ", action);
    Print("   symbol: ", symbol);
    Print("   type: ", type);
    Print("   lot: ", lot);
    Print("   sl: ", sl);
    Print("   tp: ", tp);
    Print("   comment: ", comment);
    
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
    
    // Validate symbol
    if(symbol == "")
    {
        Print("❌ No symbol specified");
        WriteResult(signal_id, "error", 0, "No symbol specified");
        ClearSignalFile(filepath);
        return;
    }
    
    // Continue with trade execution...
    Print("✅ Signal validated, executing trade...");
    
    // Update last signal ID
    last_signal_id = signal_id;
    
    // Clear the signal file
    ClearSignalFile(filepath);
    
    // Write success result
    WriteResult(signal_id, "success", 12345, "Trade would be executed here");
}

//+------------------------------------------------------------------+
//| Clear signal file after processing                               |
//+------------------------------------------------------------------+
void ClearSignalFile(string filepath)
{
    int handle = FileOpen(filepath, FILE_WRITE | FILE_TXT);
    if(handle != INVALID_HANDLE)
    {
        FileClose(handle);
        Print("🧹 Cleared signal file: ", filepath);
    }
    else
    {
        Print("❌ Failed to clear: ", filepath);
    }
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
        json += "\"timestamp\": \"" + TimeToString(TimeCurrent()) + "\"";
        json += "}";
        
        FileWriteString(handle, json);
        FileClose(handle);
        
        Print("📝 Result written to: ", filepath);
        Print("📄 Content: ", json);
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
    if(DebugMode)
    {
        Print("📡 Streaming market data to: ", MarketDataURL);
    }
    
    // Build JSON with tick data
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
        SendHTTPPost(MarketDataURL, json);
    }
    else
    {
        if(DebugMode)
        {
            Print("⚠️ No valid tick data to stream (market closed?)");
        }
    }
}

//+------------------------------------------------------------------+
//| Send HTTP POST request with timeout                             |
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
    headers += "User-Agent: BITTENBridge/2.0\r\n";
    
    // Send request with 5 second timeout
    ResetLastError();
    int res = WebRequest("POST", url, headers, 5000, post, result, headers);
    
    if(res == 200)
    {
        if(DebugMode)
        {
            Print("✅ Market data sent successfully");
        }
    }
    else if(res == -1)
    {
        int error = GetLastError();
        Print("❌ WebRequest failed. Error: ", error);
        
        if(error == 4014)
            Print("💡 Add ", url, " to allowed URLs in MT5 settings");
        else if(error == 4060)
            Print("💡 Check your internet connection");
    }
    else
    {
        Print("⚠️ HTTP error: ", res);
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
    Print("🛑 BITTENBridge DEBUG EA stopped. Reason: ", reason);
    Print("📊 Total checks performed: ", check_counter);
    Print("📋 Last signal: ", last_signal_id);
    Print("======================================================");
}

//+------------------------------------------------------------------+
//| Expert tick function (not used, timer handles everything)        |
//+------------------------------------------------------------------+
void OnTick()
{
    // All work done in OnTimer for consistent timing
}