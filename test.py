"""
Hexcell Game
------------
Controls:
  - Mouse        : Move player core toward cursor
  - R            : Restart / re-enter build phase
  - ESC          : Quit

Build Phase:
  - Click a highlighted slot to cycle through cell types
  - Right-click a cell to remove it
  - Press ENTER to start

Cell Types:
  HEART  (♥) – acts as a life; losing all hearts = death
  JOINT  (⬡) – structural cell (acts as a connector for future expansion)
  MOVE   (➤) – boosts player speed while attached
  DAMAGE (✦) – deals damage to enemies on contact

Enemy Cell Types (spawned on enemies):
  DAMAGE – damages player heart cells on contact
  SHOOT  – periodically fires projectiles at the player
"""

import pygame
import math
import pymunk
import pymunk.pygame_util
import random
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum, auto

# ── Constants ───────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 900, 650
FPS = 60
HEX_RADIUS = 24          # visual hex radius
CELL_OFFSET = 54         # center-to-center distance between hexes
CORE_RADIUS = 22
PLAYER_BASE_SPEED = 220
MOVE_CELL_BONUS = 60     # speed bonus per MOVE cell
ENEMY_SPAWN_INTERVAL = 4.0   # seconds
PROJECTILE_SPEED = 200
PROJECTILE_RADIUS = 5

COLORS = {
    "bg":          (12,  14,  22),
    "grid":        (30,  35,  55),
    "core":        (130, 200, 255),
    "core_ring":   (80,  160, 220),
    "heart":       (240, 80,  100),
    "joint":       (100, 180, 255),
    "move":        (80,  230, 160),
    "damage":      (255, 160, 60),
    "empty":       (40,  45,  65),
    "empty_hover": (70,  75,  100),
    "slot_ring":   (90,  95,  130),
    "enemy_body":  (180, 60,  80),
    "enemy_ring":  (220, 100, 120),
    "proj":        (255, 200, 60),
    "ui_text":     (200, 215, 255),
    "ui_dim":      (100, 115, 155),
    "shadow":      (0,   0,   0),
    "white":       (255, 255, 255),
    "dmg_flash":   (255, 60,  60),
}

# ── Cell types ───────────────────────────────────────────────────────────────
class CellType(Enum):
    EMPTY  = auto()
    HEART  = auto()
    JOINT  = auto()
    MOVE   = auto()
    DAMAGE = auto()

CELL_ICONS = {
    CellType.EMPTY:  "",
    CellType.HEART:  "♥",
    CellType.JOINT:  "⬡",
    CellType.MOVE:   "➤",
    CellType.DAMAGE: "✦",
}

CELL_CYCLE = [CellType.HEART, CellType.JOINT, CellType.MOVE, CellType.DAMAGE, CellType.EMPTY]

# Hex neighbor directions (flat-top, 6 slots)
HEX_DIRECTIONS = [
    (CELL_OFFSET, 0),                                           # 0  right
    (CELL_OFFSET * 0.5,  CELL_OFFSET * math.sqrt(3) / 2),      # 1  lower-right
    (-CELL_OFFSET * 0.5, CELL_OFFSET * math.sqrt(3) / 2),      # 2  lower-left
    (-CELL_OFFSET, 0),                                          # 3  left
    (-CELL_OFFSET * 0.5, -CELL_OFFSET * math.sqrt(3) / 2),     # 4  upper-left
    (CELL_OFFSET * 0.5,  -CELL_OFFSET * math.sqrt(3) / 2),     # 5  upper-right
]

# ── Helpers ──────────────────────────────────────────────────────────────────
def hex_vertices(cx, cy, r):
    pts = []
    for i in range(6):
        a = math.radians(i * 60)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts

def draw_hex(surf, color, cx, cy, r, width=0):
    pts = hex_vertices(cx, cy, r)
    pygame.draw.polygon(surf, color, pts, width)

