import pygame
import math
import random

def lerp(a, b, t):
    return a + (b - a) * t

def lerp_color(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))

def clamp(val, lo, hi):
    return max(lo, min(hi, val))

def distance(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])

def normalize(v):
    mag = math.hypot(v[0], v[1])
    if mag == 0:
        return (0, 0)
    return (v[0] / mag, v[1] / mag)

def angle_to(origin, target):
    dx, dy = target[0] - origin[0], target[1] - origin[1]
    return math.atan2(dy, dx)

def hex_to_pixel(col, row, radius, offset=(0, 0)):
    """Offset hex grid (pointy-top) to pixel coords."""
    x = radius * math.sqrt(3) * (col + 0.5 * (row % 2))
    y = radius * 1.5 * row
    return (x + offset[0], y + offset[1])

def draw_glow_circle(surface, color, pos, radius, alpha=80, layers=4):
    """Draw a soft glowing circle using layered transparent surfaces."""
    for i in range(layers, 0, -1):
        r = int(radius * (1 + i * 0.4))
        a = int(alpha / (i + 1))
        glow_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        c = (*color[:3], a)
        pygame.draw.circle(glow_surf, c, (r, r), r)
        surface.blit(glow_surf, (pos[0] - r, pos[1] - r), special_flags=pygame.BLEND_RGBA_ADD)

def draw_glow_rect(surface, color, rect, alpha=60, radius=8):
    """Draw a glowing rounded rectangle."""
    s = pygame.Surface((rect.width + 20, rect.height + 20), pygame.SRCALPHA)
    c = (*color[:3], alpha)
    pygame.draw.rect(s, c, s.get_rect().inflate(-10, -10), border_radius=radius + 4)
    surface.blit(s, (rect.x - 10, rect.y - 10), special_flags=pygame.BLEND_RGBA_ADD)

def draw_hex(surface, color, center, radius, width=0):
    points = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        points.append((
            center[0] + radius * math.cos(angle),
            center[1] + radius * math.sin(angle)
        ))
    pygame.draw.polygon(surface, color, points, width)
    return points

def pulse_value(t, speed=2.0, lo=0.7, hi=1.0):
    """Returns a pulsing float between lo and hi."""
    return lo + (hi - lo) * (0.5 + 0.5 * math.sin(t * speed))

def random_color_variation(base_color, variance=30):
    return tuple(clamp(c + random.randint(-variance, variance), 0, 255) for c in base_color[:3])

def screen_shake_offset(intensity, decay):
    if intensity <= 0:
        return (0, 0)
    return (random.uniform(-intensity, intensity), random.uniform(-intensity, intensity))
