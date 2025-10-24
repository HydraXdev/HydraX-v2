"""
BITTEN Firebase Enforcer
Server-side validation of execution requests against authoritative controls.

Zero-trust client architecture:
- User preferences in /users/{uid} are for UI only
- Enforcement uses /controls/{uid} (service-only write)
- All execution decisions logged with caps version for audit

Author: BITTEN System
Date: 2025-10-08
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import logging

try:
    from firebase_admin import firestore
except ImportError:
    firestore = None

logger = logging.getLogger(__name__)


class FirebaseEnforcer:
    """
    Server-side validation and enforcement engine.

    Validates execution requests against:
    - Slot availability
    - Cooldown periods
    - Risk caps (per-trade and daily)
    - Symbol restrictions
    - Balance requirements

    Returns enforcement decision with final lot/risk or rejection reason.
    """

    def __init__(self, db):
        """
        Args:
            db: Firestore client instance
        """
        if not db:
            raise ValueError("Firestore client required")

        self.db = db

        # Pip values per lot (used for lot calculation)
        # In production, fetch from MT5 or config service
        self.pip_values = {
            'EURUSD': 10.0,
            'GBPUSD': 10.0,
            'USDJPY': 9.09,
            'AUDUSD': 10.0,
            'USDCAD': 7.69,
            'NZDUSD': 10.0,
            'GBPJPY': 9.09,
            'EURJPY': 9.09,
            'AUDJPY': 9.09,
            'XAUUSD': 10.0,
            'BTCUSD': 10.0,
        }

    async def validate_and_enforce(self, exec_id: str, uid: str) -> Dict:
        """
        Main validation entry point.

        Args:
            exec_id: Execution request ID
            uid: User ID

        Returns:
            {
                'allowed': bool,
                'enforced': {...} if allowed,
                'reason': str if not allowed,
                'message': str if not allowed,
                'details': {...} additional info
            }
        """
        try:
            # 1. Load execution request
            exec_data = await self._load_exec(uid, exec_id)
            if not exec_data:
                return self._reject('EXEC_NOT_FOUND', 'Execution request not found')

            requested = exec_data.get('requested', {})
            signal_id = exec_data.get('signalId')

            logger.info(f"[ENFORCER] Validating {exec_id} for user {uid}, signal {signal_id}")

            # 2. Load server controls (authoritative)
            controls = await self._load_controls(uid)
            if not controls:
                return self._reject('NO_CONTROLS', 'No controls found for user')

            caps = controls.get('caps', {})
            state = controls.get('state', {})
            restrictions = controls.get('restrictions', {})
            overrides = controls.get('overrides', {})
            version = controls.get('version', 0)

            # 3. Load signal details
            signal = await self._load_signal(signal_id)
            if not signal:
                return self._reject('SIGNAL_NOT_FOUND', 'Signal not found or expired')

            pair = signal.get('pair')
            direction = signal.get('direction', 'BUY')

            # 4. Validate slot availability
            slots_check = self._check_slots(state, caps)
            if not slots_check['allowed']:
                return slots_check

            # 5. Validate cooldown
            cooldown_check = self._check_cooldown(state, restrictions)
            if not cooldown_check['allowed']:
                return cooldown_check

            # 6. Validate symbol restrictions
            symbol_check = self._check_symbol(pair, restrictions)
            if not symbol_check['allowed']:
                return symbol_check

            # 7. Validate daily trade limit
            daily_limit_check = self._check_daily_limit(restrictions)
            if not daily_limit_check['allowed']:
                return daily_limit_check

            # 8. Load user balance
            balance = await self._get_user_balance(uid)
            if balance is None:
                return self._reject('BALANCE_UNKNOWN', 'Cannot determine account balance')

            # 9. Validate minimum balance
            min_balance = caps.get('minBalance', 1000)
            if balance < min_balance:
                return self._reject(
                    'BALANCE_LOW',
                    f'Balance ${balance:.2f} below minimum ${min_balance:.2f}'
                )

            # 10. Calculate server-enforced risk & lot
            risk_calc = self._calculate_risk_and_lot(
                signal=signal,
                balance=balance,
                requested_risk_pct=requested.get('riskPct', 1.0),
                caps=caps,
                overrides=overrides
            )

            if not risk_calc['allowed']:
                return risk_calc

            # 11. Validate daily risk exposure
            daily_risk_check = self._check_daily_risk(
                current_used=state.get('dailyRiskUsed', 0),
                additional_risk=risk_calc['risk_amount'],
                balance=balance,
                max_daily_pct=caps.get('maxDailyRiskPct', 2.0)
            )
            if not daily_risk_check['allowed']:
                return daily_risk_check

            # 12. Build enforcement snapshot
            enforced = {
                'riskPct': risk_calc['risk_pct'],
                'lot': risk_calc['final_lot'],
                'risk': risk_calc['risk_amount'],
                'caps': {
                    'maxLotCap': caps.get('maxLotCap', 0.30),
                    'maxDailyRiskPct': caps.get('maxDailyRiskPct', 2.0),
                    'slotsAvailable': state.get('slotsAvailable', 0),
                    'cooldownSec': restrictions.get('cooldownSec', 0),
                    'version': version,
                },
                'pair': pair,
                'direction': direction,
                'entry': signal.get('entry_price', 0),
                'sl': signal.get('sl_price', 0),
                'tp': signal.get('tp_price', 0),
                'lot': risk_calc['final_lot'],
            }

            logger.info(
                f"[ENFORCER] {uid} - ALLOWED: {pair} {risk_calc['final_lot']:.2f} lots "
                f"(risk ${risk_calc['risk_amount']:.2f}, caps v{version})"
            )

            return {
                'allowed': True,
                'enforced': enforced,
                'details': {
                    'requested_risk_pct': requested.get('riskPct'),
                    'enforced_risk_pct': risk_calc['risk_pct'],
                    'requested_lot': requested.get('previewLot'),
                    'enforced_lot': risk_calc['final_lot'],
                    'capped_by': risk_calc.get('capped_by', []),
                }
            }

        except Exception as e:
            logger.error(f"[ENFORCER] Error validating {exec_id}: {e}", exc_info=True)
            return self._reject('VALIDATION_ERROR', f'Internal error: {str(e)}')

    # ─────────────────────────────────────────────────────────────
    # Validation Checks
    # ─────────────────────────────────────────────────────────────

    def _check_slots(self, state: Dict, caps: Dict) -> Dict:
        """Validate slot availability"""
        slots_available = state.get('slotsAvailable', 0)
        slots_used = state.get('slotsUsed', 0)
        max_slots = caps.get('maxSlots', 6)

        if slots_available <= 0:
            return self._reject(
                'SLOT_0',
                f'No slots available. Active trades: {slots_used}/{max_slots}'
            )

        return {'allowed': True}

    def _check_cooldown(self, state: Dict, restrictions: Dict) -> Dict:
        """Validate cooldown period"""
        cooldown_until = state.get('cooldownUntil')
        cooldown_sec = restrictions.get('cooldownSec', 0)

        if cooldown_until:
            if isinstance(cooldown_until, datetime):
                until_dt = cooldown_until
            else:
                # Firestore timestamp
                until_dt = cooldown_until.to_datetime() if hasattr(cooldown_until, 'to_datetime') else datetime.utcnow()

            if until_dt > datetime.utcnow():
                remaining = (until_dt - datetime.utcnow()).total_seconds()
                return self._reject(
                    'COOLDOWN',
                    f'Must wait {int(remaining)}s before next trade (cooldown: {cooldown_sec}s)'
                )

        return {'allowed': True}

    def _check_symbol(self, pair: str, restrictions: Dict) -> Dict:
        """Validate symbol is not blocked"""
        blocked = restrictions.get('blockedSymbols', [])

        if pair in blocked:
            return self._reject(
                'SYMBOL_BLOCKED',
                f'{pair} is blocked for your account'
            )

        return {'allowed': True}

    def _check_daily_limit(self, restrictions: Dict) -> Dict:
        """Validate daily trade count"""
        trades_today = restrictions.get('tradesUsedToday', 0)
        max_per_day = restrictions.get('maxTradesPerDay', 999)

        if trades_today >= max_per_day:
            return self._reject(
                'DAILY_LIMIT',
                f'Daily trade limit reached: {trades_today}/{max_per_day}'
            )

        return {'allowed': True}

    def _check_daily_risk(self, current_used: float, additional_risk: float,
                          balance: float, max_daily_pct: float) -> Dict:
        """Validate daily risk exposure"""
        max_daily_risk = balance * (max_daily_pct / 100)

        if current_used + additional_risk > max_daily_risk:
            return self._reject(
                'RISK_CAP',
                f'Daily risk cap would be exceeded: '
                f'${current_used:.2f} + ${additional_risk:.2f} > ${max_daily_risk:.2f} '
                f'({max_daily_pct}% of balance)'
            )

        return {'allowed': True}

    # ─────────────────────────────────────────────────────────────
    # Risk Calculation
    # ─────────────────────────────────────────────────────────────

    def _calculate_risk_and_lot(self, signal: Dict, balance: float,
                                requested_risk_pct: float, caps: Dict,
                                overrides: Dict) -> Dict:
        """
        Calculate server-enforced risk and lot size.

        Priority order:
        1. Server overrides (if user is restricted)
        2. Caps (hard limits)
        3. User requested (if within caps)
        """
        capped_by = []

        # 1. Determine risk %
        # Server override takes precedence
        if 'riskPct' in overrides:
            risk_pct = overrides['riskPct']
            capped_by.append(f'override_risk_{risk_pct}%')
        else:
            risk_pct = requested_risk_pct

        # 2. Calculate risk amount in $
        max_risk_per_trade = caps.get('maxRiskPerTrade', 200)
        risk_amount = balance * (risk_pct / 100)

        if risk_amount > max_risk_per_trade:
            risk_amount = max_risk_per_trade
            capped_by.append(f'max_risk_${max_risk_per_trade}')

        # 3. Get signal SL pips
        sl_pips = signal.get('sl_pips', 20)
        if sl_pips <= 0:
            return self._reject('INVALID_SL', 'Signal has invalid stop loss')

        # 4. Get pip value
        pair = signal.get('pair')
        pip_value = self._get_pip_value(pair)

        # 5. Calculate lot size
        # Formula: Lot = Risk $ / (SL pips × Pip value per lot)
        calculated_lot = risk_amount / (sl_pips * pip_value)

        # 6. Apply lot cap
        max_lot_cap = caps.get('maxLotCap', 0.30)
        final_lot = min(calculated_lot, max_lot_cap)

        if final_lot < calculated_lot:
            capped_by.append(f'max_lot_{max_lot_cap}')

        # 7. Round to 2 decimals (MT5 standard)
        final_lot = round(final_lot, 2)

        # 8. Validate minimum lot
        min_lot = 0.01
        if final_lot < min_lot:
            return self._reject(
                'LOT_TOO_SMALL',
                f'Calculated lot {final_lot:.2f} below minimum {min_lot}'
            )

        return {
            'allowed': True,
            'risk_pct': risk_pct,
            'risk_amount': risk_amount,
            'final_lot': final_lot,
            'capped_by': capped_by
        }

    def _get_pip_value(self, pair: str) -> float:
        """
        Get pip value per standard lot.

        In production, this should:
        - Fetch from MT5 SymbolInfoDouble
        - Account for account currency
        - Handle cross rates

        For now, using standard USD account values.
        """
        return self.pip_values.get(pair, 10.0)

    # ─────────────────────────────────────────────────────────────
    # Data Loading
    # ─────────────────────────────────────────────────────────────

    async def _load_exec(self, uid: str, exec_id: str) -> Optional[Dict]:
        """Load execution request from Firestore"""
        try:
            exec_ref = self.db.collection('exec').document(uid).collection('items').document(exec_id)
            exec_doc = exec_ref.get()

            if not exec_doc.exists:
                return None

            return exec_doc.to_dict()

        except Exception as e:
            logger.error(f"[ENFORCER] Error loading exec {exec_id}: {e}")
            return None

    async def _load_controls(self, uid: str) -> Optional[Dict]:
        """Load server controls from Firestore"""
        try:
            controls_ref = self.db.collection('controls').document(uid)
            controls_doc = controls_ref.get()

            if not controls_doc.exists:
                logger.warning(f"[ENFORCER] No controls found for user {uid}")
                return None

            return controls_doc.to_dict()

        except Exception as e:
            logger.error(f"[ENFORCER] Error loading controls for {uid}: {e}")
            return None

    async def _load_signal(self, signal_id: str) -> Optional[Dict]:
        """Load signal from Firestore"""
        try:
            signal_ref = self.db.collection('signals').document(signal_id)
            signal_doc = signal_ref.get()

            if not signal_doc.exists:
                return None

            signal_data = signal_doc.to_dict()

            # Check if expired
            expires_at = signal_data.get('expiresAt')
            if expires_at:
                if isinstance(expires_at, datetime):
                    expires_dt = expires_at
                else:
                    expires_dt = expires_at.to_datetime() if hasattr(expires_at, 'to_datetime') else None

                if expires_dt and expires_dt < datetime.utcnow():
                    logger.warning(f"[ENFORCER] Signal {signal_id} expired")
                    return None

            return signal_data

        except Exception as e:
            logger.error(f"[ENFORCER] Error loading signal {signal_id}: {e}")
            return None

    async def _get_user_balance(self, uid: str) -> Optional[float]:
        """Get user's current balance from Firestore"""
        try:
            user_ref = self.db.collection('users').document(uid)
            user_doc = user_ref.get()

            if not user_doc.exists:
                return None

            return user_doc.to_dict().get('stats', {}).get('balance', 0)

        except Exception as e:
            logger.error(f"[ENFORCER] Error loading balance for {uid}: {e}")
            return None

    # ─────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────

    def _reject(self, reason: str, message: str, details: Optional[Dict] = None) -> Dict:
        """Build rejection response"""
        return {
            'allowed': False,
            'reason': reason,
            'message': message,
            'details': details or {}
        }
