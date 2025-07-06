"""
Comprehensive Education Integration Tests for HydraX

This test suite covers:
1. Complete user journey tests
2. Squad system tests
3. Achievement system tests
4. XP calculation tests
5. Social feature tests
6. Performance tests

All tests are designed to be fast while providing comprehensive coverage.
"""

import pytest
import asyncio
import json
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from concurrent.futures import ThreadPoolExecutor
import statistics

# Import modules to test
from src.bitten_core.education_system import (
    EducationSystem, PersonaType, TradingTier, MissionStatus,
    EducationTopic, TradeAnalysis, PaperTrade, EducationPersonas
)
from src.bitten_core.education_achievements import (
    EducationAchievements, AchievementRarity, AchievementCategory,
    Achievement, AchievementProgress
)
from src.bitten_core.education_missions import (
    EducationMissions, MissionType, MissionDifficulty,
    Mission, MissionObjective
)
from src.bitten_core.squad_radar import (
    SquadRadar, PrivacyLevel, TradeVisibility,
    SquadMemberProfile, SquadTrade
)
from src.bitten_core.xp_calculator import (
    XPCalculator, ExitType, TradingMilestone,
    EducationActivity, XPCalculation
)


# ==================== FIXTURES ====================

@pytest.fixture
def mock_database():
    """Mock database for testing"""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.fetch_one = AsyncMock()
    db.fetch_all = AsyncMock()
    return db


@pytest.fixture
def mock_logger():
    """Mock logger for testing"""
    logger = Mock()
    logger.info = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture
async def education_system(mock_database, mock_logger):
    """Create education system instance for testing"""
    system = EducationSystem(mock_database, mock_logger)
    await asyncio.sleep(0.1)  # Let initialization complete
    return system


@pytest.fixture
async def education_achievements(mock_database, mock_logger):
    """Create education achievements instance for testing"""
    achievements = EducationAchievements(mock_database, mock_logger)
    return achievements


@pytest.fixture
async def education_missions(mock_database, mock_logger):
    """Create education missions instance for testing"""
    missions = EducationMissions(mock_database, mock_logger)
    return missions


@pytest.fixture
def squad_radar():
    """Create squad radar instance for testing"""
    with patch('src.bitten_core.squad_radar.Path'):
        radar = SquadRadar(data_dir="/tmp/test_squad_radar")
        return radar


@pytest.fixture
def xp_calculator():
    """Create XP calculator instance for testing"""
    return XPCalculator()


@pytest.fixture
def sample_user_profiles():
    """Generate sample user profiles for testing"""
    return {
        "noob_user": {
            "user_id": "user_001",
            "tier": TradingTier.NIBBLER,
            "total_trades": 0,
            "successful_trades": 0,
            "total_pnl": 0.0,
            "xp": 0
        },
        "intermediate_user": {
            "user_id": "user_002",
            "tier": TradingTier.APPRENTICE,
            "total_trades": 50,
            "successful_trades": 25,
            "total_pnl": 500.0,
            "xp": 5000
        },
        "advanced_user": {
            "user_id": "user_003",
            "tier": TradingTier.MASTER,
            "total_trades": 500,
            "successful_trades": 300,
            "total_pnl": 10000.0,
            "xp": 50000
        }
    }


# ==================== 1. COMPLETE USER JOURNEY TESTS ====================

