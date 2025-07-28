//+------------------------------------------------------------------+
//|                     BITTENBridge_TradeExecutor_PRODUCTION.mq5     |
//|                 Production EA - Robust 3-Way Communication        |
//+------------------------------------------------------------------+
#property strict
#property copyright "BITTEN Trading System"
#property version   "5.0"
#property description "Production EA with robust HTTP streaming and file-based execution"

#include <Trade/Trade.mqh>
CTrade trade;

// Input parameters
input string SignalFile = "fire.txt";                // Signal file to monitor
input string ResultFile = "trade_result.txt";        // Result file for feedback
input string UUIDFile = "uuid.txt";                  // UUID file for identification
input string MarketDataURL = "http://127.0.0.1:8001/market-data"; // Market data endpoint
input int StreamInterval = 5;                        // Stream market data every 5 seconds
input int CheckInterval = 1;                         // Check for signals every 1 second
input int MaxHTTPRetries = 1000000;                 // Essentially unlimited retries
input bool VerboseLogging = false;                  // Detailed logging (off for production)

// Global variables
string uuid = "unknown";
ulong last_ticket = 0;
string last_signal_id = "";
datetime last_stream_time = 0;
datetime last_check_time = 0;
int check_counter = 0;
int stream_counter = 0;
int http_consecutive_errors = 0;
bool http_working = false;
datetime last_http_success = 0;

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
    Print("🚀 BITTENBridge PRODUCTION v5.0");
    Print("📡 3-Way Communication: HTTP→Engine | File→EA | File→Core");
    Print("✅ Robust streaming with unlimited retries");
    Print("======================================================");
    
    // Load or generate UUID
    LoadUUID();
    
    // Set timer
    EventSetTimer(1);
    
    // Initialize files
    InitializeFiles();
    
    // Log configuration
    Print("📋 Configuration:");
    Print("   UUID: ", uuid);
    Print("   Market Data URL: ", MarketDataURL);
    Print("   Stream Interval: ", StreamInterval, " seconds");
    Print("   HTTP Retries: Unlimited");
    
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
        // Generate UUID based on account and timestamp
        uuid = "mt5_" + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)) + 
               "_" + IntegerToString(TimeCurrent());
        
        // Save UUID
        h = FileOpen(UUIDFile, FILE_WRITE | FILE_TXT);
        if(h != INVALID_HANDLE)
        {
            FileWriteString(h, uuid);
            FileClose(h);
            Print("📌 UUID generated: ", uuid);
        }
    }
}

//+------------------------------------------------------------------+
//| Initialize required files                                        |
//+------------------------------------------------------------------+
void InitializeFiles()
{
    string bittenDir = "BITTEN\\";
    
    // Ensure fire.txt is empty
    string filepath = bittenDir + SignalFile;
    FileDelete(filepath);
    int h = FileOpen(filepath, FILE_WRITE | FILE_TXT);
    if(h != INVALID_HANDLE)
    {
        FileClose(h);
        Print("✅ Initialized: ", filepath);
    }
    
    // Also create in root
    FileDelete(SignalFile);
    h = FileOpen(SignalFile, FILE_WRITE | FILE_TXT);
    if(h != INVALID_HANDLE)
    {
        FileClose(h);
    }
    
    // Initialize result file
    filepath = bittenDir + ResultFile;
    h = FileOpen(filepath, FILE_WRITE | FILE_TXT);
    if(h != INVALID_HANDLE)
    {
        FileClose(h);
        Print("✅ Initialized: ", filepath);
    }
}

//+------------------------------------------------------------------+
//| Timer function - Core of 3-way communication                     |
//+------------------------------------------------------------------+
void OnTimer()
{
    datetime current_time = TimeCurrent();
    
    // PRIORITY 1: Check for trade signals (file-based from Core)
    if(current_time - last_check_time >= CheckInterval)
    {
        CheckFireSignal();
        last_check_time = current_time;
    }
    
    // PRIORITY 2: Stream market data (HTTP to Engine)
    if(current_time - last_stream_time >= StreamInterval)
    {
        if(IsMarketOpen())
        {
            StreamMarketData();
        }
        else if(stream_counter % 12 == 0) // Log every minute when closed
        {
            Print("🔴 Market closed - HTTP streaming paused");
        }
        last_stream_time = current_time;
        stream_counter++;
    }
}

