"""
Firebase Backend Integration for BITTEN
Writes trading data to Firebase Firestore for React UI consumption
"""

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import json
import os

# Initialize Firebase Admin SDK
_firebase_initialized = False
_db = None

def initialize_firebase():
    """Initialize Firebase Admin SDK with service account"""
    global _firebase_initialized, _db

    if _firebase_initialized:
        return _db

    try:
        # Path to service account key
        cred_path = '/root/bitten-firebase-sa.json'

        if not os.path.exists(cred_path):
            print(f"❌ Firebase service account key not found at {cred_path}")
            return None

        # Initialize Firebase Admin
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

        # Get Firestore client
        _db = firestore.client()
        _firebase_initialized = True

        print("✅ Firebase Admin SDK initialized successfully")
        return _db

    except Exception as e:
        print(f"❌ Firebase initialization error: {e}")
        return None


def get_firestore_client():
    """Get Firestore client, initializing if needed"""
    global _db
    if _db is None:
        _db = initialize_firebase()
    return _db


# ==================== SIGNAL OPERATIONS ====================

def write_signal_to_firebase(signal_data: dict) -> bool:
    """
    Write trading signal to Firebase signals collection

    Args:
        signal_data: Dict with keys:
            - signal_id (required)
            - symbol/pair
            - direction
            - entry_price/entry
            - sl
            - tp
            - confidence
            - pattern_type/pattern
            - session
            - signal_type
            - created_at (timestamp)

    Returns:
        bool: True if successful
    """
    try:
        db = get_firestore_client()
        if not db:
            return False

        signal_id = signal_data.get('signal_id')
        if not signal_id:
            print("❌ Signal missing signal_id")
            return False

        # Normalize field names for frontend
        firebase_signal = {
            'signal_id': signal_id,
            'pair': signal_data.get('symbol') or signal_data.get('pair'),
            'pattern': signal_data.get('pattern_type') or signal_data.get('pattern'),
            'timeframe': signal_data.get('timeframe', '5-MIN'),
            'session': signal_data.get('session', 'UNKNOWN'),
            'timestamp': firestore.SERVER_TIMESTAMP,  # Reverted to original field name
            'confidence': signal_data.get('confidence', 0),
            'status': signal_data.get('status', 'new'),
            'signal_type': signal_data.get('signal_type', 'RAPID_ASSAULT'),
            'direction': signal_data.get('direction'),
            'entry': signal_data.get('entry_price') or signal_data.get('entry'),
            'sl': signal_data.get('sl'),
            'tp': signal_data.get('tp'),
            'outcome': signal_data.get('outcome'),
            'outcome_delta': signal_data.get('outcome_delta')
        }

        # Write to Firebase
        db.collection('signals').document(signal_id).set(firebase_signal)
        print(f"✅ Signal {signal_id} written to Firebase")
        return True

    except Exception as e:
        print(f"❌ Error writing signal to Firebase: {e}")
        return False


def update_signal_status(signal_id: str, status: str, outcome: str = None, outcome_delta: str = None) -> bool:
    """Update signal status and outcome in Firebase"""
    try:
        db = get_firestore_client()
        if not db:
            return False

        update_data = {'status': status}
        if outcome:
            update_data['outcome'] = outcome
        if outcome_delta:
            update_data['outcome_delta'] = outcome_delta

        db.collection('signals').document(signal_id).update(update_data)
        print(f"✅ Signal {signal_id} status updated to {status}")
        return True

    except Exception as e:
        print(f"❌ Error updating signal status: {e}")
        return False


# ==================== USER OPERATIONS ====================

def update_user_data(user_id: str, user_data: dict) -> bool:
    """
    Update user document in Firebase

    Args:
        user_id: Firebase UID or telegram_id
        user_data: Dict with any of:
            - balance
            - equity
            - tier
            - wins
            - losses
            - longestStreak
            - displayName
            - riskPct
            - autoFire
            - closeWeekends
            - notifications

    Returns:
        bool: True if successful
    """
    try:
        db = get_firestore_client()
        if not db:
            return False

        # Use merge=True to not overwrite entire document
        db.collection('users').document(str(user_id)).set(user_data, merge=True)
        print(f"✅ User {user_id} data updated in Firebase")
        return True

    except Exception as e:
        print(f"❌ Error updating user data: {e}")
        return False