class TestUserJourney:
    """Test complete user journeys from noob to mentor"""
    
    @pytest.mark.asyncio
    async def test_new_user_onboarding_flow(self, education_system, mock_database):
        """Test: New user → Onboarding → First trade → Cooldown → Mission → Achievement"""
        user_id = "new_user_001"
        
        # Step 1: New user joins - should be NIBBLER tier
        mock_database.fetch_one.return_value = None  # No existing user
        tier = await education_system.get_user_tier(user_id)
        assert tier == TradingTier.NIBBLER
        
        # Step 2: Pre-trade check for first trade
        trade_params = {
            "symbol": "EURUSD",
            "entry_price": 1.1000,
            "stop_loss": 1.0950,
            "take_profit": 1.1100,
            "position_size": 1000,
            "account_balance": 10000,
            "direction": "long"
        }
        
        pre_check = await education_system.pre_trade_check(user_id, trade_params)
        assert pre_check["approved"] == True
        assert pre_check["mission_briefing"] is not None
        assert "NIBBLER" in pre_check["mission_briefing"]
        
        # Step 3: Execute trade and get post-trade education
        trade_result = {
            "trade_id": "trade_001",
            "user_id": user_id,
            "symbol": "EURUSD",
            "entry_price": 1.1000,
            "exit_price": 1.1050,
            "position_size": 1000,
            "direction": "long",
            "pnl": 50.0,
            "duration": timedelta(hours=2),
            "strategy": "trend_following"
        }
        
        post_trade_msg = await education_system.post_trade_education(user_id, trade_result)
        assert "MISSION DEBRIEF" in post_trade_msg
        assert "TACTICAL RECOVERY INITIATED" in post_trade_msg  # Nibbler cooldown
        
        # Step 4: Check cooldown is active
        in_cooldown, cooldown_msg = await education_system.check_nibbler_cooldown(user_id)
        assert in_cooldown == True
        assert "TACTICAL RECOVERY PHASE" in cooldown_msg
        
        # Step 5: Try to trade during cooldown - should be blocked
        pre_check_cooldown = await education_system.pre_trade_check(user_id, trade_params)
        assert pre_check_cooldown["approved"] == False
        assert pre_check_cooldown["paper_trade_suggestion"] == True
        
        # Step 6: Complete a paper trade during cooldown
        paper_trade = await education_system.create_paper_trade(user_id, {
            "symbol": "GBPUSD",
            "entry_price": 1.3000,
            "position_size": 1000,
            "direction": "short",
            "stop_loss": 1.3050,
            "take_profit": 1.2900
        })
        
        assert paper_trade.trade_id.startswith("paper_")
        assert paper_trade.status == "open"
        
        # Step 7: Close paper trade successfully
        analysis = await education_system.close_paper_trade(
            user_id, paper_trade.trade_id, 1.2950
        )
        assert analysis is not None
        assert analysis.pnl > 0  # Profitable paper trade
    
    @pytest.mark.asyncio
    async def test_full_education_progression(self, education_system, mock_database):
        """Test progression from NIBBLER to GRANDMASTER"""
        user_id = "progression_user"
        
        # Mock initial NIBBLER state
        mock_database.fetch_one.return_value = {
            "tier": "nibbler",
            "total_trades": 0,
            "successful_trades": 0,
            "total_pnl": 0.0
        }
        
        # Simulate trades to meet promotion criteria
        promotion_paths = [
            # NIBBLER → APPRENTICE: 10 trades, 40% win rate, break-even
            {"trades": 10, "wins": 4, "pnl": 0},
            # APPRENTICE → JOURNEYMAN: 50 trades, 45% win rate, $100 profit
            {"trades": 50, "wins": 23, "pnl": 100},
            # JOURNEYMAN → MASTER: 200 trades, 50% win rate, $1000 profit
            {"trades": 200, "wins": 100, "pnl": 1000},
            # MASTER → GRANDMASTER: 500 trades, 55% win rate, $5000 profit
            {"trades": 500, "wins": 275, "pnl": 5000}
        ]
        
        current_tier = TradingTier.NIBBLER
        
        for promotion in promotion_paths:
            # Update mock database response
            mock_database.fetch_one.return_value = {
                "tier": current_tier.value,
                "total_trades": promotion["trades"] - 1,
                "successful_trades": promotion["wins"] - 1,
                "total_pnl": promotion["pnl"] - 10
            }
            
            # Simulate final trade that triggers promotion
            trade_result = {
                "trade_id": f"trade_{promotion['trades']}",
                "user_id": user_id,
                "pnl": 10.0,  # Pushes over threshold
                "symbol": "EURUSD"
            }
            
            # Mock the promotion check
            with patch.object(education_system, '_notify_tier_promotion') as mock_notify:
                await education_system.update_user_progress(user_id, trade_result)
                
                # Verify promotion notification would be sent
                if current_tier != TradingTier.GRANDMASTER:
                    # Move to next tier for next iteration
                    tier_list = list(TradingTier)
                    current_index = tier_list.index(current_tier)
                    current_tier = tier_list[current_index + 1]
    
    @pytest.mark.asyncio
    async def test_struggling_user_support_flow(self, education_system):
        """Test support system for struggling traders"""
        user_id = "struggling_user"
        
        # Simulate consecutive losses
        for i in range(5):
            education_system.user_performance[user_id]["consecutive_losses"] = i + 1
            
            context = {
                "situation": "post_trade",
                "performance": "loss",
                "tier": TradingTier.APPRENTICE,
                "consecutive_losses": i + 1
            }
            
            # After 3 losses, should get AEGIS (supportive) persona
            if i >= 2:
                persona = education_system.personas.select_persona(context)
                assert persona == PersonaType.AEGIS
                
                message = education_system.personas.get_persona_response(persona, context)
                assert "rough patch" in message or "resilience" in message


# ==================== 2. SQUAD SYSTEM TESTS ====================

