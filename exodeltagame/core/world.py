import pygame
import pymunk
import random
import math
from core.utils import draw_glow_circle, draw_hex, pulse_value
from data.biomes_data import BIOMES
from entities.enemy import Enemy, ENEMY_ARCHETYPES
from core.weather import WeatherSystem

WORLD_SIZE = 4000

# Sandy exoplanet terrain colors
SAND_PALETTE = [
    (180, 120, 50), (200, 140, 60), (160, 100, 40),
    (220, 160, 70), (140, 90,  35), (210, 150, 65),
]
ROCK_PALETTE = [
    (90, 70, 55), (110, 85, 65), (75, 58, 45), (130, 100, 75),
]
CRYSTAL_PALETTE = [
    (0, 200, 180), (180, 60, 255), (255, 120, 0), (0, 180, 255),
]


class TerrainFeature:
    """Static decorative terrain: dunes, rocks, crystals, craters."""
    def __init__(self, ftype, pos, size, color, glow=None, angle=0.0):
        self.ftype = ftype   # "dune", "rock", "crystal", "crater", "ruin"
        self.pos = pos
        self.size = size
        self.color = color
        self.glow = glow
        self.angle = angle
        self.phase = random.uniform(0, math.pi * 2)

    def draw(self, surface, camera, game_time):
        sp = camera.world_to_screen(*self.pos)
        r = max(2, int(self.size * camera.zoom))
        # Cull off-screen
        sw, sh = surface.get_size()
        if sp[0] < -r*3 or sp[0] > sw+r*3 or sp[1] < -r*3 or sp[1] > sh+r*3:
            return

        if self.ftype == "dune":
            self._draw_dune(surface, sp, r, game_time)
        elif self.ftype == "rock":
            self._draw_rock(surface, sp, r)
        elif self.ftype == "crystal":
            self._draw_crystal(surface, sp, r, game_time)
        elif self.ftype == "crater":
            self._draw_crater(surface, sp, r)
        elif self.ftype == "ruin":
            self._draw_ruin(surface, sp, r, game_time)

    def _draw_dune(self, surface, sp, r, game_time):
        # Elliptical sand dune with subtle shimmer
        s = pygame.Surface((r*4, r*2), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (*self.color, 160), (0, 0, r*4, r*2))
        # Highlight ridge
        ridge_c = tuple(min(255, c+40) for c in self.color)
        pygame.draw.ellipse(s, (*ridge_c, 80), (r//2, r//4, r*3, r//2))
        surface.blit(s, (sp[0]-r*2, sp[1]-r))

    def _draw_rock(self, surface, sp, r):
        # Irregular polygon rock
        points = []
        sides = random.randint(5, 8)
        for i in range(sides):
            angle = self.angle + (2*math.pi/sides)*i
            dist = r * random.uniform(0.7, 1.0)
            points.append((sp[0]+math.cos(angle)*dist, sp[1]+math.sin(angle)*dist))
        if len(points) >= 3:
            pygame.draw.polygon(surface, self.color, points)
            shadow = tuple(max(0, c-40) for c in self.color)
            pygame.draw.polygon(surface, shadow, points, width=2)

    def _draw_crystal(self, surface, sp, r, game_time):
        # Glowing hexagonal crystal
        pulse = pulse_value(game_time + self.phase, speed=1.5, lo=0.6, hi=1.0)
        if self.glow:
            draw_glow_circle(surface, self.glow, sp, int(r*pulse*1.4), alpha=50, layers=2)
        draw_hex(surface, self.color, sp, int(r*pulse))
        draw_hex(surface, self.glow or self.color, sp, int(r*pulse), width=1)

    def _draw_crater(self, surface, sp, r):
        # Dark crater with rim
        s = pygame.Surface((r*3, r*3), pygame.SRCALPHA)
        cx, cy = r*3//2, r*3//2
        pygame.draw.circle(s, (20, 12, 8, 180), (cx, cy), r)
        rim_c = tuple(min(255, c+30) for c in self.color)
        pygame.draw.circle(s, (*rim_c, 120), (cx, cy), r, width=max(2, r//5))
        surface.blit(s, (sp[0]-r*3//2, sp[1]-r*3//2))

    def _draw_ruin(self, surface, sp, r, game_time):
        # Ancient alien ruin — glowing broken structure
        pulse = pulse_value(game_time + self.phase, speed=0.8, lo=0.4, hi=0.9)
        if self.glow:
            draw_glow_circle(surface, self.glow, sp, int(r*1.2), alpha=int(40*pulse), layers=2)
        # Draw broken pillars
        for i in range(3):
            angle = self.angle + i * (2*math.pi/3)
            px = sp[0] + math.cos(angle) * r * 0.7
            py = sp[1] + math.sin(angle) * r * 0.7
            h = int(r * random.uniform(0.5, 1.2))
            w = max(3, r//3)
            pygame.draw.rect(surface, self.color,
                             (int(px)-w//2, int(py)-h//2, w, h), border_radius=2)
            if self.glow:
                draw_glow_circle(surface, self.glow, (int(px), int(py)-h//2),
                                 max(2, w), alpha=int(60*pulse), layers=1)


class BackgroundLayer:
    def __init__(self, biome_key):
        self.biome = BIOMES[biome_key]
        self.biome_key = biome_key
        self.terrain = []
        self.stars = []
        self.sand_drifts = []
        self.ambient_particles = []  # Biome-specific ambient particles
        self._generate_terrain()
        self._generate_stars()
        self._generate_sand_drifts()
        self._generate_ambient_particles()
    
    def _generate_boss_scenery(self, boss_pos=None):
        """Generate ominous scenery around the boss arena."""
        if boss_pos is None:
            boss_pos = (WORLD_SIZE / 2, WORLD_SIZE / 2)
        
        center_x, center_y = boss_pos
        
        # Massive dark crystals forming a ring around the arena
        for i in range(12):
            angle = (i / 12) * math.pi * 2
            dist = 350 + random.uniform(-50, 50)
            x = center_x + math.cos(angle) * dist
            y = center_y + math.sin(angle) * dist
            size = random.uniform(60, 100)
            self.terrain.append(TerrainFeature(
                "crystal", (x, y), size, 
                (80, 0, 40), glow=(255, 0, 60)
            ))
        
        # Ancient ruins forming inner circle
        for i in range(8):
            angle = (i / 8) * math.pi * 2 + 0.2
            dist = 280
            x = center_x + math.cos(angle) * dist
            y = center_y + math.sin(angle) * dist
            size = random.uniform(40, 70)
            self.terrain.append(TerrainFeature(
                "ruin", (x, y), size,
                (60, 20, 20), glow=(255, 40, 0),
                angle=angle + math.pi/2
            ))
        
        # Scattered bones/remains
        for _ in range(20):
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(250, 450)
            x = center_x + math.cos(angle) * dist
            y = center_y + math.sin(angle) * dist
            size = random.uniform(15, 35)
            self.terrain.append(TerrainFeature(
                "rock", (x, y), size,
                (40, 30, 30), angle=random.uniform(0, math.pi*2)
            ))
        
        # Pulsing energy craters
        for i in range(6):
            angle = (i / 6) * math.pi * 2 + 0.5
            dist = 320
            x = center_x + math.cos(angle) * dist
            y = center_y + math.sin(angle) * dist
            size = random.uniform(50, 80)
            self.terrain.append(TerrainFeature(
                "crater", (x, y), size,
                (60, 10, 10)
            ))
        
        # Re-sort after adding boss scenery
        self.terrain.sort(key=lambda t: t.pos[1])

    def _generate_terrain(self):
        # Sand dunes — lots of them, layered
        for _ in range(80):
            pos = (random.uniform(0, WORLD_SIZE), random.uniform(0, WORLD_SIZE))
            size = random.uniform(30, 120)
            color = random.choice(SAND_PALETTE)
            self.terrain.append(TerrainFeature("dune", pos, size, color))

        # Rocks scattered around
        for _ in range(60):
            pos = (random.uniform(0, WORLD_SIZE), random.uniform(0, WORLD_SIZE))
            size = random.uniform(10, 45)
            color = random.choice(ROCK_PALETTE)
            self.terrain.append(TerrainFeature("rock", pos, size, color,
                                               angle=random.uniform(0, math.pi*2)))

        # Glowing alien crystals
        for _ in range(40):
            pos = (random.uniform(0, WORLD_SIZE), random.uniform(0, WORLD_SIZE))
            size = random.uniform(8, 28)
            color = random.choice(CRYSTAL_PALETTE)
            glow = tuple(min(255, c+60) for c in color)
            self.terrain.append(TerrainFeature("crystal", pos, size, color, glow=glow))

        # Impact craters
        for _ in range(25):
            pos = (random.uniform(0, WORLD_SIZE), random.uniform(0, WORLD_SIZE))
            size = random.uniform(25, 80)
            color = random.choice(SAND_PALETTE)
            self.terrain.append(TerrainFeature("crater", pos, size, color))

        # Ancient alien ruins
        for _ in range(12):
            pos = (random.uniform(0, WORLD_SIZE), random.uniform(0, WORLD_SIZE))
            size = random.uniform(20, 50)
            color = random.choice(ROCK_PALETTE)
            glow = random.choice(CRYSTAL_PALETTE)
            self.terrain.append(TerrainFeature("ruin", pos, size, color, glow=glow,
                                               angle=random.uniform(0, math.pi*2)))

        # Sort by y for painter's algorithm (back to front)
        self.terrain.sort(key=lambda t: t.pos[1])
        
        # Add boss arena scenery
        self._generate_boss_scenery()

    def _generate_stars(self):
        # Distant stars/moons in the sky layer (very slow parallax)
        for _ in range(60):
            self.stars.append({
                "pos": (random.uniform(0, WORLD_SIZE), random.uniform(0, WORLD_SIZE)),
                "r": random.uniform(1, 5),
                "color": random.choice([(255,220,180),(200,180,255),(180,220,255),(255,200,100)]),
                "phase": random.uniform(0, math.pi*2),
                "parallax": 0.05,  # moves very slowly with camera
            })

    def _generate_sand_drifts(self):
        # Animated sand drift lines
        for _ in range(40):
            self.sand_drifts.append({
                "x": random.uniform(0, WORLD_SIZE),
                "y": random.uniform(0, WORLD_SIZE),
                "length": random.uniform(40, 160),
                "alpha": random.randint(20, 60),
                "color": random.choice(SAND_PALETTE),
                "speed": random.uniform(0.3, 1.2),
                "phase": random.uniform(0, math.pi*2),
            })
    
    def _generate_ambient_particles(self):
        """Generate biome-specific ambient particles for visual distinction."""
        theme = self.biome.get("ambient_particles", "floating_cells")
        
        if theme == "floating_cells":  # Membrane biome
            for _ in range(50):
                self.ambient_particles.append({
                    "type": "cell",
                    "pos": [random.uniform(0, WORLD_SIZE), random.uniform(0, WORLD_SIZE)],
                    "vel": [random.uniform(-10, 10), random.uniform(-10, 10)],
                    "size": random.uniform(3, 8),
                    "color": self.biome["particle_color"],
                    "phase": random.uniform(0, math.pi*2),
                })
        
        elif theme == "bubbles":  # Vein biome
            for _ in range(60):
                self.ambient_particles.append({
                    "type": "bubble",
                    "pos": [random.uniform(0, WORLD_SIZE), random.uniform(0, WORLD_SIZE)],
                    "vel": [random.uniform(-5, 5), random.uniform(-30, -10)],  # Float upward
                    "size": random.uniform(4, 12),
                    "color": self.biome["particle_color"],
                    "phase": random.uniform(0, math.pi*2),
                })
        
        elif theme == "sparks":  # Cortex biome
            for _ in range(70):
                self.ambient_particles.append({
                    "type": "spark",
                    "pos": [random.uniform(0, WORLD_SIZE), random.uniform(0, WORLD_SIZE)],
                    "vel": [random.uniform(-50, 50), random.uniform(-50, 50)],
                    "size": random.uniform(2, 5),
                    "color": self.biome["particle_color"],
                    "phase": random.uniform(0, math.pi*2),
                    "life": random.uniform(0.5, 2.0),
                })
        
        elif theme == "acid_drops":  # Void Stomach biome
            for _ in range(45):
                self.ambient_particles.append({
                    "type": "acid",
                    "pos": [random.uniform(0, WORLD_SIZE), random.uniform(0, WORLD_SIZE)],
                    "vel": [random.uniform(-3, 3), random.uniform(20, 40)],  # Drip downward
                    "size": random.uniform(3, 7),
                    "color": self.biome["particle_color"],
                    "phase": random.uniform(0, math.pi*2),
                })
        
        elif theme == "embers":  # Titan Core biome
            for _ in range(80):
                self.ambient_particles.append({
                    "type": "ember",
                    "pos": [random.uniform(0, WORLD_SIZE), random.uniform(0, WORLD_SIZE)],
                    "vel": [random.uniform(-15, 15), random.uniform(-40, -20)],  # Rise like fire
                    "size": random.uniform(2, 6),
                    "color": self.biome["particle_color"],
                    "phase": random.uniform(0, math.pi*2),
                    "life": random.uniform(1.0, 3.0),
                })

    def draw(self, surface, camera, game_time):
        # Sky gradient background
        biome = self.biome
        bg = biome["bg_color"]
        surface.fill(bg)

        # Distant stars (deep parallax)
        for star in self.stars:
            # Parallax: stars move at fraction of camera speed
            sx = (star["pos"][0] - camera.x * star["parallax"]) * camera.zoom
            sy = (star["pos"][1] - camera.y * star["parallax"]) * camera.zoom
            pulse = pulse_value(game_time + star["phase"], speed=0.8, lo=0.4, hi=1.0)
            r = max(1, int(star["r"] * pulse))
            draw_glow_circle(surface, star["color"], (int(sx), int(sy)), r, alpha=60, layers=1)

        # Horizon glow — warm orange/amber at bottom of sky
        horizon = pygame.Surface((surface.get_width(), 80), pygame.SRCALPHA)
        for i in range(80):
            alpha = int(40 * (1 - i/80))
            pygame.draw.line(horizon, (*biome["accent"], alpha), (0, i), (surface.get_width(), i))
        surface.blit(horizon, (0, surface.get_height() - 80))

        # Animated sand drift lines
        for drift in self.sand_drifts:
            sp = camera.world_to_screen(drift["x"], drift["y"])
            pulse = pulse_value(game_time + drift["phase"], speed=drift["speed"], lo=0.3, hi=1.0)
            alpha = int(drift["alpha"] * pulse)
            length = int(drift["length"] * camera.zoom)
            if length < 2:
                continue
            s = pygame.Surface((length + 4, 4), pygame.SRCALPHA)
            s.fill((*drift["color"], alpha))
            surface.blit(s, (sp[0], sp[1]))

        # Biome-specific ambient particles
        self._draw_ambient_particles(surface, camera, game_time)

        # Terrain features
        for feature in self.terrain:
            feature.draw(surface, camera, game_time)

        # Biome accent orbs (bioluminescent ground glow)
        # These are drawn sparsely so they don't clutter
        accent = biome["accent"]
        glow   = biome["glow"]
    
    def _draw_ambient_particles(self, surface, camera, game_time):
        """Draw biome-specific ambient particles."""
        for p in self.ambient_particles:
            # Update particle position
            p["pos"][0] += p["vel"][0] * 0.016  # Approximate dt
            p["pos"][1] += p["vel"][1] * 0.016
            
            # Wrap around world
            if p["pos"][0] < 0: p["pos"][0] += WORLD_SIZE
            if p["pos"][0] > WORLD_SIZE: p["pos"][0] -= WORLD_SIZE
            if p["pos"][1] < 0: p["pos"][1] += WORLD_SIZE
            if p["pos"][1] > WORLD_SIZE: p["pos"][1] -= WORLD_SIZE
            
            sp = camera.world_to_screen(p["pos"][0], p["pos"][1])
            sw, sh = surface.get_size()
            if sp[0] < -50 or sp[0] > sw+50 or sp[1] < -50 or sp[1] > sh+50:
                continue
            
            ptype = p["type"]
            size = max(1, int(p["size"] * camera.zoom))
            
            if ptype == "cell":
                pulse = pulse_value(game_time + p["phase"], speed=1.0, lo=0.6, hi=1.0)
                alpha = int(80 * pulse)
                draw_glow_circle(surface, p["color"], sp, size, alpha=alpha, layers=1)
            
            elif ptype == "bubble":
                pulse = pulse_value(game_time + p["phase"], speed=1.5, lo=0.5, hi=1.0)
                alpha = int(60 * pulse)
                pygame.draw.circle(surface, (*p["color"], alpha), sp, size, width=1)
            
            elif ptype == "spark":
                alpha = int(200 * (p.get("life", 1.0) / 2.0))
                pygame.draw.circle(surface, (*p["color"], alpha), sp, size)
                if "life" in p:
                    p["life"] -= 0.016
                    if p["life"] <= 0:
                        p["life"] = random.uniform(0.5, 2.0)
                        p["pos"] = [random.uniform(0, WORLD_SIZE), random.uniform(0, WORLD_SIZE)]
            
            elif ptype == "acid":
                alpha = int(100)
                pygame.draw.circle(surface, (*p["color"], alpha), sp, size)
            
            elif ptype == "ember":
                pulse = pulse_value(game_time + p["phase"], speed=2.0, lo=0.4, hi=1.0)
                alpha = int(150 * pulse * (p.get("life", 1.0) / 3.0))
                draw_glow_circle(surface, p["color"], sp, size, alpha=alpha, layers=1)
                if "life" in p:
                    p["life"] -= 0.016
                    if p["life"] <= 0:
                        p["life"] = random.uniform(1.0, 3.0)
                        p["pos"] = [random.uniform(0, WORLD_SIZE), random.uniform(0, WORLD_SIZE)]


class World:
    def __init__(self, space, biome_key="membrane", player_level=1):
        self.space = space
        self.biome_key = biome_key
        self.biome = BIOMES[biome_key]
        self.player_level = player_level
        self.background = BackgroundLayer(biome_key)
        self.enemies = []
        self.cell_drops = []
        self.wave_timer = 0.0
        self.wave_interval = 14.0
        self.wave_number = 0
        self.weather = WeatherSystem(biome_key)
        self.poi_markers = []  # Points of interest
        self._generate_map()
        self._spawn_initial_enemies()
        self._spawn_cell_drops()

    def _generate_map(self):
        """Procedurally generate points of interest across the map."""
        # Safe zones — healing areas (outer regions, far from center)
        for _ in range(4):
            # Place safe zones in outer membrane area
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(1600, 1900)
            pos = (WORLD_SIZE/2 + math.cos(angle) * dist, 
                   WORLD_SIZE/2 + math.sin(angle) * dist)
            self.poi_markers.append({
                "type": "safe_zone",
                "pos": pos,
                "radius": 180,
                "color": (0, 255, 180),
                "label": "SAFE ZONE",
            })

        # Enemy nests — high density spawns (mid regions)
        for i in range(6):
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(1000, 1600)
            pos = (WORLD_SIZE/2 + math.cos(angle) * dist,
                   WORLD_SIZE/2 + math.sin(angle) * dist)
            self.poi_markers.append({
                "type": "nest",
                "pos": pos,
                "radius": 220,
                "color": (255, 60, 60),
                "label": f"NEST #{i+1}",
            })

        # Cell caches — lots of cell drops (scattered)
        for i in range(5):
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(800, 1700)
            pos = (WORLD_SIZE/2 + math.cos(angle) * dist,
                   WORLD_SIZE/2 + math.sin(angle) * dist)
            self.poi_markers.append({
                "type": "cache",
                "pos": pos,
                "radius": 140,
                "color": (255, 200, 0),
                "label": f"CACHE #{i+1}",
            })

        # Mini-Boss Domains — unique challenges with powerful rewards
        miniboss_domains = [
            {
                "name": "THE DEVOURER",
                "color": (255, 100, 255),
                "reward_type": "mutation",
                "reward_desc": "Cells gain +50% damage permanently",
                "boss_type": "devourer",
            },
            {
                "name": "THE ARCHITECT",
                "color": (100, 200, 255),
                "reward_type": "genome_boost",
                "reward_desc": "Genome capacity +20 permanently",
                "boss_type": "architect",
            },
            {
                "name": "THE SWARM QUEEN",
                "color": (255, 180, 100),
                "reward_type": "regeneration",
                "reward_desc": "Passive regeneration +5 HP/sec",
                "boss_type": "swarm_queen",
            },
        ]
        
        for i, domain_data in enumerate(miniboss_domains):
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(1200, 1700)
            pos = (WORLD_SIZE/2 + math.cos(angle) * dist,
                   WORLD_SIZE/2 + math.sin(angle) * dist)
            self.poi_markers.append({
                "type": "miniboss_domain",
                "pos": pos,
                "radius": 250,
                "color": domain_data["color"],
                "label": domain_data["name"],
                "name": domain_data["name"],
                "reward_type": domain_data["reward_type"],
                "reward_desc": domain_data["reward_desc"],
                "boss_type": domain_data["boss_type"],
                "defeated": False,
                "phase": i * 1.5,  # For pulsing animation offset
            })

        # Boss arena — FAR from spawn, at edge of map for epic journey
        # Place boss at a corner/edge position
        boss_angle = random.choice([0.25, 0.75, 1.25, 1.75]) * math.pi  # Cardinal-ish directions
        boss_dist = WORLD_SIZE * 0.42  # 42% from center = near edge
        boss_x = WORLD_SIZE/2 + math.cos(boss_angle) * boss_dist
        boss_y = WORLD_SIZE/2 + math.sin(boss_angle) * boss_dist
        boss_pos = (boss_x, boss_y)
        
        self.poi_markers.append({
            "type": "boss_arena",
            "pos": boss_pos,
            "radius": 400,  # Larger radius for more presence
            "color": (255, 0, 100),
            "label": "XENARCH'S DOMAIN",
        })
        
        # Add ominous decorations around boss arena
        self.background._generate_boss_scenery(boss_pos)
        
        # Add mini-boss scenery around domains
        for poi in self.poi_markers:
            if poi["type"] == "miniboss_domain":
                self._generate_miniboss_scenery(poi["pos"], poi["color"])

    def _spawn_initial_enemies(self):
        enemy_types = self.biome["enemy_types"]
        count = 6 + self.player_level * 2
        for _ in range(count):
            etype = random.choice(enemy_types)
            pos = self._random_spawn_pos()
            e = Enemy(self.space, pos, etype, level=self.player_level,
                      biome_modifier=self.biome.get("modifier"))
            self.enemies.append(e)

    def _spawn_cell_drops(self):
        from data.cells_data import CELLS
        all_cells = list(CELLS.keys())
        
        # Scatter some across the map
        for _ in range(12):
            self.cell_drops.append({
                "pos": (random.uniform(300, WORLD_SIZE-300), random.uniform(300, WORLD_SIZE-300)),
                "cell_type": random.choice(all_cells),
                "pulse_t": random.uniform(0, math.pi*2),
                "bob_phase": random.uniform(0, math.pi*2),
            })
        
        # Cluster drops in cell caches
        for poi in self.poi_markers:
            if poi["type"] == "cache":
                cx, cy = poi["pos"]
                for _ in range(8):
                    angle = random.uniform(0, math.pi * 2)
                    dist = random.uniform(20, poi["radius"] - 40)
                    px = cx + math.cos(angle) * dist
                    py = cy + math.sin(angle) * dist
                    self.cell_drops.append({
                        "pos": (px, py),
                        "cell_type": random.choice(all_cells),
                        "pulse_t": random.uniform(0, math.pi*2),
                        "bob_phase": random.uniform(0, math.pi*2),
                    })

    def _random_spawn_pos(self, min_dist=700):
        center = WORLD_SIZE / 2
        for _ in range(100):
            x = random.uniform(200, WORLD_SIZE - 200)
            y = random.uniform(200, WORLD_SIZE - 200)
            if math.hypot(x - center, y - center) > min_dist:
                return (x, y)
        return (random.uniform(200, WORLD_SIZE-200), random.uniform(200, WORLD_SIZE-200))

    def update(self, dt, game_time, player):
        self.wave_timer += dt
        if self.wave_timer >= self.wave_interval:
            self.wave_timer = 0
            self._spawn_wave(player)

        alive_enemies = []
        for e in self.enemies:
            e.update(dt, game_time, player)
            if e.alive:
                alive_enemies.append(e)
            else:
                self._on_enemy_death(e, player)
                for s in e.shapes:
                    if s in self.space.shapes:
                        self.space.remove(s)
                if e.body in self.space.bodies:
                    self.space.remove(e.body)
        self.enemies = alive_enemies

        self.weather.update(dt, game_time, player, WORLD_SIZE)

    def _spawn_wave(self, player):
        self.wave_number += 1
        enemy_types = self.biome["enemy_types"]
        count = 3 + self.wave_number
        for _ in range(count):
            etype = random.choice(enemy_types)
            pos = self._random_spawn_pos(min_dist=600)
            e = Enemy(self.space, pos, etype,
                      level=self.player_level + self.wave_number // 3,
                      biome_modifier=self.biome.get("modifier"))
            self.enemies.append(e)

    def _on_enemy_death(self, enemy, player):
        player.gain_xp(enemy.xp_value)
        player.stats["enemies_killed"] = player.stats.get("enemies_killed", 0) + 1

    def draw_background(self, surface, camera, game_time):
        self.background.draw(surface, camera, game_time)

    def draw_entities(self, surface, camera, game_time):
        # Draw POI zones first (under everything)
        self._draw_poi_zones(surface, camera, game_time)
        
        # Draw enemies with clear visual distinction
        for e in self.enemies:
            e.draw(surface, camera, game_time)

        # Cell drops — visually distinct: floating, labeled, with icon ring
        self._draw_cell_drops(surface, camera, game_time)

    def _draw_poi_zones(self, surface, camera, game_time):
        """Draw visible POI zone boundaries."""
        for poi in self.poi_markers:
            sp = camera.world_to_screen(*poi["pos"])
            r = max(10, int(poi["radius"] * camera.zoom))
            sw, sh = surface.get_size()
            if sp[0] < -r or sp[0] > sw+r or sp[1] < -r or sp[1] > sh+r:
                continue
            
            # Boss arena gets special treatment - MASSIVE AURA
            if poi["type"] == "boss_arena":
                # Multiple pulsing rings
                for layer in range(4):
                    pulse = pulse_value(game_time + layer * 0.3, speed=1.0 + layer * 0.2, lo=0.3, hi=0.8)
                    layer_r = r + layer * 30
                    alpha = int(pulse * (60 - layer * 10))
                    s = pygame.Surface((layer_r*2+4, layer_r*2+4), pygame.SRCALPHA)
                    pygame.draw.circle(s, (*poi["color"], alpha), (layer_r+2, layer_r+2), 
                                     layer_r, width=max(3, int(5*camera.zoom)))
                    surface.blit(s, (sp[0]-layer_r-2, sp[1]-layer_r-2))
                
                # Ominous glow at center
                draw_glow_circle(surface, (255, 0, 60), sp, int(r * 0.6), 
                               alpha=int(100 * pulse_value(game_time, speed=2.0, lo=0.5, hi=1.0)), 
                               layers=5)
                
                # Label with extra emphasis
                if camera.zoom > 0.3:
                    font = pygame.font.SysFont("consolas", 16, bold=True)
                    pulse_text = pulse_value(game_time, speed=1.5, lo=0.7, hi=1.0)
                    c = tuple(int(v * pulse_text) for v in poi["color"])
                    t = font.render(poi["label"], True, c)
                    surface.blit(t, (sp[0] - t.get_width()//2, sp[1] - 10))
            
            # Mini-boss domains get special treatment
            elif poi["type"] == "miniboss_domain":
                defeated = poi.get("defeated", False)
                
                if not defeated:
                    # Active domain - pulsing rings
                    for layer in range(3):
                        pulse = pulse_value(game_time + poi.get("phase", 0) + layer * 0.4, 
                                          speed=1.2 + layer * 0.3, lo=0.4, hi=0.9)
                        layer_r = r + layer * 20
                        alpha = int(pulse * (50 - layer * 10))
                        s = pygame.Surface((layer_r*2+4, layer_r*2+4), pygame.SRCALPHA)
                        pygame.draw.circle(s, (*poi["color"], alpha), (layer_r+2, layer_r+2), 
                                         layer_r, width=max(2, int(4*camera.zoom)))
                        surface.blit(s, (sp[0]-layer_r-2, sp[1]-layer_r-2))
                    
                    # Glowing center
                    draw_glow_circle(surface, poi["color"], sp, int(r * 0.5), 
                                   alpha=int(80 * pulse_value(game_time + poi.get("phase", 0), 
                                                              speed=1.8, lo=0.6, hi=1.0)), 
                                   layers=3)
                else:
                    # Defeated domain - dimmed
                    pygame.draw.circle(surface, (*poi["color"], 30), sp, r)
                    pygame.draw.circle(surface, (*poi["color"], 80), sp, r, width=2)
                
                # Label
                if camera.zoom > 0.4:
                    font = pygame.font.SysFont("consolas", 12, bold=True)
                    label_text = poi.get("name", "DOMAIN")
                    if defeated:
                        label_text += " [DEFEATED]"
                    pulse_text = pulse_value(game_time + poi.get("phase", 0), speed=1.5, lo=0.7, hi=1.0)
                    c = tuple(int(v * pulse_text) for v in poi["color"]) if not defeated else (100, 100, 100)
                    t = font.render(label_text, True, c)
                    surface.blit(t, (sp[0] - t.get_width()//2, sp[1] - r - t.get_height() - 4))
            
            else:
                # Normal POI zones
                pulse = pulse_value(game_time, speed=1.5, lo=0.4, hi=0.8)
                alpha = int(pulse * 60)
                s = pygame.Surface((r*2+4, r*2+4), pygame.SRCALPHA)
                pygame.draw.circle(s, (*poi["color"], alpha), (r+2, r+2), r, 
                                 width=max(2, int(3*camera.zoom)))
                surface.blit(s, (sp[0]-r-2, sp[1]-r-2))
                
                # Label
                if camera.zoom > 0.5:
                    font = pygame.font.SysFont("consolas", 11, bold=True)
                    t = font.render(poi["label"], True, poi["color"])
                    surface.blit(t, (sp[0] - t.get_width()//2, sp[1] - r - t.get_height() - 4))

    def _draw_cell_drops(self, surface, camera, game_time):
        from data.cells_data import CELLS
        font = pygame.font.SysFont("consolas", 10)
        for drop in self.cell_drops:
            sp = camera.world_to_screen(*drop["pos"])
            sw, sh = surface.get_size()
            if sp[0] < -40 or sp[0] > sw+40 or sp[1] < -40 or sp[1] > sh+40:
                continue

            cdata = CELLS.get(drop["cell_type"], CELLS["basic"])
            # Bob up and down
            bob = math.sin(game_time * 2.5 + drop["bob_phase"]) * 4 * camera.zoom
            draw_pos = (sp[0], int(sp[1] + bob))

            # Outer pickup ring — clearly distinguishes from enemies
            ring_r = max(8, int(20 * camera.zoom))
            ring_surf = pygame.Surface((ring_r*2+4, ring_r*2+4), pygame.SRCALPHA)
            pygame.draw.circle(ring_surf, (*cdata["glow"], 60), (ring_r+2, ring_r+2), ring_r, width=2)
            surface.blit(ring_surf, (draw_pos[0]-ring_r-2, draw_pos[1]-ring_r-2))

            # Glow
            draw_glow_circle(surface, cdata["glow"], draw_pos, max(6, int(10*camera.zoom)),
                             alpha=80, layers=2)
            # Hex icon
            draw_hex(surface, cdata["color"], draw_pos, max(5, int(9*camera.zoom)))

            # Label above — always visible
            if camera.zoom > 0.4:
                abbr = cdata["name"][:6]
                t = font.render(abbr, True, cdata["glow"])
                surface.blit(t, (draw_pos[0] - t.get_width()//2,
                                 draw_pos[1] - ring_r - t.get_height() - 2))

    def draw_weather(self, surface, camera, game_time, screen_w, screen_h):
        self.weather.draw(surface, camera, game_time, screen_w, screen_h)

    def draw_weather_hud(self, surface, font, screen_w, screen_h, game_time):
        self.weather.draw_hud(surface, font, screen_w, screen_h, game_time)

    def check_cell_pickup(self, player_pos, pickup_radius=50):
        picked = []
        remaining = []
        for drop in self.cell_drops:
            dx = drop["pos"][0] - player_pos[0]
            dy = drop["pos"][1] - player_pos[1]
            if math.hypot(dx, dy) < pickup_radius:
                picked.append(drop["cell_type"])
            else:
                remaining.append(drop)
        self.cell_drops = remaining
        return picked
    
    def _generate_miniboss_scenery(self, pos, color):
        """Generate unique scenery around mini-boss domains."""
        cx, cy = pos
        
        # Colored crystals forming a ring
        for i in range(8):
            angle = (i / 8) * math.pi * 2
            dist = 220 + random.uniform(-30, 30)
            x = cx + math.cos(angle) * dist
            y = cy + math.sin(angle) * dist
            size = random.uniform(40, 70)
            self.background.terrain.append(TerrainFeature(
                "crystal", (x, y), size,
                color, glow=tuple(min(255, c+60) for c in color)
            ))
        
        # Smaller crystals scattered around
        for _ in range(12):
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(180, 280)
            x = cx + math.cos(angle) * dist
            y = cy + math.sin(angle) * dist
            size = random.uniform(20, 40)
            self.background.terrain.append(TerrainFeature(
                "crystal", (x, y), size,
                color, glow=tuple(min(255, c+60) for c in color)
            ))
        
        # Re-sort terrain
        self.background.terrain.sort(key=lambda t: t.pos[1])
    
    def check_miniboss_entry(self, player_pos):
        """Check if player entered a mini-boss domain."""
        for poi in self.poi_markers:
            if poi["type"] == "miniboss_domain" and not poi.get("defeated", False):
                dx = poi["pos"][0] - player_pos[0]
                dy = poi["pos"][1] - player_pos[1]
                dist = math.hypot(dx, dy)
                if dist < poi["radius"]:
                    return poi
        return None
    
    def apply_miniboss_reward(self, player, reward_type, reward_desc):
        """Apply permanent buff to player from defeating mini-boss."""
        if reward_type == "mutation":
            # +50% damage to all offensive cells
            for cell in player.cells:
                if cell.data.get("category") == "offense":
                    if not hasattr(cell, "mutation_bonus"):
                        cell.mutation_bonus = {}
                    cell.mutation_bonus["damage"] = cell.mutation_bonus.get("damage", 1.0) * 1.5
            return "MUTATION ACQUIRED: All offensive cells deal +50% damage!"
        
        elif reward_type == "genome_boost":
            # +20 genome capacity permanently
            if not hasattr(player, "bonus_genome"):
                player.bonus_genome = 0
            player.bonus_genome += 20
            return "GENOME BOOST: Genome capacity increased by 20!"
        
        elif reward_type == "regeneration":
            # +5 HP/sec passive regen
            if not hasattr(player, "bonus_regen"):
                player.bonus_regen = 0
            player.bonus_regen += 5
            return "REGENERATION: Passive healing +5 HP/sec!"
        
        return "Reward acquired!"
