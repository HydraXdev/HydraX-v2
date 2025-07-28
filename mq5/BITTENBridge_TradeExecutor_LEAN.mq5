//+------------------------------------------------------------------+
//|                         BITTENBridge_TradeExecutor_LEAN.mq5       |
//|                 Lean Version - Minimal, Fast, No Clutter          |
//+------------------------------------------------------------------+
#property strict
#property copyright "BITTEN Trading System"
#property version   "4.0"
#property description "Lean EA - Fast signal processing, optional HTTP streaming"

#include <Trade/Trade.mqh>
CTrade trade;

// Input parameters
input string SignalFile = "fire.txt";                // Signal file to monitor
input string ResultFile = "trade_result.txt";        // Result file for feedback
input string MarketDataURL = "http://127.0.0.1:8001/market-data"; // Market data endpoint
input bool EnableHTTPStream = false;                 // Enable HTTP streaming (OFF by default)
input int StreamInterval = 30;                       // Stream every 30 seconds (less frequent)
input int CheckInterval = 1;                         // Check for signals every 1 second

// Global variables
string uuid = "unknown";
ulong last_ticket = 0;
string last_signal_id = "";
datetime last_stream_time = 0;
datetime last_check_time = 0;
int check_counter = 0;
bool http_tested = false;

// 15 currency pairs (NO XAUUSD)
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
    Print("⚡ BITTENBridge LEAN v4.0 - Fast & Clean");
    Print("✅ Signal processing ready");
    if(EnableHTTPStream)
        Print("📡 HTTP streaming: ON (every ", StreamInterval, " seconds)");
    else
        Print("📡 HTTP streaming: OFF (faster performance)");
    Print("======================================================");
    
    // Generate simple UUID
    uuid = "mt5_" + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN));
    
    // Set timer
    EventSetTimer(1);
    
    // Initialize files
    InitializeFiles();
    
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Initialize required files                                        |
//+------------------------------------------------------------------+
void InitializeFiles()
{
    // Ensure BITTEN directory exists
    string bittenDir = "BITTEN\\";
    
    // Create empty fire.txt
    string filepath = bittenDir + SignalFile;
    if(FileDelete(filepath)) {} // Delete if exists
    
    int h = FileOpen(filepath, FILE_WRITE | FILE_TXT);
    if(h != INVALID_HANDLE)
    {
        FileClose(h);
        Print("✅ Ready: ", filepath);
    }
}

//+------------------------------------------------------------------+
//| Timer function                                                   |
//+------------------------------------------------------------------+
void OnTimer()
{
    datetime current_time = TimeCurrent();
    
    // Check for signals
    CheckFireSignal();
    
    // Optional HTTP streaming (less frequent)
    if(EnableHTTPStream && (current_time - last_stream_time >= StreamInterval))
    {
        if(IsMarketOpen())
        {
            StreamMarketData();
        }
        last_stream_time = current_time;
    }
}

//+------------------------------------------------------------------+
//| Simple market open check                                        |
//+------------------------------------------------------------------+
bool IsMarketOpen()
{
    MqlTick tick;
    if(SymbolInfoTick("EURUSD", tick))
    {
        // Within 5 minutes = market open
        return (TimeCurrent() - tick.time) < 300;
    }
    return false;
}

//+------------------------------------------------------------------+
//| Check for trade signals (FAST)                                 |
//+------------------------------------------------------------------+
void CheckFireSignal()
{
    check_counter++;
    
    string filepath = "BITTEN\\" + SignalFile;
    
    // Quick file existence check
    if(!FileIsExist(filepath))
        return;
        
    // Open and check size
    int h = FileOpen(filepath, FILE_READ | FILE_TXT);
    if(h == INVALID_HANDLE)
        return;
    
    ulong size = FileSize(h);
    
    // Skip small files
    if(size < 20)
    {
        FileClose(h);
        if(size > 0) // Clear junk
        {
            FileDelete(filepath);
            int h2 = FileOpen(filepath, FILE_WRITE | FILE_TXT);
            if(h2 != INVALID_HANDLE) FileClose(h2);
        }
        return;
    }
    
    // Read content
    string content = "";
    while(!FileIsEnding(h) && StringLen(content) < 10000) // Limit read size
    {
        content += FileReadString(h);
    }
    FileClose(h);
    
    // Quick JSON check
    if(StringFind(content, "{") >= 0 && StringFind(content, "}") >= 0)
    {
        Print("📨 Signal found! Size: ", size, " bytes");
        ProcessSignal(content, filepath);
    }
    else
    {
        // Clear invalid file
        ClearSignalFile(filepath);
    }
}

