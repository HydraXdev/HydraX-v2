#!/usr/bin/env python3
"""
PostgreSQL Adapter for Elite Guard v7.0
Allows Elite Guard to write signals to PostgreSQL v2 database
while maintaining compatibility with existing code
"""

import os
from datetime import datetime
from typing import Dict, Optional

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    print("⚠️ psycopg2 not available - PostgreSQL adapter disabled")


class PostgresAdapter:
    """Adapter to write Elite Guard signals to PostgreSQL v2"""

    def __init__(self):
        self.conn = None
        self.db_url = os.getenv(
            "DATABASE_URL",
            "postgresql://bitten_admin:bitten_secure_2025@localhost:5433/bitten_v2"
        )
        self.enabled = POSTGRES_AVAILABLE

        if self.enabled:
            try:
                self.connect()
                print(f"✅ PostgreSQL Adapter: Connected to {self.db_url.split('@')[1]}")
            except Exception as e:
                print(f"⚠️ PostgreSQL Adapter: Failed to connect - {e}")
                self.enabled = False

    def connect(self):
        """Establish PostgreSQL connection"""
        if not POSTGRES_AVAILABLE:
            return

        try:
            self.conn = psycopg2.connect(self.db_url)
            self.conn.autocommit = True
        except Exception as e:
            print(f"❌ PostgreSQL connection error: {e}")
            raise

    def reconnect_if_needed(self):
        """Check connection and reconnect if needed"""
        if not self.enabled or not POSTGRES_AVAILABLE:
            return False

        try:
            if self.conn is None or self.conn.closed:
                self.connect()
            else:
                # Test connection with simple query
                with self.conn.cursor() as cur:
                    cur.execute("SELECT 1")
            return True
        except Exception:
            try:
                self.connect()
                return True
            except Exception as e:
                print(f"⚠️ PostgreSQL reconnect failed: {e}")
                return False

    def insert_signal(self, signal: Dict) -> bool:
        """
        Insert signal into PostgreSQL v2 signals table

        Maps Elite Guard signal format to PostgreSQL schema:
        - signal_id TEXT PRIMARY KEY
        - symbol TEXT NOT NULL
        - direction TEXT NOT NULL ('BUY' or 'SELL')
        - entry_price REAL NOT NULL
        - sl_pips REAL NOT NULL
        - tp_pips REAL NOT NULL
        - confidence REAL NOT NULL
        - citadel_score REAL (nullable)
        - pattern_type TEXT NOT NULL
        - signal_type TEXT (nullable)
        - session TEXT (nullable)
        - created_at TIMESTAMP (default: now())
        - expires_at TIMESTAMP (nullable)
        - status TEXT (default: 'ACTIVE')
        """
        if not self.enabled:
            return False

        if not self.reconnect_if_needed():
            return False

        try:
            # Extract required fields
            signal_id = signal.get("signal_id")
            symbol = signal.get("symbol")
            direction = signal.get("direction")
            entry_price = signal.get("entry_price") or signal.get("entry")

            # Calculate pips from price levels if needed
            stop_pips = signal.get("stop_pips")
            target_pips = signal.get("target_pips")

            confidence = signal.get("confidence", 0)
            pattern_type = signal.get("pattern_type") or signal.get("pattern")

            # Validate required fields
            if not all([signal_id, symbol, direction, entry_price, pattern_type]):
                print(f"⚠️ PostgreSQL: Missing required fields for {signal_id}")
                return False

            if stop_pips is None or target_pips is None:
                print(f"⚠️ PostgreSQL: Missing stop_pips or target_pips for {signal_id}")
                return False

            # Optional fields
            citadel_score = signal.get("citadel_score") or signal.get("quality_score")
            signal_type = signal.get("signal_type")
            session = signal.get("session")

            # Handle timestamps
            created_at = None
            expires_at = None

            if "timestamp" in signal:
                ts = signal["timestamp"]
                if isinstance(ts, (int, float)):
                    created_at = datetime.fromtimestamp(ts)

            if "expires_at" in signal:
                exp = signal["expires_at"]
                if isinstance(exp, (int, float)):
                    expires_at = datetime.fromtimestamp(exp)

            # Insert into PostgreSQL
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO signals (
                        signal_id, symbol, direction, entry_price,
                        sl_pips, tp_pips, confidence, citadel_score,
                        pattern_type, signal_type, session,
                        created_at, expires_at, status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (signal_id) DO UPDATE SET
                        confidence = EXCLUDED.confidence,
                        citadel_score = EXCLUDED.citadel_score,
                        status = EXCLUDED.status
                    """,
                    (
                        signal_id, symbol, direction, entry_price,
                        stop_pips, target_pips, confidence, citadel_score,
                        pattern_type, signal_type, session,
                        created_at, expires_at, 'ACTIVE'
                    )
                )

            print(f"   ✅ PostgreSQL v2: Signal {signal_id} written to database")
            return True

        except Exception as e:
            print(f"   ❌ PostgreSQL v2: Failed to insert signal - {e}")
            import traceback
            traceback.print_exc()
            return False

    def close(self):
        """Close PostgreSQL connection"""
        if self.conn and not self.conn.closed:
            self.conn.close()
            print("✅ PostgreSQL Adapter: Connection closed")


# Global singleton instance
_postgres_adapter = None

def get_postgres_adapter() -> PostgresAdapter:
    """Get or create PostgreSQL adapter singleton"""
    global _postgres_adapter
    if _postgres_adapter is None:
        _postgres_adapter = PostgresAdapter()
    return _postgres_adapter


def publish_signal_to_postgres(signal: Dict) -> bool:
    """
    Convenience function to publish signal to PostgreSQL v2
    Can be called from Elite Guard without managing connection
    """
    adapter = get_postgres_adapter()
    return adapter.insert_signal(signal)


if __name__ == "__main__":
    # Test the adapter
    print("Testing PostgreSQL Adapter...")

    test_signal = {
        "signal_id": "TEST_POSTGRES_ADAPTER_1760020000",
        "symbol": "EURUSD",
        "direction": "BUY",
        "entry_price": 1.10500,
        "stop_pips": 15.0,
        "target_pips": 30.0,
        "confidence": 85.5,
        "citadel_score": 7.2,
        "pattern_type": "VCB_BREAKOUT",
        "signal_type": "RAPID_ASSAULT",
        "session": "LONDON",
        "timestamp": 1760020000,
        "expires_at": 1760021800
    }

    success = publish_signal_to_postgres(test_signal)

    if success:
        print("✅ Test signal inserted successfully!")

        # Verify it's in the database
        adapter = get_postgres_adapter()
        try:
            with adapter.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM signals WHERE signal_id = %s", (test_signal["signal_id"],))
                result = cur.fetchone()
                if result:
                    print(f"✅ Verified in database: {dict(result)}")
                else:
                    print("⚠️ Signal not found in database")
        except Exception as e:
            print(f"❌ Verification failed: {e}")
    else:
        print("❌ Test signal insertion failed")

    adapter.close()
