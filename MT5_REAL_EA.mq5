//+------------------------------------------------------------------+
//| BITTEN Real MT5 EA - ACTUAL TRADE EXECUTION                     |
//+------------------------------------------------------------------+
#property copyright "BITTEN"
#property version   "1.00"
#property strict

input int MagicNumber = 20250626;
string DropFolder = "Files\\BITTEN\\Drop\\user_7176191872\\";

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("🚀 BITTEN REAL EA STARTING - ACTUAL TRADES ENABLED");
    Print("📁 Monitoring folder: ", DropFolder);
    Print("🎯 Magic Number: ", MagicNumber);
    Print("💰 Account: ", AccountInfoInteger(ACCOUNT_LOGIN));
    Print("🏦 Broker: ", AccountInfoString(ACCOUNT_COMPANY));
    Print("💵 Balance: $", AccountInfoDouble(ACCOUNT_BALANCE));
    
    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert tick function - PROCESSES REAL TRADES                    |
//+------------------------------------------------------------------+
void OnTick()
{
    static datetime lastCheck = 0;
    
    // Check for new trade files every second
    if(TimeCurrent() > lastCheck + 1)
    {
        ProcessTradeFiles();
        lastCheck = TimeCurrent();
    }
}

//+------------------------------------------------------------------+
//| Process trade files from Python bridge                          |
//+------------------------------------------------------------------+
void ProcessTradeFiles()
{
    string pattern = DropFolder + "trade_*.json";
    string files[];
    int fileCount = 0;
    
    // Get all JSON files
    long search = FileFindFirst(pattern, files[0]);
    if(search != INVALID_HANDLE)
    {
        do
        {
            fileCount++;
            ArrayResize(files, fileCount);
            files[fileCount-1] = files[0];
        }
        while(FileFindNext(search, files[0]));
        FileFindClose(search);
    }
    
    // Process each trade file
    for(int i = 0; i < fileCount; i++)
    {
        ProcessSingleTradeFile(files[i]);
    }
}

//+------------------------------------------------------------------+
//| Process individual trade file - EXECUTES REAL TRADES            |
//+------------------------------------------------------------------+
void ProcessSingleTradeFile(string filename)
{
    string fullPath = DropFolder + filename;
    
    // Read trade instruction file
    int fileHandle = FileOpen(fullPath, FILE_READ|FILE_TXT);
    if(fileHandle == INVALID_HANDLE)
    {
        Print("❌ Cannot open file: ", fullPath);
        return;
    }
    
    string jsonData = "";
    while(!FileIsEnding(fileHandle))
    {
        jsonData += FileReadString(fileHandle);
    }
    FileClose(fileHandle);
    
    Print("📄 Processing file: ", filename);
    Print("📋 JSON Data: ", jsonData);
    
    // Parse JSON (simplified - extract key values)
    string symbol = ExtractJsonValue(jsonData, "symbol");
    string action = ExtractJsonValue(jsonData, "action");
    double volume = StringToDouble(ExtractJsonValue(jsonData, "volume"));
    double sl = StringToDouble(ExtractJsonValue(jsonData, "sl"));
    double tp = StringToDouble(ExtractJsonValue(jsonData, "tp"));
    string comment = ExtractJsonValue(jsonData, "comment");
    
    Print("🎯 Trade Details:");
    Print("   Symbol: ", symbol);
    Print("   Action: ", action);
    Print("   Volume: ", volume);
    Print("   SL: ", sl);
    Print("   TP: ", tp);
    Print("   Comment: ", comment);
    
    // EXECUTE REAL TRADE
    bool success = false;
    int ticket = 0;
    
    if(action == "buy")
    {
        ticket = ExecuteRealBuy(symbol, volume, sl, tp, comment);
        success = (ticket > 0);
    }
    else if(action == "sell")
    {
        ticket = ExecuteRealSell(symbol, volume, sl, tp, comment);
        success = (ticket > 0);
    }
    
    if(success)
    {
        Print("✅ REAL TRADE EXECUTED! Ticket: ", ticket);
        Print("💰 New Balance: $", AccountInfoDouble(ACCOUNT_BALANCE));
        
        // Write result file
        WriteTradeResult(filename, ticket, true, "Trade executed successfully");
    }
    else
    {
        Print("❌ TRADE EXECUTION FAILED!");
        WriteTradeResult(filename, 0, false, "Trade execution failed: " + IntegerToString(GetLastError()));
    }
    
    // Delete processed file
    FileDelete(fullPath);
    Print("🗑️ Deleted processed file: ", filename);
}

