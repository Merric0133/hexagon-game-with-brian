import pygame
from core.utils import lerp, screen_shake_offset

class Camera:
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.x = 0.0
        self.y = 0.0
        self.target_x = 0.0
        self.target_y = 0.0
        self.zoom = 1.0
        self.target_zoom = 1.0
        self.shake_intensity = 0.0
        self.shake_decay = 8.0
        self._shake_offset = (0, 0)

    def follow(self, target_pos, dt):
        self.target_x = target_pos[0] - self.screen_w / (2 * self.zoom)
        self.target_y = target_pos[1] - self.screen_h / (2 * self.zoom)
        speed = 6.0
        self.x = lerp(self.x, self.target_x, min(1.0, speed * dt))
        self.y = lerp(self.y, self.target_y, min(1.0, speed * dt))
        self.zoom = lerp(self.zoom, self.target_zoom, min(1.0, 3.0 * dt))
        if self.shake_intensity > 0:
            self._shake_offset = screen_shake_offset(self.shake_intensity, self.shake_decay)
            self.shake_intensity -= self.shake_decay * dt
            if self.shake_intensity < 0:
                self.shake_intensity = 0
        else:
            self._shake_offset = (0, 0)

    def shake(self, intensity=8.0):
        self.shake_intensity = max(self.shake_intensity, intensity)

    def world_to_screen(self, wx, wy):
        sx = (wx - self.x) * self.zoom + self._shake_offset[0]
        sy = (wy - self.y) * self.zoom + self._shake_offset[1]
        return (int(sx), int(sy))

    def screen_to_world(self, sx, sy):
        wx = (sx - self._shake_offset[0]) / self.zoom + self.x
        wy = (sy - self._shake_offset[1]) / self.zoom + self.y
        return (wx, wy)

    def set_zoom_for_scale(self, creature_scale):
        """Zoom out as creature grows."""
        base = 1.0
        self.target_zoom = max(0.3, base / (1 + (creature_scale - 1) * 0.15))
