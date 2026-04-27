"""
ui_enhanced.py — Modern, polished UI system for HEXCORE: ASCEND
"""
import pygame
import math
from typing import List, Tuple, Optional, Dict, Any


class UITheme:
    """Modern UI color theme"""
    BG = (10, 10, 20)
    BG_PANEL = (20, 25, 35)
    BG_PANEL_LIGHT = (30, 35, 45)
    TEXT = (220, 220, 230)
    TEXT_DIM = (140, 140, 150)
    ACCENT = (0, 200, 255)
    ACCENT_GLOW = (0, 150, 200)
    DANGER = (255, 60, 60)
    SUCCESS = (60, 255, 120)
    WARNING = (255, 220, 100)
    GOLD = (255, 215, 0)
    PURPLE = (180, 100, 255)
    BORDER = (50, 100, 150)
    SHADOW = (0, 0, 0, 80)


class ModernHUD:
    """Enhanced HUD with modern design"""
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        self.font_tiny = pygame.font.Font(None, 18)
        
        # Animation states
        self.hp_bar_width = 0
        self.xp_bar_width = 0
        self.shake_offset = (0, 0)
    
    def draw_hp_bar(self, surface: pygame.Surface, current_hp: float, max_hp: float, x: int, y: int, width: int = 300, height: int = 30):
        """Draw modern HP bar with gradient and glow"""
        # Background
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, UITheme.BG_PANEL, bg_rect, border_radius=8)
        pygame.draw.rect(surface, UITheme.BORDER, bg_rect, 2, border_radius=8)
        
        # HP percentage
        hp_percent = max(0, min(1, current_hp / max_hp)) if max_hp > 0 else 0
        
        # Smooth animation
        target_width = int(width * hp_percent)
        self.hp_bar_width += (target_width - self.hp_bar_width) * 0.2
        
        # Color gradient based on HP
        if hp_percent > 0.6:
            color = UITheme.SUCCESS
        elif hp_percent > 0.3:
            color = UITheme.WARNING
        else:
            color = UITheme.DANGER
        
        # Draw HP fill with glow
        if self.hp_bar_width > 0:
            fill_rect = pygame.Rect(x + 2, y + 2, int(self.hp_bar_width) - 4, height - 4)
            
            # Glow effect
            glow_surf = pygame.Surface((fill_rect.width + 10, fill_rect.height + 10), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*color, 60), glow_surf.get_rect(), border_radius=8)
            surface.blit(glow_surf, (fill_rect.x - 5, fill_rect.y - 5))
            
            # Main fill
            pygame.draw.rect(surface, color, fill_rect, border_radius=6)
        
        # HP text
        hp_text = "{} / {}".format(int(current_hp), int(max_hp))
        text_surf = self.font_small.render(hp_text, True, UITheme.TEXT)
        text_rect = text_surf.get_rect(center=(x + width // 2, y + height // 2))
        surface.blit(text_surf, text_rect)
        
        # Label
        label_surf = self.font_tiny.render("HP", True, UITheme.TEXT_DIM)
        surface.blit(label_surf, (x, y - 18))
    
    def draw_xp_bar(self, surface: pygame.Surface, current_xp: float, required_xp: float, level: int, x: int, y: int, width: int = 300, height: int = 20):
        """Draw modern XP bar"""
        # Background
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, UITheme.BG_PANEL, bg_rect, border_radius=6)
        pygame.draw.rect(surface, UITheme.BORDER, bg_rect, 2, border_radius=6)
        
        # XP percentage
        xp_percent = max(0, min(1, current_xp / required_xp)) if required_xp > 0 else 0
        
        # Smooth animation
        target_width = int(width * xp_percent)
        self.xp_bar_width += (target_width - self.xp_bar_width) * 0.15
        
        # Draw XP fill
        if self.xp_bar_width > 0:
            fill_rect = pygame.Rect(x + 2, y + 2, int(self.xp_bar_width) - 4, height - 4)
            pygame.draw.rect(surface, UITheme.PURPLE, fill_rect, border_radius=4)
        
        # Level text
        level_text = f"LVL {level}"
        text_surf = self.font_small.render(level_text, True, UITheme.TEXT)
        text_rect = text_surf.get_rect(midleft=(x + 8, y + height // 2))
        surface.blit(text_surf, text_rect)
        
        # XP text
        xp_text = f"{int(current_xp)}/{int(required_xp)}"
        xp_surf = self.font_tiny.render(xp_text, True, UITheme.TEXT_DIM)
        xp_rect = xp_surf.get_rect(midright=(x + width - 8, y + height // 2))
        surface.blit(xp_surf, xp_rect)
    
    def draw_wave_counter(self, surface: pygame.Surface, current_wave: int, max_waves: int, x: int, y: int):
        """Draw stylish wave counter"""
        # Background panel
        panel_width = 200
        panel_height = 60
        panel_rect = pygame.Rect(x - panel_width // 2, y, panel_width, panel_height)
        
        # Shadow
        shadow_rect = panel_rect.copy()
        shadow_rect.y += 4
        shadow_surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, UITheme.SHADOW, shadow_surf.get_rect(), border_radius=10)
        surface.blit(shadow_surf, shadow_rect)
        
        # Panel
        pygame.draw.rect(surface, UITheme.BG_PANEL, panel_rect, border_radius=10)
        pygame.draw.rect(surface, UITheme.ACCENT, panel_rect, 3, border_radius=10)
        
        # Wave text
        wave_text = f"WAVE {current_wave}"
        text_surf = self.font_large.render(wave_text, True, UITheme.ACCENT)
        text_rect = text_surf.get_rect(center=(x, y + 22))
        surface.blit(text_surf, text_rect)
        
        # Progress text
        progress_text = f"/ {max_waves}"
        progress_surf = self.font_small.render(progress_text, True, UITheme.TEXT_DIM)
        progress_rect = progress_surf.get_rect(center=(x, y + 45))
        surface.blit(progress_surf, progress_rect)
    
    def draw_ability_bar(self, surface: pygame.Surface, abilities: List[Tuple[str, float, bool]], x: int, y: int):
        """Draw ability cooldown indicators"""
        if not abilities:
            return
        
        slot_size = 50
        slot_spacing = 10
        total_width = len(abilities) * (slot_size + slot_spacing) - slot_spacing
        start_x = x - total_width // 2
        
        ability_icons = {
            "burst": "💥",
            "dash": "⚡",
        }
        
        for i, (ability_type, cooldown_percent, can_use) in enumerate(abilities):
            slot_x = start_x + i * (slot_size + slot_spacing)
            slot_rect = pygame.Rect(slot_x, y, slot_size, slot_size)
            
            # Background
            bg_color = UITheme.BG_PANEL_LIGHT if can_use else UITheme.BG_PANEL
            pygame.draw.rect(surface, bg_color, slot_rect, border_radius=8)
            
            # Cooldown overlay
            if cooldown_percent > 0:
                overlay_height = int(slot_size * cooldown_percent)
                overlay_rect = pygame.Rect(slot_x, y + slot_size - overlay_height, slot_size, overlay_height)
                overlay_surf = pygame.Surface((slot_size, overlay_height), pygame.SRCALPHA)
                pygame.draw.rect(overlay_surf, (0, 0, 0, 150), overlay_surf.get_rect())
                surface.blit(overlay_surf, overlay_rect)
            
            # Border
            border_color = UITheme.SUCCESS if can_use else UITheme.BORDER
            pygame.draw.rect(surface, border_color, slot_rect, 2, border_radius=8)
            
            # Icon
            icon = ability_icons.get(ability_type, "?")
            icon_surf = self.font_medium.render(icon, True, UITheme.TEXT)
            icon_rect = icon_surf.get_rect(center=slot_rect.center)
            surface.blit(icon_surf, icon_rect)
            
            # Keybind hint
            keybind = str(i + 1)
            key_surf = self.font_tiny.render(keybind, True, UITheme.TEXT_DIM)
            key_rect = key_surf.get_rect(bottomright=(slot_x + slot_size - 4, y + slot_size - 4))
            surface.blit(key_surf, key_rect)
    
    def draw_score(self, surface: pygame.Surface, score: int, x: int, y: int):
        """Draw score display"""
        score_text = f"SCORE: {score:,}"
        text_surf = self.font_medium.render(score_text, True, UITheme.GOLD)
        text_rect = text_surf.get_rect(topright=(x, y))
        
        # Shadow
        shadow_surf = self.font_medium.render(score_text, True, (0, 0, 0))
        shadow_rect = text_rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 2
        surface.blit(shadow_surf, shadow_rect)
        surface.blit(text_surf, text_rect)
    
    def draw_synergy_panel(self, surface: pygame.Surface, synergies: List[Tuple[str, str, float]], x: int, y: int, max_width: int = 300):
        """Draw active synergies panel"""
        if not synergies:
            return
        
        panel_height = len(synergies) * 28 + 40
        panel_rect = pygame.Rect(x, y, max_width, panel_height)
        
        # Panel background
        pygame.draw.rect(surface, UITheme.BG_PANEL, panel_rect, border_radius=8)
        pygame.draw.rect(surface, UITheme.BORDER, panel_rect, 2, border_radius=8)
        
        # Title
        title_surf = self.font_small.render("SYNERGIES", True, UITheme.ACCENT)
        surface.blit(title_surf, (x + 10, y + 8))
        
        # Synergy list
        for i, (icon, name, value) in enumerate(synergies):
            sy = y + 35 + i * 28
            
            # Icon
            icon_surf = self.font_small.render(icon, True, UITheme.TEXT)
            surface.blit(icon_surf, (x + 10, sy))
            
            # Name
            name_surf = self.font_tiny.render(name, True, UITheme.TEXT)
            surface.blit(name_surf, (x + 35, sy + 2))
            
            # Value
            value_text = f"+{int(value * 100)}%"
            value_surf = self.font_tiny.render(value_text, True, UITheme.SUCCESS)
            value_rect = value_surf.get_rect(topright=(x + max_width - 10, sy + 2))
            surface.blit(value_surf, value_rect)
    
    def draw_boss_health_bar(self, surface: pygame.Surface, boss_name: str, current_hp: float, max_hp: float, y: int):
        """Draw boss health bar at top of screen"""
        width = 600
        height = 40
        x = self.screen_width // 2 - width // 2
        
        # Background
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, UITheme.BG_PANEL, bg_rect, border_radius=10)
        pygame.draw.rect(surface, UITheme.DANGER, bg_rect, 3, border_radius=10)
        
        # HP fill
        hp_percent = max(0, min(1, current_hp / max_hp)) if max_hp > 0 else 0
        if hp_percent > 0:
            fill_width = int((width - 4) * hp_percent)
            fill_rect = pygame.Rect(x + 2, y + 2, fill_width, height - 4)
            pygame.draw.rect(surface, UITheme.DANGER, fill_rect, border_radius=8)
        
        # Boss name
        name_surf = self.font_medium.render(boss_name, True, UITheme.TEXT)
        name_rect = name_surf.get_rect(center=(self.screen_width // 2, y + height // 2))
        surface.blit(name_surf, name_rect)


class FloatingText:
    """Floating damage/score numbers"""
    def __init__(self, x: float, y: float, text: str, color: Tuple[int, int, int], size: int = 24, duration: float = 1.0):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.size = size
        self.duration = duration
        self.timer = duration
        self.vy = -80  # Float upward
        self.font = pygame.font.Font(None, size)
    
    def update(self, dt: float) -> bool:
        """Update position and fade. Returns False when expired."""
        self.timer -= dt
        if self.timer <= 0:
            return False
        
        self.y += self.vy * dt
        return True
    
    def draw(self, surface: pygame.Surface, camera_x: float = 0, camera_y: float = 0):
        """Draw the floating text"""
        alpha = int(255 * (self.timer / self.duration))
        text_surf = self.font.render(self.text, True, self.color)
        text_surf.set_alpha(alpha)
        
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        text_rect = text_surf.get_rect(center=(screen_x, screen_y))
        surface.blit(text_surf, text_rect)


class FloatingTextManager:
    """Manages all floating text"""
    def __init__(self):
        self.texts: List[FloatingText] = []
    
    def add(self, x: float, y: float, text: str, color: Tuple[int, int, int], size: int = 24, duration: float = 1.0):
        """Add a new floating text"""
        self.texts.append(FloatingText(x, y, text, color, size, duration))
    
    def update(self, dt: float):
        """Update all floating texts"""
        self.texts = [text for text in self.texts if text.update(dt)]
    
    def draw(self, surface: pygame.Surface, camera_x: float = 0, camera_y: float = 0):
        """Draw all floating texts"""
        for text in self.texts:
            text.draw(surface, camera_x, camera_y)
    
    def clear(self):
        """Clear all floating texts"""
        self.texts.clear()
