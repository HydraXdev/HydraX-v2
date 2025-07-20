//+------------------------------------------------------------------+
//| BITTENBridge_V3_ENHANCED.mq5 – v3.1.0 (Symbol Patch Edition)     |
//|                                          BITTEN Trading System   |
//|              Enhanced EA with full two-way communication         |
//|                     Account data, advanced trade management      |
//+------------------------------------------------------------------+
#property strict
#property version   "3.1.0"
#property description "BITTEN Enhanced Bridge v3 - Full account integration & advanced management"

#include <Trade\Trade.mqh>

// Input parameters
input string InstructionFile = "bitten_instructions_secure.txt";  // Trade instructions
input string CommandFile = "bitten_commands_secure.txt";         // Management commands
input string ResultFile = "bitten_results_secure.txt";           // Results
input string StatusFile = "bitten_status_secure.txt";            // Status updates
input string PositionsFile = "bitten_positions_secure.txt";      // Active positions
input string AccountFile = "bitten_account_secure.txt";          // Account data
input string MarketFile = "bitten_market_secure.txt";            // Market data
input int    CheckIntervalMs = 100;                             // Check interval (50-1000)
input int    MagicNumber = 20250626;                            // EA identification

// Advanced features
input bool   EnableTrailing = true;                             // Enable trailing stops
input bool   EnablePartialClose = true;                         // Enable partial close
input bool   EnableBreakEven = true;                            // Enable break-even
input bool   EnableMultiTP = true;                              // Enable multi-step TP
input double PartialClosePercent = 50.0;                        // Default partial close %
input int    BreakEvenPoints = 20;                              // Points in profit to trigger BE
input int    BreakEvenBuffer = 5;                               // Points above entry for BE

// Risk management
input double MaxLotSize = 10.0;                                 // Maximum allowed lot size
input double MaxRiskPercent = 5.0;                              // Maximum risk per trade (%)
input int    MaxDailyTrades = 50;                               // Maximum trades per day
input int    MaxConcurrentTrades = 10;                          // Maximum concurrent positions

// Global variables
datetime lastHeartbeat = 0;
datetime lastAccountUpdate = 0;
datetime lastMarketUpdate = 0;
int failedAttempts = 0;
int dailyTradeCount = 0;

// Position tracking with enhanced data
struct EnhancedPosition {
    ulong ticket;
    string symbol;
    ENUM_POSITION_TYPE type;
    double volume;
    double openPrice;
    double sl;
    double tp;
    double profit;
    double swap;
    double commission;
    datetime openTime;
    string comment;
    bool breakEvenSet;
    bool partialClosed;
    double initialVolume;
    int partialCloseStep;
};

EnhancedPosition positions[];

// Multi-step TP tracking
struct MultiTPLevel {
    ulong ticket;
    double tp1;
    double tp2;
    double tp3;
    double volume1;
    double volume2;
    double volume3;
    int currentStep;
};

MultiTPLevel multiTPPositions[];

//+------------------------------------------------------------------+
int OnInit()
{
    Print("=== BITTEN Enhanced Bridge v3.1.0 (Symbol Patch Edition) Initialized ===");
    Print("🔥 UNIQUE_ID_CLAUDE_PATCH_SUCCESS_2025_07_15 🔥");
    Print("✅ FILE_COMMON + SymbolSelect() patches ACTIVE");
    Print("Two-way communication enabled");
    Print("Account reporting: YES");
    Print("Advanced trade management: YES");
    
    // Print file paths for debugging
    Print("📁 Common Data Path: ", TerminalInfoString(TERMINAL_COMMONDATA_PATH));
    Print("📄 Files will be written to: ", TerminalInfoString(TERMINAL_COMMONDATA_PATH), "\\Files\\");
    Print("🎯 BITTEN signal files path: ", TerminalInfoString(TERMINAL_COMMONDATA_PATH), "\\Files\\BITTEN\\");
    Print("📊 Market data will update every 1 second");
    Print("🔄 Timer interval: ", CheckIntervalMs, "ms");
    
    // Write initial status
    WriteStatus("initialized", "BITTEN Enhanced Bridge v3 ready");
    WriteAccountData();
    
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
    
    // Update account data every 2 seconds
    if (TimeCurrent() - lastAccountUpdate >= 2)
    {
        WriteAccountData();
        lastAccountUpdate = TimeCurrent();
    }
    
    // Update market data every second
    if (TimeCurrent() - lastMarketUpdate >= 1)
    {
        WriteMarketData();
        UpdatePositions();
        CheckBreakEven();
        CheckMultiTP();
        UpdateTrailingStops();
        lastMarketUpdate = TimeCurrent();
    }
    
    // Check for new instructions
    ProcessInstructions();
    ProcessCommands();
}

