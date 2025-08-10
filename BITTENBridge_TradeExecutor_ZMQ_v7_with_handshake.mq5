//+------------------------------------------------------------------+
//|                        BITTENBridge_TradeExecutor_ZMQ_v7.mq5     |
//|                     BITTEN Trading System - ZMQ Controller       |
//|                  Modern Architecture with Full ZMQ Integration   |
//|                  WITH TICK DATA STREAMING + OHLC CANDLES         |
//|                  + ACCOUNT HANDSHAKE VERIFICATION                |
//+------------------------------------------------------------------+
#property copyright "BITTEN Trading System"
#property link      "https://bitten.trading"
#property version   "7.01"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\SymbolInfo.mqh>

#import "libzmq.dll"
long zmq_ctx_new();
int zmq_ctx_term(long context);
long zmq_socket(long context, int type);
int zmq_close(long socket);
int zmq_bind(long socket, uchar &endpoint[]);
int zmq_connect(long socket, uchar &endpoint[]);
int zmq_setsockopt(long socket, int option, uchar &value[], int size);
int zmq_getsockopt(long socket, int option, uchar &value[], int &size);
int zmq_send(long socket, uchar &data[], int size, int flags);
int zmq_recv(long socket, uchar &buffer[], int size, int flags);
int zmq_poll(long items, int nitems, long timeout);
int zmq_errno();
void zmq_version(int &major, int &minor, int &patch);
#import

#define ZMQ_REQ      3
#define ZMQ_REP      4
#define ZMQ_PUB      1
#define ZMQ_SUB      2
#define ZMQ_PUSH     8
#define ZMQ_PULL     7
#define ZMQ_DONTWAIT 1
#define ZMQ_SNDMORE  2
#define ZMQ_RCVTIMEO 27
#define ZMQ_SNDTIMEO 28
#define ZMQ_LINGER   17
#define ZMQ_RCVHWM   24
#define ZMQ_SNDHWM   23
#define ZMQ_SUBSCRIBE 6

#define BACKEND_ENDPOINT   "tcp://134.199.204.67:5555"
#define HEARTBEAT_ENDPOINT "tcp://134.199.204.67:5556"
#define BUFFER_SIZE        4096
#define RECV_TIMEOUT       1000
#define HEARTBEAT_INTERVAL 5000
#define RECONNECT_DELAY    3000
#define MAGIC_NUMBER       20250101
#define MAX_SLIPPAGE       10
#define DEFAULT_LOT        0.01

long g_zmq_context = 0;
long g_zmq_command_socket = 0;
long g_zmq_heartbeat_socket = 0;
bool g_zmq_connected = false;
bool g_shutdown_requested = false;
datetime g_last_recv_time = 0;
datetime g_last_heartbeat_time = 0;
int g_reconnect_attempts = 0;

CTrade g_trade;
CPositionInfo g_position;
CSymbolInfo g_symbol;

ulong g_messages_received = 0;
ulong g_messages_sent = 0;
ulong g_trades_executed = 0;
ulong g_errors_count = 0;

int OnInit()
{
Print("========================================================");
 Print("BITTEN Bridge ZMQ Controller v7.01 - With Tick Streaming + OHLC + Handshake");
 Print("========================================================");
 
 if(!TerminalInfoInteger(TERMINAL_DLLS_ALLOWED))
 {
    Alert("ERROR: DLL imports are disabled!");
    Alert("Enable: Tools → Options → Expert Advisors → Allow DLL imports");
    return(INIT_FAILED);
 }
 
 PrintZMQVersion();
 
 g_trade.SetExpertMagicNumber(MAGIC_NUMBER);
 g_trade.SetDeviationInPoints(MAX_SLIPPAGE);
 g_trade.SetTypeFilling(ORDER_FILLING_IOC);
 
 if(!InitializeZMQ())
 {
    Print("ERROR: Failed to initialize ZMQ");
    return(INIT_FAILED);
 }
 
 EventSetMillisecondTimer(100);
 
 SendStatusMessage("startup", "EA v7.01 initialized with tick streaming + OHLC + handshake");
 
 Print("✅  EA initialized and ready for commands");
 Print("📡 Backend endpoint: ", BACKEND_ENDPOINT);
 Print("💓 Heartbeat endpoint: ", HEARTBEAT_ENDPOINT);
 Print("📊 Tick streaming: ENABLED");
 Print("📈 OHLC candles: ENABLED");
 Print("🤝 Account handshake: ENABLED");
 
 return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
Print("========================================================");
 Print("Shutting down BITTEN Bridge ZMQ Controller...");
 Print("========================================================");
 
 if(g_zmq_connected)
 {
    SendStatusMessage("shutdown", GetDeinitReasonText(reason));
 }
 
 ShutdownZMQ();
 
 EventKillTimer();
 
 Print("📊 Session Statistics:");
 Print("   Messages received: ", g_messages_received);
 Print("   Messages sent: ", g_messages_sent);
 Print("   Trades executed: ", g_trades_executed);
 Print("   Errors: ", g_errors_count);
 Print("========================================================");
}

