"""
build_scene.py — Honeycomb build/edit scene.
"""

import math
import random
import pygame
from scene_manager import BaseScene
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, HEX_RADIUS,
    COLOR_BG, COLOR_ACCENT, COLOR_TEXT_DIM,
    CellType, CELL_COLORS, CELL_ICONS,
    SCENE_MAIN_MENU, HEX_SKINS,
)
from ui import Button, generate_stars, draw_starfield, render_text_centered
from hex_renderer import hex_vertices
from asset_manager import assets
from data.progress import (
    get_selected_skin, get_honeycomb_body, save_honeycomb_body,
    get_inventory, save_inventory,
)

HEX_COL = HEX_RADIUS * math.sqrt(3)
HEX_ROW = HEX_RADIUS * 1.5
CYCLE = [CellType.HEART, CellType.MOVE, CellType.DAMAGE, CellType.SHIELD]


def neighbors(q: int, r: int):
    return [(q + 1, r), (q - 1, r), (q, r + 1), (q, r - 1), (q + 1, r - 1), (q - 1, r + 1)]


def axial_to_pixel(q: int, r: int):
    x = HEX_COL * (q + r / 2)
    y = HEX_ROW * r
    return x, y


class BuildScene(BaseScene):
    def __init__(self):
        super().__init__()
        self.stars = generate_stars(200)
        self.t = 0.0
        self.wave_num = 1
        self._score = 0
        self._kills = 0
        self._level = 1
        self._current_xp = 0
        self._xp_needed = 100
        self._player_hp = None
        self.new_cells = []
        self.body = {}
        self.inventory = {}
        self.hover = None
        self.pan_x = SCREEN_WIDTH // 2
        self.pan_y = SCREEN_HEIGHT // 2 + 20
        self._drag = None
        self._skin = HEX_SKINS[0]
        self.btn_launch = Button(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT - 70, 220, 48, "▶  LAUNCH WAVE", color=COLOR_ACCENT, font_size=22)
        self.btn_back = Button(30, 30, 120, 40, "← MENU", color=(100, 120, 160), font_size=18)

    def on_enter(self, wave_num: int = 1, new_cells: list = None, **kwargs):
        from input_handler import input_handler
        input_handler.reset()
        self.wave_num = wave_num
        self.new_cells = new_cells or []
        self._score = kwargs.get("score", 0)
        self._kills = kwargs.get("kills", 0)
        self._level = kwargs.get("level", 1)
        self._current_xp = kwargs.get("current_xp", 0)
        self._xp_needed = kwargs.get("xp_needed", 100)
        self._player_hp = kwargs.get("player_hp", None)
        self.t = 0.0
        self._drag = None
        self.hover = None
        self.body = {}
        for item in get_honeycomb_body():
            self.body[(item["q"], item["r"])] = item["type"]
        self.inventory = get_inventory()
        if self.wave_num == 1 and self._score == 0 and self._kills == 0:
            self.inventory = self._roll_starting_inventory()
            save_inventory(self.inventory)
            self.body = {}
        if self.new_cells:
            for ct in self.new_cells:
                self.inventory[ct] = self.inventory.get(ct, 0) + 1
            save_inventory(self.inventory)
        self._sync_inventory_floor()
        skin_id = get_selected_skin()
        self._skin = next((s for s in HEX_SKINS if s["id"] == skin_id), HEX_SKINS[0])

    def update(self, events: list, dt: float):
        from input_handler import input_handler
        input_handler.update(events, dt)
        self.t += dt
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._save_and_go(SCENE_MAIN_MENU)
                elif event.key == pygame.K_RETURN:
                    self._save_and_launch()
            elif event.type == pygame.MOUSEMOTION:
                if self._drag is not None and pygame.mouse.get_pressed()[1]:
                    self.pan_x += event.pos[0] - self._drag[0]
                    self.pan_y += event.pos[1] - self._drag[1]
                    self._drag = event.pos
                self.hover = self._find_coord(*event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 2:
                    self._drag = event.pos
                elif event.button == 1:
                    self._on_left_click(event.pos)
                elif event.button == 3:
                    self._on_right_click(event.pos)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 2:
                self._drag = None

        if self.btn_launch.update(input_handler, dt):
            self._save_and_launch()
        if self.btn_back.update(input_handler, dt):
            self._save_and_go(SCENE_MAIN_MENU)

    def _find_coord(self, mx, my):
        best_d = HEX_RADIUS * 0.95
        best = None
        check = set(self.body.keys()) | self.border_slots()
        for q, r in check:
            ox, oy = axial_to_pixel(q, r)
            sx, sy = ox + self.pan_x, oy + self.pan_y
            d = math.hypot(mx - sx, my - sy)
            if d < best_d:
                best_d, best = d, (q, r)
        return best

    def border_slots(self):
        slots = set()
        for q, r in self.body.keys():
            for nq, nr in neighbors(q, r):
                if (nq, nr) not in self.body:
                    slots.add((nq, nr))
        if not self.body:
            slots.update(neighbors(0, 0))
        return slots

    def _on_left_click(self, pos):
        coord = self._find_coord(*pos)
        if coord is None:
            return
        if coord in self.body:
            self._cycle_existing_cell(coord)
        else:
            placed = self._pick_placeable_type()
            if placed is not None:
                self.body[coord] = placed

    def _on_right_click(self, pos):
        coord = self._find_coord(*pos)
        if coord is None or coord not in self.body:
            return
        if self._connected_without(coord):
            del self.body[coord]

    def _connected_without(self, remove_coord):
        remaining = set(self.body.keys()) - {remove_coord}
        if not remaining:
            return True
        start = next(iter(remaining))
        visited = set()
        stack = [start]
        while stack:
            cur = stack.pop()
            if cur in visited:
                continue
            visited.add(cur)
            for nxt in neighbors(*cur):
                if nxt in remaining and nxt not in visited:
                    stack.append(nxt)
        return len(visited) == len(remaining)

    def _save_and_launch(self):
        self._sync_inventory_floor()
        save_inventory(self.inventory)
        packed = [{"q": q, "r": r, "type": ct} for (q, r), ct in self.body.items()]
        save_honeycomb_body(packed)
        self.manager.switch(
            "game",
            wave_num=self.wave_num,
            body_layout=packed,
            score=self._score,
            kills=self._kills,
            level=self._level,
            current_xp=self._current_xp,
            xp_needed=self._xp_needed,
            player_hp=self._player_hp,
        )

    def _save_and_go(self, scene_name):
        self._sync_inventory_floor()
        save_inventory(self.inventory)
        packed = [{"q": q, "r": r, "type": ct} for (q, r), ct in self.body.items()]
        save_honeycomb_body(packed)
        self.manager.switch(scene_name)

    def draw(self, surface: pygame.Surface):
        surface.fill(COLOR_BG)
        draw_starfield(surface, self.t, 0, self.stars)
        title = "BUILD YOUR HEX" if self.wave_num == 1 else f"WAVE {self.wave_num} - REINFORCE"
        render_text_centered(surface, title, 44, COLOR_ACCENT, 44)
        self._draw_grid(surface)
        self._draw_cells(surface)
        self._draw_core(surface)
        self._draw_ui(surface)
        self.btn_launch.draw(surface)
        self.btn_back.draw(surface)

    def _draw_grid(self, surface):
        cols = int(SCREEN_WIDTH / HEX_COL) + 8
        rows = int(SCREEN_HEIGHT / HEX_ROW) + 8
        q0 = int(-self.pan_x / HEX_COL) - 4
        r0 = int(-self.pan_y / HEX_ROW) - 4
        for r in range(r0, r0 + rows):
            for q in range(q0, q0 + cols):
                ox, oy = axial_to_pixel(q, r)
                sx, sy = int(ox + self.pan_x), int(oy + self.pan_y)
                if -HEX_RADIUS < sx < SCREEN_WIDTH + HEX_RADIUS and -HEX_RADIUS < sy < SCREEN_HEIGHT + HEX_RADIUS:
                    pygame.draw.polygon(surface, (30, 35, 52), hex_vertices(sx, sy, HEX_RADIUS - 1), 1)

    def _draw_cells(self, surface):
        for q, r in self.border_slots():
            ox, oy = axial_to_pixel(q, r)
            sx, sy = int(ox + self.pan_x), int(oy + self.pan_y)
            if not (-HEX_RADIUS < sx < SCREEN_WIDTH + HEX_RADIUS and -HEX_RADIUS < sy < SCREEN_HEIGHT + HEX_RADIUS):
                continue
            col = (65, 75, 110) if self.hover == (q, r) else (40, 45, 65)
            pygame.draw.polygon(surface, col, hex_vertices(sx, sy, HEX_RADIUS - 1))
            pygame.draw.polygon(surface, (90, 95, 130), hex_vertices(sx, sy, HEX_RADIUS - 1), 1)
        for (q, r), ct in self.body.items():
            ox, oy = axial_to_pixel(q, r)
            sx, sy = int(ox + self.pan_x), int(oy + self.pan_y)
            col = CELL_COLORS.get(ct, (120, 120, 120))
            ring = (255, 255, 255) if self.hover == (q, r) else tuple(min(255, c + 60) for c in col)
            pygame.draw.polygon(surface, col, hex_vertices(sx, sy, HEX_RADIUS))
            pygame.draw.polygon(surface, ring, hex_vertices(sx, sy, HEX_RADIUS), 2)
            icon = CELL_ICONS.get(ct, "")
            if icon:
                t = assets.get_font("default", 18).render(icon, True, (255, 255, 255))
                surface.blit(t, (sx - t.get_width() // 2, sy - t.get_height() // 2))

    def _draw_core(self, surface):
        sx, sy = int(self.pan_x), int(self.pan_y)
        pts = hex_vertices(sx, sy, HEX_RADIUS - 4)
        pygame.draw.polygon(surface, self._skin.get("fill", COLOR_ACCENT), pts)
        pygame.draw.polygon(surface, self._skin.get("border", COLOR_ACCENT), pts, 3)

    def _draw_ui(self, surface):
        font = assets.get_font("default", 14)
        lines = [
            "Left-click cell: cycle type (inventory-limited)",
            "Left-click border: add next available cell",
            "Right-click cell: remove",
            "Middle-drag: pan",
            "ENTER / LAUNCH: start wave",
        ]
        y = SCREEN_HEIGHT - 115
        for line in lines:
            t = font.render(line, True, COLOR_TEXT_DIM)
            surface.blit(t, (SCREEN_WIDTH // 2 - t.get_width() // 2, y))
            y += 18
        self._draw_inventory(surface)

    def _draw_inventory(self, surface):
        font = assets.get_font("default", 15)
        counts = self._body_counts()
        x = 22
        y = 95
        total_used = 0
        total_owned = 0
        for ct in CYCLE:
            owned = self.inventory.get(ct, 0)
            used = counts.get(ct, 0)
            total_used += used
            total_owned += owned
            icon = CELL_ICONS.get(ct, "?")
            col = CELL_COLORS.get(ct, (200, 200, 200))
            txt = font.render(f"{icon} {used}/{owned}", True, col)
            surface.blit(txt, (x, y))
            y += 22
        cap = font.render(f"Blocks placed: {total_used}/{total_owned}", True, COLOR_TEXT_DIM)
        surface.blit(cap, (x, y + 6))

    def _body_counts(self):
        counts = {}
        for ct in self.body.values():
            counts[ct] = counts.get(ct, 0) + 1
        return counts

    def _available(self, ct: CellType) -> int:
        return self.inventory.get(ct, 0) - self._body_counts().get(ct, 0)

    def _pick_placeable_type(self):
        for ct in CYCLE:
            if self._available(ct) > 0:
                return ct
        return None

    def _cycle_existing_cell(self, coord):
        cur = self.body[coord]
        if cur not in CYCLE:
            return
        idx = CYCLE.index(cur)
        for step in range(1, len(CYCLE) + 1):
            nxt = CYCLE[(idx + step) % len(CYCLE)]
            if nxt == cur:
                self.body[coord] = cur
                return
            if self._available(nxt) > 0:
                self.body[coord] = nxt
                return

    def _sync_inventory_floor(self):
        counts = self._body_counts()
        for ct, used in counts.items():
            self.inventory[ct] = max(self.inventory.get(ct, 0), used)

    def _roll_starting_inventory(self):
        return {
            CellType.HEART: random.randint(1, 3),
            CellType.MOVE: random.randint(1, 3),
            CellType.DAMAGE: random.randint(1, 2),
            CellType.SHIELD: random.randint(0, 2),
        }