//+------------------------------------------------------------------+
//| Check if market is open (more robust)                          |
//+------------------------------------------------------------------+
bool IsMarketOpen()
{
    // Check multiple symbols for redundancy
    string checkSymbols[] = {"EURUSD", "GBPUSD", "USDJPY"};
    
    for(int i = 0; i < ArraySize(checkSymbols); i++)
    {
        MqlTick tick;
        if(SymbolInfoTick(checkSymbols[i], tick))
        {
            datetime tick_age = TimeCurrent() - tick.time;
            if(tick_age < 300) // Within 5 minutes
            {
                return true;
            }
        }
    }
    
    return false;
}

//+------------------------------------------------------------------+
//| Check for trade signals - FILE BASED FROM CORE                  |
//+------------------------------------------------------------------+
void CheckFireSignal()
{
    check_counter++;
    
    // Check both locations
    string locations[] = {
        "BITTEN\\" + SignalFile,
        SignalFile
    };
    
    for(int i = 0; i < ArraySize(locations); i++)
    {
        if(!FileIsExist(locations[i]))
            continue;
            
        int h = FileOpen(locations[i], FILE_READ | FILE_TXT);
        if(h == INVALID_HANDLE)
            continue;
        
        ulong size = FileSize(h);
        
        // Skip too small files
        if(size < 20)
        {
            FileClose(h);
            if(size > 0)
            {
                ClearSignalFile(locations[i]);
            }
            continue;
        }
        
        // Read content
        string content = "";
        while(!FileIsEnding(h) && StringLen(content) < 50000)
        {
            content += FileReadString(h);
        }
        FileClose(h);
        
        // Validate JSON
        if(StringFind(content, "{") >= 0 && 
           StringFind(content, "}") >= 0 &&
           StringFind(content, "symbol") >= 0)
        {
            Print("📨 SIGNAL RECEIVED! Processing...");
            ProcessSignal(content, locations[i]);
            return;
        }
        else
        {
            ClearSignalFile(locations[i]);
        }
    }
    
    // Status update
    if(VerboseLogging && check_counter % 60 == 0)
    {
        Print("👀 Monitoring... Checks: ", check_counter, " | Streams: ", stream_counter);
    }
}

//+------------------------------------------------------------------+
//| Process signal and execute trade                                |
//+------------------------------------------------------------------+
void ProcessSignal(string content, string filepath)
{
    // Parse signal
    string signal_id = GetJSONValue(content, "signal_id");
    string action = GetJSONValue(content, "action");
    string symbol = GetJSONValue(content, "symbol");
    string type = GetJSONValue(content, "type");
    double lot = StringToDouble(GetJSONValue(content, "lot"));
    double sl = StringToDouble(GetJSONValue(content, "sl"));
    double tp = StringToDouble(GetJSONValue(content, "tp"));
    string comment = GetJSONValue(content, "comment");
    
    // Validate
    if(symbol == "" || (type == "" && action == ""))
    {
        Print("❌ Invalid signal format");
        WriteResult(signal_id, "error", 0, "Invalid signal format");
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
    
    // Handle close action
    if(action == "close")
    {
        Print("🔄 Closing positions for ", symbol);
        ClosePositionsBySymbol(symbol);
        last_signal_id = signal_id;
        ClearSignalFile(filepath);
        return;
    }
    
    // Validate symbol
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
        Print("❌ Symbol not in allowed list: ", symbol);
        WriteResult(signal_id, "error", 0, "Invalid symbol");
        ClearSignalFile(filepath);
        return;
    }
    
    // Ensure symbol selected
    if(!SymbolSelect(symbol, true))
    {
        Print("❌ Failed to select symbol: ", symbol);
        WriteResult(signal_id, "error", 0, "Symbol selection failed");
        ClearSignalFile(filepath);
        return;
    }
    
    // Execute trade
    Print("🎯 Executing ", type, " ", symbol, " ", lot > 0 ? lot : 0.01, " lots");
    ExecuteTrade(signal_id, symbol, type, lot > 0 ? lot : 0.01, sl, tp, 
                 comment != "" ? comment : "BITTEN_" + signal_id);
    
    last_signal_id = signal_id;
    ClearSignalFile(filepath);
}