def create_user_if_not_exists(user_id: str, initial_data: dict) -> bool:
    """Create user document if it doesn't exist"""
    try:
        db = get_firestore_client()
        if not db:
            return False

        user_ref = db.collection('users').document(str(user_id))
        user_doc = user_ref.get()

        if not user_doc.exists:
            default_user = {
                'uid': str(user_id),
                'telegram_id': str(user_id),
                'displayName': initial_data.get('displayName', 'OPERATOR'),
                'tier': initial_data.get('tier', 'RECRUIT'),
                'balance': initial_data.get('balance', 0),
                'equity': initial_data.get('equity', 0),
                'wins': 0,
                'losses': 0,
                'longestStreak': 0,
                'xp': 0,
                'stx': 0,
                'xpAmmo': 0,
                'medals': 0,
                'achievements': [],
                'referralLink': f'https://joinbitten.com/ref/{user_id}',
                'referralCount': 0,
                'referralDiscountPct': 0,
                'riskPct': 2.0,
                'autoFire': False,
                'closeWeekends': True,
                'notifications': True,
                'initialCapital': initial_data.get('balance', 0),
                'created_at': firestore.SERVER_TIMESTAMP
            }
            user_ref.set(default_user)
            print(f"✅ User {user_id} created in Firebase")

        return True

    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return False


# ==================== TRADE OPERATIONS ====================

def write_active_trade(trade_data: dict) -> bool:
    """
    Write active trade to Firebase active_trades collection

    Args:
        trade_data: Dict with keys:
            - trade_id or fire_id (required)
            - user_id (required)
            - pair/symbol
            - entry
            - current (optional, defaults to entry)
            - stopLoss/sl
            - takeProfit/tp
            - equity (current P/L)
            - lots
            - startTime (timestamp)
            - direction
            - history (optional array)

    Returns:
        bool: True if successful
    """
    try:
        db = get_firestore_client()
        if not db:
            return False

        trade_id = trade_data.get('trade_id') or trade_data.get('fire_id')
        user_id = trade_data.get('user_id')

        if not trade_id or not user_id:
            print("❌ Trade missing trade_id or user_id")
            return False

        # Normalize field names
        firebase_trade = {
            'trade_id': trade_id,
            'user_id': str(user_id),
            'pair': trade_data.get('symbol') or trade_data.get('pair'),
            'entry': trade_data.get('entry', 0),
            'current': trade_data.get('current') or trade_data.get('entry', 0),
            'stopLoss': trade_data.get('stopLoss') or trade_data.get('sl', 0),
            'takeProfit': trade_data.get('takeProfit') or trade_data.get('tp', 0),
            'equity': trade_data.get('equity', 0),
            'lots': trade_data.get('lots') or trade_data.get('lot', 0),
            'startTime': firestore.SERVER_TIMESTAMP,
            'direction': trade_data.get('direction', 'BUY'),
            'history': trade_data.get('history', [])
        }

        db.collection('active_trades').document(trade_id).set(firebase_trade)
        print(f"✅ Active trade {trade_id} written to Firebase")
        return True

    except Exception as e:
        print(f"❌ Error writing active trade: {e}")
        return False


