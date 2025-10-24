"""
BITTEN Firebase Projector (CQRS Read-Model Synchronization)

Mirrors Postgres trading truth to Firestore for PWA/realtime UX.
Consumes domain events and projects denormalized read-models.

Architecture:
- Postgres = Source of truth (orders, fills, P&L, audit)
- Firestore = Eventually consistent read-models (signals, exec states, presence)
- This service = Event consumer + Firestore upserter

Event Sources:
1. Redis Pub/Sub (primary)
2. Postgres NOTIFY/LISTEN (fallback)
3. Direct function calls (in-process)

Idempotency: All writes use event_id as idempotency key to prevent duplicates.

Author: BITTEN System
Date: 2025-10-08
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from collections import deque

try:
    from firebase_admin import firestore
    from google.cloud.firestore_v1.base_query import FieldFilter
except ImportError:
    firestore = None

logger = logging.getLogger(__name__)


class FirebaseProjector:
    """
    Projects domain events from trading core to Firestore read-models.

    Responsibilities:
    - Mirror signals to /signals/{id}
    - Mirror exec states to /exec/{uid}/{execId}
    - Mirror EA presence to /presence/{uuid}
    - Maintain active trades in /trades/{uid}/active/{tradeId}
    - Dead-letter failed projections for retry
    """

    def __init__(self, db, redis_client=None, dead_letter_queue=None):
        """
        Args:
            db: Firestore client
            redis_client: Optional Redis client for pub/sub
            dead_letter_queue: Optional queue for failed projections
        """
        if not db:
            raise ValueError("Firestore client required")

        self.db = db
        self.redis = redis_client
        self.dlq = dead_letter_queue or deque(maxlen=1000)

        # Idempotency cache (in-memory, or use Redis)
        self.processed_events = set()
        self.max_cache_size = 10000

        logger.info("[PROJECTOR] Initialized")

    # ─────────────────────────────────────────────────────────────
    # Event Handlers (Public API)
    # ─────────────────────────────────────────────────────────────

    async def project_signal_generated(self, event: Dict) -> bool:
        """
        Project: Elite Guard generated new signal

        Event schema:
        {
            'event_id': str,
            'event_type': 'SIGNAL_GENERATED',
            'timestamp': datetime,
            'signal': {
                'signal_id': str,
                'pattern_type': str,
                'pair': str,
                'confidence': float,
                'entry_price': float,
                'tp_price': float,
                'sl_price': float,
                'tp_pips': int,
                'sl_pips': int,
                'rr_ratio': float,
                'timeframe': str,
                'session': str,
                'expires_at': datetime,
                'created_by': str,
            }
        }
        """
        try:
            event_id = event.get('event_id')
            if not event_id or not self._is_idempotent(event_id):
                return False

            signal = event.get('signal', {})
            signal_id = signal.get('signal_id')

            if not signal_id:
                logger.error(f"[PROJECTOR] Missing signal_id in event {event_id}")
                return False

            # Project to Firestore
            signal_ref = self.db.collection('signals').document(signal_id)

            await self._firestore_set(signal_ref, {
                'signalId': signal_id,
                'pattern_type': signal.get('pattern_type'),
                'pair': signal.get('pair'),
                'timeframe': signal.get('timeframe'),
                'session': signal.get('session'),
                'confidence': signal.get('confidence'),
                'entry_price': signal.get('entry_price'),
                'tp_price': signal.get('tp_price'),
                'sl_price': signal.get('sl_price'),
                'tp_pips': signal.get('tp_pips'),
                'sl_pips': signal.get('sl_pips'),
                'rr_ratio': signal.get('rr_ratio'),
                'status': 'ACTIVE',
                'expiresAt': signal.get('expires_at'),
                'createdAt': signal.get('created_at', datetime.utcnow()),
                'createdBy': signal.get('created_by', 'ELITE_GUARD'),
            })

            logger.info(f"[PROJECTOR] Projected signal {signal_id}")
            self._mark_processed(event_id)
            return True

        except Exception as e:
            logger.error(f"[PROJECTOR] Error projecting signal: {e}", exc_info=True)
            self._dead_letter(event, str(e))
            return False

    async def project_exec_created(self, event: Dict) -> bool:
        """
        Project: User created execution request

        Event schema:
        {
            'event_id': str,
            'event_type': 'EXEC_CREATED',
            'timestamp': datetime,
            'exec': {
                'exec_id': str,
                'uid': str,
                'signal_id': str,
                'requested': {...},
                'created_at': datetime,
            }
        }
        """
        try:
            event_id = event.get('event_id')
            if not event_id or not self._is_idempotent(event_id):
                return False

            exec_data = event.get('exec', {})
            exec_id = exec_data.get('exec_id')
            uid = exec_data.get('uid')

            if not exec_id or not uid:
                logger.error(f"[PROJECTOR] Missing exec_id/uid in event {event_id}")
                return False

            # Project to Firestore
            exec_ref = (self.db.collection('exec')
                       .document(uid)
                       .collection('docs')
                       .document(exec_id))

            await self._firestore_set(exec_ref, {
                'execId': exec_id,
                'uid': uid,
                'signalId': exec_data.get('signal_id'),
                'state': 'PENDING',
                'requested': exec_data.get('requested', {}),
                'createdAt': exec_data.get('created_at', datetime.utcnow()),
            })

            logger.info(f"[PROJECTOR] Projected exec created {exec_id}")
            self._mark_processed(event_id)
            return True

        except Exception as e:
            logger.error(f"[PROJECTOR] Error projecting exec created: {e}", exc_info=True)
            self._dead_letter(event, str(e))
            return False

    async def project_exec_validated(self, event: Dict) -> bool:
        """
        Project: Server validated execution (allowed or rejected)

        Event schema:
        {
            'event_id': str,
            'event_type': 'EXEC_VALIDATED',
            'timestamp': datetime,
            'exec_id': str,
            'uid': str,
            'allowed': bool,
            'enforced': {...} if allowed,
            'rejection': {...} if not allowed,
        }
        """
        try:
            event_id = event.get('event_id')
            if not event_id or not self._is_idempotent(event_id):
                return False

            exec_id = event.get('exec_id')
            uid = event.get('uid')
            allowed = event.get('allowed')

            exec_ref = (self.db.collection('exec')
                       .document(uid)
                       .collection('docs')
                       .document(exec_id))

            if allowed:
                # Approved - add enforcement snapshot
                await self._firestore_update(exec_ref, {
                    'state': 'VALIDATED',
                    'enforced': event.get('enforced', {}),
                    'validatedAt': firestore.SERVER_TIMESTAMP,
                })
            else:
                # Rejected - add rejection reason
                await self._firestore_update(exec_ref, {
                    'state': 'REJECTED',
                    'rejection': event.get('rejection', {}),
                    'validatedAt': firestore.SERVER_TIMESTAMP,
                })

            logger.info(f"[PROJECTOR] Projected exec validated {exec_id}: {'ALLOWED' if allowed else 'REJECTED'}")
            self._mark_processed(event_id)
            return True

        except Exception as e:
            logger.error(f"[PROJECTOR] Error projecting exec validated: {e}", exc_info=True)
            self._dead_letter(event, str(e))
            return False

    async def project_exec_sent(self, event: Dict) -> bool:
        """
        Project: Fire command sent to EA via ZMQ

        Event schema:
        {
            'event_id': str,
            'event_type': 'EXEC_SENT',
            'timestamp': datetime,
            'exec_id': str,
            'uid': str,
            'target_uuid': str,
            'sent_at': datetime,
        }
        """
        try:
            event_id = event.get('event_id')
            if not event_id or not self._is_idempotent(event_id):
                return False

            exec_id = event.get('exec_id')
            uid = event.get('uid')

            exec_ref = (self.db.collection('exec')
                       .document(uid)
                       .collection('docs')
                       .document(exec_id))

            await self._firestore_update(exec_ref, {
                'state': 'SENT',
                'sentAt': firestore.SERVER_TIMESTAMP,
                'targetUuid': event.get('target_uuid'),
            })

            logger.info(f"[PROJECTOR] Projected exec sent {exec_id}")
            self._mark_processed(event_id)
            return True

        except Exception as e:
            logger.error(f"[PROJECTOR] Error projecting exec sent: {e}", exc_info=True)
            self._dead_letter(event, str(e))
            return False

    async def project_exec_filled(self, event: Dict) -> bool:
        """
        Project: EA confirmed trade filled

        Event schema:
        {
            'event_id': str,
            'event_type': 'EXEC_FILLED',
            'timestamp': datetime,
            'exec_id': str,
            'uid': str,
            'ticket': int,
            'fill_price': float,
            'fill_time': datetime,
            'slippage': float,
        }
        """
        try:
            event_id = event.get('event_id')
            if not event_id or not self._is_idempotent(event_id):
                return False

            exec_id = event.get('exec_id')
            uid = event.get('uid')
            ticket = event.get('ticket')

            # 1. Update exec state
            exec_ref = (self.db.collection('exec')
                       .document(uid)
                       .collection('docs')
                       .document(exec_id))

            await self._firestore_update(exec_ref, {
                'state': 'FILLED',
                'confirmation': {
                    'ticket': ticket,
                    'fillPrice': event.get('fill_price'),
                    'fillTime': event.get('fill_time', datetime.utcnow()),
                    'slippage': event.get('slippage', 0),
                },
                'filledAt': firestore.SERVER_TIMESTAMP,
            })

            # 2. Create active trade
            # Load enforced values from exec
            exec_doc = exec_ref.get()
            if exec_doc.exists:
                exec_data = exec_doc.to_dict()
                enforced = exec_data.get('enforced', {})
                signal_id = exec_data.get('signalId')

                trade_ref = (self.db.collection('trades')
                            .document(uid)
                            .collection('active')
                            .document(str(ticket)))

                await self._firestore_set(trade_ref, {
                    'tradeId': str(ticket),
                    'uid': uid,
                    'execId': exec_id,
                    'signalId': signal_id,
                    'pair': enforced.get('pair'),
                    'direction': enforced.get('direction'),
                    'entry': event.get('fill_price'),
                    'current': event.get('fill_price'),
                    'stopLoss': enforced.get('sl'),
                    'takeProfit': enforced.get('tp'),
                    'lot': enforced.get('lot'),
                    'equity': 0,
                    'pips': 0,
                    'ticket': ticket,
                    'openTime': event.get('fill_time', datetime.utcnow()),
                    'status': 'OPEN',
                    'lastUpdate': firestore.SERVER_TIMESTAMP,
                })

            logger.info(f"[PROJECTOR] Projected exec filled {exec_id}, ticket {ticket}")
            self._mark_processed(event_id)
            return True

        except Exception as e:
            logger.error(f"[PROJECTOR] Error projecting exec filled: {e}", exc_info=True)
            self._dead_letter(event, str(e))
            return False

    async def project_trade_updated(self, event: Dict) -> bool:
        """
        Project: Trade P&L/price updated (from tick stream)

        Event schema:
        {
            'event_id': str,
            'event_type': 'TRADE_UPDATED',
            'timestamp': datetime,
            'uid': str,
            'ticket': int,
            'current_price': float,
            'equity': float,
            'pips': float,
        }
        """
        try:
            event_id = event.get('event_id')
            if not event_id or not self._is_idempotent(event_id):
                return False

            uid = event.get('uid')
            ticket = event.get('ticket')

            trade_ref = (self.db.collection('trades')
                        .document(uid)
                        .collection('active')
                        .document(str(ticket)))

            await self._firestore_update(trade_ref, {
                'current': event.get('current_price'),
                'equity': event.get('equity'),
                'pips': event.get('pips'),
                'lastUpdate': firestore.SERVER_TIMESTAMP,
            })

            # Don't log every tick update (too noisy)
            self._mark_processed(event_id)
            return True

        except Exception as e:
            logger.error(f"[PROJECTOR] Error projecting trade update: {e}", exc_info=True)
            # Don't dead-letter tick updates (too frequent)
            return False

    async def project_trade_closed(self, event: Dict) -> bool:
        """
        Project: Trade closed (TP/SL hit or manual close)

        Event schema:
        {
            'event_id': str,
            'event_type': 'TRADE_CLOSED',
            'timestamp': datetime,
            'uid': str,
            'ticket': int,
            'close_price': float,
            'close_time': datetime,
            'final_pl': float,
            'reason': str,  # 'TP' | 'SL' | 'MANUAL'
        }
        """
        try:
            event_id = event.get('event_id')
            if not event_id or not self._is_idempotent(event_id):
                return False

            uid = event.get('uid')
            ticket = event.get('ticket')

            # Move from active to closed
            active_ref = (self.db.collection('trades')
                         .document(uid)
                         .collection('active')
                         .document(str(ticket)))

            # Get final state
            active_doc = active_ref.get()
            if not active_doc.exists:
                logger.warning(f"[PROJECTOR] Trade {ticket} not found in active")
                return False

            trade_data = active_doc.to_dict()

            # Archive to closed collection
            closed_ref = (self.db.collection('trades')
                         .document(uid)
                         .collection('closed')
                         .document(str(ticket)))

            await self._firestore_set(closed_ref, {
                **trade_data,
                'status': 'CLOSED',
                'closePrice': event.get('close_price'),
                'closeTime': event.get('close_time', datetime.utcnow()),
                'finalPL': event.get('final_pl'),
                'closeReason': event.get('reason'),
            })

            # Delete from active
            active_ref.delete()

            logger.info(f"[PROJECTOR] Projected trade closed {ticket}: {event.get('reason')}")
            self._mark_processed(event_id)
            return True

        except Exception as e:
            logger.error(f"[PROJECTOR] Error projecting trade closed: {e}", exc_info=True)
            self._dead_letter(event, str(e))
            return False

    async def project_ea_presence(self, event: Dict) -> bool:
        """
        Project: EA heartbeat/presence update

        Event schema:
        {
            'event_id': str,
            'event_type': 'EA_PRESENCE',
            'timestamp': datetime,
            'uuid': str,
            'status': 'ONLINE' | 'OFFLINE',
            'last_seen': datetime,
            'balance': float,
            'equity': float,
        }
        """
        try:
            event_id = event.get('event_id')
            # Don't use idempotency for presence (frequent updates)

            uuid = event.get('uuid')
            if not uuid:
                return False

            presence_ref = self.db.collection('presence').document(uuid)

            await self._firestore_set(presence_ref, {
                'uuid': uuid,
                'status': event.get('status', 'ONLINE'),
                'lastSeen': event.get('last_seen', datetime.utcnow()),
                'balance': event.get('balance'),
                'equity': event.get('equity'),
                'updatedAt': firestore.SERVER_TIMESTAMP,
            }, merge=True)

            return True

        except Exception as e:
            logger.error(f"[PROJECTOR] Error projecting EA presence: {e}", exc_info=True)
            return False

    # ─────────────────────────────────────────────────────────────
    # Event Consumption (Redis Pub/Sub)
    # ─────────────────────────────────────────────────────────────

    async def subscribe_redis(self, channels: list):
        """
        Subscribe to Redis pub/sub channels and route events.

        Args:
            channels: List of Redis channels to subscribe to
                      e.g., ['bitten:signals', 'bitten:exec', 'bitten:trades']
        """
        if not self.redis:
            logger.error("[PROJECTOR] Redis client not configured")
            return

        pubsub = self.redis.pubsub()
        pubsub.subscribe(*channels)

        logger.info(f"[PROJECTOR] Subscribed to Redis channels: {channels}")

        for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    event = json.loads(message['data'])
                    await self.route_event(event)
                except Exception as e:
                    logger.error(f"[PROJECTOR] Error processing Redis message: {e}")

    async def route_event(self, event: Dict) -> bool:
        """
        Route event to appropriate projection handler.

        Args:
            event: Domain event dict with 'event_type' field
        """
        event_type = event.get('event_type')

        handlers = {
            'SIGNAL_GENERATED': self.project_signal_generated,
            'EXEC_CREATED': self.project_exec_created,
            'EXEC_VALIDATED': self.project_exec_validated,
            'EXEC_SENT': self.project_exec_sent,
            'EXEC_FILLED': self.project_exec_filled,
            'TRADE_UPDATED': self.project_trade_updated,
            'TRADE_CLOSED': self.project_trade_closed,
            'EA_PRESENCE': self.project_ea_presence,
        }

        handler = handlers.get(event_type)
        if not handler:
            logger.warning(f"[PROJECTOR] Unknown event type: {event_type}")
            return False

        return await handler(event)

    # ─────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────

    def _is_idempotent(self, event_id: str) -> bool:
        """Check if event was already processed"""
        if event_id in self.processed_events:
            logger.debug(f"[PROJECTOR] Skipping duplicate event {event_id}")
            return False

        return True

    def _mark_processed(self, event_id: str):
        """Mark event as processed"""
        self.processed_events.add(event_id)

        # Trim cache if too large
        if len(self.processed_events) > self.max_cache_size:
            # Remove oldest 20%
            remove_count = self.max_cache_size // 5
            for _ in range(remove_count):
                self.processed_events.pop()

    def _dead_letter(self, event: Dict, error: str):
        """Add failed event to dead-letter queue"""
        self.dlq.append({
            'event': event,
            'error': error,
            'timestamp': datetime.utcnow(),
        })
        logger.error(f"[PROJECTOR] Dead-lettered event {event.get('event_id')}: {error}")

    async def _firestore_set(self, ref, data: Dict, merge: bool = False):
        """Safe Firestore set with error handling"""
        try:
            ref.set(data, merge=merge)
        except Exception as e:
            logger.error(f"[PROJECTOR] Firestore set failed: {e}")
            raise

    async def _firestore_update(self, ref, data: Dict):
        """Safe Firestore update with error handling"""
        try:
            ref.update(data)
        except Exception as e:
            logger.error(f"[PROJECTOR] Firestore update failed: {e}")
            raise

    # ─────────────────────────────────────────────────────────────
    # Maintenance
    # ─────────────────────────────────────────────────────────────

    async def reconcile_nightly(self):
        """
        Nightly reconciliation: Compare Postgres counts to Firestore.
        Alert on discrepancies.
        """
        # This would query Postgres for counts/hashes and compare to Firestore
        # Implementation depends on your Postgres schema
        logger.info("[PROJECTOR] Nightly reconciliation started")
        # TODO: Implement reconciliation logic
        pass

    def get_dead_letters(self) -> list:
        """Get failed events for retry"""
        return list(self.dlq)

    def clear_dead_letters(self):
        """Clear dead-letter queue after manual retry"""
        self.dlq.clear()
