"""
Daily End-of-Day Drill Report System
Emotional reinforcement and habit formation through military-style daily summaries
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DrillTone(Enum):
    """Different drill sergeant tones based on performance"""
    OUTSTANDING = "outstanding"    # 80%+ win rate, 4+ trades
    SOLID = "solid"               # 60-79% win rate or 2-3 trades
    DECENT = "decent"             # 40-59% win rate or 1 trade
    ROUGH = "rough"               # <40% win rate or 0 trades
    COMEBACK = "comeback"         # Improved from yesterday


@dataclass
class DailyTradingStats:
    """Daily trading performance statistics"""
    user_id: str
    date: str
    trades_taken: int
    wins: int
    losses: int
    net_pnl_percent: float
    strategy_used: str
    xp_gained: int
    shots_remaining: int
    max_shots: int
    consecutive_wins: int
    consecutive_losses: int
    best_trade_pnl: float
    worst_trade_pnl: float
    total_pips: int
    
    @property
    def win_rate(self) -> float:
        """Calculate win rate percentage"""
        if self.trades_taken == 0:
            return 0.0
        return (self.wins / self.trades_taken) * 100
    
    @property
    def shots_used_percent(self) -> float:
        """Calculate percentage of shots used"""
        if self.max_shots == 0:
            return 0.0
        return ((self.max_shots - self.shots_remaining) / self.max_shots) * 100


@dataclass
class DrillMessage:
    """Drill sergeant message components"""
    header: str
    stats_summary: str
    performance_comment: str
    motivational_line: str
    tomorrow_guidance: str
    rank_progress: Optional[str] = None
    achievements_unlocked: List[str] = field(default_factory=list)


class DailyDrillReportSystem:
    """Daily End-of-Day Drill Report System"""
    
    # Drill sergeant responses by performance tone
    DRILL_RESPONSES = {
        DrillTone.OUTSTANDING: {
            "headers": [
                "🎖️ EXCEPTIONAL PERFORMANCE REPORT",
                "⭐ ELITE OPERATOR STATUS",
                "🏆 OUTSTANDING EXECUTION REPORT",
                "🔥 SUPERIOR COMBAT REPORT"
            ],
            "comments": [
                "Outstanding work, soldier! You executed with precision and discipline.",
                "This is what elite trading looks like. You're setting the standard.",
                "Flawless execution. Your tactical skills are razor sharp.",
                "You dominated the markets today. This is military-grade performance.",
                "Exceptional shot placement. You're operating like a true professional."
            ],
            "motivational": [
                "You're proving you belong with the elite. Keep this momentum.",
                "This is the path to greatness. Stay focused, stay disciplined.",
                "You're building something special here. Excellence is becoming habit.",
                "The markets respect discipline. You showed them who's in charge.",
                "This is what separates the pros from amateurs. Well done."
            ]
        },
        
        DrillTone.SOLID: {
            "headers": [
                "✅ SOLID PERFORMANCE REPORT",
                "💪 STRONG EXECUTION REPORT",
                "🎯 GOOD TACTICAL REPORT",
                "⚡ STEADY PROGRESS REPORT"
            ],
            "comments": [
                "Solid execution today. You followed your tactical plan well.",
                "Good discipline on shot selection. You're learning the game.",
                "Strong performance. You're building the right habits.",
                "Nice work staying within your tactical framework.",
                "You executed your strategy with good discipline today."
            ],
            "motivational": [
                "Consistency builds champions. Keep grinding, soldier.",
                "Every solid day builds toward greatness. Stay the course.",
                "You're developing real trading muscle. Keep pushing.",
                "Good traders make it look easy because they do the work.",
                "Progress over perfection. You're on the right track."
            ]
        },
        
        DrillTone.DECENT: {
            "headers": [
                "📊 MIXED RESULTS REPORT",
                "⚖️ LEARNING DAY REPORT",
                "🎯 DEVELOPMENT REPORT",
                "📈 PROGRESS REPORT"
            ],
            "comments": [
                "Mixed results today, but you stayed disciplined with your strategy.",
                "The markets tested you today. You held your ground.",
                "Some wins, some lessons. That's how traders develop.",
                "You followed your tactical plan. Results will follow discipline.",
                "Decent execution under challenging conditions."
            ],
            "motivational": [
                "Every trader faces days like this. Champions learn and adapt.",
                "The market doesn't always cooperate. Your discipline is building character.",
                "Rough days make strong traders. You're getting tougher.",
                "Focus on process, not just profit. You're building something bigger.",
                "Tomorrow is a new battlefield. Rest up and reload."
            ]
        },
        
        DrillTone.ROUGH: {
            "headers": [
                "⚠️ CHALLENGING DAY REPORT",
                "🛡️ BATTLE DAMAGE REPORT",
                "📝 LEARNING OPPORTUNITY REPORT",
                "🔄 RESET AND RELOAD REPORT"
            ],
            "comments": [
                "Tough day in the markets, soldier. Even elite units take hits.",
                "The markets gave you a beating today. Time to analyze and adapt.",
                "Rough trading day. Your risk management kept you in the fight.",
                "Markets were hostile today. You lived to fight another day.",
                "Hard lessons today. This is how professionals get forged."
            ],
            "motivational": [
                "Champions are made in moments like this. Come back stronger.",
                "Every pro has days like this. What matters is how you respond.",
                "This is temporary. Your commitment to improvement is permanent.",
                "Use this fuel for tomorrow. The best traders learn from pain.",
                "You're still standing. That means you can still fight."
            ]
        },
        
        DrillTone.COMEBACK: {
            "headers": [
                "🔄 COMEBACK PERFORMANCE REPORT",
                "⬆️ IMPROVEMENT REPORT",
                "💥 BOUNCE-BACK REPORT",
                "🎯 REDEMPTION REPORT"
            ],
            "comments": [
                "Much better execution than yesterday. You're learning and adapting.",
                "Nice bounce-back from yesterday's challenges. This is growth.",
                "You turned it around today. This is what resilience looks like.",
                "Solid improvement from yesterday. You're building momentum.",
                "Good recovery today. You're showing real character."
            ],
            "motivational": [
                "This is how champions respond to setbacks. Keep climbing.",
                "You proved you can adapt and improve. That's a rare skill.",
                "Comeback stories are the best stories. You're writing yours.",
                "This turnaround shows your true potential. Keep pushing.",
                "Every setback is setup for a comeback. You're proving it."
            ]
        }
    }
    
    # Tomorrow guidance by performance
    TOMORROW_GUIDANCE = {
        DrillTone.OUTSTANDING: [
            "Tomorrow: Maintain this level of execution. Don't get cocky.",
            "Tomorrow: Keep the same tactical approach. Consistency wins wars.",
            "Tomorrow: Stay humble, stay hungry. The market never sleeps.",
            "Tomorrow: This performance is your new standard. Protect it.",
            "Tomorrow: Build on this momentum. Excellence demands consistency."
        ],
        
        DrillTone.SOLID: [
            "Tomorrow: Look for opportunities to increase shot quality.",
            "Tomorrow: Same strategy, maybe tighten your shot selection.",
            "Tomorrow: Build on today's discipline. Small improvements compound.",
            "Tomorrow: Consider waiting for higher TCS signals if available.",
            "Tomorrow: Keep this steady approach. Consistency beats intensity."
        ],
        
        DrillTone.DECENT: [
            "Tomorrow: Focus on shot quality over quantity.",
            "Tomorrow: Review today's trades. What patterns do you see?",
            "Tomorrow: Stick to your tactical plan. Trust the process.",
            "Tomorrow: Wait for cleaner setups. Patience is a weapon.",
            "Tomorrow: Same strategy, tighter execution. You've got this."
        ],
        
        DrillTone.ROUGH: [
            "Tomorrow: Fresh start, same tactical discipline. Reload and reset.",
            "Tomorrow: Smaller position sizes until you find your rhythm again.",
            "Tomorrow: Focus on one perfect trade rather than many shots.",
            "Tomorrow: Review what went wrong, then let it go. Forward march.",
            "Tomorrow: The markets are waiting for your comeback. Show them."
        ],
        
        DrillTone.COMEBACK: [
            "Tomorrow: Keep this momentum going. You've found your groove.",
            "Tomorrow: Same energy, same focus. You're trending upward.",
            "Tomorrow: Build on this turnaround. Momentum is everything.",
            "Tomorrow: You've proven you can adapt. Keep evolving.",
            "Tomorrow: This is your real level. Prove it again."
        ]
    }
    
    def __init__(self, db_path: str = "data/drill_reports.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize drill report database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Daily trading stats
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_trading_stats (
                user_id TEXT,
                date TEXT,
                trades_taken INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                net_pnl_percent REAL DEFAULT 0.0,
                strategy_used TEXT,
                xp_gained INTEGER DEFAULT 0,
                shots_remaining INTEGER DEFAULT 0,
                max_shots INTEGER DEFAULT 0,
                consecutive_wins INTEGER DEFAULT 0,
                consecutive_losses INTEGER DEFAULT 0,
                best_trade_pnl REAL DEFAULT 0.0,
                worst_trade_pnl REAL DEFAULT 0.0,
                total_pips INTEGER DEFAULT 0,
                drill_tone TEXT,
                report_sent BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, date)
            )
        ''')
        
        # Drill report history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drill_report_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                date TEXT,
                report_content TEXT,
                tone TEXT,
                engagement_score REAL DEFAULT 0.0,
                user_reaction TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # User drill preferences
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drill_preferences (
                user_id TEXT PRIMARY KEY,
                preferred_time TEXT DEFAULT '18:00',  -- 6 PM default
                timezone TEXT DEFAULT 'UTC',
                tone_preference TEXT DEFAULT 'balanced',  -- harsh, balanced, encouraging
                include_comparisons BOOLEAN DEFAULT 1,
                include_tomorrow_guidance BOOLEAN DEFAULT 1,
                report_enabled BOOLEAN DEFAULT 1,
                streak_notifications BOOLEAN DEFAULT 1
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def record_daily_stats(self, user_id: str, stats: DailyTradingStats) -> bool:
        """Record daily trading statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO daily_trading_stats 
                (user_id, date, trades_taken, wins, losses, net_pnl_percent, strategy_used,
                 xp_gained, shots_remaining, max_shots, consecutive_wins, consecutive_losses,
                 best_trade_pnl, worst_trade_pnl, total_pips)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                stats.user_id, stats.date, stats.trades_taken, stats.wins, stats.losses,
                stats.net_pnl_percent, stats.strategy_used, stats.xp_gained,
                stats.shots_remaining, stats.max_shots, stats.consecutive_wins,
                stats.consecutive_losses, stats.best_trade_pnl, stats.worst_trade_pnl,
                stats.total_pips
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error recording daily stats: {e}")
            return False
        finally:
            conn.close()
    
    def generate_drill_report(self, user_id: str, date: str = None) -> DrillMessage:
        """Generate drill sergeant report for user"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # Get today's stats
        today_stats = self._get_daily_stats(user_id, date)
        if not today_stats:
            return self._generate_no_action_report(user_id, date)
        
        # Get yesterday's stats for comparison
        yesterday = (datetime.strptime(date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
        yesterday_stats = self._get_daily_stats(user_id, yesterday)
        
        # Determine drill tone
        drill_tone = self._determine_drill_tone(today_stats, yesterday_stats)
        
        # Generate message components
        import random
        
        responses = self.DRILL_RESPONSES[drill_tone]
        header = random.choice(responses["headers"])
        comment = random.choice(responses["comments"])
        motivational = random.choice(responses["motivational"])
        tomorrow = random.choice(self.TOMORROW_GUIDANCE[drill_tone])
        
        # Build stats summary
        stats_summary = self._build_stats_summary(today_stats)
        
        # Check for rank progress
        rank_progress = self._check_rank_progress(user_id, today_stats)
        
        # Check for achievements
        achievements = self._check_daily_achievements(user_id, today_stats)
        
        return DrillMessage(
            header=header,
            stats_summary=stats_summary,
            performance_comment=comment,
            motivational_line=motivational,
            tomorrow_guidance=tomorrow,
            rank_progress=rank_progress,
            achievements_unlocked=achievements
        )
    
    def _get_daily_stats(self, user_id: str, date: str) -> Optional[DailyTradingStats]:
        """Get daily trading stats for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM daily_trading_stats 
            WHERE user_id = ? AND date = ?
        ''', (user_id, date))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return DailyTradingStats(
            user_id=row[0], date=row[1], trades_taken=row[2], wins=row[3],
            losses=row[4], net_pnl_percent=row[5], strategy_used=row[6],
            xp_gained=row[7], shots_remaining=row[8], max_shots=row[9],
            consecutive_wins=row[10], consecutive_losses=row[11],
            best_trade_pnl=row[12], worst_trade_pnl=row[13], total_pips=row[14]
        )
    
    def _determine_drill_tone(self, today: DailyTradingStats, yesterday: Optional[DailyTradingStats]) -> DrillTone:
        """Determine appropriate drill sergeant tone"""
        
        # Check for comeback pattern
        if yesterday and today.win_rate > yesterday.win_rate + 20:
            return DrillTone.COMEBACK
        
        # No trades taken
        if today.trades_taken == 0:
            return DrillTone.ROUGH
        
        # Performance-based tones
        if today.win_rate >= 80 and today.trades_taken >= 4:
            return DrillTone.OUTSTANDING
        elif today.win_rate >= 60 and today.trades_taken >= 2:
            return DrillTone.SOLID
        elif today.win_rate >= 40 or (today.trades_taken >= 1 and today.win_rate > 0):
            return DrillTone.DECENT
        else:
            return DrillTone.ROUGH
    
    def _build_stats_summary(self, stats: DailyTradingStats) -> str:
        """Build formatted stats summary"""
        strategy_emoji = {
            "LONE_WOLF": "🐺",
            "FIRST_BLOOD": "🎯", 
            "DOUBLE_TAP": "💥",
            "TACTICAL_COMMAND": "⚡"
        }
        
        emoji = strategy_emoji.get(stats.strategy_used, "🎯")
        
        summary = f"""💥 Trades Taken: {stats.trades_taken}
✅ Wins: {stats.wins}  ❌ Losses: {stats.losses}
📈 Net Gain: {stats.net_pnl_percent:+.1f}%
🧠 Tactic Used: {emoji} {stats.strategy_used.replace('_', ' ').title()}
🔓 XP Gained: +{stats.xp_gained}"""
        
        if stats.shots_remaining > 0:
            summary += f"\n🎯 Shots Remaining: {stats.shots_remaining}/{stats.max_shots}"
        
        if stats.total_pips != 0:
            summary += f"\n📊 Total Pips: {stats.total_pips:+d}"
        
        return summary
    
    def _generate_no_action_report(self, user_id: str, date: str) -> DrillMessage:
        """Generate report when no trades were taken"""
        header = "⚠️ NO CONTACT REPORT"
        stats_summary = "💥 Trades Taken: 0\n🎯 Strategy: Not Selected\n🔓 XP Gained: 0"
        comment = "No shots fired today, soldier. The market was there, but you weren't."
        motivational = "Every day you don't trade is a day your competition gains ground."
        tomorrow = "Tomorrow: Select your tactical strategy and engage the enemy."
        
        return DrillMessage(
            header=header,
            stats_summary=stats_summary,
            performance_comment=comment,
            motivational_line=motivational,
            tomorrow_guidance=tomorrow
        )
    
    def _check_rank_progress(self, user_id: str, stats: DailyTradingStats) -> Optional[str]:
        """Check if user made progress toward next rank"""
        # This would integrate with XP economy to check progress
        # For now, return None - will integrate with existing XP system
        return None
    
    def _check_daily_achievements(self, user_id: str, stats: DailyTradingStats) -> List[str]:
        """Check for daily achievements unlocked"""
        achievements = []
        
        if stats.win_rate == 100 and stats.trades_taken >= 3:
            achievements.append("🏆 Perfect Day - 100% Win Rate")
        
        if stats.trades_taken >= 5:
            achievements.append("🔥 High Volume - 5+ Trades")
        
        if stats.net_pnl_percent >= 10:
            achievements.append("💰 Big Gains - 10%+ Daily Return")
        
        if stats.consecutive_wins >= 3:
            achievements.append("🎯 Hot Streak - 3+ Consecutive Wins")
        
        return achievements
    
    def format_telegram_report(self, drill_message: DrillMessage, user_id: str) -> str:
        """Format drill report for Telegram delivery"""
        date_str = datetime.now().strftime("%B %d").upper()
        
        report = f"""🪖 DRILL REPORT: {date_str}

{drill_message.stats_summary}

"{drill_message.performance_comment}"

{drill_message.motivational_line}

{drill_message.tomorrow_guidance}"""
        
        if drill_message.rank_progress:
            report += f"\n\n🏆 {drill_message.rank_progress}"
        
        if drill_message.achievements_unlocked:
            report += f"\n\n🎖️ ACHIEVEMENTS:\n" + "\n".join(drill_message.achievements_unlocked)
        
        report += "\n\n— DRILL SERGEANT 🎖️"
        
        return report
    
    def send_daily_reports(self, telegram_bot) -> int:
        """Send daily reports to all users (called by scheduler)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get users who need reports
        cursor.execute('''
            SELECT DISTINCT user_id FROM daily_trading_stats 
            WHERE date = ? AND report_sent = 0
        ''', (datetime.now().strftime('%Y-%m-%d'),))
        
        users = cursor.fetchall()
        reports_sent = 0
        
        for (user_id,) in users:
            try:
                drill_message = self.generate_drill_report(user_id)
                telegram_report = self.format_telegram_report(drill_message, user_id)
                
                # Send via telegram bot
                telegram_bot.send_message(user_id, telegram_report, parse_mode='HTML')
                
                # Mark as sent
                cursor.execute('''
                    UPDATE daily_trading_stats 
                    SET report_sent = 1 
                    WHERE user_id = ? AND date = ?
                ''', (user_id, datetime.now().strftime('%Y-%m-%d')))
                
                reports_sent += 1
                
            except Exception as e:
                logger.error(f"Error sending drill report to {user_id}: {e}")
        
        conn.commit()
        conn.close()
        
        return reports_sent
    
    def get_weekly_summary(self, user_id: str) -> Dict[str, Any]:
        """Get weekly performance summary"""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as days_active,
                SUM(trades_taken) as total_trades,
                SUM(wins) as total_wins,
                SUM(losses) as total_losses,
                AVG(net_pnl_percent) as avg_daily_return,
                SUM(xp_gained) as total_xp,
                MAX(consecutive_wins) as best_streak
            FROM daily_trading_stats 
            WHERE user_id = ? AND date BETWEEN ? AND ?
        ''', (user_id, start_date, end_date))
        
        stats = cursor.fetchone()
        conn.close()
        
        if not stats or stats[0] == 0:
            return {"error": "No trading activity this week"}
        
        return {
            "days_active": stats[0],
            "total_trades": stats[1] or 0,
            "total_wins": stats[2] or 0,
            "total_losses": stats[3] or 0,
            "win_rate": (stats[2] / stats[1] * 100) if stats[1] > 0 else 0,
            "avg_daily_return": round(stats[4] or 0, 2),
            "total_xp": stats[5] or 0,
            "best_streak": stats[6] or 0
        }


