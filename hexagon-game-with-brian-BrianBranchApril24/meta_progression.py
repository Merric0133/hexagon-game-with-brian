"""
meta_progression.py — Persistent unlocks and upgrades between runs
"""
import json
import os
from typing import Dict, List, Set, Any
from cell_types import CellType


class MetaProgression:
    """Manages persistent progression between runs"""
    def __init__(self, save_path: str = "data/meta_progress.json"):
        self.save_path = save_path
        
        # Unlocks
        self.unlocked_cells = set()
        self.unlocked_skins = set()
        
        # Stats
        self.total_runs = 0
        self.total_kills = 0
        self.highest_wave = 0
        self.total_score = 0
        self.best_score = 0
        
        # Permanent upgrades (purchased with meta currency)
        self.permanent_upgrades = {
            "starting_hp": 0,        # +10 HP per level
            "starting_speed": 0,     # +20 speed per level
            "starting_damage": 0,    # +5 damage per level
            "starting_defense": 0,   # +5 defense per level
            "xp_gain": 0,            # +10% XP per level
            "cell_rewards": 0,       # +1 cell per wave per level
            "powerup_chance": 0,     # +5% powerup drop per level
            "regen_boost": 0,        # +0.3 regen per level
        }
        
        # Meta currency
        self.essence = 0  # Earned from runs
        
        # Achievements
        self.achievements = set()
        
        self.load()
    
    def load(self):
        """Load meta progression from file"""
        if not os.path.exists(self.save_path):
            # First time - unlock starter cells
            self.unlocked_cells = {
                CellType.HEART, CellType.MOVE, CellType.DAMAGE, CellType.SHIELD
            }
            self.save()
            return
        
        try:
            with open(self.save_path, 'r') as f:
                data = json.load(f)
            
            # Load unlocks
            self.unlocked_cells = {CellType[name] for name in data.get("unlocked_cells", [])}
            self.unlocked_skins = set(data.get("unlocked_skins", []))
            
            # Load stats
            self.total_runs = data.get("total_runs", 0)
            self.total_kills = data.get("total_kills", 0)
            self.highest_wave = data.get("highest_wave", 0)
            self.total_score = data.get("total_score", 0)
            self.best_score = data.get("best_score", 0)
            
            # Load upgrades
            saved_upgrades = data.get("permanent_upgrades", {})
            for key in self.permanent_upgrades:
                self.permanent_upgrades[key] = saved_upgrades.get(key, 0)
            
            # Load currency
            self.essence = data.get("essence", 0)
            
            # Load achievements
            self.achievements = set(data.get("achievements", []))
            
        except Exception as e:
            print(f"Error loading meta progression: {e}")
    
    def save(self):
        """Save meta progression to file"""
        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
        
        data = {
            "unlocked_cells": [cell.name for cell in self.unlocked_cells],
            "unlocked_skins": list(self.unlocked_skins),
            "total_runs": self.total_runs,
            "total_kills": self.total_kills,
            "highest_wave": self.highest_wave,
            "total_score": self.total_score,
            "best_score": self.best_score,
            "permanent_upgrades": self.permanent_upgrades,
            "essence": self.essence,
            "achievements": list(self.achievements),
        }
        
        try:
            with open(self.save_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving meta progression: {e}")
    
    def complete_run(self, wave_reached: int, score: int, kills: int):
        """Called when a run ends"""
        self.total_runs += 1
        self.total_kills += kills
        self.total_score += score
        
        # Update best records
        if wave_reached > self.highest_wave:
            self.highest_wave = wave_reached
        if score > self.best_score:
            self.best_score = score
        
        # Award essence based on performance
        essence_earned = self._calculate_essence_reward(wave_reached, score, kills)
        self.essence += essence_earned
        
        # Check for new unlocks
        self._check_wave_unlocks(wave_reached)
        self._check_achievements(wave_reached, score, kills)
        
        self.save()
        return essence_earned
    
    def _calculate_essence_reward(self, wave: int, score: int, kills: int) -> int:
        """Calculate essence earned from a run"""
        base_essence = wave * 10
        score_bonus = score // 1000
        kill_bonus = kills * 2
        return base_essence + score_bonus + kill_bonus
    
    def _check_wave_unlocks(self, wave: int):
        """Unlock cells based on wave reached"""
        unlock_map = {
            3: CellType.REGEN,
            5: CellType.SPIKE,
            7: CellType.MAGNET,
            10: CellType.BURST,
            12: CellType.DASH,
            15: CellType.LEECH,
            18: CellType.TOXIC,
            20: CellType.CRYSTAL,
            25: CellType.VOID,
        }
        
        for unlock_wave, cell_type in unlock_map.items():
            if wave >= unlock_wave:
                self.unlocked_cells.add(cell_type)
    
    def _check_achievements(self, wave: int, score: int, kills: int):
        """Check and unlock achievements"""
        achievements = [
            ("first_blood", kills >= 1, "First Blood"),
            ("wave_10", wave >= 10, "Decimate"),
            ("wave_25", wave >= 25, "Quarter Century"),
            ("wave_50", wave >= 50, "Victory!"),
            ("score_10k", score >= 10000, "High Scorer"),
            ("score_50k", score >= 50000, "Score Master"),
            ("kills_100", self.total_kills >= 100, "Centurion"),
            ("kills_1000", self.total_kills >= 1000, "Slayer"),
            ("runs_10", self.total_runs >= 10, "Persistent"),
            ("runs_50", self.total_runs >= 50, "Dedicated"),
        ]
        
        for achievement_id, condition, name in achievements:
            if condition and achievement_id not in self.achievements:
                self.achievements.add(achievement_id)
                print(f"🏆 Achievement Unlocked: {name}")
    
    def purchase_upgrade(self, upgrade_name: str) -> bool:
        """Purchase a permanent upgrade"""
        if upgrade_name not in self.permanent_upgrades:
            return False
        
        current_level = self.permanent_upgrades[upgrade_name]
        cost = self._get_upgrade_cost(upgrade_name, current_level)
        
        if self.essence >= cost:
            self.essence -= cost
            self.permanent_upgrades[upgrade_name] += 1
            self.save()
            return True
        return False
    
    def _get_upgrade_cost(self, upgrade_name: str, current_level: int) -> int:
        """Get the cost of the next level of an upgrade"""
        base_costs = {
            "starting_hp": 50,
            "starting_speed": 40,
            "starting_damage": 60,
            "starting_defense": 60,
            "xp_gain": 80,
            "cell_rewards": 100,
            "powerup_chance": 70,
            "regen_boost": 50,
        }
        base_cost = base_costs.get(upgrade_name, 50)
        return int(base_cost * (1.5 ** current_level))
    
    def get_upgrade_info(self, upgrade_name: str) -> Dict[str, Any]:
        """Get information about an upgrade"""
        if upgrade_name not in self.permanent_upgrades:
            return {}
        
        current_level = self.permanent_upgrades[upgrade_name]
        cost = self._get_upgrade_cost(upgrade_name, current_level)
        
        descriptions = {
            "starting_hp": f"+{10 * (current_level + 1)} Starting HP",
            "starting_speed": f"+{20 * (current_level + 1)} Starting Speed",
            "starting_damage": f"+{5 * (current_level + 1)} Starting Damage",
            "starting_defense": f"+{5 * (current_level + 1)} Starting Defense",
            "xp_gain": f"+{10 * (current_level + 1)}% XP Gain",
            "cell_rewards": f"+{current_level + 1} Cells Per Wave",
            "powerup_chance": f"+{5 * (current_level + 1)}% Powerup Drop",
            "regen_boost": f"+{0.3 * (current_level + 1):.1f} HP/s Regen",
        }
        
        return {
            "name": upgrade_name.replace("_", " ").title(),
            "level": current_level,
            "cost": cost,
            "description": descriptions.get(upgrade_name, "Unknown"),
            "can_afford": self.essence >= cost,
        }
    
    def get_starting_bonuses(self) -> Dict[str, float]:
        """Get all starting bonuses from permanent upgrades"""
        return {
            "max_hp": self.permanent_upgrades["starting_hp"] * 10,
            "speed": self.permanent_upgrades["starting_speed"] * 20,
            "contact_dmg": self.permanent_upgrades["starting_damage"] * 5,
            "defense": self.permanent_upgrades["starting_defense"] * 5,
            "xp_mult": 1.0 + self.permanent_upgrades["xp_gain"] * 0.1,
            "cell_bonus": self.permanent_upgrades["cell_rewards"],
            "powerup_mult": 1.0 + self.permanent_upgrades["powerup_chance"] * 0.05,
            "regen": self.permanent_upgrades["regen_boost"] * 0.3,
        }
    
    def is_cell_unlocked(self, cell_type: CellType) -> bool:
        """Check if a cell type is unlocked"""
        return cell_type in self.unlocked_cells or cell_type == CellType.EMPTY


# Global instance
meta = MetaProgression()
