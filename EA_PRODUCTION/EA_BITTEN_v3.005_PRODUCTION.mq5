//+------------------------------------------------------------------+
//| EA_BITTEN_v3.005_PRODUCTION.mq5                                  |
//| PRODUCTION: Hardened with keepalive, prefilter, SafeNum, tunable|
//| THIS IS THE LAW - ALL OTHER VERSIONS OBSOLETE                    |
//+------------------------------------------------------------------+
#property strict
#property version   "3.005"
#property copyright "BITTEN Systems"

#include <Trade/Trade.mqh>

//============================= INPUTS ==============================
input bool   InpVerboseLogging     = false;
input int    InpDeviationPoints    = 5;
input bool   InpStreamTicks        = true;
input bool   InpStreamPositions    = true;
input bool   InpDedupPositions     = true;
input int    InpMaxSymbols         = 200;
input int    InpTickScanSleepMs    = 0;

input string InpBridgeHost         = "134.199.204.67";
input int    InpTickPort           = 5556;
input int    InpCmdPort            = 5555;
input int    InpConfirmPort        = 5558;
input int    InpMetricsPort        = 5560;

input int    InpRouterBeatSec      = 5;
input int    InpSndHWM             = 10000;
input int    InpRcvHWM             = 1000;
input int    InpLingerMs           = 0;

//============================== ZMQ ================================
#define ZMQ_DEALER    5
#define ZMQ_PUSH      8
#define ZMQ_IDENTITY  5
#define ZMQ_DONTWAIT  1
#define ZMQ_RCVMORE   13
#define ZMQ_SNDHWM    23
#define ZMQ_RCVHWM    24
#define ZMQ_LINGER    17

#import "libzmq.dll"
ulong zmq_ctx_new();
int   zmq_ctx_term(ulong context);
ulong zmq_socket(ulong context, int type);
int   zmq_close(ulong socket);
int   zmq_connect(ulong socket, uchar &endpoint[]);
int   zmq_send(ulong socket, uchar &data[], int length, int flags);
int   zmq_recv(ulong socket, uchar &data[], int length, int flags);
int   zmq_setsockopt(ulong socket, int option, uchar &value[], int option_len);
int   zmq_getsockopt(ulong socket, int option, uchar &value[], int &optlen);
#import

//============================= GLOBALS =============================
ulong g_context=0, g_tick_pub=0, g_metrics_pub=0, g_cmd_dealer=0, g_confirm_pub=0;
string g_node_id="", g_user_uuid="";
ulong  g_magic = 7176191872;
datetime g_last_heartbeat=0;
datetime g_last_router_hb=0;
int      g_tick_count=0;
string   g_monitored_symbols[];
int      g_symbol_count=0;
CTrade   g_trade;
ulong    g_last_tickets[];
double   g_last_prices[];
double   g_last_pnls[];
int      g_pos_cache_size=0;

//============================= HELPERS =============================
int VolDigits(string sym){
   double step=SymbolInfoDouble(sym, SYMBOL_VOLUME_STEP);
   if(step<=0) return 2;
   double d = -MathLog10(step);
   if(d<0) d=0; if(d>8) d=8;
   return (int)MathRound(d);
}

double NormalizeLots(string sym, double lots){
   double step=SymbolInfoDouble(sym, SYMBOL_VOLUME_STEP);
   double minv=SymbolInfoDouble(sym, SYMBOL_VOLUME_MIN);
   double maxv=SymbolInfoDouble(sym, SYMBOL_VOLUME_MAX);
   if(step<=0) step=0.01;
   double n = MathRound(lots/step)*step;
   if(n<minv) n=minv;
   if(n>maxv) n=maxv;
   return NormalizeDouble(n, VolDigits(sym));
}

double SafeNum(double v, int digs=2){
   if(!MathIsValidNumber(v)) return 0.0;
   return NormalizeDouble(v, digs);
}

string CanonDir(string d){
   string u=d;
   StringToUpper(u);
   return (u=="BUY" || u=="LONG" || u=="B" || u=="L")?"BUY":"SELL";
}

void ZMQSetIdentity(ulong socket, string id){
   uchar buf[];
   StringToCharArray(id, buf, 0, WHOLE_ARRAY, CP_UTF8);
   int len=(ArraySize(buf)>0)?ArraySize(buf)-1:0;
   if(len>0) zmq_setsockopt(socket, ZMQ_IDENTITY, buf, len);
}