void OnTimer()
{
if(g_shutdown_requested)
 {
    ExpertRemove();
    return;
 }
 
 if(!g_zmq_connected || !IsZMQHealthy())
 {
    AttemptReconnect();
    return;
 }
 
 ProcessIncomingMessages();
 SendHeartbeatIfNeeded();

 // 🤝 BITTEN HANDSHAKE - Check for ACCOUNT_INFO file-based requests
 string account_request = "";
 if(FileIsExist("bitten_instructions.txt"))
 {
    int file_handle = FileOpen("bitten_instructions.txt", FILE_READ|FILE_TXT);
    if(file_handle != INVALID_HANDLE)
    {
       account_request = FileReadString(file_handle);
       FileClose(file_handle);
       FileDelete("bitten_instructions.txt"); // Clean up immediately
    }
 }
 
 if(StringFind(account_request, "ACCOUNT_INFO") >= 0)
 {
    ProcessAccountInfoRequest(account_request);
 }
}

void OnTick()
{
// Only send tick data if we're connected
 if(!g_zmq_connected) return;
 
 // Get current tick data
 double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
 double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
 double spread = (ask - bid) / _Point;
 long volume = SymbolInfoInteger(_Symbol, SYMBOL_VOLUME);
 
 // Format tick data as JSON
 string tick = StringFormat(
    "{\"type\":\"tick\",\"symbol\":\"%s\",\"bid\":%.5f,\"ask\":%.5f,\"spread\":%.1f,\"volume\":%d,\"timestamp\":%d}",
    _Symbol, bid, ask, spread, volume, TimeCurrent()
 );
 
 // Send via heartbeat socket (PUSH to port 5556)
 uchar buffer[];
 StringToCharArray(tick, buffer);
 ArrayResize(buffer, ArraySize(buffer) - 1);  // Remove null terminator
 
 int result = zmq_send(g_zmq_heartbeat_socket, buffer, ArraySize(buffer), 0);
 
 // Optional: Log first few ticks for debugging
 static int tick_count = 0;
 if(result >= 0 && tick_count < 5)
 {
    tick_count++;
    Print("📊 Sent tick #", tick_count, ": ", tick);
 }
 
 // Also send candle data periodically
 static datetime last_candle_send = 0;
 if(TimeCurrent() - last_candle_send >= 5) // Send candles every 5 seconds
 {
    SendCandleData();
    last_candle_send = TimeCurrent();
 }
}

