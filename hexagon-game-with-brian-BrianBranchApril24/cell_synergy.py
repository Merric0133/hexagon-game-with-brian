"""
cell_synergy.py — Synergy and combo system for cell builds.

Creates interesting build variety through:
  • Positional synergies (adjacent cell combinations)
  • Type synergies (scaling bonuses for multiples of a type)
  • Special abilities triggered by specific patterns
"""
from constants import CellType
from dataclasses import dataclass


@dataclass
class Synergy:
    name: str
    description: str
    bonus_type: str  # "damage", "speed", "hp", "defense", "regen", "special"
    magnitude: float
    condition: str  # how it's triggered


# ────────────────────────────────────────────────────────────────────────────
# POSITIONAL SYNERGIES — bonuses based on hex adjacency patterns
# ────────────────────────────────────────────────────────────────────────────

def get_positional_synergies(body: dict) -> dict:
    """
    Check the honeycomb body for specific adjacency patterns.
    Returns dict of {synergy_name: magnitude}
    
    body = {(q, r): CellType, ...} from build_scene
    """
    synergies = {}
    
    if not body:
        return synergies

    # Convert to simpler structure for easier checking
    occupied = set(body.keys())
    
    # CORE REINFORCEMENT: all 6 slots filled
    if len(occupied) == 6:
        synergies["core_reinforcement"] = 1.0
        # +25% all stats when completely surrounded
    
    # FORTRESS: 4+ SHIELD cells
    shield_count = sum(1 for ct in body.values() if ct == CellType.SHIELD)
    if shield_count >= 4:
        synergies["fortress"] = shield_count * 0.15
        # +15% defense per SHIELD cell (stacking)
    
    # AGGRESSIVE: 4+ DAMAGE cells
    damage_count = sum(1 for ct in body.values() if ct == CellType.DAMAGE)
    if damage_count >= 3:
        synergies["aggressive_stance"] = damage_count * 0.2
        # +20% contact damage per DAMAGE cell
    
    # SWIFT: 3+ MOVE cells
    move_count = sum(1 for ct in body.values() if ct == CellType.MOVE)
    if move_count >= 3:
        synergies["momentum"] = move_count * 0.12
        # +12% speed per MOVE cell
    
    # VITAL: 3+ HEART cells
    heart_count = sum(1 for ct in body.values() if ct == CellType.HEART)
    if heart_count >= 3:
        synergies["vital_core"] = heart_count * 0.18
        # +18% max HP and +0.2 regen per HEART cell
    
    # BALANCED: exactly 2 of each type
    type_counts = {}
    for ct in body.values():
        type_counts[ct] = type_counts.get(ct, 0) + 1
    
    active_types = len([c for c in type_counts.values() if c > 0])
    if active_types == 4 and all(c >= 1 for c in type_counts.values()):
        synergies["harmony"] = 0.15
        # +15% efficiency (less damage taken, faster actions)
    
    # SPIKY PATTERN: alternating damage and other types
    if _check_alternating_pattern(occupied, body, CellType.DAMAGE):
        synergies["thorny_exterior"] = 0.25
        # Enemies take contact damage when hitting you
    
    return synergies


def _check_alternating_pattern(occupied, body, target_type):
    """Check if target_type cells form an alternating ring."""
    if len(occupied) < 4:
        return False
    target_positions = [pos for pos, ct in body.items() if ct == target_type]
    other_positions = [pos for pos, ct in body.items() if ct != target_type]
    return len(target_positions) >= 2 and len(other_positions) >= 2


# ────────────────────────────────────────────────────────────────────────────
# TYPE SYNERGIES — bonuses for cell counts
# ────────────────────────────────────────────────────────────────────────────

def get_type_synergies(body: dict) -> dict:
    """Bonuses based on quantity of specific cell types."""
    synergies = {}
    type_counts = {}
    
    for ct in body.values():
        if ct != CellType.EMPTY:
            type_counts[ct] = type_counts.get(ct, 0) + 1
    
    # SCALING BONUSES
    # Each type gets better bonuses as you have more of it
    
    if CellType.HEART in type_counts:
        count = type_counts[CellType.HEART]
        synergies[f"heart_resilience_{count}"] = min(0.3, count * 0.08)
    
    if CellType.MOVE in type_counts:
        count = type_counts[CellType.MOVE]
        synergies[f"move_momentum_{count}"] = min(0.35, count * 0.1)
    
    if CellType.DAMAGE in type_counts:
        count = type_counts[CellType.DAMAGE]
        synergies[f"damage_focus_{count}"] = min(0.4, count * 0.12)
    
    if CellType.SHIELD in type_counts:
        count = type_counts[CellType.SHIELD]
        synergies[f"shield_hardening_{count}"] = min(0.35, count * 0.1)
    
    return synergies


