#!/usr/bin/env python3
"""
Quick VENOM Analysis Helper
For instant analysis requests from the user or agents
"""

import sqlite3
import json
import os
from datetime import datetime

def get_venom_analysis():
    """Get comprehensive VENOM analysis for user requests"""
    
    db_path = "/root/HydraX-v2/signal_tracker.db"
    if not os.path.exists(db_path):
        return "❌ No signal tracking data available. Start realtime_signal_tracker.py first."
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Overall stats
    cursor.execute("SELECT COUNT(*) FROM signals")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM signals WHERE outcome = 'WIN'")
    wins = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM signals WHERE outcome = 'LOSS'")
    losses = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM signals WHERE outcome = 'PENDING'")
    pending = cursor.fetchone()[0]
    
    # Quality breakdown
    cursor.execute('''
        SELECT quality, outcome, COUNT(*) 
        FROM signals 
        WHERE outcome IN ('WIN', 'LOSS')
        GROUP BY quality, outcome
    ''')
    
    quality_breakdown = {}
    for quality, outcome, count in cursor.fetchall():
        if quality not in quality_breakdown:
            quality_breakdown[quality] = {'wins': 0, 'losses': 0}
        if outcome == 'WIN':
            quality_breakdown[quality]['wins'] = count
        else:
            quality_breakdown[quality]['losses'] = count
    
    # Symbol performance
    cursor.execute('''
        SELECT symbol, outcome, COUNT(*) 
        FROM signals 
        WHERE outcome IN ('WIN', 'LOSS')
        GROUP BY symbol, outcome
    ''')
    
    symbol_performance = {}
    for symbol, outcome, count in cursor.fetchall():
        if symbol not in symbol_performance:
            symbol_performance[symbol] = {'wins': 0, 'losses': 0}
        if outcome == 'WIN':
            symbol_performance[symbol]['wins'] = count
        else:
            symbol_performance[symbol]['losses'] = count
    
    # Recent signals with current prices
    current_prices = get_current_prices()
    cursor.execute('''
        SELECT signal_id, symbol, direction, confidence, quality,
               entry_price, stop_loss, take_profit, outcome, timestamp
        FROM signals 
        ORDER BY timestamp DESC 
        LIMIT 10
    ''')
    
    recent_analysis = []
    for row in cursor.fetchall():
        signal_id, symbol, direction, confidence, quality, entry, sl, tp, outcome, timestamp = row
        
        analysis = {
            'signal': f"{symbol} {direction} @{confidence}% ({quality})",
            'outcome': outcome,
            'entry': entry,
            'sl': sl,
            'tp': tp
        }
        
        if outcome == 'PENDING' and symbol in current_prices:
            current = current_prices[symbol]['bid'] if direction == 'SELL' else current_prices[symbol]['ask']
            analysis['current'] = current
            
            if direction == 'BUY':
                sl_dist = (current - sl) * 10000  # pips
                tp_dist = (tp - current) * 10000  # pips
            else:
                sl_dist = (sl - current) * 10000  # pips  
                tp_dist = (current - tp) * 10000  # pips
            
            analysis['sl_distance'] = f"{sl_dist:+.1f}p"
            analysis['tp_distance'] = f"{tp_dist:+.1f}p"
            
            if sl_dist <= 1:
                analysis['risk_level'] = "🚨 CRITICAL - Very close to SL"
            elif sl_dist <= 5:
                analysis['risk_level'] = "⚠️ HIGH RISK - Close to SL" 
            elif tp_dist <= 5:
                analysis['risk_level'] = "🎯 NEAR TARGET - Close to TP"
            else:
                analysis['risk_level'] = "⏳ PENDING - Monitoring"
        
        recent_analysis.append(analysis)
    
    conn.close()
    
    # Calculate statistics
    closed = wins + losses
    win_rate = (wins / closed * 100) if closed > 0 else 0
    expected_rate = 84.3
    performance_gap = win_rate - expected_rate
    
    # Build comprehensive analysis
    analysis = f"""
🐍⚡ VENOM PERFORMANCE ANALYSIS
===============================
🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 OVERALL PERFORMANCE:
• Total Signals: {total}
• Wins: {wins} | Losses: {losses} | Pending: {pending}
• Win Rate: {win_rate:.1f}% (Expected: {expected_rate}%)
• Performance Gap: {performance_gap:+.1f} percentage points
• Sample Size: {'HIGH' if closed >= 20 else 'MEDIUM' if closed >= 10 else 'LOW'} reliability

🏆 QUALITY BREAKDOWN:
"""
    
    for quality, stats in quality_breakdown.items():
        total_quality = stats['wins'] + stats['losses']
        if total_quality > 0:
            quality_rate = (stats['wins'] / total_quality) * 100
            emoji = "💎" if quality == "platinum" else "🥇"
            analysis += f"• {emoji} {quality.title()}: {quality_rate:.1f}% ({stats['wins']}/{total_quality})\n"
    
    analysis += "\n📈 SYMBOL PERFORMANCE:\n"
    for symbol, stats in symbol_performance.items():
        total_symbol = stats['wins'] + stats['losses']
        if total_symbol > 0:
            symbol_rate = (stats['wins'] / total_symbol) * 100
            analysis += f"• {symbol}: {symbol_rate:.1f}% ({stats['wins']}/{total_symbol})\n"
    
    analysis += "\n🔄 RECENT SIGNALS:\n"
    for signal in recent_analysis:
        if signal['outcome'] == 'WIN':
            status = "✅"
        elif signal['outcome'] == 'LOSS':
            status = "❌"
        else:
            status = "⏳"
        
        analysis += f"{status} {signal['signal']}\n"
        
        if 'current' in signal:
            analysis += f"   Current: {signal['current']:.5f} | SL: {signal['sl_distance']} | TP: {signal['tp_distance']}\n"
            analysis += f"   {signal['risk_level']}\n"
    
    # Add alerts
    analysis += "\n🚨 ALERTS:\n"
    if win_rate < 50 and closed >= 5:
        analysis += "• CRITICAL: Win rate critically low - immediate recalibration required\n"
    elif performance_gap < -20:
        analysis += f"• WARNING: Large performance gap ({performance_gap:+.1f}%) - review confidence scoring\n"
    
    if closed < 10:
        analysis += f"• INFO: Limited sample size ({closed} trades) - continue monitoring\n"
    
    pending_at_risk = len([s for s in recent_analysis if s.get('risk_level', '').startswith('🚨')])
    if pending_at_risk > 0:
        analysis += f"• WARNING: {pending_at_risk} pending signals very close to stop loss\n"
    
    analysis += "\n" + "="*50
    
    return analysis

def get_current_prices():
    """Get current market prices"""
    try:
        with open('/tmp/ea_raw_data.json', 'r') as f:
            content = f.read().strip()
            if not content.endswith('}'):
                if content.endswith(']'):
                    content += '}'
                elif content.endswith(','):
                    content = content.rstrip(',') + ']}'
            data = json.loads(content)
        
        price_map = {}
        for tick in data.get('ticks', []):
            price_map[tick['symbol']] = {
                'bid': tick['bid'],
                'ask': tick['ask']
            }
        return price_map
    except:
        return {}

if __name__ == "__main__":
    print(get_venom_analysis())