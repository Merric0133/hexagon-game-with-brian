"""
boss.py — Boss enemy system for HEXCORE: ASCEND
"""
import pygame
import math
import random
from typing import List, Tuple, Optional


class BossEnemy:
    """Boss enemy with unique mechanics and phases"""
    def __init__(self, x: float, y: float, wave: int, boss_type: str = "HEXLORD"):
        self.x = x
        self.y = y
        self.wave = wave
        self.boss_type = boss_type
        self.alive = True
        
        # Scale with wave
        wave_scale = 1.0 + (wave - 1) * 0.12
        
        # Boss stats (much tankier than normal enemies)
        self.max_hp = 500 * wave_scale
        self.hp = self.max_hp
        self.speed = 100 * wave_scale
        self.damage = 25 * wave_scale
        self.radius = 50
        
        # Boss mechanics
        self.phase = 1  # Bosses have multiple phases
        self.phase_threshold_1 = self.max_hp * 0.66
        self.phase_threshold_2 = self.max_hp * 0.33
        
        # Attack patterns
        self.attack_timer = 0.0
        self.attack_cooldown = 3.0
        self.special_attack_timer = 0.0
        self.special_attack_cooldown = 8.0
        
        # Movement
        self.vx = 0.0
        self.vy = 0.0
        self.target_x = x
        self.target_y = y
        
        # Visual
        self.color = (255, 50, 50)
        self.glow_pulse = 0.0
        
        # Invincibility frames
        self.invincible_time = 0.0
        
        # Minions spawned
        self.minions_spawned = 0
        self.max_minions_per_phase = 3
    
    def update(self, dt: float, player_x: float, player_y: float, world_bounds: Tuple[int, int]):
        """Update boss AI and mechanics"""
        if not self.alive:
            return
        
        # Update timers
        self.attack_timer = max(0, self.attack_timer - dt)
        self.special_attack_timer = max(0, self.special_attack_timer - dt)
        self.invincible_time = max(0, self.invincible_time - dt)
        self.glow_pulse += dt * 3
        
        # Check phase transitions
        if self.hp <= self.phase_threshold_2 and self.phase < 3:
            self.phase = 3
            self.enter_phase_3()
        elif self.hp <= self.phase_threshold_1 and self.phase < 2:
            self.phase = 2
            self.enter_phase_2()
        
        # AI behavior based on phase
        if self.phase == 1:
            self.phase_1_behavior(dt, player_x, player_y)
        elif self.phase == 2:
            self.phase_2_behavior(dt, player_x, player_y)
        else:
            self.phase_3_behavior(dt, player_x, player_y)
        
        # Apply movement
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Keep in bounds
        world_w, world_h = world_bounds
        self.x = max(self.radius, min(world_w - self.radius, self.x))
        self.y = max(self.radius, min(world_h - self.radius, self.y))
    
    def phase_1_behavior(self, dt: float, player_x: float, player_y: float):
        """Phase 1: Slow, methodical approach"""
        # Move toward player
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist > 200:
            # Chase player
            self.vx = (dx / dist) * self.speed
            self.vy = (dy / dist) * self.speed
        else:
            # Circle around player
            angle = math.atan2(dy, dx) + math.pi / 2
            self.vx = math.cos(angle) * self.speed * 0.7
            self.vy = math.sin(angle) * self.speed * 0.7
    
    def phase_2_behavior(self, dt: float, player_x: float, player_y: float):
        """Phase 2: Faster, more aggressive"""
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        # Charge at player
        if dist > 0:
            self.vx = (dx / dist) * self.speed * 1.5
            self.vy = (dy / dist) * self.speed * 1.5
    
    def phase_3_behavior(self, dt: float, player_x: float, player_y: float):
        """Phase 3: Erratic, desperate"""
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        # Dash toward player with random dodges
        if random.random() < 0.02:
            # Random dodge
            angle = random.uniform(0, math.pi * 2)
            self.vx = math.cos(angle) * self.speed * 2
            self.vy = math.sin(angle) * self.speed * 2
        else:
            # Chase
            if dist > 0:
                self.vx = (dx / dist) * self.speed * 1.8
                self.vy = (dy / dist) * self.speed * 1.8
    
    def enter_phase_2(self):
        """Transition to phase 2"""
        self.speed *= 1.3
        self.attack_cooldown = 2.0
        self.color = (255, 100, 50)
    
    def enter_phase_3(self):
        """Transition to phase 3"""
        self.speed *= 1.2
        self.attack_cooldown = 1.5
        self.color = (255, 150, 50)
    
    def take_damage(self, amount: float) -> bool:
        """Take damage. Returns True if killed."""
        if self.invincible_time > 0:
            return False
        
        self.hp -= amount
        self.invincible_time = 0.05  # Brief i-frames
        
        if self.hp <= 0:
            self.alive = False
            return True
        return False
    
    def can_attack(self) -> bool:
        """Check if boss can perform basic attack"""
        return self.attack_timer <= 0
    
    def can_special_attack(self) -> bool:
        """Check if boss can perform special attack"""
        return self.special_attack_timer <= 0
    
    def perform_attack(self):
        """Perform basic attack"""
        self.attack_timer = self.attack_cooldown
    
    def perform_special_attack(self) -> str:
        """Perform special attack. Returns attack type."""
        self.special_attack_timer = self.special_attack_cooldown
        
        if self.phase == 1:
            return "shockwave"
        elif self.phase == 2:
            return "summon_minions"
        else:
            return "bullet_hell"
    
    def draw(self, surface: pygame.Surface, camera_x: float, camera_y: float):
        """Draw the boss"""
        screen_x = int(self.x - camera_x)
        screen_y = int(self.y - camera_y)
        
        # Glow effect
        glow_radius = int(self.radius + 10 + math.sin(self.glow_pulse) * 5)
        glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*self.color, 60), (glow_radius, glow_radius), glow_radius)
        surface.blit(glow_surf, (screen_x - glow_radius, screen_y - glow_radius))
        
        # Main body (hexagon)
        points = []
        for i in range(6):
            angle = math.pi / 3 * i
            px = screen_x + math.cos(angle) * self.radius
            py = screen_y + math.sin(angle) * self.radius
            points.append((px, py))
        
        pygame.draw.polygon(surface, self.color, points)
        pygame.draw.polygon(surface, (255, 255, 255), points, 3)
        
        # Phase indicator (inner hexagon)
        inner_radius = self.radius * 0.5
        inner_points = []
        for i in range(6):
            angle = math.pi / 3 * i + self.glow_pulse
            px = screen_x + math.cos(angle) * inner_radius
            py = screen_y + math.sin(angle) * inner_radius
            inner_points.append((px, py))
        
        phase_color = [
            (255, 200, 200),
            (255, 150, 100),
            (255, 100, 50)
        ][self.phase - 1]
        pygame.draw.polygon(surface, phase_color, inner_points)
        
        # HP bar
        bar_width = 100
        bar_height = 8
        bar_x = screen_x - bar_width // 2
        bar_y = screen_y - self.radius - 20
        
        # Background
        pygame.draw.rect(surface, (40, 40, 40), (bar_x, bar_y, bar_width, bar_height))
        
        # HP fill
        hp_percent = self.hp / self.max_hp
        fill_width = int(bar_width * hp_percent)
        pygame.draw.rect(surface, (255, 50, 50), (bar_x, bar_y, fill_width, bar_height))
        
        # Border
        pygame.draw.rect(surface, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 1)


def should_spawn_boss(wave: int) -> bool:
    """Check if a boss should spawn this wave"""
    return wave % 10 == 0 and wave > 0


def create_boss(wave: int, world_width: int, world_height: int) -> BossEnemy:
    """Create a boss for the given wave"""
    # Spawn boss in center of world
    x = world_width / 2
    y = world_height / 2
    
    return BossEnemy(x, y, wave, "HEXLORD")
