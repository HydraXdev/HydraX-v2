//+------------------------------------------------------------------+
//|                          BITTENBridge_TradeExecutor_ZMQ_v7_CLIENT.mq5 |
//|                   CLIENT Architecture - Connects to Controller    |
//|                          NO BINDING - Only Outward Connections    |
//+------------------------------------------------------------------+
#property copyright "BITTEN Trading System"
#property version   "7.00"
#property strict

//+------------------------------------------------------------------+
//| DLL IMPORTS - Using ZMQ DLL                                      |
//+------------------------------------------------------------------+
#import "libzmq.dll"
   // Context functions
   long zmq_ctx_new();
   int zmq_ctx_term(long context);
   
   // Socket functions
   long zmq_socket(long context, int type);
   int zmq_close(long socket);
   int zmq_connect(long socket, uchar &endpoint[]);  // CONNECT, not bind
   
   // Socket options
   int zmq_setsockopt(long socket, int option, uchar &value[], int size);
   
   // Messaging
   int zmq_send(long socket, uchar &data[], int size, int flags);
   int zmq_recv(long socket, uchar &buffer[], int size, int flags);
   
   // Error handling
   int zmq_errno();
#import

//+------------------------------------------------------------------+
//| ZMQ CONSTANTS                                                    |
//+------------------------------------------------------------------+
#define ZMQ_PUSH     8      // Push socket type (send data)
#define ZMQ_PULL     7      // Pull socket type (receive commands)
#define ZMQ_SNDHWM   23     // Send high water mark
#define ZMQ_RCVHWM   24     // Receive high water mark
#define ZMQ_LINGER   17     // Linger period
#define ZMQ_SNDTIMEO 28     // Send timeout
#define ZMQ_RCVTIMEO 27     // Receive timeout
#define ZMQ_DONTWAIT 1      // Non-blocking flag

//+------------------------------------------------------------------+
//| CONFIGURATION                                                    |
//+------------------------------------------------------------------+
input string  InpControllerIP = "134.199.204.67";     // Controller IP Address
input int     InpDataPort = 5555;                     // Port to send data (PUSH)
input int     InpCommandPort = 5556;                  // Port to receive commands (PULL)
input string  InpEAIdentifier = "MT5_EA";              // Unique EA identifier
input int     InpStreamInterval = 100;                 // Stream interval (ms)
input int     InpCheckInterval = 1000;                 // Command check interval (ms)
input bool    InpEnableAllPairs = true;               // Stream all pairs
input bool    InpVerboseLog = false;                  // Verbose logging

//+------------------------------------------------------------------+
//| GLOBAL VARIABLES                                                 |
//+------------------------------------------------------------------+
// ZMQ handles
long g_zmq_context = 0;
long g_zmq_push = 0;     // For sending data to controller
long g_zmq_pull = 0;     // For receiving commands from controller
bool g_zmq_initialized = false;

// Timing
ulong g_last_stream_time = 0;
ulong g_last_check_time = 0;
ulong g_last_heartbeat = 0;

// Statistics
ulong g_messages_sent = 0;
ulong g_commands_received = 0;
ulong g_errors_count = 0;

// Trading pairs
string g_pairs[] = {"EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD",
                    "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY",
                    "XAUUSD", "GBPNZD", "GBPAUD", "EURAUD", "GBPCHF",
                    "AUDJPY"};

// File paths for trade execution
string g_fire_file;
string g_result_file;

