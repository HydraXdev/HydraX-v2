# webapp_router.py
# BITTEN WebApp Router - Handles WebApp routes and data flow

import json
import time
import hashlib
import hmac
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.parse import parse_qs, unquote

from .rank_access import RankAccess, UserRank
from .user_profile import UserProfileManager
from .mission_briefing_generator import MissionBriefingGenerator, MissionBriefing
from .signal_display import SignalDisplay
from .tier_lock_manager import TierLockManager

@dataclass
class WebAppRequest:
    """WebApp request structure"""
    user_id: int
    username: str
    view: str  # profile, mission_briefing, signals, leaderboard
    data: Dict[str, Any]
    timestamp: int
    auth_hash: str

class WebAppRouter:
    """Handles WebApp routing and data preparation for BITTEN HUD"""
    
    def __init__(self, bitten_core=None, webapp_secret: str = None):
        self.bitten_core = bitten_core
        self.rank_access = RankAccess()
        self.profile_manager = UserProfileManager()
        self.briefing_generator = MissionBriefingGenerator()
        self.signal_display = SignalDisplay()
        self.tier_manager = TierLockManager()
        self.webapp_secret = webapp_secret or "BITTEN_WEBAPP_SECRET_KEY"
        
        # View handlers
        self.view_handlers = {
            'profile': self._handle_profile_view,
            'mission_briefing': self._handle_mission_briefing_view,
            'signals': self._handle_signals_view,
            'leaderboard': self._handle_leaderboard_view,
            'achievements': self._handle_achievements_view,
            'recruitment': self._handle_recruitment_view,
            'settings': self._handle_settings_view,
            'update_settings': self._handle_update_settings
        }
        
        # Cache for webapp data
        self.webapp_cache = {}
        self.cache_ttl = 60  # 60 seconds cache
    
    def process_webapp_request(self, request_data: str) -> Dict[str, Any]:
        """Process incoming WebApp request"""
        try:
            # Parse request data
            parsed_data = self._parse_webapp_data(request_data)
            if not parsed_data:
                return self._error_response("Invalid request data")
            
            # Validate authentication
            if not self._validate_webapp_auth(parsed_data):
                return self._error_response("Authentication failed")
            
            # Create request object
            request = WebAppRequest(
                user_id=parsed_data.get('user_id', 0),
                username=parsed_data.get('username', 'unknown'),
                view=parsed_data.get('view', 'profile'),
                data=parsed_data.get('data', {}),
                timestamp=parsed_data.get('timestamp', int(time.time())),
                auth_hash=parsed_data.get('auth_hash', '')
            )
            
            # Check user permissions
            user_rank = self.rank_access.get_user_rank(request.user_id)
            if not self._check_view_permission(request.view, user_rank):
                return self._error_response("Access denied for this view")
            
            # Route to appropriate handler
            handler = self.view_handlers.get(request.view)
            if not handler:
                return self._error_response(f"Unknown view: {request.view}")
            
            # Process request
            response = handler(request)
            
            # Add common data
            response['user_rank'] = user_rank.name
            response['timestamp'] = int(time.time())
            response['version'] = "1.0.0"
            
            return response
            
        except Exception as e:
            return self._error_response(f"Processing error: {str(e)}")
    
    def _handle_profile_view(self, request: WebAppRequest) -> Dict[str, Any]:
        """Handle profile view request"""
        # Check cache
        cache_key = f"profile_{request.user_id}"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        # Get full profile
        profile = self.profile_manager.get_full_profile(request.user_id)
        
        # Get additional stats
        trading_stats = self._get_trading_stats(request.user_id)
        rank_progress = self._calculate_rank_progress(profile['total_xp'])
        
        # Build response
        response = {
            'success': True,
            'view': 'profile',
            'data': {
                'profile': profile,
                'trading_stats': trading_stats,
                'rank_progress': rank_progress,
                'achievements': {
                    'recent': self._get_recent_achievements(request.user_id),
                    'next_unlock': self._get_next_achievement(profile)
                },
                'recruitment': {
                    'link': f"https://t.me/BITTEN_bot?start=ref_{request.user_id}",
                    'qr_code': self._generate_qr_code_data(request.user_id),
                    'stats': profile.get('recruitment_stats', {})
                }
            }
        }
        
        # Cache response
        self._cache_data(cache_key, response)
        
        return response
    
    def _handle_mission_briefing_view(self, request: WebAppRequest) -> Dict[str, Any]:
        """Handle mission briefing view request"""
        mission_id = request.data.get('mission_id')
        if not mission_id:
            return self._error_response("Mission ID required")
        
        # Get mission briefing from telegram router cache
        if self.bitten_core and hasattr(self.bitten_core, 'telegram_router'):
            briefing = self.bitten_core.telegram_router.get_mission_briefing(mission_id)
        else:
            # Fallback: generate test briefing
            briefing = self._generate_test_briefing(mission_id)
        
        if not briefing:
            return self._error_response("Mission not found or expired")
        
        # Check tier access
        user_rank = self.rank_access.get_user_rank(request.user_id)
        tier_check = self.tier_manager.check_mission_access(
            user_rank.name, briefing.required_tier
        )
        
        if not tier_check['has_access']:
            # Return limited data for locked missions
            return {
                'success': True,
                'view': 'mission_briefing',
                'data': {
                    'locked': True,
                    'required_tier': briefing.required_tier,
                    'user_tier': user_rank.name,
                    'unlock_message': tier_check['message'],
                    'preview': {
                        'callsign': briefing.callsign,
                        'type': briefing.mission_type.value,
                        'urgency': briefing.urgency.value,
                        'symbol': briefing.symbol,
                        'blur_level': 'high'
                    }
                }
            }
        
        # Format briefing for webapp
        webapp_data = self.briefing_generator.format_for_webapp(briefing)
        
        # Add execution options
        webapp_data['execution_options'] = self._get_execution_options(
            briefing, user_rank.name
        )
        
        # Add market analysis
        webapp_data['market_analysis'] = self._get_market_analysis(briefing)
        
        return {
            'success': True,
            'view': 'mission_briefing',
            'data': webapp_data
        }
    
    def _handle_signals_view(self, request: WebAppRequest) -> Dict[str, Any]:
        """Handle signals list view request"""
        # Get active signals
        if self.bitten_core and hasattr(self.bitten_core, 'get_active_signals'):
            signals = self.bitten_core.get_active_signals(request.user_id)
        else:
            # Fallback: return empty or test signals
            signals = self._get_test_signals()
        
        # Filter by user tier
        user_rank = self.rank_access.get_user_rank(request.user_id)
        filtered_signals = self.tier_manager.filter_signals_by_tier(
            signals, user_rank.name
        )
        
        # Group signals by type
        grouped_signals = {
            'arcade': [],
            'sniper': [],
            'special': []
        }
        
        for signal in filtered_signals:
            signal_type = signal.get('type', 'arcade')
            if signal_type == 'sniper':
                grouped_signals['sniper'].append(signal)
            elif signal_type in ['midnight_hammer', 'chaingun']:
                grouped_signals['special'].append(signal)
            else:
                grouped_signals['arcade'].append(signal)
        
        return {
            'success': True,
            'view': 'signals',
            'data': {
                'signals': grouped_signals,
                'stats': {
                    'total_active': len(filtered_signals),
                    'your_positions': self._get_user_position_count(request.user_id),
                    'avg_tcs': self._calculate_avg_tcs(filtered_signals),
                    'hot_pairs': self._get_hot_pairs(filtered_signals)
                },
                'filters': request.data.get('filters', {})
            }
        }
    
    def _handle_leaderboard_view(self, request: WebAppRequest) -> Dict[str, Any]:
        """Handle leaderboard view request"""
        timeframe = request.data.get('timeframe', 'daily')
        metric = request.data.get('metric', 'profit')
        
        # Get leaderboard data
        leaderboard = self._get_leaderboard_data(timeframe, metric)
        
        # Get user's position
        user_position = self._get_user_leaderboard_position(
            request.user_id, timeframe, metric
        )
        
        return {
            'success': True,
            'view': 'leaderboard',
            'data': {
                'leaderboard': leaderboard,
                'user_position': user_position,
                'timeframe': timeframe,
                'metric': metric,
                'available_metrics': ['profit', 'pips', 'win_rate', 'xp', 'recruits'],
                'available_timeframes': ['daily', 'weekly', 'monthly', 'all_time']
            }
        }
    
    def _handle_achievements_view(self, request: WebAppRequest) -> Dict[str, Any]:
        """Handle achievements/medals view request"""
        # Get user medals
        medals = self.profile_manager.get_user_medals(request.user_id)
        
        # Group by tier
        grouped_medals = {
            'bronze': [],
            'silver': [],
            'gold': [],
            'platinum': []
        }
        
        for medal in medals:
            tier = medal.get('tier', 'bronze')
            grouped_medals[tier].append(medal)
        
        # Calculate progress
        total_medals = len(medals)
        earned_medals = sum(1 for m in medals if m.get('earned', False))
        
        return {
            'success': True,
            'view': 'achievements',
            'data': {
                'medals': grouped_medals,
                'stats': {
                    'total': total_medals,
                    'earned': earned_medals,
                    'completion_rate': (earned_medals / total_medals * 100) if total_medals > 0 else 0,
                    'total_xp_from_medals': sum(m.get('xp_reward', 0) for m in medals if m.get('earned', False))
                },
                'next_medals': self._get_next_achievable_medals(request.user_id, medals)
            }
        }
    
    def _handle_recruitment_view(self, request: WebAppRequest) -> Dict[str, Any]:
        """Handle recruitment center view request"""
        # Get recruitment stats
        recruit_stats = self.profile_manager.get_recruiting_stats(request.user_id)
        
        # Generate recruitment materials
        recruitment_link = f"https://t.me/BITTEN_bot?start=ref_{request.user_id}"
        
        # Create shareable content
        share_content = {
            'telegram': {
                'text': self._generate_recruitment_message(request.user_id, 'telegram'),
                'link': recruitment_link
            },
            'whatsapp': {
                'text': self._generate_recruitment_message(request.user_id, 'whatsapp'),
                'link': recruitment_link
            },
            'twitter': {
                'text': self._generate_recruitment_message(request.user_id, 'twitter'),
                'link': recruitment_link
            }
        }
        
        return {
            'success': True,
            'view': 'recruitment',
            'data': {
                'stats': recruit_stats,
                'recruitment_link': recruitment_link,
                'qr_code': self._generate_qr_code_data(request.user_id),
                'share_content': share_content,
                'rewards': {
                    'per_recruit': 50,
                    'first_trade_bonus': 100,
                    'milestone_bonus': 200,
                    'next_milestone': self._get_next_recruitment_milestone(recruit_stats['total_recruits'])
                },
                'leaderboard': self._get_recruitment_leaderboard()
            }
        }
    
    def _handle_settings_view(self, request: WebAppRequest) -> Dict[str, Any]:
        """Handle settings view request"""
        from .user_settings import settings_manager
        
        # Get formatted settings for webapp
        formatted_settings = settings_manager.format_for_webapp(str(request.user_id))
        
        return {
            'success': True,
            'view': 'settings',
            'data': formatted_settings
        }
    
    def _parse_webapp_data(self, request_data: str) -> Optional[Dict]:
        """Parse WebApp request data"""
        try:
            # Handle URL encoded data
            if '=' in request_data and '&' in request_data:
                parsed = parse_qs(request_data)
                data = {}
                for key, value in parsed.items():
                    if key == 'data' and value:
                        # Parse JSON data
                        data = json.loads(unquote(value[0]))
                    else:
                        data[key] = value[0] if value else None
                return data
            else:
                # Direct JSON
                return json.loads(request_data)
        except Exception as e:
            print(f"Error parsing webapp data: {e}")
            return None
    
    def _validate_webapp_auth(self, data: Dict) -> bool:
        """Validate WebApp authentication"""
        # For development, allow all requests
        # In production, implement proper Telegram WebApp validation
        return True
    
    def _check_view_permission(self, view: str, user_rank: UserRank) -> bool:
        """Check if user has permission to access view"""
        view_permissions = {
            'profile': UserRank.USER,
            'mission_briefing': UserRank.USER,
            'signals': UserRank.AUTHORIZED,
            'leaderboard': UserRank.USER,
            'achievements': UserRank.USER,
            'recruitment': UserRank.USER,
            'settings': UserRank.USER
        }
        
        required_rank = view_permissions.get(view, UserRank.ELITE)
        return user_rank.value >= required_rank.value
    
    def _get_cached_data(self, key: str) -> Optional[Dict]:
        """Get cached data if not expired"""
        if key in self.webapp_cache:
            cached = self.webapp_cache[key]
            if time.time() - cached['timestamp'] < self.cache_ttl:
                return cached['data']
        return None
    
    def _cache_data(self, key: str, data: Dict):
        """Cache data with timestamp"""
        self.webapp_cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
    
    def _error_response(self, message: str) -> Dict:
        """Generate error response"""
        return {
            'success': False,
            'error': message,
            'timestamp': int(time.time())
        }
    
    def _get_trading_stats(self, user_id: int) -> Dict:
        """Get user trading statistics"""
        if self.bitten_core and hasattr(self.bitten_core, 'get_trading_stats'):
            return self.bitten_core.get_trading_stats(user_id)
        
        # Fallback stats
        return {
            'total_trades': 0,
            'win_rate': 0.0,
            'avg_profit': 0.0,
            'best_day': 0.0,
            'current_streak': 0,
            'active_positions': 0
        }
    
    def _calculate_rank_progress(self, total_xp: int) -> Dict:
        """Calculate rank progression details"""
        current_rank = self.profile_manager._calculate_rank(total_xp)
        next_threshold = self.profile_manager._get_next_rank_threshold(total_xp)
        
        # Find current threshold
        current_threshold = 0
        for rank, threshold in self.profile_manager.RANK_THRESHOLDS.items():
            if total_xp >= threshold:
                current_threshold = threshold
            else:
                break
        
        xp_in_rank = total_xp - current_threshold
        xp_needed = next_threshold - current_threshold
        progress = (xp_in_rank / xp_needed * 100) if xp_needed > 0 else 100
        
        return {
            'current_rank': current_rank,
            'next_rank': self._get_next_rank_name(current_rank),
            'current_xp': total_xp,
            'next_threshold': next_threshold,
            'progress_percentage': min(100, progress),
            'xp_to_next': max(0, next_threshold - total_xp)
        }
    
    def _get_next_rank_name(self, current_rank: str) -> str:
        """Get next rank name"""
        ranks = list(self.profile_manager.RANK_THRESHOLDS.keys())
        try:
            current_index = ranks.index(current_rank)
            if current_index < len(ranks) - 1:
                return ranks[current_index + 1]
        except ValueError:
            pass
        return "MAX RANK"
    
    def _get_recent_achievements(self, user_id: int) -> List[Dict]:
        """Get recently earned achievements"""
        medals = self.profile_manager.get_user_medals(user_id)
        earned = [m for m in medals if m.get('earned', False)]
        
        # Sort by earned_at timestamp
        earned.sort(key=lambda m: m.get('earned_at', 0), reverse=True)
        
        # Return last 3
        return earned[:3]
    
    def _get_next_achievement(self, profile: Dict) -> Optional[Dict]:
        """Get next achievable medal"""
        medals = profile.get('medals', [])
        stats = profile
        
        for medal in medals:
            if not medal.get('earned', False):
                # Check how close user is
                progress = 0
                if medal['requirement_type'] == 'trades':
                    current = stats.get('missions_completed', 0)
                    progress = (current / medal['requirement_value']) * 100
                elif medal['requirement_type'] == 'profit':
                    current = stats.get('total_profit', 0)
                    progress = (current / medal['requirement_value']) * 100
                elif medal['requirement_type'] == 'streak':
                    current = stats.get('best_streak', 0)
                    progress = (current / medal['requirement_value']) * 100
                elif medal['requirement_type'] == 'recruits':
                    current = stats.get('recruits_count', 0)
                    progress = (current / medal['requirement_value']) * 100
                
                if progress > 50:  # More than 50% progress
                    medal['progress'] = progress
                    return medal
        
        return None
    
    def _generate_qr_code_data(self, user_id: int) -> str:
        """Generate QR code data URL for recruitment link"""
        # In production, use actual QR code generation
        # For now, return placeholder
        return f"data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCI+PC9zdmc+"
    
    def _generate_test_briefing(self, mission_id: str) -> MissionBriefing:
        """Generate test mission briefing"""
        test_signal = {
            'type': 'arcade',
            'symbol': 'GBPUSD',
            'direction': 'buy',
            'entry_price': 1.27650,
            'stop_loss': 1.27450,
            'take_profit': 1.27950,
            'tcs_score': 87,
            'confidence': 0.87,
            'expires_at': int(time.time()) + 300,
            'expected_duration': 45,
            'active_traders': 12,
            'total_engaged': 45,
            'squad_avg_tcs': 82.5,
            'success_rate': 0.73
        }
        
        test_market = {
            'volatility': 'NORMAL',
            'trend': 'BULLISH',
            'momentum': 'STRONG',
            'volume': 'HIGH',
            'session': 'LONDON'
        }
        
        return self.briefing_generator.generate_mission_briefing(
            test_signal, test_market, "ELITE"
        )
    
    def _get_execution_options(self, briefing: MissionBriefing, user_tier: str) -> Dict:
        """Get execution options based on briefing and tier"""
        tier_benefits = briefing.tier_benefits
        
        options = {
            'risk_levels': [
                {'value': 0.5, 'label': '0.5%', 'pips': int(briefing.risk_pips * 0.5)},
                {'value': 1.0, 'label': '1%', 'pips': briefing.risk_pips},
                {'value': 2.0, 'label': '2%', 'pips': briefing.risk_pips * 2}
            ],
            'lot_sizes': self._calculate_lot_sizes(briefing),
            'quick_actions': briefing.quick_actions,
            'max_positions': tier_benefits.get('execution_limit', 1)
        }
        
        # Add advanced options for elite
        if tier_benefits.get('advanced_intel'):
            options['advanced'] = {
                'trailing_stop': True,
                'partial_close': True,
                'scale_in': True
            }
        
        return options
    
    def _calculate_lot_sizes(self, briefing: MissionBriefing) -> List[Dict]:
        """Calculate recommended lot sizes"""
        # Simplified calculation - in production, use account balance
        base_lot = 0.01
        
        return [
            {'size': base_lot, 'label': 'Conservative', 'risk_usd': 10},
            {'size': base_lot * 2, 'label': 'Standard', 'risk_usd': 20},
            {'size': base_lot * 5, 'label': 'Aggressive', 'risk_usd': 50}
        ]
    
    def _get_market_analysis(self, briefing: MissionBriefing) -> Dict:
        """Get detailed market analysis for briefing"""
        return {
            'technical': {
                'trend': briefing.market_conditions.get('trend', 'NEUTRAL'),
                'momentum': briefing.market_conditions.get('momentum', 'STABLE'),
                'key_levels': briefing.technical_levels,
                'patterns': ['Bull Flag', 'Support Bounce']  # Example
            },
            'sentiment': {
                'overall': 'BULLISH',
                'retail': 65,  # 65% bullish
                'institutional': 70
            },
            'correlations': {
                'DXY': -0.85,
                'GOLD': 0.72
            }
        }
    
    def _get_test_signals(self) -> List[Dict]:
        """Get test signals for development"""
        return [
            {
                'signal_id': 'test_1',
                'type': 'arcade',
                'symbol': 'GBPUSD',
                'direction': 'buy',
                'entry_price': 1.27650,
                'tcs_score': 87,
                'expires_at': int(time.time()) + 300
            },
            {
                'signal_id': 'test_2',
                'type': 'sniper',
                'symbol': 'EURUSD',
                'direction': 'sell',
                'entry_price': 1.08950,
                'tcs_score': 92,
                'expires_at': int(time.time()) + 600
            }
        ]
    
    def _get_user_position_count(self, user_id: int) -> int:
        """Get user's active position count"""
        if self.bitten_core and hasattr(self.bitten_core, 'get_position_count'):
            return self.bitten_core.get_position_count(user_id)
        return 0
    
    def _calculate_avg_tcs(self, signals: List[Dict]) -> float:
        """Calculate average TCS score"""
        if not signals:
            return 0.0
        
        total = sum(s.get('tcs_score', 0) for s in signals)
        return round(total / len(signals), 1)
    
    def _get_hot_pairs(self, signals: List[Dict]) -> List[str]:
        """Get most active trading pairs"""
        pair_counts = {}
        for signal in signals:
            pair = signal.get('symbol', '')
            if pair:
                pair_counts[pair] = pair_counts.get(pair, 0) + 1
        
        # Sort by count
        sorted_pairs = sorted(pair_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Return top 3
        return [pair for pair, count in sorted_pairs[:3]]
    
    def _get_leaderboard_data(self, timeframe: str, metric: str) -> List[Dict]:
        """Get leaderboard data"""
        # In production, fetch from database
        # For now, return sample data
        return [
            {
                'rank': 1,
                'user_id': 12345,
                'username': 'EliteSniper',
                'value': 1250.50 if metric == 'profit' else 125,
                'avatar': '🎯'
            },
            {
                'rank': 2,
                'user_id': 67890,
                'username': 'PipHunter',
                'value': 980.25 if metric == 'profit' else 98,
                'avatar': '🔫'
            }
        ]
    
    def _get_user_leaderboard_position(self, user_id: int, timeframe: str, metric: str) -> Dict:
        """Get user's position in leaderboard"""
        return {
            'rank': 15,
            'value': 450.75 if metric == 'profit' else 45,
            'percentile': 85  # Top 15%
        }
    
    def _get_next_achievable_medals(self, user_id: int, medals: List[Dict]) -> List[Dict]:
        """Get next 3 achievable medals"""
        unearned = [m for m in medals if not m.get('earned', False)]
        # Sort by some criteria (e.g., easiest first)
        return unearned[:3]
    
    def _generate_recruitment_message(self, user_id: int, platform: str) -> str:
        """Generate recruitment message for different platforms"""
        link = f"https://t.me/BITTEN_bot?start=ref_{user_id}"
        
        messages = {
            'telegram': f"🤖 Join BITTEN - Elite Trading Bot Network!\n\n🎯 Professional trading signals\n💰 Proven profit system\n🏆 Exclusive community\n\nJoin through my link: {link}",
            'whatsapp': f"Hey! I've been using BITTEN trading bot and getting great results. Join through my referral link for exclusive benefits: {link}",
            'twitter': f"Trading with @BITTEN_bot 🤖 Getting consistent profits with their AI signals! Join the elite trading network: {link} #Trading #Forex #BITTEN"
        }
        
        return messages.get(platform, messages['telegram'])
    
    def _get_next_recruitment_milestone(self, current_recruits: int) -> int:
        """Get next recruitment milestone"""
        milestones = [1, 5, 10, 20, 50, 100]
        for milestone in milestones:
            if current_recruits < milestone:
                return milestone
        return 1000  # Max milestone
    
    def _get_recruitment_leaderboard(self) -> List[Dict]:
        """Get top recruiters"""
        # In production, fetch from database
        return [
            {'rank': 1, 'username': 'MasterRecruiter', 'recruits': 127, 'xp_earned': 12700},
            {'rank': 2, 'username': 'NetworkKing', 'recruits': 89, 'xp_earned': 8900},
            {'rank': 3, 'username': 'SquadBuilder', 'recruits': 67, 'xp_earned': 6700}
        ]
    
    def _get_default_settings(self) -> Dict:
        """Get default user settings"""
        return {
            'notify_signals': True,
            'notify_trades': True,
            'notify_achievements': True,
            'notify_recruitment': True,
            'risk_percentage': 2,
            'max_positions': 3,
            'default_mode': 'bit',
            'auto_close': False,
            'theme': 'dark',
            'language': 'en',
            'time_format': '24h',
            'currency_display': 'USD'
        }
    
    def _handle_update_settings(self, request: WebAppRequest) -> Dict[str, Any]:
        """Handle settings update request"""
        from .user_settings import settings_manager
        
        # Extract settings updates from request
        updates = request.data.get('settings', {})
        
        if not updates:
            return self._error_response("No settings to update")
        
        try:
            # Update settings
            updated_settings = settings_manager.update_user_settings(
                str(request.user_id),
                updates
            )
            
            # Return updated settings
            return {
                'success': True,
                'message': 'Settings updated successfully',
                'data': settings_manager.format_for_webapp(str(request.user_id))
            }
            
        except Exception as e:
            return self._error_response(f"Failed to update settings: {str(e)}")