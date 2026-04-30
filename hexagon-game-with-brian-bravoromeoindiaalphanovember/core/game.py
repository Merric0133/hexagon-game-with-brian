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

        # Boss / fast-travel state
        self._boss_active         = False
        self._current_boss_domain = None
        self._fast_travel_target  = None
        self._fast_travel_timer   = 0.0
        
        # Mini-boss confirmation dialog
        self._miniboss_confirm_domain = None
        self._miniboss_confirm_timer = 0.0

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
                # Player dash attack deals damage
                if self.player.dash_attack_active:
                    base_dmg = 35
                    # Rage mode damage boost
                    if self.player.rage_mode_active:
                        base_dmg = int(base_dmg * 1.5)
                    enemy.take_damage(base_dmg, cp)
                    self.particles.emit(cp or enemy.get_center(),
                                      (0, 255, 255), count=15, speed=150)
                    self.camera.shake(5.0)
                
                # Spike cells deal damage on collision (passive)
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
                # Enemy deals damage to player (only if not telegraphing and not during player iframes)
                if not enemy.telegraph_active and "dash_iframe" not in self.player.status_effects:
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
                        # Get current movement direction from keys
                        keys = pygame.key.get_pressed()
                        dx, dy = 0, 0
                        if keys[pygame.K_w] or keys[pygame.K_UP]:    dy -= 1
                        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  dy += 1
                        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  dx -= 1
                        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1
                        result = self.player.trigger_keybind_ability('q', direction=(dx, dy))
                        if result == 'dash':
                            self.particles.emit(self.player.get_center(), (0, 255, 255), count=20, speed=200)
                            self.camera.shake(3.0)
                if event.key == pygame.K_e and self.state == STATE_GAME:
                    if self.player:
                        result = self.player.trigger_keybind_ability('e', direction=None)
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
                        result = self.player.trigger_keybind_ability('r', direction=None)
                        if result == 'heal_pulse':
                            self.particles.emit(self.player.get_center(), (0, 255, 100), count=25, speed=120)
                            self.camera.shake(2.0)
                            if self.hud:
                                self.hud.notify("HEAL PULSE!", (0, 255, 100))
                if event.key == pygame.K_f and self.state == STATE_GAME:
                    if self.player:
                        result = self.player.trigger_keybind_ability('f', direction=None)
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
                # Map click — fast travel to captured nests
                if event.type == pygame.MOUSEBUTTONDOWN and self.map_open:
                    self._handle_map_click(event.pos)

            elif self.state == STATE_GAME_OVER:
                if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.KEYDOWN:
                    self.state = STATE_STRAIN_SELECT
                    self.strain_menu.refresh()

            elif self.state == STATE_VICTORY:
                if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.KEYDOWN:
                    self.state = STATE_STRAIN_SELECT
                    self.strain_menu.refresh()
            
            elif self.state == STATE_MINIBOSS_CONFIRM:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        # Confirm - enter mini-boss domain
                        self._current_miniboss_domain = self._miniboss_confirm_domain
                        self._spawn_miniboss(self._miniboss_confirm_domain)
                        self.world.miniboss_active = True
                        self.state = STATE_GAME
                        self._miniboss_confirm_domain = None
                    elif event.key == pygame.K_ESCAPE:
                        # Cancel - go back to game
                        self.state = STATE_GAME
                        self._miniboss_confirm_domain = None
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Check button clicks
                    mx, my = event.pos
                    cx = self.sw // 2
                    # Confirm button
                    if pygame.Rect(cx-100, self.sh//2+40, 200, 44).collidepoint(mx, my):
                        self._current_miniboss_domain = self._miniboss_confirm_domain
                        self._spawn_miniboss(self._miniboss_confirm_domain)
                        self.world.miniboss_active = True
                        self.state = STATE_GAME
                        self._miniboss_confirm_domain = None
                    # Cancel button
                    elif pygame.Rect(cx-100, self.sh//2+100, 200, 44).collidepoint(mx, my):
                        self.state = STATE_GAME
                        self._miniboss_confirm_domain = None

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
        from core.world import WORLD_SIZE
        center = WORLD_SIZE / 2
        self.player = Player(self.space, (center, center), strain_data)
        self.camera.x = center - self.sw / 2
        self.camera.y = center - self.sh / 2
        self.camera.set_zoom_for_scale(self.player.scale)
        self.hud = HUD(self.sw, self.sh)
        self.particles = ParticleSystem()
        self.editor = CellEditor(self.sw, self.sh, strain_data)
        # Fast-travel state
        self._fast_travel_target = None
        self._fast_travel_timer = 0.0
        # Boss tracking
        self._current_boss_domain = None
        self._boss_active = False
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
        layout_serialized = {"{},{}".format(k[0], k[1]): v for k, v in new_layout.items()}
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
            # Fire projectiles in all directions
            self.particles.emit_explosion((cx,cy), (255,100,0))
            self.camera.shake(12.0)
            # Spawn projectiles
            import math
            for i in range(8):
                angle = (i / 8) * math.pi * 2
                vel_x = math.cos(angle) * 300
                vel_y = math.sin(angle) * 300
                self.particles.emit_projectile((cx, cy), (vel_x, vel_y), 
                                              (255, 100, 0), damage=40, lifetime=2.0, 
                                              radius=8, glow_color=(255, 150, 0))
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
        miniboss = Enemy(self.space, boss_pos, "hunter", level=self.player.level + 2,
                        biome_modifier=None)
        # Make it cracked — boost stats (but weaker than real mini-bosses)
        miniboss.scale = 1.6
        for cell in miniboss.cells:
            cell.hp = int(cell.hp * 2.0)
            cell.max_hp = int(cell.max_hp * 2.0)
        miniboss.xp_value = int(miniboss.xp_value * 3)
        miniboss.telegraph_duration = 0.7  # Slower for tutorial
        miniboss.telegraph_color = (255, 150, 0)  # Orange for tutorial boss
        self.world.enemies.append(miniboss)
        if self.hud:
            self.hud.notify("MINI BOSS SPAWNED! Watch for red warnings!", (255, 60, 60))
    
    def _spawn_miniboss(self, domain):
        """Spawn a unique mini-boss for a domain."""
        if not self.world or not self.player:
            return
        from entities.enemy import Enemy
        
        boss_pos = domain["pos"]
        boss_type = domain.get("boss_type", "hunter")
        
        # Create EXTREMELY powerful mini-boss
        miniboss = Enemy(self.space, boss_pos, boss_type, 
                        level=self.player.level + 10,  # MASSIVE level boost
                        biome_modifier=None)
        
        # Make it ABSOLUTELY BRUTAL
        miniboss.scale = 3.2  # HUGE scale
        for cell in miniboss.cells:
            cell.hp = int(cell.hp * 9.0)  # MASSIVE HP multiplier
            cell.max_hp = int(cell.max_hp * 9.0)
        miniboss.xp_value = int(miniboss.xp_value * 10)  # HUGE XP reward
        miniboss.is_miniboss = True  # Flag for tracking
        # Faster telegraphs for mini-bosses
        miniboss.telegraph_duration = 0.4  # Even faster
        miniboss.telegraph_color = (255, 0, 0)  # Bright red for danger
        
        self.world.enemies.append(miniboss)
        self._miniboss_active = True
        
        if self.hud:
            self.hud.notify(domain['name'] + " AWAKENS!", domain["color"], duration=4.0)
            self.hud.notify("Reward: " + domain['reward_desc'], (255, 220, 0), duration=5.0)
            self.hud.notify("⚠️ EXTREME THREAT ⚠️", (255, 0, 0), duration=3.0)
        
        self.camera.shake(20.0)
        self.particles.emit(boss_pos, domain["color"], count=80, speed=400)

    def _spawn_quadrant_boss(self, domain):
        """Spawn the powerful boss for a quadrant biome."""
        if not self.world or not self.player:
            return
        from entities.enemy import Enemy
        from data.biomes_data import BIOMES

        boss_pos = domain["pos"]
        biome_key = domain.get("biome", "membrane")
        biome_data = BIOMES.get(biome_key, BIOMES["membrane"])
        # Pick the toughest enemy type from the biome
        enemy_types = biome_data["enemy_types"]
        boss_type = enemy_types[-1] if enemy_types else "armored_brute"

        # Create INSANELY powerful world boss (much stronger than mini-boss)
        boss = Enemy(self.space, boss_pos, boss_type,
                     level=self.player.level + 18,  # MASSIVE level (vs mini-boss +10)
                     biome_modifier=biome_data.get("modifier"))
        boss.scale = 4.5  # ENORMOUS (vs mini-boss 3.2)
        for cell in boss.cells:
            cell.hp = int(cell.hp * 15.0)  # INSANE HP (vs mini-boss 9.0)
            cell.max_hp = int(cell.max_hp * 15.0)
        boss.xp_value = int(boss.xp_value * 25)  # MASSIVE XP (vs mini-boss 10)
        boss.is_boss = True
        
        # World boss is AGGRESSIVE
        boss.telegraph_duration = 0.35  # Even faster attacks
        boss.telegraph_color = (255, 0, 0)  # Bright red
        boss.attack_cooldown = 0.5  # Attacks frequently
        
        # Store boss type for reward
        boss.boss_type = boss_type
        boss.biome_key = biome_key

        self.world.enemies.append(boss)
        self._boss_active = True
        self.world.miniboss_active = True  # Suppress ambient visuals

        if self.hud:
            self.hud.notify(domain["label"] + " AWAKENS!", domain["color"], duration=5.0)
            self.hud.notify("⚠️ WORLD BOSS ⚠️", (255, 0, 0), duration=4.0)
            self.hud.notify("Defeat it to activate a PILLAR!", (255, 255, 100), duration=5.0)
        self.camera.shake(30.0)
        self.particles.emit(boss_pos, domain["color"], count=120, speed=500)

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
        self.particles.update_projectiles(self.dt)

        # Camera follow
        self.camera.follow(self.player.get_center(), self.dt)
        self.camera.set_zoom_for_scale(self.player.scale)

        # Fast travel countdown
        if self._fast_travel_target is not None:
            self._fast_travel_timer -= self.dt
            if self._fast_travel_timer <= 0:
                tx, ty = self._fast_travel_target
                self.player.body.position = (tx, ty)
                self.player.body.velocity = (0, 0)
                self.camera.x = tx - self.sw / 2
                self.camera.y = ty - self.sh / 2
                self.particles.emit((tx, ty), (0, 255, 180), count=40, speed=200)
                self.hud.notify("ARRIVED AT NEST", (0, 255, 180))
                self._fast_travel_target = None
                self.map_open = False

        # Cell pickups
        picked = self.world.check_cell_pickup(self.player.get_center(), 50)
        for ctype in picked:
            if ctype not in self.player.strain_data.get("unlocked_cells", []):
                self.player.strain_data.setdefault("unlocked_cells", []).append(ctype)
                self.hud.notify("Unlocked: " + ctype.upper() + "!", NEON_CYAN)
            self.particles.emit_xp(self.player.get_center())
        
        # Projectile collision detection
        from core.utils import distance
        for proj in self.particles.projectiles:
            if proj["hit"]:
                continue
            for enemy in (self.world.enemies if self.world else []):
                if distance(proj["pos"], enemy.get_center()) < 30:
                    # Hit!
                    enemy.take_damage(proj["damage"], proj["pos"])
                    self.particles.emit(proj["pos"], proj["color"], count=12, speed=150)
                    self.camera.shake(3.0)
                    proj["hit"] = True
                    break

        # Check mini-boss domain entry
        miniboss_domain = self.world.check_miniboss_entry(self.player.get_center())
        if miniboss_domain and not hasattr(self, '_current_miniboss_domain'):
            # Show confirmation dialog instead of spawning immediately
            self._miniboss_confirm_domain = miniboss_domain
            self.state = STATE_MINIBOSS_CONFIRM
            self._miniboss_confirm_timer = 0.0

        # Check if mini-boss defeated
        if hasattr(self, '_current_miniboss_domain') and hasattr(self, '_miniboss_active'):
            if self._miniboss_active and not any(getattr(e, 'is_miniboss', False) for e in self.world.enemies):
                domain = self._current_miniboss_domain
                domain["defeated"] = True
                reward_msg = self.world.apply_miniboss_reward(
                    self.player,
                    domain["reward_type"],
                    domain["reward_desc"]
                )
                self.hud.notify(reward_msg, (255, 220, 0), duration=5.0)
                self.hud.notify(domain['name'] + " DEFEATED!", (255, 100, 255), duration=4.0)
                # Capture nearest nest in this quadrant
                if domain.get("captures_nest"):
                    qi = domain.get("quadrant_index", 0)
                    captured = self.world.capture_nearest_nest_to(domain["pos"], qi)
                    if captured:
                        self.hud.notify("NEST CAPTURED — fast travel unlocked!", (0, 255, 180), duration=4.0)
                self.particles.emit_levelup(self.player.get_center())
                self.camera.shake(15.0)
                self._miniboss_active = False
                self.world.miniboss_active = False
                del self._current_miniboss_domain

        # Check boss arena entry
        boss_domain = self.world.check_boss_arena_entry(self.player.get_center())
        if boss_domain and not self._boss_active and not hasattr(self, '_current_boss_domain'):
            # Check if all mini-bosses defeated
            miniboss_count = sum(1 for poi in self.world.poi_markers 
                                if poi["type"] == "miniboss_domain" and poi.get("defeated", False))
            if miniboss_count >= 4:
                # All mini-bosses defeated, can fight world boss
                self._current_boss_domain = boss_domain
                self._spawn_quadrant_boss(boss_domain)
            else:
                # Not ready yet
                if self.hud:
                    self.hud.notify(f"Defeat all mini-bosses first! ({miniboss_count}/4)", (255, 100, 100), duration=3.0)

        # Check if quadrant boss defeated
        if self._boss_active and not any(getattr(e, 'is_boss', False) for e in self.world.enemies):
            domain = self._current_boss_domain
            domain["defeated"] = True
            qi = domain.get("quadrant_index", 0)
            self.world.activate_pillar(qi)
            
            # Grant unique boss cell reward
            self._grant_boss_reward()
            
            self.hud.notify(domain["label"] + " DEFEATED!", domain["color"], duration=5.0)
            self.hud.notify("A PILLAR AWAKENS AT THE SHRINE!", (255, 255, 100), duration=5.0)
            self.particles.emit_levelup(self.player.get_center())
            self.camera.shake(20.0)
            self._boss_active = False
            self.world.miniboss_active = False
            del self._current_boss_domain
            # Check victory
            if self.world.all_pillars_activated():
                self.state = STATE_VICTORY

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

        elif self.state == STATE_VICTORY:
            self._draw_victory()
        
        elif self.state == STATE_MINIBOSS_CONFIRM:
            self._draw_game()
            self._draw_miniboss_confirm()

    def _draw_game(self):
        if not self.world or not self.player:
            return
        self.world.draw_background(self.screen, self.camera, self.game_time)
        self.world.draw_entities(self.screen, self.camera, self.game_time)
        self.player.draw(self.screen, self.camera, self.game_time)
        self.particles.draw(self.screen, self.camera)
        self.particles.draw_projectiles(self.screen, self.camera)
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

        def to_mm(wx, wy):
            return int((wx / WORLD_SIZE) * mm_size), int((wy / WORLD_SIZE) * mm_size)

        # POI markers
        if self.world:
            for poi in self.world.poi_markers:
                mx, my = to_mm(*poi["pos"])
                r = max(1, int((poi["radius"] / WORLD_SIZE) * mm_size))
                if poi["type"] == "pillar":
                    color = poi["color"] if poi.get("activated") else (60, 60, 60)
                    pygame.draw.circle(mm_surf, color, (mx, my), max(2, r))
                elif poi["type"] == "boss_arena":
                    color = (80, 80, 80) if poi.get("defeated") else poi["color"]
                    pygame.draw.circle(mm_surf, (*color, 120), (mx, my), max(2, r))
                    pygame.draw.circle(mm_surf, color, (mx, my), max(2, r), width=1)
                elif poi["type"] == "nest":
                    color = (0, 255, 180) if poi.get("captured") else (*poi["color"], 80)
                    if isinstance(color, tuple) and len(color) == 4:
                        pygame.draw.circle(mm_surf, color, (mx, my), max(1, r))
                    else:
                        pygame.draw.circle(mm_surf, (*color, 80), (mx, my), max(1, r))
                elif poi["type"] == "miniboss_domain":
                    if not poi.get("defeated"):
                        pygame.draw.circle(mm_surf, (*poi["color"], 60), (mx, my), max(1, r))

        # Player dot
        if self.player:
            px, py = to_mm(*self.player.get_center())
            pygame.draw.circle(mm_surf, NEON_CYAN, (px, py), 3)
            pygame.draw.circle(mm_surf, WHITE, (px, py), 3, width=1)

        # Enemy dots
        if self.world:
            for e in self.world.enemies:
                ex, ey = to_mm(*e.get_center())
                pygame.draw.circle(mm_surf, NEON_ORANGE, (ex, ey), 1)

        # Pillar progress indicator
        if self.world:
            activated = len(self.world.pillars_activated)
            font_mm = pygame.font.SysFont("consolas", 9)
            t = font_mm.render("PILLARS: " + str(activated) + "/4", True, (255, 220, 60))
            mm_surf.blit(t, (2, mm_size - 12))

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

    def _draw_victory(self):
        self.screen.fill((2, 2, 15))
        from core.utils import draw_glow_circle, pulse_value
        pulse = pulse_value(self.game_time, speed=1.2, lo=0.5, hi=1.0)
        draw_glow_circle(self.screen, (255, 220, 60), (self.sw//2, self.sh//2),
                         int(260 * pulse), alpha=int(60 * pulse), layers=5)
        font_big  = pygame.font.SysFont("consolas", 52, bold=True)
        font_mid  = pygame.font.SysFont("consolas", 24, bold=True)
        font_small = pygame.font.SysFont("consolas", 18)
        c = tuple(int(v * pulse) for v in (255, 220, 60))
        title = font_big.render("XENOVA CONQUERED", True, c)
        sub   = font_mid.render("All four pillars have been awakened.", True, (200, 200, 255))
        hint  = font_small.render("Press any key to return to strain select", True, (160, 160, 200))
        self.screen.blit(title, (self.sw//2 - title.get_width()//2, self.sh//2 - 80))
        self.screen.blit(sub,   (self.sw//2 - sub.get_width()//2,   self.sh//2 + 10))
        self.screen.blit(hint,  (self.sw//2 - hint.get_width()//2,  self.sh//2 + 60))
    
    def _draw_boss_proximity_warning(self):
        """Draw ominous warnings when near any undefeated boss arena."""
        if not self.world or not self.player:
            return

        player_pos = self.player.get_center()
        closest_boss = None
        closest_dist = float("inf")

        for poi in self.world.poi_markers:
            if poi["type"] == "boss_arena" and not poi.get("defeated", False):
                dx = poi["pos"][0] - player_pos[0]
                dy = poi["pos"][1] - player_pos[1]
                d = math.hypot(dx, dy)
                if d < closest_dist:
                    closest_dist = d
                    closest_boss = poi

        if not closest_boss:
            return

        boss_pos = closest_boss["pos"]
        dx = boss_pos[0] - player_pos[0]
        dy = boss_pos[1] - player_pos[1]

        if closest_dist < 1200:
            from core.utils import pulse_value, draw_glow_circle
            pulse = pulse_value(self.game_time, speed=3.0, lo=0.5, hi=1.0)
            vignette = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
            alpha = int(70 * pulse * (1 - closest_dist / 1200))
            pygame.draw.circle(vignette, (80, 0, 20, alpha), (self.sw//2, self.sh//2),
                               max(100, self.sw), width=self.sw//2)
            self.screen.blit(vignette, (0, 0))

            font = pygame.font.SysFont("consolas", 22, bold=True)
            c = tuple(int(v * pulse) for v in closest_boss["color"])
            txt = font.render(closest_boss["label"] + " is near...", True, c)
            self.screen.blit(txt, (self.sw//2 - txt.get_width()//2, 80))

            angle = math.atan2(dy, dx)
            ix = self.sw//2 + math.cos(angle) * 140
            iy = self.sh//2 + math.sin(angle) * 140
            draw_glow_circle(self.screen, closest_boss["color"], (int(ix), int(iy)),
                             int(10 * pulse), alpha=int(140 * pulse), layers=3)

        elif closest_dist < 2500:
            font = pygame.font.SysFont("consolas", 16)
            txt = font.render("A powerful entity lurks in this quadrant...", True, (180, 100, 100))
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
        title = self.map_font.render("WORLD MAP  [M] close  [click captured nest to fast travel]", True, NEON_CYAN)
        map_surf.blit(title, (map_size//2 - title.get_width()//2, 10))

        # Draw world boundary
        inner_x, inner_y = 40, 40
        inner_w, inner_h = map_size - 80, map_size - 80
        pygame.draw.rect(map_surf, (100, 100, 120), (inner_x, inner_y, inner_w, inner_h), width=2)

        def world_to_map(wx, wy):
            mx = int((wx / WORLD_SIZE) * inner_w) + inner_x
            my = int((wy / WORLD_SIZE) * inner_h) + inner_y
            return mx, my

        # Draw quadrant dividers (faint lines through center)
        mcx, mcy = world_to_map(WORLD_SIZE / 2, WORLD_SIZE / 2)
        pygame.draw.line(map_surf, (60, 60, 80), (mcx, inner_y), (mcx, inner_y + inner_h), 1)
        pygame.draw.line(map_surf, (60, 60, 80), (inner_x, mcy), (inner_x + inner_w, mcy), 1)

        # Store clickable nest rects for interaction (in screen space)
        self._map_nest_rects = []

        if self.world:
            for poi in self.world.poi_markers:
                poi_x, poi_y = world_to_map(*poi["pos"])
                poi_r = max(3, int((poi["radius"] / WORLD_SIZE) * inner_w))

                if poi["type"] == "pillar":
                    activated = poi.get("activated", False)
                    color = poi["color"] if activated else (80, 80, 80)
                    pulse = pulse_value(self.game_time + poi.get("phase", 0), speed=2.0, lo=0.6, hi=1.0)
                    pr = int(6 * (pulse if activated else 0.5))
                    draw_glow_circle(map_surf, color, (poi_x, poi_y), pr,
                                     alpha=int(150 * pulse) if activated else 40, layers=2)
                    pygame.draw.circle(map_surf, color, (poi_x, poi_y), max(3, pr), width=0 if activated else 1)

                elif poi["type"] == "boss_arena":
                    defeated = poi.get("defeated", False)
                    color = (100, 100, 100) if defeated else poi["color"]
                    pulse = pulse_value(self.game_time + poi.get("phase", 0), speed=2.0, lo=0.6, hi=1.0)
                    draw_glow_circle(map_surf, color, (poi_x, poi_y),
                                     int(poi_r * (pulse if not defeated else 0.5)),
                                     alpha=int(120 * pulse) if not defeated else 30, layers=3)
                    lbl = self.map_font_small.render(poi.get("label", "BOSS"), True, color)
                    map_surf.blit(lbl, (poi_x - lbl.get_width()//2, poi_y - 8))

                elif poi["type"] == "miniboss_domain":
                    defeated = poi.get("defeated", False)
                    color = (80, 80, 80) if defeated else poi["color"]
                    pygame.draw.circle(map_surf, (*color, 80 if not defeated else 30), (poi_x, poi_y), poi_r)
                    pygame.draw.circle(map_surf, color, (poi_x, poi_y), poi_r, width=1)

                elif poi["type"] == "nest":
                    captured = poi.get("captured", False)
                    color = (0, 255, 180) if captured else poi["color"]
                    pygame.draw.circle(map_surf, (*color, 100), (poi_x, poi_y), poi_r)
                    pygame.draw.circle(map_surf, color, (poi_x, poi_y), poi_r, width=1)
                    if captured:
                        # Draw travel icon (star)
                        draw_glow_circle(map_surf, (0, 255, 180), (poi_x, poi_y), poi_r + 2, alpha=60, layers=1)
                        # Store screen-space rect for click detection
                        screen_rx = map_x + poi_x - poi_r - 4
                        screen_ry = map_y + poi_y - poi_r - 4
                        self._map_nest_rects.append({
                            "rect": pygame.Rect(screen_rx, screen_ry, (poi_r + 4) * 2, (poi_r + 4) * 2),
                            "pos": poi["pos"],
                            "label": poi.get("label", "NEST"),
                        })

                elif poi["type"] == "safe_zone":
                    pygame.draw.circle(map_surf, (*poi["color"], 60), (poi_x, poi_y), poi_r)
                    pygame.draw.circle(map_surf, poi["color"], (poi_x, poi_y), poi_r, width=1)

                elif poi["type"] == "cache":
                    pygame.draw.circle(map_surf, (*poi["color"], 80), (poi_x, poi_y), max(3, poi_r // 2))

        # Player dot
        if self.player:
            px, py = world_to_map(*self.player.get_center())
            pygame.draw.circle(map_surf, NEON_CYAN, (px, py), 5)
            pygame.draw.circle(map_surf, WHITE, (px, py), 5, width=1)
            p_label = self.map_font_small.render("YOU", True, WHITE)
            map_surf.blit(p_label, (px - p_label.get_width()//2, py - 16))

        # Pillar progress bar
        if self.world:
            activated = len(self.world.pillars_activated)
            bar_y_pos = map_size - 36
            bar_w = map_size - 80
            pygame.draw.rect(map_surf, (40, 40, 60), (40, bar_y_pos, bar_w, 14), border_radius=4)
            fill = int(bar_w * activated / 4)
            if fill > 0:
                pygame.draw.rect(map_surf, (255, 220, 60), (40, bar_y_pos, fill, 14), border_radius=4)
            pygame.draw.rect(map_surf, (200, 200, 100), (40, bar_y_pos, bar_w, 14), width=1, border_radius=4)
            prog_txt = self.map_font_small.render(
                "PILLARS: " + str(activated) + "/4  — defeat each quadrant boss to activate", True, (220, 220, 100))
            map_surf.blit(prog_txt, (40, bar_y_pos - 16))

        # Legend
        legend_items = [
            ("Pillar (active)", (255, 220, 60)),
            ("Boss Arena",      (255, 60,  60)),
            ("Mini-Boss",       (200, 100, 255)),
            ("Nest",            (255, 60,  60)),
            ("Captured Nest",   (0,   255, 180)),
            ("Cache",           (255, 200, 0)),
        ]
        lx = map_size - 160
        for i, (name, color) in enumerate(legend_items):
            pygame.draw.circle(map_surf, color, (lx, 55 + i * 18), 4)
            t = self.map_font_small.render(name, True, color)
            map_surf.blit(t, (lx + 10, 55 + i * 18 - 6))

        self.screen.blit(map_surf, (map_x, map_y))

    def _handle_map_click(self, screen_pos):
        """Handle a click on the full map — fast travel to captured nests."""
        if not hasattr(self, '_map_nest_rects'):
            return
        for entry in self._map_nest_rects:
            if entry["rect"].collidepoint(screen_pos):
                tx, ty = entry["pos"]
                self._fast_travel_target = (tx, ty)
                self._fast_travel_timer = 1.5  # 1.5s channel time
                self.hud.notify("Fast travelling to " + entry["label"] + "...", (0, 255, 180))
                return

    def _draw_miniboss_confirm(self):
        """Draw mini-boss confirmation dialog."""
        if not self._miniboss_confirm_domain:
            return
        
        domain = self._miniboss_confirm_domain
        
        # Semi-transparent overlay
        overlay = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        
        # Dialog panel
        cx = self.sw // 2
        cy = self.sh // 2
        panel_w, panel_h = 400, 280
        panel_x = cx - panel_w // 2
        panel_y = cy - panel_h // 2
        
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((15, 10, 30, 240))
        pygame.draw.rect(panel, domain["color"], (0, 0, panel_w, panel_h), width=3, border_radius=8)
        self.screen.blit(panel, (panel_x, panel_y))
        
        # Title
        title_font = pygame.font.SysFont("consolas", 28, bold=True)
        title = title_font.render(domain['name'], True, domain["color"])
        self.screen.blit(title, (cx - title.get_width()//2, panel_y + 20))
        
        # Description
        desc_font = pygame.font.SysFont("consolas", 14)
        desc_lines = [
            "A powerful entity awaits.",
            "",
            "Reward: " + domain['reward_desc'],
            "",
            "Are you ready to challenge it?"
        ]
        y_offset = panel_y + 70
        for line in desc_lines:
            if line:
                desc = desc_font.render(line, True, (200, 200, 200))
                self.screen.blit(desc, (cx - desc.get_width()//2, y_offset))
            y_offset += 24
        
        # Buttons
        from ui.menus import Button
        confirm_btn = Button((cx - 100, panel_y + panel_h - 80, 200, 44), "ENTER [ENTER]", NEON_GREEN)
        cancel_btn = Button((cx - 100, panel_y + panel_h - 30, 200, 44), "RETREAT [ESC]", NEON_ORANGE)
        
        confirm_btn.draw(self.screen, self.game_time)
        cancel_btn.draw(self.screen, self.game_time)

    def _grant_boss_reward(self):
        """Grant unique cell reward based on boss type."""
        if not self.player:
            return
        
        # Find the defeated boss to get its type
        boss_type = None
        biome_key = None
        for enemy in self.world.enemies:
            if getattr(enemy, 'is_boss', False):
                boss_type = getattr(enemy, 'boss_type', 'armored_brute')
                biome_key = getattr(enemy, 'biome_key', 'membrane')
                break
        
        # Map boss types to unique reward cells
        boss_rewards = {
            "hunter": "zapper",           # Hunter → Zapper cell
            "armored_brute": "shield",    # Brute → Shield cell
            "hive_cluster": "basic",      # Hive → Basic cell
            "psychic_weaver": "zapper",   # Weaver → Zapper cell
            "mimic": "symbiont",          # Mimic → Symbiont cell
            "drifter": "speedy",          # Drifter → Speedy cell
        }
        
        reward_cell = boss_rewards.get(boss_type, "basic")
        
        # Add to unlocked cells
        if reward_cell not in self.player.strain_data.get("unlocked_cells", []):
            self.player.strain_data.setdefault("unlocked_cells", []).append(reward_cell)
            cell_name = reward_cell.upper()
            self.hud.notify(f"⭐ BOSS REWARD: {cell_name} CELL UNLOCKED! ⭐", (255, 220, 0), duration=5.0)
            self.particles.emit(self.player.get_center(), (255, 220, 0), count=50, speed=300)
        else:
            # Already unlocked, give bonus XP instead
            bonus_xp = 500
            self.player.gain_xp(bonus_xp)
            self.hud.notify(f"⭐ BOSS REWARD: +{bonus_xp} BONUS XP! ⭐", (255, 220, 0), duration=5.0)