// EA identification
string g_ea_id;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("====================================================");
   Print("BITTEN Bridge v7.0 CLIENT - ZMQ Outward Connections");
   Print("====================================================");
   
   // Generate unique EA ID
   g_ea_id = StringFormat("%s_%d_%d", InpEAIdentifier, 
                         AccountInfoInteger(ACCOUNT_LOGIN),
                         TimeLocal());
   
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
      Print("❌ CRITICAL: ZMQ initialization failed");
      return(INIT_FAILED);
   }
   
   // Set timer
   EventSetMillisecondTimer(50);
   
   Print("✅ EA Initialized Successfully");
   Print("📡 Controller: ", InpControllerIP);
   Print("🆔 EA ID: ", g_ea_id);
   
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Initialize ZMQ CLIENT connections                                |
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
   
   // Create PUSH socket (send data to controller)
   g_zmq_push = zmq_socket(g_zmq_context, ZMQ_PUSH);
   if(g_zmq_push == 0)
   {
      Print("❌ ZMQ Error: Failed to create PUSH socket");
      zmq_ctx_term(g_zmq_context);
      return false;
   }
   
   // Set PUSH socket options
   int hwm = 50000;
   uchar hwm_bytes[4];
   for(int i = 0; i < 4; i++)
      hwm_bytes[i] = (uchar)((hwm >> (i * 8)) & 0xFF);
   zmq_setsockopt(g_zmq_push, ZMQ_SNDHWM, hwm_bytes, 4);
   
   // Connect PUSH socket to controller
   string push_endpoint = StringFormat("tcp://%s:%d", InpControllerIP, InpDataPort);
   uchar push_addr[];
   StringToCharArray(push_endpoint, push_addr);
   ArrayResize(push_addr, ArraySize(push_addr) - 1);
   
   if(zmq_connect(g_zmq_push, push_addr) != 0)
   {
      Print("❌ ZMQ Error: Failed to connect PUSH to ", push_endpoint);
      zmq_close(g_zmq_push);
      zmq_ctx_term(g_zmq_context);
      return false;
   }
   Print("✅ Connected PUSH to controller at ", push_endpoint);
   
   // Create PULL socket (receive commands from controller)
   g_zmq_pull = zmq_socket(g_zmq_context, ZMQ_PULL);
   if(g_zmq_pull == 0)
   {
      Print("❌ ZMQ Error: Failed to create PULL socket");
      zmq_close(g_zmq_push);
      zmq_ctx_term(g_zmq_context);
      return false;
   }
   
   // Set PULL socket options
   zmq_setsockopt(g_zmq_pull, ZMQ_RCVHWM, hwm_bytes, 4);
   
   // Set receive timeout (100ms)
   int timeout = 100;
   uchar timeout_bytes[4];
   for(int i = 0; i < 4; i++)
      timeout_bytes[i] = (uchar)((timeout >> (i * 8)) & 0xFF);
   zmq_setsockopt(g_zmq_pull, ZMQ_RCVTIMEO, timeout_bytes, 4);
   
   // Connect PULL socket to controller
   string pull_endpoint = StringFormat("tcp://%s:%d", InpControllerIP, InpCommandPort);
   uchar pull_addr[];
   StringToCharArray(pull_endpoint, pull_addr);
   ArrayResize(pull_addr, ArraySize(pull_addr) - 1);
   
   if(zmq_connect(g_zmq_pull, pull_addr) != 0)
   {
      Print("❌ ZMQ Error: Failed to connect PULL to ", pull_endpoint);
      zmq_close(g_zmq_push);
      zmq_close(g_zmq_pull);
      zmq_ctx_term(g_zmq_context);
      return false;
   }
   Print("✅ Connected PULL to controller at ", pull_endpoint);
   
   g_zmq_initialized = true;
   
   // Send startup message
   SendStartupMessage();
   
   return true;
}

//+------------------------------------------------------------------+
//| Send startup message to controller                               |
//+------------------------------------------------------------------+
void SendStartupMessage()
{
   string message = StringFormat(
      "{\"ea_id\":\"%s\",\"type\":\"startup\",\"account\":%d," +
      "\"broker\":\"%s\",\"timestamp\":%d}",
      g_ea_id,
      AccountInfoInteger(ACCOUNT_LOGIN),
      AccountInfoString(ACCOUNT_COMPANY),
      TimeGMT()
   );
   
   SendToController(message);
}

//+------------------------------------------------------------------+
//| Send data to controller via PUSH socket                          |
//+------------------------------------------------------------------+
bool SendToController(string message)
{
   if(!g_zmq_initialized)
      return false;
      
   uchar data[];
   StringToCharArray(message, data);
   ArrayResize(data, ArraySize(data) - 1);
   
   int result = zmq_send(g_zmq_push, data, ArraySize(data), ZMQ_DONTWAIT);
   
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
      if(g_errors_count % 100 == 0)
         Print("⚠️ ZMQ send errors: ", g_errors_count);
      return false;
   }
}

//+------------------------------------------------------------------+
//| Stream market data for symbol                                    |
//+------------------------------------------------------------------+
void StreamSymbolData(string symbol)
{
   if(!SymbolSelect(symbol, true))
      return;
      
   double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
   
   if(bid <= 0 || ask <= 0)
      return;
      
   long volume = SymbolInfoInteger(symbol, SYMBOL_VOLUME);
   double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
   double spread = (ask - bid) / point;
   
   // Build message for controller
   string message = StringFormat(
      "{\"ea_id\":\"%s\",\"type\":\"market_data\"," +
      "\"data\":{\"symbol\":\"%s\",\"bid\":%.5f,\"ask\":%.5f," +
      "\"spread\":%.1f,\"volume\":%d,\"timestamp\":%d," +
      "\"broker\":\"%s\",\"source\":\"MT5_LIVE\"}}",
      g_ea_id, symbol, bid, ask, spread, volume,
      TimeGMT(), AccountInfoString(ACCOUNT_COMPANY)
   );
   
   SendToController(message);
}

//+------------------------------------------------------------------+
//| Check for commands from controller                               |
//+------------------------------------------------------------------+
void CheckControllerCommands()
{
   if(!g_zmq_initialized)
      return;
      
   uchar buffer[4096];
   int size = zmq_recv(g_zmq_pull, buffer, 4096, ZMQ_DONTWAIT);
   
   if(size > 0)
   {
      string command = CharArrayToString(buffer, 0, size);
      g_commands_received++;
      
      if(InpVerboseLog)
         Print("📥 Command from controller: ", command);
         
      ProcessControllerCommand(command);
   }
}

