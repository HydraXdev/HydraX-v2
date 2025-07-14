//+------------------------------------------------------------------+
//|                                          BITTEN_Heartbeat_24_7.mq5 |
//|                                        BITTEN 24/7 Heartbeat System |
//|                              Ensures connection NEVER goes down    |
//+------------------------------------------------------------------+
#property copyright "BITTEN Trading System"
#property link      "https://joinbitten.com"
#property version   "1.00"
#property strict

// Input parameters
input string InpDataPath = "C:\\MT5_BITTEN\\";     // Path for heartbeat files
input int InpHeartbeatInterval = 1000;             // Heartbeat interval (ms)
input bool InpAutoReconnect = true;                // Auto-reconnect on failure
input int InpMaxReconnectAttempts = 100;           // Max reconnection attempts

// Global variables
datetime lastHeartbeat;
int reconnectAttempts = 0;
bool isConnected = false;
string HeartbeatFile = "bitten_heartbeat.txt";
string StatusFile = "bitten_status.json";

//+------------------------------------------------------------------+
//| Expert initialization function                                    |
//+------------------------------------------------------------------+
int OnInit()
{
   // Ensure connection on start
   EnsureConnection();
   
   // Start heartbeat timer
   EventSetMillisecondTimer(InpHeartbeatInterval);
   
   // Initial heartbeat
   WriteHeartbeat();
   
   Print("✅ BITTEN 24/7 Heartbeat System started");
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                  |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   
   // Write shutdown status
   WriteStatus("SHUTDOWN", "EA stopped: " + GetReasonText(reason));
}

//+------------------------------------------------------------------+
//| Timer function - Main heartbeat                                   |
//+------------------------------------------------------------------+
void OnTimer()
{
   // Check connection status
   if(!TerminalInfoInteger(TERMINAL_CONNECTED))
   {
      HandleDisconnection();
      return;
   }
   
   // Check trade server connection
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED))
   {
      HandleTradeDisabled();
      return;
   }
   
   // All good - write heartbeat
   isConnected = true;
   reconnectAttempts = 0;
   WriteHeartbeat();
   
   // Also update comprehensive status
   UpdateSystemStatus();
}

//+------------------------------------------------------------------+
//| Handle disconnection                                              |
//+------------------------------------------------------------------+
void HandleDisconnection()
{
   isConnected = false;
   WriteStatus("DISCONNECTED", "No connection to broker");
   
   if(InpAutoReconnect && reconnectAttempts < InpMaxReconnectAttempts)
   {
      reconnectAttempts++;
      Print("⚠️ Connection lost! Attempt #", reconnectAttempts, " to reconnect...");
      
      // Try to reconnect
      if(ReconnectToBroker())
      {
         Print("✅ Reconnection successful!");
         isConnected = true;
         reconnectAttempts = 0;
      }
      else
      {
         // Write alert file for external monitor
         WriteAlert("CONNECTION_LOST", "Failed to reconnect after " + IntegerToString(reconnectAttempts) + " attempts");
      }
   }
}

//+------------------------------------------------------------------+
//| Handle trade disabled                                             |
//+------------------------------------------------------------------+
void HandleTradeDisabled()
{
   WriteStatus("TRADE_DISABLED", "Trading not allowed");
   
   // Check if it's due to market closed
   if(!IsMarketOpen())
   {
      WriteStatus("MARKET_CLOSED", "Market is closed");
   }
   else
   {
      // Something wrong - alert
      WriteAlert("TRADE_DISABLED", "Trading disabled but market is open!");
   }
}

//+------------------------------------------------------------------+
//| Write heartbeat file                                              |
//+------------------------------------------------------------------+
void WriteHeartbeat()
{
   int handle = FileOpen(InpDataPath + HeartbeatFile, FILE_WRITE|FILE_TXT|FILE_ANSI);
   if(handle != INVALID_HANDLE)
   {
      string data = TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "|";
      data += DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2) + "|";
      data += DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2) + "|";
      data += IntegerToString(PositionsTotal()) + "|";
      data += "ALIVE";
      
      FileWriteString(handle, data);
      FileClose(handle);
      
      lastHeartbeat = TimeCurrent();
   }
}

//+------------------------------------------------------------------+
//| Write status file                                                 |
//+------------------------------------------------------------------+
void WriteStatus(string status, string message)
{
   int handle = FileOpen(InpDataPath + StatusFile, FILE_WRITE|FILE_TXT|FILE_ANSI);
   if(handle != INVALID_HANDLE)
   {
      string json = "{";
      json += "\"status\":\"" + status + "\",";
      json += "\"message\":\"" + message + "\",";
      json += "\"timestamp\":\"" + TimeToString(TimeCurrent()) + "\",";
      json += "\"account_connected\":" + (TerminalInfoInteger(TERMINAL_CONNECTED) ? "true" : "false") + ",";
      json += "\"trade_allowed\":" + (TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) ? "true" : "false") + ",";
      json += "\"expert_enabled\":" + (TerminalInfoInteger(TERMINAL_EXPERTS_ENABLED) ? "true" : "false") + ",";
      json += "\"positions_open\":" + IntegerToString(PositionsTotal()) + ",";
      json += "\"reconnect_attempts\":" + IntegerToString(reconnectAttempts);
      json += "}";
      
      FileWriteString(handle, json);
      FileClose(handle);
   }
}

