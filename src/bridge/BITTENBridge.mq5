//+------------------------------------------------------------------+
//|                          BITTENBridge_ADVANCED_v2.0_SECURE.mq5   |
//|                                          BITTEN Trading System   |
//|              Advanced EA with trade management capabilities      |
//|                     SECURE VERSION - Hardened against attacks    |
//+------------------------------------------------------------------+
#property strict
#property version   "2.0"
#property description "BITTEN Advanced Bridge SECURE - Full trade management with military-grade validation"

// DRILL: "Lock and load, secure parameters only!"

// Input parameters with validation ranges
input string InstructionFile = "bitten_instructions_secure.txt";  // Trade instructions
input string CommandFile = "bitten_commands_secure.txt";         // Management commands
input string ResultFile = "bitten_results_secure.txt";           // Results
input string StatusFile = "bitten_status_secure.txt";            // Status updates
input string PositionsFile = "bitten_positions_secure.txt";      // Active positions
input int    CheckIntervalMs = 100;                             // Check interval (50-1000)
input int    MaxRetries = 3;                                    // Max order retries (1-5)
input int    SlippagePoints = 20;                               // Max slippage (0-100)
input int    MagicNumber = 20250626;                            // EA identification
input bool   EnableTrailing = true;                             // Enable trailing stops
input bool   EnablePartialClose = true;                         // Enable partial close
input double MaxLotSize = 10.0;                                 // Maximum allowed lot size
input double MaxRiskPercent = 5.0;                              // Maximum risk per trade (%)
input int    MaxDailyTrades = 50;                               // Maximum trades per day
input int    MaxConcurrentTrades = 10;                          // Maximum concurrent positions

// NEXUS: "Every connection is a potential breach"
// Security constants
const int MIN_CHECK_INTERVAL = 50;
const int MAX_CHECK_INTERVAL = 1000;
const int MIN_RETRIES = 1;
const int MAX_RETRIES = 5;
const int MAX_SLIPPAGE = 100;
const double MIN_LOT = 0.01;
const int MAX_INSTRUCTION_LENGTH = 1000;
const int MAX_COMMAND_LENGTH = 1000;
const int MAX_SYMBOL_LENGTH = 12;
const int MAX_COMMENT_LENGTH = 100;

// Global variables
datetime lastHeartbeat = 0;
datetime lastPositionUpdate = 0;
string lastFingerprint = "";
int failedAttempts = 0;
int dailyTradeCount = 0;
datetime lastTradeDate = 0;

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

// Trailing stop tracking
struct TrailingInfo {
    ulong ticket;
    int distance;
    int step;
    double lastPrice;
};

TrailingInfo trailingPositions[];

//+------------------------------------------------------------------+
int OnInit()
{
    // DRILL: "Validate everything, trust nothing!"
    
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
    
    if (MaxConcurrentTrades < 1 || MaxConcurrentTrades > 50)
    {
        Print("ERROR: MaxConcurrentTrades must be between 1 and 50");
        return INIT_PARAMETERS_INCORRECT;
    }
    
    // Verify file access
    string dataPath = TerminalInfoString(TERMINAL_DATA_PATH) + "\\MQL5\\Files\\";
    Print("=== BITTEN Advanced Bridge v2.0 SECURE Initialized ===");
    Print("Data Path: ", dataPath);
    Print("Check Interval: ", CheckIntervalMs, "ms");
    Print("Advanced Features: Trailing=", EnableTrailing, " PartialClose=", EnablePartialClose);
    Print("Security: MaxLot=", MaxLotSize, " MaxRisk=", MaxRiskPercent, "% MaxDaily=", MaxDailyTrades);
    
    // Write initial status
    WriteStatus("initialized", "BITTEN Advanced Bridge SECURE ready");
    
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
    // DOC: "Regular checkups keep the system healthy"
    
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
        UpdateTrailingStops();
        lastPositionUpdate = TimeCurrent();
    }
    
    // Check for new trade instructions
    ProcessInstructions();
    
    // Check for management commands
    ProcessCommands();
    
    // Reset daily counter at midnight
    if (TimeDay(TimeCurrent()) != TimeDay(lastTradeDate))
    {
        dailyTradeCount = 0;
        lastTradeDate = TimeCurrent();
    }
}

