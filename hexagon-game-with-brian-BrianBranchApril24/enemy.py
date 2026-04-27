"""
enemy.py — Enhanced enemy entities with smart AI and diverse types.

Enemy types:
  • GRUNT: Basic balanced enemy
  • TANK: Slow heavy hitter with high HP
  • SCOUT: Fast, evasive, lower damage
  • SPITTER: Ranged enemy that shoots projectiles
  • SWARM: Small weak enemies that split on death
"""
import math
import random
import pygame
from constants import (
    ENEMY_BASE_HP, ENEMY_BASE_SPEED, ENEMY_BASE_DMG,
    WORLD_WIDTH, WORLD_HEIGHT, HEX_RADIUS,
)
from hex_renderer import hex_vertices, draw_hex_glow

# ────────────────────────────────────────────────────────────────────────────
# ENEMY TYPE DEFINITIONS
# ────────────────────────────────────────────────────────────────────────────

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
        "dmg_mult": 1.0,
        "radius_mult": 0.8,
        "rotation_mult": 2.0,
        "behavior": "chase",
        "draw_width": 2,
        "special": None,
    },
    "tank": {
        "hp_mult": 2.4,
        "speed_mult": 0.65,
        "dmg_mult": 1.4,
        "radius_mult": 1.15,
        "rotation_mult": 0.8,
        "behavior": "chase",
        "draw_width": 3,
        "special": "heavy_impact",  # Deals extra knockback
    },
    "scout": {
        "hp_mult": 0.55,
        "speed_mult": 1.7,
        "dmg_mult": 0.8,
        "radius_mult": 0.65,
        "rotation_mult": 4.2,
        "behavior": "strafe",  # Circles the player
        "draw_width": 1,
        "special": "evasive",  # Dodges projectiles
    },
    "spitter": {
        "hp_mult": 1.2,
        "speed_mult": 0.9,
        "dmg_mult": 0.6,
        "radius_mult": 0.85,
        "rotation_mult": 1.5,
        "behavior": "ranged",  # Keeps distance, shoots
        "draw_width": 2,
        "special": "projectile",
    },
    "swarm": {
        "hp_mult": 0.4,
        "speed_mult": 1.3,
        "dmg_mult": 0.5,
        "radius_mult": 0.55,
        "rotation_mult": 3.0,
        "behavior": "cluster",  # Groups with others
        "draw_width": 1,
        "special": "splits",  # Spawns two smaller on death
    },
}


# ────────────────────────────────────────────────────────────────────────────
# ENEMY CLASS
# ────────────────────────────────────────────────────────────────────────────

