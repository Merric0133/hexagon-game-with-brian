import pygame
import math
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, WORLD_WIDTH, WORLD_HEIGHT

class Camera:
    def __init__(self):
        self.x = WORLD_WIDTH / 2
        self.y = WORLD_HEIGHT / 2
        self._shake_intensity = 0.0
        self._shake_timer = 0.0

    def update(self, player_x, player_y, dt):
        """Smooth camera follow with optional shake."""
        target_x = player_x - SCREEN_WIDTH / 2
        target_y = player_y - SCREEN_HEIGHT / 2
        
        # Lerp camera to target
        self.x += (target_x - self.x) * 0.1
        self.y += (target_y - self.y) * 0.1
        
        # Apply shake
        if self._shake_timer > 0:
            self._shake_timer -= dt
            shake_x = (pygame.time.get_ticks() % 20 - 10) * self._shake_intensity * 0.01
            shake_y = (pygame.time.get_ticks() % 30 - 15) * self._shake_intensity * 0.01
            self.x += shake_x
            self.y += shake_y

    def world_to_screen(self, wx, wy):
        """Convert world coordinates to screen coordinates."""
        sx = wx - self.x
        sy = wy - self.y
        return (sx, sy)

    def is_visible(self, wx, wy, margin=0):
        """Check if a world position is visible on screen."""
        sx, sy = self.world_to_screen(wx, wy)
        return (-margin < sx < SCREEN_WIDTH + margin and 
                -margin < sy < SCREEN_HEIGHT + margin)

    def shake(self, intensity, duration):
        """Trigger screen shake on impact."""
        self._shake_intensity = intensity
        self._shake_timer = duration

camera = Camera()