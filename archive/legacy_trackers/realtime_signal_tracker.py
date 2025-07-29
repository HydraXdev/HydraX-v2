#!/usr/bin/env python3
"""
Real-Time VENOM Signal Tracker
Monitors all signals continuously and provides live win/loss tracking
"""

import json
import os
import time
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading

class RealTimeSignalTracker:
    def __init__(self, db_path="/root/HydraX-v2/signal_tracker.db"):
        self.db_path = db_path
        self.missions_dir = "/root/HydraX-v2/missions/"
        self.price_file = "/tmp/ea_raw_data.json"
        self.running = False
        self.monitor_thread = None
        
        # Initialize database
        self.init_database()
        
        # Load existing signals on startup
        self.load_existing_signals()
    
    def init_database(self):
        """Initialize SQLite database for signal tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                signal_id TEXT PRIMARY KEY,
                symbol TEXT,
                direction TEXT,
                confidence REAL,
                quality TEXT,
                entry_price REAL,
                stop_loss REAL,
                take_profit REAL,
                signal_type TEXT,
                session TEXT,
                timestamp REAL,
                status TEXT DEFAULT 'PENDING',
                outcome TEXT DEFAULT 'PENDING',
                close_price REAL,
                close_time REAL,
                pips_result REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_updates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id TEXT,
                symbol TEXT,
                price REAL,
                timestamp REAL,
                distance_to_sl REAL,
                distance_to_tp REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (signal_id) REFERENCES signals (signal_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def load_existing_signals(self):
        """Load any existing VENOM signals that aren't in database yet"""
        print("🔍 Loading existing signals...")
        
        for filename in os.listdir(self.missions_dir):
            if filename.startswith("mission_VENOM_OPTIMIZED_") and filename.endswith(".json"):
                file_path = os.path.join(self.missions_dir, filename)
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    signal_id = data.get('signal_id')
                    if signal_id and not self.signal_exists(signal_id):
                        self.add_signal_to_db(data)
                        print(f"  📋 Added: {signal_id}")
                
                except Exception as e:
                    print(f"  ❌ Error loading {filename}: {e}")
    
    def signal_exists(self, signal_id: str) -> bool:
        """Check if signal already exists in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT signal_id FROM signals WHERE signal_id = ?", (signal_id,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
    
    def add_signal_to_db(self, mission_data: Dict):
        """Add new signal to database"""
        enhanced = mission_data.get('enhanced_signal', {})
        if not enhanced:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO signals 
            (signal_id, symbol, direction, confidence, quality, entry_price, 
             stop_loss, take_profit, signal_type, session, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            mission_data.get('signal_id'),
            enhanced.get('symbol'),
            enhanced.get('direction'),
            enhanced.get('confidence'),
            mission_data.get('quality'),
            enhanced.get('entry_price'),
            enhanced.get('stop_loss'),
            enhanced.get('take_profit'),
            enhanced.get('signal_type'),
            mission_data.get('session'),
            mission_data.get('timestamp')
        ))
        
        conn.commit()
        conn.close()
    
    def get_current_prices(self) -> Dict:
        """Get current market prices with fallback handling"""
        try:
            with open(self.price_file, 'r') as f:
                content = f.read().strip()
                if not content.endswith('}'):
                    if content.endswith(']'):
                        content += '}'
                    elif content.endswith(','):
                        content = content.rstrip(',') + ']}'
                return json.loads(content)
        except:
            return {"ticks": []}
    
    def update_signal_status(self, signal_id: str, current_prices: Dict):
        """Update signal status based on current market prices"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get signal data
        cursor.execute('''
            SELECT symbol, direction, entry_price, stop_loss, take_profit, outcome
            FROM signals WHERE signal_id = ?
        ''', (signal_id,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return
        
        symbol, direction, entry_price, stop_loss, take_profit, current_outcome = result
        
        # Skip if already closed
        if current_outcome in ['WIN', 'LOSS']:
            conn.close()
            return
        
        # Find current price for symbol
        current_price = None
        for tick in current_prices.get('ticks', []):
            if tick['symbol'] == symbol:
                current_price = tick['bid'] if direction == 'SELL' else tick['ask']
                break
        
        if current_price is None:
            conn.close()
            return
        
        # Calculate distances
        if direction == 'BUY':
            distance_to_sl = current_price - stop_loss
            distance_to_tp = take_profit - current_price
        else:  # SELL
            distance_to_sl = stop_loss - current_price
            distance_to_tp = current_price - take_profit
        
        # Determine outcome
        new_outcome = 'PENDING'
        close_price = None
        pips_result = None
        
        if direction == 'BUY':
            if current_price >= take_profit:
                new_outcome = 'WIN'
                close_price = take_profit
                pips_result = (take_profit - entry_price) * 10000
            elif current_price <= stop_loss:
                new_outcome = 'LOSS'
                close_price = stop_loss
                pips_result = (stop_loss - entry_price) * 10000
        else:  # SELL
            if current_price <= take_profit:
                new_outcome = 'WIN'
                close_price = take_profit
                pips_result = (entry_price - take_profit) * 10000
            elif current_price >= stop_loss:
                new_outcome = 'LOSS'
                close_price = stop_loss
                pips_result = (entry_price - stop_loss) * 10000
        
        # Update database
        if new_outcome != current_outcome:
            cursor.execute('''
                UPDATE signals 
                SET outcome = ?, close_price = ?, close_time = ?, pips_result = ?,
                    last_updated = CURRENT_TIMESTAMP
                WHERE signal_id = ?
            ''', (new_outcome, close_price, time.time() if close_price else None, 
                  pips_result, signal_id))
        
        # Log price update
        cursor.execute('''
            INSERT INTO price_updates 
            (signal_id, symbol, price, timestamp, distance_to_sl, distance_to_tp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (signal_id, symbol, current_price, time.time(), distance_to_sl, distance_to_tp))
        
        conn.commit()
        conn.close()
    
    def get_live_stats(self) -> Dict:
        """Get real-time statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Overall stats
        cursor.execute("SELECT COUNT(*) FROM signals")
        total_signals = cursor.fetchone()[0]
        
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
            GROUP BY quality, outcome
        ''')
        quality_stats = {}
        for quality, outcome, count in cursor.fetchall():
            if quality not in quality_stats:
                quality_stats[quality] = {'WIN': 0, 'LOSS': 0, 'PENDING': 0}
            quality_stats[quality][outcome] = count
        
        # Recent signals
        cursor.execute('''
            SELECT signal_id, symbol, direction, confidence, outcome, 
                   entry_price, stop_loss, take_profit
            FROM signals 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''')
        recent_signals = cursor.fetchall()
        
        conn.close()
        
        # Calculate win rate
        closed_trades = wins + losses
        win_rate = (wins / closed_trades * 100) if closed_trades > 0 else 0
        
        return {
            'total_signals': total_signals,
            'wins': wins,
            'losses': losses,
            'pending': pending,
            'win_rate': win_rate,
            'quality_stats': quality_stats,
            'recent_signals': recent_signals
        }
    
    def display_dashboard(self):
        """Display real-time dashboard"""
        os.system('clear')  # Clear screen
        
        stats = self.get_live_stats()
        current_time = datetime.now().strftime("%H:%M:%S")
        
        print("🐍⚡ VENOM REAL-TIME SIGNAL TRACKER")
        print("=" * 60)
        print(f"🕐 Last Update: {current_time}")
        print()
        
        # Main stats
        print("📊 LIVE PERFORMANCE")
        print("-" * 30)
        print(f"📈 Total Signals: {stats['total_signals']}")
        print(f"✅ Wins: {stats['wins']}")
        print(f"❌ Losses: {stats['losses']}")
        print(f"⏳ Pending: {stats['pending']}")
        print(f"🎯 Win Rate: {stats['win_rate']:.1f}%")
        print()
        
        # Quality breakdown
        if stats['quality_stats']:
            print("🏆 QUALITY BREAKDOWN")
            print("-" * 25)
            for quality, outcomes in stats['quality_stats'].items():
                total = outcomes['WIN'] + outcomes['LOSS']
                if total > 0:
                    q_win_rate = (outcomes['WIN'] / total) * 100
                    emoji = "💎" if quality == "platinum" else "🥇"
                    print(f"{emoji} {quality.title()}: {q_win_rate:.1f}% ({outcomes['WIN']}/{total})")
            print()
        
        # Recent signals
        if stats['recent_signals']:
            print("🔄 RECENT SIGNALS")
            print("-" * 20)
            for signal_data in stats['recent_signals'][:5]:
                signal_id, symbol, direction, confidence, outcome, entry, sl, tp = signal_data
                
                if outcome == 'WIN':
                    status = "✅"
                elif outcome == 'LOSS':
                    status = "❌"
                else:
                    status = "⏳"
                
                short_id = signal_id.split('_')[-1] if '_' in signal_id else signal_id[-4:]
                print(f"{status} {symbol} {direction} @{confidence}% ({short_id})")
        
        print("\n" + "=" * 60)
        print("Press Ctrl+C to stop monitoring")
    
    def monitor_signals(self):
        """Main monitoring loop"""
        self.running = True
        print("🚀 Starting real-time signal monitoring...")
        
        while self.running:
            try:
                # Check for new mission files
                for filename in os.listdir(self.missions_dir):
                    if filename.startswith("mission_VENOM_OPTIMIZED_") and filename.endswith(".json"):
                        file_path = os.path.join(self.missions_dir, filename)
                        
                        # Check if file is new (modified in last 30 seconds)
                        if os.path.getmtime(file_path) > time.time() - 30:
                            try:
                                with open(file_path, 'r') as f:
                                    data = json.load(f)
                                
                                signal_id = data.get('signal_id')
                                if signal_id and not self.signal_exists(signal_id):
                                    self.add_signal_to_db(data)
                                    print(f"\n🆕 NEW SIGNAL: {signal_id}")
                            except:
                                continue
                
                # Update all pending signals
                current_prices = self.get_current_prices()
                if current_prices.get('ticks'):
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT signal_id FROM signals WHERE outcome = 'PENDING'")
                    pending_signals = [row[0] for row in cursor.fetchall()]
                    conn.close()
                    
                    for signal_id in pending_signals:
                        self.update_signal_status(signal_id, current_prices)
                
                # Update dashboard
                self.display_dashboard()
                
                # Wait before next update
                time.sleep(5)
                
            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                print(f"❌ Monitor error: {e}")
                time.sleep(10)
    
    def start(self):
        """Start the monitoring system"""
        self.monitor_signals()

def main():
    tracker = RealTimeSignalTracker()
    try:
        tracker.start()
    except KeyboardInterrupt:
        print("\n🛑 Signal tracking stopped.")

if __name__ == "__main__":
    main()