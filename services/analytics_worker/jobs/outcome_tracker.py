"""
Outcome Tracker Job
Subscribes to market data and tracks signals to TP/SL completion
"""
import asyncio
import json
import logging
import time
from collections import defaultdict
from typing import Dict, List, Optional
from datetime import datetime, timedelta

import zmq
import zmq.asyncio
import psycopg2
from psycopg2.extras import RealDictCursor

from ..config import (
    DATABASE_URL,
    ZMQ_MARKET_DATA_ENDPOINT,
    OUTCOME_TRACKING_CONFIG,
    MAX_RETRIES,
    RETRY_DELAY_SECONDS
)

logger = logging.getLogger(__name__)


class OutcomeTracker:
    """Tracks active signals to TP/SL completion"""

    def __init__(self):
        self.context = zmq.asyncio.Context()
        self.subscriber = None
        self.active_signals: Dict[str, Dict] = {}
        self.tick_cache: Dict[str, List[Dict]] = defaultdict(list)
        self.running = False

    def _get_db_connection(self):
        """Get PostgreSQL connection"""
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

    async def initialize(self):
        """Initialize ZMQ subscriber and load active signals"""
        logger.info("Initializing Outcome Tracker...")

        # Setup ZMQ subscriber
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect(ZMQ_MARKET_DATA_ENDPOINT)
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, "")

        # Load active signals from database
        await self._load_active_signals()

        logger.info(f"Loaded {len(self.active_signals)} active signals")

    async def _load_active_signals(self):
        """Load active signals from database"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()

            # Get signals created in last 24 hours that are still active
            cutoff_time = int((datetime.utcnow() - timedelta(hours=24)).timestamp())

            cursor.execute("""
                SELECT signal_id, symbol, direction, entry_price,
                       sl_price, tp_price, confidence, pattern_type,
                       created_at
                FROM signals
                WHERE status = 'ACTIVE'
                  AND created_at > %s
                ORDER BY created_at DESC
            """, (cutoff_time,))

            signals = cursor.fetchall()

            for signal in signals:
                self.active_signals[signal['signal_id']] = dict(signal)

            cursor.close()
            conn.close()

        except Exception as e:
            logger.error(f"Error loading active signals: {e}")

    async def _process_tick(self, tick_data: Dict):
        """Process incoming tick and check for TP/SL hits"""
        symbol = tick_data.get('symbol')
        bid = tick_data.get('bid')
        ask = tick_data.get('ask')
        timestamp = tick_data.get('timestamp', int(time.time()))

        if not symbol or bid is None or ask is None:
            return

        # Cache tick
        self.tick_cache[symbol].append({
            'bid': bid,
            'ask': ask,
            'timestamp': timestamp
        })

        # Keep only last N ticks
        max_ticks = OUTCOME_TRACKING_CONFIG['tick_buffer_size']
        if len(self.tick_cache[symbol]) > max_ticks:
            self.tick_cache[symbol] = self.tick_cache[symbol][-max_ticks:]

        # Check active signals for this symbol
        signals_to_complete = []

        for signal_id, signal in list(self.active_signals.items()):
            if signal['symbol'] != symbol:
                continue

            direction = signal['direction']
            entry = signal['entry_price']
            sl = signal['sl_price']
            tp = signal['tp_price']

            outcome = None
            exit_price = None

            # Check for TP/SL hits based on direction
            if direction == 'BUY':
                # BUY: TP hit if bid >= TP, SL hit if bid <= SL
                if bid >= tp:
                    outcome = 'WIN'
                    exit_price = tp
                elif bid <= sl:
                    outcome = 'LOSS'
                    exit_price = sl

            elif direction == 'SELL':
                # SELL: TP hit if ask <= TP, SL hit if ask >= SL
                if ask <= tp:
                    outcome = 'WIN'
                    exit_price = tp
                elif ask >= sl:
                    outcome = 'LOSS'
                    exit_price = sl

            if outcome:
                signals_to_complete.append({
                    'signal_id': signal_id,
                    'outcome': outcome,
                    'exit_price': exit_price,
                    'exit_time': timestamp,
                    'signal': signal
                })

        # Batch update completed signals
        if signals_to_complete:
            await self._complete_signals(signals_to_complete)

    async def _complete_signals(self, completed_signals: List[Dict]):
        """Mark signals as complete and write outcomes"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()

            for item in completed_signals:
                signal_id = item['signal_id']
                outcome = item['outcome']
                exit_price = item['exit_price']
                exit_time = item['exit_time']
                signal = item['signal']

                # Calculate pips gained/lost
                entry = signal['entry_price']
                direction = signal['direction']

                # Simple pip calculation (should use pip_size from symbols table)
                if direction == 'BUY':
                    pips = (exit_price - entry) * 10000  # Rough estimate
                else:
                    pips = (entry - exit_price) * 10000

                pips = round(pips, 1)

                # Insert outcome record
                cursor.execute("""
                    INSERT INTO signal_outcomes
                    (signal_id, outcome, exit_price, exit_time, pips_result,
                     confidence, pattern_type, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (signal_id) DO UPDATE SET
                        outcome = EXCLUDED.outcome,
                        exit_price = EXCLUDED.exit_price,
                        exit_time = EXCLUDED.exit_time,
                        pips_result = EXCLUDED.pips_result
                """, (
                    signal_id, outcome, exit_price, exit_time, pips,
                    signal['confidence'], signal['pattern_type'],
                    int(time.time())
                ))

                # Update signal status
                cursor.execute("""
                    UPDATE signals
                    SET status = 'EXPIRED'
                    WHERE signal_id = %s
                """, (signal_id,))

                # Remove from active tracking
                if signal_id in self.active_signals:
                    del self.active_signals[signal_id]

                logger.info(
                    f"Signal {signal_id} completed: {outcome} "
                    f"({pips:+.1f} pips, exit={exit_price})"
                )

            conn.commit()
            cursor.close()
            conn.close()

        except Exception as e:
            logger.error(f"Error completing signals: {e}")

    async def _expire_old_signals(self):
        """Expire signals older than max age"""
        try:
            cutoff_time = int(
                (datetime.utcnow() -
                 timedelta(hours=OUTCOME_TRACKING_CONFIG['max_signal_age_hours'])
                ).timestamp()
            )

            expired = []
            for signal_id, signal in list(self.active_signals.items()):
                if signal['created_at'] < cutoff_time:
                    expired.append(signal_id)

            if expired:
                conn = self._get_db_connection()
                cursor = conn.cursor()

                for signal_id in expired:
                    cursor.execute("""
                        UPDATE signals
                        SET status = 'EXPIRED'
                        WHERE signal_id = %s
                    """, (signal_id,))

                    del self.active_signals[signal_id]
                    logger.info(f"Signal {signal_id} expired by age")

                conn.commit()
                cursor.close()
                conn.close()

        except Exception as e:
            logger.error(f"Error expiring old signals: {e}")

    async def run(self):
        """Main tracking loop"""
        await self.initialize()
        self.running = True

        logger.info("Outcome Tracker running...")

        # Periodic tasks
        last_reload = time.time()
        last_expire_check = time.time()

        while self.running:
            try:
                # Non-blocking receive with timeout
                if await self.subscriber.poll(timeout=1000):
                    message = await self.subscriber.recv_string()

                    # Parse market data
                    if message.startswith("TICK "):
                        try:
                            tick_json = message[5:]
                            tick_data = json.loads(tick_json)
                            await self._process_tick(tick_data)
                        except json.JSONDecodeError:
                            pass

                # Reload active signals every 5 minutes
                if time.time() - last_reload > 300:
                    await self._load_active_signals()
                    last_reload = time.time()

                # Expire old signals every hour
                if time.time() - last_expire_check > 3600:
                    await self._expire_old_signals()
                    last_expire_check = time.time()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in outcome tracker loop: {e}")
                await asyncio.sleep(5)

        logger.info("Outcome Tracker stopped")

    async def stop(self):
        """Stop the tracker"""
        self.running = False
        if self.subscriber:
            self.subscriber.close()


# Job entry point
async def run_outcome_tracker():
    """Run outcome tracker job"""
    tracker = OutcomeTracker()
    await tracker.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_outcome_tracker())