//+------------------------------------------------------------------+
//| Write alert file for critical issues                              |
//+------------------------------------------------------------------+
void WriteAlert(string alert_type, string details)
{
   string filename = "ALERT_" + alert_type + "_" + IntegerToString(GetTickCount()) + ".txt";
   int handle = FileOpen(InpDataPath + filename, FILE_WRITE|FILE_TXT|FILE_ANSI);
   if(handle != INVALID_HANDLE)
   {
      FileWriteString(handle, details);
      FileClose(handle);
   }
}

//+------------------------------------------------------------------+
//| Update comprehensive system status                                 |
//+------------------------------------------------------------------+
void UpdateSystemStatus()
{
   // Check various system components
   bool dataFlowing = CheckDataFlow();
   bool ordersWorking = CheckOrderSystem();
   bool accountOk = CheckAccountStatus();
   
   if(dataFlowing && ordersWorking && accountOk)
   {
      WriteStatus("HEALTHY", "All systems operational");
   }
   else
   {
      string issues = "";
      if(!dataFlowing) issues += "DataFlow ";
      if(!ordersWorking) issues += "Orders ";
      if(!accountOk) issues += "Account ";
      
      WriteStatus("DEGRADED", "Issues: " + issues);
   }
}

//+------------------------------------------------------------------+
//| Check if data is flowing                                          |
//+------------------------------------------------------------------+
bool CheckDataFlow()
{
   static datetime lastTickTime = 0;
   static double lastPrice = 0;
   
   double currentPrice = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   datetime currentTime = TimeCurrent();
   
   // Check if price changed or time advanced
   if(currentPrice != lastPrice || currentTime != lastTickTime)
   {
      lastPrice = currentPrice;
      lastTickTime = currentTime;
      return true;
   }
   
   // No change for more than 30 seconds during market hours
   if(IsMarketOpen() && (currentTime - lastTickTime) > 30)
   {
      return false;
   }
   
   return true;
}

//+------------------------------------------------------------------+
//| Check order system                                                |
//+------------------------------------------------------------------+
bool CheckOrderSystem()
{
   // Try to check if we can place orders
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED))
      return false;
   
   // Check if symbol is available for trading
   if(!SymbolInfoInteger(_Symbol, SYMBOL_TRADE_MODE))
      return false;
   
   return true;
}

//+------------------------------------------------------------------+
//| Check account status                                              |
//+------------------------------------------------------------------+
bool CheckAccountStatus()
{
   // Check margin level
   double marginLevel = AccountInfoDouble(ACCOUNT_MARGIN_LEVEL);
   if(marginLevel > 0 && marginLevel < 100)  // Below 100% margin
      return false;
   
   // Check if account is real and active
   if(AccountInfoInteger(ACCOUNT_TRADE_MODE) == ACCOUNT_TRADE_MODE_DEMO)
   {
      // Demo account - still ok but note it
      WriteStatus("DEMO_MODE", "Running on demo account");
   }
   
   return true;
}

//+------------------------------------------------------------------+
//| Ensure connection on startup                                      |
//+------------------------------------------------------------------+
void EnsureConnection()
{
   int attempts = 0;
   while(!TerminalInfoInteger(TERMINAL_CONNECTED) && attempts < 30)
   {
      Print("Waiting for connection... Attempt ", attempts + 1);
      Sleep(1000);
      attempts++;
   }
   
   if(TerminalInfoInteger(TERMINAL_CONNECTED))
   {
      Print("✅ Connected to broker");
   }
   else
   {
      Print("❌ Failed to connect after 30 seconds");
      WriteAlert("STARTUP_FAILURE", "Could not connect to broker on startup");
   }
}

//+------------------------------------------------------------------+
//| Try to reconnect to broker                                        |
//+------------------------------------------------------------------+
bool ReconnectToBroker()
{
   // MT5 usually auto-reconnects, but we can try to force it
   // by refreshing symbol data
   SymbolInfoDouble(_Symbol, SYMBOL_BID);
   Sleep(2000);
   
   return TerminalInfoInteger(TERMINAL_CONNECTED);
}

//+------------------------------------------------------------------+
//| Check if market is open                                           |
//+------------------------------------------------------------------+
bool IsMarketOpen()
{
   datetime currentTime = TimeCurrent();
   MqlDateTime dt;
   TimeToStruct(currentTime, dt);
   
   // Forex market closed from Friday 22:00 to Sunday 22:00 (broker time)
   if(dt.day_of_week == 0 || dt.day_of_week == 6)  // Sunday or Saturday
      return false;
   
   if(dt.day_of_week == 5 && dt.hour >= 22)  // Friday after 22:00
      return false;
   
   return true;
}

//+------------------------------------------------------------------+
//| Get disconnection reason text                                     |
//+------------------------------------------------------------------+
string GetReasonText(int reason)
{
   switch(reason)
   {
      case REASON_PROGRAM: return "Program terminated";
      case REASON_REMOVE: return "Removed from chart";
      case REASON_RECOMPILE: return "Recompiled";
      case REASON_CHARTCHANGE: return "Chart changed";
      case REASON_CHARTCLOSE: return "Chart closed";
      case REASON_PARAMETERS: return "Parameters changed";
      case REASON_ACCOUNT: return "Account changed";
      case REASON_TEMPLATE: return "Template applied";
      case REASON_INITFAILED: return "Initialization failed";
      case REASON_CLOSE: return "Terminal closed";
      default: return "Unknown reason";
   }
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
   // Additional tick-based monitoring can go here
   // Main work is done in OnTimer for reliability
}
//+------------------------------------------------------------------+