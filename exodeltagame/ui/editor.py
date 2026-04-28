import pygame
import math
from core.utils import draw_hex, draw_glow_circle, draw_glow_rect, pulse_value
from core.constants import *
from data.cells_data import CELLS, validate_layout, get_genome_cap, get_biomass_cap

HEX_R = 26
HEX_SPACING = HEX_R * 1.85
GRID_COLS = range(-5, 6)
GRID_ROWS = range(-4, 5)

def hex_center(col, row, origin):
    x = HEX_SPACING * math.sqrt(3) * (col + 0.5 * (row % 2))
    y = HEX_SPACING * 1.5 * row
    return (origin[0] + x, origin[1] + y)

def pixel_to_hex(px, py, origin):
    """Approximate pixel to hex grid coord."""
    # This function needs to be updated to work with zoom, but we'll keep it simple
    # by checking against all possible hex positions
    best = None
    best_dist = float("inf")
    for row in GRID_ROWS:
        for col in GRID_COLS:
            cx, cy = hex_center(col, row, origin)
            d = math.hypot(px - cx, py - cy)
            if d < best_dist:
                best_dist = d
                best = (col, row)
    if best_dist < HEX_R * 1.5:  # Increased tolerance for zoom
        return best
    return None

class CellEditor:
    def __init__(self, sw, sh, strain_data):
        self.sw, self.sh = sw, sh
        self.strain_data = strain_data
        self.font_title = pygame.font.SysFont("consolas", 24, bold=True)
        self.font_med   = pygame.font.SysFont("consolas", 15)
        self.font_small = pygame.font.SysFont("consolas", 12)

        # Grid origin (center of editor area)
        self.grid_origin = (sw // 2 - 60, sh // 2)
        self.grid_offset = [0, 0]  # Pan offset
        self.zoom = 1.0  # Zoom level
        self.dragging = False
        self.drag_start = None

        # Load existing layout
        raw = strain_data.get("cell_layout", {})
        self.layout = {}
        if isinstance(raw, dict):
            for k, v in raw.items():
                if isinstance(k, str) and "," in k:
                    col, row = map(int, k.split(","))
                    self.layout[(col, row)] = v
                elif isinstance(k, tuple):
                    self.layout[k] = v
        if not self.layout:
            # Default
            self.layout = {(0,0): "heart", (-1,0): "basic", (1,0): "basic", (0,-1): "basic"}

        # Unlocked cells
        self.unlocked = strain_data.get("unlocked_cells", ["basic","heart","seeker","spike"])
        self.selected_cell = self.unlocked[0] if self.unlocked else "basic"

        # Palette panel
        self.palette_x = sw - 220
        self.palette_y = 80
        self.palette_rects = {}

        # Buttons
        from ui.menus import Button
        self.back_btn = Button((30, sh-60, 120, 40), "BACK", NEON_ORANGE)
        self.play_btn = Button((sw-180, sh-60, 140, 40), "PLAY", NEON_GREEN)
        self.clear_btn= Button((sw//2-60, sh-60, 120, 40), "CLEAR", NEON_PINK)
        self.undo_btn = Button((sw//2-200, sh-60, 120, 40), "UNDO", (180, 140, 255))

        self.hover_hex = None
        self.tooltip_cell = None
        self.validation_errors = []
        self.error_flash = 0.0
        self.level = strain_data.get("level", 1)
        
        # Undo history
        self.history = [dict(self.layout)]  # Start with initial state
        self.history_index = 0

    def handle_event(self, event):
        from ui.menus import Button
        if self.back_btn.handle_event(event):
            return "back"
        if self.play_btn.handle_event(event):
            valid, errors = validate_layout(self.layout, self.level)
            if valid:
                return "play"
            else:
                self.validation_errors = errors
                self.error_flash = 3.0
                return None
        if self.clear_btn.handle_event(event):
            self._save_to_history()
            self.layout = {(0,0): "heart"}
            return None
        if self.undo_btn.handle_event(event):
            self._undo()
            return None

        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            
            # Handle dragging for pan
            if self.dragging and self.drag_start:
                dx = mx - self.drag_start[0]
                dy = my - self.drag_start[1]
                self.grid_offset[0] += dx
                self.grid_offset[1] += dy
                self.drag_start = (mx, my)
            
            self.hover_hex = pixel_to_hex(mx, my, self._get_grid_origin())
            # Palette hover
            self.tooltip_cell = None
            for ctype, rect in self.palette_rects.items():
                if rect.collidepoint(mx, my):
                    self.tooltip_cell = ctype

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            
            # Middle mouse button for panning
            if event.button == 2:  # Middle click
                self.dragging = True
                self.drag_start = (mx, my)
                return None
            
            # Palette click
            for ctype, rect in self.palette_rects.items():
                if rect.collidepoint(mx, my):
                    self.selected_cell = ctype
                    return None
            # Grid click
            coord = pixel_to_hex(mx, my, self._get_grid_origin())
            if coord:
                if event.button == 1:  # Left click = place
                    if coord == (0, 0) and self.selected_cell != "heart":
                        return None  # protect center heart
                    self._save_to_history()
                    self.layout[coord] = self.selected_cell
                elif event.button == 3:  # Right click = remove
                    if coord != (0, 0):
                        self._save_to_history()
                        self.layout.pop(coord, None)
        
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 2:  # Middle click release
                self.dragging = False
                self.drag_start = None
        
        # Mouse wheel for zoom
        if event.type == pygame.MOUSEWHEEL:
            old_zoom = self.zoom
            self.zoom += event.y * 0.1
            self.zoom = max(0.5, min(2.0, self.zoom))  # Clamp between 0.5x and 2.0x
            
            # Adjust offset to zoom toward mouse position
            mx, my = pygame.mouse.get_pos()
            origin = self._get_grid_origin()
            # Calculate relative position before zoom
            rel_x = (mx - origin[0]) / old_zoom
            rel_y = (my - origin[1]) / old_zoom
            # Calculate new position after zoom
            new_x = rel_x * self.zoom
            new_y = rel_y * self.zoom
            # Adjust offset
            self.grid_offset[0] += (mx - origin[0]) - new_x
            self.grid_offset[1] += (my - origin[1]) - new_y
            return None
        
        # Keyboard shortcuts
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL:
                self._undo()
        
        return None

    def _get_grid_origin(self):
        """Get current grid origin with zoom and pan applied."""
        return (
            self.grid_origin[0] + self.grid_offset[0],
            self.grid_origin[1] + self.grid_offset[1]
        )

    def _save_to_history(self):
        """Save current layout state to undo history."""
        # Remove any future states if we're not at the end
        self.history = self.history[:self.history_index + 1]
        # Add new state
        self.history.append(dict(self.layout))
        self.history_index += 1
        # Limit history to 50 states
        if len(self.history) > 50:
            self.history.pop(0)
            self.history_index -= 1

    def _undo(self):
        """Undo to previous layout state."""
        if self.history_index > 0:
            self.history_index -= 1
            self.layout = dict(self.history[self.history_index])

    def get_layout(self):
        return dict(self.layout)

    def draw(self, surface, game_time):
        surface.fill(DEEP_VOID)
        self._draw_grid(surface, game_time)
        self._draw_palette(surface, game_time)
        self._draw_tooltip(surface)
        self._draw_stats(surface, game_time)
        self._draw_validation_errors(surface, game_time)
        self.back_btn.draw(surface, game_time)
        self.play_btn.draw(surface, game_time)
        self.clear_btn.draw(surface, game_time)
        self.undo_btn.draw(surface, game_time)

        title = self.font_title.render("CELL EDITOR", True, NEON_CYAN)
        surface.blit(title, (self.sw//2 - title.get_width()//2, 16))
        hint = self.font_small.render(
            "LMB: place  |  RMB: remove  |  MMB: pan  |  Scroll: zoom  |  Ctrl+Z: undo", 
            True, (100,80,120))
        surface.blit(hint, (self.sw//2 - hint.get_width()//2, 48))
        
        # Zoom indicator
        zoom_txt = self.font_small.render(f"Zoom: {self.zoom:.1f}x", True, NEON_CYAN)
        surface.blit(zoom_txt, (self.sw - 240, 20))

    def _draw_grid(self, surface, game_time):
        origin = self._get_grid_origin()
        scaled_hex_r = int(HEX_R * self.zoom)
        scaled_spacing = HEX_SPACING * self.zoom
        
        for row in GRID_ROWS:
            for col in GRID_COLS:
                # Calculate position with zoom
                x = scaled_spacing * math.sqrt(3) * (col + 0.5 * (row % 2))
                y = scaled_spacing * 1.5 * row
                cx = origin[0] + x
                cy = origin[1] + y
                
                coord = (col, row)
                if coord in self.layout:
                    ctype = self.layout[coord]
                    cdata = CELLS.get(ctype, CELLS["basic"])
                    pulse = pulse_value(game_time + col*0.3 + row*0.2, speed=1.5, lo=0.85, hi=1.0)
                    r = int(scaled_hex_r * pulse)
                    draw_glow_circle(surface, cdata["glow"], (int(cx), int(cy)), r, alpha=50, layers=2)
                    draw_hex(surface, cdata["color"], (int(cx), int(cy)), r)
                    draw_hex(surface, cdata["glow"], (int(cx), int(cy)), r, width=1)
                    # Cell name (small)
                    if r > 14:
                        abbr = ctype[:3].upper()
                        t = self.font_small.render(abbr, True, WHITE)
                        surface.blit(t, (int(cx) - t.get_width()//2, int(cy) - t.get_height()//2))
                else:
                    # Empty hex outline
                    alpha = 30 if coord != self.hover_hex else 80
                    s = pygame.Surface((scaled_hex_r*2+4, scaled_hex_r*2+4), pygame.SRCALPHA)
                    draw_hex(s, (*VOID_PURPLE, alpha), (scaled_hex_r+2, scaled_hex_r+2), scaled_hex_r, width=1)
                    surface.blit(s, (int(cx) - scaled_hex_r - 2, int(cy) - scaled_hex_r - 2))

        # Hover preview
        if self.hover_hex and self.hover_hex not in self.layout:
            col, row = self.hover_hex
            x = scaled_spacing * math.sqrt(3) * (col + 0.5 * (row % 2))
            y = scaled_spacing * 1.5 * row
            cx = origin[0] + x
            cy = origin[1] + y
            cdata = CELLS.get(self.selected_cell, CELLS["basic"])
            s = pygame.Surface((scaled_hex_r*2+4, scaled_hex_r*2+4), pygame.SRCALPHA)
            draw_hex(s, (*cdata["color"], 100), (scaled_hex_r+2, scaled_hex_r+2), scaled_hex_r)
            surface.blit(s, (int(cx) - scaled_hex_r - 2, int(cy) - scaled_hex_r - 2))

    def _draw_palette(self, surface, game_time):
        self.palette_rects = {}
        px, py = self.palette_x, self.palette_y
        header = self.font_med.render("CELL PALETTE", True, NEON_CYAN)
        surface.blit(header, (px, py - 24))

        for i, ctype in enumerate(self.unlocked):
            cdata = CELLS.get(ctype, CELLS["basic"])
            row, col = divmod(i, 2)
            rx = px + col * 100
            ry = py + row * 56
            rect = pygame.Rect(rx, ry, 90, 48)
            self.palette_rects[ctype] = rect

            selected = ctype == self.selected_cell
            pulse = pulse_value(game_time + i, speed=1.5) if selected else 0.7
            c = tuple(int(v * pulse) for v in cdata["glow"])

            panel = pygame.Surface((90, 48), pygame.SRCALPHA)
            panel.fill((12, 6, 28, 200 if selected else 120))
            surface.blit(panel, rect.topleft)
            pygame.draw.rect(surface, c, rect, width=2 if selected else 1, border_radius=4)
            if selected:
                draw_glow_rect(surface, cdata["glow"], rect, alpha=40)

            # Mini hex
            draw_hex(surface, cdata["color"], (rx+18, ry+24), 12)
            name_t = self.font_small.render(cdata["name"][:12], True, WHITE if selected else (160,140,180))
            surface.blit(name_t, (rx+34, ry+16))

    def _draw_tooltip(self, surface):
        if not self.tooltip_cell:
            return
        cdata = CELLS.get(self.tooltip_cell, CELLS["basic"])
        lines = [
            cdata["name"],
            cdata["desc"],
            f"Cost: {cdata['cost']}  Genome: {cdata['genome']}",
            f"HP: {cdata['hp']}  Mass: {cdata['mass']}",
        ]
        if cdata.get("damage"):
            lines.append(f"Damage: {cdata['damage']}")
        if cdata.get("ability"):
            lines.append(f"Ability: {cdata['ability']}")

        tw = 240
        th = len(lines) * 16 + 16
        tx = self.palette_x - tw - 10
        ty = self.palette_y

        panel = pygame.Surface((tw, th), pygame.SRCALPHA)
        panel.fill((10, 5, 25, 220))
        surface.blit(panel, (tx, ty))
        pygame.draw.rect(surface, cdata["glow"], (tx, ty, tw, th), width=1, border_radius=4)

        for i, ln in enumerate(lines):
            c = WHITE if i == 0 else (180, 160, 200)
            t = self.font_small.render(ln, True, c)
            surface.blit(t, (tx + 8, ty + 8 + i * 16))

    def _draw_stats(self, surface, game_time):
        total_cost   = sum(CELLS.get(v, CELLS["basic"])["cost"]   for v in self.layout.values())
        total_genome = sum(CELLS.get(v, CELLS["basic"])["genome"] for v in self.layout.values())
        cell_count   = len(self.layout)
        offense_count = sum(1 for v in self.layout.values() if CELLS.get(v,{}).get("category") == "offense")

        genome_cap  = get_genome_cap(self.level)
        biomass_cap = get_biomass_cap(self.level)

        genome_color  = NEON_GREEN if total_genome <= genome_cap  else (255, 60, 60)
        biomass_color = NEON_GREEN if total_cost   <= biomass_cap else (255, 60, 60)

        lines = [
            (f"Cells: {cell_count}",                          NEON_CYAN),
            (f"Genome: {total_genome} / {genome_cap}",        genome_color),
            (f"Biomass Cost: {total_cost} / {biomass_cap}",   biomass_color),
            (f"Offense cells: {offense_count}",               NEON_ORANGE),
        ]
        # Panel bg
        panel = pygame.Surface((200, len(lines)*18 + 16), pygame.SRCALPHA)
        panel.fill((10, 5, 25, 180))
        surface.blit(panel, (22, 72))
        for i, (ln, c) in enumerate(lines):
            t = self.font_small.render(ln, True, c)
            surface.blit(t, (30, 80 + i * 18))

        # Genome bar
        bar_y = 80 + len(lines) * 18 + 4
        bar_w = 180
        ratio = min(1.0, total_genome / max(1, genome_cap))
        pygame.draw.rect(surface, (30, 15, 40), (30, bar_y, bar_w, 8), border_radius=3)
        fill_c = genome_color
        pygame.draw.rect(surface, fill_c, (30, bar_y, int(bar_w * ratio), 8), border_radius=3)

    def _draw_validation_errors(self, surface, game_time):
        if not self.validation_errors or self.error_flash <= 0:
            return
        self.error_flash -= 1/60
        alpha = min(255, int(self.error_flash * 120))
        y = self.sh // 2 + 160
        for err in self.validation_errors:
            t = self.font_med.render(f"✗ {err}", True, (255, 60, 60))
            t.set_alpha(alpha)
            surface.blit(t, (self.sw//2 - t.get_width()//2, y))
            y += 22
