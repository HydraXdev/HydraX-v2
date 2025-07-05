//+------------------------------------------------------------------+
//|                                   BITTENBridge_HYBRID_v1.2.mq5   |
//|                                          BITTEN Trading System   |
//|                     Production-ready file-based bridge for MT5   |
//+------------------------------------------------------------------+
#property strict
#property version   "1.2"
#property description "BITTEN Bridge - Secure file-based trade execution"

// Input parameters
input string InstructionFile = "bitten_instructions.txt";  // Trade instructions from BITTEN
input string ResultFile = "bitten_results.txt";           // Results back to BITTEN
input string StatusFile = "bitten_status.txt";            // Real-time status updates
input int    CheckIntervalMs = 100;                       // Check interval in milliseconds
input int    MaxRetries = 3;                              // Max order retry attempts
input int    SlippagePoints = 20;                         // Max slippage in points
input int    MagicNumber = 20250626;                      // EA identification

// Global variables
datetime lastHeartbeat = 0;
string lastFingerprint = "";
int failedAttempts = 0;

//+------------------------------------------------------------------+
int OnInit()
{
    // Verify file access
    string dataPath = TerminalInfoString(TERMINAL_DATA_PATH) + "\\MQL5\\Files\\";
    Print("=== BITTEN Bridge v1.2 Initialized ===");
    Print("Data Path: ", dataPath);
    Print("Check Interval: ", CheckIntervalMs, "ms");
    
    // Write initial status
    WriteStatus("initialized", "BITTEN Bridge ready");
    
    // Set timer for rapid polling
    EventSetMillisecondTimer(CheckIntervalMs);
    
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    EventKillTimer();
    WriteStatus("shutdown", "Bridge disconnected");
}

//+------------------------------------------------------------------+
void OnTimer()
{
    // Heartbeat every 5 seconds
    if (TimeCurrent() - lastHeartbeat >= 5)
    {
        WriteHeartbeat();
        lastHeartbeat = TimeCurrent();
    }
    
    // Check for instructions
    ProcessInstructions();
}

//+------------------------------------------------------------------+
void ProcessInstructions()
{
    // Check if instruction file exists
    if (!FileIsExist(InstructionFile)) return;
    
    // Read instruction file
    int fileHandle = FileOpen(InstructionFile, FILE_READ | FILE_TXT | FILE_ANSI);
    if (fileHandle == INVALID_HANDLE) 
    {
        WriteStatus("error", "Cannot open instruction file");
        return;
    }
    
    string instruction = FileReadString(fileHandle);
    FileClose(fileHandle);
    
    // Parse instruction (CSV format: ID,SYMBOL,TYPE,LOT,PRICE,TP,SL)
    string parts[];
    int count = StringSplit(instruction, ',', parts);
    
    if (count < 7)
    {
        WriteStatus("error", "Invalid instruction format");
        FileDelete(InstructionFile);
        return;
    }
    
    // Extract parameters
    string tradeId = StringTrim(parts[0]);
    string symbol = StringTrim(parts[1]);
    string typeStr = StringTrim(parts[2]);
    double lot = StringToDouble(parts[3]);
    double price = StringToDouble(parts[4]);
    double tp = StringToDouble(parts[5]);
    double sl = StringToDouble(parts[6]);
    
    // Create fingerprint to prevent duplicates
    string fingerprint = tradeId + symbol + typeStr + DoubleToString(lot, 2);
    if (fingerprint == lastFingerprint)
    {
        FileDelete(InstructionFile);
        return;
    }
    
    // Validate inputs
    if (!ValidateInputs(symbol, typeStr, lot, price))
    {
        WriteResult(tradeId, "rejected", 0, "Invalid parameters");
        FileDelete(InstructionFile);
        return;
    }
    
    // Execute trade
    bool success = ExecuteTrade(tradeId, symbol, typeStr, lot, price, tp, sl);
    
    // Clean up instruction file after processing
    FileDelete(InstructionFile);
    
    // Update fingerprint
    if (success) lastFingerprint = fingerprint;
}

//+------------------------------------------------------------------+
bool ValidateInputs(string symbol, string type, double lot, double price)
{
    // Check symbol exists
    if (!SymbolSelect(symbol, true))
    {
        WriteStatus("error", "Symbol not found: " + symbol);
        return false;
    }
    
    // Check order type
    if (type != "BUY" && type != "SELL")
    {
        WriteStatus("error", "Invalid order type: " + type);
        return false;
    }
    
    // Check lot size
    double minLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
    double maxLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
    if (lot < minLot || lot > maxLot)
    {
        WriteStatus("error", StringFormat("Invalid lot size: %.2f (min: %.2f, max: %.2f)", lot, minLot, maxLot));
        return false;
    }
    
    return true;
}

