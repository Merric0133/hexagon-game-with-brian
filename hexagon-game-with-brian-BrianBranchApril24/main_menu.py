"""
main_menu.py — Title / main-menu screen.
"""
import pygame
import math
from scene_manager import BaseScene
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG, COLOR_TEXT, COLOR_ACCENT,
    COLOR_ACCENT2, COLOR_TEXT_DIM, HEX_SKINS,
)
from ui import Button, generate_stars, draw_starfield, render_text_centered
from hex_renderer import draw_hex_preview
from asset_manager import assets
from data.progress import get_selected_skin, load_progress

SCENE_BUILD    = "build"
SCENE_HELP     = "help"
SCENE_CUSTOMIZE = "customize"


class MainMenuScene(BaseScene):

    def __init__(self):
        super().__init__()
        self.stars = generate_stars(250)
        self.t     = 0.0

        self._init_deco_hexes()

        bw, bh  = 230, 48
        cx      = SCREEN_WIDTH  // 2 - bw // 2
        spacing = 58
        start_y = SCREEN_HEIGHT // 2 + 10

        self.btn_play      = Button(cx, start_y,             bw, bh, "▶  PLAY",      COLOR_ACCENT)
        self.btn_customize = Button(cx, start_y + spacing,   bw, bh, "⬡  CUSTOMIZE", COLOR_ACCENT2)
        self.btn_help      = Button(cx, start_y + spacing*2, bw, bh, "?  HELP",       (100, 160, 220))
        self.btn_quit      = Button(cx, start_y + spacing*3, bw, bh, "✕  QUIT",       (160, 80,  80))

        self.selected_skin_data = HEX_SKINS[0]

    def _init_deco_hexes(self):
        import random
        rng = random.Random(42)
        self.deco_hexes = []
        for _ in range(8):
            self.deco_hexes.append({
                "x":  rng.uniform(0, SCREEN_WIDTH),
                "y":  rng.uniform(0, SCREEN_HEIGHT),
                "r":  rng.uniform(20, 70),
                "vx": rng.uniform(-12, 12),
                "vy": rng.uniform(-8,  8),
                "rot":  rng.uniform(0, math.tau),
                "vrot": rng.uniform(-0.3, 0.3),
                "skin": rng.choice(HEX_SKINS),
            })

    def on_enter(self, **kwargs):
        skin_id = get_selected_skin()
        self.selected_skin_data = next(
            (s for s in HEX_SKINS if s["id"] == skin_id), HEX_SKINS[0])

    def update(self, events: list, dt: float):
        self.t += dt

        for h in self.deco_hexes:
            h["x"]   = (h["x"] + h["vx"] * dt) % SCREEN_WIDTH
            h["y"]   = (h["y"] + h["vy"] * dt) % SCREEN_HEIGHT
            h["rot"] += h["vrot"] * dt

        from input_handler import input_handler
        input_handler.update(events, dt)

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.manager.switch(SCENE_BUILD, wave_num=1, new_cells=[])

        if self.btn_play.update(input_handler, dt):
            self.manager.switch(SCENE_BUILD, wave_num=1, new_cells=[])
        if self.btn_customize.update(input_handler, dt):
            self.manager.switch(SCENE_CUSTOMIZE)
        if self.btn_help.update(input_handler, dt):
            self.manager.switch(SCENE_HELP)
        if self.btn_quit.update(input_handler, dt):
            pygame.quit(); raise SystemExit

    def draw(self, surface: pygame.Surface):
        surface.fill(COLOR_BG)
        draw_starfield(surface, self.t * 5, self.t * 2, self.stars)

        for h in self.deco_hexes:
            draw_hex_preview(surface, h["x"], h["y"],
                             h["skin"], radius=h["r"])

        # Title
        title_y  = SCREEN_HEIGHT // 2 - 170
        font_big = assets.get_font("default", 72)
        title    = font_big.render("HEXCORE", True, COLOR_ACCENT)
        tx = SCREEN_WIDTH // 2 - title.get_width() // 2
        ty = title_y + int(math.sin(self.t * 1.4) * 4)
        shadow = font_big.render("HEXCORE", True, (0, 0, 0))
        surface.blit(shadow, (tx + 3, ty + 3))
        surface.blit(title, (tx, ty))

        render_text_centered(surface, "survive  •  build  •  ascend",
                             20, COLOR_TEXT_DIM, title_y + 78)

        # Selected skin preview
        if self.selected_skin_data:
            px, py = SCREEN_WIDTH - 90, 90
            draw_hex_preview(surface, px, py, self.selected_skin_data, radius=40)
            font_sm = assets.get_font("default", 14)
            lbl = font_sm.render(self.selected_skin_data["name"], True, COLOR_TEXT_DIM)
            surface.blit(lbl, (px - lbl.get_width() // 2, py + 48))

        # Best wave
        progress = load_progress()
        hw = progress.get("highest_wave", 0)
        if hw > 0:
            font_sm = assets.get_font("default", 16)
            rec = font_sm.render(f"Best: Wave {hw}", True, COLOR_TEXT_DIM)
            surface.blit(rec, (18, SCREEN_HEIGHT - 30))

        for btn in [self.btn_play, self.btn_customize, self.btn_help, self.btn_quit]:
            btn.draw(surface)

        font_xs = assets.get_font("default", 13)
        ver = font_xs.render("v1.0  —  CELL BUILD UPDATE", True, (40, 50, 70))
        surface.blit(ver, (SCREEN_WIDTH - ver.get_width() - 10, SCREEN_HEIGHT - 20))
