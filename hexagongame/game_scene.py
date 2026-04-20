# =============================================================================
# scenes/game_py — Main gameplay: waves, enemies, combat, scoring
# =============================================================================
import pygame
import random
import math
from scene_manager import BaseScene
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG, COLOR_TEXT,
    COLOR_ACCENT, COLOR_TEXT_DIM, COLOR_WARNING, COLOR_DANGER, COLOR_SUCCESS,
    SCENE_MAIN_MENU, SCENE_GAME_OVER, HEX_SKINS,
    SCORE_PER_KILL, SCORE_PER_WAVE, POWERUP_DROP_CHANCE,
    ENEMY_SPAWN_RATE, WORLD_WIDTH, WORLD_HEIGHT,
)
from ui import (
    draw_world_grid, draw_panel, Button,
    render_text_centered, draw_bar,
)
from camera import camera
from input_handler import input_handler
from asset_manager import assets
from player import Player
from enemy import Enemy, spawn_wave_enemies
from powerup import Powerup
from data.progress import get_selected_skin, load_progress, record_wave, save_highscore
from projectile import Projectile
from experience import XpOrb
from abilities import ABILITIES

# Total waves before the game is "won"
MAX_WAVES = 50
# How many enemies per wave (scales up)
BASE_ENEMIES = 5