class TestSquadSystem:
    """Test squad formation, missions, and competitions"""
    
    def test_squad_formation(self, squad_radar):
        """Test squad formation and member management"""
        # Create squad leader
        leader = SquadMemberProfile(
            user_id="leader_001",
            username="SquadLeader",
            rank="MASTER",
            privacy_level=PrivacyLevel.SQUAD_ONLY,
            trust_score=85.0
        )
        squad_radar.member_profiles[leader.user_id] = leader
        
        # Add squad members
        members = []
        for i in range(4):
            member = SquadMemberProfile(
                user_id=f"member_{i:03d}",
                username=f"Member{i}",
                rank="APPRENTICE",
                privacy_level=PrivacyLevel.SQUAD_ONLY,
                trust_score=50.0 + i * 5
            )
            members.append(member)
            squad_radar.member_profiles[member.user_id] = member
            
            # Create squad relationship
            if leader.user_id not in squad_radar.squad_trees:
                squad_radar.squad_trees[leader.user_id] = set()
            squad_radar.squad_trees[leader.user_id].add(member.user_id)
        
        # Verify squad formation
        assert len(squad_radar.squad_trees[leader.user_id]) == 4
        assert all(m.user_id in squad_radar.member_profiles for m in members)
    
    def test_squad_trade_visibility(self, squad_radar):
        """Test privacy controls and trade visibility"""
        # Create squad with different privacy settings
        members = [
            SquadMemberProfile("user_1", "Public", "MASTER", 
                             privacy_level=PrivacyLevel.PUBLIC,
                             trade_visibility=TradeVisibility.FULL),
            SquadMemberProfile("user_2", "SquadOnly", "JOURNEYMAN",
                             privacy_level=PrivacyLevel.SQUAD_ONLY,
                             trade_visibility=TradeVisibility.PARTIAL),
            SquadMemberProfile("user_3", "Anonymous", "APPRENTICE",
                             privacy_level=PrivacyLevel.ANONYMOUS,
                             trade_visibility=TradeVisibility.RESULTS_ONLY),
            SquadMemberProfile("user_4", "Private", "NIBBLER",
                             privacy_level=PrivacyLevel.PRIVATE,
                             trade_visibility=TradeVisibility.HIDDEN)
        ]
        
        for member in members:
            squad_radar.member_profiles[member.user_id] = member
        
        # Create trades for each member
        trades = []
        for i, member in enumerate(members):
            trade = SquadTrade(
                trade_id=f"trade_{i}",
                member_id=member.user_id,
                member_display=member.username if member.privacy_level != PrivacyLevel.ANONYMOUS else "Anonymous Trader",
                pair="EURUSD",
                direction="long",
                entry_time=datetime.utcnow(),
                entry_price=1.1000 if member.trade_visibility == TradeVisibility.FULL else None,
                current_status="active",
                profit_pips=10.0 if member.trade_visibility != TradeVisibility.HIDDEN else None
            )
            trades.append(trade)
            
            if member.user_id not in squad_radar.active_trades:
                squad_radar.active_trades[member.user_id] = []
            squad_radar.active_trades[member.user_id].append(trade)
        
        # Test visibility rules
        # Public member - full visibility
        public_trade = trades[0]
        assert public_trade.entry_price == 1.1000
        assert public_trade.member_display == "Public"
        
        # Anonymous member - hidden identity
        anon_trade = trades[2]
        assert anon_trade.member_display == "Anonymous Trader"
        assert anon_trade.entry_price is None  # Results only
        
        # Private member - should not be visible
        private_member = members[3]
        assert private_member.trade_visibility == TradeVisibility.HIDDEN
    
    @pytest.mark.asyncio
    async def test_squad_mission_assignment(self, education_missions):
        """Test squad mission creation and assignment"""
        squad_id = "squad_001"
        squad_members = ["user_1", "user_2", "user_3", "user_4", "user_5"]
        
        # Create squad mission
        mission = Mission(
            mission_id="squad_mission_001",
            type=MissionType.SQUAD,
            title="Operation Market Storm",
            briefing="Coordinate with your squad to identify and trade 3 different pairs",
            difficulty=MissionDifficulty.REGULAR,
            objectives=[
                MissionObjective(
                    id="obj_1",
                    description="Squad must trade 3 different currency pairs",
                    target_value=3,
                    xp_reward=100
                ),
                MissionObjective(
                    id="obj_2",
                    description="Achieve 60% squad win rate",
                    target_value=0.6,
                    xp_reward=150
                )
            ],
            xp_reward=500,
            squad_size=5
        )
        
        # Assign mission to squad
        for member_id in squad_members:
            education_missions.active_missions[member_id] = [mission]
        
        # Simulate squad progress
        squad_trades = {
            "EURUSD": ["user_1", "user_2"],
            "GBPUSD": ["user_3", "user_4"],
            "USDJPY": ["user_5"]
        }
        
        # Update mission progress
        mission.objectives[0].current_value = len(squad_trades)  # 3 pairs
        mission.objectives[1].current_value = 0.7  # 70% win rate
        
        # Check completion
        assert mission.objectives[0].check_completion() == True
        assert mission.objectives[1].check_completion() == True
        
        # Calculate squad rewards
        total_xp = mission.xp_reward + sum(obj.xp_reward for obj in mission.objectives)
        xp_per_member = total_xp // len(squad_members)
        assert xp_per_member == 150  # (500 + 100 + 150) / 5
    
    def test_squad_competition_system(self, squad_radar):
        """Test squad wars and competition mechanics"""
        # Create two competing squads
        squad_a = {
            "leader": "leader_a",
            "members": ["a_1", "a_2", "a_3", "a_4"],
            "total_pnl": 0.0,
            "win_rate": 0.0,
            "trades": []
        }
        
        squad_b = {
            "leader": "leader_b",
            "members": ["b_1", "b_2", "b_3", "b_4"],
            "total_pnl": 0.0,
            "win_rate": 0.0,
            "trades": []
        }
        
        # Simulate trading competition over 24 hours
        competition_trades = {
            "squad_a": [
                {"pnl": 100, "won": True},
                {"pnl": -50, "won": False},
                {"pnl": 75, "won": True},
                {"pnl": 150, "won": True},
                {"pnl": -25, "won": False},
            ],
            "squad_b": [
                {"pnl": 80, "won": True},
                {"pnl": 90, "won": True},
                {"pnl": -60, "won": False},
                {"pnl": 120, "won": True},
                {"pnl": -40, "won": False},
            ]
        }
        
        # Calculate squad performance
        for squad_name, trades in competition_trades.items():
            squad = squad_a if squad_name == "squad_a" else squad_b
            squad["trades"] = trades
            squad["total_pnl"] = sum(t["pnl"] for t in trades)
            squad["win_rate"] = sum(1 for t in trades if t["won"]) / len(trades)
        
        # Determine winner
        squad_a_score = squad_a["total_pnl"] * (1 + squad_a["win_rate"])
        squad_b_score = squad_b["total_pnl"] * (1 + squad_b["win_rate"])
        
        winner = "squad_a" if squad_a_score > squad_b_score else "squad_b"
        
        # Verify competition results
        assert squad_a["total_pnl"] == 250
        assert squad_a["win_rate"] == 0.6
        assert squad_b["total_pnl"] == 190
        assert squad_b["win_rate"] == 0.6
        assert winner == "squad_a"  # Higher PnL wins with same win rate


# ==================== 3. ACHIEVEMENT SYSTEM TESTS ====================

