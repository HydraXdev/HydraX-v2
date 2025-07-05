//+------------------------------------------------------------------+
//|                          BITTENBridge_HYBRID_v1.2_SECURE.mq5     |
//|                                          BITTEN Trading System   |
//|                     Production-ready file-based bridge for MT5   |
//|                         Enhanced with security validations       |
//+------------------------------------------------------------------+
#property strict
#property version   "1.2"
#property description "BITTEN Bridge - Secure file-based trade execution with enhanced validation"

// Input parameters with validation ranges
input string InstructionFile = "bitten_instructions.txt";  // Trade instructions from BITTEN
input string ResultFile = "bitten_results.txt";           // Results back to BITTEN
input string StatusFile = "bitten_status.txt";            // Real-time status updates
input int    CheckIntervalMs = 100;                       // Check interval in milliseconds (50-1000)
input int    MaxRetries = 3;                              // Max order retry attempts (1-5)
input int    SlippagePoints = 20;                         // Max slippage in points (0-100)
input int    MagicNumber = 20250626;                      // EA identification
input double MaxLotSize = 10.0;                           // Maximum allowed lot size
input double MaxRiskPercent = 5.0;                        // Maximum risk per trade (%)
input int    MaxDailyTrades = 50;                         // Maximum trades per day

// Global variables
datetime lastHeartbeat = 0;
string lastFingerprint = "";
int failedAttempts = 0;
int dailyTradeCount = 0;
datetime lastTradeDate = 0;

// Security constants
const int MIN_CHECK_INTERVAL = 50;
const int MAX_CHECK_INTERVAL = 1000;
const int MIN_RETRIES = 1;
const int MAX_RETRIES = 5;
const int MAX_SLIPPAGE = 100;
const double MIN_LOT_MULTIPLIER = 0.01;
const int MAX_INSTRUCTION_LENGTH = 500;