def update_active_trade_price(trade_id: str, current_price: float, equity: float) -> bool:
    """Update current price and equity of active trade (creates document if missing with full data from SQLite)"""
    try:
        db = get_firestore_client()
        if not db:
            return False

        # Check if document exists
        doc_ref = db.collection('active_trades').document(trade_id)
        doc = doc_ref.get()

        if not doc.exists:
            # Document doesn't exist - CHECK if position is OPEN before creating
            import sqlite3
            from datetime import datetime
            conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
            cursor = conn.cursor()

            # Check live_positions first - only create if status='OPEN'
            cursor.execute("""
                SELECT status FROM live_positions WHERE fire_id = ?
            """, (trade_id,))
            pos_row = cursor.fetchone()

            # Only create Firestore document if position is OPEN
            if pos_row and pos_row[0] == 'OPEN':
                cursor.execute("""
                    SELECT user_id, symbol, direction, price, sl, tp, lot, created_at, ticket
                    FROM fires
                    WHERE fire_id = ?
                """, (trade_id,))
                row = cursor.fetchone()

                if row:
                    user_id, symbol, direction, entry, sl, tp, lots, created_at, ticket = row
                    # Create document with full data
                    doc_ref.set({
                        'trade_id': trade_id,
                        'user_id': user_id,
                        'symbol': symbol,  # FIXED: was 'pair'
                        'pair': symbol,
                        'direction': direction,
                        'entry': float(entry) if entry else 0,
                        'current': float(current_price),
                        'stopLoss': float(sl) if sl else 0,
                        'takeProfit': float(tp) if tp else 0,
                        'equity': float(equity),
                        'volume': float(lots) if lots else 0,  # ADDED: for Battlefield
                        'lots': float(lots) if lots else 0,
                        'startTime': datetime.fromtimestamp(created_at) if created_at else datetime.now(),
                        'ticket': ticket if ticket else 0,
                        'history': []
                    })
                    print(f"✅ Created Firestore doc for OPEN position: {trade_id}")
            else:
                # Position is CLOSED or doesn't exist - do NOT create Firestore document
                print(f"⚠️ Skipping Firestore creation for closed/missing position: {trade_id}")

            conn.close()
        else:
            # Document exists - just update current price and equity
            doc_ref.set({'current': current_price, 'equity': equity}, merge=True)

        return True

    except Exception as e:
        print(f"❌ Error updating trade price: {e}")
        return False


def close_active_trade(trade_id: str, exit_price: float, profit: float, pips: float, outcome: str) -> bool:
    """
    Close active trade and move to trade_history

    Args:
        trade_id: Trade ID
        exit_price: Final exit price
        profit: Profit in account currency
        pips: Profit in pips
        outcome: 'TP HIT' or 'SL HIT'

    Returns:
        bool: True if successful
    """
    try:
        db = get_firestore_client()
        if not db:
            return False

        # Get active trade
        trade_ref = db.collection('active_trades').document(trade_id)
        trade_doc = trade_ref.get()

        if not trade_doc.exists:
            print(f"❌ Active trade {trade_id} not found")
            return False

        trade_data = trade_doc.to_dict()

        # Create history record
        history_record = {
            'trade_id': trade_id,
            'user_id': trade_data.get('user_id'),
            'pair': trade_data.get('pair'),
            'entry': trade_data.get('entry'),
            'exit': exit_price,
            'profit': profit,
            'pips': pips,
            'lots': trade_data.get('lots'),
            'direction': trade_data.get('direction'),
            'pattern': trade_data.get('pattern', ''),
            'startTime': trade_data.get('startTime'),
            'endTime': firestore.SERVER_TIMESTAMP,
            'outcome': outcome
        }

        # Write to history
        db.collection('trade_history').document(trade_id).set(history_record)

        # Delete from active trades
        trade_ref.delete()

        # Update user wins/losses
        user_id = trade_data.get('user_id')
        if user_id:
            user_ref = db.collection('users').document(str(user_id))
            is_win = (outcome == 'TP HIT')

            if is_win:
                user_ref.update({'wins': firestore.Increment(1)})
            else:
                user_ref.update({'losses': firestore.Increment(1)})

            # ✅ UPDATE COMPREHENSIVE STATISTICS
            # 1. Daily statistics (trades, P&L, daily wins/losses)
            update_daily_statistics(user_id, profit, is_win)

            # 2. Historical stats (win streaks, accuracy, total profit)
            update_historical_stats(user_id, is_win, profit)

            # 3. Update aggregated P&L and averages (for AI context enrichment)
            update_aggregated_stats(user_id, profit, is_win)

            # 4. Get current equity and update peak/drawdown tracking
            user_doc = user_ref.get()
            if user_doc.exists:
                current_equity = user_doc.to_dict().get('equity', 0)
                if current_equity > 0:
                    update_peak_equity_and_drawdown(user_id, current_equity)

        print(f"✅ Trade {trade_id} closed and moved to history ({outcome})")
        return True

    except Exception as e:
        print(f"❌ Error closing trade: {e}")
        return False