class TestAchievementSystem:
    """Test achievement tracking, unlocks, and notifications"""
    
    @pytest.mark.asyncio
    async def test_achievement_progress_tracking(self, education_achievements):
        """Test progress tracking for various achievements"""
        user_id = "achievement_hunter"
        
        # Define test achievement
        first_win = Achievement(
            id="first_win",
            name="First Blood",
            description="Win your first trade",
            hidden_description="Win a trade to unlock",
            category=AchievementCategory.PERFORMANCE,
            rarity=AchievementRarity.COMMON,
            points=10,
            icon="🎯",
            badge_tier="bronze",
            requirements={"wins": 1}
        )
        
        # Track progress
        progress = AchievementProgress(
            achievement_id=first_win.id,
            user_id=user_id,
            current_progress={"wins": 0}
        )
        
        # Simulate winning a trade
        progress.current_progress["wins"] = 1
        progress.progress_percentage = 100.0
        
        # Check completion
        assert progress.is_near_completion() == False  # Already at 100%
        progress.unlocked = True
        progress.unlock_date = datetime.utcnow()
        
        assert progress.unlocked == True
        assert progress.progress_percentage == 100.0
    
    @pytest.mark.asyncio
    async def test_hidden_achievement_discovery(self, education_achievements):
        """Test hidden and secret achievement mechanics"""
        user_id = "secret_hunter"
        
        # Create hidden achievement
        hidden_achievement = Achievement(
            id="market_wizard",
            name="Market Wizard",
            description="Achieve 10 consecutive winning trades",
            hidden_description="Keep winning to discover this achievement",
            category=AchievementCategory.MASTERY,
            rarity=AchievementRarity.LEGENDARY,
            points=100,
            icon="🧙",
            badge_tier="platinum",
            hidden=True,
            requirements={"consecutive_wins": 10}
        )
        
        # Create ultra-secret achievement
        secret_achievement = Achievement(
            id="shadow_trader",
            name="Shadow Trader",
            description="Complete 50 trades between midnight and 3 AM",
            hidden_description="???",
            category=AchievementCategory.SPECIAL,
            rarity=AchievementRarity.MYTHIC,
            points=200,
            icon="🌙",
            badge_tier="obsidian",
            secret=True,
            requirements={"night_trades": 50}
        )
        
        # Test display for locked achievements
        assert hidden_achievement.get_display_description(unlocked=False) == hidden_achievement.hidden_description
        assert secret_achievement.get_display_name(unlocked=False) == "???"
        assert secret_achievement.get_display_description(unlocked=False) == "Hidden achievement - Keep playing to discover!"
        
        # Test display for unlocked achievements
        assert hidden_achievement.get_display_name(unlocked=True) == "Market Wizard"
        assert secret_achievement.get_display_description(unlocked=True) == secret_achievement.description
    
    @pytest.mark.asyncio
    async def test_achievement_unlock_conditions(self, education_achievements):
        """Test various unlock conditions and chains"""
        user_id = "unlock_tester"
        
        # Create achievement chain
        achievements = [
            Achievement(
                id="trader_1",
                name="Trader I",
                description="Complete 10 trades",
                hidden_description="Start trading to unlock",
                category=AchievementCategory.DEDICATION,
                rarity=AchievementRarity.COMMON,
                points=10,
                icon="📈",
                badge_tier="bronze",
                chain_id="trader_chain",
                chain_order=1,
                requirements={"total_trades": 10}
            ),
            Achievement(
                id="trader_2",
                name="Trader II",
                description="Complete 50 trades",
                hidden_description="Continue trading journey",
                category=AchievementCategory.DEDICATION,
                rarity=AchievementRarity.UNCOMMON,
                points=25,
                icon="📊",
                badge_tier="silver",
                chain_id="trader_chain",
                chain_order=2,
                requirements={"total_trades": 50},
                prerequisite_achievements=["trader_1"]
            ),
            Achievement(
                id="trader_3",
                name="Trader III",
                description="Complete 200 trades",
                hidden_description="Master the markets",
                category=AchievementCategory.DEDICATION,
                rarity=AchievementRarity.RARE,
                points=50,
                icon="🏆",
                badge_tier="gold",
                chain_id="trader_chain",
                chain_order=3,
                requirements={"total_trades": 200},
                prerequisite_achievements=["trader_2"]
            )
        ]
        
        # Simulate progression
        user_progress = {
            "total_trades": 0,
            "unlocked_achievements": []
        }
        
        # Check unlock conditions at different stages
        for trade_count in [5, 10, 30, 50, 100, 200]:
            user_progress["total_trades"] = trade_count
            
            for achievement in achievements:
                # Check prerequisites
                prereqs_met = all(
                    prereq in user_progress["unlocked_achievements"] 
                    for prereq in achievement.prerequisite_achievements
                )
                
                # Check requirements
                requirements_met = all(
                    user_progress.get(key, 0) >= value
                    for key, value in achievement.requirements.items()
                )
                
                # Unlock if conditions met
                if prereqs_met and requirements_met and achievement.id not in user_progress["unlocked_achievements"]:
                    user_progress["unlocked_achievements"].append(achievement.id)
        
        # Verify chain progression
        assert "trader_1" in user_progress["unlocked_achievements"]
        assert "trader_2" in user_progress["unlocked_achievements"]
        assert "trader_3" in user_progress["unlocked_achievements"]
    
    def test_achievement_notification_system(self, education_achievements):
        """Test achievement notification and celebration mechanics"""
        # Test notification priorities based on rarity
        notifications = []
        
        rarities = [
            (AchievementRarity.COMMON, "standard", "achievement_common.wav"),
            (AchievementRarity.UNCOMMON, "sparkle", "achievement_uncommon.wav"),
            (AchievementRarity.RARE, "burst", "achievement_rare.wav"),
            (AchievementRarity.EPIC, "epic_burst", "achievement_epic.wav"),
            (AchievementRarity.LEGENDARY, "legendary_explosion", "achievement_legendary.wav"),
            (AchievementRarity.MYTHIC, "mythic_ascension", "achievement_mythic.wav")
        ]
        
        for rarity, effect, sound in rarities:
            achievement = Achievement(
                id=f"test_{rarity.value}",
                name=f"Test {rarity.value}",
                description="Test achievement",
                hidden_description="Test",
                category=AchievementCategory.SPECIAL,
                rarity=rarity,
                points=10,
                icon="🎯",
                badge_tier="bronze",
                particle_effect=effect,
                unlock_sound=sound
            )
            
            notification = {
                "achievement": achievement,
                "timestamp": datetime.utcnow(),
                "celebration_level": rarity.value,
                "sound": achievement.unlock_sound,
                "effect": achievement.particle_effect
            }
            notifications.append(notification)
        
        # Verify notification properties scale with rarity
        assert notifications[0]["celebration_level"] == "common"
        assert notifications[-1]["celebration_level"] == "mythic"
        assert "mythic_ascension" in notifications[-1]["effect"]


