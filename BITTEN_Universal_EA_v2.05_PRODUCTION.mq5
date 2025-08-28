//+------------------------------------------------------------------+
//| BITTEN_Universal_EA_v2.05.mq5                                   |
//| BITTEN - Universal Multi-Symbol ZMQ Bridge v2.05                |
//| DEALER SOCKET WITH FULL METRICS & RISK MANAGEMENT               |
//+------------------------------------------------------------------+
#property copyright "BITTEN Systems"
#property link      "https://bitten.tactical"
#property version   "2.05"
#property strict

//+------------------------------------------------------------------+
//| Fire Command Format:                                            |
//| {                                                                |
//|   "type": "fire",                                              |
//|   "fire_id": "fir_xxx",        // Unique fire identifier       |
//|   "target_uuid": "USER_UUID",                                  |
//|   "symbol": "EURUSD",                                          |
//|   "direction": "BUY" or "SELL",  // or "side"                 |
//|   "entry": 1.1000,  // Can be 0 for market order              |
//|   "sl": 1.0950,     // Actual price level                     |
//|   "tp": 1.1050,     // Actual price level                     |
//|   "lot": 0.01                                                  |
//| }                                                               |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//| ZMQ Constants                                                    |
//+------------------------------------------------------------------+
#define ZMQ_PAIR 0
#define ZMQ_PUB 1
#define ZMQ_SUB 2
#define ZMQ_REQ 3
#define ZMQ_REP 4
#define ZMQ_DEALER 5
#define ZMQ_ROUTER 6
#define ZMQ_PULL 7
#define ZMQ_PUSH 8
#define ZMQ_XPUB 9
#define ZMQ_XSUB 10
#define ZMQ_STREAM 11

#define ZMQ_DONTWAIT 1
#define ZMQ_SNDMORE 2
#define ZMQ_IDENTITY 5   // Option ID for identity (ZeroMQ)

//+------------------------------------------------------------------+
//| Direct libzmq.dll imports - FIXED FOR 64-BIT WITH IDENTITY      |
//+------------------------------------------------------------------+
#import "libzmq.dll"
ulong zmq_ctx_new();
int zmq_ctx_destroy(ulong context);
ulong zmq_socket(ulong context, int type);
int zmq_close(ulong socket);
int zmq_connect(ulong socket, uchar &endpoint[]);
int zmq_bind(ulong socket, uchar &endpoint[]);
int zmq_send(ulong socket, uchar &data[], int length, int flags);
int zmq_recv(ulong socket, uchar &data[], int length, int flags);
// Keep existing int-based setsockopt
int zmq_setsockopt(ulong socket, int option, int &value, int option_len);
// NEW: string/byte-array setsockopt (needed for ZMQ_IDENTITY)
int zmq_setsockopt(ulong socket, int option, uchar &value[], int option_len);
int zmq_poll(ulong items, int nitems, long timeout);
#import

//+------------------------------------------------------------------+
//| Global variables - LIGHTWEIGHT DEPLOYMENT                        |
//+------------------------------------------------------------------+
ulong g_context = 0;
ulong g_tick_publisher = 0;   // PUSH socket for outbound market data
ulong g_command_receiver = 0; // DEALER socket for targeted commands (with identity)
ulong g_confirm_sender = 0;   // PUSH socket for confirmations

string g_bridge_ip = "134.199.204.67"; // BITTEN command center
int g_tick_port = 5556;       // Market data output
int g_command_port = 5555;    // Targeted command input (ROUTER on CC side)
int g_confirm_port = 5558;    // Confirmation output

datetime g_last_tick_time = 0;
datetime g_last_ohlc_time = 0;
datetime g_last_heartbeat = 0;
int g_tick_count = 0;
string g_node_id = "";

// UUID Configuration
string g_user_uuid = "";
bool g_uuid_locked = false;

// Multi-symbol monitoring arrays
string g_monitored_symbols[];
datetime g_symbol_last_tick[];
int g_symbol_count = 0;

//+------------------------------------------------------------------+
//| Helper to set ZMQ_IDENTITY on socket                            |
//+------------------------------------------------------------------+
int ZMQSetIdentity(ulong socket, string id)
{
    uchar buf[];
    StringToCharArray(id, buf, 0, StringLen(id), CP_UTF8);
    // libzmq expects length WITHOUT the trailing null
    return zmq_setsockopt(socket, ZMQ_IDENTITY, buf, ArraySize(buf)-1);
}

//+------------------------------------------------------------------+
//| Load UUID from deployment configuration file                     |
//+------------------------------------------------------------------+
bool LoadDeploymentConfig()
{
    // DEVELOPER MODE - Skip config file for testing
    if (AccountInfoInteger(ACCOUNT_LOGIN) == 843859) {
        g_user_uuid = "COMMANDER_DEV_001";
        Print("🔧 DEVELOPER MODE: Using hardcoded UUID for Commander testing");
        Print("🔒 Dev UUID: ", g_user_uuid);
        return true;
    }
    
    // Production mode - Read UUID from deployment config file
    string config_file = "bitten_deployment.cfg";
    int file_handle = FileOpen(config_file, FILE_READ|FILE_TXT);
    
    if (file_handle == INVALID_HANDLE) {
        Print("❌ CRITICAL: No deployment config file found!");
        Print("❌ This EA must be deployed by BITTEN system only!");
        return false;
    }
    
    string line = "";
    while (!FileIsEnding(file_handle)) {
        line = FileReadString(file_handle);
        
        // Parse UUID line: UUID=user_123456789
        if (StringFind(line, "UUID=") == 0) {
            g_user_uuid = StringSubstr(line, 5); // Extract after "UUID="
            StringTrimLeft(g_user_uuid);
            StringTrimRight(g_user_uuid);
        }
    }
    
    FileClose(file_handle);
    
    // Validate UUID was loaded
    if (g_user_uuid == "" || StringLen(g_user_uuid) < 10) {
        Print("❌ CRITICAL: Invalid or missing UUID in deployment config!");
        return false;
    }
    
    Print("🔒 UUID loaded from deployment: ", g_user_uuid);
    return true;
}

//+------------------------------------------------------------------+
//| Initialize monitored symbols from MarketWatch                    |
//+------------------------------------------------------------------+
void InitializeMonitoredSymbols()
{
    g_symbol_count = 0;
    
    // Get all symbols from MarketWatch
    int total_symbols = SymbolsTotal(true);
    ArrayResize(g_monitored_symbols, total_symbols);
    ArrayResize(g_symbol_last_tick, total_symbols);
    
    for (int i = 0; i < total_symbols; i++) {
        string symbol = SymbolName(i, true);
        if (symbol != "") {
            g_monitored_symbols[g_symbol_count] = symbol;
            g_symbol_last_tick[g_symbol_count] = 0;
            g_symbol_count++;
            
            // Ensure symbol is selected for data access
            if (!SymbolSelect(symbol, true)) {
                Print("⚠️ Failed to select symbol: ", symbol);
            }
        }
    }
    
    // Resize arrays to actual count
    ArrayResize(g_monitored_symbols, g_symbol_count);
    ArrayResize(g_symbol_last_tick, g_symbol_count);
    
    Print("📊 Monitoring ", g_symbol_count, " symbols from MarketWatch:");
    for (int i = 0; i < MathMin(g_symbol_count, 10); i++) { // Print first 10
        Print("  - ", g_monitored_symbols[i]);
    }
    if (g_symbol_count > 10) {
        Print("  ... and ", g_symbol_count - 10, " more symbols");
    }
}