void ZMQTune(ulong s, int sndhwm, int rcvhwm, int linger_ms){
   uchar v[4];
   v[0]=(uchar)(sndhwm & 0xFF);
   v[1]=(uchar)((sndhwm>>8) & 0xFF);
   v[2]=(uchar)((sndhwm>>16) & 0xFF);
   v[3]=(uchar)((sndhwm>>24) & 0xFF);
   zmq_setsockopt(s, ZMQ_SNDHWM, v, 4);
   v[0]=(uchar)(rcvhwm & 0xFF);
   v[1]=(uchar)((rcvhwm>>8) & 0xFF);
   v[2]=(uchar)((rcvhwm>>16) & 0xFF);
   v[3]=(uchar)((rcvhwm>>24) & 0xFF);
   zmq_setsockopt(s, ZMQ_RCVHWM, v, 4);
   v[0]=(uchar)(linger_ms & 0xFF);
   v[1]=(uchar)((linger_ms>>8) & 0xFF);
   v[2]=(uchar)((linger_ms>>16) & 0xFF);
   v[3]=(uchar)((linger_ms>>24) & 0xFF);
   zmq_setsockopt(s, ZMQ_LINGER, v, 4);
}

int ZMQConnect(ulong socket, string endpoint){
   uchar ep[];
   StringToCharArray(endpoint, ep, 0, WHOLE_ARRAY, CP_UTF8);
   if(ArraySize(ep)==0 || ep[ArraySize(ep)-1]!=0){
      ArrayResize(ep, ArraySize(ep)+1);
      ep[ArraySize(ep)-1]=0;
   }
   return zmq_connect(socket, ep);
}

void ZMQSend(ulong socket, string payload){
   if(socket==0) return;
   uchar d[];
   StringToCharArray(payload, d, 0, WHOLE_ARRAY, CP_UTF8);
   int L=(ArraySize(d)>0)?ArraySize(d)-1:0;
   if(L<=0) return;
   zmq_send(socket, d, L, ZMQ_DONTWAIT);
}

bool ZMQRecvAll(ulong sock, string &out){
   out="";
   uchar buffer[16384];
   while(true){
      ArrayInitialize(buffer, 0);
      int n = zmq_recv(sock, buffer, 16384, ZMQ_DONTWAIT);
      if(n <= 0) return (StringLen(out) > 0);
      out += CharArrayToString(buffer, 0, n, CP_UTF8);
      uchar optbuf[4];
      ArrayInitialize(optbuf, 0);
      int optlen = 4;
      if(zmq_getsockopt(sock, ZMQ_RCVMORE, optbuf, optlen) != 0) break;
      int more = (int)optbuf[0] | ((int)optbuf[1]<<8) | ((int)optbuf[2]<<16) | ((int)optbuf[3]<<24);
      if(more == 0) break;
   }
   return (StringLen(out) > 0);
}

string Trim(string s){
   StringTrimLeft(s);
   StringTrimRight(s);
   return s;
}

string JsonEscape(const string s){
   string out="";
   for(int i=0; i<StringLen(s); i++){
      ushort ch = (ushort)StringGetCharacter(s, i);
      if(ch == '"')       { out += "\\\""; continue; }
      if(ch == '\\')      { out += "\\\\"; continue; }
      if(ch == 0x08)      { out += "\\b"; continue; }
      if(ch == 0x0C)      { out += "\\f"; continue; }
      if(ch == '\n')      { out += "\\n"; continue; }
      if(ch == '\r')      { out += "\\r"; continue; }
      if(ch == '\t')      { out += "\\t"; continue; }
      out += CharToString(ch);
   }
   return out;
}

string ExtractJsonValue(string json, string key){
   string needle="\""+key+"\"";
   int pos=StringFind(json, needle);
   if(pos<0) return "";
   int colon=StringFind(json, ":", pos+StringLen(needle));
   if(colon<0) return "";
   int i=colon+1, L=StringLen(json);
   while(i<L){
      int ch=StringGetCharacter(json, i);
      if(ch!=' ' && ch!='\t' && ch!='\r' && ch!='\n') break;
      i++;
   }
   if(i>=L) return "";
   if(StringGetCharacter(json, i)=='"'){
      i++;
      string out="";
      bool esc=false;
      for(int j=i; j<L; j++){
         int ch=StringGetCharacter(json, j);
         if(esc){ out+=CharToString((ushort)ch); esc=false; continue; }
         if(ch=='\\'){ esc=true; continue; }
         if(ch=='"') return Trim(out);
         out+=CharToString((ushort)ch);
      }
      return Trim(out);
   }
   int j=i;
   for(; j<L; j++){
      int ch=StringGetCharacter(json, j);
      if(ch==','||ch=='}'||ch==' '||ch=='\n'||ch=='\r'||ch=='\t') break;
   }
   string raw=(j>i)?StringSubstr(json, i, j-i):"";
   return Trim(raw);
}

double ExtractDouble(string json, string key, double defv){
   string v=ExtractJsonValue(json, key);
   if(v=="") return defv;
   return StringToDouble(v);
}

bool IsBuy(const string d){
   string u=d;
   StringToUpper(u);
   return (u=="BUY" || u=="LONG" || u=="B" || u=="L");
}

