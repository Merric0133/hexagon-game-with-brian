"""
game_scene.py — Enhanced gameplay with synergy system, better enemy AI, and polish.
"""

import pygame
import random
import math
from scene_manager import BaseScene
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_BG, COLOR_TEXT, COLOR_ACCENT, COLOR_TEXT_DIM,
    COLOR_WARNING, COLOR_DANGER, COLOR_SUCCESS,
    SCENE_MAIN_MENU, SCENE_GAME_OVER,
    SCORE_PER_KILL, SCORE_PER_WAVE,
    POWERUP_DROP_CHANCE,
    WORLD_WIDTH, WORLD_HEIGHT,
    HEX_SKINS, MAX_WAVES, BASE_ENEMIES,
    BUILD_STAGE_HEAL_AMOUNT, CellType, CELLS_PER_WAVE, BONUS_CELL_WAVES, CELL_CYCLE,
)
from ui import draw_world_grid, draw_panel, Button, render_text_centered, draw_bar
from camera import camera
from input_handler import input_handler
from asset_manager import assets
from player import Player
from enemy import Enemy, spawn_wave_enemies
from powerup import Powerup
from experience import XpOrb
from projectile import Projectile
from cell_synergy import apply_synergies_to_player, get_synergy_display
from data.progress import (
    get_selected_skin, load_progress,
    record_wave, save_highscore, get_inventory, get_honeycomb_body,
)

SCENE_BUILD = "build"


