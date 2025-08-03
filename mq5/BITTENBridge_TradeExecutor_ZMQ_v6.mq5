//+------------------------------------------------------------------+
//|                          BITTENBridge_TradeExecutor_ZMQ_v6.mq5   |
//|                   3-Way Architecture with ZMQ Data Streaming     |
//|                          File-Based Trade Execution              |
//+------------------------------------------------------------------+
#property copyright "BITTEN Trading System"
#property version   "6.00"
#property strict

//+------------------------------------------------------------------+
//| DLL IMPORTS - Using ZMQ DLL                                      |
//| Place libzmq.dll in: terminal_folder/Libraries/                 |
//+------------------------------------------------------------------+
#import "libzmq.dll"
   // Context functions
   int zmq_ctx_new();
   void zmq_ctx_destroy(int context);
   
   // Socket functions
   int zmq_socket(int context, int type);
   int zmq_close(int socket);
   int zmq_bind(int socket, uchar &endpoint[]);
   
   // Socket options
   int zmq_setsockopt(int socket, int option, uchar &value[], int size);
   
   // Messaging
   int zmq_send(int socket, uchar &data[], int size, int flags);
   
   // Error handling
   int zmq_errno();
#import

//+------------------------------------------------------------------+
//| ZMQ CONSTANTS                                                    |
//+------------------------------------------------------------------+
#define ZMQ_PUB      1      // Publisher socket type
#define ZMQ_SNDHWM   1      // Send high water mark
#define ZMQ_LINGER   2      // Linger period
#define ZMQ_SNDTIMEO 28     // Send timeout
#define ZMQ_DONTWAIT 1      // Non-blocking flag

//+------------------------------------------------------------------+
//| CONFIGURATION                                                    |
//+------------------------------------------------------------------+
input string  InpZMQEndpoint = "tcp://*:5555";        // ZMQ Publisher Endpoint
input int     InpSendBuffer = 50000;                  // High Water Mark (messages)
input int     InpStreamInterval = 100;                 // Stream interval (ms)
input int     InpCheckInterval = 1000;                 // Trade check interval (ms)
input bool    InpEnableAllPairs = true;               // Stream all 15 pairs
input bool    InpVerboseLog = false;                  // Verbose logging
input string  InpDLLReminder = "⚠️ ENABLE: Tools->Options->Expert Advisors->Allow DLL imports";

//+------------------------------------------------------------------+
//| GLOBAL VARIABLES                                                 |
//+------------------------------------------------------------------+
// ZMQ handles
int g_zmq_context = 0;
int g_zmq_socket = 0;
bool g_zmq_initialized = false;

// Timing
ulong g_last_stream_time = 0;
ulong g_last_check_time = 0;

// Statistics
ulong g_messages_sent = 0;
ulong g_errors_count = 0;
int g_last_error = 0;

// Trading pairs (16+ including Gold)
string g_pairs[] = {"EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD",
                    "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY",
                    "XAUUSD", "GBPNZD", "GBPAUD", "EURAUD", "GBPCHF",
                    "AUDJPY"}; // 16 pairs total including XAUUSD