//============================= CONFIG ==============================
bool LoadConfig(){
   if(AccountInfoInteger(ACCOUNT_LOGIN)==843859){
      g_user_uuid="COMMANDER_DEV_001";
      if(InpVerboseLogging) Print("[Config] DEV UUID: ", g_user_uuid);
      return true;
   }
   int fh=FileOpen("bitten_deployment.cfg", FILE_READ|FILE_TXT);
   if(fh==INVALID_HANDLE){
      Print("[Config] CRITICAL: missing bitten_deployment.cfg");
      return false;
   }
   while(!FileIsEnding(fh)){
      string line=FileReadString(fh);
      if(StringFind(line, "UUID=")==0){
         g_user_uuid=StringSubstr(line, 5);
         StringTrimLeft(g_user_uuid);
         StringTrimRight(g_user_uuid);
      }
   }
   FileClose(fh);
   if(g_user_uuid=="" || StringLen(g_user_uuid)<10){
      Print("[Config] CRITICAL: invalid UUID");
      return false;
   }
   if(InpVerboseLogging) Print("[Config] UUID: ", g_user_uuid);
   return true;
}

void InitSymbols(){
   g_symbol_count=0;
   int total=SymbolsTotal(true);
   int cap = MathMin(total, InpMaxSymbols);
   ArrayResize(g_monitored_symbols, cap);
   for(int i=0; i<total && g_symbol_count<cap; i++){
      string s=SymbolName(i, true);
      if(s!=""){
         g_monitored_symbols[g_symbol_count]=s;
         g_symbol_count++;
         SymbolSelect(s, true);
      }
   }
   if(InpVerboseLogging)
      Print("[Symbols] Monitoring ", g_symbol_count, " symbols (cap ", InpMaxSymbols, ")");
}

//====================== TELEMETRY =====================
void SendHandshake(){
   double bal=AccountInfoDouble(ACCOUNT_BALANCE),
          eq=AccountInfoDouble(ACCOUNT_EQUITY);
   string positions_json = "[";
   int open_count = 0;
   for(int i=PositionsTotal()-1; i>=0; i--){
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetInteger(POSITION_MAGIC)!=(long)g_magic) continue;
      string symbol = PositionGetString(POSITION_SYMBOL);
      string fire_id = PositionGetString(POSITION_COMMENT);
      long typ = PositionGetInteger(POSITION_TYPE);
      double vol = PositionGetDouble(POSITION_VOLUME);
      double open_price = PositionGetDouble(POSITION_PRICE_OPEN);
      double pnl = PositionGetDouble(POSITION_PROFIT);
      int digs = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
      int vdigs = VolDigits(symbol);
      string direction = (typ==POSITION_TYPE_BUY)?"BUY":"SELL";
      if(open_count > 0) positions_json += ",";
      positions_json += StringFormat(
         "{\"ticket\":%d,\"symbol\":\"%s\",\"direction\":\"%s\","
         "\"fire_id\":\"%s\",\"open_price\":%s,\"volume\":%s,\"pnl\":%.2f}",
         (int)ticket, JsonEscape(symbol), direction, JsonEscape(fire_id),
         DoubleToString(open_price, digs), DoubleToString(vol, vdigs), pnl
      );
      open_count++;
   }
   positions_json += "]";
   bool is_reconnect = (open_count > 0);
   string j=StringFormat(
      "{\"type\":\"handshake\",\"node_id\":\"%s\",\"uuid\":\"%s\","
      "\"account\":%d,\"broker\":\"%s\",\"server\":\"%s\","
      "\"currency\":\"%s\",\"balance\":%.2f,\"equity\":%.2f,"
      "\"symbols\":%d,\"version\":\"3.005\",\"reconnect\":%s,"
      "\"open_positions\":%s,\"timestamp\":%d}",
      JsonEscape(g_node_id), JsonEscape(g_user_uuid),
      (int)AccountInfoInteger(ACCOUNT_LOGIN),
      JsonEscape(AccountInfoString(ACCOUNT_COMPANY)),
      JsonEscape(AccountInfoString(ACCOUNT_SERVER)),
      JsonEscape(AccountInfoString(ACCOUNT_CURRENCY)),
      bal, eq, g_symbol_count, is_reconnect?"true":"false",
      positions_json, (int)TimeCurrent()
   );
   ZMQSend(g_tick_pub, j);
   if(InpVerboseLogging){
      PrintFormat("[Handshake] Sent: reconnect=%s positions=%d",
                  is_reconnect?"true":"false", open_count);
   }
}

