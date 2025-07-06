"""
BITTEN Perk Tree Visual Interface
Interactive perk tree display with Call of Duty-style aesthetics
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import math


@dataclass
class PerkNode:
    """Visual representation of a perk in the tree"""
    perk_id: str
    x: float
    y: float
    connections: List[str]  # Connected perk IDs


class PerkTreeVisual:
    """Generates visual perk tree layouts"""
    
    # Tree layout constants
    BRANCH_WIDTH = 300
    TIER_HEIGHT = 200
    NODE_SIZE = 80
    CONNECTION_WIDTH = 3
    
    # Color schemes (Call of Duty style)
    COLORS = {
        "TRADING": {
            "primary": "#FF6B6B",  # Red
            "secondary": "#FF4444",
            "glow": "#FF0000",
            "locked": "#661111"
        },
        "ANALYSIS": {
            "primary": "#4ECDC4",  # Cyan
            "secondary": "#2EA69F",
            "glow": "#00FFFF",
            "locked": "#1A4D4A"
        },
        "SOCIAL": {
            "primary": "#FFE66D",  # Yellow
            "secondary": "#FFD93D",
            "glow": "#FFFF00",
            "locked": "#665C1A"
        },
        "ECONOMY": {
            "primary": "#95E1D3",  # Green
            "secondary": "#6BCB77",
            "glow": "#00FF00",
            "locked": "#2D5A2D"
        }
    }
    
    # Tier badges
    TIER_BADGES = {
        1: "⚡",  # Basic
        2: "🔥",  # Advanced
        3: "💎",  # Elite
        4: "👑"   # Legendary
    }
    
    def __init__(self, perk_system):
        self.perk_system = perk_system
    
    def generate_tree_layout(self, user_id: int) -> Dict:
        """Generate complete tree layout with positions"""
        tree_data = self.perk_system.get_perk_tree_display(user_id)
        layout = {
            "branches": {},
            "connections": [],
            "player_info": tree_data["player"]
        }
        
        branch_index = 0
        for branch_name, branch_data in tree_data["tree"].items():
            branch_x = branch_index * self.BRANCH_WIDTH + 150
            
            layout["branches"][branch_name] = {
                "color": self.COLORS[branch_name],
                "tiers": {},
                "x": branch_x
            }
            
            tier_index = 0
            for tier_name, tier_data in branch_data["tiers"].items():
                tier_y = tier_index * self.TIER_HEIGHT + 100
                
                layout["branches"][branch_name]["tiers"][tier_name] = {
                    "y": tier_y,
                    "locked": tier_data["locked"],
                    "min_level": tier_data["min_level"],
                    "perks": []
                }
                
                # Position perks within tier
                perk_count = len(tier_data["perks"])
                for i, perk in enumerate(tier_data["perks"]):
                    # Stagger perks for visual appeal
                    offset_x = (i - (perk_count - 1) / 2) * 100
                    offset_y = (i % 2) * 30  # Slight vertical stagger
                    
                    perk_node = {
                        "x": branch_x + offset_x,
                        "y": tier_y + offset_y,
                        "data": perk
                    }
                    
                    layout["branches"][branch_name]["tiers"][tier_name]["perks"].append(perk_node)
                    
                    # Generate connections
                    for prereq in perk["prerequisites"]:
                        layout["connections"].append({
                            "from": prereq,
                            "to": perk["perk_id"],
                            "type": "prerequisite"
                        })
                    
                    for synergy in perk["synergies"]:
                        layout["connections"].append({
                            "from": perk["perk_id"],
                            "to": synergy,
                            "type": "synergy"
                        })
                
                tier_index += 1
            branch_index += 1
        
        return layout
    
    def generate_perk_card(self, perk_id: str, user_id: int) -> Dict:
        """Generate detailed perk card display"""
        player_data = self.perk_system.get_player_data(user_id)
        perk = self.perk_system.perk_catalog.get(perk_id)
        
        if not perk:
            return None
        
        # Check unlock status
        is_unlocked = perk_id in player_data.unlocked_perks
        current_rank = player_data.unlocked_perks.get(perk_id, 0)
        can_unlock, reason = self.perk_system.can_unlock_perk(
            user_id, perk_id, player_data.level
        )
        
        # Calculate effect values
        effects_display = []
        for effect in perk.effects:
            value = effect.value
            if perk.max_rank > 1 and current_rank > 0:
                value *= current_rank
            
            if effect.effect_type.endswith("multiplier") or effect.effect_type.endswith("bonus"):
                display_value = f"+{int(value * 100)}%"
            elif effect.effect_type.endswith("reduction"):
                display_value = f"-{int(value * 100)}%"
            else:
                display_value = str(int(value))
            
            effects_display.append({
                "type": effect.effect_type,
                "value": display_value,
                "description": effect.description
            })
        
        # Build card data
        card = {
            "perk_id": perk_id,
            "name": perk.name,
            "icon": perk.icon,
            "description": perk.description,
            "branch": perk.branch.value,
            "tier": perk.tier.value,
            "tier_badge": self.TIER_BADGES[perk.tier.value],
            "type": perk.perk_type.value,
            "effects": effects_display,
            "cost": perk.tier.point_cost,
            "is_unlocked": is_unlocked,
            "current_rank": current_rank,
            "max_rank": perk.max_rank,
            "can_unlock": can_unlock,
            "unlock_reason": reason,
            "requirements": {
                "level": perk.tier.min_level,
                "xp": perk.xp_requirement,
                "achievement": perk.achievement_requirement,
                "prerequisites": [
                    {
                        "id": prereq,
                        "name": self.perk_system.perk_catalog[prereq].name,
                        "unlocked": prereq in player_data.unlocked_perks
                    } for prereq in perk.prerequisites
                ]
            },
            "synergies": [
                {
                    "id": syn,
                    "name": self.perk_system.perk_catalog[syn].name,
                    "active": syn in self._get_active_perks(player_data)
                } for syn in perk.synergies
            ],
            "conflicts": [
                {
                    "id": conf,
                    "name": self.perk_system.perk_catalog[conf].name
                } for conf in perk.conflicts
            ]
        }
        
        # Add seasonal info
        if perk.perk_type == perk.PerkType.SEASONAL:
            card["seasonal_info"] = {
                "end_date": perk.seasonal_end.isoformat() if perk.seasonal_end else None,
                "days_remaining": (perk.seasonal_end - datetime.now()).days if perk.seasonal_end else 0
            }
        
        # Add elite info
        if perk.elite_only:
            card["elite_requirement"] = True
        
        return card
    
    def generate_loadout_display(self, user_id: int, loadout_id: str) -> Dict:
        """Generate loadout visualization"""
        player_data = self.perk_system.get_player_data(user_id)
        
        # Find loadout
        loadout = None
        for l in player_data.loadouts:
            if l.loadout_id == loadout_id:
                loadout = l
                break
        
        if not loadout:
            return None
        
        # Build display
        display = {
            "loadout_id": loadout_id,
            "name": loadout.name,
            "is_active": player_data.active_loadout == loadout_id,
            "branches": {}
        }
        
        # Get effects summary
        total_effects = {}
        synergy_count = 0
        
        for branch, perk_id in loadout.active_perks.items():
            if not perk_id:
                display["branches"][branch.value] = None
                continue
            
            perk = self.perk_system.perk_catalog[perk_id]
            rank = player_data.unlocked_perks.get(perk_id, 1)
            
            display["branches"][branch.value] = {
                "perk_id": perk_id,
                "name": perk.name,
                "icon": perk.icon,
                "rank": rank,
                "color": self.COLORS[branch.value]
            }
            
            # Aggregate effects
            for effect in perk.effects:
                effect_type = effect.effect_type
                value = effect.value * rank if perk.max_rank > 1 else effect.value
                
                if effect_type not in total_effects:
                    total_effects[effect_type] = 0
                total_effects[effect_type] += value
            
            # Count synergies
            for syn in perk.synergies:
                if syn in [p for p in loadout.active_perks.values() if p]:
                    synergy_count += 0.5  # Each pair counts once
        
        # Format effects
        display["total_effects"] = []
        for effect_type, value in total_effects.items():
            if effect_type.endswith("multiplier") or effect_type.endswith("bonus"):
                display_text = f"+{int(value * 100)}% {effect_type.replace('_', ' ')}"
            elif effect_type.endswith("reduction"):
                display_text = f"-{int(value * 100)}% {effect_type.replace('_', ' ')}"
            else:
                display_text = f"{int(value)} {effect_type.replace('_', ' ')}"
            
            display["total_effects"].append(display_text)
        
        # Add synergy bonus
        if synergy_count > 0:
            synergy_bonus = min(synergy_count * 0.1, 0.5)
            display["synergy_bonus"] = f"+{int(synergy_bonus * 100)}% synergy bonus"
        
        return display
    
    def generate_progression_path(self, user_id: int, target_perk_id: str) -> List[Dict]:
        """Generate optimal path to unlock a target perk"""
        player_data = self.perk_system.get_player_data(user_id)
        target_perk = self.perk_system.perk_catalog.get(target_perk_id)
        
        if not target_perk:
            return []
        
        path = []
        
        # Check if already unlocked
        if target_perk_id in player_data.unlocked_perks:
            return [{
                "perk_id": target_perk_id,
                "name": target_perk.name,
                "status": "already_unlocked"
            }]
        
        # Build dependency tree
        def add_dependencies(perk_id, visited=None):
            if visited is None:
                visited = set()
            
            if perk_id in visited:
                return
            
            visited.add(perk_id)
            perk = self.perk_system.perk_catalog.get(perk_id)
            
            if not perk:
                return
            
            # Add prerequisites first
            for prereq in perk.prerequisites:
                add_dependencies(prereq, visited)
            
            # Add to path if not unlocked
            if perk_id not in player_data.unlocked_perks:
                points_needed = perk.tier.point_cost
                level_needed = perk.tier.min_level
                
                path.append({
                    "perk_id": perk_id,
                    "name": perk.name,
                    "icon": perk.icon,
                    "branch": perk.branch.value,
                    "tier": perk.tier.value,
                    "points_needed": points_needed,
                    "level_needed": level_needed,
                    "current_level": player_data.level,
                    "available_points": player_data.available_points,
                    "can_unlock_now": (
                        player_data.level >= level_needed and
                        player_data.available_points >= points_needed and
                        all(p in player_data.unlocked_perks for p in perk.prerequisites)
                    )
                })
        
        add_dependencies(target_perk_id)
        
        # Calculate totals
        total_points = sum(p["points_needed"] for p in path)
        max_level = max(p["level_needed"] for p in path) if path else 0
        
        return {
            "path": path,
            "total_points_needed": total_points,
            "points_available": player_data.available_points,
            "points_deficit": max(0, total_points - player_data.available_points),
            "max_level_needed": max_level,
            "current_level": player_data.level,
            "levels_needed": max(0, max_level - player_data.level)
        }
    
    def generate_comparison_view(self, user_id: int, perk_ids: List[str]) -> Dict:
        """Generate comparison view for multiple perks"""
        player_data = self.perk_system.get_player_data(user_id)
        comparison = {
            "perks": [],
            "can_equip_together": True,
            "conflicts": []
        }
        
        # Check each perk
        for perk_id in perk_ids:
            perk = self.perk_system.perk_catalog.get(perk_id)
            if not perk:
                continue
            
            perk_info = {
                "perk_id": perk_id,
                "name": perk.name,
                "icon": perk.icon,
                "branch": perk.branch.value,
                "tier": perk.tier.value,
                "cost": perk.tier.point_cost,
                "unlocked": perk_id in player_data.unlocked_perks,
                "effects": []
            }
            
            # Add effects
            for effect in perk.effects:
                perk_info["effects"].append({
                    "type": effect.effect_type,
                    "value": effect.value,
                    "description": effect.description
                })
            
            comparison["perks"].append(perk_info)
            
            # Check conflicts
            for other_id in perk_ids:
                if other_id != perk_id and other_id in perk.conflicts:
                    comparison["can_equip_together"] = False
                    comparison["conflicts"].append({
                        "perk1": perk.name,
                        "perk2": self.perk_system.perk_catalog[other_id].name
                    })
        
        # Check branch conflicts (only one per branch in active loadout)
        branches = [p["branch"] for p in comparison["perks"]]
        if len(branches) != len(set(branches)):
            comparison["can_equip_together"] = False
            comparison["conflicts"].append({
                "reason": "Multiple perks from same branch"
            })
        
        return comparison
    
    def _get_active_perks(self, player_data) -> List[str]:
        """Get list of currently active perk IDs"""
        if not player_data.active_loadout:
            return []
        
        for loadout in player_data.loadouts:
            if loadout.loadout_id == player_data.active_loadout:
                return [p for p in loadout.active_perks.values() if p]
        
        return []
    
    def generate_tree_stats(self, user_id: int) -> Dict:
        """Generate statistics about player's perk tree progress"""
        player_data = self.perk_system.get_player_data(user_id)
        
        # Count perks by tier and branch
        stats = {
            "total_perks": len(self.perk_system.perk_catalog),
            "unlocked_perks": len(player_data.unlocked_perks),
            "completion_percentage": (len(player_data.unlocked_perks) / 
                                    len(self.perk_system.perk_catalog) * 100),
            "by_branch": {},
            "by_tier": {},
            "points_spent": player_data.spent_points,
            "points_available": player_data.available_points,
            "total_points_earned": player_data.spent_points + player_data.available_points,
            "max_possible_points": self._calculate_max_points(player_data.level),
            "favorite_branch": None,
            "rarest_perk": None
        }
        
        # Initialize counters
        for branch in ["TRADING", "ANALYSIS", "SOCIAL", "ECONOMY"]:
            stats["by_branch"][branch] = {
                "total": 0,
                "unlocked": 0
            }
        
        for tier in range(1, 5):
            stats["by_tier"][tier] = {
                "total": 0,
                "unlocked": 0
            }
        
        # Count perks
        for perk_id, perk in self.perk_system.perk_catalog.items():
            branch = perk.branch.value
            tier = perk.tier.value
            
            stats["by_branch"][branch]["total"] += 1
            stats["by_tier"][tier]["total"] += 1
            
            if perk_id in player_data.unlocked_perks:
                stats["by_branch"][branch]["unlocked"] += 1
                stats["by_tier"][tier]["unlocked"] += 1
        
        # Find favorite branch
        max_unlocked = 0
        for branch, data in stats["by_branch"].items():
            if data["unlocked"] > max_unlocked:
                max_unlocked = data["unlocked"]
                stats["favorite_branch"] = branch
        
        # Find rarest unlocked perk (highest tier/cost)
        if player_data.unlocked_perks:
            rarest = None
            highest_tier = 0
            for perk_id in player_data.unlocked_perks:
                perk = self.perk_system.perk_catalog.get(perk_id)
                if perk and perk.tier.value > highest_tier:
                    highest_tier = perk.tier.value
                    rarest = {
                        "perk_id": perk_id,
                        "name": perk.name,
                        "tier": perk.tier.value
                    }
            stats["rarest_perk"] = rarest
        
        return stats
    
    def _calculate_max_points(self, level: int) -> int:
        """Calculate maximum possible points at given level"""
        points = level * self.perk_system.POINTS_PER_LEVEL
        
        # Add bonus points
        for bonus_level in self.perk_system.BONUS_POINT_LEVELS:
            if level >= bonus_level:
                points += 1
        
        return points