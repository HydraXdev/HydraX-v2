#!/usr/bin/env python3
"""
BITTEN XP Progression Simulator - Enhanced Version
Provides detailed progression analysis and balance recommendations
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import random
import json
from enum import Enum
import statistics

# Define enums
class UserRank(Enum):
    """User access levels in BITTEN system"""
    UNAUTHORIZED = 0
    USER = 1
    AUTHORIZED = 2  
    ELITE = 3
    ADMIN = 4

class TradeOutcome(Enum):
    """Trade result types"""
    WIN = "win"
    LOSS = "loss"
    BREAKEVEN = "breakeven"
    PENDING = "pending"

@dataclass
class PlayerProfile:
    """Defines a player type with behavioral characteristics"""
    name: str
    trades_per_day: float
    win_rate: float
    avg_volume: float
    high_tcs_rate: float
    session_days_per_week: int
    description: str
    retention_rate: float = 0.95  # % chance to continue playing each month

@dataclass 
class SimulatedPlayer:
    """A simulated player instance"""
    profile: PlayerProfile
    current_xp: int = 0
    current_rank: UserRank = UserRank.USER
    total_trades: int = 0
    winning_trades: int = 0
    current_streak: int = 0
    best_streak: int = 0
    days_active: int = 0
    achievements: List[str] = field(default_factory=list)
    daily_trades_today: int = 0
    weekly_trades: int = 0
    rank_history: List[Tuple[int, UserRank, int]] = field(default_factory=list)  # (day, rank, xp)
    is_active: bool = True
    last_trade_day: int = 0
    achievement_history: List[Tuple[int, str, int]] = field(default_factory=list)  # (day, achievement, xp)

class EnhancedXPSimulator:
    """Enhanced XP progression simulator with detailed analytics"""
    
    def __init__(self):
        # XP configuration
        self.xp_thresholds = {
            UserRank.USER: 0,
            UserRank.AUTHORIZED: 1000,
            UserRank.ELITE: 5000,
            UserRank.ADMIN: 10000
        }
        
        self.xp_rewards = {
            'base_trade': 10,
            'winning_trade': 25,
            'high_tcs_bonus': 15,
            'volume_bonus': 5,
            'streak_bonus': 10,
            'daily_bonus': 50,
            'weekly_bonus': 200,
            'monthly_bonus': 500,
            'comeback_bonus': 100,  # Returning after 7+ days
            'achievement_multiplier': 2.0
        }
        
        # Achievement XP rewards
        self.achievement_xp = {
            'first_trade': 100,
            'trades_10': 150,
            'trades_50': 300,
            'trades_100': 500,
            'streak_3': 150,
            'streak_5': 250,
            'streak_10': 500,
            'volume_10': 100,
            'volume_50': 200,
            'volume_100': 300,
            'accuracy_60': 200,
            'accuracy_70': 300,
            'accuracy_80': 400,
            'week_active': 200,
            'month_active': 500,
            'rank_up': 500
        }
        
        # Player profiles
        self.player_profiles = {
            'casual': PlayerProfile(
                name='Casual Player',
                trades_per_day=0.5,
                win_rate=0.55,
                avg_volume=0.5,
                high_tcs_rate=0.3,
                session_days_per_week=3,
                description='Trades occasionally, moderate win rate',
                retention_rate=0.85
            ),
            'active': PlayerProfile(
                name='Active Trader',
                trades_per_day=2.0,
                win_rate=0.65,
                avg_volume=0.8,
                high_tcs_rate=0.5,
                session_days_per_week=5,
                description='Regular trader with good discipline',
                retention_rate=0.95
            ),
            'hardcore': PlayerProfile(
                name='Hardcore Trader',
                trades_per_day=5.0,
                win_rate=0.70,
                avg_volume=1.2,
                high_tcs_rate=0.7,
                session_days_per_week=7,
                description='Professional level engagement',
                retention_rate=0.98
            ),
            'newbie': PlayerProfile(
                name='New Player',
                trades_per_day=0.3,
                win_rate=0.45,
                avg_volume=0.3,
                high_tcs_rate=0.2,
                session_days_per_week=2,
                description='Learning the system, low activity',
                retention_rate=0.70
            ),
            'weekend_warrior': PlayerProfile(
                name='Weekend Warrior',
                trades_per_day=3.0,
                win_rate=0.60,
                avg_volume=1.0,
                high_tcs_rate=0.4,
                session_days_per_week=2,
                description='High activity on weekends only',
                retention_rate=0.90
            ),
            'skilled_casual': PlayerProfile(
                name='Skilled Casual',
                trades_per_day=1.0,
                win_rate=0.75,
                avg_volume=0.7,
                high_tcs_rate=0.6,
                session_days_per_week=3,
                description='High skill, low time commitment',
                retention_rate=0.92
            )
        }
        
    def simulate_trade(self, player: SimulatedPlayer) -> Dict:
        """Simulate a single trade with detailed XP calculation"""
        profile = player.profile
        
        # Determine trade outcome
        is_win = random.random() < profile.win_rate
        outcome = TradeOutcome.WIN if is_win else TradeOutcome.LOSS
        
        # Base XP
        xp_breakdown = {'base': self.xp_rewards['base_trade']}
        
        # High TCS bonus
        if random.random() < profile.high_tcs_rate:
            xp_breakdown['tcs_bonus'] = self.xp_rewards['high_tcs_bonus']
        
        # Volume bonus
        volume = random.uniform(profile.avg_volume * 0.5, profile.avg_volume * 1.5)
        if volume >= 1.0:
            xp_breakdown['volume_bonus'] = self.xp_rewards['volume_bonus']
        
        # Daily first trade bonus
        if player.daily_trades_today == 0:
            xp_breakdown['daily_bonus'] = self.xp_rewards['daily_bonus']
        
        # Comeback bonus (returning after 7+ days)
        if player.last_trade_day > 0 and player.days_active - player.last_trade_day >= 7:
            xp_breakdown['comeback_bonus'] = self.xp_rewards['comeback_bonus']
        
        # Win/loss XP
        if is_win:
            xp_breakdown['win_bonus'] = self.xp_rewards['winning_trade']
            player.current_streak += 1
            player.winning_trades += 1
            
            # Streak bonus
            if player.current_streak > 1:
                streak_xp = self.xp_rewards['streak_bonus'] * min(player.current_streak - 1, 5)
                xp_breakdown['streak_bonus'] = streak_xp
            
            player.best_streak = max(player.best_streak, player.current_streak)
        else:
            player.current_streak = 0
        
        player.total_trades += 1
        player.daily_trades_today += 1
        player.weekly_trades += 1
        player.last_trade_day = player.days_active
        
        total_xp = sum(xp_breakdown.values())
        
        return {
            'xp_earned': total_xp,
            'xp_breakdown': xp_breakdown,
            'outcome': outcome,
            'volume': volume,
            'is_win': is_win
        }
    
    def check_achievements(self, player: SimulatedPlayer, old_xp: int) -> Tuple[int, List[str]]:
        """Check and award achievements with expanded criteria"""
        achievement_xp = 0
        new_achievements = []
        
        # Trade count achievements
        trade_milestones = [(1, 'first_trade'), (10, 'trades_10'), (50, 'trades_50'), (100, 'trades_100')]
        for milestone, achievement in trade_milestones:
            if player.total_trades == milestone and achievement not in player.achievements:
                player.achievements.append(achievement)
                new_achievements.append(achievement)
                achievement_xp += self.achievement_xp[achievement]
                player.achievement_history.append((player.days_active, achievement, self.achievement_xp[achievement]))
        
        # Streak achievements
        streak_milestones = [(3, 'streak_3'), (5, 'streak_5'), (10, 'streak_10')]
        for milestone, achievement in streak_milestones:
            if player.current_streak == milestone and achievement not in player.achievements:
                player.achievements.append(achievement)
                new_achievements.append(achievement)
                achievement_xp += self.achievement_xp[achievement]
                player.achievement_history.append((player.days_active, achievement, self.achievement_xp[achievement]))
        
        # Volume milestones
        total_volume = player.total_trades * player.profile.avg_volume
        volume_milestones = [(10, 'volume_10'), (50, 'volume_50'), (100, 'volume_100')]
        for milestone, achievement in volume_milestones:
            if total_volume >= milestone and achievement not in player.achievements:
                player.achievements.append(achievement)
                new_achievements.append(achievement)
                achievement_xp += self.achievement_xp[achievement]
                player.achievement_history.append((player.days_active, achievement, self.achievement_xp[achievement]))
        
        # Accuracy achievements
        if player.total_trades >= 20:
            accuracy = (player.winning_trades / player.total_trades) * 100
            accuracy_milestones = [(60, 'accuracy_60'), (70, 'accuracy_70'), (80, 'accuracy_80')]
            for milestone, achievement in accuracy_milestones:
                if accuracy >= milestone and achievement not in player.achievements:
                    player.achievements.append(achievement)
                    new_achievements.append(achievement)
                    achievement_xp += self.achievement_xp[achievement]
                    player.achievement_history.append((player.days_active, achievement, self.achievement_xp[achievement]))
        
        # Time-based achievements
        if player.days_active == 7 and player.total_trades >= 5:
            if 'week_active' not in player.achievements:
                player.achievements.append('week_active')
                new_achievements.append('week_active')
                achievement_xp += self.achievement_xp['week_active']
                player.achievement_history.append((player.days_active, 'week_active', self.achievement_xp['week_active']))
        
        if player.days_active == 30 and player.total_trades >= 20:
            if 'month_active' not in player.achievements:
                player.achievements.append('month_active')
                new_achievements.append('month_active')
                achievement_xp += self.achievement_xp['month_active']
                player.achievement_history.append((player.days_active, 'month_active', self.achievement_xp['month_active']))
        
        # Rank up bonus
        old_rank = self.get_rank_for_xp(old_xp)
        new_rank = self.get_rank_for_xp(player.current_xp)
        if new_rank != old_rank and new_rank.value > old_rank.value:
            achievement_xp += self.achievement_xp['rank_up']
            player.current_rank = new_rank
            player.rank_history.append((player.days_active, new_rank, player.current_xp))
            new_achievements.append(f'rank_up_{new_rank.name}')
        
        return achievement_xp, new_achievements
    
    def get_rank_for_xp(self, xp: int) -> UserRank:
        """Get rank for given XP amount"""
        for rank in [UserRank.ADMIN, UserRank.ELITE, UserRank.AUTHORIZED, UserRank.USER]:
            if xp >= self.xp_thresholds[rank]:
                return rank
        return UserRank.USER
    
    def simulate_day(self, player: SimulatedPlayer, is_active_day: bool, day_num: int) -> Dict:
        """Simulate a single day with detailed tracking"""
        daily_xp = 0
        trades_today = 0
        xp_sources = {}
        
        player.daily_trades_today = 0
        
        # Check retention (monthly)
        if day_num > 0 and day_num % 30 == 0:
            if not player.is_active:
                return {'xp_earned': 0, 'trades': 0, 'xp_sources': {}}
            
            if random.random() > player.profile.retention_rate:
                player.is_active = False
                return {'xp_earned': 0, 'trades': 0, 'xp_sources': {}}
        
        if is_active_day and player.is_active:
            # Determine number of trades
            avg_trades = player.profile.trades_per_day
            if avg_trades < 1:
                trades_count = 1 if random.random() < avg_trades else 0
            else:
                trades_count = max(0, int(random.gauss(avg_trades, avg_trades ** 0.5)))
            
            for _ in range(trades_count):
                trade_result = self.simulate_trade(player)
                daily_xp += trade_result['xp_earned']
                trades_today += 1
                
                # Aggregate XP sources
                for source, xp in trade_result['xp_breakdown'].items():
                    xp_sources[source] = xp_sources.get(source, 0) + xp
        
        # Weekly bonus
        if player.days_active > 0 and player.days_active % 7 == 0:
            if player.weekly_trades >= 5:
                daily_xp += self.xp_rewards['weekly_bonus']
                xp_sources['weekly_bonus'] = self.xp_rewards['weekly_bonus']
            player.weekly_trades = 0
        
        # Monthly bonus
        if player.days_active > 0 and player.days_active % 30 == 0:
            if player.total_trades >= 20:
                daily_xp += self.xp_rewards['monthly_bonus']
                xp_sources['monthly_bonus'] = self.xp_rewards['monthly_bonus']
        
        return {
            'xp_earned': daily_xp,
            'trades': trades_today,
            'xp_sources': xp_sources
        }
    
    def simulate_player_progression(self, profile_type: str, days: int = 365) -> Dict:
        """Simulate complete player progression"""
        profile = self.player_profiles[profile_type]
        player = SimulatedPlayer(profile=profile)
        player.rank_history.append((0, UserRank.USER, 0))  # Starting rank
        
        daily_data = []
        xp_source_totals = {}
        
        for day in range(days):
            # Skip if player quit
            if not player.is_active:
                continue
            
            # Determine activity
            day_of_week = day % 7
            is_weekend = day_of_week >= 5
            
            if profile_type == 'weekend_warrior':
                is_active = is_weekend
            else:
                weekly_active_days = set(random.sample(range(7), profile.session_days_per_week))
                is_active = day_of_week in weekly_active_days
            
            # Store old XP
            old_xp = player.current_xp
            
            # Simulate day
            day_result = self.simulate_day(player, is_active, day)
            player.current_xp += day_result['xp_earned']
            
            # Aggregate XP sources
            for source, xp in day_result['xp_sources'].items():
                xp_source_totals[source] = xp_source_totals.get(source, 0) + xp
            
            # Check achievements
            achievement_xp, new_achievements = self.check_achievements(player, old_xp)
            if achievement_xp > 0:
                player.current_xp += achievement_xp
                day_result['xp_earned'] += achievement_xp
                xp_source_totals['achievements'] = xp_source_totals.get('achievements', 0) + achievement_xp
            
            player.days_active = day + 1
            
            # Track daily data
            if day_result['xp_earned'] > 0 or day % 30 == 0:  # Log active days and monthly checkpoints
                daily_data.append({
                    'day': day + 1,
                    'xp': player.current_xp,
                    'daily_xp': day_result['xp_earned'],
                    'trades': day_result['trades'],
                    'rank': player.current_rank.name,
                    'new_achievements': new_achievements
                })
        
        # Calculate statistics
        active_days = len([d for d in daily_data if d['trades'] > 0])
        win_rate = (player.winning_trades / player.total_trades * 100) if player.total_trades > 0 else 0
        avg_xp_per_day = player.current_xp / days if days > 0 else 0
        avg_xp_per_active_day = player.current_xp / active_days if active_days > 0 else 0
        avg_xp_per_trade = player.current_xp / player.total_trades if player.total_trades > 0 else 0
        
        # Get rank milestones
        rank_milestones = {}
        for day, rank, xp in player.rank_history[1:]:  # Skip initial USER rank
            rank_milestones[rank.name] = {
                'day': day,
                'xp': xp,
                'trades_at_milestone': len([d for d in daily_data if d['day'] <= day and d['trades'] > 0])
            }
        
        return {
            'profile': profile_type,
            'final_xp': player.current_xp,
            'final_rank': player.current_rank.name,
            'total_trades': player.total_trades,
            'win_rate': win_rate,
            'best_streak': player.best_streak,
            'achievements': player.achievements,
            'achievement_count': len(player.achievements),
            'rank_milestones': rank_milestones,
            'avg_xp_per_day': avg_xp_per_day,
            'avg_xp_per_active_day': avg_xp_per_active_day,
            'avg_xp_per_trade': avg_xp_per_trade,
            'active_days': active_days,
            'retention': player.is_active,
            'xp_sources': xp_source_totals,
            'daily_data': daily_data
        }
    
    def analyze_progression_balance(self, results: List[Dict]) -> Dict:
        """Comprehensive progression analysis"""
        analysis = {
            'player_summaries': {},
            'rank_achievement_rates': {},
            'xp_source_analysis': {},
            'progression_issues': [],
            'bottlenecks': [],
            'recommendations': []
        }
        
        # Player summaries
        for result in results:
            profile_name = result['profile']
            
            # Calculate time to ranks
            auth_day = result['rank_milestones'].get('AUTHORIZED', {}).get('day', 'Not reached')
            elite_day = result['rank_milestones'].get('ELITE', {}).get('day', 'Not reached')
            admin_day = result['rank_milestones'].get('ADMIN', {}).get('day', 'Not reached')
            
            analysis['player_summaries'][profile_name] = {
                'final_rank': result['final_rank'],
                'final_xp': result['final_xp'],
                'days_to_authorized': auth_day,
                'days_to_elite': elite_day,
                'days_to_admin': admin_day,
                'total_trades': result['total_trades'],
                'active_days': result['active_days'],
                'avg_xp_per_day': round(result['avg_xp_per_day'], 1),
                'avg_xp_per_active_day': round(result['avg_xp_per_active_day'], 1),
                'avg_xp_per_trade': round(result['avg_xp_per_trade'], 1),
                'achievements_unlocked': result['achievement_count'],
                'retention': result['retention']
            }
        
        # Rank achievement rates
        for rank in ['AUTHORIZED', 'ELITE', 'ADMIN']:
            achieved = sum(1 for r in results if rank in r['rank_milestones'])
            total = len(results)
            analysis['rank_achievement_rates'][rank] = {
                'achieved': achieved,
                'total': total,
                'percentage': round((achieved / total) * 100, 1)
            }
        
        # XP source analysis
        all_sources = set()
        for result in results:
            all_sources.update(result['xp_sources'].keys())
        
        for source in all_sources:
            source_data = []
            for result in results:
                if source in result['xp_sources']:
                    source_data.append({
                        'profile': result['profile'],
                        'amount': result['xp_sources'][source],
                        'percentage': (result['xp_sources'][source] / result['final_xp']) * 100
                    })
            
            if source_data:
                avg_percentage = statistics.mean([d['percentage'] for d in source_data])
                analysis['xp_source_analysis'][source] = {
                    'avg_percentage': round(avg_percentage, 1),
                    'profiles': source_data
                }
        
        # Identify progression issues
        # Issue 1: Casual player progression
        casual_result = next(r for r in results if r['profile'] == 'casual')
        if casual_result['rank_milestones'].get('ELITE', {}).get('day', 366) > 365:
            analysis['progression_issues'].append({
                'issue': 'Casual players cannot reach ELITE within a year',
                'severity': 'high',
                'affected_profiles': ['casual']
            })
        
        # Issue 2: New player retention
        newbie_result = next(r for r in results if r['profile'] == 'newbie')
        if newbie_result['rank_milestones'].get('AUTHORIZED', {}).get('day', 366) > 90:
            analysis['progression_issues'].append({
                'issue': 'New players take too long (>90 days) to reach first promotion',
                'severity': 'critical',
                'affected_profiles': ['newbie']
            })
        
        # Issue 3: Hardcore progression speed
        hardcore_result = next(r for r in results if r['profile'] == 'hardcore')
        if hardcore_result['rank_milestones'].get('ADMIN', {}).get('day', 366) < 60:
            analysis['progression_issues'].append({
                'issue': 'Hardcore players reach max rank too quickly (<60 days)',
                'severity': 'medium',
                'affected_profiles': ['hardcore']
            })
        
        # Issue 4: Weekend warrior disadvantage
        weekend_result = next(r for r in results if r['profile'] == 'weekend_warrior')
        active_result = next(r for r in results if r['profile'] == 'active')
        if weekend_result['avg_xp_per_active_day'] < active_result['avg_xp_per_active_day'] * 0.8:
            analysis['progression_issues'].append({
                'issue': 'Weekend warriors earn significantly less XP per active day',
                'severity': 'medium',
                'affected_profiles': ['weekend_warrior']
            })
        
        # Identify bottlenecks
        for result in results:
            if result['achievement_count'] < 5 and result['total_trades'] > 50:
                analysis['bottlenecks'].append({
                    'profile': result['profile'],
                    'type': 'achievement_scarcity',
                    'description': 'Low achievement unlock rate despite high activity'
                })
        
        # Generate recommendations based on issues
        if any(issue['severity'] == 'critical' for issue in analysis['progression_issues']):
            analysis['recommendations'].append({
                'priority': 'HIGH',
                'recommendation': 'Lower AUTHORIZED threshold to 750 XP or add "New Player" XP multiplier (1.5x for first 30 days)',
                'rationale': 'New player retention is critical for game health'
            })
        
        if any('cannot reach ELITE' in issue['issue'] for issue in analysis['progression_issues']):
            analysis['recommendations'].append({
                'priority': 'HIGH',
                'recommendation': 'Add more achievement tiers (25 trades, 75 trades) with 200-300 XP rewards',
                'rationale': 'Casual players need more progression milestones'
            })
        
        if any('too quickly' in issue['issue'] for issue in analysis['progression_issues']):
            analysis['recommendations'].append({
                'priority': 'MEDIUM',
                'recommendation': 'Add prestige system or extend ranks (MASTER at 20k XP, LEGEND at 50k XP)',
                'rationale': 'Extend endgame for dedicated players'
            })
        
        # General recommendations
        analysis['recommendations'].extend([
            {
                'priority': 'MEDIUM',
                'recommendation': 'Implement "Rest XP" system - 2x XP for first 3 trades after 3+ days absence',
                'rationale': 'Encourage returning players and reduce FOMO'
            },
            {
                'priority': 'LOW',
                'recommendation': 'Add social features - 10% XP bonus when trading alongside friends',
                'rationale': 'Increase retention through social engagement'
            },
            {
                'priority': 'LOW',
                'recommendation': 'Seasonal events with 1.5x XP weekends',
                'rationale': 'Drive engagement spikes and re-engage lapsed players'
            }
        ])
        
        return analysis
    
    def generate_detailed_report(self, results: List[Dict], analysis: Dict):
        """Generate comprehensive report"""
        print("\n" + "="*80)
        print("DETAILED PROGRESSION ANALYSIS")
        print("="*80)
        
        # Player progression summary
        print("\n📊 Player Progression Summary:")
        print("-" * 100)
        print(f"{'Profile':<20} {'Final Rank':<12} {'Final XP':<10} {'Days to AUTH':<15} {'Days to ELITE':<15} {'Trades':<10} {'Active Days':<12}")
        print("-" * 100)
        
        for profile, summary in analysis['player_summaries'].items():
            auth_days = str(summary['days_to_authorized'])[:12]
            elite_days = str(summary['days_to_elite'])[:12]
            print(f"{profile:<20} {summary['final_rank']:<12} {summary['final_xp']:<10} {auth_days:<15} {elite_days:<15} {summary['total_trades']:<10} {summary['active_days']:<12}")
        
        # Rank achievement rates
        print("\n🏆 Rank Achievement Rates:")
        print("-" * 50)
        for rank, data in analysis['rank_achievement_rates'].items():
            print(f"{rank:<15}: {data['achieved']}/{data['total']} players ({data['percentage']}%)")
        
        # XP source breakdown
        print("\n💰 XP Source Analysis (% of total XP):")
        print("-" * 60)
        sorted_sources = sorted(analysis['xp_source_analysis'].items(), 
                              key=lambda x: x[1]['avg_percentage'], reverse=True)
        for source, data in sorted_sources[:10]:  # Top 10 sources
            print(f"{source:<20}: {data['avg_percentage']}% average contribution")
        
        # Issues and bottlenecks
        if analysis['progression_issues']:
            print("\n⚠️  Critical Issues:")
            print("-" * 80)
            for issue in sorted(analysis['progression_issues'], key=lambda x: ['critical', 'high', 'medium'].index(x['severity'])):
                print(f"[{issue['severity'].upper()}] {issue['issue']}")
                print(f"      Affects: {', '.join(issue['affected_profiles'])}")
        
        if analysis['bottlenecks']:
            print("\n🚧 Progression Bottlenecks:")
            print("-" * 60)
            for bottleneck in analysis['bottlenecks']:
                print(f"{bottleneck['profile']}: {bottleneck['description']}")
        
        # Recommendations
        print("\n💡 Balance Recommendations:")
        print("-" * 80)
        for rec in sorted(analysis['recommendations'], key=lambda x: ['HIGH', 'MEDIUM', 'LOW'].index(x['priority'])):
            print(f"\n[{rec['priority']}] {rec['recommendation']}")
            print(f"     Rationale: {rec['rationale']}")
        
        # XP requirements vs actual performance
        print("\n📈 XP Requirements vs Reality:")
        print("-" * 80)
        print(f"{'Rank':<15} {'Required XP':<15} {'Theoretical Days':<20} {'Actual Days (Active)':<25} {'Actual Days (Casual)':<25}")
        print("-" * 80)
        
        active_data = analysis['player_summaries'].get('active', {})
        casual_data = analysis['player_summaries'].get('casual', {})
        
        for rank in [UserRank.AUTHORIZED, UserRank.ELITE, UserRank.ADMIN]:
            xp_req = self.xp_thresholds[rank]
            theoretical_days = xp_req / 50  # Assuming 50 XP/day average
            
            active_days = active_data.get(f'days_to_{rank.name.lower()}', 'Not reached')
            casual_days = casual_data.get(f'days_to_{rank.name.lower()}', 'Not reached')
            
            print(f"{rank.name:<15} {xp_req:<15} {theoretical_days:<20.0f} {str(active_days):<25} {str(casual_days):<25}")
    
    def save_enhanced_report(self, results: List[Dict], analysis: Dict):
        """Save enhanced report with all data"""
        report = {
            'simulation_date': datetime.now().isoformat(),
            'simulation_days': 365,
            'player_profiles': {k: {
                'name': v.name,
                'trades_per_day': v.trades_per_day,
                'win_rate': v.win_rate,
                'avg_volume': v.avg_volume,
                'high_tcs_rate': v.high_tcs_rate,
                'session_days_per_week': v.session_days_per_week,
                'retention_rate': v.retention_rate,
                'description': v.description
            } for k, v in self.player_profiles.items()},
            'xp_configuration': {
                'thresholds': {k.name: v for k, v in self.xp_thresholds.items()},
                'rewards': self.xp_rewards,
                'achievements': self.achievement_xp
            },
            'simulation_results': results,
            'analysis': analysis
        }
        
        output_path = '/root/HydraX-v2/data/xp_simulation_enhanced_report.json'
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Enhanced report saved to: {output_path}")
    
    def run_simulation(self, days: int = 365):
        """Run complete enhanced simulation"""
        print("="*80)
        print("BITTEN XP Progression Simulator - Enhanced Analysis")
        print("="*80)
        
        # Run simulations
        results = []
        for profile_type in self.player_profiles.keys():
            print(f"\nSimulating {profile_type} player...")
            result = self.simulate_player_progression(profile_type, days)
            results.append(result)
            
            # Quick summary
            profile = self.player_profiles[profile_type]
            print(f"  Description: {profile.description}")
            print(f"  Final: {result['final_xp']:} XP ({result['final_rank']})")
            print(f"  Performance: {result['total_trades']} trades, {result['win_rate']:.1f}% win rate")
            print(f"  Achievements: {result['achievement_count']} unlocked")
            print(f"  Retention: {'Active' if result['retention'] else 'Quit'}")
        
        # Analyze balance
        analysis = self.analyze_progression_balance(results)
        
        # Generate reports
        self.generate_detailed_report(results, analysis)
        self.save_enhanced_report(results, analysis)
        
        return results, analysis

def main():
    """Main execution"""
    simulator = EnhancedXPSimulator()
    results, analysis = simulator.run_simulation()
    
    print("\n✅ Enhanced simulation complete!")
    print("\n🎮 Key Insights:")
    print(f"  • Rank achievement rates: AUTH={analysis['rank_achievement_rates']['AUTHORIZED']['percentage']}%, "
          f"ELITE={analysis['rank_achievement_rates']['ELITE']['percentage']}%, "
          f"ADMIN={analysis['rank_achievement_rates']['ADMIN']['percentage']}%")
    print(f"  • Critical issues found: {len([i for i in analysis['progression_issues'] if i['severity'] == 'critical'])}")
    print(f"  • High priority recommendations: {len([r for r in analysis['recommendations'] if r['priority'] == 'HIGH'])}")

if __name__ == "__main__":
    main()