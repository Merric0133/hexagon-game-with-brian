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
                elif dist < attack_range and self.attack_cooldown <= 0:
                    self._ranged_attack(player)
                    self.attack_cooldown = self.arch_data.get("attack_cooldown", 2.5)
            self.body.velocity = (self.body.velocity.x * 0.9, self.body.velocity.y * 0.9)

        elif ai == "hive":
            if dist < aggro:
                n = normalize((pcenter[0]-center[0], pcenter[1]-center[1]))
                spd = self.arch_data["speed"] * self.body.mass * 0.7
                self.apply_force(n[0]*spd, n[1]*spd)
            self.body.velocity = (self.body.velocity.x * 0.9, self.body.velocity.y * 0.9)

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

    def draw(self, surface, camera, game_time):
        # Draw large glowing outline around enemy — makes them super visible
        cx, cy = self.get_center()
        sp = camera.world_to_screen(cx, cy)
        
        # Pulsing glow aura
        pulse = pulse_value(game_time, speed=2.0, lo=0.6, hi=1.0)
        glow_r = int(40 * camera.zoom * pulse)
        draw_glow_circle(surface, self.arch_data["glow"], sp, glow_r, alpha=60, layers=3)
        
        # Thick colored outline ring
        ring_r = int(35 * camera.zoom)
        ring_surf = pygame.Surface((ring_r*2+4, ring_r*2+4), pygame.SRCALPHA)
        pygame.draw.circle(ring_surf, (*self.arch_data["glow"], 120), (ring_r+2, ring_r+2), ring_r, width=3)
        surface.blit(ring_surf, (sp[0]-ring_r-2, sp[1]-ring_r-2))
        
        # Draw cells
        super().draw(surface, camera, game_time)
        
        # Health bar above enemy — always visible
        hp_ratio = self.get_total_biomass() / max(1, self.get_max_biomass())
        bar_w = max(30, int(50 * camera.zoom))
        bar_h = max(3, int(6 * camera.zoom))
        bar_x = sp[0] - bar_w // 2
        bar_y = sp[1] - int(45 * camera.zoom)
        
        # Background
        pygame.draw.rect(surface, (40, 20, 20), (bar_x, bar_y, bar_w, bar_h), border_radius=2)
        # Fill
        fill_w = int(bar_w * hp_ratio)
        bar_color = (255, 60, 60) if hp_ratio < 0.3 else (255, 180, 0) if hp_ratio < 0.6 else (0, 255, 100)
        pygame.draw.rect(surface, bar_color, (bar_x, bar_y, fill_w, bar_h), border_radius=2)
        # Border
        pygame.draw.rect(surface, (200, 200, 200), (bar_x, bar_y, bar_w, bar_h), width=1, border_radius=2)
        
        # Aggro indicator — red exclamation mark
        if self.ai_state == "chase":
            font = pygame.font.SysFont("consolas", 14, bold=True)
            aggro_txt = font.render("!", True, (255, 60, 60))
            aggro_bg = pygame.Surface((aggro_txt.get_width()+6, aggro_txt.get_height()+4), pygame.SRCALPHA)
            aggro_bg.fill((255, 60, 60, 100))
            surface.blit(aggro_bg, (sp[0] - aggro_txt.get_width()//2 - 3, bar_y - aggro_txt.get_height() - 6))
            surface.blit(aggro_txt, (sp[0] - aggro_txt.get_width()//2, bar_y - aggro_txt.get_height() - 4))
        
        # Enemy type label (small, above health bar)
        if camera.zoom > 0.6:
            font = pygame.font.SysFont("consolas", 9)
            label = self.archetype.replace("_", " ").title()
            label_txt = font.render(label, True, self.arch_data["glow"])
            surface.blit(label_txt, (sp[0] - label_txt.get_width()//2, bar_y - label_txt.get_height() - 2))
