import pygame
from core.utils import draw_glow_circle, draw_glow_rect, pulse_value
from core.constants import *
from data.achievements_data import ACHIEVEMENTS

class AchievementsScreen:
    def __init__(self, sw, sh):
        self.sw, self.sh = sw, sh
        self.font_title = pygame.font.SysFont("consolas", 30, bold=True)
        self.font_med   = pygame.font.SysFont("consolas", 15)
        self.font_small = pygame.font.SysFont("consolas", 12)
        self.scroll = 0
        from ui.menus import Button
        self.back_btn = Button((30, sh-60, 120, 40), "BACK", NEON_ORANGE)

    def handle_event(self, event, unlocked_ids):
        if self.back_btn.handle_event(event):
            return "back"
        if event.type == pygame.MOUSEWHEEL:
            self.scroll -= event.y * 30
            self.scroll = max(0, self.scroll)
        return None

    def draw(self, surface, game_time, unlocked_ids):
        surface.fill(DEEP_VOID)
        title = self.font_title.render("ACHIEVEMENTS", True, NEON_CYAN)
        surface.blit(title, (self.sw//2 - title.get_width()//2, 16))

        count_txt = self.font_med.render(
            f"{len(unlocked_ids)} / {len(ACHIEVEMENTS)} unlocked", True, NEON_GREEN)
        surface.blit(count_txt, (self.sw//2 - count_txt.get_width()//2, 52))

        # Center the content area
        content_w = min(self.sw - 80, 1200)
        content_x = self.sw//2 - content_w//2
        area = pygame.Rect(content_x, 90, content_w, self.sh - 160)
        clip = surface.get_clip()
        surface.set_clip(area)

        card_w, card_h = 360, 80
        cols = 3
        pad = 12
        items = list(ACHIEVEMENTS.items())
        for i, (aid, adata) in enumerate(items):
            unlocked = aid in unlocked_ids
            secret = adata.get("secret", False) and not unlocked
            row, col = divmod(i, cols)
            x = area.x + col * (card_w + pad)
            y = area.y + row * (card_h + pad) - self.scroll
            if y + card_h < area.y or y > area.bottom:
                continue

            rect = pygame.Rect(x, y, card_w, card_h)
            color = adata["icon_color"] if unlocked else (50, 40, 60)
            pulse = pulse_value(game_time + i, speed=1.2) if unlocked else 0.5

            panel = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            panel.fill((12, 6, 28, 220 if unlocked else 140))
            surface.blit(panel, rect.topleft)
            pygame.draw.rect(surface, tuple(int(v*pulse) for v in color),
                             rect, width=2 if unlocked else 1, border_radius=6)
            if unlocked:
                draw_glow_rect(surface, color, rect, alpha=25)

            # Icon orb
            draw_glow_circle(surface, color, (x+30, y+card_h//2),
                             16 if unlocked else 10, alpha=60 if unlocked else 20, layers=2)

            if secret:
                name_t = self.font_med.render("???", True, (80, 60, 100))
                desc_t = self.font_small.render("Secret achievement", True, (60, 50, 80))
            else:
                name_t = self.font_med.render(adata["name"], True, WHITE if unlocked else (80,70,90))
                desc_t = self.font_small.render(adata["desc"], True,
                                                (180,160,200) if unlocked else (80,70,90))
            surface.blit(name_t, (x+52, y+12))
            surface.blit(desc_t, (x+52, y+32))

            if unlocked:
                check = self.font_med.render("✓", True, NEON_GREEN)
                surface.blit(check, (x + card_w - 24, y + 8))

        surface.set_clip(clip)
        self.back_btn.draw(surface, game_time)