//+------------------------------------------------------------------+
//| Send OHLC candle data for M1, M5, M15                           |
//+------------------------------------------------------------------+
void SendCandleData()
{
if(!g_zmq_connected) return;
 
 // Get OHLC data for M1, M5, and M15 timeframes
 MqlRates rates_m1[], rates_m5[], rates_m15[];
 
 // Copy last 10 candles for each timeframe
 int copied_m1 = CopyRates(_Symbol, PERIOD_M1, 0, 10, rates_m1);
 int copied_m5 = CopyRates(_Symbol, PERIOD_M5, 0, 10, rates_m5);
 int copied_m15 = CopyRates(_Symbol, PERIOD_M15, 0, 10, rates_m15);
 
 // Build candle batch JSON
 string candle_batch = "{\"type\":\"candle_batch\",\"symbol\":\"" + _Symbol + "\",\"timestamp\":" + IntegerToString(TimeCurrent()) + ",";
 
 // Add M1 candles
 candle_batch += "\"M1\":[";
 for(int i = 0; i < copied_m1 && i < 5; i++) // Send last 5 M1 candles
 {
    if(i > 0) candle_batch += ",";
    candle_batch += StringFormat(
       "{\"time\":%d,\"open\":%.5f,\"high\":%.5f,\"low\":%.5f,\"close\":%.5f,\"volume\":%d}",
       rates_m1[i].time, rates_m1[i].open, rates_m1[i].high,
       rates_m1[i].low, rates_m1[i].close, (int)rates_m1[i].tick_volume
    );
 }
 candle_batch += "],";
 
 // Add M5 candles
 candle_batch += "\"M5\":[";
 for(int i = 0; i < copied_m5 && i < 5; i++) // Send last 5 M5 candles
 {
    if(i > 0) candle_batch += ",";
    candle_batch += StringFormat(
       "{\"time\":%d,\"open\":%.5f,\"high\":%.5f,\"low\":%.5f,\"close\":%.5f,\"volume\":%d}",
       rates_m5[i].time, rates_m5[i].open, rates_m5[i].high,
       rates_m5[i].low, rates_m5[i].close, (int)rates_m5[i].tick_volume
    );
 }
 candle_batch += "],";
 
 // Add M15 candles
 candle_batch += "\"M15\":[";
 for(int i = 0; i < copied_m15 && i < 5; i++) // Send last 5 M15 candles
 {
    if(i > 0) candle_batch += ",";
    candle_batch += StringFormat(
       "{\"time\":%d,\"open\":%.5f,\"high\":%.5f,\"low\":%.5f,\"close\":%.5f,\"volume\":%d}",
       rates_m15[i].time, rates_m15[i].open, rates_m15[i].high,
       rates_m15[i].low, rates_m15[i].close, (int)rates_m15[i].tick_volume
    );
 }
 candle_batch += "]}";
 
 // Send via heartbeat socket
 uchar buffer[];
 StringToCharArray(candle_batch, buffer);
 ArrayResize(buffer, ArraySize(buffer) - 1);  // Remove null terminator
 
 int result = zmq_send(g_zmq_heartbeat_socket, buffer, ArraySize(buffer), 0);
 
 if(result >= 0)
 {
    static int candle_log_count = 0;
    if(candle_log_count < 3) // Log first 3 candle batches
    {
       candle_log_count++;
       Print("📈 Sent candle batch #", candle_log_count, " (", StringLen(candle_batch), " bytes)");
    }
 }
}

//+------------------------------------------------------------------+
//| BITTEN HANDSHAKE - Process account info requests                |
//+------------------------------------------------------------------+
void ProcessAccountInfoRequest(string request)
{
   Print("🤝 Processing BITTEN account info handshake request");
   
   string parts[];
   int count = StringSplit(request, ',', parts);
   
   if(count >= 2)
   {
      string request_id = parts[0];
      
      // Get real account information
      double balance = AccountInfoDouble(ACCOUNT_BALANCE);
      double equity = AccountInfoDouble(ACCOUNT_EQUITY);
      double margin = AccountInfoDouble(ACCOUNT_MARGIN);
      double free_margin = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
      string currency = AccountInfoString(ACCOUNT_CURRENCY);
      long leverage = AccountInfoInteger(ACCOUNT_LEVERAGE);
      long login = AccountInfoInteger(ACCOUNT_LOGIN);
      string broker = AccountInfoString(ACCOUNT_COMPANY);

      // Create JSON handshake response
      string json_response = StringFormat(
         "{"
         "\"id\":\"%s\","
         "\"type\":\"account_info\","
         "\"status\":\"success\","
         "\"timestamp\":\"%s\","
         "\"account\":{"
            "\"balance\":%.2f,"
            "\"equity\":%.2f,"
            "\"margin\":%.2f,"
            "\"free_margin\":%.2f,"
            "\"currency\":\"%s\","
            "\"leverage\":%d,"
            "\"login\":\"%d\","
            "\"broker\":\"%s\""
         "}"
         "}",
         request_id,
         TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS),
         balance, equity, margin, free_margin,
         currency, leverage, login, broker
      );

      WriteAccountInfoResponse(json_response);
      Print("✅ BITTEN handshake completed - Balance: ", DoubleToString(balance, 2));
   }
   else
   {
      Print("❌ Invalid BITTEN handshake request format");
   }
}

//+------------------------------------------------------------------+
//| BITTEN HANDSHAKE - Write account info response                  |
//+------------------------------------------------------------------+
void WriteAccountInfoResponse(string json_response)
{
   int file_handle = FileOpen("bitten_results.txt", FILE_WRITE|FILE_TXT);
   if(file_handle != INVALID_HANDLE)
   {
      FileWriteString(file_handle, json_response);
      FileClose(file_handle);
      Print("📤 BITTEN handshake response written to bitten_results.txt");
   }
   else
   {
      Print("❌ Failed to write BITTEN handshake response");
   }
}

