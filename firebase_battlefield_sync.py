"""
Firebase Battlefield Sync Enhancement
Ensures all battlefield data is properly synced with real-time calculations
"""

import time
import sqlite3
from datetime import datetime, timedelta
from firebase_backend import (
    get_firestore_client,
    update_active_trade_price,
    update_user_data
)

DB_PATH = '/root/HydraX-v2/bitten.db'

def calculate_pip_value(symbol: str, lot_size: float) -> float:
    """Calculate pip value for a symbol and lot size"""
    # Standard lot = 100,000 units
    # 1 pip = 0.0001 for most pairs, 0.01 for JPY pairs

    if 'JPY' in symbol:
        pip = 0.01
    else:
        pip = 0.0001

    # Pip value = (pip size * lot size * 100,000)
    pip_value = pip * lot_size * 100000

    # For USD pairs, convert to USD (simplified - would need live rates)
    return pip_value


def calculate_trade_profit(entry: float, current: float, direction: str,
                          symbol: str, lot_size: float) -> tuple:
    """
    Calculate current P/L for a trade

    Returns:
        tuple: (profit_in_currency, pips)
    """
    # Calculate pip movement
    if 'JPY' in symbol:
        pip_movement = (current - entry) * 100
    else:
        pip_movement = (current - entry) * 10000

    # Apply direction
    if direction == 'SELL':
        pip_movement = -pip_movement

    # Calculate profit
    pip_value = calculate_pip_value(symbol, lot_size)
    profit = pip_movement * pip_value / (100 if 'JPY' in symbol else 10000)

    return (profit, pip_movement)


def sync_active_trades_to_firebase():
    """
    Sync all active trades from SQLite to Firebase with proper calculations
    """
    try:
        db = get_firestore_client()
        if not db:
            print("❌ Firebase not initialized")
            return

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # Get all active positions
        cur.execute("""
            SELECT
                lp.fire_id,
                lp.user_id,
                lp.symbol,
                lp.direction,
                lp.entry_price,
                lp.lot_size,
                lp.sl,
                lp.tp,
                lp.last_update,
                lp.current_price,
                lp.current_pnl,
                lp.current_pips,
                f.ticket,
                f.created_at
            FROM live_positions lp
            LEFT JOIN fires f ON lp.fire_id = f.fire_id
            WHERE lp.status = 'OPEN'
        """)

        active_trades = cur.fetchall()
        print(f"📊 Found {len(active_trades)} active trades to sync")

        for trade in active_trades:
            fire_id, user_id, symbol, direction, entry, lot_size, sl, tp, last_update, current_price, current_pnl, current_pips, ticket, created_at = trade

            # Use database current_price if available, otherwise use entry
            if not current_price:
                current_price = entry

            # Use database PNL and pips if available, otherwise calculate
            if current_pnl is not None and current_pips is not None:
                profit = current_pnl
                pips = current_pips
            else:
                profit, pips = calculate_trade_profit(entry, current_price, direction, symbol, lot_size)

            # Update Firebase
            trade_ref = db.collection('active_trades').document(fire_id)

            # Check if exists
            trade_doc = trade_ref.get()

            if trade_doc.exists:
                # Update existing
                trade_ref.update({
                    'current': current_price,
                    'equity': profit,
                    'pips': pips
                })
                print(f"✅ Updated trade {fire_id}: ${profit:.2f} ({pips:.1f} pips)")
            else:
                # Create new
                trade_data = {
                    'trade_id': fire_id,
                    'user_id': str(user_id),
                    'pair': symbol,
                    'entry': entry,
                    'current': current_price,
                    'stopLoss': sl or 0,
                    'takeProfit': tp or 0,
                    'equity': profit,
                    'pips': pips,
                    'lots': lot_size,
                    'startTime': datetime.fromtimestamp(created_at) if created_at else datetime.now(),
                    'direction': direction,
                    'history': [current_price],
                    'ticket': ticket or 0
                }
                trade_ref.set(trade_data)
                print(f"✅ Created trade {fire_id} in Firebase")

        conn.close()

    except Exception as e:
        print(f"❌ Error syncing active trades: {e}")