void SendHeartbeat(){
   if(g_tick_pub==0){
      Print("[ERROR] g_tick_pub socket is NULL - cannot send heartbeat");
      return;
   }
   double bal=SafeNum(AccountInfoDouble(ACCOUNT_BALANCE), 2),
          eq=SafeNum(AccountInfoDouble(ACCOUNT_EQUITY), 2),
          margin=SafeNum(AccountInfoDouble(ACCOUNT_MARGIN), 2),
          free_mg=SafeNum(AccountInfoDouble(ACCOUNT_MARGIN_FREE), 2);
   int positions=0;
   for(int i=PositionsTotal()-1; i>=0; i--){
      if(PositionSelectByTicket(PositionGetTicket(i))){
         if(PositionGetInteger(POSITION_MAGIC)==(long)g_magic) positions++;
      }
   }
   string j=StringFormat(
      "{\"type\":\"heartbeat\",\"node_id\":\"%s\",\"uuid\":\"%s\","
      "\"balance\":%.2f,\"equity\":%.2f,\"margin\":%.2f,\"free_margin\":%.2f,"
      "\"positions\":%d,\"ticks\":%d,\"timestamp\":%d}",
      JsonEscape(g_node_id), JsonEscape(g_user_uuid),
      bal, eq, margin, free_mg, positions, g_tick_count, (int)TimeCurrent()
   );
   uchar d[];
   StringToCharArray(j, d, 0, WHOLE_ARRAY, CP_UTF8);
   int L=(ArraySize(d)>0)?ArraySize(d)-1:0;
   if(L>0){
      int result = zmq_send(g_tick_pub, d, L, ZMQ_DONTWAIT);
      if(result<0){
         PrintFormat("[ERROR] Heartbeat send failed: result=%d socket=%d port=%d",
                     result, (int)g_tick_pub, InpTickPort);
      } else if(InpVerboseLogging){
         PrintFormat("[Heartbeat] Sent %d bytes to port %d: bal=%.2f eq=%.2f pos=%d ticks=%d",
                     result, InpTickPort, bal, eq, positions, g_tick_count);
      }
   }
}

void SendDisconnect(){
   string j=StringFormat(
      "{\"type\":\"disconnect\",\"node_id\":\"%s\",\"uuid\":\"%s\",\"timestamp\":%d}",
      JsonEscape(g_node_id), JsonEscape(g_user_uuid), (int)TimeCurrent()
   );
   ZMQSend(g_tick_pub, j);
}

void SendDealerHeartbeat(){
   string j=StringFormat(
      "{\"type\":\"dealer_heartbeat\",\"uuid\":\"%s\",\"node_id\":\"%s\",\"timestamp\":%d}",
      JsonEscape(g_user_uuid), JsonEscape(g_node_id), (int)TimeCurrent()
   );
   ZMQSend(g_cmd_dealer, j);
   if(InpVerboseLogging) Print("[DEALER] Keepalive sent");
}

