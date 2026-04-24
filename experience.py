# =============================================================================
# systems/experience.py — XP drops and leveling system
# =============================================================================
import random
import math
from constants import COLOR_SUCCESS

XP_PER_LEVEL = 100  # Exponential: each level needs 100 * level more XP

class XpOrb:
    """A glowing XP drop that the player collects."""
    COLLECT_RADIUS = 30
    LIFETIME = 15.0
    
    def __init__(self, x: float, y: float, value: int = 10):
        self.x = x
        self.y = y
        self.value = value
        self.alive = True
        self.t = 0.0
        self._age = 0.0

    def update(self, dt: float):
        self.t += dt
        self._age += dt
        if self._age >= self.LIFETIME:
            self.alive = False

    def draw(self, surface, camera):
        import pygame
        sx, sy = camera.world_to_screen(self.x, self.y)
        
        # Bob animation
        bob = math.sin(self.t * 4.0) * 4
        sy += bob
        
        # Fade in/out
        age_ratio = self._age / self.LIFETIME
        alpha = 255 if age_ratio < 0.9 else int(255 * (1 - (age_ratio - 0.9) / 0.1))
        
        col = COLOR_SUCCESS
        glow_surf = pygame.Surface((50, 50), pygame.SRCALPHA)
        glow_col = (*col, int(100 * (alpha / 255)))
        pygame.draw.circle(glow_surf, glow_col, (25, 25), 20)
        surface.blit(glow_surf, (sx - 25, sy - 25), special_flags=pygame.BLEND_ALPHA_SDL2)
        
        pygame.draw.circle(surface, col, (int(sx), int(sy)), 6)

    def check_collect(self, player) -> bool:
        dist = math.hypot(self.x - player.x, self.y - player.y)
        return dist <= self.COLLECT_RADIUS


class LevelUp:
    """Tracks player level and XP."""
    def __init__(self):
        self.level = 1
        self.current_xp = 0
        self.xp_needed = XP_PER_LEVEL

    def add_xp(self, amount: int) -> list:
        """Add XP and return list of levels gained."""
        self.current_xp += amount
        levels_gained = []
        
        while self.current_xp >= self.xp_needed:
            self.current_xp -= self.xp_needed
            self.level += 1
            self.xp_needed = XP_PER_LEVEL * self.level
            levels_gained.append(self.level)
        
        return levels_gained

    def get_xp_percent(self) -> float:
        """Return 0.0-1.0 for XP bar."""
        return min(1.0, self.current_xp / self.xp_needed)