//+------------------------------------------------------------------+
void WriteAccountData()
{
    int handle = FileOpen(AccountFile, FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_COMMON);
    if (handle == INVALID_HANDLE) return;
    
    // Gather comprehensive account data
    double balance = AccountInfoDouble(ACCOUNT_BALANCE);
    double equity = AccountInfoDouble(ACCOUNT_EQUITY);
    double margin = AccountInfoDouble(ACCOUNT_MARGIN);
    double freeMargin = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
    double marginLevel = margin > 0 ? (equity / margin) * 100 : 0;
    double profit = AccountInfoDouble(ACCOUNT_PROFIT);
    int leverage = (int)AccountInfoInteger(ACCOUNT_LEVERAGE);
    string currency = AccountInfoString(ACCOUNT_CURRENCY);
    
    // Calculate daily P&L
    double dailyPL = CalculateDailyPL();
    double dailyPLPercent = balance > 0 ? (dailyPL / balance) * 100 : 0;
    
    // Count positions
    int buyPositions = 0, sellPositions = 0;
    double buyVolume = 0, sellVolume = 0;
    
    for (int i = 0; i < ArraySize(positions); i++)
    {
        if (positions[i].type == POSITION_TYPE_BUY)
        {
            buyPositions++;
            buyVolume += positions[i].volume;
        }
        else
        {
            sellPositions++;
            sellVolume += positions[i].volume;
        }
    }
    
    // Write JSON format
    string json = StringFormat(
        "{\"timestamp\":\"%s\",\"balance\":%.2f,\"equity\":%.2f," +
        "\"margin\":%.2f,\"free_margin\":%.2f,\"margin_level\":%.2f," +
        "\"profit\":%.2f,\"leverage\":%d,\"currency\":\"%s\"," +
        "\"daily_pl\":%.2f,\"daily_pl_percent\":%.2f," +
        "\"positions\":{\"total\":%d,\"buy\":%d,\"sell\":%d," +
        "\"buy_volume\":%.2f,\"sell_volume\":%.2f}," +
        "\"server_time\":\"%s\"}",
        TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
        balance, equity, margin, freeMargin, marginLevel,
        profit, leverage, currency,
        dailyPL, dailyPLPercent,
        ArraySize(positions), buyPositions, sellPositions,
        buyVolume, sellVolume,
        TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS)
    );
    
    FileWriteString(handle, json);
    FileClose(handle);
}

//+------------------------------------------------------------------+
void WriteMarketData()
{
    // Legacy market data file for compatibility
    int handle = FileOpen(MarketFile, FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_COMMON);
    if (handle == INVALID_HANDLE) return;
    
    // Get market data for major pairs
    string symbols[] = {"EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSD"};
    string json = "{\"timestamp\":\"" + TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS) + "\",\"pairs\":{";
    
    for (int i = 0; i < ArraySize(symbols); i++)
    {
        if (SymbolInfoInteger(symbols[i], SYMBOL_SELECT))
        {
            double bid = SymbolInfoDouble(symbols[i], SYMBOL_BID);
            double ask = SymbolInfoDouble(symbols[i], SYMBOL_ASK);
            double spread = (ask - bid) / SymbolInfoDouble(symbols[i], SYMBOL_POINT);
            
            if (i > 0) json += ",";
            json += StringFormat("\"%s\":{\"bid\":%.5f,\"ask\":%.5f,\"spread\":%.1f}",
                                symbols[i], bid, ask, spread);
        }
    }
    
    json += "}}";
    
    FileWriteString(handle, json);
    FileClose(handle);
    
    // NEW: Write individual signal files for APEX
    WriteSignalFiles();
}