# ==================== MISSION OPERATIONS ====================

def write_mission_to_firebase(mission_data: dict) -> bool:
    """
    Write mission to Firebase missions collection

    Args:
        mission_data: Dict with keys:
            - mission_id (required)
            - signal_id
            - payload_json (signal details)
            - status
            - expires_at
            - created_at
            - user_id

    Returns:
        bool: True if successful
    """
    try:
        db = get_firestore_client()
        if not db:
            return False

        mission_id = mission_data.get('mission_id')
        if not mission_id:
            print("❌ Mission missing mission_id")
            return False

        firebase_mission = {
            'mission_id': mission_id,
            'signal_id': mission_data.get('signal_id'),
            'payload_json': mission_data.get('payload_json', {}),
            'status': mission_data.get('status', 'active'),
            'expires_at': mission_data.get('expires_at'),
            'created_at': mission_data.get('created_at') or firestore.SERVER_TIMESTAMP,
            'user_id': str(mission_data.get('user_id', ''))
        }

        db.collection('missions').document(mission_id).set(firebase_mission)
        print(f"✅ Mission {mission_id} written to Firebase")
        return True

    except Exception as e:
        print(f"❌ Error writing mission: {e}")
        return False


# ==================== DAILY STATISTICS ====================

def update_daily_statistics(user_id: str, profit: float, is_win: bool) -> bool:
    """
    Update daily trading statistics for user

    Args:
        user_id: Firebase user ID
        profit: Trade profit (positive or negative)
        is_win: True if win, False if loss

    Returns:
        bool: True if successful
    """
    try:
        db = get_firestore_client()
        if not db:
            return False

        user_ref = db.collection('users').document(str(user_id))

        # Update daily stats (will reset at midnight via separate scheduled job)
        # Use set with merge=True to create fields if they don't exist
        user_ref.set({
            'todayTrades': firestore.Increment(1),
            'todayPL': firestore.Increment(round(profit, 2)),
            'todayWins': firestore.Increment(1 if is_win else 0),
            'todayLosses': firestore.Increment(0 if is_win else 1)
        }, merge=True)

        print(f"✅ Updated daily stats for user {user_id}: profit=${profit:.2f}, win={is_win}")
        return True

    except Exception as e:
        print(f"❌ Error updating daily stats: {e}")
        return False


def update_peak_equity_and_drawdown(user_id: str, current_equity: float) -> bool:
    """
    Track peak equity and maximum drawdown for user

    Args:
        user_id: Firebase user ID
        current_equity: Current account equity

    Returns:
        bool: True if successful
    """
    try:
        db = get_firestore_client()
        if not db:
            return False

        user_ref = db.collection('users').document(str(user_id))
        user_doc = user_ref.get()

        if not user_doc.exists:
            return False

        user_data = user_doc.to_dict()
        peak_equity = user_data.get('peakEquity')
        max_drawdown = user_data.get('maxDrawdown', 0)

        updates = {}

        # Initialize peak equity if it doesn't exist
        if peak_equity is None:
            updates['peakEquity'] = current_equity
            peak_equity = current_equity
            print(f"🆕 Initializing peak equity for user {user_id}: ${current_equity:.2f}")
        # Update peak equity if new high
        elif current_equity > peak_equity:
            updates['peakEquity'] = current_equity
            peak_equity = current_equity

        # Calculate current drawdown from peak
        if peak_equity > 0:
            current_drawdown = ((peak_equity - current_equity) / peak_equity) * 100

            # Update max drawdown if worse
            if current_drawdown > max_drawdown:
                updates['maxDrawdown'] = round(current_drawdown, 2)

        if updates:
            # Use set with merge=True to create fields if they don't exist
            user_ref.set(updates, merge=True)
            print(f"✅ Updated equity tracking for user {user_id}: peak=${peak_equity:.2f}, drawdown={updates.get('maxDrawdown', max_drawdown):.2f}%")

        return True

    except Exception as e:
        print(f"❌ Error updating equity tracking: {e}")
        return False