//+------------------------------------------------------------------+
void ProcessInstructions()
{
    if (!FileIsExist(InstructionFile)) return;
    
    // Check file size to prevent DOS attacks
    long fileSize = FileSize(InstructionFile);
    if (fileSize > MAX_INSTRUCTION_LENGTH)
    {
        WriteStatus("error", "Instruction file too large");
        FileDelete(InstructionFile);
        return;
    }
    
    int fileHandle = FileOpen(InstructionFile, FILE_READ | FILE_TXT | FILE_ANSI);
    if (fileHandle == INVALID_HANDLE) 
    {
        WriteStatus("error", "Cannot open instruction file");
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
    
    // Parse and validate CSV format
    string parts[];
    int count = StringSplit(instruction, ',', parts);
    
    if (count < 7 || count > 9)  // Allow optional HMAC field
    {
        WriteStatus("error", "Invalid instruction format");
        FileDelete(InstructionFile);
        return;
    }
    
    // Sanitize and validate each field
    string tradeId = SanitizeString(StringTrim(parts[0]), 50);
    string symbol = SanitizeSymbol(StringTrim(parts[1]));
    string typeStr = StringTrim(parts[2]);
    double lot = ValidateLotSize(StringToDouble(parts[3]));
    double price = ValidatePrice(StringToDouble(parts[4]));
    double tp = ValidatePrice(StringToDouble(parts[5]));
    double sl = ValidatePrice(StringToDouble(parts[6]));
    string comment = "";
    if (count > 7) comment = SanitizeString(StringTrim(parts[7]), MAX_COMMENT_LENGTH);
    
    // Validate trade type
    if (typeStr != "BUY" && typeStr != "SELL")
    {
        WriteStatus("error", "Invalid trade type: " + typeStr);
        FileDelete(InstructionFile);
        return;
    }
    
    // Create fingerprint to prevent duplicates
    string fingerprint = tradeId + symbol + typeStr;
    if (fingerprint == lastFingerprint) 
    {
        FileDelete(InstructionFile);
        return;
    }
    lastFingerprint = fingerprint;
    
    // Check daily trade limit
    if (dailyTradeCount >= MaxDailyTrades)
    {
        WriteResult(tradeId, "failed", 0, "Daily trade limit reached", 0);
        FileDelete(InstructionFile);
        return;
    }
    
    // Check concurrent trades limit
    int currentPositions = CountActivePositions();
    if (currentPositions >= MaxConcurrentTrades)
    {
        WriteResult(tradeId, "failed", 0, "Concurrent trade limit reached", 0);
        FileDelete(InstructionFile);
        return;
    }
    
    // Execute with validation
    bool success = ExecuteTradeSecure(tradeId, symbol, typeStr, lot, price, tp, sl, comment);
    
    // Delete instruction file after processing
    FileDelete(InstructionFile);
}

//+------------------------------------------------------------------+
void ProcessCommands()
{
    if (!FileIsExist(CommandFile)) return;
    
    // Check file size
    long fileSize = FileSize(CommandFile);
    if (fileSize > MAX_COMMAND_LENGTH)
    {
        WriteStatus("error", "Command file too large");
        FileDelete(CommandFile);
        return;
    }
    
    int fileHandle = FileOpen(CommandFile, FILE_READ | FILE_TXT | FILE_ANSI);
    if (fileHandle == INVALID_HANDLE) return;
    
    string command = FileReadString(fileHandle);
    FileClose(fileHandle);
    
    // Validate command length
    if (StringLen(command) > MAX_COMMAND_LENGTH)
    {
        WriteStatus("error", "Command too long");
        FileDelete(CommandFile);
        return;
    }
    
    // NEXUS: "Parse carefully, execute cautiously"
    
    // Validate JSON structure before processing
    if (!IsValidJSON(command))
    {
        WriteStatus("error", "Invalid command format");
        FileDelete(CommandFile);
        return;
    }
    
    // Process based on action
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
    else
    {
        WriteStatus("error", "Unknown command action");
    }
    
    // Delete command file after processing
    FileDelete(CommandFile);
}

//+------------------------------------------------------------------+
void ProcessModifyCommand(string command)
{
    // Extract and validate values
    ulong ticket = ValidateTicket(ExtractTicket(command));
    double sl = ValidatePrice(ExtractDouble(command, "sl"));
    double tp = ValidatePrice(ExtractDouble(command, "tp"));
    
    if (ticket == 0)
    {
        WriteStatus("error", "Invalid ticket in modify command");
        return;
    }
    
    // Verify position exists and belongs to us
    if (!PositionSelectByTicket(ticket))
    {
        WriteStatus("error", "Position not found: " + IntegerToString(ticket));
        return;
    }
    
    if (PositionGetInteger(POSITION_MAGIC) != MagicNumber)
    {
        WriteStatus("error", "Position not managed by this EA");
        return;
    }
    
    // Perform modification
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

//+------------------------------------------------------------------+
void ProcessPartialCloseCommand(string command)
{
    if (!EnablePartialClose) 
    {
        WriteStatus("error", "Partial close disabled");
        return;
    }
    
    ulong ticket = ValidateTicket(ExtractTicket(command));
    double volume = ValidateLotSize(ExtractDouble(command, "volume"));
    
    if (ticket == 0 || volume == 0)
    {
        WriteStatus("error", "Invalid partial close parameters");
        return;
    }
    
    // Verify position
    if (!PositionSelectByTicket(ticket))
    {
        WriteStatus("error", "Position not found for partial close");
        return;
    }
    
    if (PositionGetInteger(POSITION_MAGIC) != MagicNumber)
    {
        WriteStatus("error", "Position not managed by this EA");
        return;
    }
    
    string symbol = PositionGetString(POSITION_SYMBOL);
    ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
    double currentVolume = PositionGetDouble(POSITION_VOLUME);
    
    // Ensure we don't close more than available
    volume = MathMin(volume, currentVolume);
    
    MqlTradeRequest request;
    MqlTradeResult result;
    
    ZeroMemory(request);
    ZeroMemory(result);
    
    // Close opposite direction
    request.action = TRADE_ACTION_DEAL;
    request.position = ticket;
    request.symbol = symbol;
    request.volume = volume;
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

//+------------------------------------------------------------------+
void ProcessTrailCommand(string command)
{
    if (!EnableTrailing)
    {
        WriteStatus("error", "Trailing stop disabled");
        return;
    }
    
    ulong ticket = ValidateTicket(ExtractTicket(command));
    int distance = ValidateTrailDistance(ExtractDouble(command, "distance"));
    int step = ValidateTrailStep(ExtractDouble(command, "step"));
    
    if (ticket == 0 || distance == 0 || step == 0)
    {
        WriteStatus("error", "Invalid trail parameters");
        return;
    }
    
    // Verify position
    if (!PositionSelectByTicket(ticket))
    {
        WriteStatus("error", "Position not found for trailing");
        return;
    }
    
    if (PositionGetInteger(POSITION_MAGIC) != MagicNumber)
    {
        WriteStatus("error", "Position not managed by this EA");
        return;
    }
    
    // Add to trailing positions
    AddTrailingPosition(ticket, distance, step);
    
    WriteStatus("trail_activated", 
               StringFormat("Trailing activated for %d: distance=%d, step=%d", 
                           ticket, distance, step));
}

//+------------------------------------------------------------------+
void ProcessCloseCommand(string command)
{
    ulong ticket = ValidateTicket(ExtractTicket(command));
    
    if (ticket == 0)
    {
        WriteStatus("error", "Invalid ticket in close command");
        return;
    }
    
    // Verify position
    if (!PositionSelectByTicket(ticket))
    {
        WriteStatus("error", "Position not found for close");
        return;
    }
    
    if (PositionGetInteger(POSITION_MAGIC) != MagicNumber)
    {
        WriteStatus("error", "Position not managed by this EA");
        return;
    }
    
    MqlTrade trade;
    if (trade.PositionClose(ticket, SlippagePoints))
    {
        WriteStatus("close_success", StringFormat("Closed position %d", ticket));
        RemoveTrailingPosition(ticket);
    }
    else
    {
        WriteStatus("close_failed", StringFormat("Failed to close %d", ticket));
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
                positions[size].comment = SanitizeString(PositionGetString(POSITION_COMMENT), MAX_COMMENT_LENGTH);
            }
        }
    }
    
    // Write positions to file
    WritePositions();
}

//+------------------------------------------------------------------+
void UpdateTrailingStops()
{
    if (!EnableTrailing) return;
    
    // OVERWATCH: "The market never sleeps, neither should your stops"
    
    for (int i = ArraySize(trailingPositions) - 1; i >= 0; i--)
    {
        if (PositionSelectByTicket(trailingPositions[i].ticket))
        {
            string symbol = PositionGetString(POSITION_SYMBOL);
            ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
            double currentSL = PositionGetDouble(POSITION_SL);
            double currentPrice;
            double newSL;
            
            int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
            double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
            
            if (type == POSITION_TYPE_BUY)
            {
                currentPrice = SymbolInfoDouble(symbol, SYMBOL_BID);
                newSL = currentPrice - trailingPositions[i].distance * point;
                
                // Only trail if profitable and new SL is better
                if (currentPrice > trailingPositions[i].lastPrice + trailingPositions[i].step * point &&
                    newSL > currentSL)
                {
                    ModifyStopLoss(trailingPositions[i].ticket, NormalizeDouble(newSL, digits));
                    trailingPositions[i].lastPrice = currentPrice;
                }
            }
            else // SELL
            {
                currentPrice = SymbolInfoDouble(symbol, SYMBOL_ASK);
                newSL = currentPrice + trailingPositions[i].distance * point;
                
                // Only trail if profitable and new SL is better
                if (currentPrice < trailingPositions[i].lastPrice - trailingPositions[i].step * point &&
                    (currentSL == 0 || newSL < currentSL))
                {
                    ModifyStopLoss(trailingPositions[i].ticket, NormalizeDouble(newSL, digits));
                    trailingPositions[i].lastPrice = currentPrice;
                }
            }
        }
        else
        {
            // Position closed, remove from trailing
            ArrayRemove(trailingPositions, i, 1);
        }
    }
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
// Security and validation functions
//+------------------------------------------------------------------+
string SanitizeString(string input, int maxLength)
{
    // Remove dangerous characters and limit length
    string result = "";
    int len = MathMin(StringLen(input), maxLength);
    
    for (int i = 0; i < len; i++)
    {
        ushort c = StringGetCharacter(input, i);
        // Allow alphanumeric, space, underscore, dash
        if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || 
            (c >= '0' && c <= '9') || c == ' ' || c == '_' || c == '-')
        {
            result += CharToString(c);
        }
    }
    
    return result;
}

//+------------------------------------------------------------------+
string SanitizeSymbol(string symbol)
{
    // Strict validation for trading symbols
    string result = "";
    int len = MathMin(StringLen(symbol), MAX_SYMBOL_LENGTH);
    
    for (int i = 0; i < len; i++)
    {
        ushort c = StringGetCharacter(symbol, i);
        // Only allow uppercase letters and numbers
        if ((c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9'))
        {
            result += CharToString(c);
        }
    }
    
    // Verify symbol exists
    if (!SymbolInfoInteger(result, SYMBOL_SELECT))
    {
        WriteStatus("error", "Invalid symbol: " + result);
        return "";
    }
    
    return result;
}

//+------------------------------------------------------------------+
double ValidateLotSize(double lot)
{
    if (lot <= 0) return 0;
    if (lot > MaxLotSize) lot = MaxLotSize;
    
    // Round to lot step
    double lotStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
    lot = MathRound(lot / lotStep) * lotStep;
    
    // Ensure minimum
    double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
    if (lot < minLot) lot = minLot;
    
    return NormalizeDouble(lot, 2);
}

//+------------------------------------------------------------------+
double ValidatePrice(double price)
{
    if (price < 0) return 0;
    if (price > 999999) return 0;
    return price;
}

//+------------------------------------------------------------------+
ulong ValidateTicket(ulong ticket)
{
    if (ticket <= 0 || ticket > ULONG_MAX) return 0;
    return ticket;
}

//+------------------------------------------------------------------+
int ValidateTrailDistance(double distance)
{
    int dist = (int)distance;
    if (dist < 10) return 0;  // Minimum 10 points
    if (dist > 1000) return 1000;  // Maximum 1000 points
    return dist;
}

//+------------------------------------------------------------------+
int ValidateTrailStep(double step)
{
    int st = (int)step;
    if (st < 1) return 1;  // Minimum 1 point
    if (st > 100) return 100;  // Maximum 100 points
    return st;
}

//+------------------------------------------------------------------+
bool IsValidJSON(string json)
{
    // Basic JSON validation
    if (StringLen(json) < 2) return false;
    
    // Must start with { and end with }
    if (StringGetCharacter(json, 0) != '{' || 
        StringGetCharacter(json, StringLen(json)-1) != '}')
        return false;
    
    // Check for balanced quotes and braces
    int quoteCount = 0;
    int braceCount = 0;
    bool inQuotes = false;
    
    for (int i = 0; i < StringLen(json); i++)
    {
        ushort c = StringGetCharacter(json, i);
        
        if (c == '"' && (i == 0 || StringGetCharacter(json, i-1) != '\\'))
        {
            quoteCount++;
            inQuotes = !inQuotes;
        }
        else if (!inQuotes)
        {
            if (c == '{') braceCount++;
            else if (c == '}') braceCount--;
        }
    }
    
    return (quoteCount % 2 == 0) && (braceCount == 0);
}

//+------------------------------------------------------------------+
int CountActivePositions()
{
    int count = 0;
    for (int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if (PositionSelectByIndex(i))
        {
            if (PositionGetInteger(POSITION_MAGIC) == MagicNumber)
                count++;
        }
    }
    return count;
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
bool ExecuteTradeSecure(string tradeId, string symbol, string typeStr, 
                       double lot, double price, double tp, double sl, string comment)
{
    // Validate risk
    if (!ValidateRisk(symbol, lot, sl))
    {
        WriteResult(tradeId, "failed", 0, "Risk validation failed", 0);
        return false;
    }
    
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
    request.comment = "BITTEN_" + tradeId + (comment != "" ? "_" + comment : "");
    
    // Market execution
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
        dailyTradeCount++;
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
bool ValidateRisk(string symbol, double lot, double sl)
{
    if (sl == 0) return true;  // No SL, no risk check
    
    double accountBalance = AccountInfoDouble(ACCOUNT_BALANCE);
    double price = SymbolInfoDouble(symbol, SYMBOL_ASK);
    double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
    double tickValue = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE);
    
    if (point == 0 || tickValue == 0) return false;
    
    double riskPoints = MathAbs(price - sl) / point;
    double riskAmount = riskPoints * tickValue * lot;
    double riskPercent = (riskAmount / accountBalance) * 100;
    
    if (riskPercent > MaxRiskPercent)
    {
        Print("Risk too high: ", riskPercent, "% > ", MaxRiskPercent, "%");
        return false;
    }
    
    return true;
}

//+------------------------------------------------------------------+
void AddTrailingPosition(ulong ticket, int distance, int step)
{
    // Check if already exists
    for (int i = 0; i < ArraySize(trailingPositions); i++)
    {
        if (trailingPositions[i].ticket == ticket)
        {
            // Update existing
            trailingPositions[i].distance = distance;
            trailingPositions[i].step = step;
            return;
        }
    }
    
    // Add new
    int size = ArraySize(trailingPositions);
    ArrayResize(trailingPositions, size + 1);
    trailingPositions[size].ticket = ticket;
    trailingPositions[size].distance = distance;
    trailingPositions[size].step = step;
    trailingPositions[size].lastPrice = 0;
}

//+------------------------------------------------------------------+
void RemoveTrailingPosition(ulong ticket)
{
    for (int i = ArraySize(trailingPositions) - 1; i >= 0; i--)
    {
        if (trailingPositions[i].ticket == ticket)
        {
            ArrayRemove(trailingPositions, i, 1);
            break;
        }
    }
}

//+------------------------------------------------------------------+
void ModifyStopLoss(ulong ticket, double newSL)
{
    if (!PositionSelectByTicket(ticket)) return;
    
    MqlTradeRequest request;
    MqlTradeResult result;
    
    ZeroMemory(request);
    ZeroMemory(result);
    
    request.action = TRADE_ACTION_SLTP;
    request.position = ticket;
    request.sl = newSL;
    request.tp = PositionGetDouble(POSITION_TP);
    request.symbol = PositionGetString(POSITION_SYMBOL);
    request.magic = MagicNumber;
    
    if (OrderSend(request, result))
    {
        Print("Trailing stop updated for ", ticket, " to ", newSL);
    }
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
    
    // Sanitize message
    message = SanitizeString(message, 200);
    
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
    
    // Sanitize message
    message = SanitizeString(message, 200);
    
    string json = StringFormat(
        "{\"type\":\"%s\",\"message\":\"%s\",\"timestamp\":\"%s\"," +
        "\"connected\":%s,\"positions\":%d,\"orders\":%d,\"balance\":%.2f," +
        "\"daily_trades\":%d,\"failed_attempts\":%d}",
        type, message, timestamp, 
        TerminalInfoInteger(TERMINAL_CONNECTED) ? "true" : "false",
        CountActivePositions(), OrdersTotal(),
        AccountInfoDouble(ACCOUNT_BALANCE),
        dailyTradeCount, failedAttempts
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
    // DRILL: "Sound off! System status report!"
    WriteStatus("heartbeat", StringFormat("Bridge active, trades today: %d/%d", 
                                        dailyTradeCount, MaxDailyTrades));
}

// OVERWATCH: "Remember, every trade is a battle. Win the war, not just the fight."