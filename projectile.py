"""
projectile.py — Generic projectile entity.

Used (or ready to be used) for any ranged attack — e.g. a future
SHOOT cell upgrade, or enemy shooter variants.

Construction
────────────
    proj = Projectile(
        x, y,               # world-space origin
        target_x, target_y, # initial aim point (world-space)
        speed    = 420,      # pixels/sec
        damage   = 15,
        radius   = 7,
        color    = (255, 200, 60),
        lifetime = 4.0,
        homing   = False,    # set True to steer toward mouse each frame
    )
"""
import math
import pygame
from constants import WORLD_WIDTH, WORLD_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT


class Projectile:
    def __init__(
        self,
        x: float, y: float,
        target_x: float, target_y: float,
        speed:    float = 420,
        damage:   float = 15,
        radius:   int   = 7,
        color:    tuple = (255, 200, 60),
        lifetime: float = 4.0,
        homing:   bool  = False,
    ):
        self.x       = x
        self.y       = y
        self.damage  = damage
        self.radius  = radius
        self.color   = color
        self.alive   = True
        self._age    = 0.0
        self._lifetime = lifetime
        self._homing   = homing
        self._speed    = speed

        dx   = target_x - x
        dy   = target_y - y
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.vx = (dx / dist) * speed
            self.vy = (dy / dist) * speed
        else:
            self.vx = 0.0
            self.vy = -speed   # fire straight up if no direction given

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float):
        self.x    += self.vx * dt
        self.y    += self.vy * dt
        self._age += dt

        if self._homing:
            self._steer_toward_mouse(dt)

        if (self.x < 0 or self.x > WORLD_WIDTH or
                self.y < 0 or self.y > WORLD_HEIGHT or
                self._age >= self._lifetime):
            self.alive = False

    def _steer_toward_mouse(self, dt: float):
        try:
            from input_handler import input_handler
            from camera import camera
            mx, my   = input_handler.mouse_pos
            world_x  = camera.x + mx - SCREEN_WIDTH  / 2
            world_y  = camera.y + my - SCREEN_HEIGHT / 2
            dx, dy   = world_x - self.x, world_y - self.y
            dist     = math.hypot(dx, dy)
            if dist > 0:
                steer_x = (dx / dist) * self._speed
                steer_y = (dy / dist) * self._speed
                self.vx += (steer_x - self.vx) * 0.25 * dt * 60
                self.vy += (steer_y - self.vy) * 0.25 * dt * 60
                spd = math.hypot(self.vx, self.vy)
                if spd > self._speed * 1.5:
                    self.vx = (self.vx / spd) * self._speed * 1.5
                    self.vy = (self.vy / spd) * self._speed * 1.5
        except Exception:
            pass

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface, camera):
        sx, sy = camera.world_to_screen(self.x, self.y)
        pygame.draw.circle(surface, self.color,      (int(sx), int(sy)), self.radius)
        pygame.draw.circle(surface, (255, 255, 255), (int(sx), int(sy)), self.radius, 1)

    # ── Collision ─────────────────────────────────────────────────────────────

    def collides_with(self, entity) -> bool:
        return math.hypot(self.x - entity.x, self.y - entity.y) <= (self.radius + entity.radius)

    def collides_with_enemy(self, enemy) -> bool:
        return self.collides_with(enemy)

    def collides_with_player(self, player) -> bool:
        return math.hypot(self.x - player.x, self.y - player.y) <= (self.radius + 26)
