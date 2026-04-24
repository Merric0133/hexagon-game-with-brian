# =============================================================================
# entities/powerup.py — Collectible power-up drops
# =============================================================================
# Enemies have a chance to drop a power-up on death.
# The player collects it by moving over it.
# =============================================================================

import pygame
import math
import random
from constants import COLOR_SUCCESS, COLOR_WARNING, COLOR_ACCENT, COLOR_DANGER


# Power-up type definitions — id, label, colour, effect description
POWERUP_TYPES = [
    {
        "id":          "hp_small",
        "label":       "+20 HP",
        "color":       (60, 220, 100),
        "hp_restore":  20,
        "description": "Restores 20 HP",
    },
    {
        "id":          "hp_large",
        "label":       "+50 HP",
        "color":       (40, 255, 130),
        "hp_restore":  50,
        "description": "Restores 50 HP",
    },
    {
        "id":          "speed_boost",
        "label":       "FAST",
        "color":       (100, 200, 255),
        "speed_bonus": 60,
        "duration":    8.0,
        "description": "Speed +60 for 8 s",
    },
    {
        "id":          "shield",
        "label":       "SHIELD",
        "color":       (180, 140, 255),
        "invincible":  4.0,
        "description": "4 s of invincibility",
    },
]


class Powerup:
    """
    A collectible item floating in the world.
    Glows and bobs up/down to attract the player.
    Disappears after LIFETIME seconds if not collected.
    """

    LIFETIME        = 10.0   # seconds before despawn
    COLLECT_RADIUS  = 28     # world-space collection radius

    def __init__(self, x: float, y: float):
        self.x     = x
        self.y     = y
        self.ptype = random.choice(POWERUP_TYPES)
        self.t     = 0.0
        self.alive = True
        self._age  = 0.0

    # --------------------------------------------------------------- Update

    def update(self, dt: float):
        self.t    += dt
        self._age += dt
        if self._age >= self.LIFETIME:
            self.alive = False

    # ---------------------------------------------------------------- Apply

    def apply(self, player):
        """Apply this power-up's effect to the player."""
        pt = self.ptype
        if "hp_restore" in pt:
            player.heal(pt["hp_restore"])
        if "speed_bonus" in pt:
            # Temporary speed boost — tracked by the game scene
            player._temp_speed_bonus  = pt["speed_bonus"]
            player._temp_speed_timer  = pt["duration"]
        if "invincible" in pt:
            player.invincible = pt["invincible"]
        self.alive = False

    # ----------------------------------------------------------------- Draw

    def draw(self, surface: pygame.Surface, camera):
        """Render the power-up as a glowing animated orb."""
        sx, sy = camera.world_to_screen(self.x, self.y)

        # Bob up and down
        bob = math.sin(self.t * 3.0) * 5
        sy += bob

        # Fade out in last 2 seconds
        age_ratio = self._age / self.LIFETIME
        alpha = 255 if age_ratio < 0.8 else int(255 * (1 - (age_ratio - 0.8) / 0.2))

        col = self.ptype["color"]

        # Outer glow ring
        glow_surf = pygame.Surface((70, 70), pygame.SRCALPHA)
        glow_col  = (*col, int(50 * (alpha / 255)))
        pygame.draw.circle(glow_surf, glow_col, (35, 35), 30)
        surface.blit(glow_surf, (sx - 35, sy - 35),
                     special_flags=pygame.BLEND_ALPHA_SDL2)

        # Core circle
        core_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(core_surf, (*col, alpha), (15, 15), 12)
        pygame.draw.circle(core_surf, (255, 255, 255, int(alpha * 0.4)), (15, 15), 7)
        surface.blit(core_surf, (sx - 15, sy - 15),
                     special_flags=pygame.BLEND_ALPHA_SDL2)

        # Label
        font = pygame.font.Font(None, 16)
        lbl  = font.render(self.ptype["label"], True, col)
        surface.blit(lbl, (sx - lbl.get_width() // 2, sy + 16))

    # --------------------------------------------------------- Collision

    def check_collect(self, player) -> bool:
        """Return True if player is close enough to collect this power-up."""
        dx      = self.x - player.x
        dy      = self.y - player.y
        dist_sq = dx * dx + dy * dy
        return dist_sq < self.COLLECT_RADIUS ** 2
