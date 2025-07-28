//+------------------------------------------------------------------+
//|                                        BITTENBridge_Close_Enabled.mq5 |
//|       2-Way Execution + Close Command Support for BITTEN System |
//+------------------------------------------------------------------+
#property strict

#include <Trade/Trade.mqh>
CTrade trade;

input string SignalFile = "fire.txt";
input string UUIDFile = "uuid.txt";
input string ReportURL = "https://terminus.joinbitten.com/report"; // Replace with your endpoint

string uuid = "unknown";
ulong last_ticket = 0;
string last_symbol = "";

int OnInit()
{
    Print("🟢 BITTENBridge with CLOSE initialized.");
    EventSetTimer(5);

    int h = FileOpen(UUIDFile, FILE_READ | FILE_TXT);
    if(h != INVALID_HANDLE)
    {
        uuid = FileReadString(h);
        FileClose(h);
        Print("📌 UUID loaded: ", uuid);
    }
    else
    {
        Print("⚠️ UUID file not found.");
    }

    return INIT_SUCCEEDED;
}

void OnTimer()
{
    // Write tick data for VENOM
    WriteTickData();
    
    // Check for signals
    string content;
    int handle = FileOpen(SignalFile, FILE_READ | FILE_TXT);
    if(handle == INVALID_HANDLE)
    {
        Print("📭 No fire.txt found.");
        return;
    }

    content = FileReadString(handle);
    FileClose(handle);

    string action = GetJSONValue(content, "action");
    string symbol = GetJSONValue(content, "symbol");
    string type = GetJSONValue(content, "type");
    string magicStr = GetJSONValue(content, "magic");
    double lot = StringToDouble(GetJSONValue(content, "lot"));
    double sl = StringToDouble(GetJSONValue(content, "sl"));
    double tp = StringToDouble(GetJSONValue(content, "tp"));
    long magic = (magicStr != "") ? StringToInteger(magicStr) : 0;

    if(symbol == "")
    {
        Print("❌ No symbol specified.");
        return;
    }

    if(!SymbolSelect(symbol, true))
    {
        Print("❌ Symbol not found in Market Watch: ", symbol);
        return;
    }

    if(action == "close")
    {
        CloseAllBySymbol(symbol);
        return;
    }

    if(type != "buy" && type != "sell")
    {
        Print("❌ Invalid trade type or action.");
        return;
    }

    if(symbol == last_symbol)
    {
        Print("⏱ Duplicate signal for ", symbol, ". Skipping.");
        return;
    }

    trade.SetExpertMagicNumber(magic > 0 ? magic : 777001);

    bool result = false;
    ulong ticket = 0;

    if(type == "buy")
        result = trade.Buy(lot, symbol, 0, sl, tp);
    else if(type == "sell")
        result = trade.Sell(lot, symbol, 0, sl, tp);

    if(result)
    {
        ticket = trade.ResultOrder();
        last_symbol = symbol;
        last_ticket = ticket;
        Print("✅ Trade executed. Ticket: ", ticket);
        ReportTrade(uuid, symbol, type, lot, sl, tp, ticket, "success");
    }
    else
    {
        string err = trade.ResultRetcodeDescription();
        Print("❌ Trade failed: ", err);
        ReportTrade(uuid, symbol, type, lot, sl, tp, 0, "fail: " + err);
    }
}

void CloseAllBySymbol(string sym)
{
    int total = PositionsTotal();
    int closed = 0;

    for(int i = total - 1; i >= 0; i--)
    {
        ulong ticket = PositionGetTicket(i);
        if(PositionGetString(POSITION_SYMBOL) == sym)
        {
            if(trade.PositionClose(ticket))
            {
                Print("✅ Closed position for ", sym);
                ReportTrade(uuid, sym, "close", 0, 0, 0, ticket, "closed");
                closed++;
            }
            else
            {
                Print("❌ Failed to close ", sym, ": ", trade.ResultRetcodeDescription());
                ReportTrade(uuid, sym, "close", 0, 0, 0, ticket, "fail: " + trade.ResultRetcodeDescription());
            }
        }
    }

    if(closed == 0)
        Print("ℹ️ No open positions found for ", sym);
}

void ReportTrade(string uid, string sym, string typ, double lot, double sl, double tp, ulong ticket, string status)
{
    char post[];
    string body = StringFormat(
        "{\"uuid\":\"%s\",\"symbol\":\"%s\",\"type\":\"%s\",\"lot\":%.2f,\"sl\":%.1f,\"tp\":%.1f,\"ticket\":%d,\"status\":\"%s\"}",
        uid, sym, typ, lot, sl, tp, ticket, status);
    StringToCharArray(body, post);
    char result[];
    string headers = "Content-Type: application/json\r\n";
    int code = WebRequest("POST", ReportURL, headers, 5000, post, result, headers);
    Print("📡 Report sent. Code: ", code);
}

string GetJSONValue(string json, string key)
{
    int pos = StringFind(json, "\"" + key + "\"");
    if(pos < 0) return "";

    int colon = StringFind(json, ":", pos);
    if(colon < 0) return "";

    int start = StringFind(json, "\"", colon + 1);
    if(start < 0) return "";

    int end = StringFind(json, "\"", start + 1);
    if(end < 0) return "";

    return StringSubstr(json, start + 1, end - start - 1);
}

void OnDeinit(const int reason)
{
    EventKillTimer();
    Print("🛑 BITTENBridge shut down.");
}

//+------------------------------------------------------------------+
//| Write real tick data for VENOM                                  |
//+------------------------------------------------------------------+
void WriteTickData()
{
    // Correct 15 pairs from HANDOVER.md
    string symbols[] = {"EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD",
                        "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY",
                        "XAUUSD", "GBPNZD", "GBPAUD", "EURAUD", "GBPCHF"};
    
    for(int i = 0; i < ArraySize(symbols); i++)
    {
        MqlTick tick;
        if(SymbolInfoTick(symbols[i], tick))
        {
            // Write individual tick file for each symbol
            string filename = "tick_data_" + symbols[i] + ".json";
            int fileHandle = FileOpen(filename, FILE_WRITE|FILE_TXT|FILE_ANSI);
            
            if(fileHandle != INVALID_HANDLE)
            {
                string data = "{";
                data += "\"symbol\": \"" + symbols[i] + "\",";
                data += "\"bid\": " + DoubleToString(tick.bid, (int)SymbolInfoInteger(symbols[i], SYMBOL_DIGITS)) + ",";
                data += "\"ask\": " + DoubleToString(tick.ask, (int)SymbolInfoInteger(symbols[i], SYMBOL_DIGITS)) + ",";
                data += "\"spread\": " + DoubleToString((tick.ask - tick.bid) / SymbolInfoDouble(symbols[i], SYMBOL_POINT), 1) + ",";
                data += "\"volume\": " + IntegerToString(tick.volume) + ",";
                data += "\"time\": " + IntegerToString(tick.time) + "}";
                
                FileWriteString(fileHandle, data);
                FileClose(fileHandle);
            }
        }
    }
}