bool InitializeZMQ()
{
g_zmq_context = zmq_ctx_new();
 if(g_zmq_context == 0)
 {
    Print("ERROR: Failed to create ZMQ context");
    return false;
 }
 
 g_zmq_command_socket = zmq_socket(g_zmq_context, ZMQ_PULL);
 if(g_zmq_command_socket == 0)
 {
    Print("ERROR: Failed to create command socket");
    zmq_ctx_term(g_zmq_context);
    return false;
 }
 
 g_zmq_heartbeat_socket = zmq_socket(g_zmq_context, ZMQ_PUSH);
 if(g_zmq_heartbeat_socket == 0)
 {
    Print("ERROR: Failed to create heartbeat socket");
    zmq_close(g_zmq_command_socket);
    zmq_ctx_term(g_zmq_context);
    return false;
 }
 
 if(!SetSocketOptions())
 {
    ShutdownZMQ();
    return false;
 }
 
 if(!ConnectSockets())
 {
    ShutdownZMQ();
    return false;
 }
 
 g_zmq_connected = true;
 g_last_recv_time = TimeCurrent();
 
 return true;
}

bool SetSocketOptions()
{
uchar timeout_bytes[4];
 int timeout = RECV_TIMEOUT;
 ArrayFromInt(timeout_bytes, timeout);
 
 if(zmq_setsockopt(g_zmq_command_socket, ZMQ_RCVTIMEO, timeout_bytes, 4) != 0)
 {
    Print("ERROR: Failed to set receive timeout");
    return false;
 }
 
 uchar linger_bytes[4];
 ArrayFromInt(linger_bytes, 0);
 
 if(zmq_setsockopt(g_zmq_command_socket, ZMQ_LINGER, linger_bytes, 4) != 0)
 {
    Print("ERROR: Failed to set linger");
    return false;
 }
 
 if(zmq_setsockopt(g_zmq_heartbeat_socket, ZMQ_LINGER, linger_bytes, 4) != 0)
 {
    Print("ERROR: Failed to set heartbeat linger");
    return false;
 }
 
 return true;
}

bool ConnectSockets()
{
uchar backend_endpoint[];
 StringToCharArray(BACKEND_ENDPOINT, backend_endpoint);
 ArrayResize(backend_endpoint, ArraySize(backend_endpoint) - 1);
 
 if(zmq_connect(g_zmq_command_socket, backend_endpoint) != 0)
 {
    Print("ERROR: Failed to connect to backend: ", BACKEND_ENDPOINT);
    return false;
 }
 
 uchar heartbeat_endpoint[];
 StringToCharArray(HEARTBEAT_ENDPOINT, heartbeat_endpoint);
 ArrayResize(heartbeat_endpoint, ArraySize(heartbeat_endpoint) - 1);
 
 if(zmq_connect(g_zmq_heartbeat_socket, heartbeat_endpoint) != 0)
 {
    Print("ERROR: Failed to connect to heartbeat: ", HEARTBEAT_ENDPOINT);
    return false;
 }
 
 Print("✅  Connected to backend controller");
 
 return true;
}

void ShutdownZMQ()
{
g_zmq_connected = false;
 
 if(g_zmq_command_socket != 0)
 {
    zmq_close(g_zmq_command_socket);
    g_zmq_command_socket = 0;
 }
 
 if(g_zmq_heartbeat_socket != 0)
 {
    zmq_close(g_zmq_heartbeat_socket);
    g_zmq_heartbeat_socket = 0;
 }
 
 if(g_zmq_context != 0)
 {
    zmq_ctx_term(g_zmq_context);
    g_zmq_context = 0;
 }
}

void ProcessIncomingMessages()
{
uchar buffer[];
 ArrayResize(buffer, BUFFER_SIZE);
 
 int bytes_received = zmq_recv(g_zmq_command_socket, buffer, BUFFER_SIZE - 1, 0);
 
 if(bytes_received > 0)
 {
    ArrayResize(buffer, bytes_received);
    string message = CharArrayToString(buffer);
    Print("📥 Received from ZMQ: ", message);  // DEBUG: Show raw message
    
    g_messages_received++;
    g_last_recv_time = TimeCurrent();
    
    HandleMessage(message);
 }
 else if(bytes_received < 0)
 {
    int error = zmq_errno();
    if(error != 11 && error != 35)
    {
       Print("ERROR: zmq_recv failed, errno: ", error);
       g_errors_count++;
    }
 }
}

