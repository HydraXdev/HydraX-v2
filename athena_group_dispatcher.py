#!/usr/bin/env python3
"""
🏛️ ATHENA GROUP DISPATCHER
Short tactical messages for @bitten_signals group with HUD links
Replaces long briefings with punchy tactical alerts
"""

import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AthenaGroupDispatcher")


class AthenaGroupDispatcher:
    """
    ATHENA tactical dispatcher for group messages
    Short, punchy messages with HUD links for full briefings
    """

    def __init__(self):
        # ATHENA Mission Bot configuration
        self.athena_bot_token = "8322305650:AAHSnZiY4nX-qFQm0URUg_WyXrGrgb7kkBM"
        self.telegram_api_base = f"https://api.telegram.org/bot{self.athena_bot_token}"

        # Group configuration - BITTEN Signals group
        self.group_chat_id = "-1002581996861"  # Numeric group ID

        # Load ATHENA personality for tactical lines
        try:
            from src.bitten_core.personality.athena_personality import AthenaPersonality

            self.athena = AthenaPersonality()
            self.athena_available = True
            logger.info("✅ ATHENA personality loaded for group dispatch")
        except ImportError as e:
            logger.error(f"❌ ATHENA personality not available: {e}")
            self.athena_available = False

        # Dispatch tracking
        self.group_signals_sent = 0
        self.last_group_signal = None

        # Import existing mission briefing generator
        try:
            from src.bitten_core.mission_briefing_generator import MissionBriefingGenerator

            self.mission_generator = MissionBriefingGenerator()
            logger.info("✅ Mission briefing generator loaded")
        except ImportError as e:
            logger.error(f"❌ Mission briefing generator not available: {e}")
            self.mission_generator = None

        logger.info("🏛️ ATHENA Group Dispatcher initialized")
        logger.info(f"📡 Target Group: {self.group_chat_id}")

    def dispatch_group_signal(self, signal_data: Dict) -> Dict:
        """
        Send short tactical message to @bitten_signals group
        Format: Short tactical alert + HUD link for full briefing
        """
        try:
            # Extract signal data
            signal_id = signal_data.get("signal_id", f"ATHENA_{int(time.time())}")
            symbol = signal_data.get("symbol", "UNKNOWN").upper()
            direction = signal_data.get("direction", "UNKNOWN").upper()
            # Try both tcs_score and confidence fields
            tcs_score = signal_data.get("tcs_score") or signal_data.get("confidence", 0)
            confidence = round(float(tcs_score), 1) if tcs_score else 0

            logger.info(f"🏛️ Dispatching group signal: {signal_id} - {symbol} {direction}")
            logger.info(f"📊 Debug - Signal data keys: {list(signal_data.keys())}")
            logger.info(f"📊 Debug - TCS Score: {tcs_score}, Confidence: {confidence}")

            # Mission files handled by PersonalizedMissionBrain via athena_signal_dispatcher

            # Generate HUD URL for full briefing (mission session deep link)
            alert_id = signal_data.get("id") or signal_data.get("alert_id") or (hash(signal_id) % 1000000)
            hud_url = self._generate_hud_url(signal_id, user_id="7176191872", alert_id=alert_id)

            # Generate tactical line based on TCS confidence
            tactical_line = self._get_tactical_line(confidence)

            # Get signal mode and determine icon
            signal_mode = signal_data.get("signal_mode", "")
            target_pips = signal_data.get("target_pips", 0)
            pattern_type = signal_data.get("pattern_type", "").replace("_", " ").title()

            # Determine mode icon based on signal_mode or target pips
            if signal_mode in ["RAPID", "RAPID_ASSAULT"] or (target_pips > 0 and target_pips < 30):
                mode_icon = "⚡"
                mode_tag = "RAPID"
            elif signal_mode in ["SNIPER", "PRECISION_STRIKE"] or target_pips >= 30:
                mode_icon = "🎯"
                mode_tag = "SNIPER"
            else:
                # Default based on confidence for backwards compatibility
                mode_icon = "⚡" if confidence < 85 else "🎯"
                mode_tag = "RAPID" if confidence < 85 else "SNIPER"

            # Create message in correct format (no tactical line!)
            message = f"""{mode_icon} {mode_tag} • {symbol} {direction} • {confidence}% • {pattern_type}
mission ready
📥 [Mission Brief]({hud_url})"""

            # Send to group
            logger.info(f"📤 Attempting to send to group: {self.group_chat_id}")
            logger.info(f"📝 Message content: {message[:100]}...")

            result = self._send_telegram_message(
                chat_id=self.group_chat_id, text=message, parse_mode="Markdown", disable_web_page_preview=True
            )

            logger.info(f"📬 Send result: {result}")

            if result["success"]:
                self.group_signals_sent += 1
                self.last_group_signal = {
                    "signal_id": signal_id,
                    "symbol": symbol,
                    "direction": direction,
                    "confidence": confidence,
                    "sent_at": datetime.now().isoformat(),
                    "message_id": result.get("message_id"),
                }

                logger.info(f"✅ Group signal dispatched: {signal_id} to {self.group_chat_id}")

                # Track message for auto-deletion after 8 hours
                try:
                    from src.bitten_core.auto_cleanup_system import track_message

                    track_message("athena", self.group_chat_id, result.get("message_id"), signal_id)
                    logger.info(f"📅 Message scheduled for auto-deletion in 8 hours")
                except Exception as e:
                    logger.warning(f"Could not track message for auto-deletion: {e}")

                return {
                    "success": True,
                    "signal_id": signal_id,
                    "group_chat_id": self.group_chat_id,
                    "message_id": result.get("message_id"),
                    "hud_url": hud_url,
                    "tactical_line": tactical_line,
                }
            else:
                logger.error(f"❌ Group dispatch failed: {result.get('error')}")
                return {"success": False, "error": result.get("error"), "signal_id": signal_id}

        except Exception as e:
            logger.error(f"❌ Group signal dispatch error: {e}")
            return {"success": False, "error": str(e), "signal_id": signal_data.get("signal_id", "unknown")}

    def _get_tactical_line(self, confidence: float) -> str:
        """Generate tactical line based on TCS confidence bands"""
        if confidence < 80:
            return "Unstable terrain. Proceed with tactical caution."
        elif 80 <= confidence <= 90:
            return "Opportunity window detected. Strike if aligned."
        else:
            return "Target is exposed. Greenlight. Precision is key."

    def _generate_hud_url(self, signal_id: str, user_id: str = "7176191872", alert_id: int = None) -> str:
        """
        Generate HUD URL for mission brief
        Uses server IP since domain is not configured
        """
        try:
            # Use server IP address - domain joinbitten.com returns 404
            base_url = "http://134.199.204.67:8888"
            hud_url = f"{base_url}/brief?signal_id={signal_id}"

            logger.info(f"✅ Generated HUD link for {signal_id}: {hud_url}")
            return hud_url

        except Exception as e:
            logger.error(f"❌ Failed to generate HUD link: {e}")
            # Fallback
            return f"http://134.199.204.67:8888/brief?signal_id={signal_id}"

    def _send_telegram_message(
        self, chat_id: str, text: str, parse_mode: str = "Markdown", disable_web_page_preview: bool = False
    ) -> Dict:
        """Send message via Telegram API"""
        try:
            url = f"{self.telegram_api_base}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": disable_web_page_preview,
            }

            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    return {"success": True, "message_id": result["result"]["message_id"]}
                else:
                    return {"success": False, "error": result.get("description", "Unknown Telegram error")}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}

        except Exception as e:
            return {"success": False, "error": f"Request failed: {str(e)}"}

    def send_tactical_update(self, message: str) -> Dict:
        """Send general tactical update to group"""
        try:
            formatted_message = f"🏛️ *ATHENA TACTICAL UPDATE*\n\n{message}"

            result = self._send_telegram_message(
                chat_id=self.group_chat_id, text=formatted_message, parse_mode="Markdown"
            )

            if result["success"]:
                logger.info(f"✅ Tactical update sent to {self.group_chat_id}")
            else:
                logger.error(f"❌ Tactical update failed: {result.get('error')}")

            return result

        except Exception as e:
            logger.error(f"❌ Tactical update error: {e}")
            return {"success": False, "error": str(e)}

    def get_group_stats(self) -> Dict:
        """Get group dispatch statistics"""
        return {
            "group_chat_id": self.group_chat_id,
            "total_signals_sent": self.group_signals_sent,
            "last_signal": self.last_group_signal,
            "athena_available": self.athena_available,
            "dispatcher_active": True,
        }


# Global instance for easy integration
athena_group_dispatcher = AthenaGroupDispatcher()


def dispatch_group_signal(signal_data: Dict) -> Dict:
    """Convenience function to dispatch signal to group"""
    return athena_group_dispatcher.dispatch_group_signal(signal_data)


def send_tactical_update(message: str) -> Dict:
    """Convenience function to send tactical update"""
    return athena_group_dispatcher.send_tactical_update(message)
