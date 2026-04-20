# =============================================================================
# entities/player.py — The player-controlled hexagonal cell
# =============================================================================
# The Player is a living hexagon that moves through the world, accumulates
# body-part sockets, takes damage from enemies, and regenerates HP.
# =============================================================================

import pygame
import math
import random
from constants import (
    PLAYER_SPEED, PLAYER_BASE_HP, PLAYER_BASE_DEFENSE,
    PLAYER_BASE_REGEN, HEX_RADIUS, HEX_SIDES, HEX_SKINS,
    WORLD_WIDTH, WORLD_HEIGHT, COLOR_DANGER, COLOR_SUCCESS, SCREEN_WIDTH, SCREEN_HEIGHT,
)
from hex_renderer import draw_hex, hex_socket_positions
from asset_manager import assets
from abilities import Ability, ABILITIES, STARTER_ABILITY
from experience import LevelUp
from projectile import Projectile

class Player:
    """
    The player entity — a hexagonal cell navigated with WASD / arrow keys.
    Now with leveling, XP, and abilities!
    """

    INVINCIBILITY_DURATION = 0.5

    def __init__(self):
        self.x: float = WORLD_WIDTH / 2
        self.y: float = WORLD_HEIGHT / 2

        self.max_hp: float = PLAYER_BASE_HP
        self.hp: float = PLAYER_BASE_HP
        self.speed: float = PLAYER_SPEED
        self.defense: float = PLAYER_BASE_DEFENSE
        self.regen: float = PLAYER_BASE_REGEN

        self.sockets: list = [None] * HEX_SIDES

        self.skin: dict = HEX_SKINS[0] if HEX_SKINS else {}
        self.rotation: float = 0.0
        self.pulse_t: float = 0.0

        self.invincible: float = 0.0
        self._flash_timer: float = 0.0

        # NEW: Leveling & abilities
        self.level_system = LevelUp()
        self.abilities: list[Ability] = []
        self.projectiles: list[Projectile] = []
        self._auto_cast_timer = 0.0
        self._radius = HEX_RADIUS
        
        # Give the player a starter ability
        self.add_ability(STARTER_ABILITY)

    def set_skin(self, skin_data: dict):
        self.skin = skin_data

    def update(self, input_handler, dt: float):
        # Movement
        dx, dy = input_handler.get_movement_vector()
        if dx != 0 or dy != 0:
            # Normalize diagonal movement
            dist = math.hypot(dx, dy)
            self.x += (dx / dist) * self.speed * dt
            self.y += (dy / dist) * self.speed * dt
        
        # Clamp to world
        self.x = max(0, min(WORLD_WIDTH, self.x))
        self.y = max(0, min(WORLD_HEIGHT, self.y))
        
        # Regeneration
        self.hp = min(self.max_hp, self.hp + self.regen * dt)
        
        # Invincibility frames
        if self.invincible > 0:
            self.invincible -= dt
            self._flash_timer -= dt
        
        # Rotation
        self.rotation += dt * 0.5
        self.pulse_t += dt
        
        # Update abilities
        for ability in self.abilities:
            ability.update(dt)
        
        # Auto-cast abilities
        self._auto_cast_timer += dt
        if self._auto_cast_timer > 0.2:  # Check every 0.2s
            self._auto_cast_timer = 0.0
            for ability in self.abilities:
                if ability.is_auto and ability.can_cast():
                    self._cast_ability(ability, input_handler)
        
        # Right-click manual ability cast
        if input_handler.mouse_just_pressed(3):  # RMB
            if self.abilities and self.abilities[0].can_cast():
                self._cast_ability(self.abilities[0], input_handler)
        
        # Update projectiles
        for proj in self.projectiles[:]:
            proj.update(dt)
            if not proj.alive:
                self.projectiles.remove(proj)

    def _cast_ability(self, ability: Ability, input_handler):
        """Cast an ability toward mouse."""
        from camera import camera
        mx, my = input_handler.mouse_pos
        
        # Convert screen to world coords
        world_x = camera.x + mx - SCREEN_WIDTH / 2
        world_y = camera.y + my - SCREEN_HEIGHT / 2
        
        # Pass self (player) so projectile can track mouse
        proj = Projectile(self.x, self.y, world_x, world_y, ability.data, player=self)
        self.projectiles.append(proj)
        ability.cast()

    def take_damage(self, amount: float):
        if self.invincible > 0:
            return
        
        actual_dmg = max(1, amount - self.defense)
        self.hp -= actual_dmg
        self.invincible = self.INVINCIBILITY_DURATION
        self._flash_timer = 0.1

    def heal(self, amount: float):
        self.hp = min(self.max_hp, self.hp + amount)

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    def add_ability(self, ability_data: dict):
        """Add a new ability from leveling up."""
        if len(self.abilities) < 6:  # Max 6 abilities
            self.abilities.append(Ability(ability_data))

    def equip_part(self, slot: int, part: dict):
        if 0 <= slot < len(self.sockets):
            self.sockets[slot] = part
            self._recalculate_stats()

    def remove_part(self, slot: int):
        if 0 <= slot < len(self.sockets):
            self.sockets[slot] = None
            self._recalculate_stats()

    def _recalculate_stats(self):
        """Recalculate stats from equipped parts."""
        self.max_hp = PLAYER_BASE_HP
        self.defense = PLAYER_BASE_DEFENSE
        self.regen = PLAYER_BASE_REGEN
        for part in self.sockets:
            if part:
                self.max_hp += part.get("hp_bonus", 0)
                self.defense += part.get("def_bonus", 0)
                self.regen += part.get("regen_bonus", 0)
        self.hp = min(self.hp, self.max_hp)

    def draw(self, surface: pygame.Surface, camera):
        sx, sy = camera.world_to_screen(self.x, self.y)
        
        # Only draw if on screen
        if not camera.is_visible(self.x, self.y, margin=100):
            return
        
        # Draw hex
        draw_hex(surface, sx, sy, self.skin, HEX_RADIUS, self.rotation,
                 pulse_t=self.pulse_t, draw_sockets=True,
                 socket_states=[s is not None for s in self.sockets])
        
        # Flash on damage
        if self.invincible > 0 and int(self._flash_timer * 10) % 2 == 0:
            draw_hex(surface, sx, sy, None, HEX_RADIUS, self.rotation,
                    color=(255, 0, 0), width=2)

    def draw_hp_bar(self, surface: pygame.Surface, camera):
        """Draw player HP bar at the top of the screen."""
        from ui import draw_bar
        from constants import SCREEN_WIDTH
        
        bar_w = 300
        bar_x = SCREEN_WIDTH // 2 - bar_w // 2
        bar_y = 20
        
        draw_bar(surface, bar_x, bar_y, bar_w, 20, self.hp, self.max_hp,
                fill_color=(50, 255, 100))
        
        # Label
        font = assets.get_font("default", 14)
        label = font.render(f"HP: {int(self.hp)}/{int(self.max_hp)}", True, (255, 255, 255))
        surface.blit(label, (bar_x + 10, bar_y + 2))

    def draw_xp_bar(self, surface: pygame.Surface):
        """Draw XP progress bar below HP bar."""
        from ui import draw_bar
        from constants import SCREEN_WIDTH
        
        bar_w = 300
        bar_x = SCREEN_WIDTH // 2 - bar_w // 2
        bar_y = 50
        
        xp_pct = self.level_system.get_xp_percent()
        draw_bar(surface, bar_x, bar_y, bar_w, 20, xp_pct, 1.0,
                fill_color=(100, 150, 255))
        
        # Label
        font = assets.get_font("default", 14)
        label = font.render(
            f"XP: {self.level_system.current_xp}/{self.level_system.xp_needed}",
            True, (255, 255, 255))
        surface.blit(label, (bar_x + 10, bar_y + 2))

    def draw_abilities(self, surface: pygame.Surface):
        """Draw ability cooldown bars at bottom."""
        from constants import SCREEN_WIDTH, SCREEN_HEIGHT
        
        bar_w = 60
        bar_h = 12
        spacing = 70
        start_x = SCREEN_WIDTH // 2 - (len(self.abilities) * spacing) // 2
        
        for i, ability in enumerate(self.abilities):
            x = start_x + i * spacing
            y = SCREEN_HEIGHT - 50
            
            # Background
            pygame.draw.rect(surface, (50, 50, 50), (x, y, bar_w, bar_h))
            
            # Cooldown fill
            ready_pct = ability.get_ready_percent()
            fill_w = int(bar_w * ready_pct)
            col = ability.data["color"] if ready_pct == 1.0 else (100, 100, 100)
            pygame.draw.rect(surface, col, (x, y, fill_w, bar_h))
            
            # Border
            pygame.draw.rect(surface, (200, 200, 200), (x, y, bar_w, bar_h), 1)
            
            # Label
            font = assets.get_font("default", 10)
            label = font.render(ability.data["id"][:2].upper(), True, (255, 255, 255))
            surface.blit(label, (x + bar_w // 2 - 5, y - 12))

    @property
    def radius(self):
        return self._radius

    def collides_with(self, wx: float, wy: float, radius: float) -> bool:
        dist = math.hypot(self.x - wx, self.y - wy)
        return dist <= (HEX_RADIUS + radius)
