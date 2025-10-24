#!/usr/bin/env python3
"""
Firebase Bridge v2.0 - PostgreSQL Integration
Reads signals from PostgreSQL v2 database and writes to Firebase Firestore
Uses PostgreSQL LISTEN/NOTIFY for real-time updates
"""
import os
import sys
import time
import signal
import json
import psycopg2
import psycopg2.extensions
from datetime import datetime
from google.cloud import firestore

# Initialize Firebase
db = firestore.Client(project="bitten-0420")

print("🔥 Firebase Bridge v2.0 Started")
print("=" * 60)
print("Project: bitten-0420")
print("Firestore: Connected")
print("Database: PostgreSQL v2 (bitten_v2)")
print("=" * 60)

# PostgreSQL connection
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://bitten_admin:bitten_secure_2025@localhost:5433/bitten_v2"
)

conn = psycopg2.connect(DATABASE_URL)
conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
cursor = conn.cursor()

print("✅ Connected to PostgreSQL v2")

# Track last processed signal to avoid duplicates
last_signal_id = None
processed_signals = set()

# Graceful shutdown
running = True

def signal_handler(sig, frame):
    global running
    print("\n🛑 Shutdown signal received, closing...")
    running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def write_to_firestore(signal_row):
    """Write signal from PostgreSQL row to Firebase Firestore"""
    try:
        signal_id = signal_row[0]  # Column 0: signal_id

        # Skip if already processed
        if signal_id in processed_signals:
            return False

        # Extract fields from PostgreSQL row
        # Columns: signal_id, symbol, direction, entry_price, sl_pips, tp_pips,
        #          confidence, citadel_score, pattern_type, signal_type, session,
        #          created_at, expires_at, status

        symbol = signal_row[1]
        direction = signal_row[2]
        entry_price = float(signal_row[3]) if signal_row[3] else 0
        sl_pips = float(signal_row[4]) if signal_row[4] else 0
        tp_pips = float(signal_row[5]) if signal_row[5] else 0
        confidence = float(signal_row[6]) if signal_row[6] else 0
        citadel_score = float(signal_row[7]) if signal_row[7] else 0
        pattern_type = signal_row[8]
        signal_type = signal_row[9]
        session = signal_row[10]
        created_at = signal_row[11]

        # Calculate SL/TP price levels from pips
        pip_size = 0.01 if "JPY" in symbol else (0.1 if symbol == "XAUUSD" else 0.0001)

        if direction == "BUY":
            sl = entry_price - (sl_pips * pip_size)
            tp = entry_price + (tp_pips * pip_size)
        else:  # SELL
            sl = entry_price + (sl_pips * pip_size)
            tp = entry_price - (tp_pips * pip_size)

        # Build Firestore document
        doc = {
            # Core fields
            'pattern': pattern_type or '',
            'pair': symbol,
            'timeframe': 'M15',
            'session': session or 'LONDON',
            'timestamp': firestore.SERVER_TIMESTAMP,
            'confidence': confidence,

            # Trade levels
            'entry': entry_price,
            'tp': round(tp, 5),
            'sl': round(sl, 5),

            # Metadata
            'status': 'new',
            'priority': 'high' if confidence >= 85 else 'medium',
            'direction': direction,
            'signal_mode': signal_type or ('SNIPER' if confidence >= 85 else 'RAPID'),
            'citadel_score': citadel_score,

            # Additional fields
            'sl_pips': sl_pips,
            'tp_pips': tp_pips,
            'created_at_pg': created_at.isoformat() if created_at else None,
        }

        # Remove empty values
        doc = {k: v for k, v in doc.items() if v not in [None, '', 0]}

        # Write to Firestore (use signal_id as document ID)
        db.collection('signals').document(signal_id).set(doc)

        # Mark as processed
        processed_signals.add(signal_id)

        print(f"✅ Firebase: {signal_id} ({symbol} {direction} @ {confidence:.1f}%)")
        return True

    except Exception as e:
        print(f"❌ Firestore write failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def poll_new_signals():
    """Poll PostgreSQL for new signals"""
    global last_signal_id

    try:
        # Query for signals created in last 10 seconds (to catch startup signals)
        query = """
            SELECT signal_id, symbol, direction, entry_price, sl_pips, tp_pips,
                   confidence, citadel_score, pattern_type, signal_type, session,
                   created_at, expires_at, status
            FROM signals
            WHERE created_at >= NOW() - INTERVAL '10 seconds'
            OR created_at IS NULL
            ORDER BY created_at DESC NULLS FIRST
            LIMIT 100
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        for row in rows:
            write_to_firestore(row)

    except Exception as e:
        print(f"⚠️  Poll error: {e}")

# Setup PostgreSQL NOTIFY listener for real-time updates (optional advanced feature)
try:
    # Create trigger for new signal notifications (if not exists)
    cursor.execute("""
        CREATE OR REPLACE FUNCTION notify_new_signal()
        RETURNS trigger AS $$
        BEGIN
            PERFORM pg_notify('new_signal', NEW.signal_id);
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    cursor.execute("""
        DROP TRIGGER IF EXISTS signal_insert_trigger ON signals;
        CREATE TRIGGER signal_insert_trigger
        AFTER INSERT ON signals
        FOR EACH ROW
        EXECUTE FUNCTION notify_new_signal();
    """)

    cursor.execute("LISTEN new_signal;")
    print("✅ PostgreSQL LISTEN/NOTIFY configured for real-time updates")
    use_notify = True
except Exception as e:
    print(f"⚠️  LISTEN/NOTIFY not available: {e}")
    use_notify = False

# Main loop
signal_count = 0
print("\n🎯 Monitoring PostgreSQL for new signals...\n")

# Initial poll to catch any existing signals
poll_new_signals()

last_poll_time = time.time()
POLL_INTERVAL = 5  # Poll every 5 seconds as fallback

while running:
    try:
        if use_notify:
            # Wait for notification with timeout
            if conn.poll() == psycopg2.extensions.POLL_OK:
                conn.poll()
                while conn.notifies:
                    notify = conn.notifies.pop(0)
                    signal_id = notify.payload

                    # Fetch the signal from database
                    cursor.execute("""
                        SELECT signal_id, symbol, direction, entry_price, sl_pips, tp_pips,
                               confidence, citadel_score, pattern_type, signal_type, session,
                               created_at, expires_at, status
                        FROM signals
                        WHERE signal_id = %s
                    """, (signal_id,))

                    row = cursor.fetchone()
                    if row:
                        if write_to_firestore(row):
                            signal_count += 1

        # Fallback polling regardless of NOTIFY
        now = time.time()
        if now - last_poll_time >= POLL_INTERVAL:
            poll_new_signals()
            last_poll_time = now

        time.sleep(1)  # Prevent tight loop

    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"❌ Error in main loop: {e}")
        import traceback
        traceback.print_exc()
        time.sleep(5)  # Prevent tight error loop

        # Try to reconnect
        try:
            conn = psycopg2.connect(DATABASE_URL)
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            if use_notify:
                cursor.execute("LISTEN new_signal;")
            print("✅ Reconnected to PostgreSQL")
        except Exception as reconnect_error:
            print(f"❌ Reconnection failed: {reconnect_error}")

# Cleanup
print(f"\n✅ Shutting down... (processed {signal_count} signals)")
if cursor:
    cursor.close()
if conn:
    conn.close()
print("👋 Firebase Bridge v2.0 stopped")