def sync_user_stats_to_firebase():
    """
    Sync user combat statistics to Firebase
    """
    try:
        db = get_firestore_client()
        if not db:
            return

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # Get all users with their stats
        cur.execute("""
            SELECT DISTINCT user_id FROM fires
        """)

        users = cur.fetchall()

        for (user_id,) in users:
            # Calculate wins/losses from closed trades
            cur.execute("""
                SELECT
                    f.fire_id,
                    lp.entry_price,
                    lp.direction,
                    lp.sl,
                    lp.tp,
                    f.price as exit_price
                FROM fires f
                LEFT JOIN live_positions lp ON f.fire_id = lp.fire_id
                WHERE f.user_id = ? AND f.status = 'CLOSED'
                ORDER BY f.created_at DESC
            """, (user_id,))

            closed_trades = cur.fetchall()

            wins = 0
            losses = 0
            current_streak = 0
            longest_streak = 0

            for fire_id, entry, direction, sl, tp, exit_price in closed_trades:
                if not entry or not exit_price:
                    continue

                # Determine if win or loss
                is_win = False
                if direction == 'BUY':
                    is_win = exit_price > entry
                elif direction == 'SELL':
                    is_win = exit_price < entry

                if is_win:
                    wins += 1
                    current_streak += 1
                    longest_streak = max(longest_streak, current_streak)
                else:
                    losses += 1
                    current_streak = 0

            # Get current balance from ea_instances
            cur.execute("""
                SELECT last_balance, last_equity
                FROM ea_instances
                WHERE user_id = ?
                ORDER BY last_seen DESC
                LIMIT 1
            """, (user_id,))

            balance_data = cur.fetchone()
            balance = balance_data[0] if balance_data else 1000
            equity = balance_data[1] if balance_data else balance

            # Update Firebase user document
            update_user_data(user_id, {
                'wins': wins,
                'losses': losses,
                'longestStreak': longest_streak,
                'balance': float(balance),
                'equity': float(equity)
            })

            print(f"✅ Updated user {user_id}: {wins}W/{losses}L, Streak: {longest_streak}, Balance: ${balance:.2f}")

        conn.close()

    except Exception as e:
        print(f"❌ Error syncing user stats: {e}")


def sync_today_performance():
    """
    Calculate and sync today's performance metrics
    """
    try:
        db = get_firestore_client()
        if not db:
            return

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # Get start of today (midnight)
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_timestamp = int(today_start.timestamp())

        # Get all users
        cur.execute("SELECT DISTINCT user_id FROM fires")
        users = cur.fetchall()

        for (user_id,) in users:
            # Get today's closed trades
            cur.execute("""
                SELECT
                    lp.entry_price,
                    lp.direction,
                    lp.symbol,
                    lp.lot_size,
                    f.price as exit_price
                FROM fires f
                LEFT JOIN live_positions lp ON f.fire_id = lp.fire_id
                WHERE f.user_id = ?
                    AND f.status = 'CLOSED'
                    AND f.created_at >= ?
            """, (user_id, today_timestamp))

            today_trades = cur.fetchall()

            total_profit = 0.0
            for entry, direction, symbol, lot_size, exit_price in today_trades:
                if entry and exit_price and direction and symbol and lot_size:
                    profit, _ = calculate_trade_profit(entry, exit_price, direction, symbol, lot_size)
                    total_profit += profit

            # Update user document with today's P/L
            db.collection('users').document(str(user_id)).update({
                'todayPL': total_profit,
                'todayTrades': len(today_trades),
                'lastSync': datetime.now()
            })

            print(f"✅ User {user_id} today's P/L: ${total_profit:.2f} ({len(today_trades)} trades)")

        conn.close()

    except Exception as e:
        print(f"❌ Error syncing today's performance: {e}")


if __name__ == '__main__':
    print("🔥 Starting Firebase Battlefield Sync...")
    print()

    print("📊 Syncing active trades...")
    sync_active_trades_to_firebase()
    print()

    print("👥 Syncing user statistics...")
    sync_user_stats_to_firebase()
    print()

    print("📈 Syncing today's performance...")
    sync_today_performance()
    print()

    print("✅ Firebase Battlefield Sync Complete!")