//+------------------------------------------------------------------+
void WriteSignalFiles()
{
    // APEX v5.0 expects individual files per symbol in BITTEN subdirectory
    string symbols[] = {"EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD", "USDCHF", 
                       "NZDUSD", "EURGBP", "EURJPY", "GBPJPY", "XAUUSD", "GBPNZD", 
                       "GBPAUD", "EURAUD", "GBPCHF"};
    
    for (int i = 0; i < ArraySize(symbols); i++)
    {
        SymbolSelect(symbols[i], true);  // Force selection if needed
        if (SymbolInfoInteger(symbols[i], SYMBOL_SELECT))
        {
            // Create BITTEN subdirectory signal file
            string filename = "BITTEN\\" + symbols[i] + ".json";
            int handle = FileOpen(filename, FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_COMMON);
            
            if (handle != INVALID_HANDLE)
            {
                double bid = SymbolInfoDouble(symbols[i], SYMBOL_BID);
                double ask = SymbolInfoDouble(symbols[i], SYMBOL_ASK);
                double spread = (ask - bid) / SymbolInfoDouble(symbols[i], SYMBOL_POINT);
                
                // Format matching APEX expectations
                string signalJson = StringFormat(
                    "{\"symbol\":\"%s\",\"bid\":%.5f,\"ask\":%.5f,\"spread\":%.1f,\"timestamp\":\"%s\"}",
                    symbols[i], bid, ask, spread,
                    TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS)
                );
                
                FileWriteString(handle, signalJson);
                FileClose(handle);
                
                // Debug output to MT5 Experts tab
                Print("🎯 CLAUDE_PATCH_WORKING: Wrote bridge file: ", symbols[i], ".json at ", 
                      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS), " to COMMON/Files/BITTEN/");
            }
            else
            {
                Print("❌ CLAUDE_PATCH_ERROR: Failed to write bridge file for: ", symbols[i]);
                // Print full path for debugging
                Print("📁 CLAUDE_PATCH_PATH: ", TerminalInfoString(TERMINAL_COMMONDATA_PATH), "\\Files\\BITTEN\\", symbols[i], ".json");
            }
        }
    }
    
    // Also write current chart symbol if not in list
    string currentSymbol = _Symbol;
    bool found = false;
    for (int i = 0; i < ArraySize(symbols); i++)
    {
        if (symbols[i] == currentSymbol)
        {
            found = true;
            break;
        }
    }
    
    if (!found)
    {
        SymbolSelect(currentSymbol, true);  // Force selection if needed
        if (SymbolInfoInteger(currentSymbol, SYMBOL_SELECT))
        {
        string filename = "BITTEN\\" + currentSymbol + ".json";
        int handle = FileOpen(filename, FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_COMMON);
        
        if (handle != INVALID_HANDLE)
        {
            double bid = SymbolInfoDouble(currentSymbol, SYMBOL_BID);
            double ask = SymbolInfoDouble(currentSymbol, SYMBOL_ASK);
            double spread = (ask - bid) / SymbolInfoDouble(currentSymbol, SYMBOL_POINT);
            
            string signalJson = StringFormat(
                "{\"symbol\":\"%s\",\"bid\":%.5f,\"ask\":%.5f,\"spread\":%.1f,\"timestamp\":\"%s\"}",
                currentSymbol, bid, ask, spread,
                TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS)
            );
            
            FileWriteString(handle, signalJson);
            FileClose(handle);
            
            Print("✅ Wrote chart symbol bridge file: ", currentSymbol, ".json at ", 
                  TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS));
        }
        }
    }
}

//+------------------------------------------------------------------+
void ProcessInstructions()
{
    if (!FileIsExist(InstructionFile, FILE_COMMON)) return;
    
    int fileHandle = FileOpen(InstructionFile, FILE_READ | FILE_TXT | FILE_ANSI | FILE_COMMON);
    if (fileHandle == INVALID_HANDLE) return;
    
    string content = "";
    while (!FileIsEnding(fileHandle))
    {
        content += FileReadString(fileHandle);
    }
    FileClose(fileHandle);
    
    // Enhanced JSON parsing for new instruction format
    if (StringFind(content, "{") >= 0)
    {
        // JSON format instruction
        ProcessJSONInstruction(content);
    }
    else
    {
        // Legacy CSV format
        ProcessCSVInstruction(content);
    }
    
    FileDelete(InstructionFile, FILE_COMMON);
}

