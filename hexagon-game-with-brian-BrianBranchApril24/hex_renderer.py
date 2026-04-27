import pygame
import math

def hex_vertices(x, y, radius, rotation=0):
    """Calculates the 6 points of a hexagon."""
    points = []
    for i in range(6):
        angle_deg = 60 * i - 30 + math.degrees(rotation)
        angle_rad = math.pi / 180 * angle_deg
        px = x + radius * math.cos(angle_rad)
        py = y + radius * math.sin(angle_rad)
        points.append((px, py))
    return points

def draw_hex_glow(surface, x, y, radius, color, rotation=0):
    """Draw a soft glow behind the hex."""
    glow_surf = pygame.Surface((int(radius * 2.5), int(radius * 2.5)), pygame.SRCALPHA)
    glow_col = (*color, 80)
    pygame.draw.circle(glow_surf, glow_col, (int(radius * 1.25), int(radius * 1.25)), int(radius * 0.8))
    surface.blit(glow_surf, (int(x - radius * 1.25), int(y - radius * 1.25)), special_flags=pygame.BLEND_ALPHA_SDL2)

def draw_hex(surface, x, y, skin=None, radius=30, rotation=0, 
             color=(0, 255, 255), pulse_t=0, draw_sockets=False, 
             socket_states=None, width=0, **kwargs):
    """Standard hex drawing used by player and enemies."""
    points = hex_vertices(x, y, radius, rotation)
    if skin:
        pygame.draw.polygon(surface, skin.get("fill", color), points, width=width or 0)
        pygame.draw.polygon(surface, skin.get("border", color), points, width=2)
    else:
        pygame.draw.polygon(surface, color, points, width=width or 2)
    
    if draw_sockets and socket_states:
        socket_pts = hex_socket_positions(x, y, radius, rotation)
        for i, (sp, filled) in enumerate(zip(socket_pts, socket_states)):
            socket_color = (100, 255, 100) if filled else (50, 50, 50)
            pygame.draw.circle(surface, socket_color, (int(sp[0]), int(sp[1])), 6)

def draw_hex_preview(surface, x, y, skin, radius=40, alpha=1.0, **kwargs):
    """Used for the menu and customization previews."""
    draw_hex(surface, x, y, skin=skin, radius=radius, width=0)
    draw_hex(surface, x, y, skin=skin, radius=radius, width=3)

def hex_socket_positions(x, y, radius, rotation=0):
    """Calculates where the 'body parts' should attach."""
    return hex_vertices(x, y, radius * 0.8, rotation)