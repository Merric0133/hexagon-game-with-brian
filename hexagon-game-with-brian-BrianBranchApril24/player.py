"""
player.py — Enhanced player entity with synergy system.

The player is a hexagonal organism that:
  - Has a core and 6 attachment slots
  - Gains stat bonuses from cell combinations (synergies)
  - Can trigger special abilities based on build
  - Takes damage from enemies via projectiles or contact
  - Regenerates health over time
"""
import math
import pygame
from constants import (
    PLAYER_BASE_SPEED, PLAYER_BASE_HP, PLAYER_BASE_REGEN,
    WORLD_WIDTH, WORLD_HEIGHT, HEX_RADIUS, CELL_OFFSET,
    CELL_TYPE_DEFS, CellType, HEX_DIRECTIONS, COLOR_DANGER,
)
from cell import Cell
from experience import LevelUp
from cell_synergy import apply_synergies_to_player, get_synergy_display


class Player:
    def __init__(self, body_layout: list = None):
        """
        body_layout: [{"q": int, "r": int, "type": CellType}, ...]
        from build_scene honeycomb
        """
        # World position
        self.x = WORLD_WIDTH / 2
        self.y = WORLD_HEIGHT / 2
        self.vx = 0.0
        self.vy = 0.0
        self.is_alive = True

        # Base stats (before synergies)
        self.max_hp = PLAYER_BASE_HP
        self.hp = self.max_hp
        self.base_speed = PLAYER_BASE_SPEED
        self.speed = PLAYER_BASE_SPEED
        self.regen_rate = PLAYER_BASE_REGEN
        self.radius = HEX_RADIUS
        self.contact_dmg = 0.0

        # Synergy multipliers (applied from cell_synergy)
        self.synergy_hp_mult = 1.0
        self.synergy_speed_mult = 1.0
        self.synergy_damage_mult = 1.0
        self.synergy_defense_mult = 1.0
        self.synergy_regen_bonus = 0.0
        self.synergy_contact_damage_mult = 1.0
        self.thorny_exterior_enabled = False

        # Defense reduces incoming damage
        self.defense = 0

        # Invincibility frames
        self.invincible = 0.0
        self._invuln_flash = 0.0

        # Temporary power-ups
        self._temp_speed_bonus = 0.0
        self._temp_speed_timer = 0.0

        # Cells (0-5 slots around the core)
        self.cells = {i: Cell(i, CellType.EMPTY) for i in range(6)}
        self.active_synergies = {}

        # Level & XP
        self.level_system = LevelUp()

        # Build honeycomb structure from body_layout
        self.honeycomb_body = {}
        if body_layout:
            for item in body_layout:
                self.honeycomb_body[(item["q"], item["r"])] = item["type"]

        # Skin / visual customization
        self._skin = None

        # Contact damage cooldowns (per cell slot)
        self._contact_cooldowns = {i: 0.0 for i in range(6)}

        # Apply synergies from initial body
        self._recalculate_stats()

    # ────────────────────────────────────────────────────────────────────────
    # SYNERGY & STAT CALCULATION
    # ────────────────────────────────────────────────────────────────────────

    def _recalculate_stats(self):
        """Rebuild stats from honeycomb body and synergies."""
        # Reset to base
        self.max_hp = PLAYER_BASE_HP
        self.speed = PLAYER_BASE_SPEED
        self.contact_dmg = 0.0
        self.defense = 0
        self.regen_rate = PLAYER_BASE_REGEN

        # Apply cell bonuses
        for cell_type in self.honeycomb_body.values():
            if cell_type == CellType.EMPTY:
                continue
            cell_def = CELL_TYPE_DEFS.get(cell_type, {})
            stats = cell_def.get("stats", {})
            self.max_hp += stats.get("max_hp", 0)
            self.speed += stats.get("speed", 0)
            self.contact_dmg += stats.get("contact_dmg", 0)
            self.defense += stats.get("defense", 0)

        # Apply synergy multipliers
        self.max_hp *= self.synergy_hp_mult
        self.speed *= self.synergy_speed_mult
        self.contact_dmg *= self.synergy_contact_damage_mult
        self.defense *= self.synergy_defense_mult
        self.regen_rate += self.synergy_regen_bonus

        # Clamp HP to max if it exceeds
        self.hp = min(self.hp, self.max_hp)

    # ────────────────────────────────────────────────────────────────────────
    # UPDATE
    # ────────────────────────────────────────────────────────────────────────

    def update(self, input_handler, dt: float):
        """Update position, regen, invincibility, etc."""
        if not self.is_alive:
            return

        # Movement
        dx, dy = input_handler.get_movement_vector()
        if dx != 0 or dy != 0:
            length = math.hypot(dx, dy)
            dx /= length
            dy /= length

        current_speed = self.speed
        if self._temp_speed_timer > 0:
            self._temp_speed_timer -= dt
            current_speed += self._temp_speed_bonus

        self.vx = dx * current_speed
        self.vy = dy * current_speed

        self.x += self.vx * dt
        self.y += self.vy * dt

        # Clamp to world
        margin = self.radius
        self.x = max(margin, min(WORLD_WIDTH - margin, self.x))
        self.y = max(margin, min(WORLD_HEIGHT - margin, self.y))

        # Regeneration
        self.hp = min(self.max_hp, self.hp + self.regen_rate * dt)

        # Invincibility
        if self.invincible > 0:
            self.invincible -= dt
        self._invuln_flash -= dt

        # Contact damage cooldowns
        for i in self._contact_cooldowns:
            self._contact_cooldowns[i] = max(0, self._contact_cooldowns[i] - dt)

        # Cell updates (flash timers)
        for cell in self.cells.values():
            if cell.flash_timer > 0:
                cell.flash_timer -= dt

    # ────────────────────────────────────────────────────────────────────────
    # DAMAGE & COLLISION
    # ────────────────────────────────────────────────────────────────────────

    def take_damage(self, amount: float):
        """Apply damage with defense reduction."""
        if self.invincible > 0:
            return
        
        # Defense reduces damage
        reduced = amount * (1.0 - (self.defense / (self.defense + 100)))
        self.hp -= reduced
        self._invuln_flash = 0.15  # Damage flash
        
        if self.hp <= 0:
            self.is_alive = False

    def heal(self, amount: float):
        """Restore health."""
        self.hp = min(self.max_hp, self.hp + amount)

    def apply_enemy_collision(self, enemy, damage: float):
        """Called when enemy touches player. Returns which cell was hit."""
        self.take_damage(damage)
        return "core"  # Could be extended to hit specific cells

    def try_contact_damage(self, cell_key: int) -> bool:
        """Trigger contact damage on a cell. Returns True if successful."""
        if self._contact_cooldowns[cell_key] <= 0:
            self._contact_cooldowns[cell_key] = 0.3  # Per-cell cooldown
            return True
        return False

    def get_damage_cell_positions(self) -> list:
        """Return list of (cell_id, world_pos) for all damage cells."""
        dmg_cells = []
        for q, r in self.honeycomb_body.keys():
            cell_type = self.honeycomb_body[(q, r)]
            if cell_type == CellType.DAMAGE:
                wx = self.x + q * CELL_OFFSET
                wy = self.y + r * CELL_OFFSET
                dmg_cells.append(((q, r), (wx, wy)))
        return dmg_cells

    # ────────────────────────────────────────────────────────────────────────
    # SKIN & VISUAL
    # ────────────────────────────────────────────────────────────────────────

    def set_skin(self, skin: dict):
        """Set the hexagon skin (color scheme)."""
        self._skin = skin

    # ────────────────────────────────────────────────────────────────────────
    # DRAWING
    # ────────────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface, camera):
        """Draw player core and all honeycomb cells."""
        from hex_renderer import draw_hex, hex_vertices, draw_hex_glow

        if not camera.is_visible(self.x, self.y, margin=150):
            return

        sx, sy = camera.world_to_screen(self.x, self.y)
        sx, sy = int(sx), int(sy)

        # Glow
        if self.invincible > 0:
            glow_color = (100, 200, 255)
        elif self.hp < self.max_hp * 0.3:
            glow_color = (255, 100, 100)
        else:
            glow_color = (0, 150, 200)
        
        draw_hex_glow(surface, sx, sy, self.radius, glow_color)

        # Core hex
        if self._skin:
            pygame.draw.polygon(surface, self._skin.get("fill", (0, 200, 255)),
                               hex_vertices(sx, sy, self.radius - 2))
            pygame.draw.polygon(surface, self._skin.get("border", (0, 150, 200)),
                               hex_vertices(sx, sy, self.radius - 2), 3)
        else:
            pygame.draw.polygon(surface, (0, 200, 255),
                               hex_vertices(sx, sy, self.radius - 2))
            pygame.draw.polygon(surface, (0, 150, 200),
                               hex_vertices(sx, sy, self.radius - 2), 3)

        # Damage flash on hit
        if self._invuln_flash > 0:
            flash_surf = pygame.Surface((self.radius * 2, self.radius * 2),
                                       pygame.SRCALPHA)
            alpha = int(255 * (self._invuln_flash / 0.15))
            pygame.draw.polygon(flash_surf, (255, 100, 100, alpha),
                               hex_vertices(self.radius, self.radius, self.radius - 2))
            surface.blit(flash_surf, (sx - self.radius, sy - self.radius))

        # Honeycomb cells
        self._draw_honeycomb_cells(surface, camera)

    def _draw_honeycomb_cells(self, surface: pygame.Surface, camera):
        """Draw all honeycomb cells around the player."""
        from hex_renderer import hex_vertices
        from constants import CELL_COLORS, CELL_ICONS
        from asset_manager import assets

        for (q, r), cell_type in self.honeycomb_body.items():
            if cell_type == CellType.EMPTY:
                continue

            # World position of this cell
            cell_x = self.x + q * CELL_OFFSET
            cell_y = self.y + r * CELL_OFFSET

            if not camera.is_visible(cell_x, cell_y, margin=100):
                continue

            sx, sy = camera.world_to_screen(cell_x, cell_y)
            sx, sy = int(sx), int(sy)

            # Cell hex
            col = CELL_COLORS.get(cell_type, (120, 120, 120))
            ring = tuple(min(255, c + 80) for c in col)
            
            pygame.draw.polygon(surface, col, hex_vertices(sx, sy, HEX_RADIUS))
            pygame.draw.polygon(surface, ring, hex_vertices(sx, sy, HEX_RADIUS), 2)

            # Icon
            icon = CELL_ICONS.get(cell_type, "")
            if icon:
                font = assets.get_font("default", 20)
                icon_surf = font.render(icon, True, (255, 255, 255))
                surface.blit(icon_surf, (sx - icon_surf.get_width() // 2,
                                        sy - icon_surf.get_height() // 2))

    def draw_hp_bar(self, surface: pygame.Surface):
        """Draw HP bar in top-left."""
        from ui import draw_bar
        from constants import SCREEN_WIDTH, SCREEN_HEIGHT

        bar_x, bar_y = 20, 20
        bar_w, bar_h = 240, 24
        
        draw_bar(surface, bar_x, bar_y, bar_w, bar_h, self.hp, self.max_hp,
                fill_color=(100, 255, 100) if self.hp > self.max_hp * 0.5 else (255, 200, 50) if self.hp > self.max_hp * 0.25 else (255, 80, 80))

        # Label
        font = pygame.font.SysFont("Arial", 16, bold=True)
        label = font.render(f"HP: {int(self.hp)}/{int(self.max_hp)}", True, (255, 255, 255))
        surface.blit(label, (bar_x + 8, bar_y + 4))

    def draw_xp_bar(self, surface: pygame.Surface):
        """Draw XP bar in top-right."""
        from ui import draw_bar
        from constants import SCREEN_WIDTH

        bar_x = SCREEN_WIDTH - 260
        bar_y = 20
        bar_w = 240
        bar_h = 24
        
        xp_pct = self.level_system.get_xp_percent()
        draw_bar(surface, bar_x, bar_y, bar_w, bar_h, xp_pct, 1.0,
                fill_color=(150, 150, 255))

        # Label
        font = pygame.font.SysFont("Arial", 16, bold=True)
        label = font.render(f"Lv{self.level_system.level}  XP: {int(self.level_system.current_xp)}/{int(self.level_system.xp_needed)}", True, (255, 255, 255))
        surface.blit(label, (bar_x + 8, bar_y + 4))

    def draw_cell_legend(self, surface: pygame.Surface):
        """Draw active synergies and cell info on screen."""
        from constants import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_TEXT_DIM
        from asset_manager import assets

        synergy_displays = get_synergy_display(self.active_synergies)
        
        if not synergy_displays:
            return

        font = assets.get_font("default", 12)
        x = 20
        y = SCREEN_HEIGHT - 120

        # Title
        title = font.render("Active Synergies:", True, (100, 200, 255))
        surface.blit(title, (x, y))
        y += 20

        for synergy_text in synergy_displays[:5]:  # Show max 5
            text_surf = font.render(synergy_text, True, COLOR_TEXT_DIM)
            surface.blit(text_surf, (x + 8, y))
            y += 16
