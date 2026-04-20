# =============================================================================
# scenes/help_py — Help / Instructions screen
# =============================================================================
# Covers controls, objectives, wave system, power-ups, and body parts.
# Required by the assignment rubric: "Help or instructions screen/page/pop-up"
# =============================================================================

import pygame
from scene_manager import BaseScene
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG, COLOR_TEXT, COLOR_ACCENT,
    COLOR_ACCENT2, COLOR_TEXT_DIM, COLOR_BORDER, COLOR_BG_PANEL,
    COLOR_SUCCESS, COLOR_WARNING, SCENE_MAIN_MENU,
)
from ui import (
    Button, draw_panel, generate_stars, draw_starfield,
    render_text_centered,
)
from asset_manager import assets


# ---------------------------------------------------------------------------
# Help content — structured so it's easy to add/edit sections
# ---------------------------------------------------------------------------
SECTIONS = [
    {
        "title": "OBJECTIVE",
        "color": (0, 220, 255),
        "lines": [
            "Survive 50 waves of enemy hexagonal cells.",
            "Defeat every enemy in a wave to advance.",
            "Your HP reaches zero → DEFEAT.",
            "Clear all 50 waves → VICTORY!",
        ],
    },
    {
        "title": "CONTROLS",
        "color": (140, 80, 255),
        "lines": [
            "WASD  /  Arrow keys  — Move your hex",
            "P                   — Pause / Unpause",
            "ESC                 — Quit current game",
            "Mouse               — Navigate menus",
        ],
    },
    {
        "title": "COMBAT & ABILITIES",
        "color": (255, 100, 100),
        "lines": [
            "Gain abilities by leveling up!",
            "Each level grants 3 random ability choices.",
            "Auto-cast abilities at nearby enemies.",
            "Right-click to manually cast your 1st ability.",
            "Max 6 abilities equipped at once.",
        ],
    },
    {
        "title": "EXPERIENCE & LEVELING",
        "color": (100, 255, 150),
        "lines": [
            "Enemies drop XP orbs when defeated.",
            "Collect orbs by moving over them.",
            "Each level requires more XP.",
            "See your XP bar below your health.",
        ],
    },
    {
        "title": "POWER-UPS",
        "color": (60, 220, 100),
        "lines": [
            "Enemies drop power-ups (25% chance).",
            "Walk over them to collect automatically.",
            "+20 HP / +50 HP  — Restore hit points",
            "FAST             — Speed boost (+60 for 8s)",
            "SHIELD           — 4 seconds of invincibility",
        ],
    },
    {
        "title": "WAVES & SCALING",
        "color": (255, 180, 0),
        "lines": [
            "Each wave spawns more enemies.",
            "Enemy HP, speed, and damage scale up.",
            "4-second intermission between waves.",
            "Waves reward exponentially more score.",
        ],
    },
    {
        "title": "SKINS & ACHIEVEMENTS",
        "color": (255, 215, 0),
        "lines": [
            "3 FREE skins: Default, Crimson, Void",
            "Unlock more by reaching wave milestones:",
            "  → Wave 10: Golden Hex",
            "  → Wave 25: Emerald Hex",
            "  → Wave 50: Platinum Hex (Victory!)",
        ],
    },
    {
        "title": "TIPS & STRATEGY",
        "color": (160, 160, 160),
        "lines": [
            "Keep moving — enemies will surround you!",
            "Grab power-ups when HP is low.",
            "Prioritize leveling up abilities early.",
            "Higher waves grant much more score.",
            "The world boundary is solid — don't get cornered!",
        ],
    },
]


class HelpScene(BaseScene):
    """Full-page help/instructions screen, scrollable."""

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
        self.t += dt

        from input_handler import input_handler
        input_handler.update(events, dt)

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

        # Clip content
        clip_rect = pygame.Rect(0, 100, SCREEN_WIDTH, SCREEN_HEIGHT - 100)
        surface.set_clip(clip_rect)

        y = 110 - self.scroll_y
        col_w  = (SCREEN_WIDTH - 80) // 2
        col_gap = 40
        left_x  = 40
        right_x = left_x + col_w + col_gap

        for i, section in enumerate(SECTIONS):
            col_x = left_x if i % 2 == 0 else right_x
            y_pos = 110 + (i // 2) * 210 - self.scroll_y

            self._draw_section(surface, section, col_x, y_pos, col_w)

        self._content_height = (len(SECTIONS) // 2 + 1) * 210

        surface.set_clip(None)

        # Fixed header
        render_text_centered(surface, "HOW TO PLAY", 42, COLOR_ACCENT, 36)
        render_text_centered(surface, "Scroll to read all sections",
                             15, COLOR_TEXT_DIM, 80)

        self.btn_back.draw(surface)

        # Scroll hint
        if self._content_height > SCREEN_HEIGHT - 100:
            font_xs = assets.get_font("default", 13)
            hint = font_xs.render("▼ scroll for more", True, COLOR_TEXT_DIM)
            surface.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2,
                                 SCREEN_HEIGHT - 20))

    def _draw_section(self, surface: pygame.Surface, section: dict,
                      x: int, y: int, w: int):
        """Draw a single help section panel."""
        panel_h = 190
        if y + panel_h < 100 or y > SCREEN_HEIGHT:
            return

        draw_panel(surface, pygame.Rect(x, y, w, panel_h))

        col    = section["color"]
        font_h = assets.get_font("default", 17)
        font_b = assets.get_font("default", 14)

        # Title
        pygame.draw.rect(surface, col, (x, y, w, 3), border_radius=2)
        title_surf = font_h.render(section["title"], True, col)
        surface.blit(title_surf, (x + 12, y + 10))

        # Lines
        ly = y + 34
        for line in section["lines"]:
            pygame.draw.circle(surface, col, (x + 18, ly + 7), 3)
            txt = font_b.render(line, True, COLOR_TEXT_DIM)
            surface.blit(txt, (x + 28, ly))
            ly += 22
