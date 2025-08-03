//+------------------------------------------------------------------+
//|                          BITTENBridge_ZMQ.mq5                    |
//|                   Real-time ZMQ Trade Execution Bridge           |
//|                          No file I/O required                    |
//+------------------------------------------------------------------+
#property copyright "BITTEN Trading System"
#property version   "1.00"
#property strict

#include <Trade/Trade.mqh>

//+------------------------------------------------------------------+
//| DLL IMPORTS - Using ZMQ DLL                                      |
//+------------------------------------------------------------------+
#import "libzmq.dll"
   long zmq_ctx_new();
   long zmq_socket(long context, int type);
   int zmq_connect(long socket, uchar &endpoint[]);
   int zmq_setsockopt(long socket, int option_name, uchar &option_value[], int option_len);
   int zmq_recv(long socket, uchar &buffer[], int length, int flags);
   int zmq_send(long socket, uchar &buffer[], int length, int flags);
   int zmq_close(long socket);
   int zmq_ctx_term(long context);
#import

//+------------------------------------------------------------------+
//| ZMQ Constants                                                    |
//+------------------------------------------------------------------+
#define ZMQ_SUB      2      // Subscriber socket type
#define ZMQ_PUSH     8      // Push socket type
#define ZMQ_SUBSCRIBE 6     // Subscribe option
#define ZMQ_DONTWAIT 1      // Non-blocking flag
#define ZMQ_RCVTIMEO 27     // Receive timeout

//+------------------------------------------------------------------+
//| Input Parameters                                                 |
//+------------------------------------------------------------------+
input string   fire_socket_url = "tcp://127.0.0.1:9001";      // Fire commands socket
input string   telemetry_socket_url = "tcp://127.0.0.1:9101"; // Telemetry push socket
input string   uuid = "user-001";                             // Unique user identifier
input int      check_interval = 100;                          // Check interval (ms)
input bool     enable_telemetry = true;                       // Enable telemetry
input double   default_lot_size = 0.1;                        // Default lot size

//+------------------------------------------------------------------+
//| Global Variables                                                 |
//+------------------------------------------------------------------+
CTrade trade;
long ctx = 0;
long fire_sub = 0;
long telemetry_push = 0;
uchar recv_buffer[2048];
datetime last_telemetry_time = 0;
int telemetry_interval = 1000; // Send telemetry every 1 second

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("====================================================");
   Print("BITTEN ZMQ Bridge - Real-time Trade Execution");
   Print("====================================================");
   
   // Initialize ZMQ context
   ctx = zmq_ctx_new();
   if(ctx == 0)
   {
      Print("❌ Failed to create ZMQ context");
      return INIT_FAILED;
   }
   
   // Create fire command subscriber socket
   fire_sub = zmq_socket(ctx, ZMQ_SUB);
   if(fire_sub == 0)
   {
      Print("❌ Failed to create fire subscriber socket");
      zmq_ctx_term(ctx);
      return INIT_FAILED;
   }
   
   // Connect to fire commands
   uchar fire_endpoint[];
   StringToCharArray(fire_socket_url, fire_endpoint);
   if(zmq_connect(fire_sub, fire_endpoint) != 0)
   {
      Print("❌ Failed to connect to fire socket: ", fire_socket_url);
      zmq_close(fire_sub);
      zmq_ctx_term(ctx);
      return INIT_FAILED;
   }
   
   // Subscribe to all messages
   uchar filter[] = {0};
   zmq_setsockopt(fire_sub, ZMQ_SUBSCRIBE, filter, 0);
   
   // Set receive timeout
   int timeout = 0; // Non-blocking
   uchar timeout_bytes[4];
   timeout_bytes[0] = (uchar)(timeout & 0xFF);
   timeout_bytes[1] = (uchar)((timeout >> 8) & 0xFF);
   timeout_bytes[2] = (uchar)((timeout >> 16) & 0xFF);
   timeout_bytes[3] = (uchar)((timeout >> 24) & 0xFF);
   zmq_setsockopt(fire_sub, ZMQ_RCVTIMEO, timeout_bytes, 4);
   
   // Create telemetry push socket
   if(enable_telemetry)
   {
      telemetry_push = zmq_socket(ctx, ZMQ_PUSH);
      if(telemetry_push == 0)
      {
         Print("⚠️ Failed to create telemetry socket");
      }
      else
      {
         uchar telemetry_endpoint[];
         StringToCharArray(telemetry_socket_url, telemetry_endpoint);
         if(zmq_connect(telemetry_push, telemetry_endpoint) != 0)
         {
            Print("⚠️ Failed to connect to telemetry socket");
            zmq_close(telemetry_push);
            telemetry_push = 0;
         }
      }
   }
   
   Print("✅ ZMQ Bridge initialized");
   Print("📡 Fire commands: ", fire_socket_url);
   Print("📊 Telemetry: ", telemetry_socket_url);
   Print("🆔 UUID: ", uuid);
   
   // Start timer for periodic checks
   EventSetMillisecondTimer(check_interval);
   
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   
   if(fire_sub != 0)
   {
      zmq_close(fire_sub);
   }
   
   if(telemetry_push != 0)
   {
      zmq_close(telemetry_push);
   }
   
   if(ctx != 0)
   {
      zmq_ctx_term(ctx);
   }
   
   Print("ZMQ Bridge shutdown complete");
}