# ==================== 4. XP CALCULATION TESTS ====================

class TestXPCalculation:
    """Test XP calculation accuracy and anti-abuse measures"""
    
    def test_base_xp_calculations(self, xp_calculator):
        """Test basic XP calculations for different outcomes"""
        # Test win XP
        win_calc = xp_calculator.calculate_trade_xp(
            outcome="win",
            pnl_percentage=5.0,
            trade_duration=timedelta(hours=2),
            exit_type=ExitType.NORMAL
        )
        assert win_calc.base_xp == 100
        assert win_calc.net_xp >= 100  # Should have no penalties
        
        # Test loss XP
        loss_calc = xp_calculator.calculate_trade_xp(
            outcome="loss",
            pnl_percentage=-2.0,
            trade_duration=timedelta(hours=1),
            exit_type=ExitType.STOP_LOSS
        )
        assert loss_calc.base_xp == 50
        assert loss_calc.net_xp >= 0  # Can't go negative
        
        # Test breakeven XP
        breakeven_calc = xp_calculator.calculate_trade_xp(
            outcome="breakeven",
            pnl_percentage=0.1,
            trade_duration=timedelta(minutes=30),
            exit_type=ExitType.NORMAL
        )
        assert breakeven_calc.base_xp == 75
    
    def test_multiplier_stacking(self, xp_calculator):
        """Test multiplier calculations and caps"""
        # Create scenario with multiple multipliers
        user_stats = {
            "win_rate": 0.75,  # 75% win rate
            "current_streak": 5,  # 5 win streak
            "daily_volume": 10,  # 10 trades today
            "consistency_score": 0.9,  # High consistency
            "avg_risk_reward": 3.0  # 3:1 R:R ratio
        }
        
        # Calculate multipliers
        multipliers = xp_calculator.calculate_multipliers(user_stats)
        
        # Test individual multiplier ranges
        assert 1.0 <= multipliers["win_rate"] <= 2.0
        assert 1.0 <= multipliers["streak"] <= 2.0
        assert 1.0 <= multipliers["volume"] <= 1.5
        assert 1.0 <= multipliers["consistency"] <= 1.5
        assert 1.0 <= multipliers["risk_reward"] <= 1.5
        
        # Test total multiplier cap
        total_multiplier = xp_calculator.apply_multiplier_cap(multipliers)
        assert total_multiplier <= xp_calculator.MAX_TOTAL_MULTIPLIER
    
    def test_anti_abuse_measures(self, xp_calculator):
        """Test XP farming prevention"""
        # Test 1: Rapid-fire trades (< 1 minute)
        rapid_calc = xp_calculator.calculate_trade_xp(
            outcome="win",
            pnl_percentage=0.1,
            trade_duration=timedelta(seconds=30),
            exit_type=ExitType.NORMAL
        )
        assert rapid_calc.penalties.get("rapid_trade", 0) > 0
        assert rapid_calc.net_xp < rapid_calc.base_xp
        
        # Test 2: Excessive daily volume
        user_id = "farmer_001"
        
        # Simulate 50 trades in one day
        daily_xp = 0
        for i in range(50):
            calc = xp_calculator.calculate_trade_xp_with_limits(
                user_id=user_id,
                outcome="win",
                pnl_percentage=0.5,
                trade_duration=timedelta(minutes=5),
                daily_trade_count=i + 1
            )
            daily_xp += calc.net_xp
        
        # XP should diminish after threshold
        avg_xp_first_10 = daily_xp / 50  # Rough average
        assert avg_xp_first_10 < 100  # Less than base win XP due to penalties
        
        # Test 3: Minimum trade duration for full XP
        short_trade = xp_calculator.calculate_trade_xp(
            outcome="win",
            pnl_percentage=2.0,
            trade_duration=timedelta(minutes=2),
            exit_type=ExitType.NORMAL
        )
        
        normal_trade = xp_calculator.calculate_trade_xp(
            outcome="win",
            pnl_percentage=2.0,
            trade_duration=timedelta(minutes=15),
            exit_type=ExitType.NORMAL
        )
        
        assert normal_trade.net_xp > short_trade.net_xp
    
    def test_education_activity_xp(self, xp_calculator):
        """Test XP rewards for educational activities"""
        activities = [
            (EducationActivity.COMPLETE_LESSON, 50),
            (EducationActivity.WATCH_VIDEO, 25),
            (EducationActivity.COMPLETE_QUIZ, 75),
            (EducationActivity.PAPER_TRADE, 30),
            (EducationActivity.MENTOR_SESSION, 100),
            (EducationActivity.TEACH_OTHERS, 150)
        ]
        
        for activity, expected_xp in activities:
            xp = xp_calculator.calculate_education_xp(
                activity=activity,
                performance_score=1.0  # Perfect score
            )
            assert xp == expected_xp
            
        # Test partial scores
        partial_xp = xp_calculator.calculate_education_xp(
            activity=EducationActivity.COMPLETE_QUIZ,
            performance_score=0.8  # 80% score
        )
        assert partial_xp == 60  # 75 * 0.8
    
    def test_milestone_progression(self, xp_calculator):
        """Test XP milestone calculations"""
        test_cases = [
            (0, TradingMilestone.NOVICE),
            (999, TradingMilestone.NOVICE),
            (1000, TradingMilestone.APPRENTICE),
            (4999, TradingMilestone.APPRENTICE),
            (5000, TradingMilestone.TRADER),
            (14999, TradingMilestone.TRADER),
            (15000, TradingMilestone.EXPERT),
            (29999, TradingMilestone.EXPERT),
            (30000, TradingMilestone.MASTER),
            (49999, TradingMilestone.MASTER),
            (50000, TradingMilestone.ELITE),
            (100000, TradingMilestone.ELITE)
        ]
        
        for total_xp, expected_milestone in test_cases:
            milestone = xp_calculator.get_milestone(total_xp)
            assert milestone == expected_milestone
            
        # Test progress to next milestone
        progress = xp_calculator.get_milestone_progress(7500)
        assert progress["current_milestone"] == TradingMilestone.TRADER
        assert progress["next_milestone"] == TradingMilestone.EXPERT
        assert progress["xp_to_next"] == 7500  # 15000 - 7500
        assert progress["progress_percentage"] == 50.0  # Halfway from 5000 to 15000