def draw_hex_shadow(surf, cx, cy, r, alpha=80):
    shadow_surf = pygame.Surface((r*2+8, r*2+8), pygame.SRCALPHA)
    pts = [(x - cx + r + 4, y - cy + r + 4) for x, y in hex_vertices(cx, cy, r)]
    pygame.draw.polygon(shadow_surf, (*COLORS["shadow"], alpha), pts)
    surf.blit(shadow_surf, (cx - r - 4 + 3, cy - r - 4 + 3))

def dist(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])

# ── Cell ─────────────────────────────────────────────────────────────────────
@dataclass
class Cell:
    slot: int                          # 0-5, which direction from core
    cell_type: CellType = CellType.EMPTY
    flash_timer: float = 0.0           # for damage flash

    def offset(self):
        d = HEX_DIRECTIONS[self.slot]
        return (d[0], d[1])

    def world_pos(self, core_pos):
        ox, oy = self.offset()
        return (core_pos[0] + ox, core_pos[1] + oy)

# ── Projectile ───────────────────────────────────────────────────────────────
@dataclass
class Projectile:
    x: float
    y: float
    vx: float
    vy: float
    lifetime: float = 4.0
    from_enemy: bool = True

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= dt

    def dead(self):
        return (self.lifetime <= 0 or
                not (0 <= self.x <= WIDTH) or
                not (0 <= self.y <= HEIGHT))

# ── Enemy ────────────────────────────────────────────────────────────────────
class EnemyKind(Enum):
    DAMAGE = auto()   # rams player
    SHOOTER = auto()  # stays at range, shoots

@dataclass
class Enemy:
    x: float
    y: float
    kind: EnemyKind
    hp: int = 2
    speed: float = 90
    shoot_timer: float = 0.0
    shoot_interval: float = 2.0
    dead: bool = False
    flash_timer: float = 0.0
    radius: float = 20.0

    def update(self, dt, player_pos, projectiles):
        if self.dead:
            return
        self.flash_timer = max(0, self.flash_timer - dt)
        dx = player_pos[0] - self.x
        dy = player_pos[1] - self.y
        d = math.hypot(dx, dy)

        if self.kind == EnemyKind.DAMAGE:
            if d > 5:
                self.x += dx/d * self.speed * dt
                self.y += dy/d * self.speed * dt
        elif self.kind == EnemyKind.SHOOTER:
            # orbit at ~200px
            target_dist = 200
            if d > target_dist + 20:
                self.x += dx/d * self.speed * dt
                self.y += dy/d * self.speed * dt
            elif d < target_dist - 20:
                self.x -= dx/d * self.speed * dt
                self.y -= dy/d * self.speed * dt
            # shoot
            self.shoot_timer -= dt
            if self.shoot_timer <= 0:
                self.shoot_timer = self.shoot_interval
                if d > 0:
                    projectiles.append(Projectile(
                        self.x, self.y,
                        dx/d * PROJECTILE_SPEED,
                        dy/d * PROJECTILE_SPEED,
                        from_enemy=True
                    ))

    def take_hit(self):
        self.hp -= 1
        self.flash_timer = 0.15
        if self.hp <= 0:
            self.dead = True

    def draw(self, surf, font_small):
        if self.dead:
            return
        col = COLORS["dmg_flash"] if self.flash_timer > 0 else COLORS["enemy_body"]
        draw_hex_shadow(surf, int(self.x), int(self.y), int(self.radius))
        draw_hex(surf, col, int(self.x), int(self.y), int(self.radius))
        draw_hex(surf, COLORS["enemy_ring"], int(self.x), int(self.y), int(self.radius), 2)
        # icon
        icon = "✦" if self.kind == EnemyKind.DAMAGE else "⊛"
        t = font_small.render(icon, True, COLORS["white"])
        surf.blit(t, t.get_rect(center=(int(self.x), int(self.y))))