void HandleMessage(string message)
{
Print("📥 Received: ", message);
 
 string msg_type = GetJsonValue(message, "type");
 
 if(msg_type == "")
 {
    Print("⚠️ Empty msg_type in ZMQ message: ", message);
 }
 
 if(msg_type == "signal")
 {
    HandleSignal(message);
 }
 else if(msg_type == "command")
 {
    HandleCommand(message);
 }
 else if(msg_type == "config")
 {
    HandleConfig(message);
 }
 else if(msg_type == "ping")
 {
    SendPong();
 }
 else
 {
    Print("WARNING: Unknown message type: ", msg_type);
 }
}

void HandleSignal(string json)
{
string symbol = GetJsonValue(json, "symbol");
 string action = GetJsonValue(json, "action");
 double lot = StringToDouble(GetJsonValue(json, "lot"));
 double sl = StringToDouble(GetJsonValue(json, "sl"));
 double tp = StringToDouble(GetJsonValue(json, "tp"));
 string signal_id = GetJsonValue(json, "signal_id");
 
 if(symbol == "" || action == "")
 {
    SendErrorResponse(signal_id, "Invalid signal parameters");
    return;
 }
 
 if(lot <= 0) lot = DEFAULT_LOT;
 
 if(action == "buy" || action == "sell")
 {
    ExecuteTrade(symbol, action, lot, sl, tp, signal_id);
 }
 else if(action == "close")
 {
    ClosePosition(symbol, signal_id);
 }
 else if(action == "close_all")
 {
    CloseAllPositions(signal_id);
 }
 else
 {
    SendErrorResponse(signal_id, "Unknown action: " + action);
 }
}

void ExecuteTrade(string symbol, string action, double lot, double sl, double tp, string signal_id)
{
if(!g_symbol.Name(symbol))
 {
    SendErrorResponse(signal_id, "Invalid symbol: " + symbol);
    return;
 }
 
 g_symbol.RefreshRates();
 
 ENUM_ORDER_TYPE order_type = (action == "buy") ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
 double price = (action == "buy") ? g_symbol.Ask() : g_symbol.Bid();
 
 double norm_volume = NormalizeDouble(lot, 2);
 double min_volume = g_symbol.LotsMin();
 double max_volume = g_symbol.LotsMax();
 double volume_step = g_symbol.LotsStep();
 
 if(norm_volume < min_volume)
    norm_volume = min_volume;
 if(norm_volume > max_volume)
    norm_volume = max_volume;
 
 norm_volume = MathFloor(norm_volume / volume_step) * volume_step;
 norm_volume = NormalizeDouble(norm_volume, 2);
 
 if(norm_volume <= 0 || norm_volume < min_volume)
 {
    SendErrorResponse(signal_id, "Invalid lot size after normalization");
    return;
 }
 
 double stop_loss = 0, take_profit = 0;
 
 if(sl > 0)
 {
    stop_loss = (action == "buy") ? price - sl * g_symbol.Point() : price + sl * g_symbol.Point();
    stop_loss = NormalizeDouble(stop_loss, g_symbol.Digits());
 }
 
 if(tp > 0)
 {
    take_profit = (action == "buy") ? price + tp * g_symbol.Point() : price - tp * g_symbol.Point();
    take_profit = NormalizeDouble(take_profit, g_symbol.Digits());
 }
 
 g_trade.SetExpertMagicNumber(MAGIC_NUMBER);
 
 bool result = g_trade.PositionOpen(symbol, order_type, norm_volume, price, stop_loss, take_profit, signal_id);
 
 if(result)
 {
    g_trades_executed++;
    SendTradeResponse(signal_id, "success", g_trade.ResultDeal(), g_trade.ResultPrice());
 }
 else
 {
    SendErrorResponse(signal_id, "Trade failed: " + GetLastErrorString());
 }
}

void ClosePosition(string symbol, string signal_id)
{
int positions_closed = 0;
 
 for(int i = PositionsTotal() - 1; i >= 0; i--)
 {
    if(g_position.SelectByIndex(i))
    {
       if(g_position.Symbol() == symbol && g_position.Magic() == MAGIC_NUMBER)
       {
          if(g_trade.PositionClose(g_position.Ticket()))
          {
             positions_closed++;
          }
       }
    }
 }
 
 if(positions_closed > 0)
 {
    SendTradeResponse(signal_id, "success", 0, 0,
       "Closed " + IntegerToString(positions_closed) + " positions");
 }
 else
 {
    SendErrorResponse(signal_id, "No positions found for " + symbol);
 }
}

