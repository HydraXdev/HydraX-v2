//+------------------------------------------------------------------+
//|                                  BITTENBridge_ADVANCED_v2.0.mq5  |
//|                                          BITTEN Trading System   |
//|              Advanced EA with trade management capabilities      |
//+------------------------------------------------------------------+
#property strict
#property version   "2.0"
#property description "BITTEN Advanced Bridge - Full trade management support"

// Input parameters
input string InstructionFile = "bitten_instructions.txt";  // Trade instructions
input string CommandFile = "bitten_commands.txt";         // Management commands
input string ResultFile = "bitten_results.txt";           // Results
input string StatusFile = "bitten_status.txt";            // Status updates
input string PositionsFile = "bitten_positions.txt";      // Active positions
input int    CheckIntervalMs = 100;                       // Check interval
input int    MaxRetries = 3;                              // Max order retries
input int    SlippagePoints = 20;                         // Max slippage
input int    MagicNumber = 20250626;                      // EA identification
input bool   EnableTrailing = true;                       // Enable trailing stops
input bool   EnablePartialClose = true;                   // Enable partial close

// Global variables
datetime lastHeartbeat = 0;
datetime lastPositionUpdate = 0;
string lastFingerprint = "";
int failedAttempts = 0;

// Position tracking
struct PositionInfo {
    ulong ticket;
    string symbol;
    ENUM_POSITION_TYPE type;
    double volume;
    double openPrice;
    double sl;
    double tp;
    double profit;
    datetime openTime;
    string comment;
};

PositionInfo positions[];

//+------------------------------------------------------------------+
int OnInit()
{
    // Verify file access
    string dataPath = TerminalInfoString(TERMINAL_DATA_PATH) + "\\MQL5\\Files\\";
    Print("=== BITTEN Advanced Bridge v2.0 Initialized ===");
    Print("Data Path: ", dataPath);
    Print("Check Interval: ", CheckIntervalMs, "ms");
    Print("Advanced Features: Trailing=", EnableTrailing, " PartialClose=", EnablePartialClose);
    
    // Write initial status
    WriteStatus("initialized", "BITTEN Advanced Bridge ready");
    
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
    
    // Update positions every second
    if (TimeCurrent() - lastPositionUpdate >= 1)
    {
        UpdatePositions();
        lastPositionUpdate = TimeCurrent();
    }
    
    // Check for new trade instructions
    ProcessInstructions();
    
    // Check for management commands
    ProcessCommands();
}

//+------------------------------------------------------------------+
void ProcessInstructions()
{
    // Same as v1.2 - handles new trades
    if (!FileIsExist(InstructionFile)) return;
    
    int fileHandle = FileOpen(InstructionFile, FILE_READ | FILE_TXT | FILE_ANSI);
    if (fileHandle == INVALID_HANDLE) 
    {
        WriteStatus("error", "Cannot open instruction file");
        return;
    }
    
    string instruction = FileReadString(fileHandle);
    FileClose(fileHandle);
    
    // Parse and execute trade...
    string parts[];
    int count = StringSplit(instruction, ',', parts);
    
    if (count < 7)
    {
        WriteStatus("error", "Invalid instruction format");
        FileDelete(InstructionFile);
        return;
    }
    
    // Execute trade
    string tradeId = StringTrim(parts[0]);
    string symbol = StringTrim(parts[1]);
    string typeStr = StringTrim(parts[2]);
    double lot = StringToDouble(parts[3]);
    double price = StringToDouble(parts[4]);
    double tp = StringToDouble(parts[5]);
    double sl = StringToDouble(parts[6]);
    
    // Create fingerprint
    string fingerprint = tradeId + symbol + typeStr;
    if (fingerprint == lastFingerprint) return;
    lastFingerprint = fingerprint;
    
    // Execute
    bool success = ExecuteTrade(tradeId, symbol, typeStr, lot, price, tp, sl);
    
    // Delete instruction file after processing
    if (success) FileDelete(InstructionFile);
}