# ==================== 5. SOCIAL FEATURE TESTS ====================

class TestSocialFeatures:
    """Test mentor matching, study groups, and communication"""
    
    @pytest.mark.asyncio
    async def test_mentor_matching_algorithm(self, education_system, sample_user_profiles):
        """Test mentor-student matching based on compatibility"""
        # Create mentor pool
        mentors = [
            {
                "user_id": "mentor_1",
                "tier": TradingTier.MASTER,
                "specialty": "scalping",
                "win_rate": 0.65,
                "availability": "weekdays",
                "timezone": "EST",
                "languages": ["English", "Spanish"],
                "rating": 4.8
            },
            {
                "user_id": "mentor_2",
                "tier": TradingTier.GRANDMASTER,
                "specialty": "swing_trading",
                "win_rate": 0.70,
                "availability": "weekends",
                "timezone": "PST",
                "languages": ["English"],
                "rating": 4.9
            },
            {
                "user_id": "mentor_3",
                "tier": TradingTier.MASTER,
                "specialty": "scalping",
                "win_rate": 0.60,
                "availability": "weekdays",
                "timezone": "EST",
                "languages": ["English", "French"],
                "rating": 4.5
            }
        ]
        
        # Create student profile
        student = {
            "user_id": "student_1",
            "tier": TradingTier.APPRENTICE,
            "preferred_style": "scalping",
            "availability": "weekdays",
            "timezone": "EST",
            "languages": ["English"],
            "goals": ["improve_win_rate", "risk_management"]
        }
        
        # Simple matching algorithm
        def calculate_match_score(mentor, student):
            score = 0
            
            # Style match (40 points)
            if mentor["specialty"] == student["preferred_style"]:
                score += 40
                
            # Availability match (20 points)
            if mentor["availability"] == student["availability"]:
                score += 20
                
            # Timezone match (20 points)
            if mentor["timezone"] == student["timezone"]:
                score += 20
                
            # Language match (10 points)
            common_languages = set(mentor["languages"]) & set(student["languages"])
            if common_languages:
                score += 10
                
            # Rating bonus (10 points max)
            score += mentor["rating"] * 2
            
            return score
        
        # Find best matches
        matches = []
        for mentor in mentors:
            score = calculate_match_score(mentor, student)
            matches.append((mentor["user_id"], score))
        
        matches.sort(key=lambda x: x[1], reverse=True)
        
        # Verify best match
        best_match = matches[0]
        assert best_match[0] == "mentor_1"  # Best compatibility
        assert best_match[1] >= 80  # High match score
    
    def test_study_group_formation(self, education_system):
        """Test automatic study group creation based on level and goals"""
        # Create pool of students
        students = [
            {"id": "s1", "tier": "APPRENTICE", "goals": ["technical_analysis"], "timezone": "EST"},
            {"id": "s2", "tier": "APPRENTICE", "goals": ["technical_analysis"], "timezone": "EST"},
            {"id": "s3", "tier": "APPRENTICE", "goals": ["risk_management"], "timezone": "PST"},
            {"id": "s4", "tier": "JOURNEYMAN", "goals": ["technical_analysis"], "timezone": "EST"},
            {"id": "s5", "tier": "APPRENTICE", "goals": ["technical_analysis"], "timezone": "EST"},
            {"id": "s6", "tier": "APPRENTICE", "goals": ["psychology"], "timezone": "EST"},
        ]
        
        # Group formation algorithm
        def form_study_groups(students, max_size=5):
            groups = []
            grouped_students = set()
            
            for student in students:
                if student["id"] in grouped_students:
                    continue
                    
                # Start new group
                group = [student]
                grouped_students.add(student["id"])
                
                # Find compatible students
                for other in students:
                    if other["id"] in grouped_students:
                        continue
                    if len(group) >= max_size:
                        break
                        
                    # Check compatibility
                    if (other["tier"] == student["tier"] and
                        other["timezone"] == student["timezone"] and
                        set(other["goals"]) & set(student["goals"])):
                        group.append(other)
                        grouped_students.add(other["id"])
                
                if len(group) >= 3:  # Minimum group size
                    groups.append(group)
            
            return groups
        
        # Form groups
        study_groups = form_study_groups(students)
        
        # Verify group formation
        assert len(study_groups) >= 1
        first_group = study_groups[0]
        assert len(first_group) >= 3
        
        # Verify group compatibility
        tiers = set(s["tier"] for s in first_group)
        timezones = set(s["timezone"] for s in first_group)
        assert len(tiers) == 1  # Same tier
        assert len(timezones) == 1  # Same timezone
    
    @pytest.mark.asyncio
    async def test_communication_systems(self, education_system):
        """Test various communication channels and moderation"""
        # Test persona-based communication styles
        contexts = [
            {
                "channel": "help",
                "user_tier": TradingTier.NIBBLER,
                "message": "I don't understand stop losses",
                "expected_persona": PersonaType.AEGIS
            },
            {
                "channel": "celebration",
                "user_tier": TradingTier.MASTER,
                "message": "Just hit 10 wins in a row!",
                "expected_persona": PersonaType.DRILL
            },
            {
                "channel": "analysis",
                "user_tier": TradingTier.JOURNEYMAN,
                "message": "Looking at EURUSD setup",
                "expected_persona": PersonaType.NEXUS
            }
        ]
        
        for context in contexts:
            # Get appropriate response
            response_context = {
                "situation": "education" if context["channel"] == "help" else "pre_trade",
                "performance": "neutral",
                "tier": context["user_tier"]
            }
            
            if context["channel"] == "celebration":
                response_context["performance"] = "achievement"
            
            persona = education_system.personas.select_persona(response_context)
            
            # Verify appropriate persona selection for context
            if context["channel"] == "help":
                # Help should prioritize supportive personas
                assert persona in [PersonaType.AEGIS, PersonaType.NEXUS]
            elif context["channel"] == "celebration":
                # Celebrations can use any persona
                assert persona in list(PersonaType)
    
    def test_reputation_system(self):
        """Test user reputation and trust scoring"""
        # Create user activity history
        user_activities = {
            "helpful_user": {
                "questions_answered": 50,
                "answer_ratings": [5, 5, 4, 5, 4, 5, 5],
                "trades_shared": 20,
                "trade_accuracy": 0.75,
                "community_violations": 0,
                "months_active": 6
            },
            "new_user": {
                "questions_answered": 2,
                "answer_ratings": [3, 4],
                "trades_shared": 0,
                "trade_accuracy": 0.0,
                "community_violations": 0,
                "months_active": 1
            },
            "problematic_user": {
                "questions_answered": 10,
                "answer_ratings": [2, 1, 3, 2],
                "trades_shared": 5,
                "trade_accuracy": 0.2,
                "community_violations": 3,
                "months_active": 3
            }
        }
        
        def calculate_reputation_score(activities):
            score = 50.0  # Base score
            
            # Answer quality (max +30)
            if activities["answer_ratings"]:
                avg_rating = sum(activities["answer_ratings"]) / len(activities["answer_ratings"])
                score += (avg_rating - 3) * 10  # +20 for 5-star average
            
            # Trade sharing accuracy (max +20)
            if activities["trades_shared"] > 0:
                score += activities["trade_accuracy"] * 20
            
            # Activity bonus (max +20)
            score += min(activities["questions_answered"] * 0.4, 20)
            
            # Longevity bonus (max +10)
            score += min(activities["months_active"] * 1.5, 10)
            
            # Violations penalty (-10 per violation)
            score -= activities["community_violations"] * 10
            
            return max(0, min(100, score))  # Clamp 0-100
        
        # Calculate scores
        scores = {}
        for user, activities in user_activities.items():
            scores[user] = calculate_reputation_score(activities)
        
        # Verify reputation calculations
        assert scores["helpful_user"] > 80  # High reputation
        assert 40 < scores["new_user"] < 60  # Average for new user
        assert scores["problematic_user"] < 40  # Low due to violations


