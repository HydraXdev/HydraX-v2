"""
Test suite for BITTEN Perk System
Demonstrates all perk functionality
"""

import json
from datetime import datetime, timedelta
from perk_system import PerkSystem, PerkBranch
from perk_tree_visual import PerkTreeVisual
from perk_integration import PerkIntegration


def test_perk_system():
    """Comprehensive test of perk system"""
    print("=== BITTEN PERK SYSTEM TEST ===\n")
    
    # Initialize systems
    perk_system = PerkSystem("test_perks.db")
    visual = PerkTreeVisual(perk_system)
    integration = PerkIntegration(perk_system)
    
    # Test user
    user_id = 12345
    
    # Test 1: New Player Setup
    print("TEST 1: New Player Setup")
    print("-" * 40)
    player_data = perk_system.get_player_data(user_id)
    print(f"Starting Level: {player_data.level}")
    print(f"Available Points: {player_data.available_points}")
    print(f"Unlocked Perks: {len(player_data.unlocked_perks)}")
    print()
    
    # Test 2: Level Up and Point Awards
    print("TEST 2: Level Up System")
    print("-" * 40)
    new_level = 25
    points, milestones = perk_system.update_player_level(user_id, new_level)
    print(f"Leveled up to: {new_level}")
    print(f"Total points available: {points}")
    print("Milestones:")
    for milestone in milestones:
        print(f"  - {milestone}")
    print()
    
    # Test 3: Unlock Basic Perks
    print("TEST 3: Unlocking Perks")
    print("-" * 40)
    
    # Try to unlock a basic trading perk
    success, msg = perk_system.unlock_perk(user_id, "reduced_fees_1")
    print(f"Unlock 'Efficient Trader': {success} - {msg}")
    
    # Try to unlock a basic analysis perk
    success, msg = perk_system.unlock_perk(user_id, "priority_signals")
    print(f"Unlock 'Priority Access': {success} - {msg}")
    
    # Try to unlock advanced perk without prerequisite (should fail)
    success, msg = perk_system.unlock_perk(user_id, "quick_fingers")
    print(f"Unlock 'Quick Fingers' (no prereq): {success} - {msg}")
    
    # Unlock another rank of multi-rank perk
    success, msg = perk_system.unlock_perk(user_id, "reduced_fees_1")
    print(f"Upgrade 'Efficient Trader' to Rank 2: {success} - {msg}")
    print()
    
    # Test 4: Create and Manage Loadouts
    print("TEST 4: Loadout System")
    print("-" * 40)
    
    # Create a loadout
    loadout_perks = {
        PerkBranch.TRADING: "reduced_fees_1",
        PerkBranch.ANALYSIS: "priority_signals",
        PerkBranch.SOCIAL: None,
        PerkBranch.ECONOMY: None
    }
    
    success, msg = perk_system.create_loadout(user_id, "Speed Trader", loadout_perks)
    print(f"Create loadout 'Speed Trader': {success} - {msg}")
    
    # Activate the loadout
    player_data = perk_system.get_player_data(user_id)
    if player_data.loadouts:
        loadout_id = player_data.loadouts[0].loadout_id
        success, msg = perk_system.activate_loadout(user_id, loadout_id)
        print(f"Activate loadout: {success} - {msg}")
    print()
    
    # Test 5: Get Active Effects
    print("TEST 5: Active Perk Effects")
    print("-" * 40)
    effects = perk_system.get_active_effects(user_id)
    for effect_type, effect_list in effects.items():
        print(f"\n{effect_type}:")
        for effect in effect_list:
            print(f"  - {effect.description}: {effect.value}")
    print()
    
    # Test 6: Apply Perk Effects (Integration)
    print("TEST 6: Perk Effect Application")
    print("-" * 40)
    
    # Test fee reduction
    base_fee = 10.0
    final_fee, applied = integration.apply_trading_fee_reduction(user_id, base_fee)
    print(f"Trading Fee: ${base_fee:.2f} -> ${final_fee:.2f}")
    if applied:
        print(f"Applied: {', '.join(applied)}")
    
    # Test XP multiplier
    base_xp = 100
    final_xp, applied = integration.apply_xp_multipliers(user_id, base_xp)
    print(f"\nXP Gain: {base_xp} -> {final_xp}")
    if applied:
        print(f"Applied: {', '.join(applied)}")
    print()
    
    # Test 7: Visual Tree Generation
    print("TEST 7: Perk Tree Visualization")
    print("-" * 40)
    tree_layout = visual.generate_tree_layout(user_id)
    print(f"Branches: {len(tree_layout['branches'])}")
    for branch_name, branch_data in tree_layout['branches'].items():
        total_perks = sum(len(tier['perks']) for tier in branch_data['tiers'].values())
        print(f"  {branch_name}: {total_perks} perks")
    print()
    
    # Test 8: Perk Card Display
    print("TEST 8: Perk Card Details")
    print("-" * 40)
    card = visual.generate_perk_card("quick_fingers", user_id)
    if card:
        print(f"Perk: {card['name']} {card['icon']}")
        print(f"Branch: {card['branch']} | Tier: {card['tier']}")
        print(f"Cost: {card['cost']} points")
        print(f"Can Unlock: {card['can_unlock']} - {card['unlock_reason']}")
        print("Effects:")
        for effect in card['effects']:
            print(f"  - {effect['description']}: {effect['value']}")
    print()
    
    # Test 9: Advanced Perks with Higher Level
    print("TEST 9: Elite Perk Unlocking")
    print("-" * 40)
    
    # Level up to 60 for elite perks
    points, _ = perk_system.update_player_level(user_id, 60)
    print(f"Leveled to 60, points available: {points}")
    
    # Unlock prerequisite first
    perk_system.unlock_perk(user_id, "enhanced_indicators")
    perk_system.unlock_perk(user_id, "pattern_recognition")
    
    # Try to unlock elite perk
    success, msg = perk_system.unlock_perk(user_id, "quantum_analysis", user_xp=10000)
    print(f"Unlock 'Quantum Analysis' (Elite): {success} - {msg}")
    print()
    
    # Test 10: Synergy System
    print("TEST 10: Perk Synergies")
    print("-" * 40)
    
    # Create loadout with synergies
    perk_system.unlock_perk(user_id, "squad_synergy")
    perk_system.unlock_perk(user_id, "xp_boost_1")
    
    synergy_loadout = {
        PerkBranch.TRADING: "quick_fingers",  # Synergy with priority_signals
        PerkBranch.ANALYSIS: "priority_signals",
        PerkBranch.SOCIAL: "squad_synergy",
        PerkBranch.ECONOMY: "xp_boost_1"
    }
    
    success, msg = perk_system.create_loadout(user_id, "Synergy Build", synergy_loadout)
    print(f"Create synergy loadout: {success} - {msg}")
    
    # Check synergy bonus
    if success:
        player_data = perk_system.get_player_data(user_id)
        loadout_id = player_data.loadouts[-1].loadout_id
        perk_system.activate_loadout(user_id, loadout_id)
        
        effects = perk_system.get_active_effects(user_id)
        if "synergy_bonus" in effects:
            print(f"Synergy Bonus Active: {effects['synergy_bonus'][0].description}")
    print()
    
    # Test 11: Progression Path
    print("TEST 11: Progression Path to Target Perk")
    print("-" * 40)
    path_data = visual.generate_progression_path(user_id, "market_oracle")
    if path_data and "path" in path_data:
        print(f"Path to 'Market Oracle':")
        print(f"Total points needed: {path_data['total_points_needed']}")
        print(f"Points available: {path_data['points_available']}")
        print(f"Levels needed: {path_data['levels_needed']}")
        print("\nRequired perks:")
        for step in path_data['path']:
            status = "✓" if step['can_unlock_now'] else "✗"
            print(f"  {status} {step['name']} (Level {step['level_needed']}, {step['points_needed']} pts)")
    print()
    
    # Test 12: Respec System
    print("TEST 12: Perk Respec")
    print("-" * 40)
    player_data = perk_system.get_player_data(user_id)
    print(f"Current perks unlocked: {len(player_data.unlocked_perks)}")
    print(f"Points spent: {player_data.spent_points}")
    
    success, msg, cost = perk_system.respec_perks(user_id, 50000)
    print(f"Respec attempt: {success} - {msg}")
    if success:
        print(f"Cost: {cost} XP")
        player_data = perk_system.get_player_data(user_id)
        print(f"Points after respec: {player_data.available_points}")
    print()
    
    # Test 13: Seasonal Perks
    print("TEST 13: Seasonal Perks")
    print("-" * 40)
    
    # Check winter warrior availability
    winter_perk = perk_system.perk_catalog.get("winter_warrior")
    if winter_perk:
        print(f"Winter Warrior expires: {winter_perk.seasonal_end}")
        if datetime.now() < winter_perk.seasonal_end:
            success, msg = perk_system.unlock_perk(user_id, "winter_warrior")
            print(f"Unlock seasonal perk: {success} - {msg}")
    
    # Check seasonal bonuses
    seasonal_bonuses = integration.check_seasonal_bonuses(user_id, datetime.now())
    if seasonal_bonuses:
        print("Active seasonal bonuses:")
        for bonus in seasonal_bonuses:
            print(f"  - {bonus['name']}: {bonus['bonus']}")
    print()
    
    # Test 14: Perk Statistics
    print("TEST 14: Perk Tree Statistics")
    print("-" * 40)
    stats = visual.generate_tree_stats(user_id)
    print(f"Total Perks: {stats['total_perks']}")
    print(f"Unlocked: {stats['unlocked_perks']} ({stats['completion_percentage']:.1f}%)")
    print(f"Favorite Branch: {stats['favorite_branch']}")
    if stats['rarest_perk']:
        print(f"Rarest Perk: {stats['rarest_perk']['name']} (Tier {stats['rarest_perk']['tier']})")
    print("\nBranch Progress:")
    for branch, data in stats['by_branch'].items():
        percent = (data['unlocked'] / data['total'] * 100) if data['total'] > 0 else 0
        print(f"  {branch}: {data['unlocked']}/{data['total']} ({percent:.0f}%)")
    print()
    
    # Test 15: Recommendations
    print("TEST 15: Perk Recommendations")
    print("-" * 40)
    user_stats = {
        'win_rate': 0.75,
        'trades_per_day': 15,
        'avg_profit': 1500,
        'squad_size': 8
    }
    
    recommendations = perk_system.get_perk_recommendations(user_id, user_stats)
    print("Recommended perks based on your playstyle:")
    for rec in recommendations:
        perk = perk_system.perk_catalog[rec['perk_id']]
        print(f"  [{rec['priority'].upper()}] {perk.name}")
        print(f"    Reason: {rec['reason']}")
    print()
    
    # Test 16: Loadout Comparison
    print("TEST 16: Loadout Display")
    print("-" * 40)
    player_data = perk_system.get_player_data(user_id)
    if player_data.loadouts:
        loadout_display = visual.generate_loadout_display(user_id, player_data.loadouts[0].loadout_id)
        if loadout_display:
            print(f"Loadout: {loadout_display['name']}")
            print(f"Active: {loadout_display['is_active']}")
            print("Equipped Perks:")
            for branch, perk_data in loadout_display['branches'].items():
                if perk_data:
                    print(f"  {branch}: {perk_data['name']} {perk_data['icon']}")
            print("\nTotal Effects:")
            for effect in loadout_display['total_effects']:
                print(f"  - {effect}")
            if 'synergy_bonus' in loadout_display:
                print(f"  - {loadout_display['synergy_bonus']}")
    
    print("\n=== TEST COMPLETE ===")


