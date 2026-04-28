import pygame
import pymunk
import math
import random
from core.constants import *
from core.camera import Camera
from core.save_manager import (load_all_slots, save_slot, delete_slot,
                                default_strain, load_global_achievements,
                                save_global_achievements, NUM_SLOTS)
from core.world import World
from entities.player import Player
from entities.particles import ParticleSystem
from ui.hud import HUD
from ui.menus import MainMenu, StrainSelectMenu, RaceSelectMenu
from ui.editor import CellEditor
from ui.xenopedia import Xenopedia
from ui.achievements_screen import AchievementsScreen
from ui.tutorial import Tutorial

class Game:
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.sw, self.sh = screen.get_size()
        self.state = STATE_MAIN_MENU
        self.game_time = 0.0
        self.dt = 0.0

        # Physics
        self.space = pymunk.Space()
        self.space.gravity = GRAVITY
        self.space.damping = 0.85

        # Camera
        self.camera = Camera(self.sw, self.sh)
        self.camera.x = 2000 - self.sw / 2
        self.camera.y = 2000 - self.sh / 2

        # Particles
        self.particles = ParticleSystem()

        # UI
        self.main_menu      = MainMenu(self.sw, self.sh)
        self.strain_menu    = StrainSelectMenu(self.sw, self.sh)
        self.race_menu      = RaceSelectMenu(self.sw, self.sh)
        self.xenopedia      = Xenopedia(self.sw, self.sh)
        self.achievements_screen = AchievementsScreen(self.sw, self.sh)
        self.hud            = None
        self.editor         = None

        # Game objects
        self.player         = None
        self.world          = None
        self.active_slot    = None
        self.pending_slot   = None

        # Achievements
        self.global_achievements = load_global_achievements()

        # Tutorial
        self.tutorial = None

        # Collision handlers
        self._setup_collisions()

        # Pause overlay
        self.pause_font = pygame.font.SysFont("consolas", 36, bold=True)
        self.pause_small = pygame.font.SysFont("consolas", 18)
        
        # Map system
        self.map_open = False
        self.map_font = pygame.font.SysFont("consolas", 14, bold=True)
        self.map_font_small = pygame.font.SysFont("consolas", 11)

    def _setup_collisions(self):
        self.space.on_collision(1, 2, begin=self._on_player_enemy_collision)

    def _on_player_enemy_collision(self, arbiter, space, data):
        if not self.player or not self.player.alive:
            return
        # Find which enemy was hit
        shapes = arbiter.shapes
        contact_point = arbiter.contact_point_set.points[0].point_a if arbiter.contact_point_set.points else None
        cp = (contact_point.x, contact_point.y) if contact_point else None

        for enemy in (self.world.enemies if self.world else []):
            if any(s in shapes for s in enemy.shapes):
                # Spike cells deal damage
                for cell in self.player.cells:
                    if cell.cell_type == "spike" and cell.alive:
                        dmg = cell.data.get("damage", 18)
                        # Rage mode damage boost
                        if self.player.rage_mode_active:
                            dmg = int(dmg * 1.5)
                        if hasattr(cell, "mutation_bonus"):
                            dmg = int(dmg * cell.mutation_bonus.get("damage", 1.0))
                        enemy.take_damage(dmg, cp)
                        # Leech heal
                        if "Vampiric Shock" in self.player.active_synergies or \
                           any(c.cell_type == "leech" for c in self.player.cells):
                            heal = int(dmg * 0.25)
                            for c in self.player.cells:
                                if c.cell_type == "leech":
                                    c.heal(heal)
                        self.particles.emit(cp or self.player.get_center(),
                                            cell.data["glow"], count=8, speed=100)
                        self.camera.shake(4.0)
                # Enemy deals damage to player
                for ecell in enemy.cells:
                    if ecell.cell_type == "spike" and ecell.alive:
                        self.player.take_damage(ecell.data.get("damage", 12), cp)
                        self.camera.shake(6.0)
                break

    def run(self):
        while True:
            self.dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            self.game_time += self.dt
            self._handle_events()
            self._update()
            self._draw()
            pygame.display.flip()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._save_current()
                pygame.quit()
                import sys; sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._handle_escape()
                if event.key == pygame.K_TAB and self.state == STATE_GAME:
                    self._open_editor()
                if event.key == pygame.K_m and self.state == STATE_GAME:
                    # Toggle map
                    if hasattr(self, 'map_open'):
                        self.map_open = not self.map_open
                    else:
                        self.map_open = True
                if event.key == pygame.K_SPACE and self.state == STATE_GAME:
                    if self.player:
                        mx, my = pygame.mouse.get_pos()
                        result = self.player.trigger_ability(self.camera, (mx, my))
                        self._handle_ability(result)
                # Keybind abilities Q, E, R, F
                if event.key == pygame.K_q and self.state == STATE_GAME:
                    if self.player:
                        result = self.player.trigger_keybind_ability('q')
                        if result == 'dash':
                            self.particles.emit(self.player.get_center(), (0, 255, 255), count=20, speed=200)
                            self.camera.shake(3.0)
                if event.key == pygame.K_e and self.state == STATE_GAME:
                    if self.player:
                        result = self.player.trigger_keybind_ability('e')
                        if result == 'shield_burst':
                            self.particles.emit(self.player.get_center(), (0, 180, 255), count=30, speed=150)
                            self.camera.shake(4.0)
                            # Knockback nearby enemies
                            cx, cy = self.player.get_center()
                            for e in (self.world.enemies if self.world else []):
                                from core.utils import distance
                                dist = distance((cx, cy), e.get_center())
                                if dist < 180:
                                    # Apply knockback
                                    dx = e.get_center()[0] - cx
                                    dy = e.get_center()[1] - cy
                                    knockback = 3000
                                    e.apply_force(dx * knockback / max(dist, 1), dy * knockback / max(dist, 1))
                if event.key == pygame.K_r and self.state == STATE_GAME:
                    if self.player:
                        result = self.player.trigger_keybind_ability('r')
                        if result == 'heal_pulse':
                            self.particles.emit(self.player.get_center(), (0, 255, 100), count=25, speed=120)
                            self.camera.shake(2.0)
                            if self.hud:
                                self.hud.notify("HEAL PULSE!", (0, 255, 100))
                if event.key == pygame.K_f and self.state == STATE_GAME:
                    if self.player:
                        result = self.player.trigger_keybind_ability('f')
                        if result == 'rage_mode':
                            self.particles.emit(self.player.get_center(), (255, 60, 0), count=40, speed=250)
                            self.camera.shake(6.0)
                            if self.hud:
                                self.hud.notify("RAGE MODE ACTIVATED!", (255, 60, 0))
                if event.key == pygame.K_DELETE and self.state == STATE_STRAIN_SELECT:
                    pass  # handled below

            # State-specific event routing
            if self.state == STATE_MAIN_MENU:
                result = self.main_menu.handle_event(event)
                if result == "play":
                    self.strain_menu.refresh()
                    self.state = STATE_STRAIN_SELECT
                elif result == "xeno":
                    self.state = STATE_XENOPEDIA
                elif result == "achiev":
                    self.state = STATE_ACHIEVEMENTS
                elif result == "quit":
                    pygame.quit()
                    import sys; sys.exit()

            elif self.state == STATE_STRAIN_SELECT:
                result = self.strain_menu.handle_event(event)
                if result:
                    action, slot = result
                    if action == "back":
                        self.state = STATE_MAIN_MENU
                    elif action == "select":
                        self.pending_slot = slot
                        slot_data = load_all_slots()[slot]
                        if slot_data is None:
                            self.state = STATE_RACE_SELECT
                        else:
                            self._load_strain(slot, slot_data)
                # Delete slot
                if event.type == pygame.KEYDOWN and event.key == pygame.K_DELETE:
                    mx, my = pygame.mouse.get_pos()
                    for i, rect in enumerate(self.strain_menu.slot_rects):
                        if rect.collidepoint(mx, my):
                            delete_slot(i)
                            self.strain_menu.refresh()

            elif self.state == STATE_RACE_SELECT:
                result = self.race_menu.handle_event(event)
                if result:
                    action, val = result
                    if action == "back":
                        self.state = STATE_STRAIN_SELECT
                    elif action == "confirm":
                        strain = default_strain(self.pending_slot, val)
                        save_slot(self.pending_slot, strain)
                        self._load_strain(self.pending_slot, strain)

            elif self.state == STATE_EDITOR:
                result = self.editor.handle_event(event)
                if result == "back":
                    self.state = STATE_GAME if self.player else STATE_STRAIN_SELECT
                elif result == "play":
                    self._apply_editor_layout()
                    self.state = STATE_GAME

            elif self.state == STATE_XENOPEDIA:
                result = self.xenopedia.handle_event(event)
                if result == "back":
                    self.state = STATE_MAIN_MENU

            elif self.state == STATE_ACHIEVEMENTS:
                result = self.achievements_screen.handle_event(event, self.global_achievements)
                if result == "back":
                    self.state = STATE_MAIN_MENU

            elif self.state == STATE_PAUSED:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = STATE_GAME
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self._handle_pause_click(event.pos)

            elif self.state == STATE_GAME:
        # Tutorial intercepts input while active
                if self.tutorial and self.tutorial.active:
                    self.tutorial.handle_event(event)
                    # Check if tutorial wants to spawn mini boss
                    if self.tutorial.dismissed and self.tutorial.spawn_miniboss:
                        self._spawn_tutorial_miniboss()
                        self.tutorial.spawn_miniboss = False

            elif self.state == STATE_GAME_OVER:
                if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.KEYDOWN:
                    self.state = STATE_STRAIN_SELECT
                    self.strain_menu.refresh()

    def _handle_escape(self):
        if self.state == STATE_GAME:
            self.state = STATE_PAUSED
        elif self.state == STATE_PAUSED:
            self.state = STATE_GAME
        elif self.state in (STATE_EDITOR, STATE_XENOPEDIA, STATE_ACHIEVEMENTS,
                            STATE_STRAIN_SELECT, STATE_RACE_SELECT):
            self.state = STATE_MAIN_MENU

    def _load_strain(self, slot, strain_data):
        self.active_slot = slot
        # Clean up old physics
        self._cleanup_world()
        self.space = pymunk.Space()
        self.space.gravity = GRAVITY
        self.space.damping = 0.85
        self._setup_collisions()

        biome = strain_data.get("current_biome", "membrane")
        level = strain_data.get("level", 1)
        self.world = World(self.space, biome, level)
        center = 2000.0
        self.player = Player(self.space, (center, center), strain_data)
        self.camera.x = center - self.sw / 2
        self.camera.y = center - self.sh / 2
        self.camera.set_zoom_for_scale(self.player.scale)
        self.hud = HUD(self.sw, self.sh)
        self.particles = ParticleSystem()
        self.editor = CellEditor(self.sw, self.sh, strain_data)
        # Show tutorial for new strains (level 1, no prior play)
        if strain_data.get("level", 1) == 1 and strain_data.get("stats", {}).get("enemies_killed", 0) == 0:
            self.tutorial = Tutorial(self.sw, self.sh)
        else:
            self.tutorial = None
        self.state = STATE_EDITOR

    def _cleanup_world(self):
        if self.world:
            for e in self.world.enemies:
                for s in e.shapes:
                    if s in self.space.shapes:
                        self.space.remove(s)
                if e.body in self.space.bodies:
                    self.space.remove(e.body)
        if self.player:
            for s in self.player.shapes:
                if s in self.space.shapes:
                    self.space.remove(s)
            if self.player.body in self.space.bodies:
                self.space.remove(self.player.body)
        self.world = None
        self.player = None

    def _open_editor(self):
        if self.player:
            strain = self.player.to_save_data()
            self.editor = CellEditor(self.sw, self.sh, strain)
            self.state = STATE_EDITOR

    def _apply_editor_layout(self):
        if not self.player or not self.editor:
            return
        new_layout = self.editor.get_layout()
        # Rebuild player with new layout
        strain = self.player.to_save_data()
        layout_serialized = {f"{k[0]},{k[1]}": v for k, v in new_layout.items()}
        strain["cell_layout"] = layout_serialized
        # Remove old player physics
        for s in self.player.shapes:
            if s in self.space.shapes:
                self.space.remove(s)
        if self.player.body in self.space.bodies:
            self.space.remove(self.player.body)
        pos = self.player.get_center()
        self.player = Player(self.space, pos, strain)
        self.camera.set_zoom_for_scale(self.player.scale)

    def _handle_ability(self, result):
        if not result or not self.player:
            return
        cx, cy = self.player.get_center()
        if result == "photon_burst":
            self.particles.emit((cx, cy), (255, 255, 200), count=30, speed=300)
            self.camera.shake(5.0)
            for e in (self.world.enemies if self.world else []):
                from core.utils import distance
                if distance((cx,cy), e.get_center()) < 200:
                    e.status_effects["blinded"] = 1.5
        elif result == "zap":
            self.particles.emit_zap((cx, cy))
            self.camera.shake(3.0)
            for e in (self.world.enemies if self.world else []):
                from core.utils import distance
                if distance((cx,cy), e.get_center()) < 150:
                    e.take_damage(25, (cx,cy))
                    self.particles.emit_zap(e.get_center())
        elif result == "explode":
            self.particles.emit_explosion((cx,cy), (255,100,0))
            self.camera.shake(12.0)
            for e in (self.world.enemies if self.world else []):
                from core.utils import distance
                if distance((cx,cy), e.get_center()) < 150:
                    e.take_damage(60, (cx,cy))
        elif result == "fission":
            # Shed outermost cell
            if len(self.player.cells) > 1:
                outer = self.player.cells[-1]
                self.particles.emit_cell_death(outer.world_pos, outer.data["glow"])
                outer.hp = 0
                outer.alive = False

    def _spawn_tutorial_miniboss(self):
        """Spawn a cracked mini boss for tutorial combat test."""
        if not self.world or not self.player:
            return
        from entities.enemy import Enemy
        # Spawn a tough enemy near the player
        px, py = self.player.get_center()
        boss_pos = (px + 400, py)
        # Create a beefed-up hunter as mini boss
        miniboss = Enemy(self.space, boss_pos, "hunter", level=self.player.level + 3,
                        biome_modifier=None)
        # Make it cracked — boost stats
        miniboss.scale = 1.8
        for cell in miniboss.cells:
            cell.hp = int(cell.hp * 2.5)
            cell.max_hp = int(cell.max_hp * 2.5)
        miniboss.xp_value = int(miniboss.xp_value * 3)
        self.world.enemies.append(miniboss)
        if self.hud:
            self.hud.notify("MINI BOSS SPAWNED! Prepare yourself!", (255, 60, 60))
    
    def _spawn_miniboss(self, domain):
        """Spawn a unique mini-boss for a domain."""
        if not self.world or not self.player:
            return
        from entities.enemy import Enemy
        
        boss_pos = domain["pos"]
        boss_type = domain.get("boss_type", "hunter")
        
        # Create powerful mini-boss
        miniboss = Enemy(self.space, boss_pos, boss_type, 
                        level=self.player.level + 5,
                        biome_modifier=None)
        
        # Make it VERY powerful
        miniboss.scale = 2.2
        for cell in miniboss.cells:
            cell.hp = int(cell.hp * 4.0)
            cell.max_hp = int(cell.max_hp * 4.0)
        miniboss.xp_value = int(miniboss.xp_value * 5)
        miniboss.is_miniboss = True  # Flag for tracking
        
        self.world.enemies.append(miniboss)
        self._miniboss_active = True
        
        if self.hud:
            self.hud.notify(f"{domain['name']} AWAKENS!", domain["color"], duration=4.0)
            self.hud.notify(f"Reward: {domain['reward_desc']}", (255, 220, 0), duration=5.0)
        
        self.camera.shake(12.0)
        self.particles.emit(boss_pos, domain["color"], count=50, speed=300)

    def _handle_pause_click(self, pos):
        cx = self.sw // 2
        if pygame.Rect(cx-80, self.sh//2+20, 160, 44).collidepoint(pos):
            self.state = STATE_GAME
        elif pygame.Rect(cx-80, self.sh//2+80, 160, 44).collidepoint(pos):
            self._save_current()
            self.state = STATE_STRAIN_SELECT
            self.strain_menu.refresh()
        elif pygame.Rect(cx-80, self.sh//2+140, 160, 44).collidepoint(pos):
            self._open_editor()

    def _save_current(self):
        if self.player and self.active_slot is not None:
            data = self.player.to_save_data()
            save_slot(self.active_slot, data)
        save_global_achievements(self.global_achievements)

    def _update(self):
        if self.state == STATE_GAME:
            self._update_game()
        elif self.state == STATE_PAUSED:
            pass
        self.hud.update(self.dt) if self.hud else None

    def _update_game(self):
        if not self.player or not self.world:
            return
        keys = pygame.key.get_pressed()
        mx, my = pygame.mouse.get_pos()
        self.player.handle_input(keys, (mx, my), self.camera, self.dt)

        # Physics step
        for _ in range(PHYSICS_STEPS):
            self.space.step(self.dt / PHYSICS_STEPS)

        self.player.update(self.dt, self.game_time)
        self.world.update(self.dt, self.game_time, self.player)
        self.particles.update(self.dt)

        # Camera follow
        self.camera.follow(self.player.get_center(), self.dt)
        self.camera.set_zoom_for_scale(self.player.scale)

        # Cell pickups
        picked = self.world.check_cell_pickup(self.player.get_center(), 50)
        for ctype in picked:
            if ctype not in self.player.strain_data.get("unlocked_cells", []):
                self.player.strain_data.setdefault("unlocked_cells", []).append(ctype)
                self.hud.notify(f"Unlocked: {ctype.upper()}!", NEON_CYAN)
            self.particles.emit_xp(self.player.get_center())
        
        # Check mini-boss domain entry
        miniboss_domain = self.world.check_miniboss_entry(self.player.get_center())
        if miniboss_domain and not hasattr(self, '_current_miniboss_domain'):
            self._current_miniboss_domain = miniboss_domain
            self._spawn_miniboss(miniboss_domain)
        
        # Check if mini-boss defeated
        if hasattr(self, '_current_miniboss_domain') and hasattr(self, '_miniboss_active'):
            if self._miniboss_active and not any(e.is_miniboss for e in self.world.enemies if hasattr(e, 'is_miniboss')):
                # Mini-boss defeated!
                domain = self._current_miniboss_domain
                domain["defeated"] = True
                reward_msg = self.world.apply_miniboss_reward(
                    self.player, 
                    domain["reward_type"], 
                    domain["reward_desc"]
                )
                self.hud.notify(reward_msg, (255, 220, 0), duration=5.0)
                self.hud.notify(f"{domain['name']} DEFEATED!", (255, 100, 255), duration=4.0)
                self.particles.emit_levelup(self.player.get_center())
                self.camera.shake(15.0)
                self._miniboss_active = False
                del self._current_miniboss_domain

        # Level up check
        if hasattr(self.player, '_levelup_data'):
            data = self.player._levelup_data
            self.hud.levelup(
                data["old_level"], data["new_level"],
                data["old_genome"], data["new_genome"],
                data["old_biomass"], data["new_biomass"]
            )
            self.particles.emit_levelup(self.player.get_center())
            del self.player._levelup_data

        # Cell loss particles
        if hasattr(self.player, '_cells_lost_this_frame'):
            for cell in self.player._cells_lost_this_frame:
                self.particles.emit_cell_death(cell.world_pos, cell.data["glow"])
                self.camera.shake(8.0)
            del self.player._cells_lost_this_frame

        # Death check
        if not self.player.alive:
            self._save_current()
            self.state = STATE_GAME_OVER

        # Achievement checks
        self._check_achievements()

        # Auto-save every 30s
        if int(self.game_time) % 30 == 0 and self.dt > 0:
            self._save_current()

    def _check_achievements(self):
        if not self.player:
            return
        stats = self.player.stats
        unlocked = self.global_achievements

        checks = {
            "first_contact":  stats.get("enemies_killed", 0) >= 1,
            "critical_mass":  len(self.player.cells) >= 10,
            "titan_rising":   self.player.scale >= 5.0,
            "synergist":      stats.get("synergies_triggered", 0) >= 1,
            "fission_reactor":stats.get("skrix_shed", 0) >= 50,
            "void_walker":    stats.get("nullborn_phases", 0) >= 100,
            "architect":      sum(1 for s in load_all_slots() if s) >= 5,
        }
        for aid, condition in checks.items():
            if condition and aid not in unlocked:
                unlocked[aid] = True
                from data.achievements_data import ACHIEVEMENTS
                self.hud.notify(f"Achievement: {ACHIEVEMENTS[aid]['name']}!", GOLD)

    def _draw(self):
        if self.state == STATE_MAIN_MENU:
            self.main_menu.draw(self.screen, self.game_time)

        elif self.state == STATE_STRAIN_SELECT:
            self.strain_menu.draw(self.screen, self.game_time)

        elif self.state == STATE_RACE_SELECT:
            self.race_menu.draw(self.screen, self.game_time)

        elif self.state == STATE_EDITOR:
            self.editor.draw(self.screen, self.game_time)

        elif self.state == STATE_XENOPEDIA:
            self.xenopedia.draw(self.screen, self.game_time)

        elif self.state == STATE_ACHIEVEMENTS:
            self.achievements_screen.draw(self.screen, self.game_time,
                                          self.global_achievements)

        elif self.state == STATE_GAME:
            self._draw_game()

        elif self.state == STATE_PAUSED:
            self._draw_game()
            self._draw_pause_overlay()

        elif self.state == STATE_GAME_OVER:
            self._draw_game_over()

    def _draw_game(self):
        if not self.world or not self.player:
            return
        self.world.draw_background(self.screen, self.camera, self.game_time)
        self.world.draw_entities(self.screen, self.camera, self.game_time)
        self.player.draw(self.screen, self.camera, self.game_time)
        self.particles.draw(self.screen, self.camera)
        self.world.draw_weather(self.screen, self.camera, self.game_time, self.sw, self.sh)
        if self.hud:
            self.hud.draw(self.screen, self.player, self.game_time)
        weather_font = pygame.font.SysFont("consolas", 18, bold=True)
        self.world.draw_weather_hud(self.screen, weather_font, self.sw, self.sh, self.game_time)
        self._draw_minimap()
        
        # Boss proximity warning
        self._draw_boss_proximity_warning()
        
        # Full map overlay
        if self.map_open:
            self._draw_full_map()
        
        if self.tutorial and self.tutorial.active:
            self.tutorial.draw(self.screen, self.game_time)

    def _draw_minimap(self):
        from core.world import WORLD_SIZE
        mm_size = 140
        mm_x, mm_y = self.sw - mm_size - 16, 16
        mm_surf = pygame.Surface((mm_size, mm_size), pygame.SRCALPHA)
        mm_surf.fill((8, 4, 20, 200))
        pygame.draw.rect(mm_surf, NEON_CYAN, (0, 0, mm_size, mm_size), width=1)
        
        # POI markers
        if self.world:
            for poi in self.world.poi_markers:
                px, py = poi["pos"]
                mx = int((px / WORLD_SIZE) * mm_size)
                my = int((py / WORLD_SIZE) * mm_size)
                r = max(2, int((poi["radius"] / WORLD_SIZE) * mm_size))
                pygame.draw.circle(mm_surf, (*poi["color"], 100), (mx, my), r)
                pygame.draw.circle(mm_surf, poi["color"], (mx, my), r, width=1)
        
        # Player dot
        if self.player:
            px, py = self.player.get_center()
            mx = int((px / WORLD_SIZE) * mm_size)
            my = int((py / WORLD_SIZE) * mm_size)
            pygame.draw.circle(mm_surf, NEON_CYAN, (mx, my), 4)
            pygame.draw.circle(mm_surf, WHITE, (mx, my), 4, width=1)
        
        # Enemy dots
        if self.world:
            for e in self.world.enemies:
                ex, ey = e.get_center()
                emx = int((ex / WORLD_SIZE) * mm_size)
                emy = int((ey / WORLD_SIZE) * mm_size)
                pygame.draw.circle(mm_surf, NEON_ORANGE, (emx, emy), 2)
        
        self.screen.blit(mm_surf, (mm_x, mm_y))

    def _draw_pause_overlay(self):
        overlay = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))
        cx = self.sw // 2
        title = self.pause_font.render("PAUSED", True, NEON_CYAN)
        self.screen.blit(title, (cx - title.get_width()//2, self.sh//2 - 60))
        from ui.menus import Button
        btns = [
            Button((cx-80, self.sh//2+20,  160, 44), "RESUME",  NEON_GREEN),
            Button((cx-80, self.sh//2+80,  160, 44), "SAVE & EXIT", NEON_ORANGE),
            Button((cx-80, self.sh//2+140, 160, 44), "EDITOR",  NEON_CYAN),
        ]
        for btn in btns:
            btn.draw(self.screen, self.game_time)

    def _draw_game_over(self):
        self.screen.fill(DEEP_VOID)
        from core.utils import draw_glow_circle
        draw_glow_circle(self.screen, (255, 0, 40), (self.sw//2, self.sh//2), 200, alpha=30, layers=4)
        font = pygame.font.SysFont("consolas", 52, bold=True)
        sub  = pygame.font.SysFont("consolas", 20)
        title = font.render("GENOME COLLAPSED", True, (255, 40, 60))
        hint  = sub.render("Press any key to return to strain select", True, (180, 100, 120))
        self.screen.blit(title, (self.sw//2 - title.get_width()//2, self.sh//2 - 60))
        self.screen.blit(hint,  (self.sw//2 - hint.get_width()//2,  self.sh//2 + 20))
    
    def _draw_boss_proximity_warning(self):
        """Draw ominous warnings when near the boss arena."""
        if not self.world or not self.player:
            return
        
        # Find boss arena position
        boss_poi = None
        for poi in self.world.poi_markers:
            if poi["type"] == "boss_arena":
                boss_poi = poi
                break
        
        if not boss_poi:
            return
        
        boss_pos = boss_poi["pos"]
        player_pos = self.player.get_center()
        
        dx = boss_pos[0] - player_pos[0]
        dy = boss_pos[1] - player_pos[1]
        dist = math.hypot(dx, dy)
        
        # Different warnings at different distances
        if dist < 800:
            # Very close - intense warning
            from core.utils import pulse_value, draw_glow_circle
            pulse = pulse_value(self.game_time, speed=3.0, lo=0.5, hi=1.0)
            
            # Screen vignette
            vignette = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
            alpha = int(80 * pulse * (1 - dist/800))
            pygame.draw.circle(vignette, (80, 0, 20, alpha), (self.sw//2, self.sh//2), 
                             max(100, self.sw), width=self.sw//2)
            self.screen.blit(vignette, (0, 0))
            
            # Ominous text
            warnings = [
                "Something ancient stirs...",
                "The air grows heavy with dread...",
                "You feel an overwhelming presence...",
                "XENARCH awaits...",
            ]
            intensity = int((800 - dist) / 200)
            if intensity < len(warnings):
                font = pygame.font.SysFont("consolas", 24, bold=True)
                c = tuple(int(v * pulse) for v in (255, 60, 60))
                txt = font.render(warnings[intensity], True, c)
                self.screen.blit(txt, (self.sw//2 - txt.get_width()//2, 80))
                
                # Boss direction indicator
                angle = math.atan2(dy, dx)
                indicator_dist = 150
                ix = self.sw//2 + math.cos(angle) * indicator_dist
                iy = self.sh//2 + math.sin(angle) * indicator_dist
                draw_glow_circle(self.screen, (255, 0, 60), (int(ix), int(iy)), 
                               int(12 * pulse), alpha=int(150 * pulse), layers=3)
        
        elif dist < 1500:
            # Medium distance - subtle warning
            font = pygame.font.SysFont("consolas", 18)
            txt = font.render("You sense a powerful entity nearby...", True, (200, 100, 100))
            self.screen.blit(txt, (self.sw//2 - txt.get_width()//2, 60))
    
    def _draw_full_map(self):
        """Draw full world map overlay (toggled with M key)."""
        from core.world import WORLD_SIZE
        from core.utils import draw_glow_circle, pulse_value
        
        # Semi-transparent overlay
        overlay = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        # Map panel
        map_size = min(self.sw - 100, self.sh - 100, 700)
        map_x = self.sw // 2 - map_size // 2
        map_y = self.sh // 2 - map_size // 2
        
        map_surf = pygame.Surface((map_size, map_size), pygame.SRCALPHA)
        map_surf.fill((15, 10, 30, 240))
        pygame.draw.rect(map_surf, NEON_CYAN, (0, 0, map_size, map_size), width=3, border_radius=8)
        
        # Title
        title = self.map_font.render("WORLD MAP - Press M to close", True, NEON_CYAN)
        map_surf.blit(title, (map_size//2 - title.get_width()//2, 15))
        
        # Draw world boundary
        pygame.draw.rect(map_surf, (100, 100, 120), (40, 50, map_size-80, map_size-100), width=2)
        
        # Player position
        if self.player:
            px, py = self.player.get_center()
            # Convert world coords to map coords
            map_px = int((px / WORLD_SIZE) * (map_size - 80)) + 40
            map_py = int((py / WORLD_SIZE) * (map_size - 100)) + 50
            pygame.draw.circle(map_surf, NEON_CYAN, (map_px, map_py), 6)
            pygame.draw.circle(map_surf, WHITE, (map_px, map_py), 6, width=2)
            
            # Player label
            p_label = self.map_font_small.render("YOU", True, WHITE)
            map_surf.blit(p_label, (map_px - p_label.get_width()//2, map_py - 20))
        
        # POI markers
        if self.world:
            for poi in self.world.poi_markers:
                poi_x = int((poi["pos"][0] / WORLD_SIZE) * (map_size - 80)) + 40
                poi_y = int((poi["pos"][1] / WORLD_SIZE) * (map_size - 100)) + 50
                poi_r = max(4, int((poi["radius"] / WORLD_SIZE) * (map_size - 80)))
                
                # Boss arena gets special treatment
                if poi["type"] == "boss_arena":
                    pulse = pulse_value(self.game_time, speed=2.0, lo=0.6, hi=1.0)
                    boss_radius = int(poi_r * pulse)
                    draw_glow_circle(map_surf, (255, 0, 60), (poi_x, poi_y), 
                                   boss_radius, alpha=int(120 * pulse), layers=4)
                    boss_label = self.map_font.render("XENARCH", True, (255, 60, 60))
                    map_surf.blit(boss_label, (poi_x - boss_label.get_width()//2, poi_y - 8))
                
                # Mini-boss domains get special treatment
                elif poi["type"] == "miniboss_domain":
                    pulse = pulse_value(self.game_time + poi.get("phase", 0), speed=1.5, lo=0.7, hi=1.0)
                    domain_radius = int(poi_r * pulse)
                    draw_glow_circle(map_surf, poi["color"], (poi_x, poi_y), 
                                   domain_radius, alpha=int(100 * pulse), layers=3)
                    # Domain name
                    domain_label = self.map_font_small.render(poi.get("name", "DOMAIN"), True, poi["color"])
                    map_surf.blit(domain_label, (poi_x - domain_label.get_width()//2, poi_y - 6))
                
                else:
                    # Regular POI
                    pygame.draw.circle(map_surf, (*poi["color"], 80), (poi_x, poi_y), poi_r)
                    pygame.draw.circle(map_surf, poi["color"], (poi_x, poi_y), poi_r, width=1)
                    
                    # Add text label for all POI types
                    label_text = poi.get("label", "")
                    if label_text:
                        poi_label = self.map_font_small.render(label_text, True, poi["color"])
                        map_surf.blit(poi_label, (poi_x - poi_label.get_width()//2, poi_y - poi_r - 12))
        
        # Legend
        legend_y = map_size - 100
        legend_items = [
            ("Safe Zone", (0, 255, 180)),
            ("Enemy Nest", (255, 60, 60)),
            ("Cell Cache", (255, 200, 0)),
            ("Mini-Boss Domain", (255, 120, 255)),
        ]
        for i, (name, color) in enumerate(legend_items):
            pygame.draw.circle(map_surf, color, (20, legend_y + i * 18), 5)
            txt = self.map_font_small.render(name, True, color)
            map_surf.blit(txt, (32, legend_y + i * 18 - 6))
        
        # Progression hint
        hint = self.map_font_small.render("Journey across the world to find XENARCH", 
                                         True, (180, 180, 180))
        map_surf.blit(hint, (map_size//2 - hint.get_width()//2, map_size - 25))
        
        self.screen.blit(map_surf, (map_x, map_y))
