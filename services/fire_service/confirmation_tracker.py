#!/usr/bin/env python3
"""
Confirmation Tracker Module
Monitors EA confirmations from port 5558 and updates fire records
"""

import json
import logging
import sqlite3
import time
import zmq
from threading import Thread
from typing import Dict
from config import config
from models import FireStatusEnum

logger = logging.getLogger(__name__)


class ConfirmationTracker:
    """Tracks EA confirmations and updates fire records"""

    def __init__(self):
        self.config = config
        self.context = zmq.Context()
        self.confirm_socket = None
        self.running = False
        self.listener_thread = None

    def start(self):
        """Start confirmation listener"""
        if self.running:
            logger.warning("Confirmation tracker already running")
            return

        try:
            self.confirm_socket = self.context.socket(zmq.PULL)
            self.confirm_socket.bind(f"tcp://0.0.0.0:{self.config.CONFIRM_LISTENER_PORT}")
            logger.info(f"Confirmation listener bound to port {self.config.CONFIRM_LISTENER_PORT}")

            self.running = True
            self.listener_thread = Thread(target=self._listen_loop, daemon=True)
            self.listener_thread.start()

            logger.info("Confirmation tracker started")

        except Exception as e:
            logger.error(f"Failed to start confirmation tracker: {e}")
            raise

    def stop(self):
        """Stop confirmation listener"""
        self.running = False
        if self.confirm_socket:
            self.confirm_socket.close()
        logger.info("Confirmation tracker stopped")

    def _listen_loop(self):
        """Main confirmation listening loop"""
        logger.info("Confirmation listener loop started")

        while self.running:
            try:
                # Receive confirmation message
                if self.confirm_socket.poll(timeout=1000):  # 1 second timeout
                    message = self.confirm_socket.recv_string()
                    self._process_confirmation(message)

            except zmq.error.Again:
                # Timeout, continue
                continue
            except Exception as e:
                logger.error(f"Error in confirmation listener: {e}")
                time.sleep(1)

    def _process_confirmation(self, message: str):
        """Process confirmation message from EA"""
        try:
            # Parse JSON message
            confirmation = json.loads(message)

            # Extract confirmation details
            msg_type = confirmation.get("type")
            fire_id = confirmation.get("fire_id")

            if not fire_id:
                logger.warning(f"Confirmation without fire_id: {confirmation}")
                return

            # Handle different confirmation types
            if msg_type == "position_opened":
                self._handle_position_opened(confirmation)
            elif msg_type == "position_closed":
                self._handle_position_closed(confirmation)
            elif msg_type == "confirmation":
                self._handle_generic_confirmation(confirmation)
            else:
                logger.debug(f"Unknown confirmation type: {msg_type}")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in confirmation: {message[:100]}")
        except Exception as e:
            logger.error(f"Error processing confirmation: {e}")

    def _handle_position_opened(self, confirmation: Dict):
        """Handle position_opened confirmation"""
        fire_id = confirmation.get("fire_id")
        ticket = confirmation.get("ticket")
        price = confirmation.get("open_price")
        symbol = confirmation.get("symbol")
        direction = confirmation.get("direction")

        if not all([fire_id, ticket, price]):
            logger.warning(f"Incomplete position_opened: {confirmation}")
            return

        # Update fire record
        self._update_fire_status(
            fire_id=fire_id,
            status=FireStatusEnum.FILLED,
            ticket=ticket,
            fill_price=price
        )

        logger.info(
            f"Position opened: {fire_id} | "
            f"Ticket: {ticket} | "
            f"Price: {price} | "
            f"{symbol} {direction}"
        )

    def _handle_position_closed(self, confirmation: Dict):
        """Handle position_closed confirmation"""
        fire_id = confirmation.get("fire_id")
        ticket = confirmation.get("ticket")
        close_price = confirmation.get("close_price")
        profit = confirmation.get("profit")

        logger.info(
            f"Position closed: {fire_id} | "
            f"Ticket: {ticket} | "
            f"Close: {close_price} | "
            f"Profit: {profit}"
        )

    def _handle_generic_confirmation(self, confirmation: Dict):
        """Handle generic confirmation message"""
        fire_id = confirmation.get("fire_id")
        command_type = confirmation.get("command_type")
        success = confirmation.get("success", False)

        if success:
            ticket = confirmation.get("ticket")
            price = confirmation.get("price")

            if ticket and price:
                self._update_fire_status(
                    fire_id=fire_id,
                    status=FireStatusEnum.FILLED,
                    ticket=ticket,
                    fill_price=price
                )
                logger.info(f"Fire confirmed: {fire_id} | Ticket: {ticket} | Price: {price}")
            else:
                self._update_fire_status(fire_id=fire_id, status=FireStatusEnum.SENT)
                logger.info(f"Fire sent: {fire_id}")
        else:
            error_code = confirmation.get("error_code", "UNKNOWN")
            self._update_fire_status(fire_id=fire_id, status=FireStatusEnum.FAILED)
            logger.warning(f"Fire failed: {fire_id} | Error: {error_code}")

    def _update_fire_status(
        self,
        fire_id: str,
        status: FireStatusEnum,
        ticket: int = None,
        fill_price: float = None
    ):
        """Update fire record status in database"""
        try:
            conn = sqlite3.connect(str(config.BITTEN_DB))
            cursor = conn.cursor()

            now = int(time.time())

            if ticket and fill_price:
                cursor.execute(
                    """
                    UPDATE fires
                    SET status = ?, ticket = ?, price = ?, updated_at = ?
                    WHERE fire_id = ?
                    """,
                    (status.value, ticket, fill_price, now, fire_id)
                )
            else:
                cursor.execute(
                    """
                    UPDATE fires
                    SET status = ?, updated_at = ?
                    WHERE fire_id = ?
                    """,
                    (status.value, now, fire_id)
                )

            if cursor.rowcount > 0:
                conn.commit()
                logger.debug(f"Updated fire {fire_id} to status {status.value}")
            else:
                logger.warning(f"Fire {fire_id} not found in database")

            conn.close()

        except Exception as e:
            logger.error(f"Error updating fire status: {e}")

    def get_fire_status(self, fire_id: str) -> Dict:
        """Get current fire status from database"""
        try:
            conn = sqlite3.connect(str(config.BITTEN_DB))
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT status, ticket, price, updated_at
                FROM fires
                WHERE fire_id = ?
                """,
                (fire_id,)
            )

            result = cursor.fetchone()
            conn.close()

            if result:
                return {
                    "fire_id": fire_id,
                    "status": result[0],
                    "ticket": result[1],
                    "fill_price": result[2],
                    "updated_at": result[3]
                }

            return None

        except Exception as e:
            logger.error(f"Error getting fire status: {e}")
            return None


# Create singleton instance
confirmation_tracker = ConfirmationTracker()