# ────────────────────────────────────────────────────────────────────────────
# APPLY SYNERGIES — calculate final stat modifications
# ────────────────────────────────────────────────────────────────────────────

def apply_synergies_to_player(player, body: dict):
    """
    Scan the player's honeycomb body and apply all relevant synergies.
    Called after player is created or body changes.
    """
    synergies_pos = get_positional_synergies(body)
    synergies_type = get_type_synergies(body)
    all_synergies = {**synergies_pos, **synergies_type}
    
    player.active_synergies = all_synergies
    
    # Apply stat multipliers
    hp_mult = 1.0
    speed_mult = 1.0
    damage_mult = 1.0
    defense_mult = 1.0
    regen_bonus = 0.0
    contact_damage_mult = 1.0
    
    # Core Reinforcement: +25% all stats
    if "core_reinforcement" in all_synergies:
        hp_mult *= 1.25
        speed_mult *= 1.25
        damage_mult *= 1.25
        defense_mult *= 1.25
        contact_damage_mult *= 1.25
    
    # Fortress: +15% defense per SHIELD
    if "fortress" in all_synergies:
        defense_mult *= (1.0 + all_synergies["fortress"])
    
    # Aggressive Stance: +20% contact damage per DAMAGE
    if "aggressive_stance" in all_synergies:
        contact_damage_mult *= (1.0 + all_synergies["aggressive_stance"])
    
    # Momentum: +12% speed per MOVE
    if "momentum" in all_synergies:
        speed_mult *= (1.0 + all_synergies["momentum"])
    
    # Vital Core: +18% HP and +0.2 regen per HEART
    if "vital_core" in all_synergies:
        hp_mult *= (1.0 + all_synergies["vital_core"])
        regen_bonus += all_synergies["vital_core"] * 0.15
    
    # Harmony: +15% efficiency
    if "harmony" in all_synergies:
        defense_mult *= 1.15
        speed_mult *= 1.08
    
    # Thorny Exterior: special effect (handled in game_scene)
    if "thorny_exterior" in all_synergies:
        player.thorny_exterior_enabled = True
    
    # Apply scaling bonuses
    for key, bonus in all_synergies.items():
        if "resilience" in key:
            hp_mult *= (1.0 + bonus)
        elif "momentum" in key and "core" not in key:
            speed_mult *= (1.0 + bonus)
        elif "focus" in key:
            contact_damage_mult *= (1.0 + bonus)
        elif "hardening" in key:
            defense_mult *= (1.0 + bonus)
    
    # Store multipliers for application
    player.synergy_hp_mult = hp_mult
    player.synergy_speed_mult = speed_mult
    player.synergy_damage_mult = damage_mult
    player.synergy_defense_mult = defense_mult
    player.synergy_regen_bonus = regen_bonus
    player.synergy_contact_damage_mult = contact_damage_mult


def get_synergy_display(synergies: dict) -> list:
    """Return human-readable descriptions of active synergies for UI."""
    descriptions = []
    
    synergy_text = {
        "core_reinforcement": "🔥 Core Reinforcement: +25% all stats",
        "fortress": "🛡️ Fortress: Extra defense",
        "aggressive_stance": "⚔️ Aggressive Stance: Enhanced contact damage",
        "momentum": "💨 Momentum: Increased speed",
        "vital_core": "❤️ Vital Core: Better HP & regen",
        "harmony": "✨ Harmony: All systems efficient",
        "thorny_exterior": "🌹 Thorny Exterior: Reflect enemy damage",
    }
    
    for synergy_name, magnitude in synergies.items():
        if synergy_name in synergy_text:
            descriptions.append(synergy_text[synergy_name])
        elif "resilience" in synergy_name:
            descriptions.append(f"🩹 Heart Resilience: +{int(magnitude*100)}% HP")
        elif "momentum" in synergy_name and "core" not in synergy_name:
            descriptions.append(f"⚡ Move Momentum: +{int(magnitude*100)}% Speed")
        elif "focus" in synergy_name:
            descriptions.append(f"💥 Damage Focus: +{int(magnitude*100)}% Damage")
        elif "hardening" in synergy_name:
            descriptions.append(f"⛓️ Shield Hardening: +{int(magnitude*100)}% Defense")
    
    return descriptions