// File paths for trade execution
string g_fire_file;
string g_result_file;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("====================================================");
   Print("BITTEN Bridge v6.0 - ZMQ Data Stream + File Trading");
   Print("====================================================");
   
   // Check DLL imports
   if(!TerminalInfoInteger(TERMINAL_DLLS_ALLOWED))
   {
      Alert("❌ ERROR: DLL imports are DISABLED!");
      Alert("Please enable: Tools → Options → Expert Advisors → Allow DLL imports");
      Alert("Then reattach this EA to the chart");
      return(INIT_FAILED);
   }
   
   // Initialize file paths
   string data_path = TerminalInfoString(TERMINAL_DATA_PATH);
   g_fire_file = data_path + "\\MQL5\\Files\\BITTEN\\fire.txt";
   g_result_file = data_path + "\\MQL5\\Files\\BITTEN\\trade_result.txt";
   
   // Create BITTEN directory
   if(!FileIsExist("BITTEN\\"))
   {
      FolderCreate("BITTEN");
      Print("Created BITTEN directory");
   }
   
   // Initialize ZMQ
   if(!InitializeZMQ())
   {
      Print("⚠️ WARNING: ZMQ failed - EA will run in trade-only mode");
      // Don't fail - can still execute trades
   }
   
   // Set millisecond timer
   EventSetMillisecondTimer(50);
   
   Print("✅ EA Initialized Successfully");
   Print("📡 ZMQ Publisher: ", g_zmq_initialized ? "ACTIVE" : "DISABLED");
   Print("📁 Trade Execution: ACTIVE");
   
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Initialize ZMQ Publisher                                         |
//+------------------------------------------------------------------+
bool InitializeZMQ()
{
   // Create context
   g_zmq_context = zmq_ctx_new();
   if(g_zmq_context == 0)
   {
      Print("❌ ZMQ Error: Failed to create context");
      return false;
   }
   
   // Create publisher socket
   g_zmq_socket = zmq_socket(g_zmq_context, ZMQ_PUB);
   if(g_zmq_socket == 0)
   {
      Print("❌ ZMQ Error: Failed to create socket");
      zmq_ctx_destroy(g_zmq_context);
      g_zmq_context = 0;
      return false;
   }
   
   // Set socket options
   // Convert int to byte array for ZMQ socket options
   uchar hwm_bytes[4];
   int hwm = InpSendBuffer;
   for(int i = 0; i < 4; i++)
   {
      hwm_bytes[i] = (uchar)((hwm >> (i * 8)) & 0xFF);
   }
   if(zmq_setsockopt(g_zmq_socket, ZMQ_SNDHWM, hwm_bytes, 4) != 0)
   {
      Print("⚠️ ZMQ Warning: Failed to set high water mark");
   }
   
   uchar linger_bytes[4];
   int linger = 0;
   for(int i = 0; i < 4; i++)
   {
      linger_bytes[i] = (uchar)((linger >> (i * 8)) & 0xFF);
   }
   if(zmq_setsockopt(g_zmq_socket, ZMQ_LINGER, linger_bytes, 4) != 0)
   {
      Print("⚠️ ZMQ Warning: Failed to set linger");
   }
   
   uchar timeout_bytes[4];
   int timeout = 100;
   for(int i = 0; i < 4; i++)
   {
      timeout_bytes[i] = (uchar)((timeout >> (i * 8)) & 0xFF);
   }
   if(zmq_setsockopt(g_zmq_socket, ZMQ_SNDTIMEO, timeout_bytes, 4) != 0)
   {
      Print("⚠️ ZMQ Warning: Failed to set send timeout");
   }
   
   // Convert endpoint string to byte array
   uchar endpoint[];
   StringToCharArray(InpZMQEndpoint, endpoint, 0, StringLen(InpZMQEndpoint));
   ArrayResize(endpoint, ArraySize(endpoint) - 1); // Remove null terminator
   
   // Bind socket
   if(zmq_bind(g_zmq_socket, endpoint) != 0)
   {
      int error = zmq_errno();
      Print("❌ ZMQ Error: Failed to bind to ", InpZMQEndpoint, " (errno: ", error, ")");
      zmq_close(g_zmq_socket);
      zmq_ctx_destroy(g_zmq_context);
      g_zmq_socket = 0;
      g_zmq_context = 0;
      return false;
   }
   
   g_zmq_initialized = true;
   Print("✅ ZMQ Publisher bound to: ", InpZMQEndpoint);
   
   // Send startup message
   SendZMQMessage("{\"type\":\"startup\",\"timestamp\":" + IntegerToString(TimeGMT()) + "}");
   
   return true;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   // Send shutdown message
   if(g_zmq_initialized)
   {
      SendZMQMessage("{\"type\":\"shutdown\",\"timestamp\":" + IntegerToString(TimeGMT()) + "}");
   }
   
   // Clean up ZMQ
   if(g_zmq_socket != 0)
   {
      zmq_close(g_zmq_socket);
      g_zmq_socket = 0;
   }
   
   if(g_zmq_context != 0)
   {
      zmq_ctx_destroy(g_zmq_context);
      g_zmq_context = 0;
   }
   
   g_zmq_initialized = false;
   
   // Kill timer
   EventKillTimer();
   
   Print("====================================================");
   Print("EA Shutdown - Messages sent: ", g_messages_sent);
   Print("Errors: ", g_errors_count);
   Print("====================================================");
}

//+------------------------------------------------------------------+
//| Timer function                                                   |
//+------------------------------------------------------------------+
void OnTimer()
{
   ulong current_time = GetTickCount();
   
   // Stream market data
   if(g_zmq_initialized && current_time - g_last_stream_time >= InpStreamInterval)
   {
      if(InpEnableAllPairs)
         StreamAllPairs();
      else
         StreamCurrentPair();
         
      g_last_stream_time = current_time;
   }
   
   // Check for trade signals
   if(current_time - g_last_check_time >= InpCheckInterval)
   {
      CheckFireSignal();
      g_last_check_time = current_time;
   }
}

//+------------------------------------------------------------------+
//| Tick function                                                    |
//+------------------------------------------------------------------+
void OnTick()
{
   // If not streaming all pairs, stream current symbol on tick
   if(g_zmq_initialized && !InpEnableAllPairs)
   {
      StreamSymbolData(Symbol());
   }
}

