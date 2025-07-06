#!/usr/bin/env python3
"""
BITTEN XP Progression Simulator
Simulates different player types and analyzes progression balance
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from dataclasses import dataclass, field
import random
import json
from enum import Enum

# Define enums directly to avoid import issues
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

class AchievementType(Enum):
    """Achievement categories"""
    FIRST_TRADE = "first_trade"
    PROFIT_STREAK = "profit_streak"
    VOLUME_MILESTONE = "volume_milestone"
    ACCURACY_MILESTONE = "accuracy_milestone"
    CONSECUTIVE_DAYS = "consecutive_days"
    RISK_MANAGEMENT = "risk_management"
    TIER_PROMOTION = "tier_promotion"
    SPECIAL_EVENT = "special_event"

@dataclass
class PlayerProfile:
    """Defines a player type with behavioral characteristics"""
    name: str
    trades_per_day: float
    win_rate: float
    avg_volume: float
    high_tcs_rate: float  # % of trades with TCS >= 85
    session_days_per_week: int
    description: str

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
    rank_history: List[Tuple[int, UserRank]] = field(default_factory=list)

class XPProgressionSimulator:
    """Simulates XP progression for different player types"""
    
    def __init__(self):
        # XP configuration from xp_logger.py
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
            'achievement_multiplier': 2.0
        }
        
        # Achievement XP rewards
        self.achievement_xp = {
            'first_trade': 100,
            'streak_5': 250,
            'streak_10': 500,
            'volume_100': 300,
            'accuracy_80': 400,
            'rank_up': 500
        }
        
        # Define player profiles
        self.player_profiles = {
            'casual': PlayerProfile(
                name='Casual Player',
                trades_per_day=0.5,  # 3-4 trades per week
                win_rate=0.55,
                avg_volume=0.5,
                high_tcs_rate=0.3,
                session_days_per_week=3,
                description='Trades occasionally, moderate win rate'
            ),
            'active': PlayerProfile(
                name='Active Trader',
                trades_per_day=2.0,
                win_rate=0.65,
                avg_volume=0.8,
                high_tcs_rate=0.5,
                session_days_per_week=5,
                description='Regular trader with good discipline'
            ),
            'hardcore': PlayerProfile(
                name='Hardcore Trader',
                trades_per_day=5.0,
                win_rate=0.70,
                avg_volume=1.2,
                high_tcs_rate=0.7,
                session_days_per_week=7,
                description='Professional level engagement'
            ),
            'newbie': PlayerProfile(
                name='New Player',
                trades_per_day=0.3,
                win_rate=0.45,
                avg_volume=0.3,
                high_tcs_rate=0.2,
                session_days_per_week=2,
                description='Learning the system, low activity'
            ),
            'weekend_warrior': PlayerProfile(
                name='Weekend Warrior',
                trades_per_day=3.0,  # But only on weekends
                win_rate=0.60,
                avg_volume=1.0,
                high_tcs_rate=0.4,
                session_days_per_week=2,
                description='High activity on weekends only'
            )
        }
        
    def simulate_trade(self, player: SimulatedPlayer) -> Dict:
        """Simulate a single trade"""
        profile = player.profile
        
        # Determine trade outcome
        is_win = random.random() < profile.win_rate
        outcome = TradeOutcome.WIN if is_win else TradeOutcome.LOSS
        
        # Calculate XP for opening
        xp_earned = self.xp_rewards['base_trade']
        
        # High TCS bonus
        if random.random() < profile.high_tcs_rate:
            xp_earned += self.xp_rewards['high_tcs_bonus']
        
        # Volume bonus
        volume = random.uniform(profile.avg_volume * 0.5, profile.avg_volume * 1.5)
        if volume >= 1.0:
            xp_earned += self.xp_rewards['volume_bonus']
        
        # Daily first trade bonus
        if player.daily_trades_today == 0:
            xp_earned += self.xp_rewards['daily_bonus']
        
        # Closing XP
        if is_win:
            xp_earned += self.xp_rewards['winning_trade']
            player.current_streak += 1
            player.winning_trades += 1
            
            # Streak bonus
            if player.current_streak > 1:
                xp_earned += self.xp_rewards['streak_bonus'] * (player.current_streak - 1)
            
            player.best_streak = max(player.best_streak, player.current_streak)
        else:
            player.current_streak = 0
        
        player.total_trades += 1
        player.daily_trades_today += 1
        player.weekly_trades += 1
        
        return {
            'xp_earned': xp_earned,
            'outcome': outcome,
            'volume': volume,
            'is_win': is_win
        }
    
    def check_achievements(self, player: SimulatedPlayer, old_xp: int) -> int:
        """Check and award achievements"""
        achievement_xp = 0
        
        # First trade
        if player.total_trades == 1 and 'first_trade' not in player.achievements:
            player.achievements.append('first_trade')
            achievement_xp += self.achievement_xp['first_trade']
        
        # Streak achievements
        if player.current_streak == 5 and 'streak_5' not in player.achievements:
            player.achievements.append('streak_5')
            achievement_xp += self.achievement_xp['streak_5']
        elif player.current_streak == 10 and 'streak_10' not in player.achievements:
            player.achievements.append('streak_10') 
            achievement_xp += self.achievement_xp['streak_10']
        
        # Volume milestone (simplified)
        total_volume = player.total_trades * player.profile.avg_volume
        if total_volume >= 100 and 'volume_100' not in player.achievements:
            player.achievements.append('volume_100')
            achievement_xp += self.achievement_xp['volume_100']
        
        # Accuracy achievement
        if player.total_trades >= 20:
            accuracy = (player.winning_trades / player.total_trades) * 100
            if accuracy >= 80 and 'accuracy_80' not in player.achievements:
                player.achievements.append('accuracy_80')
                achievement_xp += self.achievement_xp['accuracy_80']
        
        # Rank up bonus
        old_rank = self.get_rank_for_xp(old_xp)
        new_rank = self.get_rank_for_xp(player.current_xp)
        if new_rank != old_rank and new_rank.value > old_rank.value:
            achievement_xp += self.achievement_xp['rank_up']
            player.current_rank = new_rank
            player.rank_history.append((player.days_active, new_rank))
        
        return achievement_xp
    
    def get_rank_for_xp(self, xp: int) -> UserRank:
        """Get rank for given XP amount"""
        for rank in [UserRank.ADMIN, UserRank.ELITE, UserRank.AUTHORIZED, UserRank.USER]:
            if xp >= self.xp_thresholds[rank]:
                return rank
        return UserRank.USER
    
    def simulate_day(self, player: SimulatedPlayer, is_active_day: bool) -> Dict:
        """Simulate a single day"""
        daily_xp = 0
        trades_today = 0
        
        player.daily_trades_today = 0
        
        if is_active_day:
            # Determine number of trades for the day (use simple approximation instead of numpy)
            # Poisson-like distribution using random
            avg_trades = player.profile.trades_per_day
            if avg_trades < 1:
                # For low averages, use probability
                trades_count = 1 if random.random() < avg_trades else 0
            else:
                # For higher averages, use normal distribution approximation
                trades_count = max(0, int(random.gauss(avg_trades, avg_trades ** 0.5)))
            
            for _ in range(trades_count):
                trade_result = self.simulate_trade(player)
                daily_xp += trade_result['xp_earned']
                trades_today += 1
        
        # Weekly bonus check (simplified - every 7 days if enough trades)
        if player.days_active > 0 and player.days_active % 7 == 0:
            if player.weekly_trades >= 5:
                daily_xp += self.xp_rewards['weekly_bonus']
            player.weekly_trades = 0  # Reset weekly count regardless
        
        return {
            'xp_earned': daily_xp,
            'trades': trades_today
        }
    
    def simulate_player_progression(self, profile_type: str, days: int = 365) -> Dict:
        """Simulate a player's progression over time"""
        profile = self.player_profiles[profile_type]
        player = SimulatedPlayer(profile=profile)
        
        daily_data = []
        rank_milestones = {}
        
        for day in range(days):
            # Determine if player is active today
            day_of_week = day % 7
            is_weekend = day_of_week >= 5
            
            # Weekend warrior only trades on weekends
            if profile_type == 'weekend_warrior':
                is_active = is_weekend
            else:
                # Other players have random activity based on their weekly pattern
                weekly_active_days = set(random.sample(range(7), profile.session_days_per_week))
                is_active = day_of_week in weekly_active_days
            
            # Store old XP for achievement checking
            old_xp = player.current_xp
            
            # Simulate the day
            day_result = self.simulate_day(player, is_active)
            player.current_xp += day_result['xp_earned']
            
            # Check achievements
            achievement_xp = self.check_achievements(player, old_xp)
            player.current_xp += achievement_xp
            day_result['xp_earned'] += achievement_xp
            
            # Track rank milestones
            current_rank = self.get_rank_for_xp(player.current_xp)
            if current_rank != player.current_rank and current_rank.value > player.current_rank.value:
                rank_milestones[current_rank.name] = day + 1
                player.current_rank = current_rank
            
            player.days_active = day + 1
            
            daily_data.append({
                'day': day + 1,
                'xp': player.current_xp,
                'daily_xp': day_result['xp_earned'],
                'trades': day_result['trades'],
                'rank': player.current_rank.name
            })
        
        # Calculate summary statistics
        win_rate = (player.winning_trades / player.total_trades * 100) if player.total_trades > 0 else 0
        avg_xp_per_day = player.current_xp / days
        avg_xp_per_trade = player.current_xp / player.total_trades if player.total_trades > 0 else 0
        
        return {
            'profile': profile_type,
            'final_xp': player.current_xp,
            'final_rank': player.current_rank.name,
            'total_trades': player.total_trades,
            'win_rate': win_rate,
            'best_streak': player.best_streak,
            'achievements': player.achievements,
            'rank_milestones': rank_milestones,
            'avg_xp_per_day': avg_xp_per_day,
            'avg_xp_per_trade': avg_xp_per_trade,
            'daily_data': daily_data
        }
    
    def analyze_progression_balance(self, results: List[Dict]) -> Dict:
        """Analyze progression balance across player types"""
        analysis = {
            'player_summaries': {},
            'rank_achievement_rates': {},
            'progression_issues': [],
            'recommendations': []
        }
        
        # Analyze each player type
        for result in results:
            profile_name = result['profile']
            
            analysis['player_summaries'][profile_name] = {
                'final_rank': result['final_rank'],
                'days_to_authorized': result['rank_milestones'].get('AUTHORIZED', 'Not reached'),
                'days_to_elite': result['rank_milestones'].get('ELITE', 'Not reached'),
                'days_to_admin': result['rank_milestones'].get('ADMIN', 'Not reached'),
                'total_trades': result['total_trades'],
                'avg_xp_per_day': round(result['avg_xp_per_day'], 1),
                'achievements_unlocked': len(result['achievements'])
            }
        
        # Calculate rank achievement rates
        for rank in ['AUTHORIZED', 'ELITE', 'ADMIN']:
            achieved = sum(1 for r in results if rank in r['rank_milestones'])
            analysis['rank_achievement_rates'][rank] = f"{achieved}/{len(results)} players"
        
        # Identify progression issues
        # Check if casual players can reasonably reach higher ranks
        casual_result = next(r for r in results if r['profile'] == 'casual')
        if 'ELITE' not in casual_result['rank_milestones']:
            analysis['progression_issues'].append(
                "Casual players cannot reach ELITE rank within a year"
            )
        
        # Check if newbies progress too slowly
        newbie_result = next(r for r in results if r['profile'] == 'newbie')
        if 'AUTHORIZED' not in newbie_result['rank_milestones'] or \
           newbie_result['rank_milestones'].get('AUTHORIZED', 0) > 180:
            analysis['progression_issues'].append(
                "New players take too long to reach AUTHORIZED rank"
            )
        
        # Check if hardcore players progress too quickly
        hardcore_result = next(r for r in results if r['profile'] == 'hardcore')
        if hardcore_result['rank_milestones'].get('ADMIN', 365) < 90:
            analysis['progression_issues'].append(
                "Hardcore players reach max rank too quickly"
            )
        
        # Generate recommendations
        if analysis['progression_issues']:
            if "too long to reach AUTHORIZED" in str(analysis['progression_issues']):
                analysis['recommendations'].append(
                    "Consider lowering AUTHORIZED threshold to 750 XP or increasing new player bonuses"
                )
            
            if "cannot reach ELITE" in str(analysis['progression_issues']):
                analysis['recommendations'].append(
                    "Add more achievement opportunities or increase daily/weekly bonuses"
                )
            
            if "reach max rank too quickly" in str(analysis['progression_issues']):
                analysis['recommendations'].append(
                    "Consider adding more ranks or increasing ADMIN threshold to 15000 XP"
                )
        
        # Additional balance recommendations
        analysis['recommendations'].extend([
            "Consider time-based XP decay to encourage consistent activity",
            "Add seasonal events with XP multipliers to re-engage inactive players",
            "Implement prestige system for players who reach ADMIN rank",
            "Add team/guild features to encourage social progression"
        ])
        
        return analysis
    
    def generate_xp_requirements_table(self) -> str:
        """Generate a table showing XP requirements"""
        table = "\nXP Requirements per Rank:\n"
        table += "-" * 60 + "\n"
        table += f"{'Rank':<15} {'XP Required':<15} {'Days @ 50 XP/day':<15} {'Trades @ 30 XP':<15}\n"
        table += "-" * 60 + "\n"
        
        for rank in [UserRank.USER, UserRank.AUTHORIZED, UserRank.ELITE, UserRank.ADMIN]:
            xp_req = self.xp_thresholds[rank]
            days_at_50 = xp_req / 50 if xp_req > 0 else 0
            trades_at_30 = xp_req / 30 if xp_req > 0 else 0
            
            table += f"{rank.name:<15} {xp_req:<15} {days_at_50:<15.1f} {trades_at_30:<15.0f}\n"
        
        return table
    
    def run_simulation(self, days: int = 365):
        """Run complete simulation"""
        print("="*60)
        print("BITTEN XP Progression Simulator")
        print("="*60)
        
        # Run simulations for each player type
        results = []
        for profile_type in self.player_profiles.keys():
            print(f"\nSimulating {profile_type} player...")
            result = self.simulate_player_progression(profile_type, days)
            results.append(result)
            
            # Print summary
            profile = self.player_profiles[profile_type]
            print(f"  Profile: {profile.description}")
            print(f"  Final XP: {result['final_xp']:,}")
            print(f"  Final Rank: {result['final_rank']}")
            print(f"  Total Trades: {result['total_trades']}")
            print(f"  Win Rate: {result['win_rate']:.1f}%")
            print(f"  Achievements: {len(result['achievements'])}")
            
            if result['rank_milestones']:
                print("  Rank Progression:")
                for rank, day in result['rank_milestones'].items():
                    print(f"    - {rank}: Day {day}")
        
        # Analyze balance
        print("\n" + "="*60)
        print("PROGRESSION ANALYSIS")
        print("="*60)
        
        analysis = self.analyze_progression_balance(results)
        
        # Print player summaries
        print("\nPlayer Type Summary:")
        print("-" * 80)
        print(f"{'Type':<20} {'Final Rank':<15} {'Days to AUTH':<15} {'Days to ELITE':<15} {'Avg XP/Day':<15}")
        print("-" * 80)
        
        for player_type, summary in analysis['player_summaries'].items():
            days_auth = str(summary['days_to_authorized'])[:10]
            days_elite = str(summary['days_to_elite'])[:10]
            print(f"{player_type:<20} {summary['final_rank']:<15} {days_auth:<15} {days_elite:<15} {summary['avg_xp_per_day']:<15}")
        
        # Print issues and recommendations
        if analysis['progression_issues']:
            print("\n⚠️  Progression Issues Identified:")
            for issue in analysis['progression_issues']:
                print(f"  • {issue}")
        
        print("\n💡 Recommendations:")
        for rec in analysis['recommendations']:
            print(f"  • {rec}")
        
        # Print XP requirements table
        print(self.generate_xp_requirements_table())
        
        # Generate detailed report
        self.save_detailed_report(results, analysis)
        
        return results, analysis
    
    def save_detailed_report(self, results: List[Dict], analysis: Dict):
        """Save detailed simulation report"""
        report = {
            'simulation_date': datetime.now().isoformat(),
            'simulation_days': 365,
            'player_profiles': {k: {
                'name': v.name,
                'trades_per_day': v.trades_per_day,
                'win_rate': v.win_rate,
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
        
        # Save to JSON
        output_path = '/root/HydraX-v2/data/xp_simulation_report.json'
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {output_path}")
    
    def plot_progression_curves(self, results: List[Dict]):
        """Generate progression curves visualization (text-based)"""
        print("\n" + "="*60)
        print("XP PROGRESSION CURVES (First 90 days)")
        print("="*60)
        
        # Create simple ASCII chart
        max_xp = 3000  # Focus on first 3000 XP
        chart_width = 50
        
        for result in results:
            profile = result['profile']
            print(f"\n{profile.upper()}:")
            
            # Sample every 10 days for display
            for day in range(0, 91, 10):
                if day < len(result['daily_data']):
                    xp = result['daily_data'][day]['xp']
                    rank = result['daily_data'][day]['rank']
                    
                    # Calculate bar length
                    bar_length = int((xp / max_xp) * chart_width) if xp < max_xp else chart_width
                    bar = "█" * bar_length
                    
                    print(f"Day {day:3d}: {bar:<{chart_width}} {xp:5d} XP ({rank})")

def main():
    """Main execution"""
    simulator = XPProgressionSimulator()
    
    # Run simulation
    results, analysis = simulator.run_simulation()
    
    # Plot progression curves
    simulator.plot_progression_curves(results)
    
    print("\n✅ Simulation complete!")

if __name__ == "__main__":
    main()