class Enemy:
    def __init__(self, x: float, y: float, wave: int = 1, enemy_type: str = "grunt"):
        self.x = x
        self.y = y
        self.wave = wave
        self.enemy_type = enemy_type if enemy_type in ENEMY_TYPES else "grunt"
        type_data = ENEMY_TYPES[self.enemy_type]

        # Scale stats by wave with better progression
        wave_scale = 1.0 + (wave - 1) * 0.12
        self.max_hp = ENEMY_BASE_HP * wave_scale * type_data["hp_mult"]
        self.hp = self.max_hp
        self.speed = ENEMY_BASE_SPEED * (1.0 + (wave - 1) * 0.04) * type_data["speed_mult"]
        self.damage = ENEMY_BASE_DMG * wave_scale * type_data["dmg_mult"]

        self.radius = HEX_RADIUS * type_data["radius_mult"]
        self.alive = True

        # Tier-based coloring
        tier = min(len(ENEMY_TIERS) - 1, wave // 12)
        self.tier_data = ENEMY_TIERS[tier]

        # Rotation
        self.rotation = random.uniform(0, 2 * math.pi)
        self.rotation_mult = type_data["rotation_mult"]
        self.draw_width = type_data["draw_width"]

        # Behavior
        self.behavior = type_data["behavior"]
        self.special = type_data["special"]
        
        # AI state
        self.move_phase = random.uniform(0, 2 * math.pi)
        self.target_angle = 0
        self.preferred_distance = 350 if self.behavior == "ranged" else 50
        self.dodge_timer = 0.0
        self.dodge_direction = 0

        # Ranged attack
        self.shoot_timer = 0.0
        self.shoot_cooldown = random.uniform(1.5, 3.0)

    # ────────────────────────────────────────────────────────────────────────
    # UPDATE & AI
    # ────────────────────────────────────────────────────────────────────────

    def update(self, player_x: float, player_y: float, dt: float):
        """Update position and AI."""
        if not self.alive:
            return

        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.hypot(dx, dy)

        if dist > 0:
            target_nx = dx / dist
            target_ny = dy / dist
        else:
            target_nx, target_ny = 0, -1

        # Apply behavior
        if self.behavior == "chase":
            self._move_toward(target_nx, target_ny, dt)
        
        elif self.behavior == "strafe":
            self._strafe_around(target_nx, target_ny, dist, dt)
        
        elif self.behavior == "ranged":
            self._ranged_approach(target_nx, target_ny, dist, dt)
        
        elif self.behavior == "cluster":
            self._cluster_movement(target_nx, target_ny, dt)

        # Clamp to world
        self.x = max(0, min(WORLD_WIDTH, self.x))
        self.y = max(0, min(WORLD_HEIGHT, self.y))

        # Rotation
        self.rotation += dt * self.rotation_mult

        # Shoot cooldown
        self.shoot_timer += dt

    def _move_toward(self, nx: float, ny: float, dt: float):
        """Chase directly toward target."""
        self.x += nx * self.speed * dt
        self.y += ny * self.speed * dt

    def _strafe_around(self, nx: float, ny: float, dist: float, dt: float):
        """Circle around the target, staying at comfortable distance."""
        target_dist = 200 if dist < 300 else 150
        
        if dist < target_dist - 50:
            # Too close, back away
            self.x -= nx * self.speed * 0.6 * dt
            self.y -= ny * self.speed * 0.6 * dt
        elif dist > target_dist + 50:
            # Too far, approach
            self.x += nx * self.speed * 0.8 * dt
            self.y += ny * self.speed * 0.8 * dt
        else:
            # Strafe around
            self.move_phase += dt * 3.0
            strafe = math.sin(self.move_phase) * 0.7
            move_x = nx - ny * strafe
            move_y = ny + nx * strafe
            move_len = math.hypot(move_x, move_y)
            if move_len > 0:
                self.x += (move_x / move_len) * self.speed * dt
                self.y += (move_y / move_len) * self.speed * dt

    def _ranged_approach(self, nx: float, ny: float, dist: float, dt: float):
        """Stay at distance and attack."""
        if dist < self.preferred_distance - 100:
            # Back away from player
            self.x -= nx * self.speed * 0.7 * dt
            self.y -= ny * self.speed * 0.7 * dt
        elif dist > self.preferred_distance + 150:
            # Approach slowly
            self.x += nx * self.speed * 0.5 * dt
            self.y += ny * self.speed * 0.5 * dt
        # else: stay at range, handle shooting in game_scene

    def _cluster_movement(self, nx: float, ny: float, dt: float):
        """Move in loose groups, herding behavior."""
        self.move_phase += dt * 4.0
        
        # Slight sine wave in movement
        sway = math.sin(self.move_phase) * 0.3
        move_x = nx - (ny * sway)
        move_y = ny + (nx * sway)
        
        move_len = math.hypot(move_x, move_y)
        if move_len > 0:
            self.x += (move_x / move_len) * self.speed * dt
            self.y += (move_y / move_len) * self.speed * dt

    # ────────────────────────────────────────────────────────────────────────
    # DAMAGE & DEATH
    # ────────────────────────────────────────────────────────────────────────

    def take_damage(self, amount: float):
        self.hp -= amount
        if self.hp <= 0:
            self.alive = False

    def can_shoot(self) -> bool:
        """Check if spitter is ready to attack."""
        return self.shoot_timer >= self.shoot_cooldown

    def reset_shoot_timer(self):
        self.shoot_timer = 0.0

    # ────────────────────────────────────────────────────────────────────────
    # COLLISION
    # ────────────────────────────────────────────────────────────────────────

    def collides_with_player(self, player) -> bool:
        """Check if this enemy is touching the player."""
        dist = math.hypot(self.x - player.x, self.y - player.y)
        return dist <= (self.radius + HEX_RADIUS)

    # ────────────────────────────────────────────────────────────────────────
    # DRAWING
    # ────────────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface, camera):
        """Draw the enemy hex."""
        if not camera.is_visible(self.x, self.y, margin=100):
            return

        sx, sy = camera.world_to_screen(self.x, self.y)
        sx, sy = int(sx), int(sy)

        # Glow
        draw_hex_glow(surface, sx, sy, self.radius, self.tier_data["glow"])

        # Body
        points = hex_vertices(sx, sy, self.radius, self.rotation)
        pygame.draw.polygon(surface, self.tier_data["fill"], points)
        pygame.draw.polygon(surface, self.tier_data["border"], points, width=self.draw_width)

        # Special visuals
        if self.enemy_type == "tank":
            inner = hex_vertices(sx, sy, self.radius * 0.6, -self.rotation * 0.4)
            pygame.draw.polygon(surface, (80, 80, 90), inner, width=2)
        
        elif self.enemy_type == "scout":
            core = pygame.Rect(0, 0, int(self.radius * 0.7), int(self.radius * 0.7))
            core.center = (sx, sy)
            pygame.draw.rect(surface, (235, 235, 235), core, width=1, border_radius=2)
        
        elif self.enemy_type == "spitter":
            # Draw targeting reticle if ready to shoot
            if self.can_shoot():
                pygame.draw.circle(surface, (255, 150, 150), (sx, sy), int(self.radius * 0.4), 1)
        
        elif self.enemy_type == "swarm":
            # Smaller, simpler design
            pygame.draw.circle(surface, self.tier_data["fill"], (sx, sy), int(self.radius))

        # HP bar
        self._draw_hp_bar(surface, sx, sy)

    def _draw_hp_bar(self, surface: pygame.Surface, sx: float, sy: float):
        """Draw a small HP bar above the enemy."""
        bar_w, bar_h = 40, 6
        bar_x = sx - bar_w / 2
        bar_y = sy - self.radius - 15

        # Background
        pygame.draw.rect(surface, (30, 30, 30), (bar_x, bar_y, bar_w, bar_h))

        # Fill
        hp_percent = max(0, self.hp / self.max_hp)
        fill_w = bar_w * hp_percent
        hp_color = (100, 255, 100) if hp_percent > 0.5 else (255, 200, 50) if hp_percent > 0.2 else (255, 50, 50)
        pygame.draw.rect(surface, hp_color, (bar_x, bar_y, fill_w, bar_h))

        # Border
        pygame.draw.rect(surface, (150, 150, 150), (bar_x, bar_y, bar_w, bar_h), 1)


# ────────────────────────────────────────────────────────────────────────────
# SPAWNING
# ────────────────────────────────────────────────────────────────────────────

def spawn_wave_enemies(wave: int, player_x: float, player_y: float,
                       count: int) -> list:
    """Spawn a varied wave of enemies with smart distribution."""
    enemies = []
    
    for i in range(count):
        # Spawn in a wider ring around the player
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(600, 1400)
        x = player_x + math.cos(angle) * dist
        y = player_y + math.sin(angle) * dist

        # Clamp to world
        x = max(HEX_RADIUS, min(WORLD_WIDTH - HEX_RADIUS, x))
        y = max(HEX_RADIUS, min(WORLD_HEIGHT - HEX_RADIUS, y))

        # Enemy type distribution improves with wave
        enemy_type = _select_enemy_type(wave, i, count)
        
        enemies.append(Enemy(x, y, wave, enemy_type=enemy_type))

    return enemies


def _select_enemy_type(wave: int, index: int, total: int) -> str:
    """Determine enemy type based on wave and position."""
    
    # Early waves: mostly grunts
    if wave <= 3:
        return "grunt"
    
    # Waves 4-9: Start introducing scouts
    if wave < 10:
        roll = random.random()
        if roll < 0.1 * wave:  # 10-90% scouts by wave 9
            return "scout"
        return "grunt"
    
    # Waves 10-19: More variety
    if wave < 20:
        roll = random.random()
        tank_chance = min(0.35, 0.15 + wave * 0.015)
        scout_chance = min(0.35, 0.25 + wave * 0.01)
        spitter_chance = min(0.2, 0.05 + wave * 0.008)
        
        if roll < tank_chance:
            return "tank"
        elif roll < tank_chance + scout_chance:
            return "scout"
        elif roll < tank_chance + scout_chance + spitter_chance:
            return "spitter"
        return "grunt"
    
    # Waves 20+: Full variety with late-game scaling
    roll = random.random()
    tank_chance = min(0.4, 0.3 + wave * 0.01)
    scout_chance = min(0.35, 0.3 + wave * 0.005)
    spitter_chance = min(0.25, 0.15 + wave * 0.008)
    swarm_chance = min(0.2, 0.05 + wave * 0.005)
    
    if roll < swarm_chance:
        return "swarm"
    elif roll < swarm_chance + spitter_chance:
        return "spitter"
    elif roll < swarm_chance + spitter_chance + tank_chance:
        return "tank"
    elif roll < swarm_chance + spitter_chance + tank_chance + scout_chance:
        return "scout"
    return "grunt"
