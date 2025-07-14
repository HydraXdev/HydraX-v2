"""
BITTEN Battle Pass Integration
Integrates battle pass system with existing BITTEN infrastructure
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio
import json

from .battle_pass import BittenBattlePass, BattlePassType, RewardType, battle_pass_system

class BattlePassIntegration:
    """
    Integrates battle pass system with BITTEN trading platform
    
    Features:
    - XP award integration with trading activities
    - Challenge progress tracking
    - Reward distribution
    - Season management
    - User tier integration
    """
    
    def __init__(self):
        self.battle_pass = battle_pass_system
        
    async def award_trading_xp(self, user_id: str, trade_data: Dict) -> Dict:
        """Award XP for trading activities and check battle pass progression"""
        try:
            # Calculate base XP from trading activity
            base_xp = self.calculate_trading_xp(trade_data)
            
            # Apply battle pass XP multipliers
            multiplied_xp = await self.apply_battle_pass_multipliers(user_id, base_xp)
            
            # Award XP and handle progression
            progression_result = self.battle_pass.award_xp(
                user_id=user_id,
                xp_amount=multiplied_xp,
                source="trading"
            )
            
            # Update challenge progress
            await self.update_challenge_progress(user_id, trade_data)
            
            # Check for special rewards
            special_rewards = await self.check_special_rewards(user_id, trade_data)
            if special_rewards:
                progression_result["special_rewards"] = special_rewards
            
            return {
                "success": True,
                "base_xp": base_xp,
                "final_xp": multiplied_xp,
                "progression": progression_result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def calculate_trading_xp(self, trade_data: Dict) -> int:
        """Calculate XP based on trading performance"""
        base_xp = 50  # Base XP for any trade
        
        # Performance bonuses
        if trade_data.get("result") == "win":
            base_xp += 25
            
            # Profit-based bonus
            profit_pips = trade_data.get("profit_pips", 0)
            if profit_pips > 10:
                base_xp += min(profit_pips, 50)  # Max 50 bonus pips
        
        # Trade quality bonuses
        tcs_score = trade_data.get("tcs_score", 70)
        if tcs_score >= 85:
            base_xp += 30  # High confidence trade
        elif tcs_score >= 75:
            base_xp += 15  # Good confidence trade
        
        # Hold time bonus (rewards patience)
        hold_time_minutes = trade_data.get("hold_time_minutes", 0)
        if hold_time_minutes >= 60:
            base_xp += 20  # Held for over an hour
        elif hold_time_minutes >= 30:
            base_xp += 10  # Held for over 30 minutes
        
        # Risk management bonus
        risk_percent = trade_data.get("risk_percent", 2.0)
        if risk_percent <= 1.0:
            base_xp += 15  # Conservative risk
        elif risk_percent <= 1.5:
            base_xp += 10  # Moderate risk
        
        return min(base_xp, 200)  # Cap at 200 XP per trade
    
    async def apply_battle_pass_multipliers(self, user_id: str, base_xp: int) -> int:
        """Apply battle pass specific XP multipliers"""
        progress = self.battle_pass.get_user_progress(user_id)
        if not progress:
            return base_xp
        
        multiplier = 1.0
        
        # Pass type multipliers
        if progress.pass_type == BattlePassType.PREMIUM:
            multiplier += 0.25  # +25% XP
        elif progress.pass_type == BattlePassType.ELITE:
            multiplier += 0.50  # +50% XP
        
        # Level-based multipliers
        if progress.level >= 50:
            multiplier += 0.15  # High level bonus
        elif progress.level >= 25:
            multiplier += 0.10  # Mid level bonus
        
        # Weekend bonus (Fridays-Sundays)
        if datetime.now().weekday() >= 4:  # Friday = 4, Saturday = 5, Sunday = 6
            multiplier += 0.20  # Weekend warrior bonus
        
        return int(base_xp * multiplier)
    
    async def update_challenge_progress(self, user_id: str, trade_data: Dict):
        """Update weekly challenge progress based on trade data"""
        if not self.battle_pass.current_season:
            return
        
        # Get current week challenges
        current_week = self.get_current_week()
        week_challenges = [c for c in self.battle_pass.current_season.challenges 
                          if c['week'] == current_week]
        
        for challenge in week_challenges:
            await self.process_challenge_progress(user_id, challenge, trade_data)
    
    async def process_challenge_progress(self, user_id: str, challenge: Dict, trade_data: Dict):
        """Process individual challenge progress"""
        objective = challenge['objective']
        challenge_id = challenge['id']
        
        progress_increment = 0
        
        # Parse different challenge objectives
        if objective.startswith("execute_trades:"):
            target = int(objective.split(":")[1])
            progress_increment = 1  # One trade executed
            
        elif objective.startswith("win_trades:"):
            target = int(objective.split(":")[1])
            if trade_data.get("result") == "win":
                progress_increment = 1
                
        elif objective.startswith("profit_pips:"):
            target = int(objective.split(":")[1])
            if trade_data.get("result") == "win":
                progress_increment = trade_data.get("profit_pips", 0)
                
        elif objective.startswith("high_tcs_trades:"):
            target = int(objective.split(":")[1])
            if trade_data.get("tcs_score", 0) >= 85:
                progress_increment = 1
        
        # Update challenge progress in database
        if progress_increment > 0:
            await self.update_challenge_database(user_id, challenge_id, progress_increment, challenge['xp_reward'])
    
    async def update_challenge_database(self, user_id: str, challenge_id: str, progress_increment: int, xp_reward: int):
        """Update challenge progress in database"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(self.battle_pass.db_path)
            cursor = conn.cursor()
            
            # Get current progress
            cursor.execute("""
                SELECT progress, completed FROM user_challenge_progress
                WHERE user_id = ? AND challenge_id = ?
            """, (user_id, challenge_id))
            
            row = cursor.fetchone()
            if row:
                current_progress, completed = row
                if completed:
                    conn.close()
                    return
            else:
                current_progress = 0
            
            # Update progress
            new_progress = current_progress + progress_increment
            
            # Check if challenge is completed
            cursor.execute("""
                SELECT objective FROM battle_pass_challenges WHERE id = ?
            """, (challenge_id,))
            
            objective_row = cursor.fetchone()
            if objective_row:
                objective = objective_row[0]
                target = int(objective.split(":")[1]) if ":" in objective else 1
                
                is_completed = new_progress >= target
                
                # Update or insert progress
                cursor.execute("""
                    INSERT OR REPLACE INTO user_challenge_progress
                    (user_id, challenge_id, progress, completed, completed_at, season_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    challenge_id,
                    new_progress,
                    is_completed,
                    datetime.now() if is_completed else None,
                    self.battle_pass.current_season.id
                ))
                
                # Award XP if completed
                if is_completed and not (row and row[1]):  # Not previously completed
                    self.battle_pass.award_xp(user_id, xp_reward, f"challenge_{challenge_id}")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error updating challenge progress: {e}")
    
    async def check_special_rewards(self, user_id: str, trade_data: Dict) -> List[Dict]:
        """Check for special one-time rewards based on achievements"""
        special_rewards = []
        
        # First win of the day
        if await self.is_first_win_today(user_id) and trade_data.get("result") == "win":
            special_rewards.append({
                "type": "daily_bonus",
                "name": "First Victory",
                "description": "First winning trade of the day",
                "xp_bonus": 100,
                "icon": "🏆"
            })
        
        # Perfect trade (90%+ TCS and win)
        if (trade_data.get("tcs_score", 0) >= 90 and 
            trade_data.get("result") == "win"):
            special_rewards.append({
                "type": "perfect_trade",
                "name": "Perfect Execution",
                "description": "Won a 90%+ TCS trade",
                "xp_bonus": 150,
                "icon": "🎯"
            })
        
        # Big win (50+ pips)
        if trade_data.get("profit_pips", 0) >= 50:
            special_rewards.append({
                "type": "big_win",
                "name": "Big Win",
                "description": "Earned 50+ pips in one trade",
                "xp_bonus": 200,
                "icon": "💰"
            })
        
        return special_rewards
    
    async def is_first_win_today(self, user_id: str) -> bool:
        """Check if this is the user's first win today"""
        try:
            import sqlite3
            
            # This would integrate with your existing trade tracking
            # For now, return a placeholder
            return False  # Implement based on your trade history system
            
        except Exception:
            return False
    
    def get_current_week(self) -> int:
        """Get current week number within the season"""
        if not self.battle_pass.current_season:
            return 1
        
        start_date = self.battle_pass.current_season.start_date
        current_date = datetime.now()
        days_since_start = (current_date - start_date).days
        
        return min((days_since_start // 7) + 1, 12)  # Max 12 weeks per season
    
    async def get_user_battle_pass_data(self, user_id: str) -> Dict:
        """Get comprehensive battle pass data for user"""
        progress = self.battle_pass.get_user_progress(user_id)
        if not progress or not self.battle_pass.current_season:
            return {"error": "No active season or user progress"}
        
        # Get available rewards for current level
        available_rewards = self.battle_pass.get_level_rewards(
            progress.level, progress.level, progress.pass_type
        )
        
        # Get claimable rewards
        claimable_levels = []
        for level in range(1, progress.level + 1):
            if level not in progress.rewards_claimed:
                level_rewards = self.battle_pass.get_level_rewards(
                    level, level, progress.pass_type
                )
                if level_rewards:
                    claimable_levels.append(level)
        
        # Get weekly challenges progress
        current_week = self.get_current_week()
        week_challenges = await self.get_user_challenge_progress(user_id, current_week)
        
        # Get leaderboard position
        leaderboard = self.battle_pass.get_season_leaderboard()
        user_rank = next((i + 1 for i, entry in enumerate(leaderboard) 
                         if entry['user_id'] == user_id), None)
        
        return {
            "season": {
                "id": self.battle_pass.current_season.id,
                "name": self.battle_pass.current_season.name,
                "description": self.battle_pass.current_season.description,
                "end_date": self.battle_pass.current_season.end_date.isoformat(),
                "current_week": current_week
            },
            "progress": {
                "level": progress.level,
                "xp": progress.xp,
                "xp_to_next": self.battle_pass.current_season.xp_per_level - progress.xp,
                "pass_type": progress.pass_type.value,
                "rewards_claimed": progress.rewards_claimed
            },
            "rewards": {
                "available": [r.to_dict() for r in available_rewards],
                "claimable_levels": claimable_levels
            },
            "challenges": week_challenges,
            "leaderboard": {
                "user_rank": user_rank,
                "total_players": len(leaderboard)
            }
        }
    
    async def get_user_challenge_progress(self, user_id: str, week: int) -> List[Dict]:
        """Get user's progress on weekly challenges"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(self.battle_pass.db_path)
            cursor = conn.cursor()
            
            # Get challenges for the week
            cursor.execute("""
                SELECT c.*, COALESCE(up.progress, 0) as user_progress, 
                       COALESCE(up.completed, 0) as completed
                FROM battle_pass_challenges c
                LEFT JOIN user_challenge_progress up 
                    ON c.id = up.challenge_id AND up.user_id = ?
                WHERE c.season_id = ? AND c.week = ?
            """, (user_id, self.battle_pass.current_season.id, week))
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            challenges = []
            for row in rows:
                challenge_dict = dict(zip(columns, row))
                
                # Parse target from objective
                objective = challenge_dict['objective']
                target = int(objective.split(":")[1]) if ":" in objective else 1
                
                challenges.append({
                    "id": challenge_dict['id'],
                    "name": challenge_dict['name'],
                    "description": challenge_dict['description'],
                    "objective": objective,
                    "xp_reward": challenge_dict['xp_reward'],
                    "tier_requirement": challenge_dict['tier_requirement'],
                    "progress": challenge_dict['user_progress'],
                    "target": target,
                    "completed": bool(challenge_dict['completed']),
                    "progress_percent": min(100, (challenge_dict['user_progress'] / target) * 100)
                })
            
            conn.close()
            return challenges
            
        except Exception as e:
            print(f"Error getting challenge progress: {e}")
            return []

# Global instance
battle_pass_integration = BattlePassIntegration()

# Integration functions for existing BITTEN system
async def award_battle_pass_xp(user_id: str, trade_data: Dict) -> Dict:
    """Main function to award battle pass XP from trading"""
    return await battle_pass_integration.award_trading_xp(user_id, trade_data)

async def get_battle_pass_status(user_id: str) -> Dict:
    """Get user's complete battle pass status"""
    return await battle_pass_integration.get_user_battle_pass_data(user_id)

def update_user_tier(user_id: str, new_tier: str) -> Dict:
    """Update user's subscription tier (affects battle pass access)"""
    return battle_pass_system.update_user_tier(user_id, new_tier)

def claim_battle_pass_reward(user_id: str, reward_id: str) -> Dict:
    """Claim specific reward (may cost XP)"""
    return battle_pass_system.claim_reward(user_id, reward_id)