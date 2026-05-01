import pygame
import random
import math
from core.utils import draw_glow_circle, pulse_value

# Weather types and their effects on the player
WEATHER_TYPES = {
    "clear":      {"duration": (20, 40), "effect": None,              "label": ""},
    "sandstorm":  {"duration": (12, 22), "effect": "slow",            "label": "SANDSTORM",   "color": (200, 140, 40)},
    "lightning":  {"duration": (8,  16), "effect": "shock_random",    "label": "LIGHTNING",   "color": (180, 80, 255)},
    "heatwave":   {"duration": (10, 20), "effect": "dot",             "label": "HEAT WAVE",   "color": (255, 80, 0)},
    "void_rain":  {"duration": (10, 18), "effect": "vision_blur",     "label": "VOID RAIN",   "color": (0, 180, 255)},
    "spore_cloud":{"duration": (8,  14), "effect": "genome_drain",    "label": "SPORE CLOUD", "color": (120, 255, 60)},
}

# Which weather can appear per biome
BIOME_WEATHER = {
    "membrane":    ["clear", "clear", "sandstorm", "heatwave"],
    "vein":        ["clear", "void_rain", "lightning", "sandstorm"],
    "cortex":      ["clear", "lightning", "lightning", "spore_cloud"],
    "void_stomach":["clear", "void_rain", "spore_cloud", "heatwave"],
    "titan_core":  ["sandstorm", "lightning", "heatwave", "lightning"],
}