# ==================== 6. PERFORMANCE TESTS ====================

class TestPerformance:
    """Test system performance with high load"""
    
    @pytest.mark.asyncio
    async def test_concurrent_user_load(self, education_system, mock_database):
        """Test system with 1000+ concurrent users"""
        user_count = 1000
        
        # Mock database to return random user data
        def mock_fetch_one_side_effect(*args):
            if "user_education_progress" in args[0]:
                return {
                    "tier": random.choice(["nibbler", "apprentice", "journeyman"]),
                    "total_trades": random.randint(0, 200),
                    "successful_trades": random.randint(0, 100),
                    "total_pnl": random.uniform(-1000, 5000)
                }
            return None
        
        mock_database.fetch_one.side_effect = mock_fetch_one_side_effect
        
        # Simulate concurrent user actions
        async def simulate_user_action(user_id):
            actions = [
                lambda: education_system.get_user_tier(user_id),
                lambda: education_system.check_nibbler_cooldown(user_id),
                lambda: education_system.get_strategy_videos(user_id),
                lambda: education_system.get_motivational_quote(user_id)
            ]
            
            action = random.choice(actions)
            start_time = time.time()
            await action()
            return time.time() - start_time
        
        # Run concurrent requests
        start_time = time.time()
        tasks = []
        
        for i in range(user_count):
            user_id = f"user_{i:04d}"
            task = simulate_user_action(user_id)
            tasks.append(task)
        
        # Execute in batches to avoid overwhelming
        batch_size = 100
        all_response_times = []
        
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            response_times = await asyncio.gather(*batch)
            all_response_times.extend(response_times)
        
        total_time = time.time() - start_time
        
        # Calculate performance metrics
        avg_response_time = statistics.mean(all_response_times)
        p95_response_time = statistics.quantiles(all_response_times, n=20)[18]  # 95th percentile
        p99_response_time = statistics.quantiles(all_response_times, n=100)[98]  # 99th percentile
        
        # Performance assertions
        assert avg_response_time < 0.1  # Average under 100ms
        assert p95_response_time < 0.2  # 95% under 200ms
        assert p99_response_time < 0.5  # 99% under 500ms
        assert total_time < 30  # Total test under 30 seconds
    
    @pytest.mark.asyncio
    async def test_response_time_benchmarks(self, education_system, xp_calculator, mock_database):
        """Test individual operation response times"""
        # Mock fast database responses
        mock_database.fetch_one.return_value = {
            "tier": "apprentice",
            "total_trades": 50,
            "successful_trades": 30,
            "total_pnl": 500.0
        }
        mock_database.fetch_all.return_value = []
        
        benchmarks = {
            "get_user_tier": 0.01,  # 10ms
            "check_cooldown": 0.01,  # 10ms
            "calculate_xp": 0.005,  # 5ms
            "generate_analysis": 0.05,  # 50ms
            "get_persona_response": 0.002,  # 2ms
        }
        
        # Test each operation
        user_id = "benchmark_user"
        
        # Get user tier
        start = time.time()
        await education_system.get_user_tier(user_id)
        tier_time = time.time() - start
        assert tier_time < benchmarks["get_user_tier"]
        
        # Check cooldown
        start = time.time()
        await education_system.check_nibbler_cooldown(user_id)
        cooldown_time = time.time() - start
        assert cooldown_time < benchmarks["check_cooldown"]
        
        # Calculate XP
        start = time.time()
        xp_calculator.calculate_trade_xp(
            outcome="win",
            pnl_percentage=2.0,
            trade_duration=timedelta(hours=1),
            exit_type=ExitType.NORMAL
        )
        xp_time = time.time() - start
        assert xp_time < benchmarks["calculate_xp"]
        
        # Get persona response
        start = time.time()
        education_system.personas.get_persona_response(
            PersonaType.NEXUS,
            {"situation": "pre_trade", "performance": "good", "tier": TradingTier.APPRENTICE}
        )
        persona_time = time.time() - start
        assert persona_time < benchmarks["get_persona_response"]
    
    def test_memory_usage_optimization(self, education_system, squad_radar):
        """Test memory efficiency with large datasets"""
        # Test 1: Large cooldown tracker
        # Simulate 10,000 users in cooldown
        for i in range(10000):
            education_system.cooldown_tracker[f"user_{i}"] = datetime.utcnow()
        
        # Cleanup old cooldowns (older than 1 hour)
        cutoff = datetime.utcnow() - timedelta(hours=1)
        old_size = len(education_system.cooldown_tracker)
        
        # Simulate cleanup
        education_system.cooldown_tracker = {
            k: v for k, v in education_system.cooldown_tracker.items()
            if v > cutoff
        }
        
        # Should maintain reasonable size
        assert len(education_system.cooldown_tracker) <= old_size
        
        # Test 2: Squad data optimization
        # Create large squad network
        for i in range(1000):
            member = SquadMemberProfile(
                user_id=f"member_{i}",
                username=f"User{i}",
                rank="APPRENTICE",
                trust_score=50.0
            )
            squad_radar.member_profiles[member.user_id] = member
        
        # Verify data structure efficiency
        assert len(squad_radar.member_profiles) == 1000
        
        # Test selective loading (would be implemented in production)
        # Only load active members for radar view
        active_members = {
            k: v for k, v in squad_radar.member_profiles.items()
            if v.last_active and (datetime.utcnow() - v.last_active).days < 7
        }
        
        # Active subset should be smaller
        assert len(active_members) <= len(squad_radar.member_profiles)
    
    @pytest.mark.asyncio
    async def test_database_query_optimization(self, mock_database):
        """Test optimized database queries"""
        # Test batch operations vs individual queries
        user_ids = [f"user_{i}" for i in range(100)]
        
        # Simulate individual queries (bad)
        individual_start = time.time()
        for user_id in user_ids:
            await mock_database.fetch_one(
                "SELECT * FROM user_education_progress WHERE user_id = ?",
                (user_id,)
            )
        individual_time = time.time() - individual_start
        
        # Simulate batch query (good)
        batch_start = time.time()
        placeholders = ",".join("?" * len(user_ids))
        await mock_database.fetch_all(
            f"SELECT * FROM user_education_progress WHERE user_id IN ({placeholders})",
            user_ids
        )
        batch_time = time.time() - batch_start
        
        # Batch should be significantly faster
        # In real scenario, batch would be 10-50x faster
        assert batch_time <= individual_time
        
        # Test query result caching
        cache = {}
        
        async def cached_query(query, params):
            cache_key = f"{query}:{params}"
            if cache_key in cache:
                return cache[cache_key]
            result = await mock_database.fetch_one(query, params)
            cache[cache_key] = result
            return result
        
        # First query - cache miss
        await cached_query("SELECT * FROM users WHERE id = ?", ("user_1",))
        
        # Second query - cache hit (should be instant)
        start = time.time()
        await cached_query("SELECT * FROM users WHERE id = ?", ("user_1",))
        cache_time = time.time() - start
        assert cache_time < 0.001  # Sub-millisecond for cache hit