//+------------------------------------------------------------------+
//| Stream all pairs                                                 |
//+------------------------------------------------------------------+
void StreamAllPairs()
{
   for(int i = 0; i < ArraySize(g_pairs); i++)
   {
      StreamSymbolData(g_pairs[i]);
   }
}

//+------------------------------------------------------------------+
//| Stream current pair                                              |
//+------------------------------------------------------------------+
void StreamCurrentPair()
{
   StreamSymbolData(Symbol());
}

//+------------------------------------------------------------------+
//| Stream symbol data via ZMQ                                       |
//+------------------------------------------------------------------+
void StreamSymbolData(string symbol)
{
   // Ensure symbol is available
   if(!SymbolSelect(symbol, true))
      return;
      
   // Get market data
   double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
   
   // Skip if no valid quotes
   if(bid <= 0 || ask <= 0)
      return;
      
   long volume = SymbolInfoInteger(symbol, SYMBOL_VOLUME);
   double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
   double spread = (ask - bid) / point;
   
   // Build JSON message
   string json = StringFormat(
      "{\"symbol\":\"%s\",\"bid\":%.5f,\"ask\":%.5f,\"spread\":%.1f," +
      "\"volume\":%d,\"timestamp\":%d,\"account_balance\":%.2f," +
      "\"broker\":\"%s\",\"source\":\"MT5_LIVE\"}",
      symbol, bid, ask, spread, volume,
      TimeGMT(),
      AccountInfoDouble(ACCOUNT_BALANCE),
      AccountInfoString(ACCOUNT_COMPANY)
   );
   
   // Build topic-prefixed message for filtering
   string message = symbol + " " + json;
   
   // Send via ZMQ
   SendZMQMessage(message);
}

//+------------------------------------------------------------------+
//| Send message via ZMQ                                             |
//+------------------------------------------------------------------+
bool SendZMQMessage(string message)
{
   if(!g_zmq_initialized)
      return false;
      
   // Convert string to byte array
   uchar data[];
   StringToCharArray(message, data, 0, StringLen(message));
   ArrayResize(data, ArraySize(data) - 1); // Remove null terminator
   
   // Send with non-blocking flag
   int result = zmq_send(g_zmq_socket, data, ArraySize(data), ZMQ_DONTWAIT);
   
   if(result >= 0)
   {
      g_messages_sent++;
      
      if(InpVerboseLog && g_messages_sent % 1000 == 0)
         Print("📤 Sent ", g_messages_sent, " messages");
         
      return true;
   }
   else
   {
      g_errors_count++;
      int error = zmq_errno();
      
      if(error != g_last_error || g_errors_count % 100 == 0)
      {
         if(InpVerboseLog)
            Print("⚠️ ZMQ send error (", g_errors_count, "): errno=", error);
         g_last_error = error;
      }
      
      return false;
   }
}

//+------------------------------------------------------------------+
//| Check for fire signal (file-based trading)                       |
//+------------------------------------------------------------------+
void CheckFireSignal()
{
   if(!FileIsExist("BITTEN\\fire.txt"))
      return;
      
   int handle = FileOpen("BITTEN\\fire.txt", FILE_READ|FILE_TXT|FILE_ANSI);
   if(handle == INVALID_HANDLE)
      return;
      
   string signal = FileReadString(handle);
   FileClose(handle);
   
   if(StringLen(signal) > 0)
   {
      if(InpVerboseLog)
         Print("📥 Fire signal: ", signal);
         
      ProcessTradeSignal(signal);
      FileDelete("BITTEN\\fire.txt");
   }
}

//+------------------------------------------------------------------+
//| Process trade signal                                             |
//+------------------------------------------------------------------+
void ProcessTradeSignal(string signal)
{
   // Parse JSON
   string symbol = ExtractValue(signal, "symbol");
   string type = ExtractValue(signal, "type");
   string action = ExtractValue(signal, "action");
   string signal_id = ExtractValue(signal, "signal_id");
   
   if(action == "close")
   {
      ClosePosition(symbol, signal_id);
   }
   else if(symbol != "" && type != "")
   {
      double lot = StringToDouble(ExtractValue(signal, "lot"));
      int sl = (int)StringToInteger(ExtractValue(signal, "sl"));
      int tp = (int)StringToInteger(ExtractValue(signal, "tp"));
      
      if(lot <= 0) lot = 0.01;
      
      ExecuteTrade(symbol, type, lot, sl, tp, signal_id);
   }
}

