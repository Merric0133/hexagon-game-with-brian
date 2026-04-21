import pygame
import random

def draw_starfield(surface, time_offset, vertical_offset, stars):
    """Draws and animates stars."""
    if not isinstance(stars, (list, tuple)):
        return
    for star in stars:
        x, y, radius = star[0], (star[1] + vertical_offset) % 720, star[2]
        pygame.draw.circle(surface, (255, 255, 255), (int(x), int(y)), int(radius))

def generate_stars(count):
    return [[random.randint(0, 1280), random.randint(0, 720), random.randint(1, 3)] for _ in range(count)]

def render_text_centered(surface, text, size, color, y, font_name="Arial"):
    font = pygame.font.SysFont(font_name, size, bold=True)
    # Outline for glow
    outline_color = (color[0]//4, color[1]//4, color[2]//4)
    for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1)]:
        outline_surf = font.render(text, True, outline_color)
        outline_rect = outline_surf.get_rect(center=(640 + dx, y + dy))
        surface.blit(outline_surf, outline_rect)
    text_surf = font.render(text, True, color)
    text_rect = text_surf.get_rect(center=(640, y))
    surface.blit(text_surf, text_rect)

def draw_panel(surface, rect, title=None):
    from constants import COLOR_BG_PANEL, COLOR_BORDER, COLOR_GLOW, COLOR_SHADOW
    # Shadow
    shadow_rect = pygame.Rect(rect.x + 4, rect.y + 4, rect.w, rect.h)
    shadow_surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    pygame.draw.rect(shadow_surf, COLOR_SHADOW, shadow_surf.get_rect(), border_radius=12)
    surface.blit(shadow_surf, (shadow_rect.x, shadow_rect.y))
    
    # Glow
    glow_surf = pygame.Surface((rect.w + 20, rect.h + 20), pygame.SRCALPHA)
    pygame.draw.rect(glow_surf, COLOR_GLOW, glow_surf.get_rect(), border_radius=12)
    surface.blit(glow_surf, (rect.x - 10, rect.y - 10))
    
    # Main panel with gradient
    panel_surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    for i in range(10):
        alpha = 255 - i * 20
        color = (COLOR_BG_PANEL[0], COLOR_BG_PANEL[1], COLOR_BG_PANEL[2], alpha)
        pygame.draw.rect(panel_surf, color, (0, i*2, rect.w, 2), border_radius=8 if i == 0 else 0)
    surface.blit(panel_surf, (rect.x, rect.y))
    
    # Border
    pygame.draw.rect(surface, COLOR_BORDER, rect, 2, border_radius=8)
    
    if title:
        font = pygame.font.SysFont("Arial", 18, bold=True)
        title_surf = font.render(title, True, COLOR_TEXT)
        surface.blit(title_surf, (rect.x + 10, rect.y + 5))

def draw_bar(surface, x, y, w, h, current, max_val, fill_color=(0, 255, 0)):
    """Draw a progress/stat bar."""
    from constants import COLOR_GLOW
    # Background
    pygame.draw.rect(surface, (15, 15, 25), (x, y, w, h), border_radius=4)
    # Fill
    if max_val > 0:
        fill_w = int(w * (current / max_val))
        fill_surf = pygame.Surface((fill_w, h), pygame.SRCALPHA)
        for i in range(5):
            alpha = 255 - i * 40
            color = (*fill_color, alpha)
            pygame.draw.rect(fill_surf, color, (0, i*2, fill_w, 2), border_radius=4 if i == 0 else 0)
        surface.blit(fill_surf, (x, y))
        # Glow on fill
        if fill_w > 0:
            glow_surf = pygame.Surface((fill_w + 10, h + 10), pygame.SRCALPHA)
            glow_color = (*fill_color[:3], 50)
            pygame.draw.rect(glow_surf, glow_color, glow_surf.get_rect(), border_radius=6)
            surface.blit(glow_surf, (x - 5, y - 5))
    # Border
    pygame.draw.rect(surface, (100, 150, 200), (x, y, w, h), 1, border_radius=4)

def draw_rarity_badge(surface, x, y, rarity, font_size=14):
    from constants import RARITY_COLORS
    font = pygame.font.SysFont("Arial", font_size)
    badge = font.render(rarity.upper(), True, RARITY_COLORS.get(rarity, (200, 200, 200)))
    surface.blit(badge, (x, y))

def wrap_text(text, font, width):
    """Break text into lines to fit width."""
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        if font.size(test_line)[0] <= width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    return lines

def draw_world_grid(surface, camera):
    """Draw the world grid."""
    from constants import WORLD_WIDTH, WORLD_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT
    grid_size = 200
    for i in range(0, WORLD_WIDTH, grid_size):
        p1 = camera.world_to_screen(i, 0)
        p2 = camera.world_to_screen(i, WORLD_HEIGHT)
        pygame.draw.line(surface, (30, 30, 50), p1, p2, 1)
    for i in range(0, WORLD_HEIGHT, grid_size):
        p1 = camera.world_to_screen(0, i)
        p2 = camera.world_to_screen(WORLD_WIDTH, i)
        pygame.draw.line(surface, (30, 30, 50), p1, p2, 1)

class Button:
    def __init__(self, x, y, w, h, text, color, **kwargs):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.font_size = kwargs.get('font_size', 24)
        self.is_hovered = False
        self.hover_time = 0.0
        self.clicked = False

    def update(self, input_handler, dt):
        """Check if button was clicked. Returns True if clicked."""
        prev_hovered = self.is_hovered
        self.is_hovered = self.rect.collidepoint(input_handler.mouse_pos)
        if self.is_hovered:
            self.hover_time += dt
        else:
            self.hover_time = max(0, self.hover_time - dt * 2)
        
        clicked = self.is_hovered and input_handler.mouse_just_pressed(1)
        if clicked:
            self.clicked = True
        return clicked

    def draw(self, surface):
        from constants import COLOR_GLOW
        # Glow on hover
        if self.is_hovered:
            glow_intensity = min(1.0, self.hover_time * 5)
            glow_color = (COLOR_GLOW[0], COLOR_GLOW[1], COLOR_GLOW[2], int(COLOR_GLOW[3] * glow_intensity))
            glow_surf = pygame.Surface((self.rect.w + 20, self.rect.h + 20), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, glow_color, glow_surf.get_rect(), border_radius=12)
            surface.blit(glow_surf, (self.rect.x - 10, self.rect.y - 10))
        
        # Shadow
        shadow_color = (0, 0, 0, 80)
        shadow_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, shadow_color, shadow_surf.get_rect(), border_radius=8)
        surface.blit(shadow_surf, (self.rect.x + 3, self.rect.y + 3))
        
        # Main button with gradient
        button_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        base_color = self.color
        if self.is_hovered:
            base_color = tuple(min(255, c + 50) for c in self.color)
        for i in range(5):
            alpha = 255 - i * 30
            color = (*base_color, alpha)
            pygame.draw.rect(button_surf, color, (0, i*3, self.rect.w, 3), border_radius=8 if i == 0 else 0)
        surface.blit(button_surf, (self.rect.x, self.rect.y))
        
        # Border
        border_color = (150, 200, 255) if self.is_hovered else (100, 150, 200)
        pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=8)
        
        # Text
        font = pygame.font.SysFont("Arial", self.font_size, bold=True)
        text_color = (255, 255, 255) if not self.clicked else (200, 200, 200)
        label = font.render(self.text, True, text_color)
        surface.blit(label, (self.rect.centerx - label.get_width()//2, self.rect.centery - label.get_height()//2))
        
        if self.clicked:
            self.clicked = False