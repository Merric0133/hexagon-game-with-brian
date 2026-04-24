"""
player.py — Player-controlled hex core with honeycomb body cells.
"""

import math
from dataclasses import dataclass
import pygame
from camera import camera
from constants import (
    PLAYER_BASE_SPEED, PLAYER_BASE_HP, PLAYER_BASE_REGEN,
    HEX_RADIUS, HEX_SKINS,
    WORLD_WIDTH, WORLD_HEIGHT,
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_ACCENT,
    CellType, CELL_COLORS, CELL_ICONS, CELL_STAT_BONUS, get_cell_type_def,
)
from hex_renderer import hex_vertices
from asset_manager import assets
from experience import LevelUp

HEX_COL = HEX_RADIUS * math.sqrt(3)
HEX_ROW = HEX_RADIUS * 1.5
SPRING_K = 800.0
SPRING_DAMP = 13.0
CELL_DRIFT_FORCE = 120.0
CELL_TETHER_FORCE = 950.0
CELL_MAX_STRETCH = 52.0
BODY_ROTATE_SPEED = 9.0


def axial_neighbors(q: int, r: int):
    return [(q + 1, r), (q - 1, r), (q, r + 1), (q, r - 1), (q + 1, r - 1), (q - 1, r + 1)]


def axial_to_pixel(q: int, r: int):
    x = HEX_COL * (q + r / 2)
    y = HEX_ROW * r
    return x, y


@dataclass
class BodyCell:
    q: int
    r: int
    cell_type: CellType
    flash_timer: float = 0.0
    px: float = 0.0
    py: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    disabled_timer: float = 0.0
    break_hp: int = 1

    def rest_offset(self, body_rotation: float = 0.0):
        ox, oy = axial_to_pixel(self.q, self.r)
        if body_rotation == 0.0:
            return ox, oy
        c = math.cos(body_rotation)
        s = math.sin(body_rotation)
        return ox * c - oy * s, ox * s + oy * c

    def snap(self, core_x: float, core_y: float, body_rotation: float = 0.0):
        ox, oy = self.rest_offset(body_rotation)
        self.px = core_x + ox
        self.py = core_y + oy
        self.vx = 0.0
        self.vy = 0.0

    def update_physics(self, dt: float, core_x: float, core_y: float, body_rotation: float):
        self.disabled_timer = max(0.0, self.disabled_timer - dt)
        ox, oy = self.rest_offset(body_rotation)
        rx, ry = core_x + ox, core_y + oy
        fx = SPRING_K * (rx - self.px) - SPRING_DAMP * self.vx
        fy = SPRING_K * (ry - self.py) - SPRING_DAMP * self.vy
        # Each cell has slight independent drift to avoid rigid movement.
        drift_phase = pygame.time.get_ticks() * 0.002 + (self.q * 1.7 + self.r * 2.3)
        fx += math.cos(drift_phase) * CELL_DRIFT_FORCE
        fy += math.sin(drift_phase * 1.1) * CELL_DRIFT_FORCE
        # Hard tether prevents any body hex from fully separating.
        dx = self.px - rx
        dy = self.py - ry
        dist = math.hypot(dx, dy)
        if dist > CELL_MAX_STRETCH:
            over = dist - CELL_MAX_STRETCH
            fx += (-dx / dist) * (CELL_TETHER_FORCE * over)
            fy += (-dy / dist) * (CELL_TETHER_FORCE * over)
        self.vx += fx * dt
        self.vy += fy * dt
        self.px += self.vx * dt
        self.py += self.vy * dt
        self.flash_timer = max(0.0, self.flash_timer - dt)

    @property
    def active(self) -> bool:
        return self.disabled_timer <= 0