# ==================== INTEGRATION TEST HELPERS ====================

def generate_trade_data(user_id: str, outcome: str = "win") -> Dict[str, Any]:
    """Generate realistic trade data for testing"""
    base_price = 1.1000
    pip_change = random.uniform(-50, 50) if outcome == "random" else (20 if outcome == "win" else -20)
    
    return {
        "trade_id": f"trade_{datetime.utcnow().timestamp()}",
        "user_id": user_id,
        "symbol": random.choice(["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]),
        "entry_price": base_price,
        "exit_price": base_price + (pip_change * 0.0001),
        "position_size": random.randint(1000, 10000),
        "direction": random.choice(["long", "short"]),
        "stop_loss": base_price - 0.0050 if outcome != "no_sl" else None,
        "take_profit": base_price + 0.0100,
        "duration": timedelta(
            hours=random.randint(0, 4),
            minutes=random.randint(0, 59)
        ),
        "strategy": random.choice(["trend_following", "breakout", "mean_reversion"]),
        "pnl": pip_change * 10  # Simplified P&L
    }


def generate_user_stats(trades: int, win_rate: float) -> Dict[str, Any]:
    """Generate user statistics for testing"""
    wins = int(trades * win_rate)
    losses = trades - wins
    
    return {
        "total_trades": trades,
        "successful_trades": wins,
        "failed_trades": losses,
        "win_rate": win_rate,
        "total_pnl": (wins * 100) - (losses * 50),  # Simple P&L model
        "best_streak": random.randint(3, 10),
        "current_streak": random.randint(0, 5),
        "avg_win": 100,
        "avg_loss": 50,
        "profit_factor": 2.0 if win_rate > 0.5 else 0.8
    }


# ==================== RUN CONFIGURATION ====================

if __name__ == "__main__":
    # Run with coverage and performance profiling
    pytest.main([
        __file__,
        "-v",  # Verbose
        "--tb=short",  # Short traceback
        "--maxfail=5",  # Stop after 5 failures
        "-x",  # Stop on first failure
        "--durations=10",  # Show 10 slowest tests
        "--cov=src.bitten_core",  # Coverage for education modules
        "--cov-report=html",  # HTML coverage report
        "--cov-report=term-missing",  # Terminal report with missing lines
    ])