//+------------------------------------------------------------------+
//| Helper function to connect ZMQ socket                            |
//+------------------------------------------------------------------+
int ZMQConnect(ulong socket, string endpoint)
{
    uchar endpoint_bytes[];
    StringToCharArray(endpoint, endpoint_bytes, 0, StringLen(endpoint), CP_UTF8);
    ArrayResize(endpoint_bytes, ArraySize(endpoint_bytes) + 1);
    endpoint_bytes[ArraySize(endpoint_bytes) - 1] = 0; // Null terminator
    return zmq_connect(socket, endpoint_bytes);
}

//+------------------------------------------------------------------+
//| Send HELLO with full metrics via DEALER socket                   |
//+------------------------------------------------------------------+
void SendHelloDealerWithMetrics()
{
    // Gather metrics
    string acct     = IntegerToString((long)AccountInfoInteger(ACCOUNT_LOGIN));
    string broker   = AccountInfoString(ACCOUNT_SERVER);
    string company  = AccountInfoString(ACCOUNT_COMPANY);
    string term     = TerminalInfoString(TERMINAL_NAME);
    string currency = AccountInfoString(ACCOUNT_CURRENCY);
    string balance  = DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2);
    string equity   = DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2);
    string leverage = IntegerToString((int)AccountInfoInteger(ACCOUNT_LEVERAGE));
    string margin   = DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN), 2);
    string free_margin = DoubleToString(AccountInfoDouble(ACCOUNT_FREEMARGIN), 2);
    string margin_level = DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN_LEVEL), 2);
    string ts       = TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS);
    
    // Build JSON (single frame)
    string hello = "{" +
        "\"type\":\"HELLO\"," +
        "\"target_uuid\":\"" + g_user_uuid + "\"," +
        "\"node_id\":\"" + g_node_id + "\"," +
        "\"account_login\":\"" + acct + "\"," +
        "\"broker\":\"" + broker + "\"," +
        "\"company\":\"" + company + "\"," +
        "\"terminal\":\"" + term + "\"," +
        "\"currency\":\"" + currency + "\"," +
        "\"balance\":" + balance + "," +
        "\"equity\":" + equity + "," +
        "\"leverage\":" + leverage + "," +
        "\"margin\":" + margin + "," +
        "\"free_margin\":" + free_margin + "," +
        "\"margin_level\":" + margin_level + "," +
        "\"symbols\":" + IntegerToString(g_symbol_count) + "," +
        "\"version\":\"2.05\"," +
        "\"timestamp\":\"" + ts + "\"" +
        "}";
    
    uchar data[];
    if (StringToCharArray(hello, data) > 0) {
        if (zmq_send(g_command_receiver, data, ArraySize(data)-1, 0) > 0) {
            Print("✅ HELLO(DEALER) sent: bal=", balance, " eq=", equity,
                  " cur=", currency, " lev=", leverage);
        } else {
            Print("⚠️ HELLO(DEALER) send failed, errno: ", GetLastError());
        }
    }
}

