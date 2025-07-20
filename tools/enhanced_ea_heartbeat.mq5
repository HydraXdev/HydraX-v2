//+------------------------------------------------------------------+
//| Enhanced EA Heartbeat & Signal Logging                           |
//| Modifications for BITTENBridge_v3_ENHANCED.mq5                  |
//+------------------------------------------------------------------+

// Add these functions to your existing BITTENBridge_v3_ENHANCED.mq5

datetime lastHeartbeatTime = 0;
datetime lastSignalCheck = 0;
string lastProcessedSignal = "";

//+------------------------------------------------------------------+
//| Enhanced Heartbeat Function                                       |
//+------------------------------------------------------------------+
void WriteEnhancedHeartbeat()
{
    // Write heartbeat every 30 seconds
    if (TimeCurrent() - lastHeartbeatTime < 30) return;
    
    int heartbeatHandle = FileOpen("bridge_heartbeat.txt", FILE_WRITE | FILE_TXT | FILE_ANSI);
    if (heartbeatHandle != INVALID_HANDLE)
    {
        // Enhanced heartbeat with system info
        string heartbeatData = StringFormat(
            "[HEARTBEAT] %s | EA: ACTIVE | Trades: %d | Balance: %.2f | Free: %.2f | Signals: %s",
            TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
            CountActivePositions(),
            AccountInfoDouble(ACCOUNT_BALANCE),
            AccountInfoDouble(ACCOUNT_MARGIN_FREE),
            lastProcessedSignal != "" ? "YES" : "NO"
        );
        
        FileWriteString(heartbeatHandle, heartbeatData);
        FileClose(heartbeatHandle);
        
        lastHeartbeatTime = TimeCurrent();
        
        // Log to EA log as well
        Print("💓 HEARTBEAT: EA operational - Balance: $", AccountInfoDouble(ACCOUNT_BALANCE));
    }
}

//+------------------------------------------------------------------+
//| Enhanced Signal Detection and Logging                            |
//+------------------------------------------------------------------+
void LogSignalActivity(string signalType, string signalData, string status)
{
    int signalLogHandle = FileOpen("signal_activity.txt", FILE_WRITE | FILE_TXT | FILE_ANSI);
    if (signalLogHandle != INVALID_HANDLE)
    {
        string logEntry = StringFormat(
            "[%s] %s | %s | %s",
            TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
            signalType,
            signalData,
            status
        );
        
        FileWriteString(signalLogHandle, logEntry);
        FileClose(signalLogHandle);
        
        // Also log to EA log
        Print("📡 SIGNAL: ", signalType, " - ", status);
    }
}

//+------------------------------------------------------------------+
//| Enhanced Trade Execution Logging                                 |
//+------------------------------------------------------------------+
void LogTradeExecution(string tradeId, string symbol, string direction, double lot, string result, ulong ticket = 0)
{
    int tradeLogHandle = FileOpen("trade_execution.txt", FILE_WRITE | FILE_TXT | FILE_ANSI);
    if (tradeLogHandle != INVALID_HANDLE)
    {
        string logEntry = StringFormat(
            "[%s] TRADE_ID: %s | %s %s %.2f | %s | TICKET: %d | BALANCE: %.2f",
            TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
            tradeId,
            symbol,
            direction,
            lot,
            result,
            ticket,
            AccountInfoDouble(ACCOUNT_BALANCE)
        );
        
        FileWriteString(tradeLogHandle, logEntry);
        FileClose(tradeLogHandle);
        
        // Enhanced EA log
        Print("🔥 TRADE: ", tradeId, " - ", symbol, " ", direction, " ", lot, " - ", result);
    }
}

//+------------------------------------------------------------------+
//| Enhanced OnTick Function                                          |
//+------------------------------------------------------------------+
void OnTick()
{
    // Write enhanced heartbeat
    WriteEnhancedHeartbeat();
    
    // Check for signals more frequently
    if (TimeCurrent() - lastSignalCheck >= 1) // Check every second
    {
        CheckForTradeInstructionEnhanced();
        lastSignalCheck = TimeCurrent();
    }
}

//+------------------------------------------------------------------+
//| Enhanced Signal Processing                                        |
//+------------------------------------------------------------------+
void CheckForTradeInstructionEnhanced()
{
    if (!FileIsExist(InstructionFile)) return;
    
    // Log signal detection
    LogSignalActivity("SIGNAL_DETECTED", InstructionFile, "PROCESSING");
    
    int fileHandle = FileOpen(InstructionFile, FILE_READ | FILE_TXT | FILE_ANSI);
    if (fileHandle == INVALID_HANDLE) 
    {
        LogSignalActivity("SIGNAL_ERROR", InstructionFile, "CANNOT_OPEN");
        return;
    }
    
    string instruction = FileReadString(fileHandle);
    FileClose(fileHandle);
    
    // Store last processed signal for heartbeat
    lastProcessedSignal = instruction;
    
    // Log signal content
    LogSignalActivity("SIGNAL_CONTENT", instruction, "PARSED");
    
    // Parse CSV instruction
    string parts[];
    int count = StringSplit(instruction, ',', parts);
    
    if (count < 7)
    {
        LogSignalActivity("SIGNAL_ERROR", instruction, "INVALID_FORMAT");
        FileDelete(InstructionFile);
        return;
    }
    
    // Extract trade parameters
    string tradeId = StringTrim(parts[0]);
    string symbol = StringTrim(parts[1]);
    string typeStr = StringTrim(parts[2]);
    double lot = StringToDouble(parts[3]);
    double price = StringToDouble(parts[4]);
    double tp = StringToDouble(parts[5]);
    double sl = StringToDouble(parts[6]);
    
    // Log trade attempt
    LogTradeExecution(tradeId, symbol, typeStr, lot, "ATTEMPTING", 0);
    
    // Execute trade with enhanced logging
    bool success = ExecuteTradeEnhanced(tradeId, symbol, typeStr, lot, price, tp, sl);
    
    // Delete instruction file
    FileDelete(InstructionFile);
    
    // Log completion
    LogSignalActivity("SIGNAL_COMPLETE", tradeId, success ? "SUCCESS" : "FAILED");
}