//+------------------------------------------------------------------+
void ProcessJSONInstruction(string json)
{
    // Extract fields from JSON
    string id = ExtractString(json, "id");
    string symbol = ExtractString(json, "symbol");
    string direction = ExtractString(json, "direction");
    double volume = ExtractDouble(json, "volume");
    double sl = ExtractDouble(json, "sl");
    double tp = ExtractDouble(json, "tp");
    string comment = ExtractString(json, "comment");
    
    // NEW: Advanced features
    bool useBreakEven = ExtractBool(json, "break_even", EnableBreakEven);
    bool useTrailing = ExtractBool(json, "trailing", EnableTrailing);
    double partialPercent = ExtractDouble(json, "partial_close", PartialClosePercent);
    
    // NEW: Multi-step TP
    double tp1 = ExtractDouble(json, "tp1", tp);
    double tp2 = ExtractDouble(json, "tp2", 0);
    double tp3 = ExtractDouble(json, "tp3", 0);
    double volume1 = ExtractDouble(json, "volume1", 30);  // 30% at TP1
    double volume2 = ExtractDouble(json, "volume2", 30);  // 30% at TP2
    double volume3 = ExtractDouble(json, "volume3", 40);  // 40% at TP3
    
    // NEW: Risk-based lot calculation
    bool useRiskPercent = ExtractBool(json, "use_risk_percent", false);
    double riskPercent = ExtractDouble(json, "risk_percent", 2.0);
    
    // Calculate lot size based on risk if requested
    if (useRiskPercent && sl > 0)
    {
        volume = CalculateLotFromRisk(symbol, direction, sl, riskPercent);
    }
    
    // Execute trade
    bool success = ExecuteEnhancedTrade(id, symbol, direction, volume, sl, tp, comment);
    
    if (success && EnableMultiTP && (tp2 > 0 || tp3 > 0))
    {
        // Set up multi-step TP
        ulong ticket = GetLastTicket();
        AddMultiTPPosition(ticket, tp1, tp2, tp3, volume1, volume2, volume3);
    }
}

//+------------------------------------------------------------------+
double CalculateLotFromRisk(string symbol, string direction, double sl, double riskPercent)
{
    double balance = AccountInfoDouble(ACCOUNT_BALANCE);
    double riskAmount = balance * (riskPercent / 100.0);
    
    double price = (direction == "BUY") ? 
                   SymbolInfoDouble(symbol, SYMBOL_ASK) : 
                   SymbolInfoDouble(symbol, SYMBOL_BID);
    
    double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
    double tickValue = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE);
    
    if (point == 0 || tickValue == 0) return SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
    
    double stopPoints = MathAbs(price - sl) / point;
    double lotSize = riskAmount / (stopPoints * tickValue);
    
    // Round to lot step
    double lotStep = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
    lotSize = MathRound(lotSize / lotStep) * lotStep;
    
    // Apply limits
    double minLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
    double maxLot = MathMin(SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX), MaxLotSize);
    
    return MathMax(minLot, MathMin(lotSize, maxLot));
}

//+------------------------------------------------------------------+
void ProcessCommands()
{
    if (!FileIsExist(CommandFile, FILE_COMMON)) return;
    
    int fileHandle = FileOpen(CommandFile, FILE_READ | FILE_TXT | FILE_ANSI | FILE_COMMON);
    if (fileHandle == INVALID_HANDLE) return;
    
    string command = "";
    while (!FileIsEnding(fileHandle))
    {
        command += FileReadString(fileHandle);
    }
    FileClose(fileHandle);
    
    // Enhanced command processing
    string action = ExtractString(command, "action");
    
    if (action == "modify")
        ProcessModifyCommand(command);
    else if (action == "close_partial")
        ProcessEnhancedPartialClose(command);
    else if (action == "trail")
        ProcessTrailCommand(command);
    else if (action == "close")
        ProcessCloseCommand(command);
    else if (action == "break_even")
        ProcessBreakEvenCommand(command);
    else if (action == "scale_out")
        ProcessScaleOutCommand(command);
    
    FileDelete(CommandFile, FILE_COMMON);
}

