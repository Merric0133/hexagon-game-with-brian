"""
customize_scene.py — Hex skin customisation screen.
"""
import pygame
from scene_manager import BaseScene
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG, COLOR_TEXT, COLOR_ACCENT,
    COLOR_TEXT_DIM, SCENE_MAIN_MENU, HEX_SKINS, HEX_RADIUS,
)
from ui import Button, draw_panel, generate_stars, draw_starfield, render_text_centered
from hex_renderer import draw_hex, draw_hex_preview
from asset_manager import assets
from data.progress import load_progress, set_selected_skin, get_selected_skin

CARD_W    = 180
CARD_H    = 200
CARD_PAD  = 24
GRID_COLS = 3


class CustomizeScene(BaseScene):

    def __init__(self):
        super().__init__()
        self.stars     = generate_stars(200)
        self.t         = 0.0
        self.progress  = {}
        self.selected_id   = "default"
        self.preview_skin  = HEX_SKINS[0] if HEX_SKINS else {}

        self.btn_back = Button(30, 30, 120, 40, "← BACK",
                               color=(100, 120, 160), font_size=18)

    def on_enter(self, **kwargs):
        self.progress    = load_progress()
        self.selected_id = get_selected_skin()
        self.t = 0.0

    def update(self, events: list, dt: float):
        from input_handler import input_handler
        input_handler.update(events, dt)
        self.t += dt

        if self.btn_back.update(input_handler, dt):
            self.manager.switch(SCENE_MAIN_MENU)

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_skin_click(event.pos)

    def _handle_skin_click(self, mouse_pos):
        for i, skin in enumerate(HEX_SKINS):
            col  = i % GRID_COLS
            row  = i // GRID_COLS
            cx   = 50 + col * (CARD_W + CARD_PAD)
            cy   = 120 + row * (CARD_H + CARD_PAD)
            rect = pygame.Rect(cx, cy, CARD_W, CARD_H)
            if rect.collidepoint(mouse_pos):
                hw = self.progress.get("highest_wave", 0)
                if hw >= skin.get("unlock_wave", 0):
                    self.selected_id = skin["id"]
                    set_selected_skin(self.selected_id)
                    self.preview_skin = skin

    def draw(self, surface: pygame.Surface):
        surface.fill(COLOR_BG)
        draw_starfield(surface, self.t, 0, self.stars)
        render_text_centered(surface, "CUSTOMIZE HEX", 48, COLOR_ACCENT, 40)
        self.btn_back.draw(surface)

        for i, skin in enumerate(HEX_SKINS):
            col  = i % GRID_COLS
            row  = i // GRID_COLS
            cx   = 50 + col * (CARD_W + CARD_PAD)
            cy   = 120 + row * (CARD_H + CARD_PAD)
            self._draw_skin_card(surface, cx, cy, skin)

        self._draw_preview(surface, SCREEN_WIDTH - 220, 150, self.preview_skin)

    def _draw_skin_card(self, surface, x, y, skin):
        rect       = pygame.Rect(x, y, CARD_W, CARD_H)
        hw         = self.progress.get("highest_wave", 0)
        is_unlocked = hw >= skin.get("unlock_wave", 0)
        is_selected = skin.get("id") == self.selected_id

        draw_panel(surface, rect)
        if is_selected:
            pygame.draw.rect(surface, (0, 255, 150), rect, 3, border_radius=8)

        font_name = assets.get_font("default", 16)
        name_surf = font_name.render(skin.get("name", ""), True, (255, 255, 255))
        surface.blit(name_surf, (x + 10, y + 10))

        if is_unlocked:
            draw_hex_preview(surface, x + CARD_W // 2, y + CARD_H // 2 + 5,
                             skin, radius=18)
            font_b = assets.get_font("default", 11)
            badge  = font_b.render("✓ UNLOCKED", True, (100, 255, 100))
            surface.blit(badge, (x + 10, y + CARD_H - 22))
        else:
            font_l  = assets.get_font("default", 11)
            ach     = skin.get("achievement", f"Wave {skin['unlock_wave']}")
            lock    = font_l.render(ach, True, (255, 150, 100))
            surface.blit(lock, (x + CARD_W // 2 - lock.get_width() // 2,
                                y + CARD_H // 2))

    def _draw_preview(self, surface, x, y, skin):
        tf = assets.get_font("default", 20)
        t  = tf.render("Preview", True, COLOR_ACCENT)
        surface.blit(t, (x - 20, y - 30))
        draw_hex_preview(surface, x + 50, y + 80, skin, radius=60)
        df = assets.get_font("default", 12)
        ds = df.render(skin.get("description", ""), True, COLOR_TEXT_DIM)
        surface.blit(ds, (x - 80, y + 160))