//+------------------------------------------------------------------+
//| Process signal (STREAMLINED)                                    |
//+------------------------------------------------------------------+
void ProcessSignal(string content, string filepath)
{
    // Parse required fields only
    string signal_id = GetJSONValue(content, "signal_id");
    string symbol = GetJSONValue(content, "symbol");
    string type = GetJSONValue(content, "type");
    double lot = StringToDouble(GetJSONValue(content, "lot"));
    double sl = StringToDouble(GetJSONValue(content, "sl"));
    double tp = StringToDouble(GetJSONValue(content, "tp"));
    
    // Quick validation
    if(symbol == "" || type == "")
    {
        Print("❌ Invalid signal");
        ClearSignalFile(filepath);
        return;
    }
    
    // Prevent duplicates
    if(signal_id != "" && signal_id == last_signal_id)
    {
        ClearSignalFile(filepath);
        return;
    }
    
    // Block XAUUSD
    if(StringFind(symbol, "XAU") >= 0 || StringFind(symbol, "GOLD") >= 0)
    {
        Print("🚫 XAUUSD blocked");
        WriteResult(signal_id, "error", 0, "XAUUSD not supported");
        ClearSignalFile(filepath);
        return;
    }
    
    // Quick symbol validation
    bool valid = false;
    for(int i = 0; i < ArraySize(symbols); i++)
    {
        if(symbols[i] == symbol)
        {
            valid = true;
            break;
        }
    }
    
    if(!valid)
    {
        Print("❌ Invalid symbol: ", symbol);
        ClearSignalFile(filepath);
        return;
    }
    
    // Ensure symbol in Market Watch
    SymbolSelect(symbol, true);
    
    // Execute trade
    Print("🎯 Executing ", type, " on ", symbol);
    ExecuteTrade(signal_id, symbol, type, lot > 0 ? lot : 0.01, sl, tp);
    
    last_signal_id = signal_id;
    ClearSignalFile(filepath);
}

//+------------------------------------------------------------------+
//| Execute trade (SIMPLIFIED)                                      |
//+------------------------------------------------------------------+
void ExecuteTrade(string signal_id, string symbol, string type, double lot, double sl, double tp)
{
    // Normalize lot
    double minLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
    double maxLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
    double lotStep = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
    
    lot = MathMax(minLot, lot);
    lot = MathMin(maxLot, lot);
    lot = NormalizeDouble(lot / lotStep, 0) * lotStep;
    
    // Setup trade
    trade.SetExpertMagicNumber(777001);
    trade.SetDeviationInPoints(10);
    
    bool result = false;
    
    // Get prices and calculate SL/TP
    double price = 0;
    double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
    double sl_price = 0;
    double tp_price = 0;
    
    if(type == "buy")
    {
        price = SymbolInfoDouble(symbol, SYMBOL_ASK);
        if(sl > 0) sl_price = price - sl * point;
        if(tp > 0) tp_price = price + tp * point;
        result = trade.Buy(lot, symbol, price, sl_price, tp_price);
    }
    else if(type == "sell")
    {
        price = SymbolInfoDouble(symbol, SYMBOL_BID);
        if(sl > 0) sl_price = price + sl * point;
        if(tp > 0) tp_price = price - tp * point;
        result = trade.Sell(lot, symbol, price, sl_price, tp_price);
    }
    
    // Result
    if(result)
    {
        ulong ticket = trade.ResultOrder();
        last_ticket = ticket;
        Print("✅ Success! Ticket: ", ticket);
        WriteResult(signal_id, "success", ticket, "OK");
    }
    else
    {
        int error_code = trade.ResultRetcode();
        Print("❌ Failed! Code: ", error_code);
        WriteResult(signal_id, "error", 0, "Code: " + IntegerToString(error_code));
    }
}

//+------------------------------------------------------------------+
//| Clear signal file (FAST)                                        |
//+------------------------------------------------------------------+
void ClearSignalFile(string filepath)
{
    FileDelete(filepath);
    int h = FileOpen(filepath, FILE_WRITE | FILE_TXT);
    if(h != INVALID_HANDLE) FileClose(h);
}

