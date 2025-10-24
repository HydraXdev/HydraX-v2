#!/usr/bin/env python3
"""
Fire Executor Module
Handles fire command creation and execution via IPC queue
"""

import json
import logging
import psycopg2
import psycopg2.extras
import time
import zmq
from collections import OrderedDict
from datetime import datetime
from typing import Dict, Optional, Tuple
from config import config
from models import FireRequest, FireStatusEnum, DirectionEnum
from risk_calculator import risk_calculator
from bitmode_manager import bitmode_manager

logger = logging.getLogger(__name__)


class FireExecutor:
    """Executes fire commands via IPC queue"""

    def __init__(self):
        self.config = config
        self.context = zmq.Context()
        self.ipc_socket = None
        self._connect_ipc()

    def _connect_ipc(self):
        """Connect to IPC queue"""
        try:
            self.ipc_socket = self.context.socket(zmq.PUSH)
            self.ipc_socket.connect(self.config.IPC_QUEUE)
            logger.info(f"Connected to IPC queue: {self.config.IPC_QUEUE}")
        except Exception as e:
            logger.error(f"Failed to connect to IPC queue: {e}")
            raise

    def execute_fire(self, request: FireRequest) -> Tuple[str, FireStatusEnum, str]:
        """
        Execute fire command

        Args:
            request: Fire request object

        Returns:
            Tuple of (fire_id, status, message)
        """
        try:
            # Get user account balance
            account_balance = self._get_user_balance(request.user_id)
            if account_balance is None:
                return "", FireStatusEnum.REJECTED, "User account not found"

            # Calculate position size
            lot_size, calc_details = risk_calculator.calculate_position_size(
                symbol=request.symbol,
                account_balance=account_balance,
                entry_price=request.entry_price,
                sl_price=request.sl_price,
                direction=request.direction.value,
                fire_mode=request.fire_mode.value
            )

            # Validate risk limits
            sl_pips = calc_details.get("sl_pips", 20)
            pip_value = config.get_pip_value(request.symbol)
            is_valid, error_msg = risk_calculator.validate_risk_limits(
                account_balance, lot_size, sl_pips, pip_value
            )

            if not is_valid:
                return "", FireStatusEnum.REJECTED, error_msg

            # Get target UUID
            target_uuid = request.target_uuid
            if not target_uuid:
                target_uuid = self._get_user_target_uuid(request.user_id)
                if not target_uuid:
                    return "", FireStatusEnum.REJECTED, "No EA connected for user"

            # Check if BITMODE enabled
            bitmode_enabled = request.enable_bitmode and bitmode_manager.is_bitmode_enabled(request.user_id)

            # Create fire command
            fire_id = request.signal_id  # Use signal_id as fire_id
            fire_command = self._create_fire_command(
                fire_id=fire_id,
                target_uuid=target_uuid,
                symbol=request.symbol,
                direction=request.direction.value,
                entry=request.entry_price,
                sl=request.sl_price,
                tp=request.tp_price,
                lot=lot_size,
                bitmode_enabled=bitmode_enabled
            )

            # Store fire in database
            self._store_fire_record(
                fire_id=fire_id,
                user_id=request.user_id,
                signal_id=request.signal_id,
                target_uuid=target_uuid,
                symbol=request.symbol,
                direction=request.direction.value,
                sl_price=request.sl_price,
                tp_price=request.tp_price,
                fire_command=fire_command,
                lot_size=lot_size,
                fire_mode=request.fire_mode.value,
                bitmode_enabled=bitmode_enabled
            )

            # Send to IPC queue
            self._send_to_queue(fire_command)

            logger.info(
                f"Fire executed: {fire_id} | {request.symbol} {request.direction.value} | "
                f"Lot: {lot_size:.2f} | Mode: {request.fire_mode.value} | "
                f"BITMODE: {bitmode_enabled}"
            )

            return fire_id, FireStatusEnum.QUEUED, "Fire command queued successfully"

        except Exception as e:
            logger.error(f"Fire execution error: {e}")
            return "", FireStatusEnum.FAILED, str(e)

    def _create_fire_command(
        self,
        fire_id: str,
        target_uuid: str,
        symbol: str,
        direction: str,
        entry: float,
        sl: float,
        tp: float,
        lot: float,
        bitmode_enabled: bool = False
    ) -> Dict:
        """
        Create fire command with EXACT format required by EA v2.07

        CRITICAL: Field order matters, direction must be uppercase
        """
        # Ensure direction is uppercase
        direction = direction.upper()

        # Round lot size to 2 decimal places
        lot = round(lot, 2)

        # Get symbol decimals for price rounding
        spec = config.get_symbol_spec(symbol)
        decimals = spec["digits"]

        # Round prices
        if symbol in ["XAUUSD", "XAGUSD"]:
            sl = round(sl, decimals)
            tp = round(tp, decimals)
        else:
            sl = round(sl, decimals)
            tp = round(tp, decimals)

        # Build fire command with EXACT field order
        fire_cmd = OrderedDict([
            ("type", "fire"),
            ("target_uuid", target_uuid),
            ("fire_id", fire_id),
            ("symbol", symbol),
            ("direction", direction),
            ("entry", 0),  # 0 = market order
            ("sl", sl),
            ("tp", tp),
            ("lot", lot)
        ])

        # Add BITMODE hybrid configuration if enabled
        if bitmode_enabled:
            hybrid_config = bitmode_manager.create_hybrid_json(symbol)
            fire_cmd["hybrid"] = hybrid_config

        # Convert OrderedDict to regular dict for JSON serialization
        return dict(fire_cmd)

    def _send_to_queue(self, fire_command: Dict):
        """Send fire command to IPC queue"""
        try:
            command_json = json.dumps(fire_command)
            self.ipc_socket.send_string(command_json)
            logger.debug(f"Sent to queue: {command_json}")
        except Exception as e:
            logger.error(f"Failed to send to queue: {e}")
            raise

    def _store_fire_record(
        self,
        fire_id: str,
        user_id: str,
        signal_id: str,
        target_uuid: str,
        symbol: str,
        direction: str,
        sl_price: float,
        tp_price: float,
        fire_command: Dict,
        lot_size: float,
        fire_mode: str,
        bitmode_enabled: bool
    ):
        """Store fire record in PostgreSQL database"""
        try:
            conn = psycopg2.connect(config.DATABASE_URL)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO fires (
                    fire_id, user_id, signal_id, mission_id, target_uuid, status,
                    symbol, direction, sl_price, tp_price,
                    lot_size, fire_mode, bitmode_enabled, fire_command_json
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    fire_id,
                    user_id,
                    signal_id,
                    signal_id,  # mission_id = signal_id
                    target_uuid,
                    FireStatusEnum.QUEUED.value,
                    symbol,
                    direction,
                    sl_price,
                    tp_price,
                    lot_size,
                    fire_mode,
                    bitmode_enabled,
                    json.dumps(fire_command)
                )
            )

            conn.commit()
            conn.close()

            logger.debug(f"Stored fire record: {fire_id}")

        except Exception as e:
            logger.error(f"Failed to store fire record: {e}")
            # Don't raise - fire command already sent

    def _get_user_balance(self, user_id: str) -> Optional[float]:
        """Get user account balance from EA instances (PostgreSQL)"""
        try:
            conn = psycopg2.connect(config.DATABASE_URL)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT last_balance FROM ea_instances
                WHERE user_id = %s
                ORDER BY last_seen DESC
                LIMIT 1
                """,
                (user_id,)
            )

            result = cursor.fetchone()
            conn.close()

            if result:
                return float(result[0])

            return None

        except Exception as e:
            logger.error(f"Error getting user balance: {e}")
            return None

    def _get_user_target_uuid(self, user_id: str) -> Optional[str]:
        """Get user's active EA target UUID (PostgreSQL)"""
        try:
            conn = psycopg2.connect(config.DATABASE_URL)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT target_uuid FROM ea_instances
                WHERE user_id = %s
                AND EXTRACT(EPOCH FROM (NOW() - last_seen)) < 120
                ORDER BY last_seen DESC
                LIMIT 1
                """,
                (user_id,)
            )

            result = cursor.fetchone()
            conn.close()

            if result:
                return result[0]

            return None

        except Exception as e:
            logger.error(f"Error getting target UUID: {e}")
            return None

    def get_fire_details(self, fire_id: str) -> Optional[Dict]:
        """Get fire execution details from database"""
        try:
            conn = sqlite3.connect(str(config.BITTEN_DB))
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT fire_id, user_id, mission_id, status, ticket, price,
                       created_at, updated_at, fire_mode, lot_size,
                       bitmode_enabled, fire_command_json
                FROM fires
                WHERE fire_id = ?
                """,
                (fire_id,)
            )

            result = cursor.fetchone()
            conn.close()

            if result:
                return {
                    "fire_id": result[0],
                    "user_id": result[1],
                    "signal_id": result[2],
                    "status": result[3],
                    "ticket": result[4],
                    "fill_price": result[5],
                    "created_at": result[6],
                    "updated_at": result[7],
                    "fire_mode": result[8],
                    "lot_size": result[9],
                    "bitmode_enabled": bool(result[10]),
                    "fire_command": json.loads(result[11]) if result[11] else None
                }

            return None

        except Exception as e:
            logger.error(f"Error getting fire details: {e}")
            return None

    def get_user_fires(self, user_id: str, limit: int = 10) -> list:
        """Get user's recent fires"""
        try:
            conn = sqlite3.connect(str(config.BITTEN_DB))
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT fire_id, mission_id, status, ticket, price,
                       created_at, fire_mode, lot_size
                FROM fires
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, limit)
            )

            results = cursor.fetchall()
            conn.close()

            fires = []
            for row in results:
                fires.append({
                    "fire_id": row[0],
                    "signal_id": row[1],
                    "status": row[2],
                    "ticket": row[3],
                    "fill_price": row[4],
                    "created_at": row[5],
                    "fire_mode": row[6],
                    "lot_size": row[7]
                })

            return fires

        except Exception as e:
            logger.error(f"Error getting user fires: {e}")
            return []


# Create singleton instance
fire_executor = FireExecutor()