//+------------------------------------------------------------------+
//| Execute real BUY trade                                           |
//+------------------------------------------------------------------+
int ExecuteRealBuy(string symbol, double volume, double sl, double tp, string comment)
{
    MqlTradeRequest request = {};
    MqlTradeResult result = {};
    
    request.action = TRADE_ACTION_DEAL;
    request.symbol = symbol;
    request.volume = volume;
    request.type = ORDER_TYPE_BUY;
    request.price = SymbolInfoDouble(symbol, SYMBOL_ASK);
    request.sl = sl;
    request.tp = tp;
    request.magic = MagicNumber;
    request.comment = comment;
    request.type_filling = ORDER_FILLING_IOC;
    
    bool success = OrderSend(request, result);
    
    Print("🔥 BUY ORDER SENT:");
    Print("   Symbol: ", symbol);
    Print("   Volume: ", volume);
    Print("   Price: ", request.price);
    Print("   Success: ", success);
    Print("   Ticket: ", result.order);
    Print("   Retcode: ", result.retcode);
    Print("   Comment: ", result.comment);
    
    return success ? (int)result.order : 0;
}

//+------------------------------------------------------------------+
//| Execute real SELL trade                                          |
//+------------------------------------------------------------------+
int ExecuteRealSell(string symbol, double volume, double sl, double tp, string comment)
{
    MqlTradeRequest request = {};
    MqlTradeResult result = {};
    
    request.action = TRADE_ACTION_DEAL;
    request.symbol = symbol;
    request.volume = volume;
    request.type = ORDER_TYPE_SELL;
    request.price = SymbolInfoDouble(symbol, SYMBOL_BID);
    request.sl = sl;
    request.tp = tp;
    request.magic = MagicNumber;
    request.comment = comment;
    request.type_filling = ORDER_FILLING_IOC;
    
    bool success = OrderSend(request, result);
    
    Print("🔥 SELL ORDER SENT:");
    Print("   Symbol: ", symbol);
    Print("   Volume: ", volume);
    Print("   Price: ", request.price);
    Print("   Success: ", success);
    Print("   Ticket: ", result.order);
    Print("   Retcode: ", result.retcode);
    Print("   Comment: ", result.comment);
    
    return success ? (int)result.order : 0;
}

//+------------------------------------------------------------------+
//| Simple JSON value extractor                                      |
//+------------------------------------------------------------------+
string ExtractJsonValue(string json, string key)
{
    string searchPattern = "\"" + key + "\":";
    int startPos = StringFind(json, searchPattern);
    if(startPos == -1) return "";
    
    startPos += StringLen(searchPattern);
    
    // Skip whitespace and quotes
    while(startPos < StringLen(json) && (StringGetCharacter(json, startPos) == ' ' || 
          StringGetCharacter(json, startPos) == '"'))
        startPos++;
    
    int endPos = startPos;
    bool inQuotes = (StringGetCharacter(json, startPos-1) == '"');
    
    if(inQuotes)
    {
        // Find closing quote
        while(endPos < StringLen(json) && StringGetCharacter(json, endPos) != '"')
            endPos++;
    }
    else
    {
        // Find comma or closing brace
        while(endPos < StringLen(json) && StringGetCharacter(json, endPos) != ',' && 
              StringGetCharacter(json, endPos) != '}')
            endPos++;
    }
    
    return StringSubstr(json, startPos, endPos - startPos);
}

//+------------------------------------------------------------------+
//| Write trade execution result                                     |
//+------------------------------------------------------------------+
void WriteTradeResult(string originalFile, int ticket, bool success, string message)
{
    string resultFile = StringReplace(originalFile, "trade_", "result_");
    resultFile = StringReplace(resultFile, ".json", "_result.json");
    
    int handle = FileOpen(DropFolder + "../Results/user_7176191872/" + resultFile, 
                         FILE_WRITE|FILE_TXT);
    if(handle != INVALID_HANDLE)
    {
        FileWrite(handle, "{");
        FileWrite(handle, "  \"ticket\": " + IntegerToString(ticket) + ",");
        FileWrite(handle, "  \"success\": " + (success ? "true" : "false") + ",");
        FileWrite(handle, "  \"message\": \"" + message + "\",");
        FileWrite(handle, "  \"timestamp\": \"" + TimeToString(TimeCurrent()) + "\",");
        FileWrite(handle, "  \"account\": " + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)) + ",");
        FileWrite(handle, "  \"balance\": " + DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2));
        FileWrite(handle, "}");
        FileClose(handle);
        
        Print("📝 Result written: ", resultFile);
    }
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("🛑 BITTEN REAL EA STOPPED");
}