//+------------------------------------------------------------------+
int OnInit()
{
    // Validate input parameters
    if (CheckIntervalMs < MIN_CHECK_INTERVAL || CheckIntervalMs > MAX_CHECK_INTERVAL)
    {
        Print("ERROR: CheckIntervalMs must be between ", MIN_CHECK_INTERVAL, " and ", MAX_CHECK_INTERVAL);
        return INIT_PARAMETERS_INCORRECT;
    }
    
    if (MaxRetries < MIN_RETRIES || MaxRetries > MAX_RETRIES)
    {
        Print("ERROR: MaxRetries must be between ", MIN_RETRIES, " and ", MAX_RETRIES);
        return INIT_PARAMETERS_INCORRECT;
    }
    
    if (SlippagePoints < 0 || SlippagePoints > MAX_SLIPPAGE)
    {
        Print("ERROR: SlippagePoints must be between 0 and ", MAX_SLIPPAGE);
        return INIT_PARAMETERS_INCORRECT;
    }
    
    if (MaxLotSize <= 0 || MaxLotSize > 100)
    {
        Print("ERROR: MaxLotSize must be between 0 and 100");
        return INIT_PARAMETERS_INCORRECT;
    }
    
    if (MaxRiskPercent <= 0 || MaxRiskPercent > 10)
    {
        Print("ERROR: MaxRiskPercent must be between 0 and 10");
        return INIT_PARAMETERS_INCORRECT;
    }
    
    if (MaxDailyTrades < 1 || MaxDailyTrades > 100)
    {
        Print("ERROR: MaxDailyTrades must be between 1 and 100");
        return INIT_PARAMETERS_INCORRECT;
    }
    
    // Verify file access
    string dataPath = TerminalInfoString(TERMINAL_DATA_PATH) + "\\MQL5\\Files\\";
    Print("=== BITTEN Bridge v1.2 SECURE Initialized ===");
    Print("Data Path: ", dataPath);
    Print("Check Interval: ", CheckIntervalMs, "ms");
    Print("Max Lot Size: ", MaxLotSize);
    Print("Max Risk: ", MaxRiskPercent, "%");
    Print("Max Daily Trades: ", MaxDailyTrades);
    
    // Write initial status
    WriteStatus("initialized", "BITTEN Bridge SECURE ready");
    
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
    // Reset daily counter at midnight
    datetime currentDate = TimeCurrent() - (TimeCurrent() % 86400);
    if (currentDate != lastTradeDate)
    {
        dailyTradeCount = 0;
        lastTradeDate = currentDate;
    }
    
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
    
    // Check daily trade limit
    if (dailyTradeCount >= MaxDailyTrades)
    {
        WriteStatus("error", "Daily trade limit reached");
        FileDelete(InstructionFile);
        return;
    }
    
    // Read instruction file with size limit
    int fileHandle = FileOpen(InstructionFile, FILE_READ | FILE_TXT | FILE_ANSI);
    if (fileHandle == INVALID_HANDLE) 
    {
        WriteStatus("error", "Cannot open instruction file");
        return;
    }
    
    // Check file size
    ulong fileSize = FileSize(fileHandle);
    if (fileSize > MAX_INSTRUCTION_LENGTH)
    {
        FileClose(fileHandle);
        WriteStatus("error", "Instruction file too large");
        FileDelete(InstructionFile);
        return;
    }
    
    string instruction = FileReadString(fileHandle);
    FileClose(fileHandle);
    
    // Validate instruction length
    if (StringLen(instruction) > MAX_INSTRUCTION_LENGTH)
    {
        WriteStatus("error", "Instruction too long");
        FileDelete(InstructionFile);
        return;
    }
    
    // Parse instruction (CSV format: ID,SYMBOL,TYPE,LOT,PRICE,TP,SL)
    string parts[];
    int count = StringSplit(instruction, ',', parts);
    
    if (count < 7)
    {
        WriteStatus("error", "Invalid instruction format");
        FileDelete(InstructionFile);
        return;
    }
    
    // Extract and validate parameters
    string tradeId = StringTrim(parts[0]);
    string symbol = StringTrim(parts[1]);
    string typeStr = StringTrim(parts[2]);
    double lot = StringToDouble(parts[3]);
    double price = StringToDouble(parts[4]);
    double tp = StringToDouble(parts[5]);
    double sl = StringToDouble(parts[6]);
    
    // Validate trade ID length
    if (StringLen(tradeId) > 50 || StringLen(tradeId) < 1)
    {
        WriteStatus("error", "Invalid trade ID length");
        FileDelete(InstructionFile);
        return;
    }
    
    // Validate symbol format (alphanumeric only)
    if (!IsValidSymbolFormat(symbol))
    {
        WriteStatus("error", "Invalid symbol format");
        FileDelete(InstructionFile);
        return;
    }
    
    // Create fingerprint to prevent duplicates
    string fingerprint = tradeId + symbol + typeStr + DoubleToString(lot, 2);
    if (fingerprint == lastFingerprint)
    {
        FileDelete(InstructionFile);
        return;
    }
    
    // Enhanced input validation
    if (!ValidateInputs(symbol, typeStr, lot, price, tp, sl))
    {
        WriteResult(tradeId, "rejected", 0, "Invalid parameters");
        FileDelete(InstructionFile);
        return;
    }
    
    // Execute trade
    bool success = ExecuteTrade(tradeId, symbol, typeStr, lot, price, tp, sl);
    
    // Clean up instruction file after processing
    FileDelete(InstructionFile);
    
    // Update fingerprint and counter
    if (success) 
    {
        lastFingerprint = fingerprint;
        dailyTradeCount++;
    }
}