//+------------------------------------------------------------------+
//| Send metrics heartbeat via DEALER socket                         |
//+------------------------------------------------------------------+
void SendDealerHeartbeatMetrics()
{
    string balance  = DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2);
    string equity   = DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2);
    string currency = AccountInfoString(ACCOUNT_CURRENCY);
    string leverage = IntegerToString((int)AccountInfoInteger(ACCOUNT_LEVERAGE));
    string margin   = DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN), 2);
    string free_margin = DoubleToString(AccountInfoDouble(ACCOUNT_FREEMARGIN), 2);
    string margin_level = DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN_LEVEL), 2);
    string ts       = TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS);
    
    string hb = "{" +
        "\"type\":\"HEARTBEAT\"," +
        "\"target_uuid\":\"" + g_user_uuid + "\"," +
        "\"node_id\":\"" + g_node_id + "\"," +
        "\"currency\":\"" + currency + "\"," +
        "\"balance\":" + balance + "," +
        "\"equity\":" + equity + "," +
        "\"leverage\":" + leverage + "," +
        "\"margin\":" + margin + "," +
        "\"free_margin\":" + free_margin + "," +
        "\"margin_level\":" + margin_level + "," +
        "\"ticks_processed\":" + IntegerToString(g_tick_count) + "," +
        "\"timestamp\":\"" + ts + "\"" +
        "}";
    
    uchar data[];
    if (StringToCharArray(hb, data) > 0) {
        zmq_send(g_command_receiver, data, ArraySize(data)-1, 0);
        // Silent send - don't spam logs with heartbeats
    }
}

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("🎯 BITTEN Universal EA v2.05 - FULL METRICS INTEGRATION");
    Print("🏢 Single Chart Deployment - Monitors ALL MarketWatch Symbols");
    Print("💰 Risk Management Ready - Real-time Equity Tracking");
    
    // CRITICAL: Load UUID from deployment configuration
    if (!LoadDeploymentConfig()) {
        Comment("❌ DEPLOYMENT ERROR\nContact BITTEN Support");
        return INIT_FAILED;
    }
    
    // Check trading and DLL permissions
    if (!TerminalInfoInteger(TERMINAL_DLLS_ALLOWED)) {
        Print("⚠️ DLL imports disabled - ZMQ will not work");
        return INIT_FAILED;
    }
    if (!AccountInfoInteger(ACCOUNT_TRADE_ALLOWED)) {
        Print("⚠️ Trading not allowed by account");
        return INIT_FAILED;
    }
    
    // Generate unique node ID
    g_node_id = "NODE_" + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)) + "_" + IntegerToString(GetTickCount());
    
    Print("📡 Node ID: ", g_node_id);
    Print("🔒 User UUID: ", g_user_uuid, " (BITTEN HOSTED)");
    Print("🏢 MT5 Account: ", AccountInfoInteger(ACCOUNT_LOGIN));
    Print("🌐 Broker: ", AccountInfoString(ACCOUNT_COMPANY));
    Print("💱 Currency: ", AccountInfoString(ACCOUNT_CURRENCY));
    Print("💰 Balance: ", DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2));
    Print("📊 Equity: ", DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2));
    Print("🔧 Leverage: 1:", AccountInfoInteger(ACCOUNT_LEVERAGE));
    Print("📈 Chart Symbol: ", Symbol(), " (Attachment Point Only)");
    
    // Initialize monitored symbols
    InitializeMonitoredSymbols();
    
    // Create ZMQ context
    g_context = zmq_ctx_new();
    if (g_context == 0) {
        Print("❌ Failed to create ZMQ context, errno: ", GetLastError());
        return INIT_FAILED;
    }
    Print("✅ ZMQ context created");
    
    // Create PUSH socket for market data (ticks + OHLC)
    g_tick_publisher = zmq_socket(g_context, ZMQ_PUSH);
    if (g_tick_publisher == 0) {
        Print("❌ Failed to create market data publisher socket");
        zmq_ctx_destroy(g_context);
        return INIT_FAILED;
    }
    string tick_endpoint = "tcp://" + g_bridge_ip + ":" + IntegerToString(g_tick_port);
    if (ZMQConnect(g_tick_publisher, tick_endpoint) != 0) {
        Print("❌ Failed to connect market data publisher to ", tick_endpoint, ", errno: ", GetLastError());
        zmq_close(g_tick_publisher);
        zmq_ctx_destroy(g_context);
        return INIT_FAILED;
    }
    Print("✅ Market data publisher connected to ", tick_endpoint);
    
    // Create DEALER socket for targeted commands (addressable by identity)
    g_command_receiver = zmq_socket(g_context, ZMQ_DEALER);
    if (g_command_receiver == 0) {
        Print("❌ Failed to create DEALER command socket");
        zmq_close(g_tick_publisher);
        zmq_ctx_destroy(g_context);
        return INIT_FAILED;
    }
    
    // Set socket identity to UUID for precise routing
    if (ZMQSetIdentity(g_command_receiver, g_user_uuid) != 0) {
        Print("❌ Failed to set ZMQ_IDENTITY on DEALER socket");
        zmq_close(g_tick_publisher);
        zmq_close(g_command_receiver);
        zmq_ctx_destroy(g_context);
        return INIT_FAILED;
    }
    Print("✅ DEALER socket identity set to: ", g_user_uuid);
    
    string command_endpoint = "tcp://" + g_bridge_ip + ":" + IntegerToString(g_command_port);
    if (ZMQConnect(g_command_receiver, command_endpoint) != 0) {
        Print("❌ Failed to connect DEALER to ", command_endpoint, ", errno: ", GetLastError());
        zmq_close(g_tick_publisher);
        zmq_close(g_command_receiver);
        zmq_ctx_destroy(g_context);
        return INIT_FAILED;
    }
    Print("✅ DEALER command socket connected (identity=", g_user_uuid, ") to ", command_endpoint);
    
    // Create PUSH socket for confirmations
    g_confirm_sender = zmq_socket(g_context, ZMQ_PUSH);
    if (g_confirm_sender == 0) {
        Print("❌ Failed to create confirmation sender socket");
        zmq_close(g_tick_publisher);
        zmq_close(g_command_receiver);
        zmq_ctx_destroy(g_context);
        return INIT_FAILED;
    }
    string confirm_endpoint = "tcp://" + g_bridge_ip + ":" + IntegerToString(g_confirm_port);
    if (ZMQConnect(g_confirm_sender, confirm_endpoint) != 0) {
        Print("❌ Failed to connect confirmation sender to ", confirm_endpoint, ", errno: ", GetLastError());
        zmq_close(g_tick_publisher);
        zmq_close(g_command_receiver);
        zmq_close(g_confirm_sender);
        zmq_ctx_destroy(g_context);
        return INIT_FAILED;
    }
    Print("✅ Confirmation sender connected to ", confirm_endpoint);
    
    // Send HELLO with full metrics via DEALER
    SendHelloDealerWithMetrics();
    
    // Send handshake packet (telemetry - optional, can keep for ops monitoring)
    SendHandshake();
    
    // Enable timer for multi-symbol monitoring
    EventSetTimer(1); // Check every second
    Print("✅ Timer enabled for multi-symbol monitoring (1 second interval)");
    
    // Display status on chart
    Comment("🎯 BITTEN UNIVERSAL EA v2.05\n🔒 UUID: " + g_user_uuid + "\n📡 Node: " + g_node_id + 
            "\n🏢 Account: " + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)) + 
            "\n💰 Balance: " + AccountInfoString(ACCOUNT_CURRENCY) + " " + DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2) +
            "\n📊 Equity: " + AccountInfoString(ACCOUNT_CURRENCY) + " " + DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2) +
            "\n📈 Symbols: " + IntegerToString(g_symbol_count) + 
            "\n⏰ Ticks: " + IntegerToString(g_tick_count) +
            "\n🔐 DEALER + Metrics Active");
    
    Print("🚀 BITTEN Universal EA v2.05 initialized successfully - Monitoring ", g_symbol_count, " symbols");
    Print("💎 FULL METRICS INTEGRATION ACTIVE - Risk management enabled");
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("🔒 BITTEN Universal EA v2.05 - Shutting down...");
    
    // Kill the timer
    EventKillTimer();
    Print("✅ Timer disabled");
    
    // Send disconnect message
    SendDisconnect();
    
    // Close all sockets
    if (g_tick_publisher != 0) {
        zmq_close(g_tick_publisher);
        Print("✅ Market data publisher closed");
    }
    if (g_command_receiver != 0) {
        zmq_close(g_command_receiver);
        Print("✅ DEALER command receiver closed");
    }
    if (g_confirm_sender != 0) {
        zmq_close(g_confirm_sender);
        Print("✅ Confirmation sender closed");
    }
    
    // Destroy context
    if (g_context != 0) {
        zmq_ctx_destroy(g_context);
        Print("✅ ZMQ context destroyed");
    }
    
    Comment("");
    Print("👋 BITTEN Universal EA v2.05 shutdown complete");
}

//+------------------------------------------------------------------+
//| Expert tick function - Chart symbol only                         |
//+------------------------------------------------------------------+
void OnTick()
{
    // Process chart symbol tick (high frequency)
    if (TimeCurrent() != g_last_tick_time) {
        if (g_tick_publisher != 0) PushTickData(Symbol());
        g_last_tick_time = TimeCurrent();
        g_tick_count++;
        
        // Update display every 50 ticks
        if (g_tick_count % 50 == 0) {
            Comment("🎯 BITTEN UNIVERSAL EA v2.05\n🔒 UUID: " + g_user_uuid + "\n📡 Node: " + g_node_id + 
                    "\n🏢 Account: " + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)) + 
                    "\n💰 Balance: " + AccountInfoString(ACCOUNT_CURRENCY) + " " + DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2) +
                    "\n📊 Equity: " + AccountInfoString(ACCOUNT_CURRENCY) + " " + DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2) +
                    "\n📈 Symbols: " + IntegerToString(g_symbol_count) + 
                    "\n⏰ Ticks: " + IntegerToString(g_tick_count) +
                    "\n🕐 " + TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) +
                    "\n🔐 DEALER + Metrics Active");
        }
    }
    
    // Check for unified commands (non-blocking)
    if (g_command_receiver != 0) CheckUnifiedCommands();
}