//+------------------------------------------------------------------+
//| Enhanced Trade Execution                                          |
//+------------------------------------------------------------------+
bool ExecuteTradeEnhanced(string tradeId, string symbol, string typeStr, double lot, double price, double tp, double sl)
{
    ENUM_ORDER_TYPE orderType = (typeStr == "BUY") ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
    
    // Pre-execution validation
    if (lot <= 0 || lot > MaxLotSize)
    {
        LogTradeExecution(tradeId, symbol, typeStr, lot, "INVALID_LOT_SIZE", 0);
        return false;
    }
    
    if (AccountInfoDouble(ACCOUNT_BALANCE) < 10)
    {
        LogTradeExecution(tradeId, symbol, typeStr, lot, "INSUFFICIENT_BALANCE", 0);
        return false;
    }
    
    MqlTradeRequest request;
    MqlTradeResult result;
    
    ZeroMemory(request);
    ZeroMemory(result);
    
    // Setup trade request
    request.action = TRADE_ACTION_DEAL;
    request.symbol = symbol;
    request.volume = lot;
    request.type = orderType;
    request.deviation = SlippagePoints;
    request.magic = MagicNumber;
    request.comment = "BITTEN_" + tradeId;
    
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
    
    // Execute with retries
    bool success = false;
    for (int i = 0; i < MaxRetries && !success; i++)
    {
        success = OrderSend(request, result);
        if (!success) 
        {
            LogTradeExecution(tradeId, symbol, typeStr, lot, "RETRY_" + IntegerToString(i + 1), 0);
            Sleep(100);
        }
    }
    
    // Log final result
    if (success && result.retcode == TRADE_RETCODE_DONE)
    {
        LogTradeExecution(tradeId, symbol, typeStr, lot, "SUCCESS", result.order);
        WriteResult(tradeId, "success", result.order, "Order executed successfully", result.price);
        return true;
    }
    else
    {
        string error = StringFormat("Error %d: %s", result.retcode, result.comment);
        LogTradeExecution(tradeId, symbol, typeStr, lot, "FAILED_" + IntegerToString(result.retcode), 0);
        WriteResult(tradeId, "failed", 0, error, 0);
        return false;
    }
}

//+------------------------------------------------------------------+
//| Enhanced Status Reporting                                         |
//+------------------------------------------------------------------+
void WriteEnhancedStatus()
{
    int statusHandle = FileOpen("ea_status_enhanced.txt", FILE_WRITE | FILE_TXT | FILE_ANSI);
    if (statusHandle != INVALID_HANDLE)
    {
        string statusData = StringFormat(
            "{\"timestamp\":\"%s\",\"status\":\"ACTIVE\",\"balance\":%.2f,\"equity\":%.2f,\"margin\":%.2f,\"free_margin\":%.2f,\"positions\":%d,\"last_signal\":\"%s\",\"ea_version\":\"BITTEN_v3_ENHANCED\",\"heartbeat_active\":true}",
            TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
            AccountInfoDouble(ACCOUNT_BALANCE),
            AccountInfoDouble(ACCOUNT_EQUITY),
            AccountInfoDouble(ACCOUNT_MARGIN),
            AccountInfoDouble(ACCOUNT_MARGIN_FREE),
            CountActivePositions(),
            lastProcessedSignal
        );
        
        FileWriteString(statusHandle, statusData);
        FileClose(statusHandle);
    }
}

//+------------------------------------------------------------------+
//| Enhanced OnInit Function                                          |
//+------------------------------------------------------------------+
int OnInit()
{
    // Your existing OnInit code...
    
    // Initialize enhanced logging
    LogSignalActivity("EA_INIT", "BITTEN_v3_ENHANCED", "STARTED");
    WriteEnhancedHeartbeat();
    WriteEnhancedStatus();
    
    Print("🚀 BITTEN Enhanced EA with Fire Loop Validation INITIALIZED");
    Print("💓 Heartbeat: ACTIVE");
    Print("📡 Signal Logging: ACTIVE");
    Print("🔥 Trade Logging: ACTIVE");
    
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Enhanced OnDeinit Function                                        |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    LogSignalActivity("EA_DEINIT", "BITTEN_v3_ENHANCED", "STOPPED");
    Print("🛑 BITTEN Enhanced EA STOPPED - Reason: ", reason);
}

// Add this to your existing EA's OnTick function:
/*
void OnTick()
{
    // Your existing OnTick code...
    
    // Add enhanced heartbeat and signal checking
    WriteEnhancedHeartbeat();
    
    if (TimeCurrent() - lastSignalCheck >= 1)
    {
        CheckForTradeInstructionEnhanced();
        lastSignalCheck = TimeCurrent();
    }
}
*/