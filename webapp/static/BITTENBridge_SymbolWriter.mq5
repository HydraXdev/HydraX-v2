//+------------------------------------------------------------------+
//|                          BITTENBridge_SymbolWriter.mq5          |
//|                    BITTEN Final Bridge Writer + Trailing Stop   |
//|                              Standalone Permanent Edition       |
//+------------------------------------------------------------------+
#property strict
#property version   "1.10"
#property description "BITTEN Final Bridge Writer + Trailing Stop Edition"

// Input parameters
input bool EnableTrailingStop = true;      // Enable trailing stops
input int TrailStart = 15;                 // Pips in profit before trailing activates
input int TrailDistance = 5;               // Distance behind price to trail

// Global variables
datetime lastUpdate = 0;

//+------------------------------------------------------------------+
int OnInit()
{
    Print("=== BITTEN Bridge Writer + Trailing Stop v1.10 Initialized ===");
    Print("📁 Common Data Path: ", TerminalInfoString(TERMINAL_COMMONDATA_PATH));
    Print("🎯 Bridge files path: ", TerminalInfoString(TERMINAL_COMMONDATA_PATH), "\\Files\\BITTEN\\");
    Print("🔁 Trailing Stops: ", EnableTrailingStop ? "ENABLED" : "DISABLED");
    Print("⚡ Update interval: 1 second");
    
    // Set 1-second timer
    EventSetTimer(1);
    
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    EventKillTimer();
    Print("BITTEN Bridge Writer stopped");
}

//+------------------------------------------------------------------+
void OnTimer()
{
    // Write bridge files every second
    WriteBridgeFiles();
    
    // Check trailing stops if enabled
    if (EnableTrailingStop)
    {
        CheckTrailingStops();
    }
}

//+------------------------------------------------------------------+
void WriteBridgeFiles()
{
    // Symbol list for APEX scanning
    string symbols[] = {"EURUSD","GBPUSD","USDJPY","USDCAD","AUDUSD","USDCHF","NZDUSD",
                       "EURGBP","EURJPY","GBPJPY","XAUUSD","GBPNZD","GBPAUD","EURAUD","GBPCHF"};
    
    for (int i = 0; i < ArraySize(symbols); i++)
    {
        // Force symbol selection
        SymbolSelect(symbols[i], true);
        
        if (SymbolInfoInteger(symbols[i], SYMBOL_SELECT))
        {
            // Get market data
            double bid = SymbolInfoDouble(symbols[i], SYMBOL_BID);
            double ask = SymbolInfoDouble(symbols[i], SYMBOL_ASK);
            double spread = (ask - bid) / SymbolInfoDouble(symbols[i], SYMBOL_POINT);
            
            // Create BITTEN subdirectory file
            string filename = "BITTEN\\" + symbols[i] + ".json";
            int handle = FileOpen(filename, FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_COMMON);
            
            if (handle != INVALID_HANDLE)
            {
                // Write JSON content
                string json = StringFormat(
                    "{\"symbol\":\"%s\",\"bid\":%.5f,\"ask\":%.5f,\"spread\":%.1f,\"timestamp\":\"%s\"}",
                    symbols[i], bid, ask, spread,
                    TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS)
                );
                
                FileWriteString(handle, json);
                FileClose(handle);
                
                // Debug output
                Print("✅ Wrote bridge file: ", symbols[i], ".json at ", 
                      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS));
            }
        }
    }
}

//+------------------------------------------------------------------+
void CheckTrailingStops()
{
    // Check all open positions
    for (int i = PositionsTotal() - 1; i >= 0; i--)
    {
        ulong ticket = PositionGetTicket(i);
        if (PositionSelectByTicket(ticket))
        {
            string symbol = PositionGetString(POSITION_SYMBOL);
            ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
            double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
            double currentSL = PositionGetDouble(POSITION_SL);
            
            // Get current market prices
            double currentPrice = (type == POSITION_TYPE_BUY) ? 
                                 SymbolInfoDouble(symbol, SYMBOL_BID) : 
                                 SymbolInfoDouble(symbol, SYMBOL_ASK);
            
            double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
            int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
            
            // Calculate profit in pips
            double profitPips = 0;
            if (type == POSITION_TYPE_BUY)
            {
                profitPips = (currentPrice - openPrice) / point;
            }
            else
            {
                profitPips = (openPrice - currentPrice) / point;
            }
            
            // Check if trailing should activate
            if (profitPips >= TrailStart)
            {
                double newSL = 0;
                bool shouldUpdate = false;
                
                if (type == POSITION_TYPE_BUY)
                {
                    // Trail behind current price by TrailDistance pips
                    newSL = NormalizeDouble(currentPrice - TrailDistance * point, digits);
                    
                    // Only move SL up (never down for BUY)
                    if (newSL > currentSL || currentSL == 0)
                    {
                        shouldUpdate = true;
                    }
                }
                else // SELL position
                {
                    // Trail above current price by TrailDistance pips
                    newSL = NormalizeDouble(currentPrice + TrailDistance * point, digits);
                    
                    // Only move SL down (never up for SELL)
                    if (newSL < currentSL || currentSL == 0)
                    {
                        shouldUpdate = true;
                    }
                }
                
                // Update stop loss if needed
                if (shouldUpdate)
                {
                    MqlTradeRequest request;
                    MqlTradeResult result;
                    
                    ZeroMemory(request);
                    request.action = TRADE_ACTION_SLTP;
                    request.position = ticket;
                    request.symbol = symbol;
                    request.sl = newSL;
                    request.tp = PositionGetDouble(POSITION_TP);
                    
                    if (OrderSend(request, result))
                    {
                        Print("🔁 Trailing SL moved for ", 
                              (type == POSITION_TYPE_BUY) ? "BUY" : "SELL",
                              " on ", symbol, " to ", DoubleToString(newSL, digits));
                    }
                }
            }
        }
    }
}

//+------------------------------------------------------------------+