//+------------------------------------------------------------------+
//| Timer function - Multi-symbol monitoring                         |
//+------------------------------------------------------------------+
void OnTimer()
{
    // Monitor all symbols for ticks and OHLC data
    if (g_tick_publisher != 0) {
        MonitorAllSymbols();
    }
    
    // Send heartbeat every 30 seconds
    if (TimeCurrent() - g_last_heartbeat >= 30) {
        // Existing telemetry heartbeat to 5556 (keep for ops)
        SendHeartbeat();
        
        // NEW: Metrics heartbeat to ROUTER/DEALER (5555)
        SendDealerHeartbeatMetrics();
        
        g_last_heartbeat = TimeCurrent();
    }
    
    // Send OHLC data every 60 seconds
    if (TimeCurrent() - g_last_ohlc_time >= 60) {
        PushAllOHLCData();
        g_last_ohlc_time = TimeCurrent();
    }
}

//+------------------------------------------------------------------+
//| Monitor all symbols for new ticks                                |
//+------------------------------------------------------------------+
void MonitorAllSymbols()
{
    for (int i = 0; i < g_symbol_count; i++) {
        string symbol = g_monitored_symbols[i];
        
        // Get current tick
        MqlTick tick;
        if (SymbolInfoTick(symbol, tick)) {
            // Check if this is a new tick for this symbol
            if (tick.time > g_symbol_last_tick[i]) {
                PushTickData(symbol);
                g_symbol_last_tick[i] = tick.time;
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Push OHLC data for all monitored symbols                         |
//+------------------------------------------------------------------+
void PushAllOHLCData()
{
    for (int i = 0; i < g_symbol_count; i++) {
        string symbol = g_monitored_symbols[i];
        
        // Send M1 candle data
        PushOHLCData(symbol, PERIOD_M1);
        
        // Send M5 candle data every 5 minutes
        if (TimeCurrent() % 300 == 0) {
            PushOHLCData(symbol, PERIOD_M5);
        }
        
        // Send M15 candle data every 15 minutes
        if (TimeCurrent() % 900 == 0) {
            PushOHLCData(symbol, PERIOD_M15);
        }
    }
}

//+------------------------------------------------------------------+
//| Send handshake packet (telemetry via tick publisher)            |
//+------------------------------------------------------------------+
void SendHandshake()
{
    string symbols_list = "";
    for (int i = 0; i < MathMin(g_symbol_count, 20); i++) { // First 20 symbols
        if (i > 0) symbols_list += ",";
        symbols_list += g_monitored_symbols[i];
    }
    
    string handshake = "{" + 
        "\"type\":\"handshake\"," + 
        "\"deployment_mode\":\"universal_dealer\"," +
        "\"node_id\":\"" + g_node_id + "\"," +
        "\"user_uuid\":\"" + g_user_uuid + "\"," +
        "\"account\":" + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)) + "," + 
        "\"broker\":\"" + AccountInfoString(ACCOUNT_COMPANY) + "\"," + 
        "\"server\":\"" + AccountInfoString(ACCOUNT_SERVER) + "\"," + 
        "\"chart_symbol\":\"" + Symbol() + "\"," +
        "\"monitored_symbols\":" + IntegerToString(g_symbol_count) + "," +
        "\"symbol_list\":\"" + symbols_list + "\"," +
        "\"currency\":\"" + AccountInfoString(ACCOUNT_CURRENCY) + "\"," +
        "\"balance\":" + DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2) + "," + 
        "\"equity\":" + DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2) + "," +
        "\"leverage\":" + IntegerToString((int)AccountInfoInteger(ACCOUNT_LEVERAGE)) + "," + 
        "\"version\":\"2.05\"," +
        "\"socket_type\":\"DEALER\"," +
        "\"timestamp\":\"" + TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "\"" + 
        "}";
    
    uchar data[];
    if (StringToCharArray(handshake, data) > 0) {
        if (zmq_send(g_tick_publisher, data, ArraySize(data) - 1, 0) > 0) {
            Print("✅ Telemetry handshake sent for UUID: ", g_user_uuid, " (", g_symbol_count, " symbols)");
            g_uuid_locked = true;
        } else {
            Print("⚠️ Failed to send telemetry handshake, errno: ", GetLastError());
        }
    } else {
        Print("⚠️ Failed to convert handshake to char array");
    }
}

//+------------------------------------------------------------------+
//| Send heartbeat with account info (telemetry)                    |
//+------------------------------------------------------------------+
void SendHeartbeat()
{
    string heartbeat = "{" +
        "\"type\":\"heartbeat\"," +
        "\"node_id\":\"" + g_node_id + "\"," +
        "\"user_uuid\":\"" + g_user_uuid + "\"," +
        "\"account\":" + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)) + "," +
        "\"currency\":\"" + AccountInfoString(ACCOUNT_CURRENCY) + "\"," +
        "\"balance\":" + DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2) + "," +
        "\"equity\":" + DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2) + "," +
        "\"leverage\":" + IntegerToString((int)AccountInfoInteger(ACCOUNT_LEVERAGE)) + "," +
        "\"free_margin\":" + DoubleToString(AccountInfoDouble(ACCOUNT_FREEMARGIN), 2) + "," +
        "\"margin_level\":" + DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN_LEVEL), 2) + "," +
        "\"symbols_monitored\":" + IntegerToString(g_symbol_count) + "," +
        "\"ticks_processed\":" + IntegerToString(g_tick_count) + "," +
        "\"socket_type\":\"DEALER\"," +
        "\"timestamp\":\"" + TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "\"" +
        "}";
    
    uchar data[];
    if (StringToCharArray(heartbeat, data) > 0) {
        if (zmq_send(g_tick_publisher, data, ArraySize(data) - 1, 0) > 0) {
            // Heartbeat sent successfully (don't spam logs)
        } else {
            Print("⚠️ Failed to send telemetry heartbeat, errno: ", GetLastError());
        }
    }
}

//+------------------------------------------------------------------+
//| Send disconnect message                                          |
//+------------------------------------------------------------------+
void SendDisconnect()
{
    string disconnect = "{" +
        "\"type\":\"DISCONNECT\"," +
        "\"deployment_mode\":\"universal_dealer\"," +
        "\"node_id\":\"" + g_node_id + "\"," +
        "\"user_uuid\":\"" + g_user_uuid + "\"," +
        "\"symbols_monitored\":" + IntegerToString(g_symbol_count) + "," +
        "\"ticks_processed\":" + IntegerToString(g_tick_count) + "," +
        "\"socket_type\":\"DEALER\"," +
        "\"timestamp\":\"" + TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "\"" +
        "}";
    
    uchar data[];
    if (StringToCharArray(disconnect, data) > 0) {
        zmq_send(g_tick_publisher, data, ArraySize(data) - 1, 0);
    }
}