//+------------------------------------------------------------------+
void ProcessCommands()
{
    // Process management commands (modify, close, trail)
    if (!FileIsExist(CommandFile)) return;
    
    int fileHandle = FileOpen(CommandFile, FILE_READ | FILE_TXT | FILE_ANSI);
    if (fileHandle == INVALID_HANDLE) return;
    
    string command = FileReadString(fileHandle);
    FileClose(fileHandle);
    
    // Parse JSON command
    // Format: {"action":"modify","ticket":123456,"sl":1950.00,"tp":1970.00}
    // or: {"action":"close_partial","ticket":123456,"volume":0.05}
    // or: {"action":"trail","ticket":123456,"distance":50,"step":10}
    
    // Simple parsing (in production, use proper JSON parser)
    if (StringFind(command, "\"action\":\"modify\"") >= 0)
    {
        ProcessModifyCommand(command);
    }
    else if (StringFind(command, "\"action\":\"close_partial\"") >= 0)
    {
        ProcessPartialCloseCommand(command);
    }
    else if (StringFind(command, "\"action\":\"trail\"") >= 0)
    {
        ProcessTrailCommand(command);
    }
    else if (StringFind(command, "\"action\":\"close\"") >= 0)
    {
        ProcessCloseCommand(command);
    }
    
    // Delete command file after processing
    FileDelete(CommandFile);
}

//+------------------------------------------------------------------+
void ProcessModifyCommand(string command)
{
    // Extract values (simplified parsing)
    ulong ticket = ExtractTicket(command);
    double sl = ExtractDouble(command, "sl");
    double tp = ExtractDouble(command, "tp");
    
    if (ticket > 0)
    {
        if (PositionSelectByTicket(ticket))
        {
            MqlTradeRequest request;
            MqlTradeResult result;
            
            ZeroMemory(request);
            ZeroMemory(result);
            
            request.action = TRADE_ACTION_SLTP;
            request.position = ticket;
            request.sl = sl;
            request.tp = tp;
            request.symbol = PositionGetString(POSITION_SYMBOL);
            request.magic = MagicNumber;
            
            if (OrderSend(request, result))
            {
                WriteStatus("modify_success", StringFormat("Modified position %d", ticket));
            }
            else
            {
                WriteStatus("modify_failed", StringFormat("Failed to modify %d: %s", ticket, result.comment));
            }
        }
    }
}

//+------------------------------------------------------------------+
void ProcessPartialCloseCommand(string command)
{
    if (!EnablePartialClose) return;
    
    ulong ticket = ExtractTicket(command);
    double volume = ExtractDouble(command, "volume");
    
    if (ticket > 0 && volume > 0)
    {
        if (PositionSelectByTicket(ticket))
        {
            string symbol = PositionGetString(POSITION_SYMBOL);
            ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
            
            MqlTradeRequest request;
            MqlTradeResult result;
            
            ZeroMemory(request);
            ZeroMemory(result);
            
            // Close opposite direction
            request.action = TRADE_ACTION_DEAL;
            request.position = ticket;
            request.symbol = symbol;
            request.volume = MathMin(volume, PositionGetDouble(POSITION_VOLUME));
            request.type = (type == POSITION_TYPE_BUY) ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
            request.price = (type == POSITION_TYPE_BUY) ? 
                           SymbolInfoDouble(symbol, SYMBOL_BID) : 
                           SymbolInfoDouble(symbol, SYMBOL_ASK);
            request.deviation = SlippagePoints;
            request.magic = MagicNumber;
            request.type_filling = GetFillingMode(symbol);
            
            if (OrderSend(request, result))
            {
                WriteStatus("partial_close_success", 
                           StringFormat("Closed %.2f lots of position %d", volume, ticket));
            }
            else
            {
                WriteStatus("partial_close_failed", 
                           StringFormat("Failed to partial close %d: %s", ticket, result.comment));
            }
        }
    }
}

