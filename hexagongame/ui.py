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
    font = pygame.font.SysFont(font_name, size)
    text_surf = font.render(text, True, color)
    text_rect = text_surf.get_rect(center=(640, y))
    surface.blit(text_surf, text_rect)

def draw_panel(surface, rect, title=None):
    from constants import COLOR_BG_PANEL, COLOR_BORDER
    pygame.draw.rect(surface, COLOR_BG_PANEL, rect, border_radius=8)
    pygame.draw.rect(surface, COLOR_BORDER, rect, 2, border_radius=8)

def draw_bar(surface, x, y, w, h, current, max_val, fill_color=(0, 255, 0)):
    """Draw a progress/stat bar."""
    pygame.draw.rect(surface, (30, 30, 40), (x, y, w, h))
    if max_val > 0:
        fill_w = int(w * (current / max_val))
        pygame.draw.rect(surface, fill_color, (x, y, fill_w, h))
    pygame.draw.rect(surface, (100, 100, 120), (x, y, w, h), 1)

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

    def update(self, input_handler, dt):
        """Check if button was clicked. Returns True if clicked."""
        self.is_hovered = self.rect.collidepoint(input_handler.mouse_pos)
        return self.is_hovered and input_handler.mouse_just_pressed(1)

    def draw(self, surface):
        draw_color = tuple(min(255, c + 30) for c in self.color) if self.is_hovered else self.color
        pygame.draw.rect(surface, (10, 10, 15), (self.rect.x+3, self.rect.y+3, self.rect.w, self.rect.h), border_radius=8)
        pygame.draw.rect(surface, draw_color, self.rect, border_radius=8)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 2, border_radius=8)
        font = pygame.font.SysFont("Arial", self.font_size, bold=True)
        label = font.render(self.text, True, (255, 255, 255))
        surface.blit(label, (self.rect.centerx - label.get_width()//2, self.rect.centery - label.get_height()//2))