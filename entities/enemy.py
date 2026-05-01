import pygame
import pymunk
import math
import random
from entities.creature import Creature, HEX_SPACING
from core.utils import normalize, distance, draw_glow_circle, pulse_value
from core.constants import NEON_ORANGE, NEON_PINK

# Enemy archetype definitions
ENEMY_ARCHETYPES = {
    "drifter": {
        "cells": {(0,0): "basic", (1,0): "basic"},
        "color": (80, 200, 120), "glow": (0, 255, 100),
        "speed": 70, "xp": 20, "aggro_range": 200,
        "ai": "passive", "hp_mult": 1.0,
    },
    "hunter": {
        "cells": {(0,0): "heart", (-1,0): "spike", (1,0): "spike", (0,-1): "basic"},
        "color": (220, 80, 0), "glow": (255, 120, 0),
        "speed": 140, "xp": 50, "aggro_range": 350,
        "ai": "chase", "hp_mult": 1.2,
    },
    "armored_brute": {
        "cells": {(0,0): "heart", (-1,0): "shield", (1,0): "shield",
                  (0,-1): "anchor", (0,1): "spike", (-1,1): "basic", (1,1): "basic"},
        "color": (60, 60, 100), "glow": (100, 100, 180),
        "speed": 55, "xp": 120, "aggro_range": 280,
        "ai": "chase", "hp_mult": 2.5,
    },
    "hive_cluster": {
        "cells": {(0,0): "basic", (1,0): "basic", (-1,0): "basic"},
        "color": (180, 255, 0), "glow": (200, 255, 60),
        "speed": 100, "xp": 80, "aggro_range": 300,
        "ai": "hive", "hp_mult": 0.8, "splits_into": "drifter", "split_count": 3,
    },
    "psychic_weaver": {
        "cells": {(0,0): "heart", (0,-1): "zapper", (0,1): "zapper"},
        "color": (160, 0, 255), "glow": (200, 80, 255),
        "speed": 90, "xp": 100, "aggro_range": 400,
        "ai": "ranged", "hp_mult": 1.0, "attack_range": 350, "attack_cooldown": 2.5,
    },
    "mimic": {
        "cells": None,  # Copies player layout at spawn
        "color": (255, 100, 200), "glow": (255, 150, 220),
        "speed": 180, "xp": 200, "aggro_range": 500,
        "ai": "mimic", "hp_mult": 1.5,
    },
}

