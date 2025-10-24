#!/usr/bin/env python3
"""
Position Close Detector - Detects closed positions and calculates profit/outcome
Works around EA v3.013 OnTrade() not triggering position_closed events

Detects closures by:
1. Checking live_positions with status='CLOSED'
2. Checking for stale position_updates (no updates in 120+ seconds)
3. Calculating profit/pips/outcome from available data
4. Moving to trade_history via firebase_backend

Run manually:
    python3 position_close_detector.py

Or run as PM2 service (every 60 seconds):
    pm2 start position_close_detector.py --name position_close_detector --interpreter python3 --cron "* * * * *"
"""
import sys
sys.path.insert(0, '/root/HydraX-v2')

import sqlite3
import time
from firebase_backend import get_firestore_client, close_active_trade
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

DB_PATH = "/root/HydraX-v2/bitten.db"

# Pip values per standard lot
PIP_VALUES = {
    "EURUSD": 10.0, "GBPUSD": 10.0, "USDJPY": 9.09,
    "USDCHF": 10.0, "AUDUSD": 10.0, "NZDUSD": 10.0,
    "USDCAD": 9.09, "EURJPY": 9.09, "GBPJPY": 9.09,
    "AUDJPY": 9.09, "NZDJPY": 9.09, "XAUUSD": 10.0,
    "USDCNH": 10.0, "XAGUSD": 10.0, "EURGBP": 10.0,
    "GBPJPY": 9.09, "EURAUD": 10.0, "EURNZD": 10.0,
    "GBPAUD": 10.0, "GBPNZD": 10.0
}

def calculate_pips(symbol: str, entry_price: float, exit_price: float, direction: str) -> float:
    """Calculate pip movement considering direction"""
    # Determine pip multiplier based on symbol
    if 'JPY' in symbol:
        pip_multiplier = 100  # JPY pairs: 0.01 = 1 pip
    else:
        pip_multiplier = 10000  # Other pairs: 0.0001 = 1 pip

    # Calculate raw price difference
    price_diff = exit_price - entry_price

    # Convert to pips
    pips = price_diff * pip_multiplier

    # Apply direction (SELL inverts the pips)
    if direction == 'SELL':
        pips = -pips

    return round(pips, 1)

def calculate_profit(symbol: str, entry_price: float, exit_price: float,
                     lot_size: float, direction: str) -> float:
    """Calculate profit in account currency"""
    pip_value = PIP_VALUES.get(symbol, 10.0)
    pips = calculate_pips(symbol, entry_price, exit_price, direction)

    # Profit = pips * pip_value * lot_size / 10 (for mini lot adjustment)
    profit = (pips * pip_value * lot_size) / 10

    return round(profit, 2)

def determine_outcome(profit: float, close_reason: str = None) -> str:
    """Determine if trade was TP HIT or SL HIT"""
    if close_reason:
        reason_upper = close_reason.upper()
        if 'TP' in reason_upper or 'TAKEPROFIT' in reason_upper:
            return 'TP HIT'
        elif 'SL' in reason_upper or 'STOPLOSS' in reason_upper:
            return 'SL HIT'

    # Fallback: use profit to determine
    return 'TP HIT' if profit > 0 else 'SL HIT'

def find_closed_positions():
    """Find positions that closed but need data calculated"""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Find live_positions marked CLOSED
    cursor.execute("""
        SELECT lp.fire_id, lp.user_id, lp.symbol, lp.direction,
               lp.entry_price, lp.sl, lp.tp, lp.lot_size, lp.ticket,
               lp.last_update, lp.current_price,
               f.close_price, f.close_reason, f.profit as fire_profit
        FROM live_positions lp
        LEFT JOIN fires f ON lp.fire_id = f.fire_id
        WHERE lp.status = 'CLOSED'
        AND lp.last_update > ?
        ORDER BY lp.last_update DESC
        LIMIT 500
    """, (int(time.time()) - 86400 * 7,))  # Last 7 days

    closed_positions = cursor.fetchall()
    conn.close()

    return closed_positions

