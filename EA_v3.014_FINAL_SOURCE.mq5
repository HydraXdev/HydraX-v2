//+------------------------------------------------------------------+
//| BITTEN_Streamlined_Pipe_v3.014_FINAL.mq5                        |
//| Production: FINAL - All Critical Bugs Fixed                      |
//| FIXES: Deal tracking, ticket serialization, BE safety, file I/O  |
//+------------------------------------------------------------------+
#property strict
#property version   "3.014"
#property copyright "BITTEN Systems"

#include <Trade/Trade.mqh>

//============================= INPUTS ==============================
input bool   InpVerboseLogging     = false;
input bool   InpTestModeNoTrades   = false;
input bool   InpEnableZmq          = true;
input int    InpDeviationPoints    = 5;
input bool   InpStreamTicks        = true;
input bool   InpStreamPositions    = true;
input bool   InpDedupPositions     = true;
input int    InpMaxSymbols         = 200;
input int    InpTickScanSleepMs    = 0;
input int    InpEmitHzPositions    = 2;
input int    InpLingerOnExitMs     = 250;
input string InpBridgeHost         = "134.199.204.67";
input int    InpTickPort           = 5556;
input int    InpCmdPort            = 5555;
input int    InpConfirmPort        = 5558;
input int    InpMetricsPort        = 5560;
input int    InpRouterBeatSec      = 5;
input int    InpSndHWM             = 10000;
input int    InpRcvHWM             = 1000;
input int    InpLingerMs           = 0;

// Smart Trailing Inputs
input bool   InpSmartTrailingEnabled = true;
input string InpTrailingStateFile    = "bitten_trailing_state.dat";

//============================== ZMQ ================================
#define ZMQ_DEALER    5  // ZMQ constant for DEALER socket type
#define ZMQ_PUSH      8
#define ZMQ_IDENTITY  5  // ZMQ constant for identity option (same value as DEALER)
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

//==================== SMART TRAILING ENUMS ========================
enum TRAIL_STATE {
    TRAIL_NONE = 0,
    TRAIL_ELIGIBLE = 1,
    TRAIL_ARMED = 2,
    TRAIL_ACTIVE = 3,
    TRAIL_PROTECTION_ACHIEVED = 4,
    TRAIL_EXITED = 5
};

enum TRAIL_STYLE {
    STYLE_NONE = 0,
    STYLE_ATR = 1,
    STYLE_CHANDELIER = 2,
    STYLE_FIXED_PIP = 3,
    STYLE_STEP = 4,
    STYLE_STRUCTURE = 5
};

enum ACTIVATION_MODE {
    ACT_RR_ONLY = 0,
    ACT_PIPS_ONLY = 1,
    ACT_EITHER = 2
};

//==================== SMART TRAILING STRUCTURES ====================
struct TrailingConfig {
    bool enabled;
    TRAIL_STYLE style;
    int atr_len;
    double atr_mult;
    double fixed_pips;
    double step_pips;
    ACTIVATION_MODE act_mode;
    double min_rr;
    double min_pips;
    int min_minutes;
    bool be_enable;
    double be_trigger_rr;
    bool tighten_only;
    string update_on;         // "bar_open", "step_change", "tick" (NOTE: "bar_close" actually triggers on bar OPEN)
    double update_step_pips;
    int max_updates_per_min;
    double min_stop_distance_pips;
    double spread_guard_pips;
    string protection_type;   // "locked_pips" or "locked_rr"
    double protection_value;
};

struct TrailingState {
    ulong ticket;
    string trade_id;
    string symbol;
    bool is_buy;
    double entry_price;
    double initial_sl;
    double initial_tp;
    double size;
    TRAIL_STATE state;
    TrailingConfig config;
    datetime opened_time;
    datetime armed_time;
    datetime active_time;
    double   last_applied_sl;
    double   last_price_checked;
    datetime last_update_time;
    int      updates_this_minute;
    datetime minute_start;
    bool   protection_emitted;
    double highest_locked_pips;
    double highest_locked_rr;
    int      event_seq;
    datetime last_bar_time;
    int      modify_failure_count;
    datetime last_modify_attempt;
};

//==================== ATR HANDLE CACHE ============================
struct AtrCacheKey {
    string symbol;
    ENUM_TIMEFRAMES period;
    int length;
};

struct AtrCacheVal { int handle; };

AtrCacheKey g_atr_keys[];
AtrCacheVal g_atr_vals[];
int g_atr_cache_count = 0;

int GetATRHandle(const string sym, const ENUM_TIMEFRAMES per, const int len){
    for(int i=0; i<g_atr_cache_count; i++){
        if(g_atr_keys[i].symbol==sym && g_atr_keys[i].period==per && g_atr_keys[i].length==len)
            return g_atr_vals[i].handle;
    }
    int h = iATR(sym, per, len);
    if(h != INVALID_HANDLE){
        ArrayResize(g_atr_keys, g_atr_cache_count+1);
        ArrayResize(g_atr_vals, g_atr_cache_count+1);
        g_atr_keys[g_atr_cache_count].symbol = sym;
        g_atr_keys[g_atr_cache_count].period = per;
        g_atr_keys[g_atr_cache_count].length = len;
        g_atr_vals[g_atr_cache_count].handle = h;
        g_atr_cache_count++;
    }
    return h;
}

void ReleaseATRHandles(){
    for(int i=0; i<g_atr_cache_count; i++){
        if(g_atr_vals[i].handle != INVALID_HANDLE) IndicatorRelease(g_atr_vals[i].handle);
    }
    g_atr_cache_count = 0;
}

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

TrailingState g_trailing_states[];
int g_trailing_count = 0;

// FIX #1: Track last processed deal to prevent missing closes
ulong g_last_deal_id = 0;

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
    string u=d; StringToUpper(u);
    return (u=="BUY" || u=="LONG" || u=="B" || u=="L")?"BUY":"SELL";
}

bool IsBuy(const string d){
    string u=d; StringToUpper(u);
    return (u=="BUY" || u=="LONG" || u=="B" || u=="L");
}

double GetPipValue(string symbol){
    double tick = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_SIZE);
    if(tick > 0) return tick;
    return SymbolInfoDouble(symbol, SYMBOL_POINT);
}

double PipsToPriceDistance(string symbol, double pips){ return pips * GetPipValue(symbol); }

double PriceToPips(string symbol, double price_distance){
    double pv = GetPipValue(symbol);
    if(pv == 0) return 0;
    return price_distance / pv;
}

// ... (rest of EA code continues - truncated for brevity, full code saved)