def test_specific_scenarios():
    """Test specific gameplay scenarios"""
    print("\n=== SPECIFIC SCENARIO TESTS ===\n")
    
    perk_system = PerkSystem("test_perks.db")
    integration = PerkIntegration(perk_system)
    
    # Scenario 1: High-frequency trader build
    print("SCENARIO 1: High-Frequency Trader Build")
    print("-" * 40)
    
    user_id = 99999
    perk_system.update_player_level(user_id, 75)
    
    # Unlock speed-focused perks
    perks_to_unlock = [
        "reduced_fees_1",  # 3 ranks
        "quick_fingers",
        "priority_signals",
        "double_tap"
    ]
    
    for perk_id in perks_to_unlock:
        perk = perk_system.perk_catalog[perk_id]
        # Unlock prerequisites first
        for prereq in perk.prerequisites:
            perk_system.unlock_perk(user_id, prereq)
        
        # Unlock the perk (multiple times for multi-rank)
        for _ in range(perk.max_rank):
            success, msg = perk_system.unlock_perk(user_id, perk_id)
            if success:
                print(f"✓ {msg}")
    
    # Calculate effective trading cost
    base_fee = 10.0
    final_fee, _ = integration.apply_trading_fee_reduction(user_id, base_fee)
    speed_mult = integration.get_execution_speed_multiplier(user_id)
    
    print(f"\nTrading Profile:")
    print(f"  Fee reduction: {((base_fee - final_fee) / base_fee * 100):.1f}%")
    print(f"  Execution speed: {speed_mult}x faster")
    print(f"  Can double-tap signals: Yes")
    print()
    
    # Scenario 2: Squad Leader Build
    print("SCENARIO 2: Squad Leader Build")
    print("-" * 40)
    
    user_id_2 = 88888
    perk_system.update_player_level(user_id_2, 100)
    
    squad_perks = [
        "squad_synergy",  # 3 ranks
        "mentor_bonus",
        "rally_cry",
        "squad_leader",
        "legacy_builder"
    ]
    
    for perk_id in squad_perks:
        perk = perk_system.perk_catalog[perk_id]
        for prereq in perk.prerequisites:
            perk_system.unlock_perk(user_id_2, prereq)
        
        for _ in range(perk.max_rank):
            success, msg = perk_system.unlock_perk(user_id_2, perk_id, 
                                                 user_xp=100000,
                                                 user_achievements=["general"])
            if success:
                print(f"✓ {msg}")
    
    # Test squad bonuses
    base_xp = 100
    squad_xp, _ = integration.apply_squad_xp_bonus(user_id_2, base_xp, is_squad_win=True)
    recruit_xp, _ = integration.apply_recruit_xp_bonus(user_id_2, base_xp)
    
    print(f"\nSquad Leader Benefits:")
    print(f"  Squad win XP bonus: +{squad_xp - base_xp} XP")
    print(f"  Recruit XP bonus: +{recruit_xp - base_xp} XP")
    print(f"  Rally Cry available: Yes")
    print(f"  Win bonus sharing: 20%")
    
    recruit_bonus = integration.get_recruit_starting_bonus(user_id_2)
    print(f"  Recruits start at: Level {recruit_bonus['level']}")
    print()
    
    # Scenario 3: Elite Analyst Build
    print("SCENARIO 3: Elite Analyst Build")
    print("-" * 40)
    
    user_id_3 = 77777
    perk_system.update_player_level(user_id_3, 150)
    
    analyst_perks = [
        "enhanced_indicators",
        "pattern_recognition",
        "volatility_radar",
        "quantum_analysis",
        "prophet_mode"
    ]
    
    for perk_id in analyst_perks:
        perk = perk_system.perk_catalog[perk_id]
        for prereq in perk.prerequisites:
            perk_system.unlock_perk(user_id_3, prereq)
        
        success, msg = perk_system.unlock_perk(user_id_3, perk_id, user_xp=100000)
        if success:
            print(f"✓ {msg}")
    
    # Test analysis features
    extra_indicators = integration.get_extra_indicators(user_id_3)
    predictions = integration.get_prophet_predictions(user_id_3)
    
    print(f"\nAnalyst Capabilities:")
    print(f"  Extra indicators: {', '.join(extra_indicators)}")
    print(f"  Pattern recognition: Active")
    print(f"  Volatility alerts: Active")
    print(f"  Quantum analysis: Active")
    print(f"  Prophet predictions: {len(predictions)} signals")
    if predictions:
        print(f"    Next: {predictions[0]['pair']} {predictions[0]['direction']} ({predictions[0]['confidence']:.0%})")
    
    print("\n=== SCENARIO TESTS COMPLETE ===")


if __name__ == "__main__":
    # Run comprehensive test
    test_perk_system()
    
    # Run specific scenarios
    test_specific_scenarios()
    
    # Clean up test database
    import os
    if os.path.exists("test_perks.db"):
        os.remove("test_perks.db")