"""
cell_types.py — Expanded cell type system with abilities and mutations
"""
from enum import Enum
from typing import Dict, Set, Optional, Any

class CellType(Enum):
    """All available cell types in the game"""
    EMPTY    = 0
    HEART    = 1
    MOVE     = 2
    DAMAGE   = 3
    SHIELD   = 4
    REGEN    = 5   # Healing over time
    SPIKE    = 6   # Reflects damage
    MAGNET   = 7   # Pulls XP/powerups
    BURST    = 8   # AOE damage ability
    DASH     = 9   # Quick dodge ability
    LEECH    = 10  # Lifesteal
    TOXIC    = 11  # Damage over time
    CRYSTAL  = 12  # Bonus XP
    VOID     = 13  # Dodge chance

# Cell type definitions with stats, abilities, and visual properties
CELL_TYPE_DEFS = {
    CellType.EMPTY: {
        "name": "Empty",
        "icon": "",
        "color": (40, 45, 65),
        "stats": {},
        "tags": set(),
        "can_break": False,
        "unlock_wave": 0,
        "description": "Empty slot",
        "rarity": "common",
    },
    CellType.HEART: {
        "name": "Heart",
        "icon": "♥",
        "color": (240, 80, 100),
        "stats": {"max_hp": 15},
        "tags": {"heart", "vital"},
        "can_break": True,
        "break_hp": 12,
        "respawn_time": 4.0,
        "unlock_wave": 0,
        "description": "+15 Max HP. Respawns after 4s if destroyed.",
        "rarity": "common",
    },
    CellType.MOVE: {
        "name": "Move",
        "icon": "➤",
        "color": (80, 230, 160),
        "stats": {"speed": 70},
        "tags": {"move", "mobility"},
        "can_break": True,
        "break_hp": 8,
        "respawn_time": 2.0,
        "unlock_wave": 0,
        "description": "+70 Speed. Essential for dodging.",
        "rarity": "common",
    },
    CellType.DAMAGE: {
        "name": "Damage",
        "icon": "✦",
        "color": (255, 160, 60),
        "stats": {"contact_dmg": 12},
        "tags": {"contact_damage", "offensive"},
        "can_break": True,
        "break_hp": 15,
        "respawn_time": 1.5,
        "unlock_wave": 0,
        "description": "+12 Contact damage. Hurts nearby enemies.",
        "rarity": "common",
    },
    CellType.SHIELD: {
        "name": "Shield",
        "icon": "⬡",
        "color": (100, 160, 255),
        "stats": {"defense": 10},
        "tags": {"shield", "defensive"},
        "can_break": True,
        "break_hp": 20,
        "respawn_time": 3.0,
        "unlock_wave": 0,
        "description": "+10 Defense. Reduces incoming damage.",
        "rarity": "common",
    },
    CellType.REGEN: {
        "name": "Regen",
        "icon": "✚",
        "color": (100, 255, 150),
        "stats": {"regen": 1.2},
        "tags": {"regen", "healing", "vital"},
        "can_break": True,
        "break_hp": 10,
        "respawn_time": 5.0,
        "unlock_wave": 3,
        "description": "+1.2 HP/s regeneration. Sustain in combat.",
        "rarity": "uncommon",
    },
    CellType.SPIKE: {
        "name": "Spike",
        "icon": "⚡",
        "color": (255, 100, 255),
        "stats": {"reflect_dmg": 0.3},
        "tags": {"spike", "defensive", "offensive"},
        "can_break": True,
        "break_hp": 12,
        "respawn_time": 2.5,
        "unlock_wave": 5,
        "description": "Reflects 30% of damage taken back to attacker.",
        "rarity": "uncommon",
    },
    CellType.MAGNET: {
        "name": "Magnet",
        "icon": "◉",
        "color": (180, 180, 255),
        "stats": {"magnet_range": 120},
        "tags": {"magnet", "utility"},
        "can_break": True,
        "break_hp": 8,
        "respawn_time": 3.0,
        "unlock_wave": 7,
        "description": "Pulls XP and powerups from 120px away.",
        "rarity": "uncommon",
    },
    CellType.BURST: {
        "name": "Burst",
        "icon": "💥",
        "color": (255, 140, 0),
        "stats": {"burst_dmg": 40},
        "tags": {"burst", "offensive", "ability"},
        "can_break": True,
        "break_hp": 10,
        "respawn_time": 2.0,
        "unlock_wave": 10,
        "description": "Active: AOE burst dealing 40 damage (8s cooldown).",
        "rarity": "rare",
        "ability": {
            "type": "burst",
            "cooldown": 8.0,
            "radius": 150,
            "damage": 40,
        }
    },
    CellType.DASH: {
        "name": "Dash",
        "icon": "⚡",
        "color": (200, 255, 255),
        "stats": {"dash_speed": 800},
        "tags": {"dash", "mobility", "ability"},
        "can_break": True,
        "break_hp": 8,
        "respawn_time": 2.0,
        "unlock_wave": 12,
        "description": "Active: Quick dash (5s cooldown). Invulnerable while dashing.",
        "rarity": "rare",
        "ability": {
            "type": "dash",
            "cooldown": 5.0,
            "duration": 0.3,
            "speed": 800,
        }
    },
    CellType.LEECH: {
        "name": "Leech",
        "icon": "🩸",
        "color": (180, 50, 80),
        "stats": {"lifesteal": 0.25},
        "tags": {"leech", "offensive", "healing"},
        "can_break": True,
        "break_hp": 10,
        "respawn_time": 3.0,
        "unlock_wave": 15,
        "description": "Heal for 25% of damage dealt.",
        "rarity": "rare",
    },
    CellType.TOXIC: {
        "name": "Toxic",
        "icon": "☠",
        "color": (150, 255, 50),
        "stats": {"toxic_dps": 5},
        "tags": {"toxic", "offensive", "dot"},
        "can_break": True,
        "break_hp": 10,
        "respawn_time": 2.0,
        "unlock_wave": 18,
        "description": "Applies poison: 5 damage/s for 3s.",
        "rarity": "rare",
    },
    CellType.CRYSTAL: {
        "name": "Crystal",
        "icon": "💎",
        "color": (255, 215, 255),
        "stats": {"xp_mult": 0.15},
        "tags": {"crystal", "utility"},
        "can_break": True,
        "break_hp": 5,
        "respawn_time": 4.0,
        "unlock_wave": 20,
        "description": "+15% XP gain. Fragile but valuable.",
        "rarity": "rare",
    },
    CellType.VOID: {
        "name": "Void",
        "icon": "🌀",
        "color": (120, 80, 180),
        "stats": {"dodge_chance": 0.12},
        "tags": {"void", "defensive"},
        "can_break": True,
        "break_hp": 8,
        "respawn_time": 3.5,
        "unlock_wave": 25,
        "description": "12% chance to completely dodge attacks.",
        "rarity": "legendary",
    },
}