void CloseAllPositions(string signal_id)
{
int positions_closed = 0;
 
 for(int i = PositionsTotal() - 1; i >= 0; i--)
 {
    if(g_position.SelectByIndex(i))
    {
       if(g_position.Magic() == MAGIC_NUMBER)
       {
          if(g_trade.PositionClose(g_position.Ticket()))
          {
             positions_closed++;
          }
       }
    }
 }
 
 SendTradeResponse(signal_id, "success", 0, 0,
    "Closed " + IntegerToString(positions_closed) + " positions");
}

void HandleCommand(string json)
{
string command = GetJsonValue(json, "command");
 
 if(command == "shutdown")
 {
    Print("Shutdown command received");
    g_shutdown_requested = true;
 }
 else if(command == "reset")
 {
    Print("Reset command received");
    ResetStatistics();
    SendStatusMessage("reset", "Statistics reset");
 }
 else if(command == "status")
 {
    SendDetailedStatus();
 }
 else
 {
    Print("Unknown command: ", command);
 }
}

void HandleConfig(string json)
{
string param = GetJsonValue(json, "param");
 string value = GetJsonValue(json, "value");
 
 Print("Config update: ", param, " = ", value);
 
 if(param == "magic_number")
 {
    int new_magic = (int)StringToInteger(value);
    g_trade.SetExpertMagicNumber(new_magic);
    SendStatusMessage("config", "Magic number updated to " + value);
 }
 else if(param == "slippage")
 {
    int new_slippage = (int)StringToInteger(value);
    g_trade.SetDeviationInPoints(new_slippage);
    SendStatusMessage("config", "Slippage updated to " + value);
 }
}

void SendTradeResponse(string signal_id, string status, ulong ticket, double price, string message = "")
{
string response = StringFormat(
    "{\"type\":\"trade_result\",\"signal_id\":\"%s\",\"status\":\"%s\"," +
    "\"ticket\":%d,\"price\":%.5f,\"message\":\"%s\"," +
    "\"balance\":%.2f,\"equity\":%.2f,\"margin\":%.2f," +
    "\"timestamp\":\"%s\"}",
    signal_id, status, ticket, price, message,
    AccountInfoDouble(ACCOUNT_BALANCE),
    AccountInfoDouble(ACCOUNT_EQUITY),
    AccountInfoDouble(ACCOUNT_MARGIN),
    TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS)
 );
 
 SendMessage(response);
}

void SendErrorResponse(string signal_id, string error)
{
string response = StringFormat(
    "{\"type\":\"error\",\"signal_id\":\"%s\",\"error\":\"%s\"," +
    "\"timestamp\":\"%s\"}",
    signal_id, error,
    TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS)
 );
 
 SendMessage(response);
 g_errors_count++;
}

void SendStatusMessage(string status, string message)
{
string response = StringFormat(
    "{\"type\":\"status\",\"status\":\"%s\",\"message\":\"%s\"," +
    "\"ea_version\":\"%s\",\"account\":%d,\"server\":\"%s\"," +
    "\"timestamp\":\"%s\"}",
    status, message,
    "7.01", AccountInfoInteger(ACCOUNT_LOGIN),
    AccountInfoString(ACCOUNT_SERVER),
    TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS)
 );
 
 SendMessage(response);
}

void SendDetailedStatus()
{
string response = StringFormat(
    "{\"type\":\"status_report\"," +
    "\"connected\":%s,\"uptime\":%d," +
    "\"messages_received\":%d,\"messages_sent\":%d," +
    "\"trades_executed\":%d,\"errors\":%d," +
    "\"open_positions\":%d,\"account_balance\":%.2f," +
    "\"account_equity\":%.2f,\"account_margin\":%.2f," +
    "\"timestamp\":\"%s\"}",
    g_zmq_connected ? "true" : "false",
    (int)(TimeCurrent() - g_last_recv_time),
    g_messages_received, g_messages_sent,
    g_trades_executed, g_errors_count,
    PositionsTotal(),
    AccountInfoDouble(ACCOUNT_BALANCE),
    AccountInfoDouble(ACCOUNT_EQUITY),
    AccountInfoDouble(ACCOUNT_MARGIN),
    TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS)
 );
 
 SendMessage(response);
}

void SendHeartbeatIfNeeded()
{
if(TimeCurrent() - g_last_heartbeat_time >= HEARTBEAT_INTERVAL / 1000)
 {
    string heartbeat = StringFormat(
       "{\"type\":\"heartbeat\",\"balance\":%.2f,\"equity\":%.2f," +
       "\"positions\":%d,\"timestamp\":\"%s\"}",
       AccountInfoDouble(ACCOUNT_BALANCE),
       AccountInfoDouble(ACCOUNT_EQUITY),
       PositionsTotal(),
       TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS)
    );
    
    SendMessage(heartbeat);
    g_last_heartbeat_time = TimeCurrent();
 }
}