//+------------------------------------------------------------------+
//| Execute trade                                                    |
//+------------------------------------------------------------------+
void ExecuteTrade(string signal_id, string symbol, string type, double lot, 
                  double sl, double tp, string trade_comment)
{
    // Normalize lot size
    double minLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
    double maxLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
    double lotStep = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
    
    lot = MathMax(minLot, lot);
    lot = MathMin(maxLot, lot);
    lot = NormalizeDouble(lot / lotStep, 0) * lotStep;
    
    // Setup trade
    trade.SetExpertMagicNumber(777001);
    trade.SetComment(trade_comment);
    trade.SetDeviationInPoints(10);
    
    bool result = false;
    double price = 0;
    double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
    double sl_price = 0;
    double tp_price = 0;
    
    if(type == "buy")
    {
        price = SymbolInfoDouble(symbol, SYMBOL_ASK);
        if(sl > 0) sl_price = price - sl * point;
        if(tp > 0) tp_price = price + tp * point;
        result = trade.Buy(lot, symbol, price, sl_price, tp_price, trade_comment);
    }
    else if(type == "sell")
    {
        price = SymbolInfoDouble(symbol, SYMBOL_BID);
        if(sl > 0) sl_price = price + sl * point;
        if(tp > 0) tp_price = price - tp * point;
        result = trade.Sell(lot, symbol, price, sl_price, tp_price, trade_comment);
    }
    
    // Write result - FILE BASED TO CORE
    if(result)
    {
        ulong ticket = trade.ResultOrder();
        last_ticket = ticket;
        Print("✅ Trade executed! Ticket: ", ticket);
        WriteResult(signal_id, "success", ticket, "Executed at " + DoubleToString(price, 5));
    }
    else
    {
        int error_code = trade.ResultRetcode();
        string error_msg = trade.ResultRetcodeDescription();
        Print("❌ Trade failed: ", error_msg, " (", error_code, ")");
        WriteResult(signal_id, "error", 0, error_msg);
    }
}

//+------------------------------------------------------------------+
//| Close positions by symbol                                       |
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
                    closed++;
                    Print("✅ Closed position: ", ticket);
                }
            }
        }
    }
    
    WriteResult("", "closed", 0, IntegerToString(closed) + " positions closed");
}

//+------------------------------------------------------------------+
//| Clear signal file                                               |
//+------------------------------------------------------------------+
void ClearSignalFile(string filepath)
{
    FileDelete(filepath);
    int h = FileOpen(filepath, FILE_WRITE | FILE_TXT);
    if(h != INVALID_HANDLE) FileClose(h);
}

//+------------------------------------------------------------------+
//| Write result - FILE BASED TO CORE with full account data       |
//+------------------------------------------------------------------+
void WriteResult(string signal_id, string status, ulong ticket, string message)
{
    string filepath = "BITTEN\\" + ResultFile;
    int h = FileOpen(filepath, FILE_WRITE | FILE_TXT);
    
    if(h != INVALID_HANDLE)
    {
        // Build comprehensive result
        string json = "{";
        json += "\"signal_id\":\"" + signal_id + "\",";
        json += "\"status\":\"" + status + "\",";
        json += "\"ticket\":" + IntegerToString(ticket) + ",";
        json += "\"message\":\"" + message + "\",";
        json += "\"timestamp\":\"" + TimeToString(TimeCurrent()) + "\",";
        json += "\"uuid\":\"" + uuid + "\",";
        
        // Full account data for Core
        json += "\"account\":{";
        json += "\"balance\":" + DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2) + ",";
        json += "\"equity\":" + DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2) + ",";
        json += "\"margin\":" + DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN), 2) + ",";
        json += "\"free_margin\":" + DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN_FREE), 2) + ",";
        json += "\"profit\":" + DoubleToString(AccountInfoDouble(ACCOUNT_PROFIT), 2) + ",";
        json += "\"margin_level\":" + DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN_LEVEL), 2) + ",";
        json += "\"leverage\":" + IntegerToString(AccountInfoInteger(ACCOUNT_LEVERAGE)) + ",";
        json += "\"currency\":\"" + AccountInfoString(ACCOUNT_CURRENCY) + "\",";
        json += "\"server\":\"" + AccountInfoString(ACCOUNT_SERVER) + "\",";
        json += "\"company\":\"" + AccountInfoString(ACCOUNT_COMPANY) + "\",";
        json += "\"positions\":" + IntegerToString(PositionsTotal());
        json += "}";
        
        json += "}";
        
        FileWriteString(h, json);
        FileClose(h);
        
        if(VerboseLogging)
        {
            Print("📝 Result written to Core");
        }
    }
}