class WeatherSystem:
    def __init__(self, biome_key):
        self.biome_key = biome_key
        self.current = "clear"
        self.timer = random.uniform(10, 20)  # time until first weather
        self.duration = 0.0
        self.particles = []
        self.lightning_flash = 0.0
        self.lightning_strikes = []  # [(x, y, timer)]
        self.warning_timer = 0.0
        self.warning_text = ""
        self.active = False

    def update(self, dt, game_time, player, world_size):
        self.timer -= dt
        if self.warning_timer > 0:
            self.warning_timer -= dt

        if self.timer <= 0:
            if self.active:
                self._end_weather(player)
            else:
                self._start_weather(player, world_size)

        if self.active:
            self.duration -= dt
            self._update_particles(dt, game_time, player, world_size)
            self._apply_effects(dt, player, world_size)
            if self.duration <= 0:
                self.timer = random.uniform(15, 35)
                self._end_weather(player)

        # Update lightning flashes
        self.lightning_flash = max(0, self.lightning_flash - dt * 4)
        self.lightning_strikes = [(x, y, t - dt) for x, y, t in self.lightning_strikes if t > 0]

        # Update particles
        for p in self.particles:
            p["life"] -= dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
        self.particles = [p for p in self.particles if p["life"] > 0]

    def _start_weather(self, player, world_size):
        pool = BIOME_WEATHER.get(self.biome_key, ["clear"])
        self.current = random.choice(pool)
        if self.current == "clear":
            self.timer = random.uniform(15, 30)
            return
        wdata = WEATHER_TYPES[self.current]
        lo, hi = wdata["duration"]
        self.duration = random.uniform(lo, hi)
        self.active = True
        self.warning_timer = 3.0
        self.warning_text = f"WARNING: {wdata['label']} INCOMING!"
        self._spawn_particles(world_size)

    def _end_weather(self, player):
        self.active = False
        self.current = "clear"
        self.particles = []
        self.warning_text = ""

    def _spawn_particles(self, world_size):
        self.particles = []
        if self.current == "sandstorm":
            for _ in range(300):
                self.particles.append({
                    "x": random.uniform(0, world_size),
                    "y": random.uniform(0, world_size),
                    "vx": random.uniform(180, 320),
                    "vy": random.uniform(-30, 30),
                    "life": random.uniform(1.0, 3.0),
                    "max_life": 3.0,
                    "r": random.uniform(1, 4),
                    "color": (random.randint(180, 220), random.randint(120, 160), random.randint(30, 60)),
                })
        elif self.current == "void_rain":
            for _ in range(200):
                self.particles.append({
                    "x": random.uniform(0, world_size),
                    "y": random.uniform(0, world_size),
                    "vx": random.uniform(-20, 20),
                    "vy": random.uniform(200, 350),
                    "life": random.uniform(0.5, 1.5),
                    "max_life": 1.5,
                    "r": random.uniform(1, 3),
                    "color": (0, random.randint(140, 220), random.randint(200, 255)),
                })
        elif self.current == "spore_cloud":
            for _ in range(150):
                angle = random.uniform(0, math.pi * 2)
                spd = random.uniform(20, 80)
                self.particles.append({
                    "x": random.uniform(0, world_size),
                    "y": random.uniform(0, world_size),
                    "vx": math.cos(angle) * spd,
                    "vy": math.sin(angle) * spd,
                    "life": random.uniform(2.0, 5.0),
                    "max_life": 5.0,
                    "r": random.uniform(3, 8),
                    "color": (random.randint(80, 140), random.randint(200, 255), random.randint(40, 80)),
                })

    def _update_particles(self, dt, game_time, player, world_size):
        # Respawn particles to keep density
        if self.current == "sandstorm" and len(self.particles) < 200:
            for _ in range(5):
                self.particles.append({
                    "x": random.uniform(0, world_size),
                    "y": random.uniform(0, world_size),
                    "vx": random.uniform(180, 320),
                    "vy": random.uniform(-30, 30),
                    "life": random.uniform(1.0, 3.0),
                    "max_life": 3.0,
                    "r": random.uniform(1, 4),
                    "color": (random.randint(180, 220), random.randint(120, 160), random.randint(30, 60)),
                })
        elif self.current == "void_rain" and len(self.particles) < 150:
            for _ in range(4):
                self.particles.append({
                    "x": random.uniform(0, world_size),
                    "y": 0,
                    "vx": random.uniform(-20, 20),
                    "vy": random.uniform(200, 350),
                    "life": random.uniform(0.5, 1.5),
                    "max_life": 1.5,
                    "r": random.uniform(1, 3),
                    "color": (0, random.randint(140, 220), random.randint(200, 255)),
                })

    def _apply_effects(self, dt, player, world_size):
        if not player or not player.alive:
            return
        if self.current == "sandstorm":
            # Slow the player
            player.body.velocity = (
                player.body.velocity.x * 0.92,
                player.body.velocity.y * 0.92,
            )
            # Occasional sand damage
            if random.random() < 0.02:
                player.take_damage(3)
        elif self.current == "lightning":
            # Random lightning strikes near player
            if random.random() < 0.015:
                cx, cy = player.get_center()
                sx = cx + random.uniform(-400, 400)
                sy = cy + random.uniform(-400, 400)
                self.lightning_strikes.append((sx, sy, 0.4))
                self.lightning_flash = 0.3
                # If strike is close, damage player
                if math.hypot(sx - cx, sy - cy) < 120:
                    player.take_damage(20)
        elif self.current == "heatwave":
            if random.random() < 0.03:
                player.take_damage(2)
        elif self.current == "spore_cloud":
            if random.random() < 0.025:
                player.take_damage(4)

    def draw(self, surface, camera, game_time, screen_w, screen_h):
        if not self.active and not self.lightning_flash:
            return

        # Lightning flash overlay
        if self.lightning_flash > 0:
            flash = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
            flash.fill((200, 150, 255, int(self.lightning_flash * 120)))
            surface.blit(flash, (0, 0))

        # Lightning bolt visuals
        for sx, sy, t in self.lightning_strikes:
            sp = camera.world_to_screen(sx, sy)
            draw_glow_circle(surface, (200, 100, 255), sp, int(30 * camera.zoom), alpha=80, layers=3)
            # Draw jagged bolt from top of screen
            self._draw_bolt(surface, (sp[0], 0), sp, (220, 150, 255))

        if not self.active:
            return

        # Weather tint overlay
        wdata = WEATHER_TYPES.get(self.current, {})
        tint_color = wdata.get("color", (255, 255, 255))
        tint = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        tint.fill((*tint_color, 18))
        surface.blit(tint, (0, 0))

        # Draw particles
        for p in self.particles:
            sp = camera.world_to_screen(p["x"], p["y"])
            if -20 < sp[0] < screen_w + 20 and -20 < sp[1] < screen_h + 20:
                alpha = int(200 * (p["life"] / p["max_life"]))
                r = max(1, int(p["r"] * camera.zoom))
                s = pygame.Surface((r * 2 + 1, r * 2 + 1), pygame.SRCALPHA)
                s.fill((*p["color"], alpha))
                surface.blit(s, (sp[0] - r, sp[1] - r))

        # Sandstorm: draw streaks
        if self.current == "sandstorm":
            for p in self.particles[:80]:
                sp = camera.world_to_screen(p["x"], p["y"])
                ep = (int(sp[0] - p["vx"] * 0.04 * camera.zoom),
                      int(sp[1] - p["vy"] * 0.04 * camera.zoom))
                alpha = int(160 * (p["life"] / p["max_life"]))
                c = (*p["color"], alpha)
                s = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
                pygame.draw.line(s, c, sp, ep, max(1, int(p["r"] * camera.zoom)))
                surface.blit(s, (0, 0))

    def _draw_bolt(self, surface, start, end, color):
        """Draw a jagged lightning bolt."""
        points = [start]
        steps = 8
        for i in range(1, steps):
            t = i / steps
            mx = start[0] + (end[0] - start[0]) * t + random.uniform(-20, 20)
            my = start[1] + (end[1] - start[1]) * t + random.uniform(-10, 10)
            points.append((int(mx), int(my)))
        points.append(end)
        if len(points) >= 2:
            s = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            pygame.draw.lines(s, (*color, 180), False, points, 2)
            surface.blit(s, (0, 0))

    def draw_hud(self, surface, font, screen_w, screen_h, game_time):
        """Draw weather label and warning."""
        if self.warning_timer > 0 and self.warning_text:
            alpha = min(255, int(self.warning_timer * 120))
            t = font.render(self.warning_text, True, (255, 60, 60))
            t.set_alpha(alpha)
            surface.blit(t, (screen_w // 2 - t.get_width() // 2, screen_h // 2 - 120))

        if self.active:
            wdata = WEATHER_TYPES.get(self.current, {})
            label = wdata.get("label", "")
            color = wdata.get("color", (255, 255, 255))
            if label:
                pulse = pulse_value(game_time, speed=2.0, lo=0.6, hi=1.0)
                c = tuple(int(v * pulse) for v in color)
                t = font.render(f"⚠ {label}", True, c)
                surface.blit(t, (screen_w // 2 - t.get_width() // 2, 16))
