//+------------------------------------------------------------------+
//|                                        BITTEN_OHLCV_Provider.mq5 |
//|                                          BITTEN Trading System    |
//|                     Provides OHLCV data for AAA Signal Engine    |
//+------------------------------------------------------------------+
#property copyright "BITTEN Trading System"
#property link      "https://joinbitten.com"
#property version   "1.00"
#property strict

// Input parameters
input string InpDataPath = "C:\\MT5_BITTEN\\";  // Path for data files
input int InpCheckInterval = 100;               // Check interval in milliseconds

// File names
string RequestFile = "bitten_ohlcv_request.txt";
string ResponseFile = "bitten_ohlcv_response.json";
string MarketDataFile = "bitten_market_data.json";

//+------------------------------------------------------------------+
//| Expert initialization function                                    |
//+------------------------------------------------------------------+
int OnInit()
{
   // Create directory if it doesn't exist
   if(!FileIsExist(InpDataPath))
   {
      Print("Creating BITTEN data directory: ", InpDataPath);
   }
   
   // Start continuous market data updates
   EventSetMillisecondTimer(InpCheckInterval);
   
   Print("BITTEN OHLCV Provider started successfully");
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                  |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   Print("BITTEN OHLCV Provider stopped");
}

//+------------------------------------------------------------------+
//| Timer function - Check for data requests                          |
//+------------------------------------------------------------------+
void OnTimer()
{
   // Update current market data
   UpdateMarketData();
   
   // Check for OHLCV requests
   CheckForOHLCVRequests();
}

//+------------------------------------------------------------------+
//| Update current market data file                                   |
//+------------------------------------------------------------------+
void UpdateMarketData()
{
   string data = "{";
   string symbols[] = {"EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", 
                      "EURJPY", "GBPJPY", "NZDUSD", "USDCHF", "EURGBP"};
   
   for(int i = 0; i < ArraySize(symbols); i++)
   {
      if(SymbolSelect(symbols[i], true))
      {
         double bid = SymbolInfoDouble(symbols[i], SYMBOL_BID);
         double ask = SymbolInfoDouble(symbols[i], SYMBOL_ASK);
         double spread = (ask - bid) / SymbolInfoDouble(symbols[i], SYMBOL_POINT);
         
         if(i > 0) data += ",";
         data += "\"" + symbols[i] + "\":{";
         data += "\"bid\":" + DoubleToString(bid, 5) + ",";
         data += "\"ask\":" + DoubleToString(ask, 5) + ",";
         data += "\"spread\":" + DoubleToString(spread, 1) + ",";
         data += "\"time\":" + IntegerToString(TimeCurrent()) + "}";
      }
   }
   
   data += "}";
   
   // Write to file
   int handle = FileOpen(InpDataPath + MarketDataFile, FILE_WRITE|FILE_TXT|FILE_ANSI);
   if(handle != INVALID_HANDLE)
   {
      FileWriteString(handle, data);
      FileClose(handle);
   }
}

//+------------------------------------------------------------------+
//| Check for OHLCV data requests                                     |
//+------------------------------------------------------------------+
void CheckForOHLCVRequests()
{
   string requestPath = InpDataPath + RequestFile;
   
   if(!FileIsExist(requestPath))
      return;
   
   // Read request
   int handle = FileOpen(requestPath, FILE_READ|FILE_TXT|FILE_ANSI);
   if(handle == INVALID_HANDLE)
      return;
   
   string requestData = FileReadString(handle, FileSize(handle));
   FileClose(handle);
   
   // Delete request file
   FileDelete(requestPath);
   
   // Parse request (simplified - in production use proper JSON parsing)
   ProcessOHLCVRequest(requestData);
}

//+------------------------------------------------------------------+
//| Process OHLCV request and generate response                       |
//+------------------------------------------------------------------+
void ProcessOHLCVRequest(string request)
{
   Print("Processing OHLCV request");
   
   // Default parameters
   ENUM_TIMEFRAMES timeframe = PERIOD_M5;
   int bars = 500;
   
   // Parse timeframe from request
   if(StringFind(request, "\"M1\"") >= 0) timeframe = PERIOD_M1;
   else if(StringFind(request, "\"M5\"") >= 0) timeframe = PERIOD_M5;
   else if(StringFind(request, "\"M15\"") >= 0) timeframe = PERIOD_M15;
   else if(StringFind(request, "\"M30\"") >= 0) timeframe = PERIOD_M30;
   else if(StringFind(request, "\"H1\"") >= 0) timeframe = PERIOD_H1;
   else if(StringFind(request, "\"H4\"") >= 0) timeframe = PERIOD_H4;
   else if(StringFind(request, "\"D1\"") >= 0) timeframe = PERIOD_D1;
   
   // Get pairs to process
   string symbols[] = {"EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", 
                      "EURJPY", "GBPJPY", "NZDUSD", "USDCHF", "EURGBP"};
   
   // Build response
   string response = "{\"status\":\"success\",\"data\":{";
   
   for(int i = 0; i < ArraySize(symbols); i++)
   {
      string symbol = symbols[i];
      
      // Check if symbol is in request
      if(StringFind(request, symbol) < 0)
         continue;
      
      if(i > 0 && StringLen(response) > 30) response += ",";
      
      // Get OHLCV data
      MqlRates rates[];
      int copied = CopyRates(symbol, timeframe, 0, bars, rates);
      
      if(copied > 0)
      {
         response += "\"" + symbol + "\":[";
         
         for(int j = 0; j < copied && j < bars; j++)
         {
            if(j > 0) response += ",";
            response += "[";
            response += IntegerToString(rates[j].time) + ",";
            response += DoubleToString(rates[j].open, 5) + ",";
            response += DoubleToString(rates[j].high, 5) + ",";
            response += DoubleToString(rates[j].low, 5) + ",";
            response += DoubleToString(rates[j].close, 5) + ",";
            response += IntegerToString(rates[j].tick_volume);
            response += "]";
         }
         
         response += "]";
      }
   }
   
   response += "}}";
   
   // Write response
   int handle = FileOpen(InpDataPath + ResponseFile, FILE_WRITE|FILE_TXT|FILE_ANSI);
   if(handle != INVALID_HANDLE)
   {
      FileWriteString(handle, response);
      FileClose(handle);
      Print("OHLCV response written successfully");
   }
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
   // Main work is done in OnTimer
}
//+------------------------------------------------------------------+