import pygame
import math
from core.utils import draw_glow_rect, draw_glow_circle, pulse_value, lerp_color
from core.constants import *

class HUD:
    def __init__(self, screen_w, screen_h):
        self.sw = screen_w
        self.sh = screen_h
        self.font_large = pygame.font.SysFont("consolas", 22, bold=True)
        self.font_med   = pygame.font.SysFont("consolas", 16)
        self.font_small = pygame.font.SysFont("consolas", 12)
        self.notifications = []  # {"text": str, "timer": float, "color": tuple}
        self.levelup_flash = 0.0
        self.levelup_display = None  # {"timer": float, "old_level": int, "new_level": int, "stats": dict}

    def notify(self, text, color=(0, 255, 180), duration=3.0):
        self.notifications.append({"text": text, "timer": duration,
                                   "max_timer": duration, "color": color})

    def levelup(self, old_level, new_level, old_genome, new_genome, old_biomass, new_biomass):
        self.levelup_flash = 2.0
        self.levelup_display = {
            "timer": 4.0,  # Show for 4 seconds
            "old_level": old_level,
            "new_level": new_level,
            "old_genome": old_genome,
            "new_genome": new_genome,
            "old_biomass": old_biomass,
            "new_biomass": new_biomass,
        }
        self.notify("LEVEL UP!", (255, 220, 0), duration=2.5)

    def update(self, dt):
        for n in self.notifications:
            n["timer"] -= dt
        self.notifications = [n for n in self.notifications if n["timer"] > 0]
        if self.levelup_flash > 0:
            self.levelup_flash -= dt
        if self.levelup_display and self.levelup_display.get("timer", 0) > 0:
            self.levelup_display["timer"] -= dt
        elif self.levelup_display and self.levelup_display.get("timer", 0) <= 0:
            self.levelup_display = None

    def draw(self, surface, player, game_time):
        self._draw_genome_bar(surface, player, game_time)
        self._draw_heart_shield(surface, player, game_time)
        self._draw_xp_bar(surface, player)
        self._draw_synergies(surface, player, game_time)
        self._draw_race_badge(surface, player, game_time)
        self._draw_ability_cooldowns(surface, player, game_time)
        self._draw_notifications(surface, game_time)
        if self.levelup_flash > 0:
            self._draw_levelup_flash(surface, game_time)
        if self.levelup_display:
            self._draw_levelup_indicator(surface, game_time)

    def _draw_genome_bar(self, surface, player, game_time):
        biomass = player.get_total_biomass()
        max_bio = player.get_max_biomass()
        ratio = biomass / max(1, max_bio)

        bar_w, bar_h = 280, 18
        x, y = 20, self.sh - 50

        # Background panel
        panel = pygame.Surface((bar_w + 20, bar_h + 30), pygame.SRCALPHA)
        panel.fill((10, 5, 25, 180))
        surface.blit(panel, (x - 10, y - 8))

        # Label
        label = self.font_small.render("GENOME INTEGRITY", True, NEON_CYAN)
        surface.blit(label, (x, y - 6))

        # Bar bg
        pygame.draw.rect(surface, (30, 10, 40), (x, y + 10, bar_w, bar_h), border_radius=4)

        # Bar fill - color shifts red when low
        if ratio > 0.5:
            bar_color = lerp_color((255, 200, 0), (0, 255, 100), (ratio - 0.5) * 2)
        else:
            bar_color = lerp_color((255, 0, 40), (255, 200, 0), ratio * 2)

        fill_w = int(bar_w * ratio)
        if fill_w > 0:
            pygame.draw.rect(surface, bar_color, (x, y + 10, fill_w, bar_h), border_radius=4)
            draw_glow_rect(surface, bar_color, pygame.Rect(x, y+10, fill_w, bar_h), alpha=40)

        # Crack effect when low
        if ratio < 0.3:
            pulse = pulse_value(game_time, speed=4.0, lo=0.3, hi=1.0)
            pygame.draw.rect(surface, (255, 0, 40, int(pulse*180)),
                             (x, y+10, bar_w, bar_h), width=2, border_radius=4)

        # Text
        txt = self.font_small.render(f"{int(biomass)}/{int(max_bio)}", True, WHITE)
        surface.blit(txt, (x + bar_w + 5, y + 12))
    
    def _draw_heart_shield(self, surface, player, game_time):
        """Draw heart shield bar below genome bar."""
        if not hasattr(player, 'heart_shield'):
            return
        
        shield = player.heart_shield
        max_shield = player.heart_shield_max
        ratio = shield / max(1, max_shield)
        
        bar_w, bar_h = 280, 12
        x, y = 20, self.sh - 80  # Above genome bar
        
        # Label
        label = self.font_small.render("HEART SHIELD", True, (100, 200, 255))
        surface.blit(label, (x, y - 6))
        
        # Bar bg
        pygame.draw.rect(surface, (15, 25, 40), (x, y + 8, bar_w, bar_h), border_radius=3)
        
        # Bar fill - cyan/blue shield color
        shield_color = (0, 180, 255) if ratio > 0.3 else (255, 100, 0)
        fill_w = int(bar_w * ratio)
        if fill_w > 0:
            pygame.draw.rect(surface, shield_color, (x, y + 8, fill_w, bar_h), border_radius=3)
            # Pulse when regenerating
            if player.heart_shield_regen_timer <= 0 and shield < max_shield:
                pulse = pulse_value(game_time, speed=3.0, lo=0.5, hi=1.0)
                draw_glow_rect(surface, shield_color, pygame.Rect(x, y+8, fill_w, bar_h), alpha=int(60*pulse))
        
        # Recharging indicator
        if player.heart_shield_regen_timer > 0:
            recharge_txt = self.font_small.render(f"Recharging in {player.heart_shield_regen_timer:.1f}s", 
                                                  True, (150, 150, 150))
            surface.blit(recharge_txt, (x + bar_w + 5, y + 10))
        else:
            # Text
            txt = self.font_small.render(f"{int(shield)}/{int(max_shield)}", True, WHITE)
            surface.blit(txt, (x + bar_w + 5, y + 10))

    def _draw_xp_bar(self, surface, player):
        from core.constants import XP_PER_LEVEL
        level = player.level
        xp = player.xp
        xp_needed = XP_PER_LEVEL[min(level, len(XP_PER_LEVEL)-1)]
        ratio = xp / max(1, xp_needed)

        bar_w, bar_h = 280, 8
        x, y = 20, self.sh - 22

        pygame.draw.rect(surface, (20, 10, 35), (x, y, bar_w, bar_h), border_radius=3)
        if ratio > 0:
            pygame.draw.rect(surface, NEON_PURPLE, (x, y, int(bar_w * ratio), bar_h), border_radius=3)

        lv_txt = self.font_small.render(f"LV {level}  {xp}/{xp_needed} XP", True, NEON_PURPLE)
        surface.blit(lv_txt, (x + bar_w + 5, y - 2))

    def _draw_synergies(self, surface, player, game_time):
        if not player.active_synergies_display:
            return
        x, y = self.sw - 220, 20
        header = self.font_small.render("ACTIVE SYNERGIES", True, NEON_CYAN)
        surface.blit(header, (x, y))
        for i, syn in enumerate(player.active_synergies_display):
            pulse = pulse_value(game_time + i, speed=1.5, lo=0.7, hi=1.0)
            c = tuple(int(v * pulse) for v in NEON_PURPLE)
            txt = self.font_small.render(f"◆ {syn}", True, c)
            surface.blit(txt, (x, y + 16 + i * 16))

    def _draw_race_badge(self, surface, player, game_time):
        race = player.race_name
        color = player.race_data.get("glow", NEON_CYAN)
        pulse = pulse_value(game_time, speed=1.2, lo=0.8, hi=1.0)
        c = tuple(int(v * pulse) for v in color)
        txt = self.font_med.render(f"[ {race.upper()} ]", True, c)
        surface.blit(txt, (self.sw - txt.get_width() - 20, self.sh - 30))

    def _draw_notifications(self, surface, game_time):
        y = 20  # Move to top of screen
        for n in self.notifications:
            alpha = min(255, int(255 * (n["timer"] / n["max_timer"]) * 2))
            alpha = min(255, alpha)
            txt = self.font_large.render(n["text"], True, n["color"])
            txt.set_alpha(alpha)
            x = self.sw // 2 - txt.get_width() // 2
            surface.blit(txt, (x, y))
            y += 30

    def _draw_levelup_flash(self, surface, game_time):
        alpha = int(min(255, self.levelup_flash * 80))
        flash = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        flash.fill((255, 220, 0, alpha))
        surface.blit(flash, (0, 0))
    
    def _draw_ability_cooldowns(self, surface, player, game_time):
        """Draw ability cooldown indicators for Q, E, R, F keys."""
        abilities = [
            {'key': 'Q', 'name': 'DASH', 'color': (0, 255, 255)},
            {'key': 'E', 'name': 'SHIELD', 'color': (0, 180, 255)},
            {'key': 'R', 'name': 'HEAL', 'color': (0, 255, 100)},
            {'key': 'F', 'name': 'RAGE', 'color': (255, 60, 0)},
        ]
        
        # Position at bottom center
        start_x = self.sw // 2 - 200
        y = self.sh - 80
        spacing = 100
        
        for i, ability in enumerate(abilities):
            x = start_x + i * spacing
            key = ability['key'].lower()
            cooldown = player.ability_cooldowns[key]
            max_cooldown = player.ability_durations[key]
            
            # Background circle
            radius = 28
            pygame.draw.circle(surface, (20, 10, 30), (x, y), radius)
            pygame.draw.circle(surface, ability['color'], (x, y), radius, width=2)
            
            # Cooldown overlay
            if cooldown > 0:
                ratio = cooldown / max_cooldown
                # Draw pie slice for cooldown
                angle = ratio * 360
                points = [(x, y)]
                for a in range(int(angle) + 1):
                    rad = math.radians(a - 90)
                    px = x + math.cos(rad) * radius
                    py = y + math.sin(rad) * radius
                    points.append((px, py))
                if len(points) > 2:
                    pygame.draw.polygon(surface, (40, 20, 50, 180), points)
                
                # Cooldown text
                cd_txt = self.font_small.render(f"{cooldown:.1f}s", True, (200, 200, 200))
                surface.blit(cd_txt, (x - cd_txt.get_width()//2, y - cd_txt.get_height()//2))
            else:
                # Ready - show key
                pulse = pulse_value(game_time + i, speed=2.0, lo=0.7, hi=1.0)
                c = tuple(int(v * pulse) for v in ability['color'])
                key_txt = self.font_large.render(ability['key'], True, c)
                surface.blit(key_txt, (x - key_txt.get_width()//2, y - key_txt.get_height()//2))
            
            # Ability name below
            name_txt = self.font_small.render(ability['name'], True, ability['color'])
            surface.blit(name_txt, (x - name_txt.get_width()//2, y + radius + 4))
    
    def _draw_levelup_indicator(self, surface, game_time):
        """Draw detailed level-up indicator showing stat increases."""
        if not self.levelup_display or not isinstance(self.levelup_display, dict):
            return
        
        data = self.levelup_display
        timer = data.get("timer", 0)
        
        if timer <= 0:
            return
        
        # Fade in/out
        if timer > 3.5:
            alpha = int((4.0 - timer) * 255 * 2)  # Fade in
        elif timer < 0.5:
            alpha = int(timer * 255 * 2)  # Fade out
        else:
            alpha = 255
        
        # Panel dimensions
        panel_w, panel_h = 400, 200
        panel_x = self.sw // 2 - panel_w // 2
        panel_y = self.sh // 2 - panel_h // 2 - 50
        
        # Background panel
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((15, 10, 35, min(240, alpha)))
        
        # Glowing border
        pulse = pulse_value(game_time, speed=2.0, lo=0.7, hi=1.0)
        border_color = tuple(int(v * pulse) for v in (255, 220, 0))
        pygame.draw.rect(panel, (*border_color, min(255, alpha)), (0, 0, panel_w, panel_h), 
                        width=3, border_radius=10)
        
        # Glow effect
        glow_surf = pygame.Surface((panel_w + 20, panel_h + 20), pygame.SRCALPHA)
        for i in range(3):
            glow_alpha = int((30 - i * 10) * pulse * (alpha / 255))
            pygame.draw.rect(glow_surf, (*border_color, glow_alpha), 
                           (10 - i * 3, 10 - i * 3, panel_w + i * 6, panel_h + i * 6), 
                           width=3, border_radius=12)
        surface.blit(glow_surf, (panel_x - 10, panel_y - 10))
        
        # Title
        title = self.font_large.render("LEVEL UP!", True, (255, 220, 0))
        title.set_alpha(alpha)
        panel.blit(title, (panel_w // 2 - title.get_width() // 2, 15))
        
        # Level change
        level_text = self.font_large.render(
            f"{data.get('old_level', 1)} → {data.get('new_level', 2)}", 
            True, (255, 255, 255)
        )
        level_text.set_alpha(alpha)
        panel.blit(level_text, (panel_w // 2 - level_text.get_width() // 2, 45))
        
        # Divider
        pygame.draw.line(panel, (255, 220, 0, min(200, alpha)), 
                        (30, 75), (panel_w - 30, 75), width=2)
        
        # Stat increases
        y_offset = 90
        
        # Genome capacity
        old_genome = data.get('old_genome', 40)
        new_genome = data.get('new_genome', 48)
        genome_increase = new_genome - old_genome
        genome_txt = self.font_med.render("Genome Capacity:", True, NEON_CYAN)
        genome_txt.set_alpha(alpha)
        panel.blit(genome_txt, (40, y_offset))
        
        genome_val = self.font_med.render(
            f"{old_genome} → {new_genome} (+{genome_increase})", 
            True, (0, 255, 100)
        )
        genome_val.set_alpha(alpha)
        panel.blit(genome_val, (panel_w - genome_val.get_width() - 40, y_offset))
        
        y_offset += 30
        
        # Biomass capacity
        old_biomass = data.get('old_biomass', 60)
        new_biomass = data.get('new_biomass', 70)
        biomass_increase = new_biomass - old_biomass
        biomass_txt = self.font_med.render("Biomass Capacity:", True, NEON_CYAN)
        biomass_txt.set_alpha(alpha)
        panel.blit(biomass_txt, (40, y_offset))
        
        biomass_val = self.font_med.render(
            f"{old_biomass} → {new_biomass} (+{biomass_increase})", 
            True, (0, 255, 100)
        )
        biomass_val.set_alpha(alpha)
        panel.blit(biomass_val, (panel_w - biomass_val.get_width() - 40, y_offset))
        
        y_offset += 35
        
        # Hint text
        hint = self.font_small.render("Press TAB to redesign your creature!", True, (200, 200, 200))
        hint.set_alpha(alpha)
        panel.blit(hint, (panel_w // 2 - hint.get_width() // 2, y_offset))
        
        # Blit panel to screen
        surface.blit(panel, (panel_x, panel_y))
