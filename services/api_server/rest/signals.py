"""
Signal API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Dict
import time
import json
import sqlite3
import logging

from ..models import get_db, Signal, SignalResponse

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# 🚨 FIREBASE UID RESOLVER - ALL USER IDENTIFICATION MUST USE FIREBASE UIDS 🚨
# ═══════════════════════════════════════════════════════════════════════════
# ✅ FIREBASE UID STANDARD - ALL USER IDENTIFICATION USES FIREBASE UIDs
# Telegram IDs have been completely purged from the system (October 2025)
# ═══════════════════════════════════════════════════════════════════════════

router = APIRouter(prefix="/api/signals", tags=["signals"])


@router.get("", response_model=List[SignalResponse])
async def list_signals(
    limit: int = 50,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """List active signals"""
    query = db.query(Signal)

    if active_only:
        current_time = int(time.time())
        query = query.filter(Signal.expires_at > current_time)

    signals = query.order_by(Signal.created_at.desc()).limit(limit).all()

    return [
        SignalResponse(
            signal_id=s.signal_id,
            symbol=s.symbol,
            direction=s.direction,
            entry=s.entry or 0,
            sl=s.sl or 0,
            tp=s.tp or 0,
            confidence=s.confidence or 0,
            pattern_type=s.pattern_type,
            created_at=s.created_at or 0,
            expires_at=s.expires_at or 0
        )
        for s in signals
    ]


@router.get("/{signal_id}", response_model=SignalResponse)
async def get_signal(signal_id: str, db: Session = Depends(get_db)):
    """Get signal by ID"""
    signal = db.query(Signal).filter(Signal.signal_id == signal_id).first()

    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    # Fix NULL entry handling: try entry_price first, then entry, then parse from payload_json
    entry_value = signal.entry or signal.entry_price or 0

    # If still 0/NULL, try to get from payload_json
    if not entry_value and signal.payload_json:
        try:
            payload = json.loads(signal.payload_json)
            entry_value = payload.get("entry_price", payload.get("entry", 0))
        except:
            pass

    return SignalResponse(
        signal_id=signal.signal_id,
        symbol=signal.symbol,
        direction=signal.direction,
        entry=entry_value,
        sl=signal.sl or 0,
        tp=signal.tp or 0,
        confidence=signal.confidence or 0,
        pattern_type=signal.pattern_type,
        created_at=signal.created_at or 0,
        expires_at=signal.expires_at or 0
    )


@router.post("")
async def create_signal(request: Request, db: Session = Depends(get_db)):
    """
    Receive signal from Elite Guard and process for auto-fire eligibility.

    Mirrors logic from webapp_server_optimized.py lines 446-700:
    1. Store signal in database
    2. Check for auto-fire eligibility using FireValidator
    3. Execute auto-fire if approved
    4. Return success/failure response
    """
    try:
        # Parse incoming signal data
        signal_data = await request.json()

        if not signal_data:
            raise HTTPException(status_code=400, detail="No signal data provided")

        logger.info(
            f"📨 Received signal: {signal_data.get('signal_id')} "
            f"for {signal_data.get('symbol')} @ {signal_data.get('confidence', 0)}%"
        )

        # Extract signal fields (support both formats)
        signal_id = signal_data.get("signal_id", "")
        symbol = signal_data.get("symbol", signal_data.get("pair", ""))
        direction = signal_data.get("direction", "")

        # CRITICAL: Try multiple field names for entry_price
        entry_price = (
            signal_data.get("entry_price") or
            signal_data.get("entry") or
            signal_data.get("entry_level") or
            0
        )

        # Convert to float if string
        if entry_price and isinstance(entry_price, str):
            entry_price = float(entry_price)

        logger.info(f"🔍 Entry price extracted: {entry_price} from signal {signal_id}")

        stop_loss = float(signal_data.get("stop_loss", 0)) or float(signal_data.get("sl", 0))
        take_profit = float(signal_data.get("take_profit", 0)) or float(signal_data.get("tp", 0))
        confidence = signal_data.get("confidence", 0)
        pattern_type = signal_data.get("pattern_type", "")
        created_at = int(time.time())

        # Extract pips values for tracker compatibility
        stop_pips = signal_data.get("stop_pips", 0)
        target_pips = signal_data.get("target_pips", 0)

        # Store signal in database (bitten.db)
        try:
            bitten_db_path = "/root/HydraX-v2/bitten.db"
            with sqlite3.connect(bitten_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO signals
                    (signal_id, symbol, direction, entry, sl, tp, confidence, pattern_type,
                     created_at, payload_json, entry_price, stop_pips, target_pips)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        signal_id,
                        symbol,
                        direction,
                        entry_price,
                        stop_loss,
                        take_profit,
                        confidence,
                        pattern_type,
                        created_at,
                        json.dumps(signal_data),
                        entry_price,  # Also populate entry_price column for tracker
                        stop_pips,    # Populate stop_pips for tracker
                        target_pips,  # Populate target_pips for tracker
                    ),
                )
                conn.commit()
                logger.info(f"📊 Signal {signal_id} stored in database with tracker fields")

                # CREATE MISSION RECORD for UI display
                try:
                    # Generate mission briefing payload
                    mission_payload = {
                        "signal_id": signal_id,
                        "symbol": symbol,
                        "direction": direction,
                        "entry_price": entry_price,
                        "sl": stop_loss,
                        "tp": take_profit,
                        "stop_pips": stop_pips,
                        "target_pips": target_pips,
                        "confidence": confidence,
                        "pattern_type": pattern_type,
                        "created_at": created_at
                    }

                    mission_id = f"{signal_id}_MISSION"
                    expires_at = created_at + 7200  # 2 hours expiry

                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO missions
                        (mission_id, signal_id, payload_json, status, expires_at, created_at)
                        VALUES (?, ?, ?, 'ACTIVE', ?, ?)
                        """,
                        (mission_id, signal_id, json.dumps(mission_payload), expires_at, created_at)
                    )
                    conn.commit()
                    logger.info(f"🎯 Mission {mission_id} created for signal {signal_id}")
                except Exception as mission_error:
                    logger.warning(f"⚠️ Failed to create mission: {mission_error}")

                # FIREBASE SYNC: Write to Firestore for alerts page
                try:
                    import firebase_admin
                    from firebase_admin import firestore

                    # Initialize Firebase if not already done
                    try:
                        firebase_admin.get_app()
                    except ValueError:
                        from firebase_admin import credentials
                        cred = credentials.Certificate('/root/bitten-firebase-sa.json')
                        firebase_admin.initialize_app(cred)

                    firestore_db = firestore.client()

                    # Calculate SL/TP price levels from entry and pips
                    pip_multiplier = 100 if 'JPY' in symbol else 10000
                    sl_price = entry_price - (stop_pips / pip_multiplier) if direction == 'BUY' else entry_price + (stop_pips / pip_multiplier)
                    tp_price = entry_price + (target_pips / pip_multiplier) if direction == 'BUY' else entry_price - (target_pips / pip_multiplier)

                    # Determine signal_type for classification (webapp expects this)
                    signal_type_value = signal_data.get('signal_type', 'RAPID_ASSAULT')  # Default to rapid if not specified

                    # Write to signals collection (webapp reads from this)
                    firestore_db.collection('signals').document(signal_id).set({
                        'signal_id': signal_id,
                        'symbol': symbol,
                        'pair': symbol,  # Webapp checks both
                        'direction': direction,
                        'entry': entry_price,
                        'sl': sl_price,
                        'tp': tp_price,
                        'stop_pips': stop_pips,
                        'target_pips': target_pips,
                        'confidence': confidence,
                        'pattern_type': pattern_type,
                        'pattern': pattern_type,  # Webapp checks both
                        'signal_type': signal_type_value,  # For classification (sniper/rapid)
                        'session': signal_data.get('session', 'UNKNOWN'),
                        'timeframe': signal_data.get('timeframe', '5-MIN'),
                        'status': 'new',
                        'created_at': created_at,
                        'timestamp': firestore.SERVER_TIMESTAMP
                    })
                    logger.info(f"📤 Signal {signal_id} synced to Firebase (signals collection)")
                except Exception as firebase_error:
                    logger.warning(f"⚠️ Failed to sync to Firebase: {firebase_error}")

        except Exception as db_error:
            logger.warning(f"⚠️ Failed to store signal in database: {db_error}")

        # AUTO-FIRE SYSTEM: Check for instant execution
        auto_fire_results = []
        signal_confidence = float(confidence)

        try:
            # Import FireValidator for rule validation
            import sys
            sys.path.insert(0, '/root/HydraX-v2')
            from src.bitten_core.fire_validator import fire_validator
            from src.bitten_core.constants import get_pip_size, pips_from_price_distance, verify_pip_conversion

            # Query bitten.db for COMMANDER users with AUTO mode enabled
            fire_modes_db_path = "/root/HydraX-v2/bitten.db"
            with sqlite3.connect(fire_modes_db_path) as fire_conn:
                fire_cursor = fire_conn.cursor()

                # Get COMMANDER tier users with AUTO mode in confidence range
                fire_cursor.execute(
                    """
                    SELECT user_id, COALESCE(max_concurrent_positions, max_auto_slots, 10) as max_slots, 'COMMANDER',
                           auto_fire_min_confidence, auto_fire_max_confidence
                    FROM user_fire_modes
                    WHERE current_mode = 'AUTO'
                    AND auto_fire_enabled = 1
                    AND ? >= auto_fire_min_confidence
                    AND ? <= auto_fire_max_confidence
                    """,
                    (signal_confidence, signal_confidence),
                )
                auto_candidates = fire_cursor.fetchall()

            logger.info(f"🎯 AUTO FIRE: Found {len(auto_candidates)} COMMANDER candidates")

            # Validate each candidate with FireValidator
            for user_id, max_slots, user_tier, min_conf, max_conf in auto_candidates:
                # ✅ user_fire_modes now stores Firebase UIDs directly (Telegram IDs purged Oct 2025)
                logger.info(f"🎯 AUTO FIRE: Evaluating user {user_id} (tier: {user_tier})")

                try:
                    # Calculate SL/TP in pips using UNIFIED pip size system
                    # CRITICAL FIX: If SL/TP prices are 0, use stop_pips/target_pips directly
                    if stop_loss == 0 or take_profit == 0:
                        # Elite Guard provides pips instead of absolute prices
                        sl_pips = float(signal_data.get("stop_pips", 15))
                        tp_pips = float(signal_data.get("target_pips", 20))
                        logger.info(f"   Using pips from signal: SL={sl_pips}, TP={tp_pips}")
                    else:
                        # Calculate from absolute prices using UNIFIED pip size
                        sl_pips = pips_from_price_distance(entry_price, stop_loss, symbol)
                        tp_pips = pips_from_price_distance(entry_price, take_profit, symbol)
                        logger.info(f"   Calculated pips from prices (unified): SL={sl_pips:.1f}, TP={tp_pips:.1f}")

                        # ✅ VERIFICATION: Ensure pip conversion is accurate
                        try:
                            verify_pip_conversion(entry_price, stop_loss, sl_pips, symbol, tolerance=1.0)
                            logger.info(f"   ✅ Pip conversion verified for {symbol}")
                        except AssertionError as e:
                            logger.warning(f"   ⚠️ Pip conversion check: {e}")

                    # Validate with FireValidator
                    # ✅ Use Firebase UID for validation

                    # Get user's risk setting, risk mode, and trailing stop setting
                    user_risk_pct = 2.0  # Default fallback
                    risk_mode = "MODERATE"  # Default fallback
                    trailing_enabled = False  # Default fallback

                    # Read user's settings from database
                    with sqlite3.connect(bitten_db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT risk_per_trade_pct, trailing_enabled FROM user_fire_modes WHERE user_id = ?",
                            (user_id,)
                        )
                        result = cursor.fetchone()
                        if result:
                            user_risk_pct = result[0]
                            trailing_enabled = bool(result[1]) if result[1] is not None else False

                    # Read risk mode from Firebase (MODERATE = 50%, AGGRESSIVE = 100%)
                    try:
                        import firebase_admin
                        from firebase_admin import firestore

                        # Initialize Firebase if not already done
                        try:
                            firebase_admin.get_app()
                        except ValueError:
                            import os
                            cred_path = '/root/bitten-firebase-sa.json'
                            if os.path.exists(cred_path):
                                from firebase_admin import credentials
                                cred = credentials.Certificate(cred_path)
                                firebase_admin.initialize_app(cred)

                        # Get risk mode and engine settings from Firebase
                        firestore_db = firestore.client()
                        autofire_doc = firestore_db.collection('autofire_settings').document(user_id).get()
                        if autofire_doc.exists:
                            autofire_settings = autofire_doc.to_dict()
                            risk_mode = autofire_settings.get('riskMode', 'MODERATE')

                            # Check engine filter: skip if this engine is disabled for user
                            engines = autofire_settings.get('engines', {'eliteGuard': True, 'pulse': True, 'apex': True})
                            signal_source = signal_id.split('_')[0].lower()  # Extract ELITE/PULSE/APEX from signal_id

                            # Map signal sources to engine keys
                            if signal_source == 'elite':
                                if not engines.get('eliteGuard', True):
                                    logger.info(f"⏭️ SKIPPING: Elite Guard disabled for user {user_id}")
                                    continue
                            elif signal_source == 'pulse':
                                if not engines.get('pulse', True):
                                    logger.info(f"⏭️ SKIPPING: Pulse disabled for user {user_id}")
                                    continue
                            elif signal_source == 'apex':
                                if not engines.get('apex', True):
                                    logger.info(f"⏭️ SKIPPING: Apex Sentinel disabled for user {user_id}")
                                    continue
                    except Exception as e:
                        logger.warning(f"Could not read Firebase risk mode for {user_id}: {e}")

                    # Apply risk mode multiplier
                    if risk_mode == "MODERATE":
                        auto_risk_pct = user_risk_pct * 0.5  # 50% of manual risk
                        logger.info(f"🛡️ MODERATE mode: Using {auto_risk_pct}% (50% of {user_risk_pct}% manual risk)")
                    else:  # AGGRESSIVE
                        auto_risk_pct = user_risk_pct  # 100% of manual risk
                        logger.info(f"⚡ AGGRESSIVE mode: Using {auto_risk_pct}% (100% of {user_risk_pct}% manual risk)")

                    client_request = {
                        "symbol": symbol,
                        "direction": direction.upper(),
                        "sl_pips": sl_pips,
                        "tp_pips": tp_pips,
                        "risk_pct": auto_risk_pct,
                        "fire_mode": "AUTO"
                    }

                    validation = fire_validator.validate_fire_request(
                        user_id=str(user_id),  # ✅ FIREBASE UID (Telegram IDs purged Oct 2025)
                        signal_id=signal_id,
                        client_request=client_request
                    )

                    if not validation["allowed"]:
                        logger.info(f"🚫 AUTO FIRE BLOCKED for user {user_id}: {validation['reason']}")
                        continue

                    logger.info(f"✅ AUTO FIRE APPROVED for user {user_id}: {validation['enforced']}")

                    # Execute fire command
                    from enqueue_fire import create_fire_command, enqueue_fire

                    # Get user's EA target_uuid from bitten.db
                    with sqlite3.connect(bitten_db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            """
                            SELECT target_uuid FROM ea_instances
                            WHERE user_id = ?
                            AND (strftime('%s','now') - last_seen) <= 120
                            ORDER BY last_seen DESC LIMIT 1
                            """,
                            (str(user_id),)
                        )
                        ea_row = cursor.fetchone()

                    if not ea_row:
                        logger.warning(f"⚠️ No fresh EA connection for user {user_id}")
                        continue

                    target_uuid = ea_row[0]

                    # Create fire command with validated parameters
                    fire_cmd = create_fire_command(
                        mission_id=signal_id,
                        user_id=str(user_id),
                        symbol=symbol,
                        direction=direction.upper(),
                        entry=entry_price,
                        sl=stop_loss,
                        tp=take_profit,
                        lot=validation["enforced"]["lot_size"],
                        enable_trailing=trailing_enabled  # ✅ Pass user's trailing setting
                    )

                    if fire_cmd:
                        fire_cmd["target_uuid"] = target_uuid

                        # CRITICAL: Create fire record in database BEFORE enqueuing
                        # This allows confirmation handler to update it with ticket/price
                        # ✅ SET fire_mode='AUTO' to track this as an auto-fired position
                        with sqlite3.connect(bitten_db_path) as fire_conn:
                            fire_cursor = fire_conn.cursor()
                            fire_cursor.execute(
                                """
                                INSERT OR REPLACE INTO fires
                                (fire_id, mission_id, user_id, symbol, direction, sl, tp, lot,
                                 status, fire_mode, created_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'SENT', 'AUTO', ?)
                                """,
                                (signal_id, signal_id, str(user_id), symbol, direction.upper(),
                                 stop_loss, take_profit, validation["enforced"]["lot_size"],
                                 int(time.time()))
                            )
                            fire_conn.commit()

                        enqueue_fire(fire_cmd)
                        auto_fire_results.append({
                            "user_id": str(user_id),
                            "status": "ENQUEUED",
                            "lot_size": validation["enforced"]["lot_size"]
                        })
                        logger.info(f"🔥 AUTO FIRE EXECUTED for user {user_id}: {signal_id}")

                except Exception as user_error:
                    logger.error(f"❌ AUTO FIRE SYSTEM ERROR: {user_error}")
                    continue

        except Exception as auto_fire_error:
            logger.error(f"❌ AUTO FIRE SYSTEM ERROR: {auto_fire_error}")

        # Return success response
        return {
            "success": True,
            "signal_id": signal_id,
            "symbol": symbol,
            "confidence": confidence,
            "stored": True,
            "auto_fire_count": len(auto_fire_results),
            "auto_fire_results": auto_fire_results
        }

    except Exception as e:
        logger.error(f"❌ Signal processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Signal processing failed: {str(e)}")
