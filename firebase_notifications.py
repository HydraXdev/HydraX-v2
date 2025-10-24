"""
Firebase Push Notifications for Trailing Stops
Sends FCM notifications to users when trailing stops activate
"""
import logging
import firebase_admin
from firebase_admin import messaging, firestore
from typing import Optional

logger = logging.getLogger(__name__)

def send_trailing_notification(
    user_id: str,
    fire_id: str,
    event_type: str,
    symbol: str,
    direction: str,
    ticket: int,
    current_profit_pips: float,
    new_sl: Optional[float] = None,
    style: Optional[str] = None
) -> bool:
    """
    Send Firebase Cloud Messaging notification for trailing stop events

    Args:
        user_id: Firebase user ID
        fire_id: Trade fire ID
        event_type: "ARMED", "PROTECTION", "EXIT"
        symbol: Trading pair
        direction: "BUY" or "SELL"
        ticket: MT5 ticket number
        current_profit_pips: Current profit in pips
        new_sl: New stop loss price (for ARMED event)
        style: Trailing style (ATR, Fixed, etc.)
    """
    try:
        # Get user's FCM token from Firestore
        db = firestore.client()
        user_doc = db.collection('users').document(user_id).get()

        if not user_doc.exists:
            logger.warning(f"User {user_id} not found in Firestore")
            return False

        user_data = user_doc.to_dict()
        fcm_token = user_data.get('fcmToken')

        if not fcm_token:
            logger.debug(f"No FCM token for user {user_id} - notifications disabled")
            return False

        # Craft notification based on event type
        if event_type == "ARMED":
            title = "🎯 Trailing Stop Activated"
            body = f"{symbol} {direction} #{ticket}\n+{current_profit_pips:.1f} pips\nPosition protected!"
            data_payload = {
                'type': 'trailing_armed',
                'fire_id': fire_id,
                'symbol': symbol,
                'direction': direction,
                'ticket': str(ticket),
                'profit_pips': str(current_profit_pips),
                'new_sl': str(new_sl) if new_sl else '',
                'style': style or 'ATR'
            }

        elif event_type == "PROTECTION":
            title = "🛡️ Profit Protection Achieved"
            body = f"{symbol} {direction} #{ticket}\n+{current_profit_pips:.1f} pips locked\nSlot unlocked!"
            data_payload = {
                'type': 'trailing_protection',
                'fire_id': fire_id,
                'symbol': symbol,
                'direction': direction,
                'ticket': str(ticket),
                'profit_pips': str(current_profit_pips)
            }

        elif event_type == "EXIT":
            title = "🏁 Trailing Stop Exit"
            body = f"{symbol} {direction} #{ticket}\nClosed at +{current_profit_pips:.1f} pips"
            data_payload = {
                'type': 'trailing_exit',
                'fire_id': fire_id,
                'symbol': symbol,
                'direction': direction,
                'ticket': str(ticket),
                'profit_pips': str(current_profit_pips)
            }

        else:
            logger.warning(f"Unknown trailing event type: {event_type}")
            return False

        # Create FCM message
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data=data_payload,
            token=fcm_token,
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    sound='default',
                    color='#00FF00' if event_type in ['ARMED', 'PROTECTION'] else '#FFD700'
                )
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound='default',
                        badge=1
                    )
                )
            )
        )

        # Send message
        response = messaging.send(message)
        logger.info(f"✅ FCM notification sent to {user_id}: {title} (response: {response})")
        return True

    except Exception as e:
        logger.error(f"Failed to send FCM notification: {e}")
        return False


def update_trailing_status_firestore(
    fire_id: str,
    user_id: str,
    trailing_status: str,
    current_profit_pips: float,
    new_sl: Optional[float] = None
) -> bool:
    """
    Update active_trades Firestore document with trailing stop status

    Args:
        fire_id: Trade fire ID
        user_id: Firebase user ID
        trailing_status: "ARMED", "ACTIVE", "PROTECTED", "CLOSED"
        current_profit_pips: Current profit in pips
        new_sl: New stop loss price
    """
    try:
        db = firestore.client()

        # Find the active trade document
        trades_ref = db.collection('active_trades')
        query = trades_ref.where('user_id', '==', user_id).where('trade_id', '==', fire_id)
        docs = query.stream()

        doc_id = None
        for doc in docs:
            doc_id = doc.id
            break

        if not doc_id:
            logger.warning(f"Active trade not found for fire_id {fire_id}")
            return False

        # Update document with trailing status
        update_data = {
            'trailing_status': trailing_status,
            'trailing_profit_pips': current_profit_pips,
            'updated_at': firestore.SERVER_TIMESTAMP
        }

        if new_sl is not None:
            update_data['stopLoss'] = new_sl

        db.collection('active_trades').document(doc_id).update(update_data)
        logger.info(f"✅ Updated Firestore trailing status: {fire_id} → {trailing_status}")
        return True

    except Exception as e:
        logger.error(f"Failed to update Firestore trailing status: {e}")
        return False


def create_trailing_activity_event(
    user_id: str,
    fire_id: str,
    event_type: str,
    symbol: str,
    direction: str,
    ticket: int,
    current_profit_pips: float
) -> bool:
    """
    Create activity feed event for trailing stop activation

    Args:
        user_id: Firebase user ID
        fire_id: Trade fire ID
        event_type: "ARMED", "PROTECTION", "EXIT"
        symbol: Trading pair
        direction: "BUY" or "SELL"
        ticket: MT5 ticket number
        current_profit_pips: Current profit in pips
    """
    try:
        db = firestore.client()

        # Create activity event
        event_icons = {
            'ARMED': '🎯',
            'PROTECTION': '🛡️',
            'EXIT': '🏁'
        }

        event_titles = {
            'ARMED': 'Trailing Stop Activated',
            'PROTECTION': 'Profit Protection Achieved',
            'EXIT': 'Trailing Stop Exit'
        }

        event_messages = {
            'ARMED': f'Position protected at +{current_profit_pips:.1f} pips',
            'PROTECTION': f'Slot unlocked, profit secured at +{current_profit_pips:.1f} pips',
            'EXIT': f'Trade closed by trailing stop at +{current_profit_pips:.1f} pips'
        }

        activity_event = {
            'user_id': user_id,
            'type': 'trailing_event',
            'event_type': event_type,
            'icon': event_icons.get(event_type, '🎯'),
            'title': event_titles.get(event_type, 'Trailing Event'),
            'message': event_messages.get(event_type, f'Trailing event at +{current_profit_pips:.1f} pips'),
            'symbol': symbol,
            'direction': direction,
            'ticket': ticket,
            'fire_id': fire_id,
            'profit_pips': current_profit_pips,
            'timestamp': firestore.SERVER_TIMESTAMP,
            'read': False
        }

        db.collection('activity_feed').add(activity_event)
        logger.info(f"✅ Created activity event: {event_type} for {fire_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to create activity event: {e}")
        return False
