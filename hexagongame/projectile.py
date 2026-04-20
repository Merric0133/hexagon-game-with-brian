# =============================================================================
# entities/projectile.py — Player attack projectiles
# =============================================================================
import math
import pygame
from constants import WORLD_WIDTH, WORLD_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT

class Projectile:
    """A projectile fired by the player's abilities."""
    def __init__(self, x: float, y: float, target_x: float, target_y: float,
                 ability_data: dict, player=None):
        self.x = x
        self.y = y
        self.ability = ability_data
        self.alive = True
        self.player = player  # Reference to player for mouse tracking
        
        # Direction
        dx = target_x - x
        dy = target_y - y
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.vx = (dx / dist) * 400  # pixels/sec
            self.vy = (dy / dist) * 400
        else:
            self.vx = self.vy = 0
        
        self.radius = 8
        self.lifetime = 5.0
        self._age = 0.0

    def update(self, dt: float):
        # Update position
        self.x += self.vx * dt
        self.y += self.vy * dt
        self._age += dt
        
        # Home toward mouse if player is available
        if self.player:
            from input_handler import input_handler
            from camera import camera
            
            mx, my = input_handler.mouse_pos
            
            # Convert screen to world coords — more accurate
            world_x = camera.x + mx - SCREEN_WIDTH / 2
            world_y = camera.y + my - SCREEN_HEIGHT / 2
            
            # Direction to mouse
            dx = world_x - self.x
            dy = world_y - self.y
            dist = math.hypot(dx, dy)
            
            if dist > 0:
                # Strong homing — steer aggressively toward mouse
                homing_factor = 0.3  # Increased from 0.15
                steer_x = (dx / dist) * 400
                steer_y = (dy / dist) * 400
                
                # Lerp velocity toward target direction
                self.vx += (steer_x - self.vx) * homing_factor * dt
                self.vy += (steer_y - self.vy) * homing_factor * dt
                
                # Cap speed so it doesn't accelerate infinitely
                speed = math.hypot(self.vx, self.vy)
                max_speed = 600
                if speed > max_speed:
                    self.vx = (self.vx / speed) * max_speed
                    self.vy = (self.vy / speed) * max_speed
        
        # Out of bounds or lifetime
        if (self.x < 0 or self.x > WORLD_WIDTH or 
            self.y < 0 or self.y > WORLD_HEIGHT or
            self._age >= self.lifetime):
            self.alive = False

    def draw(self, surface: pygame.Surface, camera):
        sx, sy = camera.world_to_screen(self.x, self.y)
        col = self.ability["color"]
        pygame.draw.circle(surface, col, (int(sx), int(sy)), self.radius)
        pygame.draw.circle(surface, (255, 255, 255), (int(sx), int(sy)), self.radius, 1)

    def collides_with_enemy(self, enemy) -> bool:
        dist = math.hypot(self.x - enemy.x, self.y - enemy.y)
        return dist <= (self.radius + enemy.radius)