//+------------------------------------------------------------------+
//| Timer function                                                   |
//+------------------------------------------------------------------+
void OnTimer()
{
   CheckForFireCommands();
   
   // Send telemetry periodically
   if(enable_telemetry && telemetry_push != 0)
   {
      datetime current_time = TimeCurrent();
      if(current_time - last_telemetry_time >= telemetry_interval)
      {
         SendTelemetry();
         last_telemetry_time = current_time;
      }
   }
}

//+------------------------------------------------------------------+
//| Check for incoming fire commands                                 |
//+------------------------------------------------------------------+
void CheckForFireCommands()
{
   if(fire_sub == 0) return;
   
   // Try to receive message (non-blocking)
   int bytes = zmq_recv(fire_sub, recv_buffer, 2048, ZMQ_DONTWAIT);
   
   if(bytes > 0)
   {
      // Convert to string
      string message = CharArrayToString(recv_buffer, 0, bytes);
      Print("🔥 FIRE COMMAND RECEIVED: ", message);
      
      // Parse and execute trade
      ExecuteFireCommand(message);
   }
}

//+------------------------------------------------------------------+
//| Send telemetry data                                             |
//+------------------------------------------------------------------+
void SendTelemetry()
{
   if(telemetry_push == 0) return;
   
   // Prepare telemetry data
   string telemetry = StringFormat(
      "{\"uuid\":\"%s\",\"balance\":%.2f,\"equity\":%.2f,\"margin\":%.2f,\"free_margin\":%.2f,\"profit\":%.2f,\"positions\":%d,\"timestamp\":%d}",
      uuid,
      AccountInfoDouble(ACCOUNT_BALANCE),
      AccountInfoDouble(ACCOUNT_EQUITY),
      AccountInfoDouble(ACCOUNT_MARGIN),
      AccountInfoDouble(ACCOUNT_MARGIN_FREE),
      AccountInfoDouble(ACCOUNT_PROFIT),
      PositionsTotal(),
      TimeCurrent()
   );
   
   // Send telemetry
   uchar send_buf[];
   StringToCharArray(telemetry, send_buf);
   int result = zmq_send(telemetry_push, send_buf, StringLen(telemetry), ZMQ_DONTWAIT);
   
   if(result > 0)
   {
      // Telemetry sent successfully (silent)
   }
}