def get_cell_type_def(cell_type: CellType) -> Dict[str, Any]:
    """Get the definition for a cell type"""
    return CELL_TYPE_DEFS.get(cell_type, CELL_TYPE_DEFS[CellType.EMPTY])


def get_unlocked_cells(highest_wave: int) -> Set[CellType]:
    """Get all cell types unlocked at the given wave"""
    unlocked = set()
    for cell_type, data in CELL_TYPE_DEFS.items():
        if cell_type != CellType.EMPTY and data["unlock_wave"] <= highest_wave:
            unlocked.add(cell_type)
    return unlocked


def get_cell_rarity(cell_type: CellType) -> str:
    """Get the rarity of a cell type"""
    return get_cell_type_def(cell_type).get("rarity", "common")


# Cycle order for build phase (left-click cycling)
CELL_CYCLE = [
    CellType.HEART, CellType.MOVE, CellType.DAMAGE, CellType.SHIELD,
    CellType.REGEN, CellType.SPIKE, CellType.MAGNET, CellType.BURST,
    CellType.DASH, CellType.LEECH, CellType.TOXIC, CellType.CRYSTAL,
    CellType.VOID, CellType.EMPTY
]

# Starting inventory
STARTING_INVENTORY = {
    CellType.HEART:  2,
    CellType.MOVE:   1,
    CellType.DAMAGE: 1,
    CellType.SHIELD: 0,
}

# Cells awarded per wave
CELLS_PER_WAVE = 2
BONUS_CELL_WAVES = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