class Enemy(Creature):
    def __init__(self, space, pos, archetype, player_layout=None, level=1, biome_modifier=None):
        self.archetype = archetype
        self.arch_data = ENEMY_ARCHETYPES.get(archetype, ENEMY_ARCHETYPES["drifter"]).copy()
        self.collision_type = 2
        self.xp_value = int(self.arch_data["xp"] * (1 + (level - 1) * 0.2))
        self.ai_state = "idle"
        self.ai_timer = 0.0
        self.attack_cooldown = 0.0
        self.target = None
        self.level = level
        self.biome_modifier = biome_modifier
        self.split_spawned = False
        
        # Telegraph system
        self.telegraph_active = False
        self.telegraph_timer = 0.0
        self.telegraph_duration = 0.6  # Wind-up time before attack
        self.telegraph_color = (255, 100, 100)

        # Build layout
        if archetype == "mimic" and player_layout:
            layout = player_layout
        else:
            layout = self.arch_data.get("cells") or {(0,0): "basic"}

        # Scale HP with level
        super().__init__(space, pos, layout, race_data={})
        for cell in self.cells:
            cell.max_hp = int(cell.max_hp * self.arch_data["hp_mult"] * (1 + (level-1)*0.15))
            cell.hp = cell.max_hp

        for s in self.shapes:
            s.collision_type = 2

    def update(self, dt, game_time, player=None):
        super().update(dt, game_time)
        self.attack_cooldown -= dt
        self.ai_timer += dt
        
        # Update telegraph
        if self.telegraph_active:
            self.telegraph_timer -= dt
            if self.telegraph_timer <= 0:
                self.telegraph_active = False
                # Execute attack after telegraph
                if player and player.alive:
                    self._execute_attack(player)

        if player and player.alive:
            self._run_ai(dt, player)

    def _run_ai(self, dt, player):
        ai = self.arch_data["ai"]
        center = self.get_center()
        pcenter = player.get_center()
        dist = distance(center, pcenter)
        aggro = self.arch_data["aggro_range"]

        if ai == "passive":
            if dist < aggro:
                self.ai_state = "flee"
            else:
                self.ai_state = "drift"
            if self.ai_state == "flee":
                n = normalize((center[0]-pcenter[0], center[1]-pcenter[1]))
                spd = self.arch_data["speed"] * self.body.mass
                self.apply_force(n[0]*spd, n[1]*spd)

        elif ai in ("chase", "mimic"):
            if dist < aggro:
                self.ai_state = "chase"
            if self.ai_state == "chase":
                # Check if close enough to telegraph attack
                attack_range = 100 if not getattr(self, 'is_boss', False) else 120
                if dist < attack_range and self.attack_cooldown <= 0 and not self.telegraph_active:
                    self._start_telegraph()
                    self.attack_cooldown = 1.5 if getattr(self, 'is_boss', False) else 2.5  # Bosses attack faster
                elif not self.telegraph_active:  # Don't move during telegraph
                    n = normalize((pcenter[0]-center[0], pcenter[1]-center[1]))
                    spd = self.arch_data["speed"] * self.body.mass * 0.8
                    self.apply_force(n[0]*spd, n[1]*spd)
                    # Rotate toward player
                    target_angle = math.atan2(pcenter[1]-center[1], pcenter[0]-center[0])
                    diff = target_angle - self.body.angle
                    while diff > math.pi:  diff -= 2*math.pi
                    while diff < -math.pi: diff += 2*math.pi
                    self.body.angular_velocity = diff * 5.0
            self.body.velocity = (self.body.velocity.x * 0.9, self.body.velocity.y * 0.9)

        elif ai == "ranged":
            attack_range = self.arch_data.get("attack_range", 300)
            if dist < aggro:
                if dist > attack_range * 0.6:
                    n = normalize((pcenter[0]-center[0], pcenter[1]-center[1]))
                    spd = self.arch_data["speed"] * self.body.mass * 0.5
                    self.apply_force(n[0]*spd, n[1]*spd)
                elif dist < attack_range and self.attack_cooldown <= 0 and not self.telegraph_active:
                    self._start_telegraph()
                    self.attack_cooldown = self.arch_data.get("attack_cooldown", 2.5)
            self.body.velocity = (self.body.velocity.x * 0.9, self.body.velocity.y * 0.9)

        elif ai == "hive":
            if dist < aggro:
                if dist < 120 and self.attack_cooldown <= 0 and not self.telegraph_active:
                    self._start_telegraph()
                    self.attack_cooldown = 2.0
                elif not self.telegraph_active:
                    n = normalize((pcenter[0]-center[0], pcenter[1]-center[1]))
                    spd = self.arch_data["speed"] * self.body.mass * 0.7
                    self.apply_force(n[0]*spd, n[1]*spd)
            self.body.velocity = (self.body.velocity.x * 0.9, self.body.velocity.y * 0.9)
    
    def _start_telegraph(self):
        """Begin attack telegraph - visual warning before damage."""
        self.telegraph_active = True
        self.telegraph_timer = self.telegraph_duration
        # Stop movement during telegraph
        self.body.velocity = (0, 0)
    
    def _execute_attack(self, player):
        """Execute the actual attack after telegraph completes."""
        center = self.get_center()
        pcenter = player.get_center()
        
        # Deal damage based on enemy type
        if self.arch_data["ai"] == "ranged":
            # Ranged attack - force push
            n = normalize((pcenter[0]-center[0], pcenter[1]-center[1]))
            player.body.apply_impulse_at_world_point(
                (n[0]*800, n[1]*800), player.body.position
            )
            player.take_damage(15, center)
        else:
            # Melee attack - direct damage
            damage = 20
            for ecell in self.cells:
                if ecell.cell_type == "spike" and ecell.alive:
                    damage = ecell.data.get("damage", 20)
                    break
            player.take_damage(damage, center)

    def _ranged_attack(self, player):
        """Psychic weaver: apply force push to player."""
        center = self.get_center()
        pcenter = player.get_center()
        n = normalize((pcenter[0]-center[0], pcenter[1]-center[1]))
        player.body.apply_impulse_at_world_point(
            (n[0]*800, n[1]*800), player.body.position
        )
        player.take_damage(15, center)

    def should_split(self):
        return (self.arch_data["ai"] == "hive"
                and not self.split_spawned
                and len(self.cells) <= 1)

    def _on_cells_lost(self, lost_cells):
        """When cells are lost, check if core (heart) was destroyed."""
        # Check if any lost cell was a heart
        for cell in lost_cells:
            if "heart" in cell.cell_type:
                # Core destroyed - kill all remaining cells
                for c in self.cells:
                    c.hp = 0
                    c.alive = False
                self.cells = []
                self.alive = False
                break

    def draw(self, surface, camera, game_time):
        cx, cy = self.get_center()
        sp = camera.world_to_screen(cx, cy)
        
        # Xenarch aura - MASSIVE intimidating glow
        if getattr(self, 'is_xenarch', False):
            pulse = pulse_value(game_time, speed=1.5, lo=0.5, hi=1.0)
            # Massive outer aura - magenta
            aura_radius = int(200 * camera.zoom * pulse)
            draw_glow_circle(surface, (255, 0, 255), sp, aura_radius, alpha=int(100 * pulse), layers=5)
            # Middle aura - pink
            aura_radius2 = int(140 * camera.zoom * pulse)
            draw_glow_circle(surface, (255, 100, 200), sp, aura_radius2, alpha=int(120 * pulse), layers=4)
            # Inner aura - bright magenta
            aura_radius3 = int(80 * camera.zoom * pulse)
            draw_glow_circle(surface, (255, 0, 255), sp, aura_radius3, alpha=int(150 * pulse), layers=3)
        
        # Boss aura - massive intimidating glow
        elif getattr(self, 'is_boss', False):
            pulse = pulse_value(game_time, speed=2.0, lo=0.6, hi=1.0)
            # Massive outer aura
            aura_radius = int(120 * camera.zoom * pulse)
            draw_glow_circle(surface, (255, 0, 0), sp, aura_radius, alpha=int(80 * pulse), layers=4)
            # Inner aura
            aura_radius2 = int(80 * camera.zoom * pulse)
            draw_glow_circle(surface, (255, 100, 0), sp, aura_radius2, alpha=int(100 * pulse), layers=3)
        
        # Mini-boss aura - smaller but still intimidating
        elif getattr(self, 'is_miniboss', False):
            pulse = pulse_value(game_time, speed=2.5, lo=0.7, hi=1.0)
            aura_radius = int(80 * camera.zoom * pulse)
            draw_glow_circle(surface, (255, 100, 0), sp, aura_radius, alpha=int(70 * pulse), layers=3)
        
        # Telegraph warning visual
        if self.telegraph_active:
            pulse = pulse_value(game_time, speed=8.0, lo=0.4, hi=1.0)
            # Pulsing red glow
            draw_glow_circle(surface, self.telegraph_color, sp, 
                           int(50 * camera.zoom * pulse), 
                           alpha=int(120 * pulse), layers=3)
            # Warning ring
            ring_radius = int(40 * camera.zoom)
            pygame.draw.circle(surface, self.telegraph_color, sp, ring_radius, 
                             width=max(2, int(3 * camera.zoom)))
        
        # Draw cells
        super().draw(surface, camera, game_time)
        
        # Boss/Mini-boss/Xenarch title above
        if getattr(self, 'boss_title', None):
            font = pygame.font.SysFont("consolas", max(12, int(16 * camera.zoom)))
            if getattr(self, 'is_xenarch', False):
                title_color = (255, 0, 255)
            elif getattr(self, 'is_miniboss', False):
                title_color = (255, 100, 0)
            else:
                title_color = (255, 0, 0)
            title_text = font.render(self.boss_title, True, title_color)
            title_rect = title_text.get_rect(center=(sp[0], sp[1] - int(60 * camera.zoom)))
            surface.blit(title_text, title_rect)
        
        # Health bar above enemy — only visible when damaged or close
        hp_ratio = self.get_total_biomass() / max(1, self.get_max_biomass())
        if hp_ratio < 1.0 or camera.zoom > 0.7:
            bar_w = max(20, int(36 * camera.zoom))
            bar_h = max(2, int(4 * camera.zoom))
            bar_x = sp[0] - bar_w // 2
            bar_y = sp[1] - int(38 * camera.zoom)
            
            # Background
            pygame.draw.rect(surface, (40, 20, 20), (bar_x, bar_y, bar_w, bar_h), border_radius=1)
            # Fill
            fill_w = int(bar_w * hp_ratio)
            bar_color = (255, 60, 60) if hp_ratio < 0.3 else (255, 180, 0) if hp_ratio < 0.6 else (0, 200, 80)
            pygame.draw.rect(surface, bar_color, (bar_x, bar_y, fill_w, bar_h), border_radius=1)
