# =============================================================================
# entities/enemy.py — Enemy entities with basic seek-player AI
# =============================================================================
import math
import random
import pygame
from constants import (
    ENEMY_BASE_HP, ENEMY_BASE_SPEED, ENEMY_BASE_DMG,
    WORLD_WIDTH, WORLD_HEIGHT, HEX_RADIUS,
)
from hex_renderer import hex_vertices

# ------------------------------------------------------------------ Palettes
ENEMY_TIERS = [
    {"fill": (40, 10, 10), "border": (200, 60, 60),  "glow": (160, 30, 30)},   # tier 0 red
    {"fill": (10, 30, 50), "border": (60,  120, 200), "glow": (30, 80, 160)},  # tier 1 blue
    {"fill": (30, 10, 40), "border": (160, 50, 240),  "glow": (100, 20, 200)}, # tier 2 purple
    {"fill": (50, 35,  0), "border": (240, 180, 20),  "glow": (200, 130, 0)},  # tier 3 gold
]


class Enemy:
    def __init__(self, x: float, y: float, wave: int = 1):
        self.x = x
        self.y = y
        self.wave = wave
        
        # Scale stats by wave
        wave_scale = 1.0 + (wave - 1) * 0.15
        self.max_hp = ENEMY_BASE_HP * wave_scale
        self.hp = self.max_hp
        self.speed = ENEMY_BASE_SPEED * (1.0 + (wave - 1) * 0.05)
        self.damage = ENEMY_BASE_DMG * wave_scale
        
        self.radius = HEX_RADIUS * 0.8
        self.alive = True
        
        # Tier-based coloring
        tier = min(len(ENEMY_TIERS) - 1, wave // 10)
        self.tier_data = ENEMY_TIERS[tier]
        
        self.rotation = random.uniform(0, 2 * math.pi)

    def update(self, player_x: float, player_y: float, dt: float):
        """Move toward the player."""
        if not self.alive:
            return
        
        # Direction to player
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.hypot(dx, dy)
        
        if dist > 0:
            # Normalize and apply speed
            self.x += (dx / dist) * self.speed * dt
            self.y += (dy / dist) * self.speed * dt
            self.rotation += dt * 2.0
        
        # Clamp to world
        self.x = max(0, min(WORLD_WIDTH, self.x))
        self.y = max(0, min(WORLD_HEIGHT, self.y))

    def take_damage(self, amount: float):
        self.hp -= amount
        if self.hp <= 0:
            self.alive = False

    def collides_with_player(self, player) -> bool:
        """Check if this enemy is touching the player."""
        dist = math.hypot(self.x - player.x, self.y - player.y)
        return dist <= (self.radius + HEX_RADIUS)

    def draw(self, surface: pygame.Surface, camera):
        """Draw the enemy hex."""
        from hex_renderer import draw_hex_glow, hex_vertices
        
        # Check visibility
        if not camera.is_visible(self.x, self.y, margin=100):
            return
        
        sx, sy = camera.world_to_screen(self.x, self.y)
        
        # Draw glow
        draw_hex_glow(surface, sx, sy, self.radius, self.tier_data["glow"])
        
        # Draw hex body
        points = hex_vertices(sx, sy, self.radius, self.rotation)
        pygame.draw.polygon(surface, self.tier_data["fill"], points)
        pygame.draw.polygon(surface, self.tier_data["border"], points, width=2)
        
        # Draw HP bar above enemy
        self._draw_hp_bar(surface, sx, sy)

    def _draw_hp_bar(self, surface: pygame.Surface, sx: float, sy: float):
        """Draw a small HP bar above the enemy."""
        bar_w, bar_h = 40, 6
        bar_x = sx - bar_w / 2
        bar_y = sy - self.radius - 15
        
        # Background
        pygame.draw.rect(surface, (30, 30, 30), (bar_x, bar_y, bar_w, bar_h))
        
        # HP fill
        hp_percent = max(0, self.hp / self.max_hp)
        fill_w = bar_w * hp_percent
        hp_color = (100, 255, 100) if hp_percent > 0.5 else (255, 200, 50) if hp_percent > 0.2 else (255, 50, 50)
        pygame.draw.rect(surface, hp_color, (bar_x, bar_y, fill_w, bar_h))
        
        # Border
        pygame.draw.rect(surface, (150, 150, 150), (bar_x, bar_y, bar_w, bar_h), 1)


# ---------------------------------------------------------------- Spawning

def spawn_wave_enemies(wave: int, player_x: float, player_y: float,
                       count: int) -> list[Enemy]:
    """Spawn a batch of enemies around the player."""
    enemies = []
    for _ in range(count):
        # Spawn in a circle around the player at distance 400-600
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(400, 600)
        x = player_x + math.cos(angle) * dist
        y = player_y + math.sin(angle) * dist
        
        # Clamp to world
        x = max(0, min(WORLD_WIDTH, x))
        y = max(0, min(WORLD_HEIGHT, y))
        
        enemies.append(Enemy(x, y, wave))
    
    return enemies
