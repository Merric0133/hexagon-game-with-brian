"""
input_handler.py — Centralised input state for the current frame.
"""
import pygame


class InputHandler:
    def __init__(self):
        self.mouse_pos   = (0, 0)
        self._mouse_prev = [False, False, False, False, False]
        self._mouse_curr = [False, False, False, False, False]

    def reset(self):
        """Reset input state, clearing mouse button states."""
        self._mouse_prev = [False] * 5
        self._mouse_curr = [False] * 5

    def update(self, events, dt=None):
        self.mouse_pos   = pygame.mouse.get_pos()
        self._mouse_prev = list(self._mouse_curr)
        buttons          = pygame.mouse.get_pressed(num_buttons=5)
        self._mouse_curr = list(buttons) + [False] * (5 - len(buttons))

    def get_movement_vector(self):
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  dx -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  dy += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:    dy -= 1
        return dx, dy

    def mouse_just_pressed(self, button: int) -> bool:
        """button: 1=LMB 2=MMB 3=RMB (pygame numbering)."""
        idx = button - 1
        if idx < 0 or idx >= 5:
            return False
        return self._mouse_curr[idx] and not self._mouse_prev[idx]

    def mouse_held(self, button: int) -> bool:
        idx = button - 1
        if idx < 0 or idx >= 5:
            return False
        return bool(self._mouse_curr[idx])


input_handler = InputHandler()