# ── Player ────────────────────────────────────────────────────────────────────
class Player:
    def __init__(self, cells):
        self.x = WIDTH / 2
        self.y = HEIGHT / 2
        self.cells: list[Cell] = cells
        self.flash_timer = 0.0
        self.invincible_timer = 0.0   # brief invincibility after hit

    @property
    def heart_count(self):
        return sum(1 for c in self.cells if c.cell_type == CellType.HEART)

    @property
    def speed(self):
        move_count = sum(1 for c in self.cells if c.cell_type == CellType.MOVE)
        return PLAYER_BASE_SPEED + move_count * MOVE_CELL_BONUS

    @property
    def pos(self):
        return (self.x, self.y)

    def is_dead(self):
        return self.heart_count <= 0

    def update(self, dt, mouse_pos):
        self.flash_timer = max(0, self.flash_timer - dt)
        self.invincible_timer = max(0, self.invincible_timer - dt)
        dx = mouse_pos[0] - self.x
        dy = mouse_pos[1] - self.y
        d = math.hypot(dx, dy)
        if d > 8:
            move = min(d, self.speed * dt)
            self.x += dx/d * move
            self.y += dy/d * move
        # clamp
        self.x = max(CORE_RADIUS + CELL_OFFSET + HEX_RADIUS, min(WIDTH  - CORE_RADIUS - CELL_OFFSET - HEX_RADIUS, self.x))
        self.y = max(CORE_RADIUS + CELL_OFFSET + HEX_RADIUS, min(HEIGHT - CORE_RADIUS - CELL_OFFSET - HEX_RADIUS, self.y))

    def lose_heart(self):
        """Remove one heart cell. Returns True if hearts remain."""
        if self.invincible_timer > 0:
            return True
        for c in self.cells:
            if c.cell_type == CellType.HEART:
                c.cell_type = CellType.EMPTY
                c.flash_timer = 0.4
                self.flash_timer = 0.25
                self.invincible_timer = 1.2
                return self.heart_count > 0
        return False

    def cell_world_positions(self):
        return [(c, c.world_pos(self.pos)) for c in self.cells]

    def draw(self, surf, font_small, font_icon):
        px, py = int(self.x), int(self.y)

        # Draw attached cells first (behind core)
        for cell in self.cells:
            wp = cell.world_pos(self.pos)
            cx, cy = int(wp[0]), int(wp[1])
            if cell.flash_timer > 0:
                cell.flash_timer -= 1/FPS
                col = COLORS["dmg_flash"]
            elif cell.cell_type == CellType.EMPTY:
                col = COLORS["empty"]
            elif cell.cell_type == CellType.HEART:
                col = COLORS["heart"]
            elif cell.cell_type == CellType.JOINT:
                col = COLORS["joint"]
            elif cell.cell_type == CellType.MOVE:
                col = COLORS["move"]
            elif cell.cell_type == CellType.DAMAGE:
                col = COLORS["damage"]
            else:
                col = COLORS["empty"]

            draw_hex_shadow(surf, cx, cy, HEX_RADIUS)
            draw_hex(surf, col, cx, cy, HEX_RADIUS)
            ring_col = tuple(min(255, c + 40) for c in col) if cell.cell_type != CellType.EMPTY else COLORS["slot_ring"]
            draw_hex(surf, ring_col, cx, cy, HEX_RADIUS, 2)

            icon = CELL_ICONS.get(cell.cell_type, "")
            if icon:
                t = font_icon.render(icon, True, COLORS["white"])
                surf.blit(t, t.get_rect(center=(cx, cy)))

        # Core
        core_col = COLORS["dmg_flash"] if self.flash_timer > 0 else COLORS["core"]
        draw_hex_shadow(surf, px, py, CORE_RADIUS)
        draw_hex(surf, core_col, px, py, CORE_RADIUS)
        draw_hex(surf, COLORS["core_ring"], px, py, CORE_RADIUS, 2)


