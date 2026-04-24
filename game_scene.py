"""
game_scene.py — Main gameplay: waves, enemies, combat, scoring.

Flow:
  BuildScene  →  GameScene  →  (wave cleared)  →  BuildScene (next wave)
                            →  (player dead)   →  GameOverScene
"""

import pygame
import random
import math
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
    HEX_SKINS,
    MAX_WAVES, BASE_ENEMIES,
    BUILD_STAGE_HEAL_AMOUNT,
    CellType,
    CELLS_PER_WAVE, BONUS_CELL_WAVES, CELL_CYCLE,
)
from ui import draw_world_grid, draw_panel, Button, render_text_centered, draw_bar
from camera import camera
from input_handler import input_handler
from asset_manager import assets
from player import Player
from enemy import Enemy, spawn_wave_enemies
from powerup import Powerup
from experience import XpOrb
from data.progress import (
    get_selected_skin, load_progress,
    record_wave, save_highscore, get_inventory, get_honeycomb_body,
)

# Scene name for build (avoid circular import by keeping as string)
SCENE_BUILD = "build"


class GameScene(BaseScene):

    def __init__(self):
        super().__init__()
        self.player: Player = None
        self.enemies:  list[Enemy]    = []
        self.powerups: list[Powerup]  = []
        self.xp_orbs:  list[XpOrb]   = []


        self.wave_num:  int   = 1
        self.score:     int   = 0
        self.kills:     int   = 0
        self.paused:    bool  = False
        self.t:         float = 0.0

        self._wave_state:     str   = "active"
        self._intermission_t: float = 0.0
        self._game_ended            = False

        self._popups: list[dict] = []
        self._contact_dmg_cooldown = 0.0

    # ── Scene entry ───────────────────────────────────────────────────────────

    def on_enter(self, wave_num: int = 1, body_layout: list = None, **kwargs):
        """
        wave_num    — wave to start (1 for a fresh game)
        body_layout — list of honeycomb cell dicts from build scene
        """
        self.wave_num = wave_num
        self.score    = kwargs.get("score", 0)
        self.kills    = kwargs.get("kills", 0)
        self._game_ended = False
        self.t = 0.0

        # Build player with equipped honeycomb body
        if body_layout is None:
            body_layout = get_honeycomb_body()
        self.player = Player(body_layout)
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

        self.enemies  = []
        self.powerups = []
        self.xp_orbs  = []
        self.paused   = False

        self._begin_wave(wave_num)
        camera.update(self.player.x, self.player.y, 0.0)

    # ── Wave management ───────────────────────────────────────────────────────

    def _begin_wave(self, wave: int):
        self.wave_num    = wave
        self.enemies     = spawn_wave_enemies(wave, self.player.x, self.player.y,
                                              BASE_ENEMIES + wave // 2)
        self._wave_state = "active"

    def _end_wave(self):
        """Called when all enemies in a wave are dead."""
        self.score += SCORE_PER_WAVE * self.wave_num
        record_wave(self.wave_num)
        save_highscore(self.score)

        if self.wave_num >= MAX_WAVES:
            self._finish_game(won=True)
        else:
            self._wave_state = "intermission"
            self._intermission_t = 3.5

    def _advance_to_build(self):
        """Go to build scene with the new cell rewards."""
        new_cells = self._generate_cell_rewards(self.wave_num)
        self.manager.switch(
            SCENE_BUILD,
            wave_num  = self.wave_num + 1,
            new_cells = new_cells,
            # carry score/kills through
            score     = self.score,
            kills     = self.kills,
            level     = self.player.level_system.level,
            current_xp = self.player.level_system.current_xp,
            xp_needed = self.player.level_system.xp_needed,
            player_hp = self.player.hp,
        )

    def _generate_cell_rewards(self, wave: int) -> list:
        """
        Returns a list of CellType to award the player.
        Base: CELLS_PER_WAVE random cells.
        Bonus: one extra on milestone waves.
        """
        pool = [ct for ct in CELL_CYCLE if ct != CellType.EMPTY]
        # Bias toward damage/shield at higher waves
        if wave >= 10:
            pool += [CellType.DAMAGE, CellType.SHIELD]
        if wave >= 20:
            pool += [CellType.DAMAGE]

        count = CELLS_PER_WAVE
        if wave in BONUS_CELL_WAVES:
            count += 1

        return [random.choice(pool) for _ in range(count)]

    def _finish_game(self, won: bool):
        self._game_ended = True
        self.manager.switch(
            SCENE_GAME_OVER,
            won   = won,
            wave  = self.wave_num,
            score = self.score,
            kills = self.kills,
        )

    # ── Main update ───────────────────────────────────────────────────────────

    def update(self, events: list, dt: float):
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

        # Player
        self.player.update(input_handler, dt)
        camera.update(self.player.x, self.player.y, dt)

        # XP orbs
        for orb in self.xp_orbs[:]:
            orb.update(dt)
            if orb.check_collect(self.player):
                self.player.level_system.add_xp(orb.value)
                self.xp_orbs.remove(orb)
            elif not orb.alive:
                self.xp_orbs.remove(orb)

        # Enemies
        self._update_enemies(dt)

        # Powerups
        for pup in self.powerups[:]:
            pup.update(dt)
            if pup.check_collect(self.player):
                pup.apply(self.player)
                self.powerups.remove(pup)
            elif not pup.alive:
                self.powerups.remove(pup)

        # Player contact-damage cells vs enemies
        self._check_contact_damage(dt)

        # Wave state
        if self._wave_state == "active" and len(self.enemies) == 0:
            self._end_wave()
        elif self._wave_state == "intermission":
            self._intermission_t -= dt
            if self._intermission_t <= 0:
                self._advance_to_build()

        # Player death
        if not self.player.is_alive:
            self._finish_game(won=False)

    def _resolve_enemy_collisions(self):
        """Resolve collisions between enemies by pushing them apart."""
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
                    # Push enemies apart
                    overlap = min_dist - dist
                    push_x = (dx / dist) * overlap * 0.5
                    push_y = (dy / dist) * overlap * 0.5
                    enemy1.x -= push_x
                    enemy1.y -= push_y
                    enemy2.x += push_x
                    enemy2.y += push_y

    # ── Enemy update ─────────────────────────────────────────────────────────

    def _update_enemies(self, dt: float):
        # Update enemy positions
        for enemy in self.enemies[:]:
            enemy.update(self.player.x, self.player.y, dt)

        # Check enemy-enemy collisions
        self._resolve_enemy_collisions()

        # Enemy collisions against body cells/core
        for enemy in self.enemies[:]:
            hit_type = self.player.apply_enemy_collision(enemy, enemy.damage * dt * 5)  # Increased damage multiplier
            if hit_type == "heart":
                self._add_popup(enemy.x, enemy.y - 24, "HEART HIT!", COLOR_DANGER, lifetime=0.55)

    # ── Contact-damage aura ───────────────────────────────────────────────────

    def _check_contact_damage(self, dt: float):
        """
        Damage cells on the player deal contact damage to adjacent enemies.
        Each slot has its own cooldown managed in player.
        """
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
                        enemy.take_damage(self.player.contact_dmg)
                        self._add_popup(enemy.x, enemy.y - 20,
                                        f"-{int(self.player.contact_dmg)}",
                                        (255, 160, 60))
                        if not enemy.alive:
                            self._on_enemy_killed(enemy)
                            if enemy in self.enemies:
                                self.enemies.remove(enemy)

    # ── Enemy killed ──────────────────────────────────────────────────────────

    def _on_enemy_killed(self, enemy: Enemy):
        self.kills += 1
        self.score += SCORE_PER_KILL * self.wave_num
        self._add_popup(enemy.x, enemy.y, f"+{SCORE_PER_KILL * self.wave_num}", COLOR_SUCCESS)

        # XP orb
        xp_val = 10 + self.wave_num * 2
        self.xp_orbs.append(XpOrb(enemy.x, enemy.y, xp_val))

        # Power-up drop
        if random.random() < POWERUP_DROP_CHANCE:
            self.powerups.append(Powerup(enemy.x, enemy.y))

    # ── Popups ────────────────────────────────────────────────────────────────

    def _add_popup(self, wx, wy, text, color, lifetime=1.0):
        self._popups.append({
            "x": wx, "y": wy, "vx": random.uniform(-20, 20),
            "text": text, "color": color, "lifetime": lifetime, "age": 0.0
        })

    # ── Draw ─────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface):
        surface.fill(COLOR_BG)
        draw_world_grid(surface, camera)

        for orb in self.xp_orbs:
            orb.draw(surface, camera)
        for enemy in self.enemies:
            enemy.draw(surface, camera)
        for pup in self.powerups:
            pup.draw(surface, camera)

        self.player.draw(surface, camera)

        # HUD
        self._draw_hud(surface)
        self.player.draw_hp_bar(surface)
        self.player.draw_xp_bar(surface)
        self.player.draw_cell_legend(surface)

        self._draw_popups(surface)

        if self._wave_state == "intermission":
            self._draw_intermission(surface)
        if self.paused:
            self._draw_pause_overlay(surface)

    def _draw_hud(self, surface):
        render_text_centered(surface, f"Wave  {self.wave_num} / {MAX_WAVES}", 24, COLOR_TEXT, 70)
        render_text_centered(surface, f"Score  {self.score}", 18, COLOR_TEXT_DIM, 100)

        # Kill counter top-right
        font = assets.get_font("default", 16)
        k = font.render(f"Kills: {self.kills}", True, COLOR_TEXT_DIM)
        surface.blit(k, (SCREEN_WIDTH - k.get_width() - 16, 16))

    def _draw_popups(self, surface):
        font = assets.get_font("default", 16)
        for popup in self._popups[:]:
            popup["age"] += 0.016
            if popup["age"] >= popup["lifetime"]:
                self._popups.remove(popup)
                continue
            alpha = int(255 * (1 - popup["age"] / popup["lifetime"]))
            popup["y"] -= 30 * 0.016
            sx, sy = camera.world_to_screen(popup["x"], popup["y"])
            surf = font.render(popup["text"], True, popup["color"])
            surf.set_alpha(alpha)
            surface.blit(surf, (sx - surf.get_width() // 2, sy))

    def _draw_intermission(self, surface):
        next_w = self.wave_num + 1
        secs   = max(0, int(self._intermission_t))
        render_text_centered(surface,
            f"Wave {next_w} incoming — heading to Build Phase in {secs}s…",
            28, COLOR_ACCENT, SCREEN_HEIGHT // 2)

    def _draw_pause_overlay(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))
        render_text_centered(surface, "PAUSED", 48, COLOR_TEXT, SCREEN_HEIGHT // 2)