//+------------------------------------------------------------------+
//| Push tick data for specific symbol                               |
//+------------------------------------------------------------------+
void PushTickData(string symbol)
{
    MqlTick tick;
    if (!SymbolInfoTick(symbol, tick)) {
        // Don't spam logs for symbols that might not have current quotes
        return;
    }
    
    string tick_json = "{" + 
        "\"type\":\"TICK\"," + 
        "\"node_id\":\"" + g_node_id + "\"," + 
        "\"user_uuid\":\"" + g_user_uuid + "\"," +
        "\"symbol\":\"" + symbol + "\"," + 
        "\"bid\":" + DoubleToString(tick.bid, (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS)) + "," + 
        "\"ask\":" + DoubleToString(tick.ask, (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS)) + "," + 
        "\"spread\":" + DoubleToString((tick.ask - tick.bid) / SymbolInfoDouble(symbol, SYMBOL_POINT), 1) + "," + 
        "\"volume\":" + IntegerToString(tick.volume) + "," + 
        "\"timestamp\":\"" + TimeToString(tick.time, TIME_DATE|TIME_SECONDS) + "\"" + 
        "}";
    
    uchar data[];
    if (StringToCharArray(tick_json, data) > 0) {
        if (zmq_send(g_tick_publisher, data, ArraySize(data) - 1, 0) <= 0) {
            // Don't spam logs with tick send failures
        }
    }
}

//+------------------------------------------------------------------+
//| Push OHLC data for specific symbol and timeframe                 |
//+------------------------------------------------------------------+
void PushOHLCData(string symbol, ENUM_TIMEFRAMES timeframe)
{
    datetime time = iTime(symbol, timeframe, 1); // Previous completed candle
    double open = iOpen(symbol, timeframe, 1);
    double high = iHigh(symbol, timeframe, 1);
    double low = iLow(symbol, timeframe, 1);
    double close = iClose(symbol, timeframe, 1);
    
    if (time == 0 || open == 0 || high == 0 || low == 0 || close == 0) {
        // Don't spam logs for symbols that might not have history
        return;
    }
    
    string timeframe_str = "";
    switch(timeframe) {
        case PERIOD_M1: timeframe_str = "M1"; break;
        case PERIOD_M5: timeframe_str = "M5"; break;
        case PERIOD_M15: timeframe_str = "M15"; break;
        case PERIOD_M30: timeframe_str = "M30"; break;
        case PERIOD_H1: timeframe_str = "H1"; break;
        default: timeframe_str = "M1"; break;
    }
    
    string ohlc_json = "{" + 
        "\"type\":\"OHLC\"," + 
        "\"node_id\":\"" + g_node_id + "\"," + 
        "\"user_uuid\":\"" + g_user_uuid + "\"," +
        "\"symbol\":\"" + symbol + "\"," + 
        "\"timeframe\":\"" + timeframe_str + "\"," +
        "\"time\":" + IntegerToString(time) + "," + 
        "\"open\":" + DoubleToString(open, (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS)) + "," + 
        "\"high\":" + DoubleToString(high, (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS)) + "," + 
        "\"low\":" + DoubleToString(low, (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS)) + "," + 
        "\"close\":" + DoubleToString(close, (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS)) + "," + 
        "\"timestamp\":\"" + TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "\"" + 
        "}";
    
    uchar data[];
    if (StringToCharArray(ohlc_json, data) > 0) {
        if (zmq_send(g_tick_publisher, data, ArraySize(data) - 1, 0) <= 0) {
            // Don't spam logs with OHLC send failures
        }
    }
}

//+------------------------------------------------------------------+
//| Check for unified commands (non-blocking) - DEALER SOCKET        |
//+------------------------------------------------------------------+
void CheckUnifiedCommands()
{
    uchar buffer[4096];
    ArrayInitialize(buffer, 0);
    
    int bytes = zmq_recv(g_command_receiver, buffer, 4096, ZMQ_DONTWAIT);
    
    if (bytes > 0) {
        string command = CharArrayToString(buffer, 0, bytes);
        
        // With DEALER socket, we already receive only our messages (filtered by ROUTER)
        // But still verify target_uuid for extra security
        string command_uuid = ExtractJsonValue(command, "target_uuid");
        if (command_uuid != "" && command_uuid != g_user_uuid) {
            Print("⚠️ Received command for wrong UUID: ", command_uuid, " (expected: ", g_user_uuid, ")");
            return;
        }
        
        // Extract command type for unified dispatching
        string command_type = ExtractJsonValue(command, "type");
        
        Print("⚡ TARGETED COMMAND received via DEALER for UUID: ", g_user_uuid, " Type: ", command_type);
        
        // UNIFIED COMMAND DISPATCHER
        if (command_type == "fire") {
            ExecuteFireCommand(command);
        } else if (command_type == "close_all") {
            ExecuteCloseAllCommand(command);
        } else if (command_type == "close_ticket") {
            ExecuteCloseTicketCommand(command);
        } else if (command_type == "ping") {
            SendPingResponse(command);
        } else {
            Print("⚠️ Unknown command type: ", command_type);
            SendCommandConfirmation("unknown", false, 0, 0, 0, "Unknown command type: " + command_type, "");
        }
        
    } else if (bytes < 0) {
        // errno 11 (EAGAIN) is normal for non-blocking recv when no data
        int err = GetLastError();
        if (err != 11) {
            Print("⚠️ ZMQ recv error, errno: ", err);
        }
    }
}

//+------------------------------------------------------------------+
//| Send ping response                                               |
//+------------------------------------------------------------------+
void SendPingResponse(string json_command)
{
    string ping_id = ExtractJsonValue(json_command, "ping_id");
    
    string pong = "{" +
        "\"type\":\"pong\"," +
        "\"ping_id\":\"" + ping_id + "\"," +
        "\"node_id\":\"" + g_node_id + "\"," +
        "\"user_uuid\":\"" + g_user_uuid + "\"," +
        "\"timestamp\":\"" + TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "\"" +
        "}";
    
    uchar data[];
    if (StringToCharArray(pong, data) > 0) {
        if (zmq_send(g_confirm_sender, data, ArraySize(data) - 1, 0) > 0) {
            Print("✅ PONG sent for ping_id: ", ping_id);
        }
    }
}