def update_historical_stats(user_id: str, is_win: bool, profit: float) -> bool:
    """
    Update historical trading statistics and streaks

    Args:
        user_id: Firebase user ID
        is_win: True if win, False if loss
        profit: Trade profit

    Returns:
        bool: True if successful
    """
    try:
        db = get_firestore_client()
        if not db:
            return False

        user_ref = db.collection('users').document(str(user_id))
        user_doc = user_ref.get()

        if not user_doc.exists:
            return False

        user_data = user_doc.to_dict()

        # Get current streak data
        current_win_streak = user_data.get('currentWinStreak', 0)
        current_loss_streak = user_data.get('currentLossStreak', 0)
        longest_win_streak = user_data.get('longestWinStreak', 0)
        longest_loss_streak = user_data.get('longestLossStreak', 0)
        total_wins = user_data.get('wins', 0)
        total_losses = user_data.get('losses', 0)

        updates = {}

        if is_win:
            # Update win streak
            current_win_streak += 1
            current_loss_streak = 0

            if current_win_streak > longest_win_streak:
                updates['longestWinStreak'] = current_win_streak

            updates['currentWinStreak'] = current_win_streak
            updates['currentLossStreak'] = 0

        else:
            # Update loss streak
            current_loss_streak += 1
            current_win_streak = 0

            if current_loss_streak > longest_loss_streak:
                updates['longestLossStreak'] = current_loss_streak

            updates['currentLossStreak'] = current_loss_streak
            updates['currentWinStreak'] = 0

        # Calculate win rate
        total_trades = total_wins + total_losses + (1 if is_win else 0) + (0 if is_win else 1)
        if total_trades > 0:
            win_rate = ((total_wins + (1 if is_win else 0)) / total_trades) * 100
            updates['accuracy'] = round(win_rate, 1)

        # Update total profit
        updates['totalProfit'] = firestore.Increment(round(profit, 2))

        # Use set with merge=True to create fields if they don't exist
        user_ref.set(updates, merge=True)
        print(f"✅ Updated historical stats for user {user_id}: win_streak={current_win_streak}, accuracy={updates.get('accuracy', 0):.1f}%")
        return True

    except Exception as e:
        print(f"❌ Error updating historical stats: {e}")
        return False


def update_aggregated_stats(user_id: str, profit: float, is_win: bool) -> bool:
    """
    Update aggregated P&L and average win/loss (for AI context enrichment)

    Args:
        user_id: Firebase user ID
        profit: Trade profit (positive or negative)
        is_win: True if win, False if loss

    Returns:
        bool: True if successful
    """
    try:
        db = get_firestore_client()
        if not db:
            return False

        user_ref = db.collection('users').document(str(user_id))
        user_doc = user_ref.get()

        if not user_doc.exists:
            return False

        user_data = user_doc.to_dict()

        # Get current aggregated values
        total_wins = user_data.get('wins', 0)
        total_losses = user_data.get('losses', 0)
        old_avg_win = user_data.get('avgWin', 0)
        old_avg_loss = user_data.get('avgLoss', 0)

        updates = {
            'totalPnL': firestore.Increment(round(profit, 2)),
            'lastTradeAt': firestore.SERVER_TIMESTAMP
        }

        # Update running average for wins or losses
        if is_win and profit > 0:
            # Calculate new average win (incremental mean formula)
            new_avg_win = ((old_avg_win * (total_wins - 1)) + profit) / total_wins if total_wins > 0 else profit
            updates['avgWin'] = round(new_avg_win, 2)
        elif not is_win and profit < 0:
            # Calculate new average loss (use absolute value)
            new_avg_loss = ((old_avg_loss * (total_losses - 1)) + abs(profit)) / total_losses if total_losses > 0 else abs(profit)
            updates['avgLoss'] = round(new_avg_loss, 2)

        user_ref.set(updates, merge=True)
        print(f"✅ Updated aggregated stats for user {user_id}: totalPnL updated, avg_win={updates.get('avgWin', old_avg_win):.2f}, avg_loss={updates.get('avgLoss', old_avg_loss):.2f}")
        return True

    except Exception as e:
        print(f"❌ Error updating aggregated stats: {e}")
        return False


