# =============================================================================
# scenes/customize_py — Hex skin customisation screen
# =============================================================================

import pygame
from scene_manager import BaseScene
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG, COLOR_TEXT, COLOR_ACCENT,
    COLOR_TEXT_DIM, COLOR_BORDER, COLOR_BG_PANEL, SCENE_MAIN_MENU,
    HEX_SKINS, HEX_RADIUS,
)
from ui import (
    Button, draw_panel, generate_stars, draw_starfield, render_text_centered,
)
from hex_renderer import draw_hex, draw_hex_preview
from asset_manager import assets
from data.progress import load_progress, set_selected_skin, get_selected_skin

# Grid layout constants
CARD_W    = 180
CARD_H    = 200
CARD_PAD  = 24
GRID_COLS = 3


class CustomizeScene(BaseScene):
    """
    Shows all hex skins in a grid.
    Locked skins display their wave unlock requirement.
    Clicking an unlocked skin equips it immediately and persists the choice.
    A large animated preview is shown on the right side.
    """

    def __init__(self):
        super().__init__()
        self.stars = generate_stars(200)
        self.t = 0.0
        self.pulse_t = 0.0

        self.progress = {}
        self.selected_id = "default"
        self.hover_id = None

        self.btn_back = Button(30, 30, 120, 40, "← BACK",
                               color=(100, 120, 160), font_size=18)

        self.preview_rot = 0.0
        self.preview_skin = HEX_SKINS[0] if HEX_SKINS else {}

    def on_enter(self, **kwargs):
        self.progress = load_progress()
        self.selected_id = get_selected_skin()
        self.t = 0.0

    def update(self, events: list, dt: float):
        from input_handler import input_handler
        input_handler.update(events, dt)
        
        self.t += dt
        self.pulse_t += dt
        self.preview_rot += dt * 0.5
        
        if self.btn_back.update(input_handler, dt):
            self.manager.switch(SCENE_MAIN_MENU)
        
        # Click on a skin card
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_skin_click(event.pos)

    def _handle_skin_click(self, mouse_pos):
        """Check if player clicked a skin and equip it."""
        if not HEX_SKINS:
            return
        
        for i, skin in enumerate(HEX_SKINS):
            col = i % GRID_COLS
            row = i // GRID_COLS
            card_x = 50 + col * (CARD_W + CARD_PAD)
            card_y = 120 + row * (CARD_H + CARD_PAD)
            
            card_rect = pygame.Rect(card_x, card_y, CARD_W, CARD_H)
            if card_rect.collidepoint(mouse_pos):
                highest_wave = self.progress.get("highest_wave", 0)
                unlock_wave = skin.get("unlock_wave", 0)
                
                if highest_wave >= unlock_wave:
                    self.selected_id = skin.get("id", "default")
                    set_selected_skin(self.selected_id)
                    self.preview_skin = skin

    def draw(self, surface: pygame.Surface):
        surface.fill(COLOR_BG)
        draw_starfield(surface, self.t, 0, self.stars)
        
        render_text_centered(surface, "CUSTOMIZE HEX", 48, COLOR_ACCENT, 40)
        
        self.btn_back.draw(surface)
        
        # Draw skin cards in grid
        if HEX_SKINS:
            for i, skin in enumerate(HEX_SKINS):
                col = i % GRID_COLS
                row = i // GRID_COLS
                card_x = 50 + col * (CARD_W + CARD_PAD)
                card_y = 120 + row * (CARD_H + CARD_PAD)
                
                self._draw_skin_card(surface, card_x, card_y, skin)
        
        # Preview on right
        self._draw_preview(surface, SCREEN_WIDTH - 220, 150, self.preview_skin)

    def _draw_skin_card(self, surface: pygame.Surface, x: float, y: float, skin: dict):
        """Draw a single skin card."""
        rect = pygame.Rect(x, y, CARD_W, CARD_H)
        
        highest_wave = self.progress.get("highest_wave", 0)
        unlock_wave = skin.get("unlock_wave", 0)
        is_unlocked = highest_wave >= unlock_wave
        is_selected = skin.get("id") == self.selected_id
        
        # Draw card
        bg_color = (50, 60, 70) if is_unlocked else (35, 35, 40)
        draw_panel(surface, rect)
        if is_selected:
            pygame.draw.rect(surface, (0, 255, 150), rect, 3, border_radius=8)
        
        # Skin name
        font_name = assets.get_font("default", 16)
        name = font_name.render(skin.get("name", "Unknown"), True, (255, 255, 255))
        surface.blit(name, (x + 10, y + 10))
        
        # Mini preview
        if is_unlocked:
            draw_hex_preview(surface, x + CARD_W // 2, y + CARD_H // 2 + 5, skin, radius=18)
            # Unlocked badge
            font_badge = assets.get_font("default", 11)
            badge = font_badge.render("✓ UNLOCKED", True, (100, 255, 100))
            surface.blit(badge, (x + 10, y + CARD_H - 22))
        else:
            # Locked indicator with achievement
            font_lock = assets.get_font("default", 11)
            achievement = skin.get("achievement", f"Wave {unlock_wave}")
            lock_text = font_lock.render(achievement, True, (255, 150, 100))
            surface.blit(lock_text, (x + CARD_W // 2 - lock_text.get_width() // 2, y + CARD_H // 2))

    def _draw_preview(self, surface: pygame.Surface, x: float, y: float, skin: dict):
        """Draw large animated preview of selected skin."""
        title_font = assets.get_font("default", 20)
        title = title_font.render("Preview", True, COLOR_ACCENT)
        surface.blit(title, (x - 20, y - 30))
        
        draw_hex_preview(surface, x + 50, y + 80, skin, radius=60)
        
        # Description
        desc = skin.get("description", "")
        desc_font = assets.get_font("default", 12)
        desc_text = desc_font.render(desc, True, COLOR_TEXT_DIM)
        surface.blit(desc_text, (x - 80, y + 160))
