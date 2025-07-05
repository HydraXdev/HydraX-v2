# alert_designs_wip.py
# Work in progress alert designs for BITTEN

# Current designs being tested:

def tactical_compact_v1(trade_data):
    """Version 1 - Ultra compact"""
    return f"""▓▓▓ {trade_data['callsign']} ▓▓▓
{trade_data['symbol']} • {trade_data['direction']} @ {trade_data['entry_price']}
TP: +{trade_data['take_profit_pips']}p • SL: -{trade_data['stop_loss_pips']}p
TCS: {trade_data['tcs_score']}% • SQUAD: {trade_data['active_traders']}
EXPIRES: {trade_data['time_remaining']}"""

def tactical_compact_v2(trade_data):
    """Version 2 - Even more minimal"""
    dir_icon = "🟢" if trade_data['direction'] == "BUY" else "🔴"
    return f"""{trade_data['callsign']}
{trade_data['symbol']} {dir_icon} {trade_data['entry_price']}
+{trade_data['take_profit_pips']}p/-{trade_data['stop_loss_pips']}p • {trade_data['tcs_score']}%
Squad: {trade_data['active_traders']} • {trade_data['time_remaining']}"""

def military_radio_v1(trade_data):
    """Radio style"""
    return f""">>> {trade_data['callsign']} <<<
TGT: {trade_data['symbol']} {trade_data['direction']}
POS: {trade_data['entry_price']}
OBJ: +{trade_data['take_profit_pips']}p
>>> END <<<"""

def sniper_minimal_v1(trade_data):
    """Sniper minimal"""
    return f"""🎯 CLASSIFIED
{trade_data['symbol']} {trade_data['direction']} {trade_data['entry_price']}
+{trade_data['take_profit_pips']}p • {trade_data['tcs_score']}%"""

# Ideas to try:
# 1. Use emojis as section dividers instead of text
# 2. Single line format for extreme minimal
# 3. Color coding with emoji indicators
# 4. Military brevity codes
# 5. Morse code style dots/dashes

# Test data template:
test_arcade = {
    'callsign': '🌅 DAWN RAID',
    'symbol': 'EURUSD',
    'direction': 'BUY',
    'entry_price': 1.08450,
    'take_profit_pips': 15,
    'stop_loss_pips': 10,
    'tcs_score': 82,
    'active_traders': 17,
    'time_remaining': '04:32'
}

test_sniper = {
    'symbol': 'USDJPY',
    'direction': 'SELL',
    'entry_price': 110.250,
    'take_profit_pips': 35,
    'stop_loss_pips': 15,
    'tcs_score': 94,
    'active_traders': 8,
    'time_remaining': '08:15'
}