void SendPong()
{
string pong = StringFormat(
    "{\"type\":\"pong\",\"timestamp\":\"%s\"}",
    TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS)
 );
 
 SendMessage(pong);
}

bool SendMessage(string message)
{
if(!g_zmq_connected) return false;
 
 uchar data[];
 StringToCharArray(message, data);
 ArrayResize(data, ArraySize(data) - 1);
 
 int result = zmq_send(g_zmq_heartbeat_socket, data, ArraySize(data), 0);
 
 if(result >= 0)
 {
    g_messages_sent++;
    return true;
 }
 else
 {
    int error = zmq_errno();
    Print("ERROR: Failed to send message, errno: ", error);
    g_errors_count++;
    return false;
 }
}

bool IsZMQHealthy()
{
int silence_seconds = (int)(TimeCurrent() - g_last_recv_time);
 
 if(silence_seconds > 120)  // Extended from 30 to 120 seconds
 {
    Print("WARNING: No messages received for ", silence_seconds, " seconds");
    return false;
 }
 
 return true;
}

void AttemptReconnect()
{
g_reconnect_attempts++;
 
 Print("Attempting reconnect #", g_reconnect_attempts, "...");
 
 ShutdownZMQ();
 
 Sleep(RECONNECT_DELAY);
 
 if(InitializeZMQ())
 {
    Print("✅  Reconnected successfully");
    g_reconnect_attempts = 0;
    SendStatusMessage("reconnected", "Reconnected after " + IntegerToString(g_reconnect_attempts) + " attempts");
 }
 else
 {
    Print("❌  Reconnect failed");
 }
}

void ResetStatistics()
{
g_messages_received = 0;
 g_messages_sent = 0;
 g_trades_executed = 0;
 g_errors_count = 0;
 g_reconnect_attempts = 0;
}

string GetJsonValue(string json, string key)
{
int key_pos = StringFind(json, "\"" + key + "\":");
 if(key_pos < 0) return "";
 
 int start = StringFind(json, ":", key_pos) + 1;
 if(start <= key_pos) return "";
 
 while(start < StringLen(json) &&
       (StringGetCharacter(json, start) == ' ' ||
        StringGetCharacter(json, start) == '\t'))
 {
    start++;
 }
 
 bool is_string = (StringGetCharacter(json, start) == '"');
 
 if(is_string)
 {
    start++;
    int end = StringFind(json, "\"", start);
    if(end < 0) return "";
    return StringSubstr(json, start, end - start);
 }
 else
 {
    int end = start;
    while(end < StringLen(json))
    {
       ushort ch = StringGetCharacter(json, end);
       if(ch == ',' || ch == '}' || ch == ' ' || ch == '\n' || ch == '\r')
          break;
       end++;
    }
    return StringSubstr(json, start, end - start);
 }
}

void ArrayFromInt(uchar &arr[], int value)
{
ArrayResize(arr, 4);
 arr[0] = (uchar)(value & 0xFF);
 arr[1] = (uchar)((value >> 8) & 0xFF);
 arr[2] = (uchar)((value >> 16) & 0xFF);
 arr[3] = (uchar)((value >> 24) & 0xFF);
}

