#property strict #include <Trade/Trade.mqh> #include <Files/File.mqh>

input string TradeFile = "trade.json";            // Local sandbox path only input string ResponseFile = "response.json"; input int Slippage = 5; input int CheckIntervalSec = 2;

CTrade trade;

int OnInit() { Print("[INIT] FileBridgeEA initialized."); EventSetTimer(CheckIntervalSec); return INIT_SUCCEEDED; }

void OnDeinit(const int reason) { EventKillTimer(); }

void OnTimer() { string tradePath = TerminalInfoString(TERMINAL_DATA_PATH) + "\" + TradeFile; string responsePath = TerminalInfoString(TERMINAL_DATA_PATH) + "\" + ResponseFile;

if (!FileIsExist(tradePath)) {
    Print("[INFO] No trade file found.");
    return;
}

int fh = FileOpen(tradePath, FILE_READ | FILE_TXT);
if (fh == INVALID_HANDLE) {
    Print("[ERROR] Cannot open trade file. Code: ", GetLastError());
    return;
}

string raw = FileReadString(fh);
FileClose(fh);
if (raw == "") {
    Print("[WARN] trade.json is empty.");
    return;
}

Print("[READ] Raw JSON: ", raw);

string symbol = Extract(raw, "symbol");
double lot = StrToDouble(Extract(raw, "lot"));
double sl = StrToDouble(Extract(raw, "sl"));
double tp = StrToDouble(Extract(raw, "tp"));
string type = Extract(raw, "type");

if (symbol == "" || lot <= 0 || (type != "buy" && type != "sell")) {
    Print("[ERROR] Invalid trade parameters.");
    return;
}

ENUM_ORDER_TYPE orderType = (type == "buy") ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
double price = (orderType == ORDER_TYPE_BUY) ? SymbolInfoDouble(symbol, SYMBOL_ASK) : SymbolInfoDouble(symbol, SYMBOL_BID);
double sl_price = (orderType == ORDER_TYPE_BUY) ? price - sl * _Point : price + sl * _Point;
double tp_price = (orderType == ORDER_TYPE_BUY) ? price + tp * _Point : price - tp * _Point;

Print("[ACTION] ", type, " on ", symbol, " @ ", price, " SL=", sl_price, " TP=", tp_price);
trade.SetSlippage(Slippage);

string status = "error";
ulong ticket = 0;
if (trade.PositionOpen(symbol, orderType, lot, price, sl_price, tp_price)) {
    status = "filled";
    ticket = trade.ResultOrder();
    Print("[SUCCESS] Trade executed. Ticket: ", ticket);
} else {
    Print("[FAIL] ", trade.ResultRetcodeDescription());
}

double bal = AccountInfoDouble(ACCOUNT_BALANCE);
double eq = AccountInfoDouble(ACCOUNT_EQUITY);
string result = "{\"status\":\"" + status + "\",\"ticket\":" + (string)ticket + ",\"balance\":" + DoubleToString(bal,2) + ",\"equity\":" + DoubleToString(eq,2) + "}";

int fr = FileOpen(responsePath, FILE_WRITE | FILE_TXT);
if (fr != INVALID_HANDLE) {
    FileWrite(fr, result);
    FileClose(fr);
    Print("[RESULT] Response saved.");
}

FileDelete(tradePath);
Print("[CLEANUP] trade.json deleted.");

}

string Extract(string json, string key) { int i = StringFind(json, '"' + key + '"'); if (i == -1) return ""; i = StringFind(json, ":", i); if (i == -1) return ""; int start = i + 1; while (StringGetCharacter(json, start) == ' ' || StringGetCharacter(json, start) == '"') start++; int end = start; while (end < StringLen(json) && StringGetCharacter(json, end) != ',' && StringGetCharacter(json, end) != '"' && StringGetCharacter(json, end) != '}') end++; return StringSubstr(json, start, end - start); }