class Player:
    """
    The player entity.

    HP is derived from equipped Heart cells (PLAYER_BASE_HP + 20 per heart).
    Speed is boosted by Move cells.
    Defense is boosted by Shield cells.
    Damage cells create a contact-damage aura around those hex slots.
    """

    INVINCIBILITY_DURATION = 0.6
    CONTACT_DMG_RATE = 0.12
    CELL_COLLISION_TOLERANCE = 8.0
    CELL_BREAK_DURATION = 2.8
    HEART_DIRECT_DAMAGE_MULT = 1.8
    BODY_DAMAGE_MULT = 0.65
    JELLY_IMPULSE = 170.0

    def __init__(self, body_layout: list[dict]):
        self.x: float = WORLD_WIDTH  / 2
        self.y: float = WORLD_HEIGHT / 2
        self.cells: dict[tuple[int, int], BodyCell] = {}
        for item in body_layout:
            q = int(item["q"])
            r = int(item["r"])
            ct = item["type"]
            if ct != CellType.EMPTY:
                cell_def = get_cell_type_def(ct)
                self.cells[(q, r)] = BodyCell(
                    q=q,
                    r=r,
                    cell_type=ct,
                    break_hp=max(1, int(cell_def.get("break_hp", 1))),
                )

        # Skin
        self.skin: dict = HEX_SKINS[0]
        self.rotation: float = 0.0
        self.pulse_t: float  = 0.0

        # Invincibility / flash
        self.invincible: float    = 0.0
        self._flash_timer: float  = 0.0

        self._contact_cooldowns: dict[tuple[int, int], float] = {}

        # Temporary speed bonus from power-ups
        self._temp_speed_bonus: float = 0.0
        self._temp_speed_timer: float = 0.0

        # Leveling (XP-based, for ability unlocks if desired)
        self.level_system = LevelUp()

        self._snap_all()
        self._recalculate_stats()

    # ── Stat derivation ───────────────────────────────────────────────────────

    def _recalculate_stats(self):
        """Re-derive every stat from the currently equipped cells."""
        self.max_hp    = PLAYER_BASE_HP
        self.speed     = PLAYER_BASE_SPEED
        self.defense   = 0.0
        self.regen     = PLAYER_BASE_REGEN
        self.contact_dmg = 0.0

        for cell in self.cells.values():
            if not cell.active:
                continue
            bonus = CELL_STAT_BONUS.get(cell.cell_type)
            if bonus:
                self.max_hp     += bonus.get("max_hp",       0)
                self.speed      += bonus.get("speed",        0)
                self.defense    += bonus.get("defense",      0)
                self.contact_dmg+= bonus.get("contact_dmg",  0)

        # Clamp HP to new max
        if not hasattr(self, "hp"):
            self.hp = self.max_hp
        else:
            self.hp = min(self.hp, self.max_hp)

    def set_cells(self, body_layout: list[dict]):
        self.cells = {}
        for item in body_layout:
            q = int(item["q"])
            r = int(item["r"])
            ct = item["type"]
            if ct != CellType.EMPTY:
                cell_def = get_cell_type_def(ct)
                self.cells[(q, r)] = BodyCell(
                    q=q,
                    r=r,
                    cell_type=ct,
                    break_hp=max(1, int(cell_def.get("break_hp", 1))),
                )
        self._snap_all()
        self._recalculate_stats()
        self.hp = self.max_hp

    def set_skin(self, skin_data: dict):
        self.skin = skin_data

    # ── Frame update ─────────────────────────────────────────────────────────

    def update(self, input_handler, dt: float):
        dx, dy = input_handler.get_movement_vector()
        effective_speed = self.speed + self._temp_speed_bonus
        if dx != 0 or dy != 0:
            dist = math.hypot(dx, dy)
            self.x += (dx / dist) * effective_speed * dt
            self.y += (dy / dist) * effective_speed * dt

        # Tick down temp speed bonus
        if self._temp_speed_timer > 0:
            self._temp_speed_timer -= dt
            if self._temp_speed_timer <= 0:
                self._temp_speed_bonus = 0.0
                self._temp_speed_timer = 0.0

        self.x = max(0, min(WORLD_WIDTH,  self.x))
        self.y = max(0, min(WORLD_HEIGHT, self.y))

        # Invincibility frames
        if self.invincible > 0:
            self.invincible   -= dt
            self._flash_timer -= dt

        # Rotation + pulse
        mx, my = input_handler.mouse_pos
        aim_x = camera.x + mx
        aim_y = camera.y + my
        target_rot = math.atan2(aim_y - self.y, aim_x - self.x)
        diff = (target_rot - self.rotation + math.pi) % (2 * math.pi) - math.pi
        self.rotation += diff * min(1.0, BODY_ROTATE_SPEED * dt)
        self.pulse_t  += dt

        for key in list(self._contact_cooldowns.keys()):
            self._contact_cooldowns[key] = max(0.0, self._contact_cooldowns[key] - dt)

        needs_recalc = False
        for cell in self.cells.values():
            was_disabled = cell.disabled_timer > 0
            cell.update_physics(dt, self.x, self.y, self.rotation)
            if was_disabled and cell.active:
                cell.break_hp = max(1, int(get_cell_type_def(cell.cell_type).get("break_hp", 1)))
                needs_recalc = True
        if needs_recalc:
            self._recalculate_stats()

    # ── Damage / heal ─────────────────────────────────────────────────────────

    def take_damage(self, amount: float):
        if self.invincible > 0:
            return
        actual = max(1.0, amount - self.defense)
        self.hp       -= actual
        self.invincible = self.INVINCIBILITY_DURATION
        self._flash_timer = 0.15

    def heal(self, amount: float):
        self.hp = min(self.max_hp, self.hp + amount)

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    # ── Contact damage helpers ────────────────────────────────────────────────

    def get_damage_cell_positions(self):
        return [
            ((cell.q, cell.r), (cell.px, cell.py))
            for cell in self.cells.values()
            if cell.cell_type == CellType.DAMAGE and cell.active
        ]

    def try_contact_damage(self, cell_key: tuple[int, int]) -> bool:
        if self._contact_cooldowns.get(cell_key, 0.0) <= 0:
            self._contact_cooldowns[cell_key] = self.CONTACT_DMG_RATE
            return True
        return False

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface, camera):
        if not camera.is_visible(self.x, self.y, margin=150):
            return

        sx, sy = camera.world_to_screen(self.x, self.y)
        self._draw_cells(surface, camera)
        self._draw_core(surface, sx, sy)

    def _draw_cells(self, surface, camera):
        font_icon = assets.get_font("default", 18)

        for cell in self.cells.values():
            if not cell.active:
                continue
            cx, cy = camera.world_to_screen(cell.px, cell.py)
            cx, cy = int(cx), int(cy)

            if cell.flash_timer > 0:
                col = (255, 60, 60)
            else:
                col = CELL_COLORS.get(cell.cell_type, CELL_COLORS[CellType.EMPTY])

            shadow_surf = pygame.Surface((HEX_RADIUS * 2 + 8, HEX_RADIUS * 2 + 8), pygame.SRCALPHA)
            pts = hex_vertices(HEX_RADIUS + 4, HEX_RADIUS + 4, HEX_RADIUS)
            pygame.draw.polygon(shadow_surf, (0, 0, 0, 70), pts)
            surface.blit(shadow_surf, (cx - HEX_RADIUS - 1, cy - HEX_RADIUS - 1))

            pts = hex_vertices(cx, cy, HEX_RADIUS, self.rotation)
            pygame.draw.polygon(surface, col, pts)

            if cell.cell_type != CellType.EMPTY:
                ring_col = tuple(min(255, c + 50) for c in col)
            else:
                ring_col = (70, 75, 100)
            pygame.draw.polygon(surface, ring_col, pts, 2)

            icon = CELL_ICONS.get(cell.cell_type, "")
            if icon:
                t = font_icon.render(icon, True, (255, 255, 255))
                surface.blit(t, (cx - t.get_width() // 2, cy - t.get_height() // 2))

    def _draw_core(self, surface, sx, sy):
        """Draw the central player hex (core)."""
        flash = self.invincible > 0 and int(self._flash_timer * 10) % 2 == 0
        skin = self.skin

        # Core hex
        pts = hex_vertices(sx, sy, HEX_RADIUS - 4, self.rotation)
        fill_col = (255, 60, 60) if flash else skin.get("fill", COLOR_ACCENT)
        pygame.draw.polygon(surface, fill_col, pts)
        pygame.draw.polygon(surface, skin.get("border", COLOR_ACCENT), pts, 3)

    # ── HUD drawing ───────────────────────────────────────────────────────────

    def draw_hp_bar(self, surface: pygame.Surface, camera=None):
        from ui import draw_bar
        bar_w = 300
        bar_x = SCREEN_WIDTH  // 2 - bar_w // 2
        bar_y = 20
        draw_bar(surface, bar_x, bar_y, bar_w, 20, self.hp, self.max_hp,
                 fill_color=(50, 255, 100))
        font = assets.get_font("default", 14)
        label = font.render(f"HP  {int(self.hp)} / {int(self.max_hp)}", True, (255, 255, 255))
        surface.blit(label, (bar_x + 10, bar_y + 2))

    def draw_xp_bar(self, surface: pygame.Surface):
        from ui import draw_bar
        bar_w = 300
        bar_x = SCREEN_WIDTH  // 2 - bar_w // 2
        bar_y = 50
        xp_pct = self.level_system.get_xp_percent()
        draw_bar(surface, bar_x, bar_y, bar_w, 12, xp_pct, 1.0,
                 fill_color=(100, 150, 255))
        font = assets.get_font("default", 11)
        label = font.render(
            f"LVL {self.level_system.level}   XP {self.level_system.current_xp}/{self.level_system.xp_needed}",
            True, (180, 180, 255))
        surface.blit(label, (bar_x + 10, bar_y))

    def draw_cell_legend(self, surface: pygame.Surface):
        font = assets.get_font("default", 13)
        counts = {}
        for cell in self.cells.values():
            if cell.cell_type != CellType.EMPTY:
                counts[cell.cell_type] = counts.get(cell.cell_type, 0) + 1

        x, y = 16, SCREEN_HEIGHT - 18 - len(counts) * 20
        for ct, n in counts.items():
            col  = CELL_COLORS[ct]
            icon = CELL_ICONS[ct]
            txt  = font.render(f"{icon} x{n}", True, col)
            surface.blit(txt, (x, y))
            y += 20

    # ── Collision helpers ─────────────────────────────────────────────────────

    def collides_with(self, wx: float, wy: float, radius: float) -> bool:
        return math.hypot(self.x - wx, self.y - wy) <= (HEX_RADIUS + radius)

    def _snap_all(self):
        for cell in self.cells.values():
            cell.snap(self.x, self.y, self.rotation)

    # ── Collision + jelly helpers ─────────────────────────────────────────────

    def _colliding_cell(self, wx: float, wy: float, radius: float):
        best_key = None
        best_dist = 1e9
        threshold = HEX_RADIUS + radius - self.CELL_COLLISION_TOLERANCE
        for key, cell in self.cells.items():
            if not cell.active:
                continue
            d = math.hypot(cell.px - wx, cell.py - wy)
            if d <= threshold and d < best_dist:
                best_key = key
                best_dist = d
        return best_key

    def apply_enemy_collision(self, enemy, scaled_damage: float):
        """
        Returns one of: "cell", "heart", "core", None.
        """
        hit_cell = self._colliding_cell(enemy.x, enemy.y, enemy.radius)
        if hit_cell is not None:
            cell = self.cells[hit_cell]
            self._resolve_enemy_overlap(enemy, cell.px, cell.py)
            self._apply_jelly_impulse(cell, enemy.x, enemy.y, scaled_damage)
            cell.flash_timer = 0.12
            
            # Apply break damage if the cell is breakable
            can_break = get_cell_type_def(cell.cell_type).get("can_break", False)
            broke = False
            if can_break:
                broke = self._apply_break_damage(cell)
                if broke:
                    self._recalculate_stats()
            
            # Apply direct damage based on cell type
            if cell.cell_type == CellType.HEART:
                self.take_damage(scaled_damage * self.HEART_DIRECT_DAMAGE_MULT)
                return "heart"
            else:
                self.take_damage(scaled_damage * self.BODY_DAMAGE_MULT)
                return "cell"

        if self.collides_with(enemy.x, enemy.y, enemy.radius):
            self._resolve_enemy_overlap(enemy, self.x, self.y)
            self.take_damage(scaled_damage)
            return "core"
        return None

    def _apply_jelly_impulse(self, cell: BodyCell, ex: float, ey: float, dmg: float):
        dx = cell.px - ex
        dy = cell.py - ey
        dist = math.hypot(dx, dy)
        if dist <= 0:
            return
        impulse = self.JELLY_IMPULSE + min(140.0, dmg * 10.0)
        cell.vx += (dx / dist) * impulse
        cell.vy += (dy / dist) * impulse

    def _resolve_enemy_overlap(self, enemy, center_x: float, center_y: float):
        dx = enemy.x - center_x
        dy = enemy.y - center_y
        dist = math.hypot(dx, dy)
        min_dist = enemy.radius + HEX_RADIUS - self.CELL_COLLISION_TOLERANCE
        if dist <= 0:
            dx, dy, dist = 1.0, 0.0, 1.0
        if dist < min_dist:
            push = min_dist - dist
            enemy.x += (dx / dist) * push
            enemy.y += (dy / dist) * push

    def _apply_break_damage(self, cell: BodyCell) -> bool:
        """
        Returns True when a cell actually gets disabled this hit.
        """
        cell.break_hp -= 1
        if cell.break_hp > 0:
            return False
        cell_def = get_cell_type_def(cell.cell_type)
        cell.disabled_timer = float(cell_def.get("respawn_time", self.CELL_BREAK_DURATION))
        cell.break_hp = max(1, int(cell_def.get("break_hp", 1)))
        # If a heart breaks, lose a bunch of HP
        if cell.cell_type == CellType.HEART:
            self.take_damage(60.0)  # Lose 60 HP when a heart breaks
        return True