//+------------------------------------------------------------------+
//| Stream market data - HTTP TO ENGINE (ROBUST)                    |
//+------------------------------------------------------------------+
void StreamMarketData()
{
    // Build market data JSON
    string json = "{";
    json += "\"uuid\":\"" + uuid + "\",";
    json += "\"timestamp\":" + IntegerToString(TimeCurrent()) + ",";
    json += "\"account_balance\":" + DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2) + ",";
    json += "\"broker\":\"" + AccountInfoString(ACCOUNT_COMPANY) + "\",";
    json += "\"server\":\"" + AccountInfoString(ACCOUNT_SERVER) + "\",";
    json += "\"ticks\":[";
    
    bool first = true;
    int validTicks = 0;
    
    // Stream ALL 15 pairs for complete market view
    for(int i = 0; i < ArraySize(symbols); i++)
    {
        MqlTick tick;
        if(SymbolInfoTick(symbols[i], tick))
        {
            if(!first) json += ",";
            first = false;
            
            double spread = (tick.ask - tick.bid) / SymbolInfoDouble(symbols[i], SYMBOL_POINT);
            
            json += "{";
            json += "\"symbol\":\"" + symbols[i] + "\",";
            json += "\"bid\":" + DoubleToString(tick.bid, (int)SymbolInfoInteger(symbols[i], SYMBOL_DIGITS)) + ",";
            json += "\"ask\":" + DoubleToString(tick.ask, (int)SymbolInfoInteger(symbols[i], SYMBOL_DIGITS)) + ",";
            json += "\"spread\":" + DoubleToString(spread, 1) + ",";
            json += "\"volume\":" + IntegerToString(tick.volume) + ",";
            json += "\"time\":" + IntegerToString(tick.time);
            json += "}";
            
            validTicks++;
        }
    }
    
    json += "]}";
    
    // Send if we have data
    if(validTicks > 0)
    {
        SendHTTPPost(MarketDataURL, json);
    }
}

//+------------------------------------------------------------------+
//| Send HTTP POST - ROBUST WITH UNLIMITED RETRIES                  |
//+------------------------------------------------------------------+
void SendHTTPPost(string url, string json_data)
{
    char post[];
    char result[];
    string headers;
    
    // Prepare data
    StringToCharArray(json_data, post, 0, StringLen(json_data), CP_UTF8);
    ArrayResize(post, ArraySize(post) - 1);
    
    headers = "Content-Type: application/json\r\n";
    headers += "User-Agent: BITTENBridge/5.0\r\n";
    
    // Send with retry logic
    ResetLastError();
    int res = WebRequest("POST", url, headers, 5000, post, result, headers);
    
    if(res == 200)
    {
        // Success
        http_consecutive_errors = 0;
        last_http_success = TimeCurrent();
        
        if(!http_working)
        {
            Print("✅ HTTP streaming connected!");
            http_working = true;
        }
    }
    else
    {
        // Error but keep trying
        http_consecutive_errors++;
        
        if(res == -1)
        {
            int error = GetLastError();
            
            // Log errors sparingly
            if(http_consecutive_errors == 1)
            {
                Print("⚠️ HTTP error ", error, " - will keep retrying...");
                
                if(error == 4014)
                {
                    Print("💡 Add ", url, " to allowed URLs in MT5");
                }
            }
            else if(http_consecutive_errors % 100 == 0)
            {
                Print("⚠️ HTTP retry #", http_consecutive_errors);
            }
        }
        
        http_working = false;
    }
}

//+------------------------------------------------------------------+
//| JSON parser                                                      |
//+------------------------------------------------------------------+
string GetJSONValue(string json, string key)
{
    int key_pos = StringFind(json, "\"" + key + "\"");
    if(key_pos < 0) return "";
    
    int colon_pos = StringFind(json, ":", key_pos);
    if(colon_pos < 0) return "";
    
    int value_start = colon_pos + 1;
    while(value_start < StringLen(json) && 
          (StringGetCharacter(json, value_start) == ' ' || 
           StringGetCharacter(json, value_start) == '\t'))
    {
        value_start++;
    }
    
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
            if(ch == ',' || ch == '}' || ch == ']' || 
               ch == ' ' || ch == '\n' || ch == '\r')
                break;
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
    Print("======================================================");
    Print("🛑 BITTENBridge PRODUCTION stopped");
    Print("📊 Stats:");
    Print("   Signal checks: ", check_counter);
    Print("   HTTP streams: ", stream_counter);
    Print("   HTTP errors: ", http_consecutive_errors);
    Print("   Last trade: ", last_ticket);
    Print("======================================================");
}

//+------------------------------------------------------------------+
//| OnTick (unused - all work in timer)                            |
//+------------------------------------------------------------------+
void OnTick()
{
}