//+------------------------------------------------------------------+
//| Process command from controller                                  |
//+------------------------------------------------------------------+
void ProcessControllerCommand(string command)
{
   // Parse JSON command
   string cmd_type = ExtractValue(command, "type");
   
   if(cmd_type == "ping")
   {
      // Respond with pong
      string response = StringFormat(
         "{\"ea_id\":\"%s\",\"type\":\"pong\",\"timestamp\":%d}",
         g_ea_id, TimeGMT()
      );
      SendToController(response);
   }
   else if(cmd_type == "trade")
   {
      // Execute trade command
      string signal_data = ExtractValue(command, "signal");
      if(signal_data != "")
      {
         // Write to fire.txt for execution
         int handle = FileOpen("BITTEN\\fire.txt", FILE_WRITE|FILE_TXT|FILE_ANSI);
         if(handle != INVALID_HANDLE)
         {
            FileWriteString(handle, signal_data);
            FileClose(handle);
            Print("🔥 Trade signal written to fire.txt");
         }
      }
   }
   else if(cmd_type == "config")
   {
      // Update configuration
      Print("📋 Configuration update received");
   }
}

//+------------------------------------------------------------------+
//| Send heartbeat to controller                                     |
//+------------------------------------------------------------------+
void SendHeartbeat()
{
   string message = StringFormat(
      "{\"ea_id\":\"%s\",\"type\":\"heartbeat\"," +
      "\"balance\":%.2f,\"equity\":%.2f,\"positions\":%d," +
      "\"timestamp\":%d}",
      g_ea_id,
      AccountInfoDouble(ACCOUNT_BALANCE),
      AccountInfoDouble(ACCOUNT_EQUITY),
      PositionsTotal(),
      TimeGMT()
   );
   
   SendToController(message);
}

//+------------------------------------------------------------------+
//| Timer event handler                                              |
//+------------------------------------------------------------------+
void OnTimer()
{
   ulong current_time = GetTickCount();
   
   // Stream market data
   if(current_time - g_last_stream_time >= InpStreamInterval)
   {
      if(InpEnableAllPairs)
      {
         for(int i = 0; i < ArraySize(g_pairs); i++)
            StreamSymbolData(g_pairs[i]);
      }
      else
      {
         StreamSymbolData(Symbol());
      }
      
      g_last_stream_time = current_time;
   }
   
   // Check for commands
   if(current_time - g_last_check_time >= InpCheckInterval)
   {
      CheckControllerCommands();
      CheckFireSignal();  // Still check for local fire.txt
      g_last_check_time = current_time;
   }
   
   // Send heartbeat every 30 seconds
   if(current_time - g_last_heartbeat >= 30000)
   {
      SendHeartbeat();
      g_last_heartbeat = current_time;
   }
}

//+------------------------------------------------------------------+
//| Check for local fire signal                                      |
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
      ProcessTradeSignal(signal);
      FileDelete("BITTEN\\fire.txt");
   }
}

//+------------------------------------------------------------------+
//| Process trade signal                                             |
//+------------------------------------------------------------------+
void ProcessTradeSignal(string signal)
{
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
      
      // Send execution confirmation to controller
      string confirm = StringFormat(
         "{\"ea_id\":\"%s\",\"type\":\"trade_result\"," +
         "\"signal_id\":\"%s\",\"status\":\"success\"," +
         "\"ticket\":%d,\"price\":%.5f}",
         g_ea_id, signal_id, result.deal, result.price
      );
      SendToController(confirm);
   }
   else
   {
      WriteResult(signal_id, "error", 0, 
                  StringFormat("Error %d", result.retcode));
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
            request.position = ticket;
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
      "\"ea_id\":\"%s\"}",
      signal_id, status, ticket, message,
      TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS),
      g_ea_id
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
//| Expert deinitialization                                          |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   if(g_zmq_initialized)
   {
      // Send shutdown message
      string message = StringFormat(
         "{\"ea_id\":\"%s\",\"type\":\"shutdown\",\"timestamp\":%d}",
         g_ea_id, TimeGMT()
      );
      SendToController(message);
   }
   
   // Clean up ZMQ
   if(g_zmq_push != 0)
   {
      zmq_close(g_zmq_push);
      g_zmq_push = 0;
   }
   
   if(g_zmq_pull != 0)
   {
      zmq_close(g_zmq_pull);
      g_zmq_pull = 0;
   }
   
   if(g_zmq_context != 0)
   {
      zmq_ctx_term(g_zmq_context);
      g_zmq_context = 0;
   }
   
   EventKillTimer();
   
   Print("====================================================");
   Print("EA Shutdown - Messages sent: ", g_messages_sent);
   Print("Commands received: ", g_commands_received);
   Print("====================================================");
}