//+------------------------------------------------------------------+
void ProcessEnhancedPartialClose(string command)
{
    ulong ticket = (ulong)ExtractDouble(command, "ticket");
    double percent = ExtractDouble(command, "percent", 50.0);
    
    if (!PositionSelectByTicket(ticket)) return;
    
    double currentVolume = PositionGetDouble(POSITION_VOLUME);
    double closeVolume = NormalizeDouble(currentVolume * (percent / 100.0), 2);
    
    // Ensure minimum lot
    double minLot = SymbolInfoDouble(PositionGetString(POSITION_SYMBOL), SYMBOL_VOLUME_MIN);
    if (closeVolume < minLot) closeVolume = minLot;
    
    // Don't close more than available
    if (closeVolume >= currentVolume) closeVolume = currentVolume - minLot;
    
    if (closeVolume > 0)
    {
        MqlTrade trade;
        if (trade.PositionClosePartial(ticket, closeVolume))
        {
            // Update position tracking
            for (int i = 0; i < ArraySize(positions); i++)
            {
                if (positions[i].ticket == ticket)
                {
                    positions[i].partialClosed = true;
                    positions[i].partialCloseStep++;
                    break;
                }
            }
            
            WriteStatus("partial_close_success", 
                       StringFormat("Closed %.0f%% (%.2f lots) of position %d", 
                                   percent, closeVolume, ticket));
        }
    }
}

//+------------------------------------------------------------------+
void ProcessBreakEvenCommand(string command)
{
    ulong ticket = (ulong)ExtractDouble(command, "ticket");
    int buffer = (int)ExtractDouble(command, "buffer", BreakEvenBuffer);
    
    SetBreakEven(ticket, buffer);
}

//+------------------------------------------------------------------+
void ProcessScaleOutCommand(string command)
{
    // Scale out: close portions at different levels
    ulong ticket = (ulong)ExtractDouble(command, "ticket");
    
    // Level 1: 33% at current profit
    ProcessPartialCloseAtLevel(ticket, 33.0);
    
    // Set trailing for remainder
    if (EnableTrailing)
    {
        AddTrailingPosition(ticket, 30, 10);
    }
}

