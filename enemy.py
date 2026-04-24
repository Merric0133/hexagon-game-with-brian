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

# ------------------------------------------------------------------ Palettes / types
ENEMY_TIERS = [
    {"fill": (40, 10, 10), "border": (200, 60, 60), "glow": (160, 30, 30)},      # tier 0 red
    {"fill": (10, 30, 50), "border": (60, 120, 200), "glow": (30, 80, 160)},     # tier 1 blue
    {"fill": (30, 10, 40), "border": (160, 50, 240), "glow": (100, 20, 200)},    # tier 2 purple
    {"fill": (50, 35, 0), "border": (240, 180, 20), "glow": (200, 130, 0)},      # tier 3 gold
]

ENEMY_TYPES = {
    "grunt": {
        "hp_mult": 1.0,
        "speed_mult": 1.0,
        "dmg_mult": 2.0,
        "radius_mult": 0.8,
        "rotation_mult": 2.0,
        "zigzag_strength": 0.0,
        "draw_width": 2,
    },
    "tank": {
        "hp_mult": 2.2,
        "speed_mult": 0.68,
        "dmg_mult": 2.35,
        "radius_mult": 1.05,
        "rotation_mult": 1.0,
        "zigzag_strength": 0.0,
        "draw_width": 3,
    },
    "scout": {
        "hp_mult": 0.62,
        "speed_mult": 1.55,
        "dmg_mult": 1.75,
        "radius_mult": 0.68,
        "rotation_mult": 3.6,
        "zigzag_strength": 0.42,
        "draw_width": 1,
    },
}


class Enemy:
    def __init__(self, x: float, y: float, wave: int = 1, enemy_type: str = "grunt"):
        self.x = x
        self.y = y
        self.wave = wave
        self.enemy_type = enemy_type if enemy_type in ENEMY_TYPES else "grunt"
        type_data = ENEMY_TYPES[self.enemy_type]

        # Scale stats by wave
        wave_scale = 1.0 + (wave - 1) * 0.15
        self.max_hp = ENEMY_BASE_HP * wave_scale * type_data["hp_mult"]
        self.hp = self.max_hp
        self.speed = ENEMY_BASE_SPEED * (1.0 + (wave - 1) * 0.05) * type_data["speed_mult"]
        self.damage = ENEMY_BASE_DMG * wave_scale * type_data["dmg_mult"]

        self.radius = HEX_RADIUS * type_data["radius_mult"]
        self.alive = True

        # Tier-based coloring
        tier = min(len(ENEMY_TIERS) - 1, wave // 10)
        self.tier_data = ENEMY_TIERS[tier]

        self.rotation = random.uniform(0, 2 * math.pi)
        self.rotation_mult = type_data["rotation_mult"]
        self.zigzag_strength = type_data["zigzag_strength"]
        self.draw_width = type_data["draw_width"]
        self.move_phase = random.uniform(0, 2 * math.pi)

    def update(self, player_x: float, player_y: float, dt: float):
        """Move toward the player."""
        if not self.alive:
            return

        # Direction to player
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.hypot(dx, dy)

        if dist > 0:
            nx = dx / dist
            ny = dy / dist

            # Scout-type enemies weave as they chase.
            if self.zigzag_strength > 0:
                self.move_phase += dt * 9.0
                sway = math.sin(self.move_phase) * self.zigzag_strength
                nx, ny = nx - ny * sway, ny + nx * sway
                nlen = math.hypot(nx, ny) or 1.0
                nx, ny = nx / nlen, ny / nlen

            self.x += nx * self.speed * dt
            self.y += ny * self.speed * dt
            self.rotation += dt * self.rotation_mult

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
        pygame.draw.polygon(surface, self.tier_data["border"], points, width=self.draw_width)

        if self.enemy_type == "tank":
            inner = hex_vertices(sx, sy, self.radius * 0.62, -self.rotation * 0.4)
            pygame.draw.polygon(surface, (80, 80, 90), inner, width=2)
        elif self.enemy_type == "scout":
            core = pygame.Rect(0, 0, int(self.radius * 0.7), int(self.radius * 0.7))
            core.center = (sx, sy)
            pygame.draw.rect(surface, (235, 235, 235), core, width=1, border_radius=2)

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
        # Spawn in a wider ring around the player.
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(550, 1350)
        x = player_x + math.cos(angle) * dist
        y = player_y + math.sin(angle) * dist

        # Clamp to world
        x = max(0, min(WORLD_WIDTH, x))
        y = max(0, min(WORLD_HEIGHT, y))

        # Mix enemy types as waves progress.
        if wave < 4:
            enemy_type = "grunt"
        else:
            roll = random.random()
            tank_chance = min(0.42, 0.12 + wave * 0.01)
            scout_chance = min(0.34, 0.06 + wave * 0.008)
            if roll < tank_chance:
                enemy_type = "tank"
            elif roll < tank_chance + scout_chance:
                enemy_type = "scout"
            else:
                enemy_type = "grunt"

        enemies.append(Enemy(x, y, wave, enemy_type=enemy_type))

    return enemies