string GetLastErrorString()
{
int error = GetLastError();
 ResetLastError();
 
 switch(error)
 {
    case 0:         return "No error";
    case 4000:      return "No error";
    case 4001:      return "Wrong function pointer";
    case 4002:      return "Array index is out of range";
    case 4003:      return "No memory for function call stack";
    case 4004:      return "Recursive stack overflow";
    case 4005:      return "Not enough stack for parameter";
    case 4006:      return "No memory for parameter string";
    case 4007:      return "No memory for temp string";
    case 4008:      return "Not initialized string";
    case 4009:      return "Not initialized string in array";
    case 4010:      return "No memory for array string";
    case 4011:      return "Too long string";
    case 4012:      return "Remainder from zero divide";
    case 4013:      return "Zero divide";
    case 4014:      return "Unknown command";
    case 4015:      return "Wrong jump";
    case 4016:      return "Not initialized array";
    case 4017:      return "DLL calls are not allowed";
    case 4018:      return "Cannot load library";
    case 4019:      return "Cannot call function";
    case 4020:      return "Expert function calls are not allowed";
    case 4021:      return "Not enough memory for temp string from function";
    case 4022:      return "System is busy";
    case 4101:      return "Wrong file name";
    case 4102:      return "Too many opened files";
    case 4103:      return "Cannot open file";
    case 4104:      return "Incompatible access to a file";
    case 4105:      return "No order selected";
    case 4106:      return "Unknown symbol";
    case 4107:      return "Invalid price";
    case 4108:      return "Invalid ticket";
    case 4109:      return "Trade is not allowed";
    case 4110:      return "Longs are not allowed";
    case 4111:      return "Shorts are not allowed";
    case 4200:      return "Object already exists";
    case 4201:      return "Unknown object property";
    case 4202:      return "Object does not exist";
    case 4203:      return "Unknown object type";
    case 4204:      return "No object name";
    case 4205:      return "Object coordinates error";
    case 4206:      return "No specified subwindow";
    case 4207:      return "Graphical object error";
    case 4301:      return "Unknown symbol";
    case 4302:      return "Symbol is not selected in MarketWatch";
    case 4303:      return "Invalid symbol trade mode";
    case 4304:      return "Market is closed";
    case 4305:      return "Trade is not allowed";
    case 10004:     return "Requote";
    case 10006:     return "Request rejected";
    case 10007:     return "Request canceled by trader";
    case 10008:     return "Order placed";
    case 10009:     return "Request completed";
    case 10010:     return "Only part of the request was completed";
    case 10011:     return "Request processing error";
    case 10012:     return "Request canceled by timeout";
    case 10013:     return "Invalid request";
    case 10014:     return "Invalid volume in the request";
    case 10015:     return "Invalid price in the request";
    case 10016:     return "Invalid stops in the request";
    case 10017:     return "Trade is disabled";
    case 10018:     return "Market is closed";
    case 10019:     return "There is not enough money to complete the request";
    case 10020:     return "Prices changed";
    case 10021:     return "There are no quotes to process the request";
    case 10022:     return "Invalid order expiration date in the request";
    case 10023:     return "Order state changed";
    case 10024:     return "Too frequent requests";
    case 10025:     return "No changes in request";
    case 10026:     return "Autotrading disabled by server";
    case 10027:     return "Autotrading disabled by client terminal";
    case 10028:     return "Request locked for processing";
    case 10029:     return "Order or position frozen";
    case 10030:     return "Invalid order filling type";
    case 10031:     return "No connection with the trade server";
    case 10032:     return "Operation is allowed only for live accounts";
    case 10033:     return "The number of pending orders has reached the limit";
    case 10034:     return "The volume of orders and positions has reached the limit";
    case 10035:     return "Incorrect or prohibited order type";
    case 10036:     return "Position with the specified identifier has already been closed";
    case 10038:     return "Close volume exceeds the current position volume";
    case 10039:     return "A close order already exists for a specified position";
    case 10040:     return "The number of open positions has reached the limit";
    case 10041:     return "Pending order activation request is rejected";
    case 10042:     return "The request is rejected, because the rule is violated";
    case 10043:     return "The request is rejected, because the total volume limit is violated";
    case 10044:     return "The request is rejected, because the hedge is prohibited";
    case 4500:      return "Trade request sending failed";
    case 4501:      return "Trade request canceled";
    case 4502:      return "Trade request structure not filled";
    case 4503:      return "Invalid trade request structure";
    case 10045:     return "Close by order is prohibited for the trading account";
    case 10046:     return "Only closing of positions is allowed";
    case 10047:     return "Only closing of positions by FIFO rule is allowed";
    case 10048:     return "The request is rejected, because the max total pending order volume limit is violated";
    default:        return "Unknown error (" + IntegerToString(error) + ")";
 }
}

string GetDeinitReasonText(int reason)
{
switch(reason)
 {
    case REASON_PROGRAM:     return "Program terminated";
    case REASON_REMOVE:      return "EA removed from chart";
    case REASON_RECOMPILE:   return "EA recompiled";
    case REASON_CHARTCHANGE: return "Chart symbol or period changed";
    case REASON_CHARTCLOSE:  return "Chart closed";
    case REASON_PARAMETERS:  return "Parameters changed";
    case REASON_ACCOUNT:     return "Account changed";
    default:                 return "Unknown reason";
 }
}

void PrintZMQVersion()
{
int major = 0, minor = 0, patch = 0;
 zmq_version(major, minor, patch);
 Print("ZMQ Version: ", major, ".", minor, ".", patch);
}

void OnTrade()
{
}