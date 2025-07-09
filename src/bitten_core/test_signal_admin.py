"""
Test Signal Admin Interface
Admin tools for managing and monitoring the 60 TCS test signal system
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

from .test_signal_system import test_signal_system
from .test_signal_config import (
    get_test_signal_config, 
    update_test_signal_config,
    enable_debug_mode,
    disable_debug_mode
)
from .test_signal_integration import test_signal_integration

logger = logging.getLogger(__name__)


class TestSignalAdmin:
    """Admin interface for test signal system"""
    
    def __init__(self):
        self.test_system = test_signal_system
        self.integration = test_signal_integration
        
    async def get_system_overview(self) -> Dict[str, Any]:
        """Get comprehensive system overview for admin dashboard"""
        try:
            config = get_test_signal_config()
            summary = self.integration.get_test_signal_summary()
            
            # Get recent activity
            recent_signals = self._get_recent_signals(days=7)
            
            # Calculate success metrics
            total_sent = sum(len(s.users_sent) for s in recent_signals)
            total_passed = sum(
                1 for s in recent_signals 
                for r in s.results.values() 
                if r.value == "passed"
            )
            
            detection_rate = (total_passed / total_sent * 100) if total_sent > 0 else 0
            
            return {
                "status": "active" if config["enabled"] else "disabled",
                "debug_mode": config["debug_mode"],
                "config": {
                    "frequency": f"{config['min_days_between']}-{config['max_days_between']} days",
                    "max_per_week": config["max_active_per_week"],
                    "eligible_tiers": config["eligible_tiers"],
                    "user_selection": f"{config['user_selection_probability']*100}%"
                },
                "statistics": summary,
                "recent_activity": {
                    "signals_last_7_days": len(recent_signals),
                    "total_users_targeted": total_sent,
                    "detection_rate": f"{detection_rate:.1f}%",
                    "next_signal": summary.get("next_signal_time", "Unknown")
                },
                "top_performers": summary.get("top_detectors", [])
            }
            
        except Exception as e:
            logger.error(f"Error getting system overview: {e}")
            return {"error": str(e)}
    
    def _get_recent_signals(self, days: int = 7) -> List:
        """Get signals from the last N days"""
        cutoff = datetime.now() - timedelta(days=days)
        return [
            s for s in self.test_system.signal_history 
            if s.timestamp > cutoff
        ]
    
    async def toggle_system(self, enabled: bool) -> Dict[str, str]:
        """Enable or disable the test signal system"""
        try:
            update_test_signal_config({"enabled": enabled})
            self.test_system.config["enabled"] = enabled
            
            status = "enabled" if enabled else "disabled"
            logger.info(f"Test signal system {status}")
            
            return {
                "status": "success",
                "message": f"Test signal system {status}"
            }
            
        except Exception as e:
            logger.error(f"Error toggling system: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def set_debug_mode(self, enabled: bool) -> Dict[str, str]:
        """Enable or disable debug mode"""
        try:
            if enabled:
                enable_debug_mode()
                message = "Debug mode enabled - test signals will be more frequent"
            else:
                disable_debug_mode()
                message = "Debug mode disabled - normal frequency restored"
            
            # Update the test system's config
            self.test_system.config = get_test_signal_config()
            
            # Recalculate next signal time if enabling debug
            if enabled:
                self.test_system.next_signal_time = datetime.now() + timedelta(hours=0.5)
            
            logger.info(message)
            
            return {
                "status": "success",
                "message": message
            }
            
        except Exception as e:
            logger.error(f"Error setting debug mode: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def force_test_signal(self, target_user_id: Optional[str] = None) -> Dict[str, Any]:
        """Force generate a test signal (admin only)"""
        try:
            # Create a mock base signal
            base_signal = {
                "signal_id": f"ADMIN_TEST_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "pair": "EURUSD",
                "action": "BUY",
                "entry": 1.0850,
                "sl": 1.0790,  # Will be modified to 60 pips
                "tp": 1.0870,
                "confidence": 75,
                "tier": "nibbler",
                "timestamp": datetime.now(),
                "metadata": {}
            }
            
            # Force generation
            old_next_time = self.test_system.next_signal_time
            self.test_system.next_signal_time = datetime.now() - timedelta(seconds=1)
            
            test_signal = self.test_system.generate_test_signal(base_signal)
            
            if test_signal:
                result = {
                    "status": "success",
                    "message": "Test signal generated",
                    "signal": {
                        "id": test_signal["test_signal_id"],
                        "pair": test_signal["pair"],
                        "sl_distance": test_signal["tcs_distance"],
                        "risk_reward": test_signal["risk_reward_ratio"]
                    }
                }
                
                # If target user specified, mark as sent
                if target_user_id:
                    self.test_system.record_signal_sent(
                        test_signal["test_signal_id"],
                        target_user_id
                    )
                    result["target_user"] = target_user_id
                
                return result
            else:
                # Restore next signal time
                self.test_system.next_signal_time = old_next_time
                return {
                    "status": "error",
                    "message": "Failed to generate test signal"
                }
                
        except Exception as e:
            logger.error(f"Error forcing test signal: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def get_user_details(self, user_id: str) -> Dict[str, Any]:
        """Get detailed test signal stats for a specific user"""
        try:
            stats = self.test_system.get_user_stats(user_id)
            
            if not stats["has_received_test_signals"]:
                return {
                    "user_id": user_id,
                    "status": "no_data",
                    "message": "User has not received any test signals"
                }
            
            user_stats = stats["stats"]
            
            # Get user's signal history
            user_signals = []
            for signal in self.test_system.signal_history:
                if user_id in signal.users_sent:
                    result = signal.results.get(user_id, "pending")
                    action = signal.user_actions.get(user_id, {})
                    
                    user_signals.append({
                        "signal_id": signal.signal_id,
                        "timestamp": signal.timestamp.isoformat(),
                        "pair": signal.pair,
                        "result": result.value if hasattr(result, 'value') else str(result),
                        "action": action.get("action", "unknown"),
                        "rewards": action.get("rewards", {})
                    })
            
            return {
                "user_id": user_id,
                "status": "active",
                "statistics": user_stats,
                "signal_history": user_signals[-10:],  # Last 10 signals
                "performance_grade": self._calculate_grade(user_stats),
                "recommendations": self._get_recommendations(user_stats)
            }
            
        except Exception as e:
            logger.error(f"Error getting user details: {e}")
            return {
                "user_id": user_id,
                "status": "error",
                "message": str(e)
            }
    
    def _calculate_grade(self, stats: Dict) -> str:
        """Calculate performance grade"""
        if stats["total_received"] < 3:
            return "Not enough data"
        
        pass_rate = stats["pass_rate"]
        attention = stats["attention_score"]
        
        score = (pass_rate * 0.7) + (attention * 0.3)
        
        if score >= 90:
            return "A+ (Expert Detector)"
        elif score >= 80:
            return "A (Sharp Eye)"
        elif score >= 70:
            return "B (Good Awareness)"
        elif score >= 60:
            return "C (Average)"
        elif score >= 50:
            return "D (Needs Improvement)"
        else:
            return "F (Frequently Baited)"
    
    def _get_recommendations(self, stats: Dict) -> List[str]:
        """Get personalized recommendations"""
        recommendations = []
        
        if stats["pass_rate"] < 50:
            recommendations.append("Focus on checking SL distance - 60 pips is a red flag!")
        
        if stats["attention_score"] < 70:
            recommendations.append("Pay closer attention to signal parameters before trading")
        
        if stats["total_taken"] > stats["total_passed"]:
            recommendations.append("Be more selective - not every signal is worth taking")
        
        if stats["total_won"] == 0 and stats["total_taken"] > 2:
            recommendations.append("Even with 30% win chance, you haven't won yet. Consider passing more often!")
        
        return recommendations
    
    async def export_data(self, format: str = "json") -> Dict[str, Any]:
        """Export test signal data for analysis"""
        try:
            data = {
                "export_date": datetime.now().isoformat(),
                "config": get_test_signal_config(),
                "summary": self.integration.get_test_signal_summary(),
                "signal_history": [
                    {
                        "signal_id": s.signal_id,
                        "timestamp": s.timestamp.isoformat(),
                        "pair": s.pair,
                        "users_sent": s.users_sent,
                        "results": {k: v.value for k, v in s.results.items()},
                        "actions": s.user_actions
                    }
                    for s in self.test_system.signal_history
                ],
                "user_statistics": {
                    user_id: {
                        "total_received": stats.total_received,
                        "total_passed": stats.total_passed,
                        "total_taken": stats.total_taken,
                        "total_won": stats.total_won,
                        "total_hit_sl": stats.total_hit_sl,
                        "attention_score": stats.attention_score,
                        "xp_earned": stats.xp_bonuses_earned,
                        "extra_shots": stats.extra_shots_earned
                    }
                    for user_id, stats in self.test_system.user_stats.items()
                }
            }
            
            if format == "json":
                return {
                    "status": "success",
                    "data": data
                }
            else:
                return {
                    "status": "error",
                    "message": f"Unsupported format: {format}"
                }
                
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return {
                "status": "error",
                "message": str(e)
            }


# Create global admin instance
test_signal_admin = TestSignalAdmin()


# Admin command handlers for Telegram
async def handle_admin_test_overview(update, context):
    """Admin command: /admin_test_overview"""
    overview = await test_signal_admin.get_system_overview()
    
    message = f"""📊 **Test Signal System Overview**

**Status:** {overview.get('status', 'Unknown')}
**Debug Mode:** {'ON' if overview.get('debug_mode') else 'OFF'}

**Configuration:**
• Frequency: {overview['config']['frequency']}
• Max per week: {overview['config']['max_per_week']}
• User selection: {overview['config']['user_selection']}

**Recent Activity:**
• Signals (7d): {overview['recent_activity']['signals_last_7_days']}
• Detection rate: {overview['recent_activity']['detection_rate']}
• Next signal: {overview['recent_activity']['next_signal']}

Use /admin_test_toggle to enable/disable
Use /admin_test_debug to toggle debug mode"""
    
    return message


async def handle_admin_test_toggle(update, context):
    """Admin command: /admin_test_toggle"""
    current = get_test_signal_config()["enabled"]
    result = await test_signal_admin.toggle_system(not current)
    return f"✅ {result['message']}"


async def handle_admin_test_debug(update, context):
    """Admin command: /admin_test_debug"""
    current = get_test_signal_config()["debug_mode"]
    result = await test_signal_admin.set_debug_mode(not current)
    return f"🔧 {result['message']}"