//+------------------------------------------------------------------+
bool IsValidSymbolFormat(string symbol)
{
    // Check length
    int len = StringLen(symbol);
    if (len < 6 || len > 10) return false;
    
    // Check each character is alphanumeric
    for (int i = 0; i < len; i++)
    {
        ushort ch = StringGetCharacter(symbol, i);
        if (!((ch >= 'A' && ch <= 'Z') || (ch >= '0' && ch <= '9')))
            return false;
    }
    
    return true;
}

//+------------------------------------------------------------------+
bool ValidateInputs(string symbol, string type, double lot, double price, double tp, double sl)
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
    
    // Enhanced lot size validation
    double minLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
    double maxLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
    double lotStep = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
    
    // Apply global maximum
    maxLot = MathMin(maxLot, MaxLotSize);
    
    if (lot < minLot || lot > maxLot)
    {
        WriteStatus("error", StringFormat("Invalid lot size: %.2f (min: %.2f, max: %.2f)", lot, minLot, maxLot));
        return false;
    }
    
    // Validate lot step
    double lotMod = MathMod(lot - minLot, lotStep);
    if (lotMod > 0.00001)
    {
        WriteStatus("error", StringFormat("Lot size not aligned with step: %.2f (step: %.2f)", lot, lotStep));
        return false;
    }
    
    // Validate prices are positive
    if (price < 0 || (tp < 0 && tp != 0) || (sl < 0 && sl != 0))
    {
        WriteStatus("error", "Negative price values not allowed");
        return false;
    }
    
    // Risk validation
    if (sl > 0)
    {
        double accountBalance = AccountInfoDouble(ACCOUNT_BALANCE);
        double tickValue = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE);
        double tickSize = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_SIZE);
        
        // Get current price if market order
        if (price == 0)
        {
            price = (type == "BUY") ? 
                    SymbolInfoDouble(symbol, SYMBOL_ASK) : 
                    SymbolInfoDouble(symbol, SYMBOL_BID);
        }
        
        // Calculate risk
        double priceDiff = MathAbs(price - sl);
        double ticks = priceDiff / tickSize;
        double riskAmount = ticks * tickValue * lot;
        double riskPercent = (riskAmount / accountBalance) * 100;
        
        if (riskPercent > MaxRiskPercent)
        {
            WriteStatus("error", StringFormat("Risk too high: %.2f%% (max: %.2f%%)", riskPercent, MaxRiskPercent));
            return false;
        }
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
    
    // Additional SL/TP validation
    if (request.sl > 0)
    {
        double minStop = SymbolInfoInteger(symbol, SYMBOL_TRADE_STOPS_LEVEL) * SymbolInfoDouble(symbol, SYMBOL_POINT);
        if (orderType == ORDER_TYPE_BUY)
        {
            if (request.price - request.sl < minStop)
            {
                WriteStatus("error", "Stop loss too close to entry");
                return false;
            }
        }
        else
        {
            if (request.sl - request.price < minStop)
            {
                WriteStatus("error", "Stop loss too close to entry");
                return false;
            }
        }
    }
    
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
    
    // Sanitize message to prevent JSON injection
    StringReplace(message, "\"", "'");
    StringReplace(message, "\n", " ");
    StringReplace(message, "\r", " ");
    
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
    
    // Sanitize message
    StringReplace(message, "\"", "'");
    StringReplace(message, "\n", " ");
    StringReplace(message, "\r", " ");
    
    string json = StringFormat(
        "{\"type\":\"%s\",\"message\":\"%s\",\"timestamp\":\"%s\",\"connected\":%s,\"positions\":%d,\"orders\":%d,\"daily_trades\":%d,\"max_daily\":%d}",
        type, message, timestamp, 
        TerminalInfoInteger(TERMINAL_CONNECTED) ? "true" : "false",
        PositionsTotal(), OrdersTotal(),
        dailyTradeCount, MaxDailyTrades
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
    WriteStatus("heartbeat", StringFormat("Bridge active, failed attempts: %d, daily trades: %d/%d", 
                                         failedAttempts, dailyTradeCount, MaxDailyTrades));
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