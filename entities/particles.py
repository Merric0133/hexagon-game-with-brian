import pygame
import random
import math
from core.utils import draw_glow_circle

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit(self, pos, color, count=8, speed=80, radius_range=(2,6),
             life_range=(0.3, 0.9), spread=math.pi*2, direction=0.0, glow=True):
        for _ in range(count):
            angle = direction + random.uniform(-spread/2, spread/2)
            spd = random.uniform(speed * 0.5, speed)
            r = random.uniform(*radius_range)
            life = random.uniform(*life_range)
            self.particles.append({
                "pos": [pos[0] + random.uniform(-4,4), pos[1] + random.uniform(-4,4)],
                "vel": [math.cos(angle)*spd, math.sin(angle)*spd],
                "color": color,
                "radius": r,
                "life": life,
                "max_life": life,
                "glow": glow,
            })

    def emit_explosion(self, pos, color, count=24):
        self.emit(pos, color, count=count, speed=200, radius_range=(3,8),
                  life_range=(0.4, 1.2), glow=True)

    def emit_zap(self, pos, color=(180, 80, 255), count=12):
        self.emit(pos, color, count=count, speed=150, radius_range=(1,4),
                  life_range=(0.2, 0.6), glow=True)

    def emit_cell_death(self, pos, color, count=16):
        self.emit(pos, color, count=count, speed=120, radius_range=(2,7),
                  life_range=(0.5, 1.0), glow=True)

    def emit_xp(self, pos, count=6):
        self.emit(pos, (0, 255, 180), count=count, speed=60, radius_range=(2,4),
                  life_range=(0.6, 1.2), glow=True)

    def emit_levelup(self, pos):
        self.emit(pos, (255, 220, 0), count=40, speed=250, radius_range=(3,9),
                  life_range=(0.6, 1.5), glow=True)
        self.emit(pos, (255, 255, 255), count=20, speed=180, radius_range=(2,5),
                  life_range=(0.4, 1.0), glow=True)

    def update(self, dt):
        for p in self.particles:
            p["life"] -= dt
            p["pos"][0] += p["vel"][0] * dt
            p["pos"][1] += p["vel"][1] * dt
            p["vel"][0] *= 0.95
            p["vel"][1] *= 0.95
        self.particles = [p for p in self.particles if p["life"] > 0]

    def draw(self, surface, camera):
        for p in self.particles:
            sp = camera.world_to_screen(*p["pos"])
            alpha = int(255 * (p["life"] / p["max_life"]))
            r = max(1, int(p["radius"] * camera.zoom))
            if p["glow"]:
                draw_glow_circle(surface, p["color"], sp, r, alpha=alpha//2, layers=2)
            c = (*p["color"][:3], alpha)
            s = pygame.Surface((r*2+1, r*2+1), pygame.SRCALPHA)
            pygame.draw.circle(s, c, (r, r), r)
            surface.blit(s, (sp[0]-r, sp[1]-r))