# ── Build Phase UI ────────────────────────────────────────────────────────────
class BuildPhase:
    def __init__(self, initial_cells):
        self.cells = initial_cells    # list[Cell]
        self.hovered_slot = -1

    def handle_event(self, event, player_pos):
        mx, my = pygame.mouse.get_pos()
        self.hovered_slot = -1
        for cell in self.cells:
            wp = cell.world_pos(player_pos)
            if dist((mx, my), wp) < HEX_RADIUS:
                self.hovered_slot = cell.slot
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        # cycle type
                        idx = CELL_CYCLE.index(cell.cell_type)
                        cell.cell_type = CELL_CYCLE[(idx + 1) % len(CELL_CYCLE)]
                    elif event.button == 3:
                        cell.cell_type = CellType.EMPTY
                break

    def draw(self, surf, player_pos, font_small, font_icon, font_ui):
        px, py = int(player_pos[0]), int(player_pos[1])

        # Instructions panel
        panel = pygame.Surface((300, 160), pygame.SRCALPHA)
        panel.fill((15, 18, 35, 200))
        surf.blit(panel, (10, 10))
        lines = [
            "BUILD PHASE",
            "Left-click slot → cycle cell type",
            "Right-click slot → clear cell",
            "ENTER → start game",
            "",
            f"Hearts: {sum(1 for c in self.cells if c.cell_type==CellType.HEART)}  "
            f"Move: {sum(1 for c in self.cells if c.cell_type==CellType.MOVE)}  "
            f"Dmg: {sum(1 for c in self.cells if c.cell_type==CellType.DAMAGE)}",
        ]
        for i, line in enumerate(lines):
            col = COLORS["core"] if i == 0 else COLORS["ui_text"]
            t = font_small.render(line, True, col)
            surf.blit(t, (18, 16 + i * 24))

        # Legend
        legend = [
            (CellType.HEART,  "♥ Heart – life"),
            (CellType.JOINT,  "⬡ Joint – structural"),
            (CellType.MOVE,   "➤ Move – speed boost"),
            (CellType.DAMAGE, "✦ Damage – hurts enemies"),
        ]
        lx, ly = WIDTH - 220, 10
        lp = pygame.Surface((210, 110), pygame.SRCALPHA)
        lp.fill((15, 18, 35, 200))
        surf.blit(lp, (lx - 5, ly))
        for i, (ct, label) in enumerate(legend):
            cmap = {CellType.HEART: COLORS["heart"], CellType.JOINT: COLORS["joint"],
                    CellType.MOVE: COLORS["move"], CellType.DAMAGE: COLORS["damage"]}
            pygame.draw.circle(surf, cmap[ct], (lx + 8, ly + 14 + i*24), 7)
            t = font_small.render(label, True, COLORS["ui_text"])
            surf.blit(t, (lx + 20, ly + 6 + i*24))

        # Hover tooltip
        for cell in self.cells:
            wp = cell.world_pos(player_pos)
            cx, cy = int(wp[0]), int(wp[1])
            if cell.slot == self.hovered_slot:
                draw_hex(surf, COLORS["white"], cx, cy, HEX_RADIUS, 2)
                label = cell.cell_type.name.capitalize()
                t = font_small.render(label, True, COLORS["white"])
                surf.blit(t, (cx - t.get_width()//2, cy + HEX_RADIUS + 4))


# ── Game ──────────────────────────────────────────────────────────────────────
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Hexcell")
        self.clock = pygame.time.Clock()

        # Fonts – use system fallbacks if needed
        try:
            self.font_ui    = pygame.font.SysFont("Consolas", 18, bold=True)
            self.font_small = pygame.font.SysFont("Consolas", 14)
            self.font_icon  = pygame.font.SysFont("Segoe UI Symbol", 15)
            self.font_big   = pygame.font.SysFont("Consolas", 36, bold=True)
        except Exception:
            self.font_ui    = pygame.font.SysFont(None, 22)
            self.font_small = pygame.font.SysFont(None, 18)
            self.font_icon  = pygame.font.SysFont(None, 18)
            self.font_big   = pygame.font.SysFont(None, 42)

        self.reset()

    def reset(self):
        # Pre-attach default cells: heart, move, damage, joint, empty, empty
        default_types = [CellType.HEART, CellType.MOVE, CellType.DAMAGE,
                         CellType.JOINT, CellType.EMPTY, CellType.EMPTY]
        cells = [Cell(slot=i, cell_type=default_types[i]) for i in range(6)]
        self.player = Player(cells)
        self.build = BuildPhase(cells)
        self.phase = "build"   # "build" | "play" | "dead"

        self.enemies: list[Enemy] = []
        self.projectiles: list[Projectile] = []
        self.spawn_timer = 0.0
        self.score = 0
        self.time_alive = 0.0

    def start_play(self):
        if self.player.heart_count == 0:
            # Force at least one heart
            self.player.cells[0].cell_type = CellType.HEART
        self.phase = "play"

    def spawn_enemy(self):
        side = random.choice(["top", "bottom", "left", "right"])
        if side == "top":    x, y = random.uniform(0, WIDTH), -30
        elif side == "bottom": x, y = random.uniform(0, WIDTH), HEIGHT+30
        elif side == "left": x, y = -30, random.uniform(0, HEIGHT)
        else:                x, y = WIDTH+30, random.uniform(0, HEIGHT)
        kind = random.choice([EnemyKind.DAMAGE, EnemyKind.SHOOTER])
        hp = 2 if kind == EnemyKind.DAMAGE else 3
        self.enemies.append(Enemy(x, y, kind, hp=hp))

    def check_collisions(self):
        px, py = self.player.pos

        # Player DAMAGE cells vs enemies
        for cell in self.player.cells:
            if cell.cell_type != CellType.DAMAGE:
                continue
            wp = cell.world_pos(self.player.pos)
            for enemy in self.enemies:
                if not enemy.dead and dist(wp, (enemy.x, enemy.y)) < HEX_RADIUS + enemy.radius:
                    enemy.take_hit()
                    if enemy.dead:
                        self.score += 10

        # Enemy body vs player core
        if self.player.invincible_timer <= 0:
            for enemy in self.enemies:
                if not enemy.dead and dist((enemy.x, enemy.y), (px, py)) < enemy.radius + CORE_RADIUS + 4:
                    alive = self.player.lose_heart()
                    if not alive:
                        self.phase = "dead"
                    break

        # Projectiles vs player core/cells
        for proj in self.projectiles:
            if not proj.from_enemy:
                continue
            hit = False
            # vs core
            if dist((proj.x, proj.y), (px, py)) < CORE_RADIUS + PROJECTILE_RADIUS:
                alive = self.player.lose_heart()
                if not alive:
                    self.phase = "dead"
                hit = True
            # vs cells
            if not hit:
                for cell in self.player.cells:
                    if cell.cell_type == CellType.EMPTY:
                        continue
                    wp = cell.world_pos(self.player.pos)
                    if dist((proj.x, proj.y), wp) < HEX_RADIUS + PROJECTILE_RADIUS:
                        if cell.cell_type == CellType.HEART:
                            alive = self.player.lose_heart()
                            if not alive:
                                self.phase = "dead"
                        else:
                            cell.flash_timer = 0.2
                        hit = True
                        break
            if hit:
                proj.lifetime = 0  # mark dead

    def draw_hud(self):
        # Hearts
        hx = 10
        hy = HEIGHT - 34
        t = self.font_small.render("LIVES:", True, COLORS["ui_dim"])
        self.screen.blit(t, (hx, hy + 4))
        hx += t.get_width() + 8
        total_hearts = self.player.heart_count
        max_slots = sum(1 for c in self.player.cells if c.cell_type == CellType.HEART or c.cell_type == CellType.EMPTY)
        for c in self.player.cells:
            if c.cell_type in (CellType.HEART, CellType.EMPTY):
                col = COLORS["heart"] if c.cell_type == CellType.HEART else (50, 30, 35)
                pygame.draw.circle(self.screen, col, (hx + 10, hy + 12), 10)
                pygame.draw.circle(self.screen, COLORS["white"], (hx + 10, hy + 12), 10, 1)
                hx += 26

        # Score & time
        st = self.font_small.render(f"SCORE: {self.score}   TIME: {self.time_alive:.0f}s", True, COLORS["ui_dim"])
        self.screen.blit(st, (WIDTH - st.get_width() - 10, HEIGHT - 28))

        # Speed info
        sp = self.font_small.render(f"SPD: {self.player.speed:.0f}", True, COLORS["ui_dim"])
        self.screen.blit(sp, (WIDTH - sp.get_width() - 10, HEIGHT - 52))

    def draw_bg(self):
        self.screen.fill(COLORS["bg"])
        # subtle hex grid
        for gx in range(-HEX_RADIUS*2, WIDTH + HEX_RADIUS*2, int(CELL_OFFSET*0.9)):
            for gy in range(-HEX_RADIUS*2, HEIGHT + HEX_RADIUS*2, int(CELL_OFFSET * math.sqrt(3) / 2)):
                offset = (HEX_RADIUS) if ((gy // int(CELL_OFFSET * math.sqrt(3)/2)) % 2 == 1) else 0
                draw_hex(self.screen, COLORS["grid"], gx + offset, gy, 10, 1)

    def draw_dead_screen(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))
        t1 = self.font_big.render("HEXCELL DESTROYED", True, COLORS["dmg_flash"])
        t2 = self.font_small.render(f"Score: {self.score}   Survived: {self.time_alive:.1f}s", True, COLORS["ui_text"])
        t3 = self.font_small.render("Press R to rebuild  |  ESC to quit", True, COLORS["ui_dim"])
        self.screen.blit(t1, t1.get_rect(center=(WIDTH//2, HEIGHT//2 - 40)))
        self.screen.blit(t2, t2.get_rect(center=(WIDTH//2, HEIGHT//2 + 10)))
        self.screen.blit(t3, t3.get_rect(center=(WIDTH//2, HEIGHT//2 + 44)))

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r:
                        self.reset()
                    elif event.key == pygame.K_RETURN and self.phase == "build":
                        self.start_play()

                if self.phase == "build":
                    self.build.handle_event(event, self.player.pos)

            # ── Update ──
            if self.phase == "play":
                self.time_alive += dt
                self.player.update(dt, mouse_pos)

                # Spawn enemies
                self.spawn_timer -= dt
                if self.spawn_timer <= 0:
                    difficulty = 1 + int(self.time_alive / 20)
                    for _ in range(difficulty):
                        self.spawn_enemy()
                    self.spawn_timer = max(1.5, ENEMY_SPAWN_INTERVAL - self.time_alive * 0.05)

                for enemy in self.enemies:
                    enemy.update(dt, self.player.pos, self.projectiles)
                self.enemies = [e for e in self.enemies if not e.dead]

                for proj in self.projectiles:
                    proj.update(dt)
                self.projectiles = [p for p in self.projectiles if not p.dead()]

                self.check_collisions()

            # ── Draw ──
            self.draw_bg()

            for proj in self.projectiles:
                pygame.draw.circle(self.screen, COLORS["proj"],
                                   (int(proj.x), int(proj.y)), PROJECTILE_RADIUS)
                pygame.draw.circle(self.screen, COLORS["white"],
                                   (int(proj.x), int(proj.y)), PROJECTILE_RADIUS, 1)

            for enemy in self.enemies:
                enemy.draw(self.screen, self.font_small)

            self.player.draw(self.screen, self.font_small, self.font_icon)

            if self.phase == "build":
                self.build.draw(self.screen, self.player.pos,
                                self.font_small, self.font_icon, self.font_ui)

            if self.phase == "play":
                self.draw_hud()

            if self.phase == "dead":
                self.player.draw(self.screen, self.font_small, self.font_icon)
                self.draw_dead_screen()

            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    Game().run()