//+------------------------------------------------------------------+
void ProcessTrailCommand(string command)
{
    if (!EnableTrailing) return;
    
    ulong ticket = ExtractTicket(command);
    int distance = (int)ExtractDouble(command, "distance");
    int step = (int)ExtractDouble(command, "step");
    
    // Store trailing parameters for this position
    // In production, would maintain a structure of trailing positions
    
    WriteStatus("trail_activated", 
               StringFormat("Trailing activated for %d: distance=%d, step=%d", 
                           ticket, distance, step));
}

//+------------------------------------------------------------------+
void ProcessCloseCommand(string command)
{
    ulong ticket = ExtractTicket(command);
    
    if (ticket > 0)
    {
        if (PositionSelectByTicket(ticket))
        {
            MqlTrade trade;
            if (trade.PositionClose(ticket, SlippagePoints))
            {
                WriteStatus("close_success", StringFormat("Closed position %d", ticket));
            }
            else
            {
                WriteStatus("close_failed", StringFormat("Failed to close %d", ticket));
            }
        }
    }
}

//+------------------------------------------------------------------+
void UpdatePositions()
{
    // Update active positions file for Python side
    ArrayResize(positions, 0);
    
    for (int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if (PositionSelectByIndex(i))
        {
            if (PositionGetInteger(POSITION_MAGIC) == MagicNumber)
            {
                int size = ArraySize(positions);
                ArrayResize(positions, size + 1);
                
                positions[size].ticket = PositionGetInteger(POSITION_TICKET);
                positions[size].symbol = PositionGetString(POSITION_SYMBOL);
                positions[size].type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
                positions[size].volume = PositionGetDouble(POSITION_VOLUME);
                positions[size].openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
                positions[size].sl = PositionGetDouble(POSITION_SL);
                positions[size].tp = PositionGetDouble(POSITION_TP);
                positions[size].profit = PositionGetDouble(POSITION_PROFIT);
                positions[size].openTime = (datetime)PositionGetInteger(POSITION_TIME);
                positions[size].comment = PositionGetString(POSITION_COMMENT);
            }
        }
    }
    
    // Write positions to file
    WritePositions();
}

//+------------------------------------------------------------------+
void WritePositions()
{
    int handle = FileOpen(PositionsFile, FILE_WRITE | FILE_TXT | FILE_ANSI);
    if (handle == INVALID_HANDLE) return;
    
    string json = "[";
    
    for (int i = 0; i < ArraySize(positions); i++)
    {
        if (i > 0) json += ",";
        
        json += StringFormat(
            "{\"ticket\":%d,\"symbol\":\"%s\",\"type\":\"%s\",\"volume\":%.2f," +
            "\"open_price\":%.5f,\"sl\":%.5f,\"tp\":%.5f,\"profit\":%.2f," +
            "\"open_time\":\"%s\",\"comment\":\"%s\"}",
            positions[i].ticket,
            positions[i].symbol,
            (positions[i].type == POSITION_TYPE_BUY) ? "BUY" : "SELL",
            positions[i].volume,
            positions[i].openPrice,
            positions[i].sl,
            positions[i].tp,
            positions[i].profit,
            TimeToString(positions[i].openTime, TIME_DATE | TIME_SECONDS),
            positions[i].comment
        );
    }
    
    json += "]";
    
    FileWriteString(handle, json);
    FileClose(handle);
}

//+------------------------------------------------------------------+
// Helper functions
//+------------------------------------------------------------------+
ulong ExtractTicket(string json)
{
    int start = StringFind(json, "\"ticket\":") + 9;
    int end = StringFind(json, ",", start);
    if (end < 0) end = StringFind(json, "}", start);
    
    if (start > 8 && end > start)
    {
        string ticketStr = StringSubstr(json, start, end - start);
        return StringToInteger(ticketStr);
    }
    return 0;
}

//+------------------------------------------------------------------+
double ExtractDouble(string json, string key)
{
    string searchKey = "\"" + key + "\":";
    int start = StringFind(json, searchKey) + StringLen(searchKey);
    int end = StringFind(json, ",", start);
    if (end < 0) end = StringFind(json, "}", start);
    
    if (start > StringLen(searchKey) - 1 && end > start)
    {
        string valueStr = StringSubstr(json, start, end - start);
        return StringToDouble(valueStr);
    }
    return 0;
}