def sync_fire_mode_status(user_id: str) -> bool:
    """
    Sync user's fire mode status from SQLite to Firebase

    Args:
        user_id: Firebase user ID

    Returns:
        bool: True if successful
    """
    try:
        import sqlite3
        db = get_firestore_client()
        if not db:
            return False

        # Check bitten.db for user's fire mode (user_fire_modes table)
        bitten_db = '/root/HydraX-v2/bitten.db'
        if not os.path.exists(bitten_db):
            return False

        conn = sqlite3.connect(bitten_db)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT current_mode, auto_fire_enabled, trading_enabled FROM user_fire_modes WHERE user_id = ?",
            (str(user_id),)
        )
        result = cursor.fetchone()
        conn.close()

        if result:
            mode = result[0]  # MANUAL, AUTO, etc.
            auto_fire_enabled = result[1]  # 1 or 0
            trading_enabled = result[2] if len(result) > 2 else 1  # 1 or 0, default enabled

            user_ref = db.collection('users').document(str(user_id))
            # Use set with merge=True to create fields if they don't exist
            user_ref.set({
                'fireMode': mode,
                'isAutoFire': bool(auto_fire_enabled),
                'safetyLocked': not bool(trading_enabled)  # Inverted: trading_enabled=0 means locked
            }, merge=True)

            print(f"✅ Synced fire mode for user {user_id}: {mode} (auto: {bool(auto_fire_enabled)}, locked: {not bool(trading_enabled)})")
            return True

        return False

    except Exception as e:
        print(f"❌ Error syncing fire mode: {e}")
        return False


