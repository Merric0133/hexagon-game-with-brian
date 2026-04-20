# =============================================================================
# systems/abilities.py — Active combat abilities for the player
# =============================================================================
import math
import random
from constants import COLOR_ACCENT, COLOR_DANGER, COLOR_SUCCESS

STARTER_ABILITY = {
    "id": "basic_shot",
    "name": "Basic Shot",
    "description": "Your starting ability. Fast projectile.",
    "damage": 10,
    "cooldown": 0.8,
    "range": 300,
    "rarity": "common",
    "color": (100, 200, 255),
}

ABILITIES = [
    {
        "id": "fireball",
        "name": "Fireball",
        "description": "Launch a projectile that explodes on impact",
        "damage": 15,
        "cooldown": 1.2,
        "range": 300,
        "rarity": "common",
        "color": (255, 100, 50),
    },
    {
        "id": "slash",
        "name": "Slash",
        "description": "Swift melee attack in front of you",
        "damage": 8,
        "cooldown": 0.6,
        "range": 60,
        "rarity": "common",
        "color": (200, 100, 255),
    },
    {
        "id": "beam",
        "name": "Laser Beam",
        "description": "Fire a continuous beam",
        "damage": 12,
        "cooldown": 2.0,
        "range": 400,
        "rarity": "uncommon",
        "color": (0, 255, 100),
    },
    {
        "id": "nova",
        "name": "Nova Burst",
        "description": "Explode in all directions, damaging nearby enemies",
        "damage": 20,
        "cooldown": 3.0,
        "range": 150,
        "rarity": "rare",
        "color": (255, 255, 0),
    },
    {
        "id": "whip",
        "name": "Void Whip",
        "description": "Lash out with a tendril of dark energy",
        "damage": 18,
        "cooldown": 1.5,
        "range": 200,
        "rarity": "rare",
        "color": (150, 50, 255),
    },
]

class Ability:
    """A single equipped ability with cooldown tracking."""
    def __init__(self, ability_data: dict):
        self.data = ability_data
        self.cooldown_remaining = 0.0
        self.is_auto = True  # Auto-cast by default

    def update(self, dt: float):
        self.cooldown_remaining = max(0, self.cooldown_remaining - dt)

    def can_cast(self) -> bool:
        return self.cooldown_remaining <= 0

    def cast(self):
        self.cooldown_remaining = self.data["cooldown"]

    def get_ready_percent(self) -> float:
        """Return 0.0-1.0 for cooldown bar."""
        return 1.0 - (self.cooldown_remaining / self.data["cooldown"])