"""
synergy_enhanced.py — Enhanced synergy system with more complex interactions
"""
from typing import Dict, List, Tuple, Set
from cell_types import CellType, get_cell_type_def
from collections import Counter


class SynergySystem:
    """Enhanced synergy calculation with complex interactions"""
    
    @staticmethod
    def calculate_synergies(cells: List[CellType]) -> Dict[str, float]:
        """
        Calculate all synergies from a cell configuration.
        Returns dict of stat multipliers.
        """
        if not cells:
            return {}
        
        # Count cell types
        cell_counts = Counter(cells)
        cell_counts.pop(CellType.EMPTY, None)  # Ignore empty slots
        
        # Get cell tags
        all_tags = set()
        for cell in cells:
            if cell != CellType.EMPTY:
                tags = get_cell_type_def(cell).get("tags", set())
                all_tags.update(tags)
        
        multipliers = {
            "max_hp": 1.0,
            "speed": 1.0,
            "contact_dmg": 1.0,
            "defense": 1.0,
            "regen": 1.0,
            "reflect_dmg": 1.0,
            "lifesteal": 1.0,
            "xp_mult": 1.0,
            "dodge_chance": 0.0,  # Additive
        }
        
        # === POSITIONAL SYNERGIES ===
        
        # Core Reinforcement: All 6 slots filled
        if len([c for c in cells if c != CellType.EMPTY]) == 6:
            multipliers["max_hp"] *= 1.25
            multipliers["defense"] *= 1.25
            multipliers["speed"] *= 1.15
        
        # === TYPE-BASED SYNERGIES ===
        
        # Heart synergies
        heart_count = cell_counts.get(CellType.HEART, 0)
        if heart_count >= 2:
            multipliers["max_hp"] *= 1.0 + (heart_count * 0.12)
            multipliers["regen"] *= 1.0 + (heart_count * 0.08)
        
        # Move synergies
        move_count = cell_counts.get(CellType.MOVE, 0)
        if move_count >= 2:
            multipliers["speed"] *= 1.0 + (move_count * 0.15)
        
        # Damage synergies
        damage_count = cell_counts.get(CellType.DAMAGE, 0)
        if damage_count >= 2:
            multipliers["contact_dmg"] *= 1.0 + (damage_count * 0.18)
        
        # Shield synergies
        shield_count = cell_counts.get(CellType.SHIELD, 0)
        if shield_count >= 2:
            multipliers["defense"] *= 1.0 + (shield_count * 0.15)
        
        # === ADVANCED SYNERGIES ===
        
        # Vampiric Build: Leech + Damage
        if CellType.LEECH in cell_counts and CellType.DAMAGE in cell_counts:
            multipliers["lifesteal"] *= 1.5
            multipliers["contact_dmg"] *= 1.2
        
        # Toxic Burst: Toxic + Burst
        if CellType.TOXIC in cell_counts and CellType.BURST in cell_counts:
            multipliers["contact_dmg"] *= 1.3
        
        # Speed Demon: Move + Dash
        if CellType.MOVE in cell_counts and CellType.DASH in cell_counts:
            multipliers["speed"] *= 1.4
        
        # Tank Build: Heart + Shield + Regen
        if (CellType.HEART in cell_counts and 
            CellType.SHIELD in cell_counts and 
            CellType.REGEN in cell_counts):
            multipliers["max_hp"] *= 1.3
            multipliers["defense"] *= 1.3
            multipliers["regen"] *= 1.5
        
        # Glass Cannon: Damage + Crystal (no shields)
        if (CellType.DAMAGE in cell_counts and 
            CellType.CRYSTAL in cell_counts and 
            CellType.SHIELD not in cell_counts):
            multipliers["contact_dmg"] *= 1.5
            multipliers["xp_mult"] *= 1.3
        
        # Fortress: 3+ Shields
        if shield_count >= 3:
            multipliers["defense"] *= 1.4
            multipliers["reflect_dmg"] *= 1.3
        
        # Berserker: 3+ Damage cells
        if damage_count >= 3:
            multipliers["contact_dmg"] *= 1.5
        
        # Speedster: 3+ Move cells
        if move_count >= 3:
            multipliers["speed"] *= 1.4
        
        # Regenerator: 2+ Regen cells
        regen_count = cell_counts.get(CellType.REGEN, 0)
        if regen_count >= 2:
            multipliers["regen"] *= 1.0 + (regen_count * 0.4)
        
        # Reflective Armor: Spike + Shield
        if CellType.SPIKE in cell_counts and CellType.SHIELD in cell_counts:
            multipliers["reflect_dmg"] *= 2.0
            multipliers["defense"] *= 1.2
        
        # Void Walker: Void + Move
        if CellType.VOID in cell_counts and CellType.MOVE in cell_counts:
            multipliers["dodge_chance"] += 0.08
            multipliers["speed"] *= 1.2
        
        # Magnetic Collector: Magnet + Crystal
        if CellType.MAGNET in cell_counts and CellType.CRYSTAL in cell_counts:
            multipliers["xp_mult"] *= 1.4
        
        # === TAG-BASED SYNERGIES ===
        
        # Balanced Build: At least one of each category
        has_offensive = any(tag in all_tags for tag in ["offensive", "contact_damage"])
        has_defensive = any(tag in all_tags for tag in ["defensive", "shield"])
        has_mobility = "mobility" in all_tags
        has_utility = "utility" in all_tags
        
        if has_offensive and has_defensive and has_mobility:
            # Harmony bonus
            multipliers["max_hp"] *= 1.15
            multipliers["speed"] *= 1.15
            multipliers["contact_dmg"] *= 1.15
        
        return multipliers
    
    @staticmethod
    def get_active_synergies(cells: List[CellType]) -> List[Tuple[str, str, float]]:
        """
        Get list of active synergies for UI display.
        Returns list of (icon, name, bonus_value) tuples.
        """
        if not cells:
            return []
        
        cell_counts = Counter(cells)
        cell_counts.pop(CellType.EMPTY, None)
        
        synergies = []
        
        # Check each synergy condition
        if len([c for c in cells if c != CellType.EMPTY]) == 6:
            synergies.append(("🔷", "Core Reinforcement", 0.25))
        
        heart_count = cell_counts.get(CellType.HEART, 0)
        if heart_count >= 2:
            synergies.append(("♥", "Vital Force", heart_count * 0.12))
        
        move_count = cell_counts.get(CellType.MOVE, 0)
        if move_count >= 2:
            synergies.append(("➤", "Momentum", move_count * 0.15))
        
        damage_count = cell_counts.get(CellType.DAMAGE, 0)
        if damage_count >= 2:
            synergies.append(("✦", "Aggression", damage_count * 0.18))
        
        shield_count = cell_counts.get(CellType.SHIELD, 0)
        if shield_count >= 2:
            synergies.append(("⬡", "Fortress", shield_count * 0.15))
        
        if CellType.LEECH in cell_counts and CellType.DAMAGE in cell_counts:
            synergies.append(("🩸", "Vampiric", 0.5))
        
        if CellType.TOXIC in cell_counts and CellType.BURST in cell_counts:
            synergies.append(("☠", "Toxic Burst", 0.3))
        
        if CellType.MOVE in cell_counts and CellType.DASH in cell_counts:
            synergies.append(("⚡", "Speed Demon", 0.4))
        
        if (CellType.HEART in cell_counts and 
            CellType.SHIELD in cell_counts and 
            CellType.REGEN in cell_counts):
            synergies.append(("🛡", "Tank", 0.3))
        
        if (CellType.DAMAGE in cell_counts and 
            CellType.CRYSTAL in cell_counts and 
            CellType.SHIELD not in cell_counts):
            synergies.append(("💎", "Glass Cannon", 0.5))
        
        if shield_count >= 3:
            synergies.append(("🏰", "Impenetrable", 0.4))
        
        if damage_count >= 3:
            synergies.append(("⚔", "Berserker", 0.5))
        
        if move_count >= 3:
            synergies.append(("💨", "Speedster", 0.4))
        
        regen_count = cell_counts.get(CellType.REGEN, 0)
        if regen_count >= 2:
            synergies.append(("✚", "Regenerator", regen_count * 0.4))
        
        if CellType.SPIKE in cell_counts and CellType.SHIELD in cell_counts:
            synergies.append(("⚡", "Reflective", 1.0))
        
        if CellType.VOID in cell_counts and CellType.MOVE in cell_counts:
            synergies.append(("🌀", "Void Walker", 0.08))
        
        if CellType.MAGNET in cell_counts and CellType.CRYSTAL in cell_counts:
            synergies.append(("◉", "Collector", 0.4))
        
        return synergies
    
    @staticmethod
    def get_synergy_description(synergy_name: str) -> str:
        """Get a description of what a synergy does"""
        descriptions = {
            "Core Reinforcement": "All slots filled: +25% HP, Defense, +15% Speed",
            "Vital Force": "Multiple Hearts: Increased HP and Regen",
            "Momentum": "Multiple Move cells: Increased Speed",
            "Aggression": "Multiple Damage cells: Increased Contact Damage",
            "Fortress": "Multiple Shields: Increased Defense",
            "Vampiric": "Leech + Damage: Enhanced Lifesteal",
            "Toxic Burst": "Toxic + Burst: Increased Damage",
            "Speed Demon": "Move + Dash: Massive Speed Boost",
            "Tank": "Heart + Shield + Regen: Ultimate Defense",
            "Glass Cannon": "Damage + Crystal (no Shield): High Risk, High Reward",
            "Impenetrable": "3+ Shields: Fortress Defense",
            "Berserker": "3+ Damage: Overwhelming Offense",
            "Speedster": "3+ Move: Lightning Fast",
            "Regenerator": "Multiple Regen: Rapid Healing",
            "Reflective": "Spike + Shield: Reflect Damage",
            "Void Walker": "Void + Move: Dodge and Speed",
            "Collector": "Magnet + Crystal: XP Magnet",
        }
        return descriptions.get(synergy_name, "Unknown synergy")