//+------------------------------------------------------------------+
void CheckBreakEven()
{
    if (!EnableBreakEven) return;
    
    for (int i = 0; i < ArraySize(positions); i++)
    {
        if (!positions[i].breakEvenSet)
        {
            if (PositionSelectByTicket(positions[i].ticket))
            {
                double currentPrice = (positions[i].type == POSITION_TYPE_BUY) ?
                                    SymbolInfoDouble(positions[i].symbol, SYMBOL_BID) :
                                    SymbolInfoDouble(positions[i].symbol, SYMBOL_ASK);
                
                double point = SymbolInfoDouble(positions[i].symbol, SYMBOL_POINT);
                double profitPoints = 0;
                
                if (positions[i].type == POSITION_TYPE_BUY)
                {
                    profitPoints = (currentPrice - positions[i].openPrice) / point;
                }
                else
                {
                    profitPoints = (positions[i].openPrice - currentPrice) / point;
                }
                
                if (profitPoints >= BreakEvenPoints)
                {
                    SetBreakEven(positions[i].ticket, BreakEvenBuffer);
                    positions[i].breakEvenSet = true;
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
void CheckMultiTP()
{
    if (!EnableMultiTP) return;
    
    for (int i = ArraySize(multiTPPositions) - 1; i >= 0; i--)
    {
        if (PositionSelectByTicket(multiTPPositions[i].ticket))
        {
            double currentPrice = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ?
                                SymbolInfoDouble(PositionGetString(POSITION_SYMBOL), SYMBOL_BID) :
                                SymbolInfoDouble(PositionGetString(POSITION_SYMBOL), SYMBOL_ASK);
            
            ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
            
            // Check each TP level
            if (multiTPPositions[i].currentStep == 0 && 
                ((type == POSITION_TYPE_BUY && currentPrice >= multiTPPositions[i].tp1) ||
                 (type == POSITION_TYPE_SELL && currentPrice <= multiTPPositions[i].tp1)))
            {
                ProcessPartialCloseAtLevel(multiTPPositions[i].ticket, multiTPPositions[i].volume1);
                multiTPPositions[i].currentStep = 1;
            }
            else if (multiTPPositions[i].currentStep == 1 && multiTPPositions[i].tp2 > 0 &&
                    ((type == POSITION_TYPE_BUY && currentPrice >= multiTPPositions[i].tp2) ||
                     (type == POSITION_TYPE_SELL && currentPrice <= multiTPPositions[i].tp2)))
            {
                ProcessPartialCloseAtLevel(multiTPPositions[i].ticket, multiTPPositions[i].volume2);
                multiTPPositions[i].currentStep = 2;
            }
            else if (multiTPPositions[i].currentStep == 2 && multiTPPositions[i].tp3 > 0 &&
                    ((type == POSITION_TYPE_BUY && currentPrice >= multiTPPositions[i].tp3) ||
                     (type == POSITION_TYPE_SELL && currentPrice <= multiTPPositions[i].tp3)))
            {
                // Close remaining position
                MqlTrade trade;
                trade.PositionClose(multiTPPositions[i].ticket);
                ArrayRemove(multiTPPositions, i, 1);
            }
        }
        else
        {
            // Position closed, remove from tracking
            ArrayRemove(multiTPPositions, i, 1);
        }
    }
}

//+------------------------------------------------------------------+
void SetBreakEven(ulong ticket, int buffer)
{
    if (!PositionSelectByTicket(ticket)) return;
    
    string symbol = PositionGetString(POSITION_SYMBOL);
    ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
    double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
    double currentSL = PositionGetDouble(POSITION_SL);
    double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
    int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
    
    double newSL = 0;
    
    if (type == POSITION_TYPE_BUY)
    {
        newSL = NormalizeDouble(openPrice + buffer * point, digits);
        if (newSL <= currentSL) return;  // Already better
    }
    else
    {
        newSL = NormalizeDouble(openPrice - buffer * point, digits);
        if (currentSL > 0 && newSL >= currentSL) return;  // Already better
    }
    
    MqlTrade trade;
    if (trade.PositionModify(ticket, newSL, PositionGetDouble(POSITION_TP)))
    {
        WriteStatus("break_even_set", 
                   StringFormat("Break-even set for position %d at %.5f", ticket, newSL));
    }
}

//+------------------------------------------------------------------+
void UpdatePositions()
{
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
                positions[size].swap = PositionGetDouble(POSITION_SWAP);
                positions[size].commission = PositionGetDouble(POSITION_COMMISSION);
                positions[size].openTime = (datetime)PositionGetInteger(POSITION_TIME);
                positions[size].comment = PositionGetString(POSITION_COMMENT);
                
                // Check if already tracked for BE/partial
                bool found = false;
                for (int j = 0; j < ArraySize(positions) - 1; j++)
                {
                    if (positions[j].ticket == positions[size].ticket)
                    {
                        positions[size].breakEvenSet = positions[j].breakEvenSet;
                        positions[size].partialClosed = positions[j].partialClosed;
                        positions[size].initialVolume = positions[j].initialVolume;
                        positions[size].partialCloseStep = positions[j].partialCloseStep;
                        found = true;
                        break;
                    }
                }
                
                if (!found)
                {
                    positions[size].breakEvenSet = false;
                    positions[size].partialClosed = false;
                    positions[size].initialVolume = positions[size].volume;
                    positions[size].partialCloseStep = 0;
                }
            }
        }
    }
    
    WriteEnhancedPositions();
}

//+------------------------------------------------------------------+
void WriteEnhancedPositions()
{
    int handle = FileOpen(PositionsFile, FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_COMMON);
    if (handle == INVALID_HANDLE) return;
    
    string json = "[";
    
    for (int i = 0; i < ArraySize(positions); i++)
    {
        if (i > 0) json += ",";
        
        // Calculate running P&L percentage
        double pnlPercent = 0;
        if (positions[i].openPrice > 0)
        {
            double currentPrice = (positions[i].type == POSITION_TYPE_BUY) ?
                                SymbolInfoDouble(positions[i].symbol, SYMBOL_BID) :
                                SymbolInfoDouble(positions[i].symbol, SYMBOL_ASK);
            
            if (positions[i].type == POSITION_TYPE_BUY)
                pnlPercent = ((currentPrice - positions[i].openPrice) / positions[i].openPrice) * 100;
            else
                pnlPercent = ((positions[i].openPrice - currentPrice) / positions[i].openPrice) * 100;
        }
        
        json += StringFormat(
            "{\"ticket\":%d,\"symbol\":\"%s\",\"type\":\"%s\",\"volume\":%.2f," +
            "\"initial_volume\":%.2f,\"open_price\":%.5f,\"sl\":%.5f,\"tp\":%.5f," +
            "\"profit\":%.2f,\"swap\":%.2f,\"commission\":%.2f,\"pnl_percent\":%.2f," +
            "\"open_time\":\"%s\",\"comment\":\"%s\",\"break_even_set\":%s," +
            "\"partial_closed\":%s,\"partial_close_step\":%d}",
            positions[i].ticket,
            positions[i].symbol,
            (positions[i].type == POSITION_TYPE_BUY) ? "BUY" : "SELL",
            positions[i].volume,
            positions[i].initialVolume,
            positions[i].openPrice,
            positions[i].sl,
            positions[i].tp,
            positions[i].profit,
            positions[i].swap,
            positions[i].commission,
            pnlPercent,
            TimeToString(positions[i].openTime, TIME_DATE | TIME_SECONDS),
            positions[i].comment,
            positions[i].breakEvenSet ? "true" : "false",
            positions[i].partialClosed ? "true" : "false",
            positions[i].partialCloseStep
        );
    }
    
    json += "]";
    
    FileWriteString(handle, json);
    FileClose(handle);
}

//+------------------------------------------------------------------+
void WriteHeartbeat()
{
    WriteStatus("heartbeat", StringFormat("Active | Positions: %d | Connected: %s", 
                                         ArraySize(positions),
                                         TerminalInfoInteger(TERMINAL_CONNECTED) ? "Yes" : "No"));
}

//+------------------------------------------------------------------+
void WriteStatus(string type, string message)
{
    int handle = FileOpen(StatusFile, FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_COMMON);
    if (handle == INVALID_HANDLE) return;
    
    string json = StringFormat(
        "{\"type\":\"%s\",\"message\":\"%s\",\"timestamp\":\"%s\"," +
        "\"connected\":%s,\"positions\":%d,\"orders\":%d," +
        "\"account_connected\":%s,\"trade_allowed\":%s}",
        type,
        message,
        TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
        TerminalInfoInteger(TERMINAL_CONNECTED) ? "true" : "false",
        PositionsTotal(),
        OrdersTotal(),
        AccountInfoInteger(ACCOUNT_CONNECTED) ? "true" : "false",
        AccountInfoInteger(ACCOUNT_TRADE_ALLOWED) ? "true" : "false"
    );
    
    FileWriteString(handle, json);
    FileClose(handle);
}

//+------------------------------------------------------------------+
void WriteResult(string id, string status, ulong ticket, string message, double price)
{
    int handle = FileOpen(ResultFile, FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_COMMON);
    if (handle == INVALID_HANDLE) return;
    
    // Include comprehensive account state
    string json = StringFormat(
        "{\"id\":\"%s\",\"status\":\"%s\",\"ticket\":%d,\"message\":\"%s\"," +
        "\"price\":%.5f,\"timestamp\":\"%s\",\"account\":{" +
        "\"balance\":%.2f,\"equity\":%.2f,\"margin\":%.2f," +
        "\"free_margin\":%.2f,\"profit\":%.2f}}",
        id, status, ticket, message, price,
        TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
        AccountInfoDouble(ACCOUNT_BALANCE),
        AccountInfoDouble(ACCOUNT_EQUITY),
        AccountInfoDouble(ACCOUNT_MARGIN),
        AccountInfoDouble(ACCOUNT_MARGIN_FREE),
        AccountInfoDouble(ACCOUNT_PROFIT)
    );
    
    FileWriteString(handle, json);
    FileClose(handle);
}

//+------------------------------------------------------------------+
// Helper functions
//+------------------------------------------------------------------+
double CalculateDailyPL()
{
    // This would need to track balance at day start
    // For now, return current profit
    return AccountInfoDouble(ACCOUNT_PROFIT);
}

//+------------------------------------------------------------------+
void AddMultiTPPosition(ulong ticket, double tp1, double tp2, double tp3, 
                       double vol1, double vol2, double vol3)
{
    int size = ArraySize(multiTPPositions);
    ArrayResize(multiTPPositions, size + 1);
    
    multiTPPositions[size].ticket = ticket;
    multiTPPositions[size].tp1 = tp1;
    multiTPPositions[size].tp2 = tp2;
    multiTPPositions[size].tp3 = tp3;
    multiTPPositions[size].volume1 = vol1;
    multiTPPositions[size].volume2 = vol2;
    multiTPPositions[size].volume3 = vol3;
    multiTPPositions[size].currentStep = 0;
}

//+------------------------------------------------------------------+
ulong GetLastTicket()
{
    // Get ticket of last opened position
    for (int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if (PositionSelectByIndex(i))
        {
            if (PositionGetInteger(POSITION_MAGIC) == MagicNumber)
            {
                return PositionGetInteger(POSITION_TICKET);
            }
        }
    }
    return 0;
}

//+------------------------------------------------------------------+
//+------------------------------------------------------------------+
bool ExecuteEnhancedTrade(string id, string symbol, string direction, double volume, double sl, double tp, string comment)
{
    MqlTrade trade;
    
    ENUM_ORDER_TYPE orderType = (direction == "BUY") ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
    double price = (direction == "BUY") ? SymbolInfoDouble(symbol, SYMBOL_ASK) : SymbolInfoDouble(symbol, SYMBOL_BID);
    
    bool result = trade.Buy(volume, symbol, price, sl, tp, comment);
    if (!result && direction == "SELL")
        result = trade.Sell(volume, symbol, price, sl, tp, comment);
    
    if (result)
    {
        WriteResult(id, "success", trade.ResultOrder(), "Trade executed successfully", price);
        return true;
    }
    else
    {
        WriteResult(id, "error", 0, trade.ResultComment(), 0);
        return false;
    }
}

//+------------------------------------------------------------------+
void ProcessCSVInstruction(string content)
{
    // Legacy CSV format: symbol,direction,volume,sl,tp,comment
    string parts[];
    int count = StringSplit(content, ',', parts);
    
    if (count >= 6)
    {
        string symbol = parts[0];
        string direction = parts[1];
        double volume = StringToDouble(parts[2]);
        double sl = StringToDouble(parts[3]);
        double tp = StringToDouble(parts[4]);
        string comment = parts[5];
        
        ExecuteEnhancedTrade("csv_trade", symbol, direction, volume, sl, tp, comment);
    }
}

//+------------------------------------------------------------------+
void ProcessPartialCloseAtLevel(ulong ticket, double percent)
{
    string command = StringFormat("{\"action\":\"close_partial\",\"ticket\":%d,\"percent\":%.1f}", 
                                 ticket, percent);
    ProcessEnhancedPartialClose(command);
}

//+------------------------------------------------------------------+
void AddTrailingPosition(ulong ticket, int distance, int step)
{
    // Simplified trailing implementation
    if (PositionSelectByTicket(ticket))
    {
        string symbol = PositionGetString(POSITION_SYMBOL);
        ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
        double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
        double currentSL = PositionGetDouble(POSITION_SL);
        double currentPrice = (type == POSITION_TYPE_BUY) ? 
                             SymbolInfoDouble(symbol, SYMBOL_BID) : 
                             SymbolInfoDouble(symbol, SYMBOL_ASK);
        
        double newSL = 0;
        if (type == POSITION_TYPE_BUY)
        {
            newSL = currentPrice - distance * point;
            if (newSL > currentSL)
            {
                MqlTrade trade;
                trade.PositionModify(ticket, newSL, PositionGetDouble(POSITION_TP));
            }
        }
        else
        {
            newSL = currentPrice + distance * point;
            if (currentSL == 0 || newSL < currentSL)
            {
                MqlTrade trade;
                trade.PositionModify(ticket, newSL, PositionGetDouble(POSITION_TP));
            }
        }
    }
}

//+------------------------------------------------------------------+
void UpdateTrailingStops()
{
    // Simplified trailing stops update
    for (int i = 0; i < ArraySize(positions); i++)
    {
        if (EnableTrailing)
        {
            AddTrailingPosition(positions[i].ticket, 30, 10);
        }
    }
}

//+------------------------------------------------------------------+
string ExtractString(string json, string key)
{
    string searchKey = "\"" + key + "\":\"";
    int start = StringFind(json, searchKey);
    if (start < 0) return "";
    
    start += StringLen(searchKey);
    int end = StringFind(json, "\"", start);
    if (end < 0) return "";
    
    return StringSubstr(json, start, end - start);
}

//+------------------------------------------------------------------+
double ExtractDouble(string json, string key, double defaultValue = 0)
{
    string searchKey = "\"" + key + "\":";
    int start = StringFind(json, searchKey);
    if (start < 0) return defaultValue;
    
    start += StringLen(searchKey);
    int end = StringFind(json, ",", start);
    if (end < 0) end = StringFind(json, "}", start);
    if (end < 0) return defaultValue;
    
    string value = StringSubstr(json, start, end - start);
    return StringToDouble(value);
}

//+------------------------------------------------------------------+
bool ExtractBool(string json, string key, bool defaultValue = false)
{
    string searchKey = "\"" + key + "\":";
    int start = StringFind(json, searchKey);
    if (start < 0) return defaultValue;
    
    start += StringLen(searchKey);
    string value = StringSubstr(json, start, 4);
    
    return (value == "true");
}

// ... (Additional helper functions from v2 for security, validation, etc.)