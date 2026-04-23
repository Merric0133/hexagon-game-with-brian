"""
help_scene.py — Scrollable help / instructions screen.
"""
import pygame
from scene_manager import BaseScene
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG, COLOR_TEXT, COLOR_ACCENT,
    COLOR_TEXT_DIM, SCENE_MAIN_MENU,
)
from ui import Button, draw_panel, generate_stars, draw_starfield, render_text_centered
from asset_manager import assets

SECTIONS = [
    {
        "title": "OBJECTIVE",
        "color": (0, 220, 255),
        "lines": [
            "Survive 50 waves of enemy hexagonal cells.",
            "Between each wave, reinforce your hex body.",
            "Your HP reaches zero → DEFEAT.",
            "Clear all 50 waves → VICTORY!",
        ],
    },
    {
        "title": "CONTROLS",
        "color": (140, 80, 255),
        "lines": [
            "WASD / Arrow keys  — Move your hex",
            "P                  — Pause / Unpause",
            "ESC                — Quit to main menu",
            "Mouse              — Navigate menus & Build Phase",
        ],
    },
    {
        "title": "BUILD PHASE",
        "color": (255, 160, 60),
        "lines": [
            "Before each wave you visit the Build Phase.",
            "Drag cells from your INVENTORY onto the 6 slots.",
            "Right-click a slot to return that cell to inventory.",
            "Press ENTER or LAUNCH when ready.",
            "Each slot is a hex adjacent to your core.",
        ],
    },
    {
        "title": "CELL TYPES",
        "color": (255, 100, 100),
        "lines": [
            "♥ HEART  — +20 Max HP per cell",
            "➤ MOVE   — +60 Speed per cell",
            "✦ DAMAGE — Contact damage aura (+15 dmg)",
            "⬡ SHIELD — +8 Defense (reduces damage taken)",
        ],
    },
    {
        "title": "EARNING CELLS",
        "color": (100, 255, 150),
        "lines": [
            "You earn 2 random cells after every wave.",
            "Milestone waves (5, 10, 15…) give a bonus cell.",
            "Higher waves bias rewards toward Damage/Shield.",
            "Cells accumulate — plan your build over time!",
        ],
    },
    {
        "title": "COMBAT",
        "color": (255, 80, 80),
        "lines": [
            "Enemies seek and ram your hex core.",
            "DAMAGE cells deal contact aura damage nearby.",
            "Contact damage triggers per-slot with cooldown.",
            "Enemies drop XP orbs and occasional power-ups.",
        ],
    },
    {
        "title": "POWER-UPS",
        "color": (60, 220, 100),
        "lines": [
            "Enemies drop power-ups (20% chance on kill).",
            "Walk over them to collect automatically.",
            "+20 HP / +50 HP  — Restore hit points",
            "FAST             — Speed +60 for 8 seconds",
            "SHIELD           — 4 seconds of invincibility",
        ],
    },
    {
        "title": "SKINS & ACHIEVEMENTS",
        "color": (255, 215, 0),
        "lines": [
            "3 FREE skins: Default, Crimson, Void",
            "  → Wave 10: Golden Hex",
            "  → Wave 25: Emerald Hex",
            "  → Wave 50: Platinum Hex (Victory!)",
        ],
    },
]


class HelpScene(BaseScene):

    def __init__(self):
        super().__init__()
        self.stars    = generate_stars(180)
        self.t        = 0.0
        self.scroll_y = 0
        self._content_height = 0
        self.btn_back = Button(30, 30, 120, 40, "← BACK",
                               color=(100, 120, 160), font_size=18)

    def on_enter(self, **kwargs):
        self.scroll_y = 0

    def update(self, events: list, dt: float):
        from input_handler import input_handler
        input_handler.update(events, dt)
        self.t += dt

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.manager.switch(SCENE_MAIN_MENU)
            if event.type == pygame.MOUSEWHEEL:
                max_scroll = max(0, self._content_height - SCREEN_HEIGHT + 140)
                self.scroll_y = max(0, min(max_scroll,
                                           self.scroll_y - event.y * 24))
        if self.btn_back.update(input_handler, dt):
            self.manager.switch(SCENE_MAIN_MENU)

    def draw(self, surface: pygame.Surface):
        surface.fill(COLOR_BG)
        draw_starfield(surface, self.t * 2, 0, self.stars)

        clip_rect = pygame.Rect(0, 100, SCREEN_WIDTH, SCREEN_HEIGHT - 100)
        surface.set_clip(clip_rect)

        col_w   = (SCREEN_WIDTH - 80) // 2
        col_gap = 40
        left_x  = 40
        right_x = left_x + col_w + col_gap

        for i, section in enumerate(SECTIONS):
            col_x = left_x if i % 2 == 0 else right_x
            y_pos = 110 + (i // 2) * 210 - self.scroll_y
            self._draw_section(surface, section, col_x, y_pos, col_w)

        self._content_height = (len(SECTIONS) // 2 + 1) * 210
        surface.set_clip(None)

        render_text_centered(surface, "HOW TO PLAY", 42, COLOR_ACCENT, 36)
        render_text_centered(surface, "Scroll to read all sections",
                             15, COLOR_TEXT_DIM, 80)
        self.btn_back.draw(surface)

        if self._content_height > SCREEN_HEIGHT - 100:
            font_xs = assets.get_font("default", 13)
            hint = font_xs.render("▼ scroll for more", True, COLOR_TEXT_DIM)
            surface.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2,
                                 SCREEN_HEIGHT - 20))

    def _draw_section(self, surface, section, x, y, w):
        panel_h = 190
        if y + panel_h < 100 or y > SCREEN_HEIGHT:
            return
        draw_panel(surface, pygame.Rect(x, y, w, panel_h))
        col    = section["color"]
        font_h = assets.get_font("default", 17)
        font_b = assets.get_font("default", 14)
        pygame.draw.rect(surface, col, (x, y, w, 3), border_radius=2)
        title_surf = font_h.render(section["title"], True, col)
        surface.blit(title_surf, (x + 12, y + 10))
        ly = y + 34
        for line in section["lines"]:
            pygame.draw.circle(surface, col, (x + 18, ly + 7), 3)
            txt = font_b.render(line, True, COLOR_TEXT_DIM)
            surface.blit(txt, (x + 28, ly))
            ly += 22