//+------------------------------------------------------------------+
//| Write result (MINIMAL)                                          |
//+------------------------------------------------------------------+
void WriteResult(string signal_id, string status, ulong ticket, string message)
{
    string filepath = "BITTEN\\" + ResultFile;
    int h = FileOpen(filepath, FILE_WRITE | FILE_TXT);
    
    if(h != INVALID_HANDLE)
    {
        string json = "{";
        json += "\"signal_id\":\"" + signal_id + "\",";
        json += "\"status\":\"" + status + "\",";
        json += "\"ticket\":" + IntegerToString(ticket) + ",";
        json += "\"message\":\"" + message + "\",";
        json += "\"balance\":" + DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2);
        json += "}";
        
        FileWriteString(h, json);
        FileClose(h);
    }
}

//+------------------------------------------------------------------+
//| Stream market data (OPTIONAL, MINIMAL)                          |
//+------------------------------------------------------------------+
void StreamMarketData()
{
    if(!http_tested)
    {
        http_tested = true;
        Print("📡 Testing HTTP connection...");
    }
    
    // Minimal JSON - only what's needed
    string json = "{\"uuid\":\"" + uuid + "\",\"ticks\":[";
    
    bool first = true;
    int count = 0;
    
    // Only send first 5 symbols to reduce size
    for(int i = 0; i < 5 && i < ArraySize(symbols); i++)
    {
        MqlTick tick;
        if(SymbolInfoTick(symbols[i], tick))
        {
            if(!first) json += ",";
            first = false;
            
            json += "{";
            json += "\"symbol\":\"" + symbols[i] + "\",";
            json += "\"bid\":" + DoubleToString(tick.bid, (int)SymbolInfoInteger(symbols[i], SYMBOL_DIGITS)) + ",";
            json += "\"ask\":" + DoubleToString(tick.ask, (int)SymbolInfoInteger(symbols[i], SYMBOL_DIGITS));
            json += "}";
            count++;
        }
    }
    
    json += "]}";
    
    if(count > 0)
    {
        SendHTTPPost(MarketDataURL, json);
    }
}

//+------------------------------------------------------------------+
//| Send HTTP POST (SIMPLE)                                         |
//+------------------------------------------------------------------+
void SendHTTPPost(string url, string json_data)
{
    char post[];
    char result[];
    string headers = "Content-Type: application/json\r\n";
    
    StringToCharArray(json_data, post, 0, StringLen(json_data), CP_UTF8);
    ArrayResize(post, ArraySize(post) - 1);
    
    ResetLastError();
    int res = WebRequest("POST", url, headers, 5000, post, result, headers);
    
    // Silent operation - only log errors once
    if(res == -1 && !http_tested)
    {
        int error = GetLastError();
        if(error == 4014)
        {
            Print("⚠️ HTTP disabled - Add URL to allowed list");
            EnableHTTPStream = false; // Auto-disable
        }
    }
}

//+------------------------------------------------------------------+
//| JSON parser (FAST)                                              |
//+------------------------------------------------------------------+
string GetJSONValue(string json, string key)
{
    int key_pos = StringFind(json, "\"" + key + "\"");
    if(key_pos < 0) return "";
    
    int colon_pos = StringFind(json, ":", key_pos);
    if(colon_pos < 0) return "";
    
    int value_start = colon_pos + 1;
    while(value_start < StringLen(json) && StringGetCharacter(json, value_start) == ' ')
        value_start++;
    
    if(value_start >= StringLen(json)) return "";
    
    if(StringGetCharacter(json, value_start) == '"')
    {
        int quote_end = StringFind(json, "\"", value_start + 1);
        if(quote_end > value_start + 1)
            return StringSubstr(json, value_start + 1, quote_end - value_start - 1);
    }
    else
    {
        int value_end = value_start;
        while(value_end < StringLen(json))
        {
            ushort ch = StringGetCharacter(json, value_end);
            if(ch == ',' || ch == '}') break;
            value_end++;
        }
        return StringSubstr(json, value_start, value_end - value_start);
    }
    
    return "";
}

//+------------------------------------------------------------------+
//| Expert deinitialization                                         |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    EventKillTimer();
    Print("🛑 BITTENBridge LEAN stopped");
}

//+------------------------------------------------------------------+
//| OnTick (unused)                                                 |
//+------------------------------------------------------------------+
void OnTick()
{
}