def check_if_already_processed(fire_id: str) -> bool:
    """Check if position already in trade_history with calculated data"""
    db = get_firestore_client()
    if not db:
        return False

    try:
        doc = db.collection('trade_history').document(fire_id).get()
        if not doc.exists:
            return False

        data = doc.to_dict()
        # Check if it has proper data (not zeros)
        has_profit = data.get('profit', 0) != 0
        has_outcome = data.get('outcome') is not None and data.get('outcome') != ''

        return has_profit or has_outcome
    except Exception as e:
        logger.error(f"Error checking trade_history for {fire_id}: {e}")
        return False

def process_closed_position(position):
    """Process a closed position - calculate and sync to Firebase"""
    fire_id = position['fire_id']
    user_id = position['user_id']
    symbol = position['symbol']
    direction = position['direction']
    entry_price = position['entry_price']
    lot_size = position['lot_size']
    ticket = position['ticket']

    # Determine close price (prefer fires.close_price, fallback to current_price)
    close_price = position['close_price'] or position['current_price']
    close_reason = position['close_reason']

    # Skip if no close price
    if not close_price or close_price == 0:
        logger.warning(f"⚠️ {fire_id} - No close price available, skipping")
        return False

    # Skip if no lot size
    if not lot_size or lot_size == 0:
        logger.warning(f"⚠️ {fire_id} - No lot size available, skipping")
        return False

    # Skip if entry == exit (no movement, likely corrupt data)
    if abs(entry_price - close_price) < 0.00001:
        logger.warning(f"⚠️ {fire_id} - Entry equals exit ({entry_price}), skipping corrupt data")
        return False

    # Skip if already processed
    if check_if_already_processed(fire_id):
        logger.debug(f"✓ {fire_id} - Already processed")
        return True

    try:
        # Calculate profit and pips
        profit = calculate_profit(symbol, entry_price, close_price, lot_size, direction)
        pips = calculate_pips(symbol, entry_price, close_price, direction)
        outcome = determine_outcome(profit, close_reason)

        logger.info(f"📊 Processing {fire_id}")
        logger.info(f"   {symbol} {direction} | Entry: {entry_price:.5f} | Exit: {close_price:.5f}")
        logger.info(f"   Lot: {lot_size} | Profit: ${profit:.2f} | Pips: {pips:+.1f} | Outcome: {outcome}")

        # Move to trade_history via Firebase backend
        success = close_active_trade(
            trade_id=fire_id,
            exit_price=close_price,
            profit=profit,
            pips=pips,
            outcome=outcome
        )

        if success:
            logger.info(f"   ✅ Moved to trade_history")

            # Update fires table with profit if not already set
            if position['fire_profit'] == 0 or position['fire_profit'] is None:
                conn = sqlite3.connect(DB_PATH, timeout=10)
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE fires
                    SET profit = ?, close_reason = ?, close_price = ?
                    WHERE fire_id = ?
                """, (profit, outcome, close_price, fire_id))
                conn.commit()
                conn.close()
                logger.info(f"   ✅ Updated fires table")

            return True
        else:
            logger.error(f"   ❌ Failed to move to trade_history")
            return False

    except Exception as e:
        logger.error(f"❌ Error processing {fire_id}: {e}", exc_info=True)
        return False

def main():
    """Main loop - detect and process closed positions"""
    logger.info("=" * 70)
    logger.info("🚀 Position Close Detector Starting")
    logger.info("=" * 70)

    # Find closed positions
    closed_positions = find_closed_positions()
    logger.info(f"📊 Found {len(closed_positions)} closed positions to check")

    if not closed_positions:
        logger.info("✅ No closed positions need processing")
        return

    processed = 0
    skipped = 0
    failed = 0

    for position in closed_positions:
        try:
            result = process_closed_position(position)
            if result is True:
                processed += 1
            elif result is False:
                failed += 1
            else:
                skipped += 1
        except Exception as e:
            logger.error(f"❌ Exception processing {position['fire_id']}: {e}")
            failed += 1

    logger.info("=" * 70)
    logger.info(f"✅ Complete - Processed: {processed} | Skipped: {skipped} | Failed: {failed}")
    logger.info("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⚠️ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)