//+------------------------------------------------------------------+
//| Execute BITMODE hybrid position management                       |
//+------------------------------------------------------------------+
void ExecuteHybridPosition(string json_command, string fire_id, string symbol, string direction, 
                          double entry, double sl, double tp, double total_lot)
{
    // Extract hybrid parameters using simple string search
    int p1_trigger = 8, p1_percent = 25;  // defaults
    int p2_trigger = 12, p2_percent = 25; // defaults  
    int trail_dist = 8;                   // default
    
    // Parse trigger values from JSON
    int pos = StringFind(json_command, "\"trigger\":");
    if (pos >= 0) {
        string temp = StringSubstr(json_command, pos + 10, 5);
        p1_trigger = (int)StringToInteger(temp);
    }
    
    pos = StringFind(json_command, "\"trigger\":", pos + 1);
    if (pos >= 0) {
        string temp = StringSubstr(json_command, pos + 10, 5);
        p2_trigger = (int)StringToInteger(temp);
    }
    
    pos = StringFind(json_command, "\"distance\":");
    if (pos >= 0) {
        string temp = StringSubstr(json_command, pos + 11, 5);
        trail_dist = (int)StringToInteger(temp);
    }
    
    // Calculate position sizes
    double p1_lot = NormalizeDouble(total_lot * 0.25, 2);  // 25%
    double p2_lot = NormalizeDouble(total_lot * 0.25, 2);  // 25% 
    double trail_lot = NormalizeDouble(total_lot - p1_lot - p2_lot, 2); // remaining 50%
    
    Print("🎯 HYBRID EXECUTION: ", symbol, " ", direction, " Total: ", DoubleToString(total_lot,2));
    Print("   P1: ", DoubleToString(p1_lot,2), " lots @ +", p1_trigger, "pips");
    Print("   P2: ", DoubleToString(p2_lot,2), " lots @ +", p2_trigger, "pips"); 
    Print("   Trail: ", DoubleToString(trail_lot,2), " lots, trail: ", trail_dist, "pips");
    
    bool is_buy = (direction == "BUY" || direction == "buy");
    double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
    double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
    double pip_size = SymbolInfoDouble(symbol, SYMBOL_POINT);
    
    // Adjust pip size for different symbol types
    if (StringFind(symbol, "JPY") >= 0) pip_size = 0.01;
    else if (symbol == "XAUUSD") pip_size = 0.1;
    
    int tickets_opened = 0;
    long main_ticket = 0;
    double avg_price = 0;
    
    // Execute Position 1 - Early profit taking
    MqlTradeRequest rq1; MqlTradeResult rs1; ZeroMemory(rq1); ZeroMemory(rs1);
    rq1.action = TRADE_ACTION_DEAL;
    rq1.symbol = symbol;
    rq1.volume = p1_lot;
    rq1.deviation = 3;
    rq1.magic = 7176191872;
    rq1.comment = fire_id + "_P1";
    rq1.type = is_buy ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
    rq1.price = is_buy ? ask : bid;
    
    // Calculate P1 TP
    if (is_buy) {
        rq1.tp = rq1.price + (p1_trigger * pip_size);
        rq1.sl = (sl > 0 && sl < rq1.price) ? sl : 0;
    } else {
        rq1.tp = rq1.price - (p1_trigger * pip_size);
        rq1.sl = (sl > 0 && sl > rq1.price) ? sl : 0;
    }
    
    if (OrderSend(rq1, rs1) && rs1.retcode == TRADE_RETCODE_DONE) {
        tickets_opened++;
        main_ticket = rs1.order;
        avg_price += rs1.price;
        Print("✅ P1 opened: Ticket ", rs1.order, " TP @ ", DoubleToString(rq1.tp, 5));
    }
    
    // Execute Position 2 - Medium profit taking
    MqlTradeRequest rq2; MqlTradeResult rs2; ZeroMemory(rq2); ZeroMemory(rs2);
    rq2.action = TRADE_ACTION_DEAL;
    rq2.symbol = symbol;
    rq2.volume = p2_lot;
    rq2.deviation = 3;
    rq2.magic = 7176191872;
    rq2.comment = fire_id + "_P2";
    rq2.type = is_buy ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
    rq2.price = is_buy ? ask : bid;
    
    // Calculate P2 TP
    if (is_buy) {
        rq2.tp = rq2.price + (p2_trigger * pip_size);
        rq2.sl = (sl > 0 && sl < rq2.price) ? sl : 0;
    } else {
        rq2.tp = rq2.price - (p2_trigger * pip_size);
        rq2.sl = (sl > 0 && sl > rq2.price) ? sl : 0;
    }
    
    if (OrderSend(rq2, rs2) && rs2.retcode == TRADE_RETCODE_DONE) {
        tickets_opened++;
        if (main_ticket == 0) main_ticket = rs2.order;
        avg_price += rs2.price;
        Print("✅ P2 opened: Ticket ", rs2.order, " TP @ ", DoubleToString(rq2.tp, 5));
    }
    
    // Execute Trail Position - No initial TP, will use trailing SL
    MqlTradeRequest rq3; MqlTradeResult rs3; ZeroMemory(rq3); ZeroMemory(rs3);
    rq3.action = TRADE_ACTION_DEAL;
    rq3.symbol = symbol;
    rq3.volume = trail_lot;
    rq3.deviation = 3;
    rq3.magic = 7176191872;
    rq3.comment = fire_id + "_TRAIL";
    rq3.type = is_buy ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
    rq3.price = is_buy ? ask : bid;
    
    // Trail position: SL only, no TP initially
    if (is_buy) {
        rq3.sl = (sl > 0 && sl < rq3.price) ? sl : 0;
        rq3.tp = 0; // No TP - will trail
    } else {
        rq3.sl = (sl > 0 && sl > rq3.price) ? sl : 0;
        rq3.tp = 0; // No TP - will trail
    }
    
    if (OrderSend(rq3, rs3) && rs3.retcode == TRADE_RETCODE_DONE) {
        tickets_opened++;
        if (main_ticket == 0) main_ticket = rs3.order;
        avg_price += rs3.price;
        Print("✅ Trail opened: Ticket ", rs3.order, " - will trail at ", trail_dist, " pips");
    }
    
    // Calculate average price and send confirmation
    if (tickets_opened > 0) {
        avg_price = avg_price / tickets_opened;
        string msg = "HYBRID: " + IntegerToString(tickets_opened) + "/3 positions opened";
        SendCommandConfirmation("fire", true, main_ticket, avg_price, total_lot, msg, fire_id);
        Print("✅ HYBRID COMPLETE: ", tickets_opened, " positions opened for [", fire_id, "]");
    } else {
        SendCommandConfirmation("fire", false, 0, 0, total_lot, "HYBRID failed: No positions opened", fire_id);
        Print("❌ HYBRID FAILED: No positions opened for [", fire_id, "]");
    }
}

