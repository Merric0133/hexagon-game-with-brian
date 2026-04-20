import pygame
import math
import sys
import random
import os

# =============================================================================
# 1. CONSTANTS & CONFIGURATION
# =============================================================================
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
WINDOW_TITLE, TARGET_FPS = "HEXCORE: ASCEND", 60

# Colors
COLOR_BG = (15, 15, 20)
COLOR_TEXT = (240, 240, 240)
COLOR_TEXT_DIM = (140, 140, 150)
COLOR_ACCENT = (0, 255, 255)
COLOR_ACCENT2 = (255, 0, 255)
COLOR_DANGER = (255, 50, 50)
COLOR_SUCCESS = (50, 255, 100)

HEX_RADIUS = 30
WORLD_WIDTH, WORLD_HEIGHT = 3000, 3000

# =============================================================================
# 2. CORE SYSTEMS (CAMERA & UI)
# =============================================================================
class Camera:
    def __init__(self):
        self.x, self.y = WORLD_WIDTH//2, WORLD_HEIGHT//2
    def apply(self, pos):
        return (pos[0] - self.x + SCREEN_WIDTH//2, pos[1] - self.y + SCREEN_HEIGHT//2)

camera = Camera()

def draw_hex(surface, x, y, color, radius=HEX_RADIUS, width=0):
    points = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        points.append((x + radius * math.cos(angle), y + radius * math.sin(angle)))
    pygame.draw.polygon(surface, color, points, width)

class Button:
    def __init__(self, x, y, w, h, text, color):
        self.rect = pygame.Rect(x, y, w, h)
        self.text, self.color = text, color
    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=8)
        font = pygame.font.SysFont("Arial", 24, bold=True)
        txt = font.render(self.text, True, (255, 255, 255))
        surface.blit(txt, txt.get_rect(center=self.rect.center))
    def is_clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos)

# =============================================================================
# 3. ENTITIES
# =============================================================================
class Player:
    def __init__(self):
        self.x, self.y = WORLD_WIDTH//2, WORLD_HEIGHT//2
        self.hp, self.max_hp = 100, 100
        self.speed = 5
        self.score = 0
    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w] or keys[pygame.K_UP]: self.y -= self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: self.y += self.speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: self.x -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: self.x += self.speed
        self.x = max(0, min(WORLD_WIDTH, self.x))
        self.y = max(0, min(WORLD_HEIGHT, self.y))

class Enemy:
    def __init__(self):
        angle = random.uniform(0, math.tau)
        dist = random.randint(500, 800)
        self.x = WORLD_WIDTH//2 + math.cos(angle) * dist
        self.y = WORLD_HEIGHT//2 + math.sin(angle) * dist
        self.hp = 20
        self.speed = random.uniform(2, 3.5)
    def update(self, px, py):
        angle = math.atan2(py - self.y, px - self.x)
        self.x += math.cos(angle) * self.speed
        self.y += math.sin(angle) * self.speed
    def draw(self, surface):
        pos = camera.apply((self.x, self.y))
        draw_hex(surface, pos[0], pos[1], COLOR_DANGER, radius=20)

# =============================================================================
# 4. GAME ENGINE
# =============================================================================
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()
    
    player = Player()
    enemies = [Enemy() for _ in range(8)]
    state = "MENU"
    play_btn = Button(SCREEN_WIDTH//2-100, SCREEN_HEIGHT//2, 200, 50, "START", (0, 150, 200))

    while True:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if state == "MENU" and play_btn.is_clicked(event):
                state = "GAME"

        screen.fill(COLOR_BG)

        if state == "MENU":
            font = pygame.font.SysFont("Arial", 80, bold=True)
            title = font.render("HEXCORE", True, COLOR_ACCENT)
            screen.blit(title, title.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2-100)))
            play_btn.draw(screen)
        
        elif state == "GAME":
            player.update()
            camera.x, camera.y = player.x, player.y
            
            # Draw simple grid
            for i in range(0, WORLD_WIDTH, 200):
                p1 = camera.apply((i, 0)); p2 = camera.apply((i, WORLD_HEIGHT))
                pygame.draw.line(screen, (30,30,45), p1, p2)
            
            # Draw Player
            p_pos = camera.apply((player.x, player.y))
            draw_hex(screen, p_pos[0], p_pos[1], COLOR_ACCENT)
            
            # Update/Draw Enemies
            for e in enemies:
                e.update(player.x, player.y)
                e.draw(screen)
                # Simple collision
                if math.hypot(player.x - e.x, player.y - e.y) < 40:
                    player.hp -= 0.5
            
            # HUD
            pygame.draw.rect(screen, (50, 10, 10), (20, 20, 200, 20))
            pygame.draw.rect(screen, (0, 255, 100), (20, 20, player.hp * 2, 20))
            if player.hp <= 0: state = "MENU"; player.hp = 100 # Reset on death

        pygame.display.flip()
        clock.tick(TARGET_FPS)

if __name__ == "__main__":
    main()