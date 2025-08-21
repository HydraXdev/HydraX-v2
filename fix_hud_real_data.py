#!/usr/bin/env python3
"""
Fix HUD to display real-time data instead of placeholders
"""

import sqlite3
import json

def get_real_win_rate(user_id):
    """Calculate actual win rate from trade history"""
    try:
        conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
        cursor = conn.cursor()
        
        # Get completed trades for user
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN status = 'WIN' OR price > entry_price THEN 1 ELSE 0 END) as wins
            FROM fires 
            WHERE user_id = ? AND status IN ('FILLED', 'WIN', 'LOSS', 'CLOSED')
        """, (user_id,))
        
        result = cursor.fetchone()
        if result and result[0] > 0:
            total, wins = result
            win_rate = (wins / total) * 100
        else:
            win_rate = 0
            
        conn.close()
        return round(win_rate, 1)
    except:
        return 0

def get_pattern_type_for_signal(signal_id):
    """Get the actual pattern type from signals table"""
    try:
        conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT pattern_type, confidence, symbol, direction
            FROM signals 
            WHERE signal_id = ?
        """, (signal_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            pattern_type = result[0] or 'UNKNOWN'
            # Format pattern type for display
            pattern_display = pattern_type.replace('_', ' ').title()
            return pattern_display, result[1], result[2], result[3]
        else:
            return 'Pattern Unknown', 0, '', ''
    except:
        return 'Pattern Unknown', 0, '', ''

def get_user_stats(user_id):
    """Get comprehensive user statistics"""
    try:
        conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
        cursor = conn.cursor()
        
        # Get EA data
        cursor.execute("""
            SELECT last_balance, last_equity, broker, leverage
            FROM ea_instances 
            WHERE user_id = ? 
            ORDER BY last_seen DESC 
            LIMIT 1
        """, (user_id,))
        
        ea_data = cursor.fetchone()
        
        # Get trade statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN status = 'WIN' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN status = 'LOSS' THEN 1 ELSE 0 END) as losses,
                AVG(equity_used) as avg_position_size
            FROM fires 
            WHERE user_id = ? AND status IN ('WIN', 'LOSS', 'CLOSED')
        """, (user_id,))
        
        trade_stats = cursor.fetchone()
        
        conn.close()
        
        stats = {
            'balance': ea_data[0] if ea_data else 0,
            'equity': ea_data[1] if ea_data else 0,
            'broker': ea_data[2] if ea_data else 'Not Connected',
            'leverage': ea_data[3] if ea_data else 500,
            'total_trades': trade_stats[0] if trade_stats else 0,
            'wins': trade_stats[1] if trade_stats else 0,
            'losses': trade_stats[2] if trade_stats else 0,
            'win_rate': 0,
            'avg_position_size': trade_stats[3] if trade_stats else 0
        }
        
        if stats['total_trades'] > 0:
            stats['win_rate'] = round((stats['wins'] / stats['total_trades']) * 100, 1)
        
        return stats
    except Exception as e:
        print(f"Error getting user stats: {e}")
        return {
            'balance': 0,
            'equity': 0,
            'broker': 'Error',
            'leverage': 500,
            'total_trades': 0,
            'wins': 0,
            'losses': 0,
            'win_rate': 0,
            'avg_position_size': 0
        }

def update_mission_files_with_pattern_types():
    """Update existing mission files with pattern types from database"""
    import os
    import glob
    
    mission_files = glob.glob('/root/HydraX-v2/missions/*.json')
    updated = 0
    
    for mission_file in mission_files:
        try:
            # Extract signal_id from filename
            filename = os.path.basename(mission_file)
            signal_id = filename.replace('.json', '')
            
            # Get pattern type from database
            pattern_type, confidence, symbol, direction = get_pattern_type_for_signal(signal_id)
            
            # Load mission file
            with open(mission_file, 'r') as f:
                mission_data = json.load(f)
            
            # Update with real pattern type
            mission_data['pattern_type'] = pattern_type
            mission_data['pattern_raw'] = pattern_type.upper().replace(' ', '_')
            
            # Save updated mission file
            with open(mission_file, 'w') as f:
                json.dump(mission_data, f, indent=2)
            
            updated += 1
            
        except Exception as e:
            print(f"Error updating {mission_file}: {e}")
    
    print(f"Updated {updated} mission files with pattern types")
    return updated

if __name__ == "__main__":
    # Test functions
    print("Testing real data functions...")
    
    # Test win rate
    user_id = "7176191872"
    win_rate = get_real_win_rate(user_id)
    print(f"User {user_id} win rate: {win_rate}%")
    
    # Test pattern type
    signal_id = "ELITE_GUARD_GBPJPY_1755611045"
    pattern, conf, sym, dir = get_pattern_type_for_signal(signal_id)
    print(f"Signal {signal_id}: {pattern} @ {conf}% confidence")
    
    # Test user stats
    stats = get_user_stats(user_id)
    print(f"User stats: {stats}")
    
    # Update mission files
    print("\nUpdating mission files with pattern types...")
    update_mission_files_with_pattern_types()