//+------------------------------------------------------------------+
//| Execute fire command - WITH FIRE_ID TRACKING                    |
//+------------------------------------------------------------------+
void ExecuteFireCommand(string json_command)
{
    // Extract fire_id for tracking
    string fire_id = ExtractJsonValue(json_command, "fire_id");
    string symbol = ExtractJsonValue(json_command, "symbol");
    
    // Accept both "direction" and "side" fields for compatibility
    string direction = ExtractJsonValue(json_command, "direction");
    if (direction == "") direction = ExtractJsonValue(json_command, "side");
    
    double entry = StringToDouble(ExtractJsonValue(json_command, "entry"));
    double sl = StringToDouble(ExtractJsonValue(json_command, "sl"));
    double tp = StringToDouble(ExtractJsonValue(json_command, "tp"));
    double lot = StringToDouble(ExtractJsonValue(json_command, "lot"));
    
    // *** BITMODE HYBRID DETECTION - FIXED JSON PARSING ***
    bool is_hybrid = false;
    if (StringFind(json_command, "\"hybrid\":{\"enabled\":true") >= 0) {
        is_hybrid = true;
        Print("🎯 BITMODE HYBRID DETECTED for [", fire_id, "]");
        
        // Execute hybrid position management instead of standard trade
        ExecuteHybridPosition(json_command, fire_id, symbol, direction, entry, sl, tp, lot);
        return;
    }
    
    Print("🔥 Executing STANDARD FIRE [", fire_id, "] for UUID ", g_user_uuid, ": ", symbol, " Direction: ", direction, " Lot: ", lot, " Entry: ", entry, " SL: ", sl, " TP: ", tp);
    
    // Verify symbol is available in MarketWatch
    if (!SymbolSelect(symbol, true)) {
        Print("❌ Symbol not available in MarketWatch: ", symbol);
        SendCommandConfirmation("fire", false, 0, 0, lot, "Symbol not available: " + symbol, fire_id);
        return;
    }
    
    MqlTradeRequest request;
    MqlTradeResult result;
    
    ZeroMemory(request);
    ZeroMemory(result);
    
    request.action = TRADE_ACTION_DEAL;
    request.symbol = symbol;
    request.volume = (lot <= 0) ? 0.01 : lot;
    request.deviation = 3;
    request.magic = 7176191872; // BITTEN magic number
    request.comment = fire_id != "" ? fire_id : "BITTEN_DEALER";
    
    double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
    double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
    
    if (bid == 0 || ask == 0) {
        Print("❌ No quotes for symbol: ", symbol);
        SendCommandConfirmation("fire", false, 0, 0, lot, "No quotes available for " + symbol, fire_id);
        return;
    }
    
    // Use explicit direction from command, fallback to old logic if not provided
    bool is_buy;
    if (direction != "") {
        is_buy = (direction == "BUY" || direction == "buy");
        Print("🎯 Using explicit direction: ", direction);
    } else {
        // Fallback to old logic if no direction provided
        is_buy = (entry == 0) ? true : (MathAbs(entry - ask) < MathAbs(entry - bid));
        Print("⚠️ No direction provided, guessing: ", is_buy ? "BUY" : "SELL");
    }
    
    request.type = is_buy ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
    request.price = is_buy ? ask : bid;
    
    // STRICT SL/TP ENFORCEMENT WITH DIRECTION VALIDATION
    // Assign SL/TP based on trade direction to prevent 4756 errors
    if (is_buy) {
        // BUY: SL must be below price, TP must be above price
        request.sl = (sl > 0 && sl < request.price) ? sl : 0;
        request.tp = (tp > 0 && tp > request.price) ? tp : 0;
    } else {
        // SELL: SL must be above price, TP must be below price
        request.sl = (sl > 0 && sl > request.price) ? sl : 0;
        request.tp = (tp > 0 && tp < request.price) ? tp : 0;
    }
    
    Print("🔧 Direction: ", is_buy ? "BUY" : "SELL", " Price: ", DoubleToString(request.price, 5));
    Print("🔧 Original SL: ", DoubleToString(sl, 5), " TP: ", DoubleToString(tp, 5));
    Print("🔧 Final SL: ", DoubleToString(request.sl, 5), " TP: ", DoubleToString(request.tp, 5));
    
    // Execute the order with strict enforcement
    if (OrderSend(request, result)) {
        Print("✅ Trade executed [", fire_id, "] for UUID ", g_user_uuid, "! Symbol: ", symbol, " Ticket: ", result.order, " Price: ", result.price);
        
        // Use the actual execution price from broker
        double confirmed_price = (result.price > 0) ? result.price : request.price;
        
        SendCommandConfirmation("fire", true, result.order, confirmed_price, lot, "Trade executed successfully via DEALER", fire_id);
    } else {
        int error_code = GetLastError();
        Print("❌ Trade failed [", fire_id, "] for UUID ", g_user_uuid, ": Symbol: ", symbol, " Error: ", error_code, " Result: ", result.retcode);
        
        // Send detailed failure information back to core brain
        string error_msg = "Trade execution failed - Error: " + IntegerToString(error_code) + " Result: " + IntegerToString(result.retcode);
        if (error_code == 10016 || StringFind(error_msg, "stops") >= 0) {
            error_msg += " (Invalid SL/TP - Core brain should adjust)";
        }
        
        SendCommandConfirmation("fire", false, 0, 0, lot, error_msg, fire_id);
    }
}

//+------------------------------------------------------------------+
//| Execute close all command                                        |
//+------------------------------------------------------------------+
void ExecuteCloseAllCommand(string json_command)
{
    Print("🛑 Executing CLOSE_ALL for UUID ", g_user_uuid);
    
    int positions_closed = 0;
    int positions_failed = 0;
    double total_closed_volume = 0;
    
    // Iterate through all open positions
    for (int i = PositionsTotal() - 1; i >= 0; i--) {
        if (PositionGetTicket(i) > 0) {
            string pos_symbol = PositionGetString(POSITION_SYMBOL);
            long pos_magic = PositionGetInteger(POSITION_MAGIC);
            
            // Only close positions with BITTEN magic number
            if (pos_magic == 7176191872) {
                long ticket = PositionGetInteger(POSITION_TICKET);
                double volume = PositionGetDouble(POSITION_VOLUME);
                
                if (ClosePositionByTicket(ticket)) {
                    positions_closed++;
                    total_closed_volume += volume;
                    Print("✅ Closed position: ", ticket, " Symbol: ", pos_symbol, " Volume: ", volume);
                } else {
                    positions_failed++;
                    Print("❌ Failed to close position: ", ticket, " Symbol: ", pos_symbol);
                }
            }
        }
    }
    
    string result_msg = "Closed " + IntegerToString(positions_closed) + " positions, " + 
                       IntegerToString(positions_failed) + " failed, Total volume: " + 
                       DoubleToString(total_closed_volume, 2);
    
    Print("🛑 CLOSE_ALL completed: ", result_msg);
    SendCloseConfirmation("close_all", (positions_failed == 0), 0, 0, total_closed_volume, result_msg);
}

//+------------------------------------------------------------------+
//| Execute close ticket command                                     |
//+------------------------------------------------------------------+
void ExecuteCloseTicketCommand(string json_command)
{
    long ticket = StringToInteger(ExtractJsonValue(json_command, "ticket"));
    
    Print("🛑 Executing CLOSE_TICKET for UUID ", g_user_uuid, ": Ticket ", ticket);
    
    if (ticket <= 0) {
        Print("❌ Invalid ticket number: ", ticket);
        SendCloseConfirmation("close_ticket", false, ticket, 0, 0, "Invalid ticket number");
        return;
    }
    
    // Select the position by ticket
    if (!PositionSelectByTicket(ticket)) {
        Print("❌ Position not found: ", ticket);
        SendCloseConfirmation("close_ticket", false, ticket, 0, 0, "Position not found");
        return;
    }
    
    // Verify it's a BITTEN position
    long pos_magic = PositionGetInteger(POSITION_MAGIC);
    if (pos_magic != 7176191872) {
        Print("❌ Position not owned by BITTEN: ", ticket, " Magic: ", pos_magic);
        SendCloseConfirmation("close_ticket", false, ticket, 0, 0, "Position not owned by BITTEN");
        return;
    }
    
    string symbol = PositionGetString(POSITION_SYMBOL);
    double volume = PositionGetDouble(POSITION_VOLUME);
    
    if (ClosePositionByTicket(ticket)) {
        Print("✅ Successfully closed position: ", ticket, " Symbol: ", symbol, " Volume: ", volume);
        SendCloseConfirmation("close_ticket", true, ticket, 0, volume, "Position closed successfully");
    } else {
        Print("❌ Failed to close position: ", ticket);
        SendCloseConfirmation("close_ticket", false, ticket, 0, volume, "Failed to close position");
    }
}

