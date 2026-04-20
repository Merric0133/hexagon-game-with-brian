import pygame

class InputHandler:
    def __init__(self):
        self.keys = []
        self.mouse_pos = (0, 0)
        self._mouse_pressed_last = set()
        self._mouse_pressed = set()

    def update(self, events=None, dt=0):
        self.keys = pygame.key.get_pressed()
        self.mouse_pos = pygame.mouse.get_pos()
        self._mouse_pressed_last = self._mouse_pressed.copy()
        self._mouse_pressed = set()
        
        if events:
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self._mouse_pressed.add(event.button)

    def get_movement_vector(self):
        """Return (dx, dy) movement vector."""
        dx = 0
        dy = 0
        
        if self.keys[pygame.K_d] or self.keys[pygame.K_RIGHT]:
            dx += 1
        if self.keys[pygame.K_a] or self.keys[pygame.K_LEFT]:
            dx -= 1
        if self.keys[pygame.K_s] or self.keys[pygame.K_DOWN]:
            dy += 1
        if self.keys[pygame.K_w] or self.keys[pygame.K_UP]:
            dy -= 1
        
        return (dx, dy)

    def mouse_just_pressed(self, button):
        return button in self._mouse_pressed and button not in self._mouse_pressed_last

input_handler = InputHandler()