class GameScene(BaseScene):
    def __init__(self):
        super().__init__()
        self.player: Player = None
        self.enemies: list[Enemy] = []
        self.powerups: list[Powerup] = []
        self.xp_orbs: list[XpOrb] = []

        self.wave_num: int = 1
        self.score: int = 0
        self.kills: int = 0
        self.paused: bool = False
        self.t: float = 0.0

        self._wave_state: str = "spawning"
        self._intermission_t: float = 0.0
        self._remaining_spawns: int = 0
        self._spawn_timer: float = 0.0

        self._popups: list[dict] = []
        self._game_ended = False
        
        self._level_up_pending = False
        self._level_up_choices = []
        self._mouse_pressed_last = False

    def on_enter(self, **kwargs):
        self.player = Player()
        skin_id = get_selected_skin()
        for skin in HEX_SKINS:
            if skin.get("id") == skin_id:
                self.player.set_skin(skin)
                break
        
        self.enemies = []
        self.powerups = []
        self.xp_orbs = []
        self.wave_num = 1
        self.score = 0
        self.kills = 0
        self.paused = False
        self.t = 0.0
        self._wave_state = "spawning"
        self._level_up_pending = False
        self._begin_wave(1)
        camera.update(self.player.x, self.player.y, 0.0)

    def _begin_wave(self, wave: int):
        self.wave_num = wave
        self.enemies = spawn_wave_enemies(wave, self.player.x, self.player.y,
                                          BASE_ENEMIES + wave // 2)
        self._wave_state = "active"

    def _end_wave(self):
        self.score += SCORE_PER_WAVE * self.wave_num
        if self.wave_num >= MAX_WAVES:
            self._finish_game(won=True)
        else:
            self._wave_state = "intermission"
            self._intermission_t = 4.0

    def _next_wave(self):
        self._begin_wave(self.wave_num + 1)

    def _finish_game(self, won: bool):
        self._game_ended = True
        record_wave(self.wave_num)
        self.manager.switch(SCENE_GAME_OVER,
                           won=won, wave=self.wave_num, score=self.score,
                           kills=self.kills)

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

        if self.paused and not self._level_up_pending:
            return

        self.t += dt

        # Player update
        self.player.update(input_handler, dt)
        camera.update(self.player.x, self.player.y, dt)

        # Update XP orbs
        for orb in self.xp_orbs[:]:
            orb.update(dt)
            if orb.check_collect(self.player):
                levels = self.player.level_system.add_xp(orb.value)
                self.xp_orbs.remove(orb)
                if levels:
                    self._show_level_up()
            elif not orb.alive:
                self.xp_orbs.remove(orb)

        # Update enemies
        self._update_enemies(dt)

        # Update powerups
        for pup in self.powerups[:]:
            pup.update(dt)
            if pup.check_collect(self.player):
                pup.apply(self.player)
                self.powerups.remove(pup)

        # Projectile-enemy collision
        for proj in self.player.projectiles[:]:
            for enemy in self.enemies[:]:
                if proj.collides_with_enemy(enemy):
                    enemy.take_damage(proj.ability["damage"])
                    proj.alive = False
                    if not enemy.alive:
                        self._on_enemy_killed(enemy)
                        self.enemies.remove(enemy)

        # Wave management
        if self._wave_state == "active" and len(self.enemies) == 0:
            self._end_wave()
        elif self._wave_state == "intermission":
            self._intermission_t -= dt
            if self._intermission_t <= 0:
                self._next_wave()

        # Check player death
        if self.player.hp <= 0:
            self._finish_game(won=False)

    def _show_level_up(self):
        """Show random ability choices."""
        choices = random.sample(ABILITIES, min(3, len(ABILITIES)))
        self._level_up_choices = choices
        self._level_up_pending = True
        self.paused = True

    def _update_enemies(self, dt: float):
        for enemy in self.enemies[:]:
            enemy.update(self.player.x, self.player.y, dt)
            
            # Enemy-player collision (damage)
            if enemy.collides_with_player(self.player):
                self.player.take_damage(enemy.damage)

    def _on_enemy_killed(self, enemy: Enemy):
        self.kills += 1
        self.score += SCORE_PER_KILL * self.wave_num
        self._add_popup(enemy.x, enemy.y, f"+{SCORE_PER_KILL}", COLOR_SUCCESS)
        
        # Drop XP
        xp_val = 10 + self.wave_num * 2
        orb = XpOrb(enemy.x, enemy.y, xp_val)
        self.xp_orbs.append(orb)

    def _add_popup(self, wx, wy, text, color, lifetime=1.2):
        self._popups.append({
            "x": wx, "y": wy, "text": text, "color": color,
            "lifetime": lifetime, "age": 0.0
        })

    def draw(self, surface: pygame.Surface):
        surface.fill(COLOR_BG)
        
        # World grid
        draw_world_grid(surface, camera)
        
        # Entities
        for orb in self.xp_orbs:
            orb.draw(surface, camera)
        
        for enemy in self.enemies:
            enemy.draw(surface, camera)
        
        for proj in self.player.projectiles:
            proj.draw(surface, camera)
        
        for pup in self.powerups:
            pup.draw(surface, camera)
        
        self.player.draw(surface, camera)
        
        # HUD
        self._draw_hud(surface)
        self.player.draw_hp_bar(surface, camera)
        self.player.draw_xp_bar(surface)
        self.player.draw_abilities(surface)
        
        self._draw_popups(surface)
        
        if self._wave_state == "intermission":
            self._draw_intermission(surface)
        
        if self.paused and not self._level_up_pending:
            self._draw_pause_overlay(surface)
        
        # Level-up menu
        if self._level_up_pending:
            self._draw_level_up_menu(surface)

    def _draw_hud(self, surface: pygame.Surface):
        render_text_centered(surface, f"Wave {self.wave_num}/{MAX_WAVES}",
                           24, COLOR_TEXT, 60)
        render_text_centered(surface, f"Score: {self.score}",
                           20, COLOR_TEXT_DIM, 95)
        render_text_centered(surface, f"Lvl {self.player.level_system.level}",
                           18, COLOR_ACCENT, 680)

    def _draw_popups(self, surface: pygame.Surface):
        for popup in self._popups[:]:
            popup["age"] += 0.016
            if popup["age"] >= popup["lifetime"]:
                self._popups.remove(popup)

    def _draw_level_up_menu(self, surface: pygame.Surface):
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))
        
        # Title
        render_text_centered(surface, "LEVEL UP!", 48, COLOR_SUCCESS, 100)
        render_text_centered(surface, "Choose an ability:", 24, COLOR_TEXT, 160)
        
        # Ability choice buttons
        bw, bh = 300, 70
        cx = SCREEN_WIDTH // 2 - bw // 2
        
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]
        
        for i, ability in enumerate(self._level_up_choices):
            y = 220 + i * 100
            rect = pygame.Rect(cx, y, bw, bh)
            
            # Hover effect
            is_hover = rect.collidepoint(mouse_pos)
            draw_color = ability["color"] if is_hover else (100, 100, 100)
            
            # Draw button
            pygame.draw.rect(surface, (30, 30, 40), rect, border_radius=8)
            pygame.draw.rect(surface, draw_color, rect, 3, border_radius=8)
            
            # Ability name
            font_name = assets.get_font("default", 22)
            label = font_name.render(ability["name"], True, draw_color)
            surface.blit(label, (cx + 20, y + 10))
            
            # Description
            font_desc = assets.get_font("default", 14)
            desc = font_desc.render(ability["description"], True, (200, 200, 200))
            surface.blit(desc, (cx + 20, y + 40))
            
            # Click detection
            if is_hover and mouse_pressed and not self._mouse_pressed_last:
                self.player.add_ability(ability)
                self._level_up_pending = False
                self.paused = False
                self._level_up_choices = []
        
        self._mouse_pressed_last = mouse_pressed

    def _draw_pause_overlay(self, surface: pygame.Surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))
        render_text_centered(surface, "PAUSED", 48, COLOR_TEXT, SCREEN_HEIGHT // 2)

    def _draw_intermission(self, surface: pygame.Surface):
        render_text_centered(surface, f"Wave {self.wave_num + 1} in {max(0, int(self._intermission_t))}...",
                           32, COLOR_ACCENT, SCREEN_HEIGHT // 2)
