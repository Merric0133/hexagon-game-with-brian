# =============================================================================
# scenes/codex_scene.py — Body-part codex / build-reference screen
# =============================================================================
from scene_manager import BaseScene
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG, COLOR_TEXT,
    COLOR_ACCENT, COLOR_TEXT_DIM, COLOR_BORDER, COLOR_BG_PANEL,
    RARITY_COLORS, SCENE_MAIN_MENU,
)
from ui import (
    Button, draw_panel, generate_stars, draw_starfield,
    render_text_centered, draw_rarity_badge, wrap_text,
)
from asset_manager import assets
from data.parts_data import BODY_PARTS, RARITY_ORDER
from data.progress import load_progress
import pygame


class CodexScene(BaseScene):
    """
    Displays all body parts with their stats, rarity, and unlock conditions.
    """

    def __init__(self):
        super().__init__()
        self.stars = generate_stars(200)
        self.t = 0.0
        
        self.btn_back = Button(30, 30, 120, 40, "← BACK",
                              color=(100, 120, 160), font_size=18)
        
        self.scroll_y = 0
        self.selected_part = None
        self.progress = {}

    def on_enter(self, **kwargs):
        self.progress = load_progress()
        self.scroll_y = 0
        self.selected_part = None

    def update(self, events: list, dt: float):
        from input_handler import input_handler
        input_handler.update(events)
        
        self.t += dt
        
        if self.btn_back.update(input_handler, dt):
            self.manager.switch(SCENE_MAIN_MENU)
        
        # Mouse wheel scroll
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # Scroll up
                    self.scroll_y += 30
                elif event.button == 5:  # Scroll down
                    self.scroll_y -= 30
            
            # Click to select a part
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                for i, part in enumerate(BODY_PARTS):
                    card_y = 100 + i * 140 + self.scroll_y
                    if pygame.Rect(20, card_y, SCREEN_WIDTH - 40, 130).collidepoint(mouse_pos):
                        self.selected_part = part

    def draw(self, surface: pygame.Surface):
        surface.fill(COLOR_BG)
        
        # Starfield
        draw_starfield(surface, self.t, 0, self.stars)
        
        # Title
        render_text_centered(surface, "BODY PARTS CODEX", 48, COLOR_ACCENT, 50)
        
        # Back button
        self.btn_back.draw(surface)
        
        # Two-column layout
        if self.selected_part:
            self._draw_parts_list(surface, 20, 100, (SCREEN_WIDTH - 40) // 2 - 10)
            self._draw_part_detail(surface, (SCREEN_WIDTH // 2) + 10, 100)
        else:
            self._draw_parts_list(surface, 20, 100, SCREEN_WIDTH - 40)

    def _draw_parts_list(self, surface: pygame.Surface, x: float, y: float, w: float):
        """Draw scrollable list of all parts."""
        max_visible = 4
        
        for i, part in enumerate(BODY_PARTS):
            card_y = y + i * 140 + self.scroll_y
            
            if card_y < -150 or card_y > SCREEN_HEIGHT:
                continue
            
            self._draw_part_card(surface, x, card_y, w, 130, part)

    def _draw_part_card(self, surface: pygame.Surface, x: float, y: float,
                       w: float, h: float, part: dict):
        """Draw a single part card."""
        rect = pygame.Rect(x, y, w, h)
        
        # Get rarity color
        rarity = part.get("rarity", "common")
        rarity_colors = {
            "common": (200, 200, 200),
            "uncommon": (100, 255, 100),
            "rare": (100, 150, 255),
            "legendary": (255, 215, 0),
        }
        rarity_col = rarity_colors.get(rarity, (200, 200, 200))
        
        # Check if unlocked
        highest_wave = self.progress.get("highest_wave", 0)
        is_unlocked = highest_wave >= part.get("wave_unlock", 1)
        
        # Draw card background
        bg_color = (50, 50, 60) if is_unlocked else (30, 30, 35)
        pygame.draw.rect(surface, bg_color, rect, border_radius=8)
        pygame.draw.rect(surface, rarity_col, rect, 2, border_radius=8)
        
        # Part name
        font_name = assets.get_font("default", 22)
        name_text = font_name.render(part["name"], True, rarity_col)
        surface.blit(name_text, (x + 15, y + 10))
        
        # Rarity badge
        font_rarity = assets.get_font("default", 12)
        rarity_text = font_rarity.render(rarity.upper(), True, rarity_col)
        surface.blit(rarity_text, (x + w - 80, y + 10))
        
        # Stats
        font_stats = assets.get_font("default", 14)
        stats_y = y + 40
        
        hp_bonus = part.get("hp_bonus", 0)
        def_bonus = part.get("def_bonus", 0)
        regen_bonus = part.get("regen_bonus", 0)
        
        if hp_bonus > 0:
            stat_text = font_stats.render(f"❤ +{hp_bonus:.0f} HP", True, (100, 255, 100))
            surface.blit(stat_text, (x + 15, stats_y))
        
        if def_bonus > 0:
            stat_text = font_stats.render(f"🛡 +{def_bonus:.0f} DEF", True, (100, 150, 255))
            surface.blit(stat_text, (x + 15, stats_y + 20))
        
        if regen_bonus > 0:
            stat_text = font_stats.render(f"✧ +{regen_bonus:.1f} REGEN", True, (100, 255, 150))
            surface.blit(stat_text, (x + 15, stats_y + 40))
        
        # Unlock requirement
        if not is_unlocked:
            req_text = font_stats.render(f"Unlock at Wave {part.get('wave_unlock', 1)}", True, COLOR_TEXT_DIM)
            surface.blit(req_text, (x + 15, y + h - 25))

    def _draw_part_detail(self, surface: pygame.Surface, x: float, y: float):
        """Draw detailed view of selected part."""
        if not self.selected_part:
            return
        
        part = self.selected_part
        rarity = part.get("rarity", "common")
        rarity_colors = {
            "common": (200, 200, 200),
            "uncommon": (100, 255, 100),
            "rare": (100, 150, 255),
            "legendary": (255, 215, 0),
        }
        rarity_col = rarity_colors.get(rarity, (200, 200, 200))
        
        panel_h = SCREEN_HEIGHT - 150
        panel = pygame.Rect(x, y, SCREEN_WIDTH - x - 20, panel_h)
        
        draw_panel(surface, panel)
        
        # Title
        font_title = assets.get_font("default", 32)
        title = font_title.render(part["name"], True, rarity_col)
        surface.blit(title, (x + 20, y + 15))
        
        # Description
        font_desc = assets.get_font("default", 16)
        desc = font_desc.render(part["description"], True, (200, 200, 200))
        surface.blit(desc, (x + 20, y + 55))
        
        # Full stats breakdown
        font_stat = assets.get_font("default", 18)
        stat_y = y + 110
        
        stats_text = [
            f"Max HP Bonus: +{part.get('hp_bonus', 0):.0f}",
            f"Defense Bonus: +{part.get('def_bonus', 0):.0f}",
            f"Regen Bonus: +{part.get('regen_bonus', 0):.1f} HP/s",
        ]
        
        for stat_line in stats_text:
            stat_surf = font_stat.render(stat_line, True, (150, 200, 255))
            surface.blit(stat_surf, (x + 20, stat_y))
            stat_y += 35
        
        # Unlock info
        highest_wave = self.progress.get("highest_wave", 0)
        is_unlocked = highest_wave >= part.get("wave_unlock", 1)
        
        unlock_col = (100, 255, 100) if is_unlocked else (255, 100, 100)
        unlock_text = f"✓ Unlocked" if is_unlocked else f"Unlocks at Wave {part.get('wave_unlock', 1)}"
        unlock_surf = font_stat.render(unlock_text, True, unlock_col)
        surface.blit(unlock_surf, (x + 20, stat_y + 40))
