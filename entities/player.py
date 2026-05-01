import pygame
import pymunk
import math
import random
from entities.creature import Creature, HEX_SPACING
from core.utils import normalize, distance, draw_glow_circle, hex_to_pixel
from core.constants import NEON_CYAN, NEON_PURPLE, NEON_GREEN
from data.races_data import RACES

MOVE_FORCE = 3200   # increased for snappier feel
BOOST_FORCE = 5000
PHASE_DURATION = 0.8
PHASE_COOLDOWN = 6.0
DAMPING = 0.82      # lower = snappier stop

class Player(Creature):
    def __init__(self, space, pos, strain_data):
        self.strain_data = strain_data
        race_name = strain_data.get("race", "Vorrkai")
        race_data = RACES.get(race_name, {})
        layout = strain_data.get("cell_layout") or {}
        if isinstance(layout, dict) and layout:
            # Normalize string keys to tuple keys
            normalized = {}
            for k, v in layout.items():
                if isinstance(k, str) and "," in k:
                    col, row = map(int, k.split(","))
                    normalized[(col, row)] = v
                else:
                    normalized[k] = v
            layout = normalized
        if not layout:
            # Default starting layout from saved cells list
            cells_list = strain_data.get("cells", ["heart", "basic", "basic", "basic"])
            # Replace generic heart with race-specific heart
            cells_list = [f"heart_{race_name.lower()}" if c == "heart" else c for c in cells_list]
            layout = {(i - len(cells_list)//2, 0): ct for i, ct in enumerate(cells_list)}

        super().__init__(space, pos, layout, race_data)
        self.collision_type = 1
        for s in self.shapes:
            s.collision_type = 1

        self.race_name = race_name
        self.race_data = race_data
        self.level = strain_data.get("level", 1)
        self.xp = strain_data.get("xp", 0)
        self.scale = strain_data.get("scale", 1.0)

        # Heart shield system
        self.heart_shield = 100.0
        self.heart_shield_max = 100.0
        self.heart_shield_regen = 5.0  # per second
        self.heart_shield_regen_delay = 3.0  # seconds after taking damage
        self.heart_shield_regen_timer = 0.0

        # Ability state
        self.ability_active = False
        self.phase_timer = 0.0
        self.phase_cooldown_timer = 0.0
        self.calcify_timer = 0.0
        self.boost_charge = 0.0  # for pulse dash synergy
        
        # Dash attack state
        self.dash_attack_active = False
        self.dash_attack_timer = 0.0
        self.dash_iframe_duration = 0.18  # Brief iframes during dash

        # Keybind ability cooldowns
        self.ability_cooldowns = {
            'q': 0.0,  # Dash
            'e': 0.0,  # Shield Burst
            'r': 0.0,  # Heal Pulse
            'f': 0.0,  # Rage Mode
        }
        self.ability_durations = {
            'q': 8.0,   # Dash cooldown
            'e': 12.0,  # Shield Burst cooldown
            'r': 15.0,  # Heal Pulse cooldown
            'f': 20.0,  # Rage Mode cooldown
        }
        self.rage_mode_active = False
        self.rage_timer = 0.0
        self.dash_glide_timer = 0.0  # For dash glide effect

        # Particle trail
        self.trail_particles = []

        # Stats tracking
        self.stats = strain_data.get("stats", {})
        self.active_synergies_display = set()

    def handle_input(self, keys, mouse_pos, camera, dt):
        # WASD = movement, mouse = rotation only
        dx, dy = 0, 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:    dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1

        # Race-specific movement modifiers
        race_damping = self.race_data.get("damping", 0.85)
        race_turn_speed = self.race_data.get("turn_speed", 10.0)
        movement_style = self.race_data.get("movement_style", "default")

        force_mult = MOVE_FORCE * self.body.mass
        
        # Apply movement style
        if movement_style == "slithering_snake":
            # Snake: smooth slithering with body following head
            if dx != 0 or dy != 0:
                n = normalize((dx, dy))
                # Head leads, body follows with delay
                self.apply_force(n[0] * force_mult * 1.3, n[1] * force_mult * 1.3)
                # Add slight perpendicular wiggle for slither feel
                wiggle = math.sin(self.game_time * 8.0) * 0.15
                perp = (-n[1], n[0])
                self.apply_force(perp[0] * force_mult * wiggle, perp[1] * force_mult * wiggle)
        
        elif movement_style == "heavy_tank":
            # Tank: slow acceleration, momentum-heavy
            if dx != 0 or dy != 0:
                n = normalize((dx, dy))
                self.apply_force(n[0] * force_mult * 0.7, n[1] * force_mult * 0.7)
        
        elif movement_style == "darting":
            # Darting: quick bursts, responsive
            if dx != 0 or dy != 0:
                n = normalize((dx, dy))
                self.apply_force(n[0] * force_mult * 1.4, n[1] * force_mult * 1.4)
        
        elif movement_style == "erratic_swarm":
            # Swarm: jittery, unpredictable micro-movements
            if dx != 0 or dy != 0:
                n = normalize((dx, dy))
                jitter_x = random.uniform(-0.1, 0.1)
                jitter_y = random.uniform(-0.1, 0.1)
                self.apply_force((n[0] + jitter_x) * force_mult * 1.2,
                                 (n[1] + jitter_y) * force_mult * 1.2)
        
        elif movement_style == "flowing":
            # Flowing: smooth, wave-like
            if dx != 0 or dy != 0:
                n = normalize((dx, dy))
                wave = math.sin(self.game_time * 4.0) * 0.08
                self.apply_force(n[0] * force_mult * (1.0 + wave),
                                 n[1] * force_mult * (1.0 + wave))
        
        else:
            # Default
            if dx != 0 or dy != 0:
                n = normalize((dx, dy))
                self.apply_force(n[0] * force_mult, n[1] * force_mult)

        # Mouse only rotates the creature
        world_mouse = camera.screen_to_world(*mouse_pos)
        center = self.get_center()
        to_mouse = (world_mouse[0] - center[0], world_mouse[1] - center[1])
        dist_to_mouse = math.hypot(*to_mouse)
        if dist_to_mouse > 10:
            target_angle = math.atan2(to_mouse[1], to_mouse[0])
            current_angle = self.body.angle
            diff = target_angle - current_angle
            while diff > math.pi:  diff -= 2 * math.pi
            while diff < -math.pi: diff += 2 * math.pi
            self.body.angular_velocity = diff * race_turn_speed

        # Velocity damping (race-specific) - reduced during dash glide
        vx, vy = self.body.velocity
        if hasattr(self, 'dash_glide_timer') and self.dash_glide_timer > 0:
            # Less damping during dash for glide effect
            self.body.velocity = (vx * 0.98, vy * 0.98)
        else:
            self.body.velocity = (vx * race_damping, vy * race_damping)

    def trigger_keybind_ability(self, key, direction=None):
        """Trigger abilities bound to Q, E, R, F keys.
        
        Args:
            key: The ability key ('q', 'e', 'r', 'f')
            direction: For dash, a tuple (dx, dy) for directional input, or None for facing direction
        """
        if self.ability_cooldowns[key] > 0:
            return None  # On cooldown
        
        center = self.get_center()
        
        if key == 'q':  # Dash Attack - directional with WASD
            self.ability_cooldowns['q'] = self.ability_durations['q']
            
            # Determine dash direction
            if direction and (direction[0] != 0 or direction[1] != 0):
                # Use WASD direction (world space, not local)
                dash_dir = normalize(direction)
                angle = math.atan2(dash_dir[1], dash_dir[0])
            else:
                # Fall back to facing direction
                angle = self.body.angle
            
            # Balanced dash force - not too far, not too short
            dash_force = 1400 * self.body.mass
            # Apply impulse in world space (not local)
            impulse_x = math.cos(angle) * dash_force
            impulse_y = math.sin(angle) * dash_force
            self.body.apply_impulse_at_world_point((impulse_x, impulse_y), self.body.position)
            # Activate dash attack state
            self.dash_attack_active = True
            self.dash_attack_timer = 0.25  # Dash attack window
            # Brief iframes for dodging telegraphed attacks
            self.status_effects['dash_iframe'] = self.dash_iframe_duration
            # Reduce damping briefly for a subtle glide
            self.dash_glide_timer = 0.15
            return 'dash'
        
        elif key == 'e':  # Shield Burst - temporary damage reduction + knockback
            self.ability_cooldowns['e'] = self.ability_durations['e']
            self.status_effects['shield_burst'] = 2.5
            return 'shield_burst'
        
        elif key == 'r':  # Heal Pulse - restore health to all cells
            self.ability_cooldowns['r'] = self.ability_durations['r']
            heal_amount = 15
            for cell in self.cells:
                if cell.alive:
                    cell.heal(heal_amount)
            return 'heal_pulse'
        
        elif key == 'f':  # Rage Mode - increased damage for duration
            self.ability_cooldowns['f'] = self.ability_durations['f']
            self.rage_mode_active = True
            self.rage_timer = 5.0  # 5 seconds of rage
            return 'rage_mode'
        
        return None

    def trigger_ability(self, camera, mouse_pos):
        """Called on SPACE press."""
        race = self.race_name
        center = self.get_center()

        if race == "Nullborn" and self.phase_cooldown_timer <= 0:
            self.status_effects["phase"] = PHASE_DURATION
            self.phase_cooldown_timer = PHASE_COOLDOWN
            for s in self.shapes:
                s.filter = pymunk.ShapeFilter(mask=0)  # intangible
            return "phase"

        if race == "Lumenid":
            return "photon_burst"

        if race == "Skrix":
            return "fission"

        # Generic: activate ability cells
        for cell in self.cells:
            if cell.data.get("ability") and cell.ability_cooldown <= 0:
                return cell.data["ability"]
        return None
        """Called on SPACE press."""
        race = self.race_name
        center = self.get_center()

        if race == "Nullborn" and self.phase_cooldown_timer <= 0:
            self.status_effects["phase"] = PHASE_DURATION
            self.phase_cooldown_timer = PHASE_COOLDOWN
            for s in self.shapes:
                s.filter = pymunk.ShapeFilter(mask=0)  # intangible
            return "phase"

        if race == "Lumenid":
            return "photon_burst"

        if race == "Skrix":
            return "fission"

        # Generic: activate ability cells
        for cell in self.cells:
            if cell.data.get("ability") and cell.ability_cooldown <= 0:
                return cell.data["ability"]
        return None

    def update(self, dt, game_time):
        super().update(dt, game_time)

        # Update ability cooldowns
        for key in self.ability_cooldowns:
            if self.ability_cooldowns[key] > 0:
                self.ability_cooldowns[key] -= dt
        
        # Heart shield regeneration
        if self.heart_shield < self.heart_shield_max:
            if self.heart_shield_regen_timer > 0:
                self.heart_shield_regen_timer -= dt
            else:
                self.heart_shield += self.heart_shield_regen * dt
                self.heart_shield = min(self.heart_shield, self.heart_shield_max)
        
        # Dash attack timer
        if self.dash_attack_active:
            self.dash_attack_timer -= dt
            if self.dash_attack_timer <= 0:
                self.dash_attack_active = False
        
        # Dash glide timer
        if hasattr(self, 'dash_glide_timer') and self.dash_glide_timer > 0:
            self.dash_glide_timer -= dt
        
        # Rage mode timer
        if self.rage_mode_active:
            self.rage_timer -= dt
            if self.rage_timer <= 0:
                self.rage_mode_active = False
        
        # Bonus regeneration from mini-boss rewards
        if hasattr(self, 'bonus_regen') and self.bonus_regen > 0:
            # Heal all cells by bonus_regen * dt
            heal_amount = self.bonus_regen * dt
            for cell in self.cells:
                if cell.alive:
                    cell.heal(heal_amount)

        # Phase timer
        if self.phase_cooldown_timer > 0:
            self.phase_cooldown_timer -= dt
        if "phase" in self.status_effects:
            pass  # handled by status_effects dict
        else:
            # Restore collision
            for s in self.shapes:
                if s.filter.mask == 0:
                    s.filter = pymunk.ShapeFilter()

        # Calcify (Vorrkai)
        if "calcify" in self.status_effects:
            pass  # damage reduction handled in take_damage

        # Trail particles
        cx, cy = self.get_center()
        if random.random() < 0.4:
            race_color = self.race_data.get("glow", (0, 255, 180))
            # Rage mode changes particle color
            if self.rage_mode_active:
                race_color = (255, 60, 0)
            self.trail_particles.append({
                "pos": [cx + random.uniform(-8, 8), cy + random.uniform(-8, 8)],
                "vel": [random.uniform(-20, 20), random.uniform(-20, 20)],
                "life": random.uniform(0.3, 0.8),
                "max_life": 0.8,
                "color": race_color,
                "radius": random.uniform(2, 5),
            })

        # Update trail
        for p in self.trail_particles:
            p["life"] -= dt
            p["pos"][0] += p["vel"][0] * dt
            p["pos"][1] += p["vel"][1] * dt
        self.trail_particles = [p for p in self.trail_particles if p["life"] > 0]

        self.active_synergies_display = self.active_synergies.copy()

    def take_damage(self, amount, source_pos=None):
        # Phase = immune
        if "phase" in self.status_effects:
            race_stats = self.strain_data.get("stats", {})
            race_stats["nullborn_phases"] = race_stats.get("nullborn_phases", 0) + 1
            return
        # Dash iframes = immune
        if "dash_iframe" in self.status_effects:
            return
        # Shield Burst = 70% reduction
        if "shield_burst" in self.status_effects:
            amount = int(amount * 0.3)
        # Calcify = 50% reduction
        if "calcify" in self.status_effects:
            amount = int(amount * 0.5)
        # Fortress synergy
        if "Fortress" in self.active_synergies:
            amount = int(amount * 0.6)
        
        # Check if damage hits a heart cell - apply shield first
        if source_pos:
            from core.utils import distance
            for cell in self.cells:
                if cell.cell_type == "heart" and cell.alive:
                    if distance(cell.world_pos, source_pos) < 30:  # Heart is being hit
                        if self.heart_shield > 0:
                            # Shield absorbs damage
                            shield_damage = min(amount, self.heart_shield)
                            self.heart_shield -= shield_damage
                            amount -= shield_damage
                            # Reset regen delay
                            self.heart_shield_regen_timer = self.heart_shield_regen_delay
                            if amount <= 0:
                                return  # Shield absorbed all damage
        
        super().take_damage(amount, source_pos)

    def _on_cells_lost(self, lost_cells):
        # Skrix: spawn minions
        if self.race_name == "Skrix":
            self.stats["skrix_shed"] = self.stats.get("skrix_shed", 0) + len(lost_cells)
        # Vorrkai: calcify on heavy loss
        if self.race_name == "Vorrkai" and len(lost_cells) >= 2:
            self.status_effects["calcify"] = 3.0
        # Screen shake signal (handled by game)
        self._cells_lost_this_frame = lost_cells

    def gain_xp(self, amount):
        self.xp += amount
        from core.constants import XP_PER_LEVEL
        from data.cells_data import get_genome_cap, get_biomass_cap
        
        while self.level < len(XP_PER_LEVEL) and self.xp >= XP_PER_LEVEL[self.level]:
            self.xp -= XP_PER_LEVEL[self.level]
            
            # Store old stats
            old_level = self.level
            old_genome = get_genome_cap(self.level)
            old_biomass = get_biomass_cap(self.level)
            
            # Level up
            self.level += 1
            self.scale = 1.0 + (self.level - 1) * 0.12
            
            # Get new stats
            new_genome = get_genome_cap(self.level)
            new_biomass = get_biomass_cap(self.level)
            
            # Store level up data for HUD
            self._levelup_data = {
                "old_level": old_level,
                "new_level": self.level,
                "old_genome": old_genome,
                "new_genome": new_genome,
                "old_biomass": old_biomass,
                "new_biomass": new_biomass,
            }
            
            self._rebuild_physics()
            return True  # leveled up
        return False

    def draw(self, surface, camera, game_time):
        # Draw trail
        for p in self.trail_particles:
            sp = camera.world_to_screen(*p["pos"])
            alpha = int(255 * (p["life"] / p["max_life"]))
            r = max(1, int(p["radius"] * camera.zoom))
            glow_surf = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
            c = (*p["color"][:3], alpha // 2)
            pygame.draw.circle(glow_surf, c, (r * 2, r * 2), r * 2)
            surface.blit(glow_surf, (sp[0] - r * 2, sp[1] - r * 2), special_flags=pygame.BLEND_RGBA_ADD)

        # Phase visual
        if "phase" in self.status_effects:
            cx, cy = self.get_center()
            sp = camera.world_to_screen(cx, cy)
            draw_glow_circle(surface, (120, 60, 255), sp, int(40 * camera.zoom), alpha=60, layers=3)
        
        # Dash iframe visual
        if "dash_iframe" in self.status_effects:
            cx, cy = self.get_center()
            sp = camera.world_to_screen(cx, cy)
            draw_glow_circle(surface, (0, 255, 255), sp, int(35 * camera.zoom), alpha=100, layers=2)
        
        # Shield Burst visual
        if "shield_burst" in self.status_effects:
            cx, cy = self.get_center()
            sp = camera.world_to_screen(cx, cy)
            draw_glow_circle(surface, (0, 180, 255), sp, int(50 * camera.zoom), alpha=80, layers=3)
        
        # Rage Mode visual
        if self.rage_mode_active:
            cx, cy = self.get_center()
            sp = camera.world_to_screen(cx, cy)
            draw_glow_circle(surface, (255, 60, 0), sp, int(45 * camera.zoom), alpha=70, layers=3)

        super().draw(surface, camera, game_time)

    def to_save_data(self):
        layout = {f"{k[0]},{k[1]}": v.cell_type for k, v in self.cell_layout.items()}
        self.strain_data.update({
            "level": self.level,
            "xp": self.xp,
            "scale": self.scale,
            "cell_layout": layout,
            "stats": self.stats,
        })
        return self.strain_data
