
#property strict

input string TradeFileName = "trade_instructions.txt";
input string ResultLogFilename = "trade_result.txt";
datetime lastExecution = 0;

int OnInit()
{
   Print("📂 BITTEN EA Ready — Data folder: ", TerminalInfoString(TERMINAL_DATA_PATH));
   return INIT_SUCCEEDED;
}

void OnTick()
{
   if (TimeCurrent() - lastExecution < 5) return;

   int fileHandle = FileOpen(TradeFileName, FILE_READ | FILE_ANSI);
   if (fileHandle == INVALID_HANDLE) return;

   string fileData = FileReadString(fileHandle);
   FileClose(fileHandle);

   string parts[];
   StringSplit(fileData, ',', parts);
   if (ArraySize(parts) < 6) return;

   string symbol = StringTrim(parts[0]);
   string typeStr = StringTrim(parts[1]);
   double lot     = StringToDouble(parts[2]);
   double price   = StringToDouble(parts[3]);
   double tp      = StringToDouble(parts[4]);
   double sl      = StringToDouble(parts[5]);

   Print("🔥 FILE INPUT: ", fileData);
   Print("📌 Parsed type: ", typeStr);

   ENUM_ORDER_TYPE orderType;
   if (typeStr == "BUY") orderType = ORDER_TYPE_BUY;
   else if (typeStr == "SELL") orderType = ORDER_TYPE_SELL;
   else {
      Print("⚠️ Invalid order type: ", typeStr);
      return;
   }

   MqlTradeRequest request;
   MqlTradeResult  result;
   ZeroMemory(request);
   ZeroMemory(result);

   request.action       = TRADE_ACTION_DEAL;
   request.symbol       = symbol;
   request.volume       = lot;
   request.type         = orderType;
   request.price        = NormalizeDouble(price, (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS));
   request.sl           = NormalizeDouble(sl,    (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS));
   request.tp           = NormalizeDouble(tp,    (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS));
   request.deviation    = 20;
   request.magic        = 20250626;
   request.type_filling = ORDER_FILLING_IOC;

   bool success = OrderSend(request, result);
   if (success && result.retcode == TRADE_RETCODE_DONE)
      Print("✅ Executed: ", result.order);
   else
      Print("❌ Order failed: ", result.retcode, " ", result.comment);

   string currentFingerprint = symbol + typeStr + DoubleToString(price, 5);
   static string lastFingerprint = "";
   if (currentFingerprint == lastFingerprint) return;
   lastFingerprint = currentFingerprint;
   LogResult(IntegerToString(result.order), symbol, typeStr, lot, price, tp, sl, success);
   lastExecution = TimeCurrent();
   if (success && result.retcode == TRADE_RETCODE_DONE) FileDelete(TradeFileName);
}

void LogResult(string id, string symbol, string type, double lot, double price, double tp, double sl, bool success)
{
   string status = success ? "filled" : "failed";
   string ts     = TimeToString(TimeCurrent(), TIME_DATE | TIME_MINUTES);
   string line   = StringFormat("{"id":"%s","symbol":"%s","type":"%s","lot":%.2f,"price":%.2f,"tp":%.2f,"sl":%.2f,"status":"%s","timestamp":"%s"}",
                                id, symbol, type, lot, price, tp, sl, status, ts);

   int fh = FileOpen(ResultLogFilename, FILE_WRITE | FILE_TXT | FILE_ANSI);
   if (fh != INVALID_HANDLE)
   {
      FileSeek(fh, 0, SEEK_END);
      FileWriteString(fh, line + "\n");
      FileClose(fh);
   }
   else
   {
      Print("⚠️ Failed to log result.");
   }
}
