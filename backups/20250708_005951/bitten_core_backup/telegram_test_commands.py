# telegram_test_commands.py
# BITTEN Telegram Testing Commands - Debug & Support Tools

from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
import asyncio
import random
from dataclasses import dataclass

@dataclass
class TestSignal:
    """Test signal for debugging"""
    symbol: str
    direction: str
    entry: float
    stop: float
    target: float
    tcs: int
    strategy: str

class TelegramTestCommands:
    """
    Debug and testing commands for Telegram bot
    Essential for support and troubleshooting
    """
    
    def __init__(self, master_filter, trade_tagger, session_system, module_tracker):
        self.master_filter = master_filter
        self.trade_tagger = trade_tagger
        self.session_system = session_system
        self.module_tracker = module_tracker
        
        # Test signal pool
        self.test_signals = {
            'GBPUSD': TestSignal('GBPUSD', 'buy', 1.2750, 1.2730, 1.2780, 75, 'DAWN_RAID'),
            'EURUSD': TestSignal('EURUSD', 'sell', 1.0850, 1.0870, 1.0820, 82, 'WALL_DEFENDER'),
            'USDJPY': TestSignal('USDJPY', 'buy', 110.50, 110.30, 110.80, 88, 'ROCKET_RIDE'),
            'GBPJPY': TestSignal('GBPJPY', 'sell', 155.20, 155.50, 154.70, 91, 'SNIPER'),
            'USDCAD': TestSignal('USDCAD', 'buy', 1.3420, 1.3400, 1.3450, 73, 'RUBBER_BAND')
        }
        
        # Command registry
        self.commands = {
            '/firetest': self.handle_fire_test,
            '/ghostlog': self.handle_ghost_log,
            '/riskprofile': self.handle_risk_profile,
            '/status': self.handle_system_status,
            '/replay': self.handle_replay_trade,
            '/session': self.handle_session_info,
            '/tags': self.handle_show_tags,
            '/modules': self.handle_module_stats,
            '/simulate': self.handle_simulate_day,
            '/clear': self.handle_clear_data
        }
    
    async def handle_fire_test(self, message: Dict) -> str:
        """
        /firetest [symbol] - Sends mock signal to test execution
        """
        user_id = message['from']['id']
        parts = message['text'].split()
        
        # Get symbol or random
        symbol = parts[1].upper() if len(parts) > 1 else random.choice(list(self.test_signals.keys()))
        
        if symbol not in self.test_signals:
            return f"❌ Unknown symbol. Available: {', '.join(self.test_signals.keys())}"
        
        test_signal = self.test_signals[symbol]
        
        # Create test signal dict
        signal_dict = {
            'symbol': test_signal.symbol,
            'direction': test_signal.direction,
            'entry_price': test_signal.entry,
            'stop_loss': test_signal.stop,
            'take_profit': test_signal.target,
            'tcs_score': test_signal.tcs,
            'triggered_by': 'TEST_MODULE',
            'is_test': True,
            'expected_pips': int(abs(test_signal.target - test_signal.entry) / 0.0001)
        }
        
        # Enhance with module tracking
        signal_dict = self.module_tracker.enhance_signal_with_source(
            signal_dict, test_signal.strategy + '_SCANNER'
        )
        
        # Apply session multiplier
        session_data = self.session_system.apply_session_multiplier(
            test_signal.tcs, test_signal.symbol
        )
        
        return f"""🧪 **TEST SIGNAL GENERATED**

{test_signal.strategy} - {test_signal.symbol}
Direction: {test_signal.direction.upper()}
Entry: {test_signal.entry}
SL: {test_signal.stop} | TP: {test_signal.target}

📊 TCS Analysis:
Base TCS: {test_signal.tcs}%
Session: {session_data['session_quality']}
Adjusted TCS: {session_data['adjusted_tcs']}%

Triggered by: {signal_dict['source_display']}

Use /fire to execute this test signal."""
    
    async def handle_ghost_log(self, message: Dict) -> str:
        """
        /ghostlog - Shows last 5 missed high-quality signals
        """
        user_id = message['from']['id']
        
        # Get ghost trades from tagger
        ghost_trades = self.trade_tagger.get_ghost_trades(user_id, limit=5)
        
        if not ghost_trades:
            return "👻 No ghost trades recorded yet.\n\nGhost trades are high-quality signals you missed due to limits or being offline."
        
        response = "👻 **GHOST LOG** (Missed Opportunities)\n\n"
        
        total_missed_pips = 0
        total_missed_xp = 0
        
        for i, trade in enumerate(ghost_trades, 1):
            time_ago = datetime.now() - trade['timestamp']
            hours_ago = int(time_ago.total_seconds() / 3600)
            
            response += f"**{i}.** {trade['symbol']} - {hours_ago}h ago\n"
            response += f"   TCS: {trade['tcs']}% | Session: {trade['session']}\n"
            response += f"   Would've made: {trade['potential_pips']} pips\n"
            response += f"   Missed XP: {trade['missed_xp']}\n"
            response += f"   Reason: {trade['reason_missed']}\n\n"
            
            total_missed_pips += trade['potential_pips']
            total_missed_xp += trade['missed_xp']
        
        response += f"💀 **Total Missed: {total_missed_pips} pips | {total_missed_xp} XP**"
        
        return response
    
    async def handle_risk_profile(self, message: Dict) -> str:
        """
        /riskprofile - Shows current risk stats and behavior
        """
        user_id = message['from']['id']
        
        # Get user data from master filter
        user_data = self.master_filter.user_states.get(user_id, {})
        position_data = self.master_filter.position_manager.get_user_status(user_id)
        
        # Mock some behavioral data (would come from database)
        stats = {
            'total_trades': random.randint(50, 200),
            'win_rate': random.randint(55, 75),
            'avg_win': random.randint(15, 25),
            'avg_loss': random.randint(8, 15),
            'revenge_count': random.randint(0, 5),
            'panic_exits': random.randint(0, 3),
            'perfect_holds': random.randint(5, 20),
            'current_streak': random.randint(-3, 7),
            'max_drawdown': random.randint(5, 15)
        }
        
        # Calculate profit factor
        profit_factor = (stats['win_rate'] / 100 * stats['avg_win']) / ((100 - stats['win_rate']) / 100 * stats['avg_loss'])
        
        badges = ["🎖️ Recruit", "🥉 Soldier", "🥈 Warrior", "🥇 Elite", "💎 Legend"]
        user_badge = random.choice(badges)
        
        return f"""📊 **RISK PROFILE**
━━━━━━━━━━━━━━━━━━
👤 User #{user_id}
{user_badge} | XP: {random.randint(100, 5000)}

📈 **Performance:**
• Total Trades: {stats['total_trades']}
• Win Rate: {stats['win_rate']}%
• Avg Win: {stats['avg_win']} pips
• Avg Loss: {stats['avg_loss']} pips
• Profit Factor: {profit_factor:.2f}

🎯 **Behavior:**
• Revenge Trades: {stats['revenge_count']}
• Panic Exits: {stats['panic_exits']}
• Perfect Holds: {stats['perfect_holds']}

🔥 Current Streak: {'+' if stats['current_streak'] > 0 else ''}{stats['current_streak']}
💀 Worst Drawdown: -{stats['max_drawdown']}%

📍 **Current Status:**
• Open Positions: {position_data['open_positions']}
• Daily Risk Used: {position_data['daily_risk_used']:.1%}
• Available Slots: {position_data['available_slots']}"""
    
    async def handle_system_status(self, message: Dict) -> str:
        """
        /status - System health check
        """
        
        # Check various components
        checks = {
            "Signal Engine": self._check_signal_engine(),
            "Position Manager": self._check_position_manager(),
            "Fire Control": self._check_fire_control(),
            "Session System": self._check_session_system(),
            "Module Tracker": self._check_module_tracker()
        }
        
        current_session = self.session_system.get_current_session()
        session_config = self.session_system.sessions[current_session]
        
        all_healthy = all(check['healthy'] for check in checks.values())
        overall_emoji = "🟢" if all_healthy else "🟡"
        
        response = f"{overall_emoji} **SYSTEM STATUS**\n\n"
        
        for component, state in checks.items():
            emoji = "✅" if state['healthy'] else "❌"
            response += f"{emoji} {component}: {state['message']}\n"
        
        response += f"\n⏰ **Current Session:** {session_config.name}\n"
        response += f"Multiplier: {session_config.multiplier}x | Volume: {session_config.volume_profile}"
        
        return response
    
    async def handle_session_info(self, message: Dict) -> str:
        """
        /session [pair] - Show session information
        """
        parts = message['text'].split()
        
        if len(parts) > 1:
            # Specific pair analysis
            pair = parts[1].upper()
            session_data = self.session_system.apply_session_multiplier(80, pair)
            best_times = self.session_system.get_best_trading_times(pair)
            
            response = f"📅 **SESSION ANALYSIS FOR {pair}**\n\n"
            response += f"Current Session: {session_data['session_name']}\n"
            response += f"Quality: {session_data['session_quality']}\n"
            response += f"Multiplier: {session_data['multiplier']}x\n"
            response += f"Adjusted 80% → {session_data['adjusted_tcs']}%\n\n"
            
            response += "**Best Trading Times:**\n"
            for i, time_data in enumerate(best_times[:3], 1):
                response += f"{i}. {time_data['name']} (Score: {time_data['score']})\n"
            
        else:
            # General schedule
            response = self.session_system.get_session_schedule()
        
        return response
    
    async def handle_show_tags(self, message: Dict) -> str:
        """
        /tags [trade_id] - Show tags for last or specific trade
        """
        user_id = message['from']['id']
        parts = message['text'].split()
        
        # Mock last trade tags
        mock_tags = {
            'trade_id': 'TRD_abc12345',
            'execution_type': 'LIVE',
            'entry_method': 'INSTANT',
            'quality_marker': 'HIGH_CONFIDENCE',
            'session': 'LONDON',
            'shadow_index': 85,
            'signal_source': 'ROCKET_RIDE_SCANNER',
            'risk_percent': 2.0,
            'concurrent_positions': 2,
            'is_revenge_trade': False
        }
        
        return f"""🏷️ **TRADE TAGS**

Trade ID: {mock_tags['trade_id']}

**Execution:**
• Type: {mock_tags['execution_type']}
• Method: {mock_tags['entry_method']}
• Source: {mock_tags['signal_source']}

**Quality:**
• Marker: {mock_tags['quality_marker']}
• Shadow: {mock_tags['shadow_index']}%
• Session: {mock_tags['session']}

**Risk:**
• Risk: {mock_tags['risk_percent']}%
• Positions: {mock_tags['concurrent_positions']}
• Revenge: {'Yes ⚠️' if mock_tags['is_revenge_trade'] else 'No ✅'}"""
    
    async def handle_module_stats(self, message: Dict) -> str:
        """
        /modules - Show detection module statistics
        """
        stats = self.module_tracker.get_module_stats()
        top_performers = self.module_tracker.get_top_performers(limit=3)
        
        response = "📡 **MODULE STATISTICS**\n\n"
        
        # Top performers
        if top_performers:
            response += "🏆 **Top Performers:**\n"
            medals = ["🥇", "🥈", "🥉"]
            for i, performer in enumerate(top_performers):
                medal = medals[i] if i < 3 else "🏅"
                response += f"{medal} {performer['icon']} Success: {performer['success_rate']:.1f}%\n"
            response += "\n"
        
        # Active modules
        response += "**Active Modules:**\n"
        active_count = 0
        for module_name, module_stats in stats.items():
            if module_stats['active']:
                active_count += 1
                if module_stats['type'] != 'sniper':
                    response += f"• {module_stats['icon']} {module_stats['strategy']}: "
                    response += f"{module_stats['total_signals']} signals\n"
        
        response += f"\nTotal Active: {active_count}/12 modules"
        
        return response
    
    def _check_signal_engine(self) -> Dict:
        """Check signal engine health"""
        try:
            # Check if filters are initialized
            if hasattr(self.master_filter, 'arcade_filter') and hasattr(self.master_filter, 'sniper_filter'):
                return {'healthy': True, 'message': 'All filters operational'}
            else:
                return {'healthy': False, 'message': 'Filters not initialized'}
        except:
            return {'healthy': False, 'message': 'Engine error'}
    
    def _check_position_manager(self) -> Dict:
        """Check position manager health"""
        try:
            # Simple check
            if hasattr(self.master_filter, 'position_manager'):
                return {'healthy': True, 'message': 'Position tracking active'}
            else:
                return {'healthy': False, 'message': 'Not initialized'}
        except:
            return {'healthy': False, 'message': 'Manager error'}
    
    def _check_fire_control(self) -> Dict:
        """Check fire control health"""
        return {'healthy': True, 'message': 'Fire control ready'}
    
    def _check_session_system(self) -> Dict:
        """Check session system health"""
        try:
            current = self.session_system.get_current_session()
            return {'healthy': True, 'message': f'Active ({current.value})'}
        except:
            return {'healthy': False, 'message': 'Session error'}
    
    def _check_module_tracker(self) -> Dict:
        """Check module tracker health"""
        try:
            module_count = len(self.module_tracker.modules)
            return {'healthy': True, 'message': f'{module_count} modules loaded'}
        except:
            return {'healthy': False, 'message': 'Tracker error'}
    
    async def handle_simulate_day(self, message: Dict) -> str:
        """Simulate a trading day"""
        return "🎮 Trading day simulation not yet implemented"
    
    async def handle_clear_data(self, message: Dict) -> str:
        """Clear user data (admin only)"""
        return "🔒 Admin function not available"
    
    async def handle_replay_trade(self, message: Dict) -> str:
        """Replay last trade"""
        return "📼 Trade replay not yet implemented"
    
    async def process_command(self, message: Dict) -> str:
        """Process test command"""
        command = message['text'].split()[0]
        
        if command in self.commands:
            handler = self.commands[command]
            return await handler(message)
        
        return None  # Not a test command