# Integration with existing tactical strategy system
def integrate_with_tactical_system(tactical_manager, drill_system):
    """Integration point with tactical strategy manager"""
    
    def record_trade_result(user_id: str, trade_result: Dict[str, Any]):
        """Called when a trade completes"""
        
        # Get user's daily state
        daily_state = tactical_manager.get_daily_state(user_id)
        
        # Build daily stats
        today = datetime.now().strftime('%Y-%m-%d')
        
        # This would be called at end of day or after each trade
        stats = DailyTradingStats(
            user_id=user_id,
            date=today,
            trades_taken=daily_state.shots_fired,
            wins=daily_state.wins_today,
            losses=daily_state.losses_today,
            net_pnl_percent=daily_state.daily_pnl,
            strategy_used=daily_state.selected_strategy.value if daily_state.selected_strategy else "NONE",
            xp_gained=trade_result.get('xp_gained', 0),
            shots_remaining=tactical_manager.TACTICAL_CONFIGS[daily_state.selected_strategy].max_shots - daily_state.shots_fired if daily_state.selected_strategy else 0,
            max_shots=tactical_manager.TACTICAL_CONFIGS[daily_state.selected_strategy].max_shots if daily_state.selected_strategy else 0,
            consecutive_wins=0,  # Would track this in tactical manager
            consecutive_losses=0,  # Would track this in tactical manager
            best_trade_pnl=trade_result.get('pnl_percent', 0),
            worst_trade_pnl=trade_result.get('pnl_percent', 0),
            total_pips=trade_result.get('pips', 0)
        )
        
        drill_system.record_daily_stats(user_id, stats)
    
    return record_trade_result


# Example usage
if __name__ == "__main__":
    drill_system = DailyDrillReportSystem()
    
    # Example daily stats
    stats = DailyTradingStats(
        user_id="test_user",
        date="2025-07-22",
        trades_taken=4,
        wins=3,
        losses=1,
        net_pnl_percent=6.1,
        strategy_used="FIRST_BLOOD",
        xp_gained=10,
        shots_remaining=0,
        max_shots=4,
        consecutive_wins=2,
        consecutive_losses=0,
        best_trade_pnl=3.2,
        worst_trade_pnl=-1.1,
        total_pips=45
    )
    
    # Record stats and generate report
    drill_system.record_daily_stats("test_user", stats)
    drill_message = drill_system.generate_drill_report("test_user")
    
    # Format for Telegram
    telegram_report = drill_system.format_telegram_report(drill_message, "test_user")
    print("=== SAMPLE DRILL REPORT ===")
    print(telegram_report)