//+------------------------------------------------------------------+
//| Close position by ticket                                         |
//+------------------------------------------------------------------+
bool ClosePositionByTicket(long ticket)
{
    if (!PositionSelectByTicket(ticket)) {
        return false;
    }
    
    MqlTradeRequest request;
    MqlTradeResult result;
    
    ZeroMemory(request);
    ZeroMemory(result);
    
    request.action = TRADE_ACTION_DEAL;
    request.position = ticket;
    request.symbol = PositionGetString(POSITION_SYMBOL);
    request.volume = PositionGetDouble(POSITION_VOLUME);
    request.deviation = 3;
    request.magic = 7176191872;
    request.comment = "BITTEN_CLOSE";
    
    // Determine close direction
    ENUM_POSITION_TYPE pos_type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
    if (pos_type == POSITION_TYPE_BUY) {
        request.type = ORDER_TYPE_SELL;
        request.price = SymbolInfoDouble(request.symbol, SYMBOL_BID);
    } else {
        request.type = ORDER_TYPE_BUY;
        request.price = SymbolInfoDouble(request.symbol, SYMBOL_ASK);
    }
    
    return OrderSend(request, result);
}

//+------------------------------------------------------------------+
//| Send command confirmation WITH FIRE_ID                          |
//+------------------------------------------------------------------+
void SendCommandConfirmation(string command_type, bool success, long ticket, double price, double lot, string message, string fire_id)
{
    string status = success ? "success" : "failed";
    
    string confirmation = "{" + 
        "\"type\":\"confirmation\"," + 
        "\"command_type\":\"" + command_type + "\"," +
        "\"fire_id\":\"" + fire_id + "\"," +
        "\"node_id\":\"" + g_node_id + "\"," + 
        "\"user_uuid\":\"" + g_user_uuid + "\"," +
        "\"status\":\"" + status + "\"," + 
        "\"ticket\":" + IntegerToString(ticket) + "," + 
        "\"price\":" + DoubleToString(price, 5) + "," + 
        "\"lot\":" + DoubleToString(lot, 2) + "," + 
        "\"message\":\"" + message + "\"," +
        "\"account\":" + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)) + "," +
        "\"currency\":\"" + AccountInfoString(ACCOUNT_CURRENCY) + "\"," + 
        "\"balance\":" + DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2) + "," + 
        "\"equity\":" + DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2) + "," + 
        "\"free_margin\":" + DoubleToString(AccountInfoDouble(ACCOUNT_FREEMARGIN), 2) + "," + 
        "\"margin_level\":" + DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN_LEVEL), 2) + "," + 
        "\"timestamp\":\"" + TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "\"" + 
        "}";
    
    uchar data[];
    if (StringToCharArray(confirmation, data) > 0) {
        if (zmq_send(g_confirm_sender, data, ArraySize(data) - 1, 0) > 0) {
            if (fire_id != "") {
                Print("✅ Confirmation sent: ", status, " for fire_id: ", fire_id);
            } else {
                Print("✅ Confirmation sent: ", status, " for ", command_type);
            }
        } else {
            Print("⚠️ Failed to send confirmation, errno: ", GetLastError());
        }
    } else {
        Print("⚠️ Failed to convert confirmation to char array");
    }
}

//+------------------------------------------------------------------+
//| Send close confirmation                                          |
//+------------------------------------------------------------------+
void SendCloseConfirmation(string command_type, bool success, long ticket, double close_price, double lot, string message)
{
    string status = success ? "success" : "failed";
    
    string confirmation = "{" + 
        "\"type\":\"close_confirmation\"," + 
        "\"command_type\":\"" + command_type + "\"," +
        "\"node_id\":\"" + g_node_id + "\"," + 
        "\"user_uuid\":\"" + g_user_uuid + "\"," +
        "\"status\":\"" + status + "\"," + 
        "\"ticket\":" + IntegerToString(ticket) + "," + 
        "\"close_price\":" + DoubleToString(close_price, 5) + "," + 
        "\"lot\":" + DoubleToString(lot, 2) + "," + 
        "\"message\":\"" + message + "\"," +
        "\"account\":" + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)) + "," +
        "\"currency\":\"" + AccountInfoString(ACCOUNT_CURRENCY) + "\"," + 
        "\"balance\":" + DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2) + "," + 
        "\"equity\":" + DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2) + "," + 
        "\"free_margin\":" + DoubleToString(AccountInfoDouble(ACCOUNT_FREEMARGIN), 2) + "," + 
        "\"margin_level\":" + DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN_LEVEL), 2) + "," + 
        "\"timestamp\":\"" + TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "\"" + 
        "}";
    
    uchar data[];
    if (StringToCharArray(confirmation, data) > 0) {
        if (zmq_send(g_confirm_sender, data, ArraySize(data) - 1, 0) > 0) {
            Print("✅ Close confirmation sent: ", status, " for ", command_type);
        } else {
            Print("⚠️ Failed to send close confirmation, errno: ", GetLastError());
        }
    } else {
        Print("⚠️ Failed to convert close confirmation to char array");
    }
}

//+------------------------------------------------------------------+
//| Extract JSON value by key                                        |
//+------------------------------------------------------------------+
string ExtractJsonValue(string json, string key)
{
    string search = "\"" + key + "\":";
    int start = StringFind(json, search);
    if (start == -1) return "";
    
    start += StringLen(search);
    
    // Skip whitespace
    while (start < StringLen(json) && (StringGetCharacter(json, start) == ' ' || StringGetCharacter(json, start) == '\t')) {
        start++;
    }
    
    if (start >= StringLen(json)) return "";
    
    int end;
    if (StringGetCharacter(json, start) == '"') {
        // String value
        start++; // Skip opening quote
        end = start;
        while (end < StringLen(json) && StringGetCharacter(json, end) != '"') {
            end++;
        }
    } else {
        // Numeric or boolean value
        end = start;
        while (end < StringLen(json) && 
               StringGetCharacter(json, end) != ',' && 
               StringGetCharacter(json, end) != '}' && 
               StringGetCharacter(json, end) != ']') {
            end++;
        }
    }
    
    if (end > start) {
        return StringSubstr(json, start, end - start);
    }
    
    return "";
}