//+------------------------------------------------------------------+
bool ExecuteTrade(string tradeId, string symbol, string typeStr, double lot, double price, double tp, double sl)
{
    ENUM_ORDER_TYPE orderType = (typeStr == "BUY") ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
    
    MqlTradeRequest request;
    MqlTradeResult result;
    
    // Initialize structures
    ZeroMemory(request);
    ZeroMemory(result);
    
    // Fill request
    request.action = TRADE_ACTION_DEAL;
    request.symbol = symbol;
    request.volume = lot;
    request.type = orderType;
    request.deviation = SlippagePoints;
    request.magic = MagicNumber;
    request.comment = "BITTEN_" + tradeId;
    
    // Get current market price if price is 0
    if (price == 0)
    {
        price = (orderType == ORDER_TYPE_BUY) ? 
                SymbolInfoDouble(symbol, SYMBOL_ASK) : 
                SymbolInfoDouble(symbol, SYMBOL_BID);
    }
    
    // Normalize prices
    int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
    request.price = NormalizeDouble(price, digits);
    request.tp = NormalizeDouble(tp, digits);
    request.sl = NormalizeDouble(sl, digits);
    
    // Determine filling mode
    ENUM_ORDER_TYPE_FILLING filling = GetFillingMode(symbol);
    request.type_filling = filling;
    
    // Attempt to send order with retries
    bool success = false;
    for (int i = 0; i < MaxRetries && !success; i++)
    {
        success = OrderSend(request, result);
        
        if (!success)
        {
            Print("Order attempt ", i+1, " failed: ", result.retcode, " - ", result.comment);
            Sleep(100); // Brief pause before retry
        }
    }
    
    // Log result
    if (success && result.retcode == TRADE_RETCODE_DONE)
    {
        string status = "filled";
        WriteResult(tradeId, status, result.order, "Success");
        WriteStatus("trade_executed", StringFormat("Order %d executed", result.order));
        failedAttempts = 0;
    }
    else
    {
        string status = "failed";
        string error = StringFormat("Error %d: %s", result.retcode, result.comment);
        WriteResult(tradeId, status, 0, error);
        WriteStatus("trade_failed", error);
        failedAttempts++;
    }
    
    return success;
}

//+------------------------------------------------------------------+
ENUM_ORDER_TYPE_FILLING GetFillingMode(string symbol)
{
    // Get symbol filling mode
    int filling = (int)SymbolInfoInteger(symbol, SYMBOL_FILLING_MODE);
    
    if ((filling & SYMBOL_FILLING_FOK) == SYMBOL_FILLING_FOK)
        return ORDER_FILLING_FOK;
    else if ((filling & SYMBOL_FILLING_IOC) == SYMBOL_FILLING_IOC)
        return ORDER_FILLING_IOC;
    else
        return ORDER_FILLING_RETURN;
}

//+------------------------------------------------------------------+
void WriteResult(string tradeId, string status, ulong ticket, string message)
{
    string timestamp = TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS);
    double balance = AccountInfoDouble(ACCOUNT_BALANCE);
    double equity = AccountInfoDouble(ACCOUNT_EQUITY);
    double margin = AccountInfoDouble(ACCOUNT_MARGIN);
    double freeMargin = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
    
    // Create JSON result
    string json = StringFormat(
        "{\"id\":\"%s\",\"status\":\"%s\",\"ticket\":%d,\"message\":\"%s\",\"timestamp\":\"%s\",\"account\":{\"balance\":%.2f,\"equity\":%.2f,\"margin\":%.2f,\"free_margin\":%.2f}}",
        tradeId, status, ticket, message, timestamp, balance, equity, margin, freeMargin
    );
    
    // Write to file
    int handle = FileOpen(ResultFile, FILE_WRITE | FILE_TXT | FILE_ANSI);
    if (handle != INVALID_HANDLE)
    {
        FileWriteString(handle, json);
        FileClose(handle);
    }
}

//+------------------------------------------------------------------+
void WriteStatus(string type, string message)
{
    string timestamp = TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS);
    
    string json = StringFormat(
        "{\"type\":\"%s\",\"message\":\"%s\",\"timestamp\":\"%s\",\"connected\":%s,\"positions\":%d,\"orders\":%d}",
        type, message, timestamp, 
        TerminalInfoInteger(TERMINAL_CONNECTED) ? "true" : "false",
        PositionsTotal(), OrdersTotal()
    );
    
    int handle = FileOpen(StatusFile, FILE_WRITE | FILE_TXT | FILE_ANSI);
    if (handle != INVALID_HANDLE)
    {
        FileWriteString(handle, json);
        FileClose(handle);
    }
}

//+------------------------------------------------------------------+
void WriteHeartbeat()
{
    WriteStatus("heartbeat", StringFormat("Bridge active, failed attempts: %d", failedAttempts));
}

//+------------------------------------------------------------------+
void OnTick()
{
    // Process on tick as backup (belt and suspenders approach)
    static datetime lastTickProcess = 0;
    if (TimeCurrent() - lastTickProcess >= 1)
    {
        ProcessInstructions();
        lastTickProcess = TimeCurrent();
    }
}
//+------------------------------------------------------------------+