def sync_autofire_settings_to_db(user_id: str) -> bool:
    """
    Sync user's autofire settings FROM Firebase TO SQLite database
    This ensures Fire Control Settings page changes are reflected in auto fire logic

    Args:
        user_id: Firebase user ID

    Returns:
        bool: True if successful
    """
    try:
        import sqlite3
        db = get_firestore_client()
        if not db:
            return False

        # Read from Firebase autofire_settings collection
        autofire_ref = db.collection('autofire_settings').document(str(user_id))
        autofire_doc = autofire_ref.get()

        if not autofire_doc.exists:
            return False

        settings = autofire_doc.to_dict()

        # Extract settings
        auto_slots = settings.get('autoSlots', 5)
        confidence_min = settings.get('confidenceMin', 80)
        confidence_max = settings.get('confidenceMax', 97)

        # Update bitten.db
        bitten_db = '/root/HydraX-v2/bitten.db'
        if not os.path.exists(bitten_db):
            return False

        conn = sqlite3.connect(bitten_db)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE user_fire_modes
            SET max_auto_slots = ?,
                auto_fire_min_confidence = ?,
                auto_fire_max_confidence = ?
            WHERE user_id = ?
        """, (auto_slots, confidence_min, confidence_max, str(user_id)))

        rows_updated = cursor.rowcount
        conn.commit()
        conn.close()

        if rows_updated > 0:
            print(f"✅ Synced autofire settings for user {user_id}: slots={auto_slots}, conf={confidence_min}-{confidence_max}")
            return True

        return False

    except Exception as e:
        print(f"❌ Error syncing autofire settings: {e}")
        return False


def toggle_safety_lock(user_id: str, locked: bool) -> dict:
    """
    Toggle safety lock for user - 100% prevents ALL trading when locked

    Args:
        user_id: Firebase user ID
        locked: True to lock (prevent trading), False to unlock (allow trading)

    Returns:
        dict: {'success': bool, 'locked': bool, 'message': str}
    """
    try:
        import sqlite3

        bitten_db = '/root/HydraX-v2/bitten.db'
        if not os.path.exists(bitten_db):
            return {'success': False, 'message': 'Database not found'}

        conn = sqlite3.connect(bitten_db)
        cursor = conn.cursor()

        # Update trading_enabled in database (inverted logic: 0 = locked, 1 = unlocked)
        trading_enabled = 0 if locked else 1

        cursor.execute(
            """
            UPDATE user_fire_modes
            SET trading_enabled = ?, updated_at = ?
            WHERE user_id = ?
            """,
            (trading_enabled, int(time.time()), str(user_id))
        )

        # If user doesn't exist, create record with locked status
        if cursor.rowcount == 0:
            cursor.execute(
                """
                INSERT INTO user_fire_modes
                (user_id, trading_enabled, updated_at)
                VALUES (?, ?, ?)
                """,
                (str(user_id), trading_enabled, int(time.time()))
            )

        conn.commit()
        conn.close()

        # Sync to Firebase
        db = get_firestore_client()
        if db:
            user_ref = db.collection('users').document(str(user_id))
            user_ref.set({
                'safetyLocked': locked
            }, merge=True)
            print(f"✅ Firebase: Safety lock {'ENGAGED' if locked else 'DISENGAGED'} for user {user_id}")

        status = "LOCKED 🔒" if locked else "UNLOCKED 🔓"
        print(f"✅ Safety lock {status} for user {user_id}")

        return {
            'success': True,
            'locked': locked,
            'message': f'Safety lock {status}. {"All trading BLOCKED." if locked else "Trading enabled."}'
        }

    except Exception as e:
        print(f"❌ Error toggling safety lock: {e}")
        return {'success': False, 'message': str(e)}


def check_safety_lock(user_id: str) -> bool:
    """
    Check if user's safety lock is engaged (trading blocked)

    Args:
        user_id: Firebase user ID

    Returns:
        bool: True if locked (trading blocked), False if unlocked (trading allowed)
    """
    try:
        import sqlite3

        bitten_db = '/root/HydraX-v2/bitten.db'
        if not os.path.exists(bitten_db):
            return False  # Default to unlocked if DB doesn't exist

        conn = sqlite3.connect(bitten_db)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT trading_enabled FROM user_fire_modes WHERE user_id = ?",
            (str(user_id),)
        )
        result = cursor.fetchone()
        conn.close()

        if result:
            trading_enabled = result[0]
            return trading_enabled == 0  # Return True if locked (trading_enabled = 0)

        return False  # Default to unlocked if user not found

    except Exception as e:
        print(f"❌ Error checking safety lock: {e}")
        return False  # Default to unlocked on error


# ==================== BATCH OPERATIONS ====================

def sync_all_users_to_firebase():
    """Sync all users from SQLite to Firebase (one-time migration helper)"""
    try:
        import sqlite3
        db = get_firestore_client()
        if not db:
            return False

        # Connect to SQLite
        conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
        cursor = conn.cursor()

        # Get all users (you may need to adjust table name)
        cursor.execute("SELECT user_id, balance, tier FROM ea_instances")  # Adjust query as needed

        for row in cursor.fetchall():
            user_id, balance, tier = row
            create_user_if_not_exists(user_id, {
                'balance': balance or 0,
                'tier': tier or 'RECRUIT'
            })

        conn.close()
        print("✅ Users synced to Firebase")
        return True

    except Exception as e:
        print(f"❌ Error syncing users: {e}")
        return False


# Initialize on import
initialize_firebase()