//+------------------------------------------------------------------+
//| Execute fire command                                             |
//+------------------------------------------------------------------+
void ExecuteFireCommand(string command)
{
   // Parse JSON command
   // Expected format: {"uuid":"user-001","action":"BUY","symbol":"XAUUSD","lot":0.1,"tp":40,"sl":20}
   
   // Simple parsing (for production, use proper JSON parser)
   string action = "";
   string symbol = "";
   double lot = default_lot_size;
   double tp_points = 0;
   double sl_points = 0;
   
   // Extract action
   int action_pos = StringFind(command, "\"action\":\"");
   if(action_pos >= 0)
   {
      int start = action_pos + 10;
      int end = StringFind(command, "\"", start);
      if(end > start)
      {
         action = StringSubstr(command, start, end - start);
      }
   }
   
   // Extract symbol
   int symbol_pos = StringFind(command, "\"symbol\":\"");
   if(symbol_pos >= 0)
   {
      int start = symbol_pos + 10;
      int end = StringFind(command, "\"", start);
      if(end > start)
      {
         symbol = StringSubstr(command, start, end - start);
      }
   }
   
   // Extract lot size
   int lot_pos = StringFind(command, "\"lot\":");
   if(lot_pos >= 0)
   {
      int start = lot_pos + 6;
      int end = StringFind(command, ",", start);
      if(end < 0) end = StringFind(command, "}", start);
      if(end > start)
      {
         lot = StringToDouble(StringSubstr(command, start, end - start));
      }
   }
   
   // Extract TP
   int tp_pos = StringFind(command, "\"tp\":");
   if(tp_pos >= 0)
   {
      int start = tp_pos + 5;
      int end = StringFind(command, ",", start);
      if(end < 0) end = StringFind(command, "}", start);
      if(end > start)
      {
         tp_points = StringToDouble(StringSubstr(command, start, end - start));
      }
   }
   
   // Extract SL
   int sl_pos = StringFind(command, "\"sl\":");
   if(sl_pos >= 0)
   {
      int start = sl_pos + 5;
      int end = StringFind(command, ",", start);
      if(end < 0) end = StringFind(command, "}", start);
      if(end > start)
      {
         sl_points = StringToDouble(StringSubstr(command, start, end - start));
      }
   }
   
   // Validate inputs
   if(symbol == "" || (action != "BUY" && action != "SELL"))
   {
      Print("❌ Invalid command format");
      SendResult(false, "Invalid command format", 0);
      return;
   }
   
   // Calculate TP/SL prices
   double price = 0;
   double tp_price = 0;
   double sl_price = 0;
   
   if(action == "BUY")
   {
      price = SymbolInfoDouble(symbol, SYMBOL_ASK);
      if(tp_points > 0) tp_price = price + tp_points * SymbolInfoDouble(symbol, SYMBOL_POINT);
      if(sl_points > 0) sl_price = price - sl_points * SymbolInfoDouble(symbol, SYMBOL_POINT);
   }
   else // SELL
   {
      price = SymbolInfoDouble(symbol, SYMBOL_BID);
      if(tp_points > 0) tp_price = price - tp_points * SymbolInfoDouble(symbol, SYMBOL_POINT);
      if(sl_points > 0) sl_price = price + sl_points * SymbolInfoDouble(symbol, SYMBOL_POINT);
   }
   
   // Execute trade
   bool result = false;
   if(action == "BUY")
   {
      result = trade.Buy(lot, symbol, price, sl_price, tp_price, "ZMQ Fire");
   }
   else
   {
      result = trade.Sell(lot, symbol, price, sl_price, tp_price, "ZMQ Fire");
   }
   
   // Send result
   if(result)
   {
      ulong ticket = trade.ResultDeal();
      Print("✅ Trade executed: ", action, " ", symbol, " Ticket: ", ticket);
      SendResult(true, "Trade executed", ticket);
   }
   else
   {
      Print("❌ Trade failed: ", trade.ResultRetcode());
      SendResult(false, trade.ResultComment(), 0);
   }
}

//+------------------------------------------------------------------+
//| Send trade result back                                          |
//+------------------------------------------------------------------+
void SendResult(bool success, string message, ulong ticket)
{
   if(telemetry_push == 0) return;
   
   // Prepare result message
   string result = StringFormat(
      "{\"type\":\"trade_result\",\"uuid\":\"%s\",\"success\":%s,\"message\":\"%s\",\"ticket\":%d,\"timestamp\":%d}",
      uuid,
      success ? "true" : "false",
      message,
      ticket,
      TimeCurrent()
   );
   
   // Send result
   uchar send_buf[];
   StringToCharArray(result, send_buf);
   zmq_send(telemetry_push, send_buf, StringLen(result), ZMQ_DONTWAIT);
}

//+------------------------------------------------------------------+
//| Tick function                                                    |
//+------------------------------------------------------------------+
void OnTick()
{
   // Check for commands on every tick as well
   CheckForFireCommands();
}