class GameScene(BaseScene):

    def __init__(self):
        super().__init__()
        self.player: Player = None
        self.enemies: list = []
        self.powerups: list = []
        self.xp_orbs: list = []
        self.projectiles: list = []

        self.wave_num: int = 1
        self.score: int = 0
        self.kills: int = 0
        self.paused: bool = False
        self.t: float = 0.0

        self._wave_state: str = "active"
        self._intermission_t: float = 0.0
        self._game_ended = False

        self._popups: list = []
        self._wave_start_time = 0.0
        self._enemies_spawned = 0

    # ────────────────────────────────────────────────────────────────────────
    # SCENE ENTRY
    # ────────────────────────────────────────────────────────────────────────

    def on_enter(self, wave_num: int = 1, body_layout: list = None, **kwargs):
        """Initialize game with player build and wave config."""
        self.wave_num = wave_num
        self.score = kwargs.get("score", 0)
        self.kills = kwargs.get("kills", 0)
        self._game_ended = False
        self.t = 0.0

        # Build player
        if body_layout is None:
            body_layout = get_honeycomb_body()
        
        self.player = Player(body_layout)
        
        # Apply synergies from build
        apply_synergies_to_player(self.player, self.player.honeycomb_body)
        self.player._recalculate_stats()

        # Restore HP and XP
        self.player.level_system.level = int(kwargs.get("level", 1))
        self.player.level_system.current_xp = int(kwargs.get("current_xp", 0))
        self.player.level_system.xp_needed = int(
            kwargs.get("xp_needed", max(100, 100 * self.player.level_system.level))
        )
        carried_hp = kwargs.get("player_hp", None)
        if carried_hp is not None:
            self.player.hp = min(self.player.max_hp, float(carried_hp) + BUILD_STAGE_HEAL_AMOUNT)

        # Apply skin
        skin_id = get_selected_skin()
        for skin in HEX_SKINS:
            if skin.get("id") == skin_id:
                self.player.set_skin(skin)
                break

        self.enemies = []
        self.powerups = []
        self.xp_orbs = []
        self.projectiles = []
        self.paused = False
        self._popups = []

        self._begin_wave(wave_num)
        camera.update(self.player.x, self.player.y, 0.0)

    # ────────────────────────────────────────────────────────────────────────
    # WAVE MANAGEMENT
    # ────────────────────────────────────────────────────────────────────────

    def _begin_wave(self, wave: int):
        """Start a new wave with scaled difficulty."""
        self.wave_num = wave
        
        # Scale enemy count by wave
        base_count = BASE_ENEMIES + (wave // 2)
        # Add bonus enemies every 5 waves
        bonus_count = (wave - 1) // 5
        total_count = base_count + bonus_count
        
        self.enemies = spawn_wave_enemies(wave, self.player.x, self.player.y, total_count)
        self._wave_state = "active"
        self._wave_start_time = self.t
        self._enemies_spawned = total_count

    def _end_wave(self):
        """Called when all enemies are dead."""
        self.score += SCORE_PER_WAVE * self.wave_num
        record_wave(self.wave_num)
        save_highscore(self.score)

        if self.wave_num >= MAX_WAVES:
            self._finish_game(won=True)
        else:
            self._wave_state = "intermission"
            self._intermission_t = 3.5

    def _advance_to_build(self):
        """Return to build phase with rewards."""
        new_cells = self._generate_cell_rewards(self.wave_num)
        self.manager.switch(
            SCENE_BUILD,
            wave_num=self.wave_num + 1,
            new_cells=new_cells,
            score=self.score,
            kills=self.kills,
            level=self.player.level_system.level,
            current_xp=self.player.level_system.current_xp,
            xp_needed=self.player.level_system.xp_needed,
            player_hp=self.player.hp,
        )

    def _generate_cell_rewards(self, wave: int) -> list:
        """Generate cell rewards for wave completion."""
        pool = [ct for ct in CELL_CYCLE if ct != CellType.EMPTY]
        
        # Bias toward useful cells at higher waves
        if wave >= 10:
            pool += [CellType.DAMAGE, CellType.SHIELD, CellType.SHIELD]
        if wave >= 20:
            pool += [CellType.DAMAGE, CellType.DAMAGE]
        if wave >= 35:
            pool += [CellType.HEART]

        count = CELLS_PER_WAVE
        if wave in BONUS_CELL_WAVES:
            count += 1

        return [random.choice(pool) for _ in range(count)]

    def _finish_game(self, won: bool):
        """End the game and transition to game over screen."""
        self._game_ended = True
        self.manager.switch(
            SCENE_GAME_OVER,
            won=won,
            wave=self.wave_num,
            score=self.score,
            kills=self.kills,
        )

    # ────────────────────────────────────────────────────────────────────────
    # UPDATE
    # ────────────────────────────────────────────────────────────────────────

    def update(self, events: list, dt: float):
        """Main game loop."""
        if self._game_ended:
            return

        input_handler.update(events, dt)

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.manager.switch(SCENE_MAIN_MENU)
                if event.key == pygame.K_p:
                    self.paused = not self.paused

        if self.paused:
            return

        self.t += dt

        # Player update
        self.player.update(input_handler, dt)
        camera.update(self.player.x, self.player.y, dt)

        # XP orbs
        for orb in self.xp_orbs[:]:
            orb.update(dt)
            if orb.check_collect(self.player):
                levels = self.player.level_system.add_xp(orb.value)
                for _ in levels:
                    self._add_popup(self.player.x, self.player.y, "LEVEL UP!", COLOR_SUCCESS, lifetime=1.2)
                self.xp_orbs.remove(orb)
            elif not orb.alive:
                self.xp_orbs.remove(orb)

        # Enemies
        self._update_enemies(dt)

        # Projectiles (for spitter enemies)
        self._update_projectiles(dt)

        # Power-ups
        for pup in self.powerups[:]:
            pup.update(dt)
            if pup.check_collect(self.player):
                pup.apply(self.player)
                self.powerups.remove(pup)
            elif not pup.alive:
                self.powerups.remove(pup)

        # Player contact-damage vs enemies
        self._check_contact_damage(dt)

        # Wave state management
        if self._wave_state == "active" and len(self.enemies) == 0:
            self._end_wave()
        elif self._wave_state == "intermission":
            self._intermission_t -= dt
            if self._intermission_t <= 0:
                self._advance_to_build()

        # Death check
        if not self.player.is_alive:
            self._finish_game(won=False)

    # ────────────────────────────────────────────────────────────────────────
    # ENEMY LOGIC
    # ────────────────────────────────────────────────────────────────────────

    def _update_enemies(self, dt: float):
        """Update all enemies and handle collision."""
        # Update positions
        for enemy in self.enemies[:]:
            enemy.update(self.player.x, self.player.y, dt)

        # Enemy-enemy collision resolution
        self._resolve_enemy_collisions()

        # Enemy-player collision
        for enemy in self.enemies[:]:
            if not enemy.alive:
                continue
            
            # Contact damage
            if enemy.collides_with_player(self.player):
                self.player.take_damage(enemy.damage * dt)

            # Spitter ranged attacks
            if enemy.enemy_type == "spitter" and enemy.can_shoot():
                self._spawn_enemy_projectile(enemy)
                enemy.reset_shoot_timer()

    def _resolve_enemy_collisions(self):
        """Push enemies apart to prevent clumping."""
        for i, enemy1 in enumerate(self.enemies):
            if not enemy1.alive:
                continue
            for j, enemy2 in enumerate(self.enemies):
                if i >= j or not enemy2.alive:
                    continue
                dx = enemy2.x - enemy1.x
                dy = enemy2.y - enemy1.y
                dist = math.hypot(dx, dy)
                min_dist = enemy1.radius + enemy2.radius
                if dist < min_dist and dist > 0:
                    overlap = min_dist - dist
                    push_x = (dx / dist) * overlap * 0.5
                    push_y = (dy / dist) * overlap * 0.5
                    enemy1.x -= push_x
                    enemy1.y -= push_y
                    enemy2.x += push_x
                    enemy2.y += push_y

    # ────────────────────────────────────────────────────────────────────────
    # PROJECTILES
    # ────────────────────────────────────────────────────────────────────────

    def _spawn_enemy_projectile(self, enemy):
        """Spitter enemies shoot projectiles at player."""
        proj = Projectile(
            enemy.x, enemy.y,
            self.player.x, self.player.y,
            speed=300,
            damage=enemy.damage * 0.7,
            radius=5,
            color=(255, 150, 80),
            lifetime=8.0,
        )
        self.projectiles.append(proj)

    def _update_projectiles(self, dt: float):
        """Update projectiles and check collisions with player."""
        for proj in self.projectiles[:]:
            proj.update(dt)
            
            # Hit player?
            if proj.collides_with_player(self.player):
                self.player.take_damage(proj.damage)
                self._add_popup(proj.x, proj.y, f"-{int(proj.damage)}", COLOR_DANGER)
                self.projectiles.remove(proj)
            elif not proj.alive:
                self.projectiles.remove(proj)

    # ────────────────────────────────────────────────────────────────────────
    # CONTACT DAMAGE
    # ────────────────────────────────────────────────────────────────────────

    def _check_contact_damage(self, dt: float):
        """Damage cells deal contact damage to nearby enemies."""
        if self.player.contact_dmg <= 0:
            return

        dmg_cells = self.player.get_damage_cell_positions()

        for cell_key, (wx, wy) in dmg_cells:
            for enemy in self.enemies[:]:
                if not enemy.alive:
                    continue
                dist = math.hypot(wx - enemy.x, wy - enemy.y)
                if dist < (32 + enemy.radius):
                    if self.player.try_contact_damage(cell_key):
                        damage = self.player.contact_dmg
                        enemy.take_damage(damage)
                        self._add_popup(enemy.x, enemy.y - 20,
                                       f"-{int(damage)}", (255, 160, 60))
                        if not enemy.alive:
                            self._on_enemy_killed(enemy)

        # Remove dead enemies
        self.enemies = [e for e in self.enemies if e.alive]

    # ────────────────────────────────────────────────────────────────────────
    # ENEMY DEATH
    # ────────────────────────────────────────────────────────────────────────

    def _on_enemy_killed(self, enemy: Enemy):
        """Handle enemy death: drops, score, etc."""
        self.kills += 1
        self.score += SCORE_PER_KILL * self.wave_num
        self._add_popup(enemy.x, enemy.y, f"+{SCORE_PER_KILL * self.wave_num}", COLOR_SUCCESS)

        # XP drop
        xp_val = 10 + self.wave_num * 2
        self.xp_orbs.append(XpOrb(enemy.x, enemy.y, xp_val))

        # Power-up drop
        if random.random() < POWERUP_DROP_CHANCE:
            self.powerups.append(Powerup(enemy.x, enemy.y))

        # Swarm splits on death
        if enemy.enemy_type == "swarm":
            for _ in range(2):
                angle = random.uniform(0, 2 * math.pi)
                offset = 40
                spawn_x = enemy.x + math.cos(angle) * offset
                spawn_y = enemy.y + math.sin(angle) * offset
                new_swarm = Enemy(spawn_x, spawn_y, self.wave_num, "swarm")
                self.enemies.append(new_swarm)

    # ────────────────────────────────────────────────────────────────────────
    # UI
    # ────────────────────────────────────────────────────────────────────────

    def _add_popup(self, wx, wy, text, color, lifetime=1.0):
        """Create floating text popup."""
        self._popups.append({
            "x": wx, "y": wy, "vx": random.uniform(-20, 20),
            "text": text, "color": color, "lifetime": lifetime, "age": 0.0
        })

    # ────────────────────────────────────────────────────────────────────────
    # DRAW
    # ────────────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface):
        """Render entire scene."""
        surface.fill(COLOR_BG)
        draw_world_grid(surface, camera)

        # World objects
        for orb in self.xp_orbs:
            orb.draw(surface, camera)
        for proj in self.projectiles:
            proj.draw(surface, camera)
        for enemy in self.enemies:
            enemy.draw(surface, camera)
        for pup in self.powerups:
            pup.draw(surface, camera)

        # Player
        self.player.draw(surface, camera)

        # HUD
        self._draw_hud(surface)
        self.player.draw_hp_bar(surface)
        self.player.draw_xp_bar(surface)
        self.player.draw_cell_legend(surface)

        # Popups
        self._draw_popups(surface)

        # Wave states
        if self._wave_state == "intermission":
            self._draw_intermission(surface)
        if self.paused:
            self._draw_pause_overlay(surface)

    def _draw_hud(self, surface):
        """Draw HUD elements."""
        render_text_centered(surface, f"Wave  {self.wave_num} / {MAX_WAVES}", 24, COLOR_TEXT, 70)
        render_text_centered(surface, f"Score  {self.score}", 18, COLOR_TEXT_DIM, 100)

        # Kill counter top-right
        font = assets.get_font("default", 16)
        k = font.render(f"Kills: {self.kills}", True, COLOR_TEXT_DIM)
        surface.blit(k, (SCREEN_WIDTH - k.get_width() - 16, 16))

        # Wave timer
        elapsed = self.t - self._wave_start_time
        t = font.render(f"Time: {int(elapsed)}s", True, COLOR_TEXT_DIM)
        surface.blit(t, (16, SCREEN_HEIGHT - 30))

    def _draw_popups(self, surface):
        """Draw floating damage/score popups."""
        font = assets.get_font("default", 16)
        for popup in self._popups[:]:
            popup["age"] += 0.016
            if popup["age"] >= popup["lifetime"]:
                self._popups.remove(popup)
                continue
            
            alpha = int(255 * (1 - popup["age"] / popup["lifetime"]))
            popup["y"] -= 30 * 0.016
            sx, sy = camera.world_to_screen(popup["x"], popup["y"])
            
            text_surf = font.render(popup["text"], True, popup["color"])
            text_surf.set_alpha(alpha)
            surface.blit(text_surf, (sx - text_surf.get_width() // 2, sy))

    def _draw_intermission(self, surface):
        """Draw wave intermission screen."""
        next_w = self.wave_num + 1
        secs = max(0, int(self._intermission_t))
        render_text_centered(surface,
            f"Wave {next_w} incoming — heading to Build Phase in {secs}s…",
            28, COLOR_ACCENT, SCREEN_HEIGHT // 2)

    def _draw_pause_overlay(self, surface):
        """Draw pause overlay."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))
        render_text_centered(surface, "PAUSED", 48, COLOR_TEXT, SCREEN_HEIGHT // 2)