//==================== TICK STREAMING ====================
void StreamTick(string symbol){
   if(!InpStreamTicks) return;
   MqlTick t;
   if(!SymbolInfoTick(symbol, t)) return;
   int digs=(int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
   string j=StringFormat(
      "{\"type\":\"tick\",\"uuid\":\"%s\",\"symbol\":\"%s\","
      "\"bid\":%s,\"ask\":%s,\"volume\":%d,\"timestamp\":%d}",
      JsonEscape(g_user_uuid), JsonEscape(symbol),
      DoubleToString(t.bid, digs), DoubleToString(t.ask, digs),
      (int)t.volume, (int)t.time
   );
   ZMQSend(g_tick_pub, j);
   g_tick_count++;
}

void StreamAllTicks(){
   if(!InpStreamTicks) return;
   for(int i=0; i<g_symbol_count; i++){
      StreamTick(g_monitored_symbols[i]);
      if(InpTickScanSleepMs>0) Sleep(InpTickScanSleepMs);
   }
}

//================ POSITION UPDATES ================
void RemoveFromPosCache(ulong ticket){
   for(int i=0; i<g_pos_cache_size; i++){
      if(g_last_tickets[i]==ticket){
         for(int j=i+1; j<g_pos_cache_size; j++){
            g_last_tickets[j-1]=g_last_tickets[j];
            g_last_prices[j-1]=g_last_prices[j];
            g_last_pnls[j-1]=g_last_pnls[j];
         }
         g_pos_cache_size--;
         ArrayResize(g_last_tickets, g_pos_cache_size);
         ArrayResize(g_last_prices, g_pos_cache_size);
         ArrayResize(g_last_pnls, g_pos_cache_size);
         return;
      }
   }
}

bool PosSeen(ulong ticket, double px, double pnl){
   if(!InpDedupPositions) return false;
   int digs = 5;
   if(PositionSelectByTicket(ticket)){
      string sym = PositionGetString(POSITION_SYMBOL);
      digs = (int)SymbolInfoInteger(sym, SYMBOL_DIGITS);
   }
   double rpx  = NormalizeDouble(px, digs);
   double rpnl = NormalizeDouble(pnl, 2);
   for(int i=0; i<g_pos_cache_size; i++){
      if(g_last_tickets[i]==ticket){
         bool same = (g_last_prices[i]==rpx && g_last_pnls[i]==rpnl);
         g_last_prices[i]=rpx;
         g_last_pnls[i]=rpnl;
         return same;
      }
   }
   ArrayResize(g_last_tickets, g_pos_cache_size+1);
   ArrayResize(g_last_prices, g_pos_cache_size+1);
   ArrayResize(g_last_pnls, g_pos_cache_size+1);
   g_last_tickets[g_pos_cache_size]=ticket;
   g_last_prices[g_pos_cache_size]=rpx;
   g_last_pnls[g_pos_cache_size]=rpnl;
   g_pos_cache_size++;
   return false;
}

void StreamPositionUpdates(){
   if(!InpStreamPositions) return;
   for(int i=PositionsTotal()-1; i>=0; i--){
      ulong ticket=PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetInteger(POSITION_MAGIC)!=(long)g_magic) continue;
      string symbol=PositionGetString(POSITION_SYMBOL);
      string fire_id=PositionGetString(POSITION_COMMENT);
      long typ=PositionGetInteger(POSITION_TYPE);
      double vol=PositionGetDouble(POSITION_VOLUME);
      double open_price=PositionGetDouble(POSITION_PRICE_OPEN);
      double pnl=PositionGetDouble(POSITION_PROFIT);
      int digs=(int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
      int vdigs=VolDigits(symbol);
      double current=(typ==POSITION_TYPE_BUY)
                     ?SymbolInfoDouble(symbol, SYMBOL_BID)
                     :SymbolInfoDouble(symbol, SYMBOL_ASK);
      if(PosSeen(ticket, current, pnl)) continue;
      string j=StringFormat(
         "{\"type\":\"position_update\",\"uuid\":\"%s\","
         "\"ticket\":%d,\"fire_id\":\"%s\",\"symbol\":\"%s\","
         "\"open_price\":%s,\"current_price\":%s,"
         "\"volume\":%s,\"pnl\":%.2f,\"timestamp\":%d}",
         JsonEscape(g_user_uuid), (int)ticket, JsonEscape(fire_id), JsonEscape(symbol),
         DoubleToString(open_price, digs), DoubleToString(current, digs),
         DoubleToString(vol, vdigs), pnl, (int)TimeCurrent()
      );
      ZMQSend(g_metrics_pub, j);
   }
}

//================ CONFIRMATIONS ================
void SendConfirmation(string cmd_type, bool success, ulong ticket, double price, string msg, string fire_id, string symbol=""){
   double bal=AccountInfoDouble(ACCOUNT_BALANCE),
          eq=AccountInfoDouble(ACCOUNT_EQUITY);
   int digs = (symbol != "") ? (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS) : 5;
   string j=StringFormat(
      "{\"type\":\"confirmation\",\"cmd_type\":\"%s\",\"fire_id\":\"%s\","
      "\"uuid\":\"%s\",\"node_id\":\"%s\",\"status\":\"%s\","
      "\"ticket\":%d,\"price\":%s,\"message\":\"%s\","
      "\"balance\":%.2f,\"equity\":%.2f,\"timestamp\":%d}",
      JsonEscape(cmd_type), JsonEscape(fire_id), JsonEscape(g_user_uuid), JsonEscape(g_node_id),
      success?"success":"failed",
      (int)ticket, DoubleToString(price, digs), JsonEscape(msg),
      bal, eq, (int)TimeCurrent()
   );
   ZMQSend(g_confirm_pub, j);
}

void SendPositionOpened(ulong ticket, string fire_id, string symbol, string direction, double entry, double vol){
   double bal=SafeNum(AccountInfoDouble(ACCOUNT_BALANCE), 2),
          eq=SafeNum(AccountInfoDouble(ACCOUNT_EQUITY), 2);
   int positions=0;
   for(int i=PositionsTotal()-1; i>=0; i--){
      if(PositionSelectByTicket(PositionGetTicket(i))){
         if(PositionGetInteger(POSITION_MAGIC)==(long)g_magic) positions++;
      }
   }
   int digs=(int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
   int vdigs=VolDigits(symbol);
   string j=StringFormat(
      "{\"type\":\"position_opened\",\"uuid\":\"%s\",\"fire_id\":\"%s\","
      "\"ticket\":%d,\"symbol\":\"%s\",\"direction\":\"%s\","
      "\"entry_price\":%s,\"volume\":%s,"
      "\"balance\":%.2f,\"equity\":%.2f,\"open_positions\":%d,\"timestamp\":%d}",
      JsonEscape(g_user_uuid), JsonEscape(fire_id), (int)ticket, JsonEscape(symbol),
      JsonEscape(CanonDir(direction)),
      DoubleToString(entry, digs), DoubleToString(vol, vdigs),
      bal, eq, positions, (int)TimeCurrent()
   );
   ZMQSend(g_confirm_pub, j);
}

void SendPositionClosed(ulong ticket, string fire_id, string symbol, double close_price, double pnl, string reason){
   double bal=AccountInfoDouble(ACCOUNT_BALANCE),
          eq=AccountInfoDouble(ACCOUNT_EQUITY);
   int digs=(int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
   string j=StringFormat(
      "{\"type\":\"position_closed\",\"uuid\":\"%s\",\"fire_id\":\"%s\","
      "\"ticket\":%d,\"symbol\":\"%s\",\"close_price\":%s,"
      "\"profit\":%.2f,\"reason\":\"%s\","
      "\"balance\":%.2f,\"equity\":%.2f,\"timestamp\":%d}",
      JsonEscape(g_user_uuid), JsonEscape(fire_id), (int)ticket, JsonEscape(symbol),
      DoubleToString(close_price, digs), pnl, JsonEscape(reason),
      bal, eq, (int)TimeCurrent()
   );
   ZMQSend(g_confirm_pub, j);
   RemoveFromPosCache(ticket);
}

//================ COMMAND EXECUTION ================
void ExecuteFire(string json){
   string fire_id=ExtractJsonValue(json, "fire_id");
   string symbol=Trim(ExtractJsonValue(json, "symbol"));
   string direction=Trim(ExtractJsonValue(json, "direction"));
   if(symbol==""){
      SendConfirmation("fire", false, 0, 0, "Missing 'symbol'", fire_id, "");
      return;
   }
   if(direction==""){
      SendConfirmation("fire", false, 0, 0, "Missing 'direction'", fire_id, symbol);
      return;
   }
   double sl=ExtractDouble(json, "sl", 0);
   double tp=ExtractDouble(json, "tp", 0);
   double lot=ExtractDouble(json, "lot", 0.01);
   if(!SymbolSelect(symbol, true)){
      SendConfirmation("fire", false, 0, 0, "Symbol not available", fire_id, symbol);
      return;
   }
   double bid=SymbolInfoDouble(symbol, SYMBOL_BID);
   double ask=SymbolInfoDouble(symbol, SYMBOL_ASK);
   if(bid==0 || ask==0){
      SendConfirmation("fire", false, 0, 0, "No quotes", fire_id, symbol);
      return;
   }
   bool is_buy = IsBuy(direction);
   double price = is_buy ? ask : bid;
   lot = NormalizeLots(symbol, lot);
   g_trade.SetExpertMagicNumber(g_magic);
   g_trade.SetDeviationInPoints(InpDeviationPoints);
   bool result=false;
   if(is_buy)
      result=g_trade.Buy(lot, symbol, 0, sl, tp, fire_id);
   else
      result=g_trade.Sell(lot, symbol, 0, sl, tp, fire_id);
   if(result){
      ulong ticket=g_trade.ResultOrder();
      double exec_price=g_trade.ResultPrice();
      if(exec_price==0) exec_price=price;
      SendConfirmation("fire", true, ticket, exec_price, "Executed", fire_id, symbol);
      SendPositionOpened(ticket, fire_id, symbol, direction, exec_price, lot);
   }else{
      string msg=StringFormat("Failed: retcode=%d", g_trade.ResultRetcode());
      SendConfirmation("fire", false, 0, 0, msg, fire_id, symbol);
   }
}

bool CloseByTicket(ulong ticket){
   if(!PositionSelectByTicket(ticket)) return false;
   string sym = PositionGetString(POSITION_SYMBOL);
   g_trade.SetExpertMagicNumber(g_magic);
   if(g_trade.PositionClose(ticket)) return true;
   return g_trade.PositionClose(sym);
}

void ExecuteClose(string json){
   string ticket_str=ExtractJsonValue(json, "ticket");
   ulong ticket=(ulong)StringToInteger(ticket_str);
   if(ticket==0){
      SendConfirmation("close", false, 0, 0, "Invalid ticket", "", "");
      return;
   }
   if(!PositionSelectByTicket(ticket)){
      SendConfirmation("close", false, ticket, 0, "Position not found", "", "");
      return;
   }
   if(PositionGetInteger(POSITION_MAGIC)!=(long)g_magic){
      SendConfirmation("close", false, ticket, 0, "Not our position", "", "");
      return;
   }
   string symbol=PositionGetString(POSITION_SYMBOL);
   string fire_id=PositionGetString(POSITION_COMMENT);
   if(CloseByTicket(ticket)){
      SendConfirmation("close", true, ticket, 0, "Closed", fire_id, symbol);
   }else{
      string msg=StringFormat("Failed: retcode=%d", g_trade.ResultRetcode());
      SendConfirmation("close", false, ticket, 0, msg, fire_id, symbol);
   }
}

void ExecuteCloseAll(){
   int closed=0, failed=0;
   for(int i=PositionsTotal()-1; i>=0; i--){
      ulong ticket=PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetInteger(POSITION_MAGIC)!=(long)g_magic) continue;
      if(CloseByTicket(ticket))
         closed++;
      else
         failed++;
   }
   string msg=StringFormat("Closed %d, failed %d", closed, failed);
   SendConfirmation("close_all", (failed==0), 0, 0, msg, "", "");
}

void CheckCommands(){
   string command="";
   if(!ZMQRecvAll(g_cmd_dealer, command)) return;
   if(StringFind(command, "\"target_uuid\"") >= 0 &&
      StringFind(command, "\"target_uuid\":\""+g_user_uuid+"\"") < 0){
      return;
   }
   string type=ExtractJsonValue(command, "type");
   if(type==""){
      if(InpVerboseLogging) Print("[Cmd] Failed to parse: ", command);
      return;
   }
   if(InpVerboseLogging) Print("[Cmd] Type: ", type);
   if(type=="fire")
      ExecuteFire(command);
   else if(type=="close_ticket" || type=="close")
      ExecuteClose(command);
   else if(type=="close_all")
      ExecuteCloseAll();
   else if(type=="ping"){
      string ping_id=ExtractJsonValue(command, "ping_id");
      string j=StringFormat(
         "{\"type\":\"pong\",\"ping_id\":\"%s\",\"uuid\":\"%s\",\"timestamp\":%d}",
         JsonEscape(ping_id), JsonEscape(g_user_uuid), (int)TimeCurrent()
      );
      ZMQSend(g_confirm_pub, j);
   }
}

//================ TRADE EVENTS ================
void OnTrade(){
   static int last_deals=0;
   int cur=HistoryDealsTotal();
   if(cur>last_deals && HistorySelect(TimeCurrent()-600, TimeCurrent())){
      int total=HistoryDealsTotal();
      for(int i=total-1; i>=0 && i>=total-10; i--){
         ulong deal_ticket=HistoryDealGetTicket(i);
         if(deal_ticket==0) continue;
         ENUM_DEAL_ENTRY entry=(ENUM_DEAL_ENTRY)HistoryDealGetInteger(deal_ticket, DEAL_ENTRY);
         if(entry==DEAL_ENTRY_OUT || entry==DEAL_ENTRY_OUT_BY){
            ulong pos_ticket=(ulong)HistoryDealGetInteger(deal_ticket, DEAL_POSITION_ID);
            string symbol=HistoryDealGetString(deal_ticket, DEAL_SYMBOL);
            string fire_id=HistoryDealGetString(deal_ticket, DEAL_COMMENT);
            double close_price=HistoryDealGetDouble(deal_ticket, DEAL_PRICE);
            double profit=HistoryDealGetDouble(deal_ticket, DEAL_PROFIT);
            ENUM_DEAL_REASON reason=(ENUM_DEAL_REASON)HistoryDealGetInteger(deal_ticket, DEAL_REASON);
            string close_reason="MANUAL";
            if(reason==DEAL_REASON_TP) close_reason="TP";
            else if(reason==DEAL_REASON_SL) close_reason="SL";
            else if(reason==DEAL_REASON_SO) close_reason="STOPOUT";
            SendPositionClosed(pos_ticket, fire_id, symbol, close_price, profit, close_reason);
         }
      }
   }
   last_deals=cur;
}

//================ LIFECYCLE ================
int OnInit(){
   if(InpVerboseLogging) Print("[Init] EA_BITTEN v3.005 PRODUCTION");
   if(!LoadConfig()){
      Comment("CONFIG ERROR");
      return INIT_FAILED;
   }
   if(!TerminalInfoInteger(TERMINAL_DLLS_ALLOWED)){
      Print("[Init] DLL not allowed");
      Comment("DLL NOT ALLOWED");
      return INIT_FAILED;
   }
   if(!AccountInfoInteger(ACCOUNT_TRADE_ALLOWED)){
      Print("[Init] Trading not allowed");
      Comment("TRADING NOT ALLOWED");
      return INIT_FAILED;
   }
   g_node_id=StringFormat("NODE_%d_%d",
      (int)AccountInfoInteger(ACCOUNT_LOGIN),
      (int)GetTickCount()
   );
   InitSymbols();
   g_context=zmq_ctx_new();
   if(!g_context){
      Print("[Init] ZMQ context failed");
      return INIT_FAILED;
   }
   g_tick_pub=zmq_socket(g_context, ZMQ_PUSH);
   g_metrics_pub=zmq_socket(g_context, ZMQ_PUSH);
   g_cmd_dealer=zmq_socket(g_context, ZMQ_DEALER);
   g_confirm_pub=zmq_socket(g_context, ZMQ_PUSH);
   if(!g_tick_pub || !g_metrics_pub || !g_cmd_dealer || !g_confirm_pub){
      Print("[Init] Socket creation failed");
      return INIT_FAILED;
   }
   ZMQTune(g_tick_pub, InpSndHWM, InpRcvHWM, InpLingerMs);
   ZMQTune(g_metrics_pub, InpSndHWM, InpRcvHWM, InpLingerMs);
   ZMQTune(g_cmd_dealer, InpRcvHWM, InpRcvHWM, InpLingerMs);
   ZMQTune(g_confirm_pub, InpSndHWM, InpRcvHWM, InpLingerMs);
   if(InpVerboseLogging){
      PrintFormat("[Init] Socket handles: tick=%d metrics=%d cmd=%d confirm=%d",
                  (int)g_tick_pub, (int)g_metrics_pub, (int)g_cmd_dealer, (int)g_confirm_pub);
   }
   string ep_tick=StringFormat("tcp://%s:%d", InpBridgeHost, InpTickPort);
   string ep_cmd=StringFormat("tcp://%s:%d", InpBridgeHost, InpCmdPort);
   string ep_confirm=StringFormat("tcp://%s:%d", InpBridgeHost, InpConfirmPort);
   string ep_metrics=StringFormat("tcp://%s:%d", InpBridgeHost, InpMetricsPort);
   if(InpVerboseLogging){
      PrintFormat("[Init] Connecting to: tick=%s metrics=%s cmd=%s confirm=%s",
                  ep_tick, ep_metrics, ep_cmd, ep_confirm);
   }
   if(ZMQConnect(g_tick_pub, ep_tick)!=0){
      PrintFormat("[Init] Connect tick failed: %s", ep_tick);
      return INIT_FAILED;
   }
   if(InpVerboseLogging) PrintFormat("[Init] Connect tick success: %s", ep_tick);
   ZMQSetIdentity(g_cmd_dealer, g_user_uuid);
   if(ZMQConnect(g_cmd_dealer, ep_cmd)!=0){
      PrintFormat("[Init] Connect cmd failed: %s", ep_cmd);
      return INIT_FAILED;
   }
   if(InpVerboseLogging) PrintFormat("[Init] Connect cmd success: %s", ep_cmd);
   if(ZMQConnect(g_confirm_pub, ep_confirm)!=0){
      PrintFormat("[Init] Connect confirm failed: %s", ep_confirm);
      return INIT_FAILED;
   }
   if(InpVerboseLogging) PrintFormat("[Init] Connect confirm success: %s", ep_confirm);
   if(ZMQConnect(g_metrics_pub, ep_metrics)!=0){
      PrintFormat("[Init] Connect metrics failed: %s", ep_metrics);
      return INIT_FAILED;
   }
   if(InpVerboseLogging) PrintFormat("[Init] Connect metrics success: %s", ep_metrics);
   string hello=StringFormat(
      "{\"type\":\"hello\",\"uuid\":\"%s\",\"node_id\":\"%s\",\"timestamp\":%d}",
      JsonEscape(g_user_uuid), JsonEscape(g_node_id), (int)TimeCurrent()
   );
   ZMQSend(g_cmd_dealer, hello);
   if(InpVerboseLogging) Print("[Init] Sent DEALER hello");
   SendHandshake();
   EventSetTimer(1);
   Comment(StringFormat(
      "EA_BITTEN v3.005 PRODUCTION\nUUID: %s\nNode: %s\nSymbols: %d\nDedup: %s\nKeepalive: %ds",
      g_user_uuid, g_node_id, g_symbol_count, InpDedupPositions?"ON":"OFF", InpRouterBeatSec
   ));
   if(InpVerboseLogging) Print("[Init] SUCCESS");
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason){
   EventKillTimer();
   SendDisconnect();
   if(g_tick_pub)    zmq_close(g_tick_pub);
   if(g_metrics_pub) zmq_close(g_metrics_pub);
   if(g_cmd_dealer)  zmq_close(g_cmd_dealer);
   if(g_confirm_pub) zmq_close(g_confirm_pub);
   if(g_context)     zmq_ctx_term(g_context);
   Comment("");
}

void OnTick(){
   CheckCommands();
}

void OnTimer(){
   static int timer_count = 0;
   timer_count++;
   if(InpVerboseLogging && timer_count % 5 == 0){
      PrintFormat("[Timer] Fired %d times | last_hb=%d current=%d diff=%d",
                  timer_count, (int)g_last_heartbeat, (int)TimeCurrent(),
                  (int)(TimeCurrent()-g_last_heartbeat));
   }
   StreamAllTicks();
   StreamPositionUpdates();
   CheckCommands();
   if(TimeCurrent()-g_last_heartbeat>=1){
      SendHeartbeat();
      g_last_heartbeat=TimeCurrent();
   }
   if(InpRouterBeatSec>0 && TimeCurrent()-g_last_router_hb>=InpRouterBeatSec){
      SendDealerHeartbeat();
      g_last_router_hb=TimeCurrent();
   }
}