//+------------------------------------------------------------------+
//| Execute trade                                                    |
//+------------------------------------------------------------------+
void ExecuteTrade(string symbol, string type, double lot, int sl_points, int tp_points, string signal_id)
{
   if(!SymbolSelect(symbol, true))
   {
      WriteResult(signal_id, "error", 0, "Symbol not available: " + symbol);
      return;
   }
   
   MqlTradeRequest request = {};
   MqlTradeResult result = {};
   
   double price = (type == "buy") ? SymbolInfoDouble(symbol, SYMBOL_ASK) : 
                                   SymbolInfoDouble(symbol, SYMBOL_BID);
   double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
   
   request.action = TRADE_ACTION_DEAL;
   request.symbol = symbol;
   request.volume = lot;
   request.type = (type == "buy") ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   request.price = price;
   request.deviation = 10;
   
   if(sl_points > 0)
   {
      request.sl = (type == "buy") ? price - sl_points * point : 
                                    price + sl_points * point;
   }
   
   if(tp_points > 0)
   {
      request.tp = (type == "buy") ? price + tp_points * point : 
                                    price - tp_points * point;
   }
   
   request.comment = signal_id;
   request.magic = 20240718;
   
   if(OrderSend(request, result))
   {
      WriteResult(signal_id, "success", result.deal, 
                  StringFormat("Executed at %.5f", result.price));
   }
   else
   {
      WriteResult(signal_id, "error", 0, 
                  StringFormat("Error %d: %s", result.retcode, 
                              GetErrorDescription(result.retcode)));
   }
}

//+------------------------------------------------------------------+
//| Close position                                                   |
//+------------------------------------------------------------------+
void ClosePosition(string symbol, string signal_id)
{
   int total = PositionsTotal();
   
   for(int i = total - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(PositionSelectByTicket(ticket))
      {
         if(PositionGetString(POSITION_SYMBOL) == symbol)
         {
            MqlTradeRequest request = {};
            MqlTradeResult result = {};
            
            request.action = TRADE_ACTION_DEAL;
            request.position = PositionGetInteger(POSITION_TICKET);
            request.symbol = symbol;
            request.volume = PositionGetDouble(POSITION_VOLUME);
            request.type = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? 
                          ORDER_TYPE_SELL : ORDER_TYPE_BUY;
            request.price = (request.type == ORDER_TYPE_BUY) ? 
                           SymbolInfoDouble(symbol, SYMBOL_ASK) : 
                           SymbolInfoDouble(symbol, SYMBOL_BID);
            request.deviation = 10;
            
            if(OrderSend(request, result))
            {
               WriteResult(signal_id, "success", result.deal, "Position closed");
               return;
            }
         }
      }
   }
   
   WriteResult(signal_id, "error", 0, "No position found");
}

//+------------------------------------------------------------------+
//| Write trade result                                               |
//+------------------------------------------------------------------+
void WriteResult(string signal_id, string status, ulong ticket, string message)
{
   string result = StringFormat(
      "{\"signal_id\":\"%s\",\"status\":\"%s\",\"ticket\":%d," +
      "\"message\":\"%s\",\"timestamp\":\"%s\"," +
      "\"account\":{\"balance\":%.2f,\"equity\":%.2f," +
      "\"margin\":%.2f,\"free_margin\":%.2f,\"profit\":%.2f}}",
      signal_id, status, ticket, message,
      TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS),
      AccountInfoDouble(ACCOUNT_BALANCE),
      AccountInfoDouble(ACCOUNT_EQUITY),
      AccountInfoDouble(ACCOUNT_MARGIN),
      AccountInfoDouble(ACCOUNT_MARGIN_FREE),
      AccountInfoDouble(ACCOUNT_PROFIT)
   );
   
   int handle = FileOpen("BITTEN\\trade_result.txt", FILE_WRITE|FILE_TXT|FILE_ANSI);
   if(handle != INVALID_HANDLE)
   {
      FileWriteString(handle, result);
      FileClose(handle);
   }
}

//+------------------------------------------------------------------+
//| Extract JSON value                                               |
//+------------------------------------------------------------------+
string ExtractValue(string json, string key)
{
   int key_pos = StringFind(json, "\"" + key + "\":");
   if(key_pos < 0) return "";
   
   int start = StringFind(json, ":", key_pos) + 1;
   int end = StringFind(json, ",", start);
   if(end < 0) end = StringFind(json, "}", start);
   
   string value = StringSubstr(json, start, end - start);
   StringTrimLeft(value);
   StringTrimRight(value);
   
   if(StringGetCharacter(value, 0) == '"')
   {
      value = StringSubstr(value, 1, StringLen(value) - 2);
   }
   
   return value;
}

//+------------------------------------------------------------------+
//| Get error description                                            |
//+------------------------------------------------------------------+
string GetErrorDescription(int code)
{
   switch(code)
   {
      case 10004: return "Requote";
      case 10006: return "Request rejected";
      case 10009: return "Request completed";
      case 10013: return "Invalid request";
      case 10014: return "Invalid volume";
      case 10015: return "Invalid price";
      case 10016: return "Invalid stops";
      case 10019: return "Not enough money";
      case 10030: return "Invalid order type";
      default: return "Unknown error";
   }
}