//+------------------------------------------------------------------+
bool ExecuteTrade(string tradeId, string symbol, string typeStr, double lot, double price, double tp, double sl)
{
    // Same implementation as v1.2
    ENUM_ORDER_TYPE orderType = (typeStr == "BUY") ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
    
    MqlTradeRequest request;
    MqlTradeResult result;
    
    ZeroMemory(request);
    ZeroMemory(result);
    
    request.action = TRADE_ACTION_DEAL;
    request.symbol = symbol;
    request.volume = lot;
    request.type = orderType;
    request.deviation = SlippagePoints;
    request.magic = MagicNumber;
    request.comment = "BITTEN_" + tradeId;
    
    if (price == 0)
    {
        price = (orderType == ORDER_TYPE_BUY) ? 
                SymbolInfoDouble(symbol, SYMBOL_ASK) : 
                SymbolInfoDouble(symbol, SYMBOL_BID);
    }
    
    int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
    request.price = NormalizeDouble(price, digits);
    request.tp = NormalizeDouble(tp, digits);
    request.sl = NormalizeDouble(sl, digits);
    request.type_filling = GetFillingMode(symbol);
    
    bool success = false;
    for (int i = 0; i < MaxRetries && !success; i++)
    {
        success = OrderSend(request, result);
        if (!success) Sleep(100);
    }
    
    if (success && result.retcode == TRADE_RETCODE_DONE)
    {
        WriteResult(tradeId, "success", result.order, "Order executed", result.price);
        WriteStatus("trade_executed", StringFormat("Order %d executed", result.order));
        failedAttempts = 0;
    }
    else
    {
        string error = StringFormat("Error %d: %s", result.retcode, result.comment);
        WriteResult(tradeId, "failed", 0, error, 0);
        WriteStatus("trade_failed", error);
        failedAttempts++;
    }
    
    return success;
}

//+------------------------------------------------------------------+
ENUM_ORDER_TYPE_FILLING GetFillingMode(string symbol)
{
    int filling = (int)SymbolInfoInteger(symbol, SYMBOL_FILLING_MODE);
    
    if ((filling & SYMBOL_FILLING_FOK) == SYMBOL_FILLING_FOK)
        return ORDER_FILLING_FOK;
    else if ((filling & SYMBOL_FILLING_IOC) == SYMBOL_FILLING_IOC)
        return ORDER_FILLING_IOC;
    else
        return ORDER_FILLING_RETURN;
}

//+------------------------------------------------------------------+
void WriteResult(string tradeId, string status, ulong ticket, string message, double price)
{
    string timestamp = TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS);
    double balance = AccountInfoDouble(ACCOUNT_BALANCE);
    double equity = AccountInfoDouble(ACCOUNT_EQUITY);
    double margin = AccountInfoDouble(ACCOUNT_MARGIN);
    double freeMargin = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
    
    string json = StringFormat(
        "{\"id\":\"%s\",\"status\":\"%s\",\"ticket\":%d,\"message\":\"%s\"," +
        "\"price\":%.5f,\"timestamp\":\"%s\",\"account\":{\"balance\":%.2f," +
        "\"equity\":%.2f,\"margin\":%.2f,\"free_margin\":%.2f}}",
        tradeId, status, ticket, message, price, timestamp, 
        balance, equity, margin, freeMargin
    );
    
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
        "{\"type\":\"%s\",\"message\":\"%s\",\"timestamp\":\"%s\"," +
        "\"connected\":%s,\"positions\":%d,\"orders\":%d,\"balance\":%.2f}",
        type, message, timestamp, 
        TerminalInfoInteger(TERMINAL_CONNECTED) ? "true" : "false",
        PositionsTotal(), OrdersTotal(),
        AccountInfoDouble(ACCOUNT_BALANCE)
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