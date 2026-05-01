"""Settings menu with volume sliders."""

import pygame
import math
import json
from pathlib import Path
from core.constants import *
from core.utils import draw_glow_rect, pulse_value
from core.sounds import play_sound


class VolumeSlider:
    """A horizontal volume slider."""
    
    def __init__(self, x, y, width, label, initial_value=0.7, on_change=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = 20
        self.label = label
        self.value = initial_value
        self.dragging = False
        self.on_change = on_change  # Callback when value changes
        self.font = pygame.font.SysFont("consolas", 14)
        self.rect = pygame.Rect(x, y, width, self.height)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self._update_value(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._update_value(event.pos[0])
    
    def _update_value(self, mouse_x):
        """Update slider value based on mouse position."""
        relative_x = max(0, min(mouse_x - self.x, self.width))
        new_value = relative_x / self.width
        if new_value != self.value:
            self.value = new_value
            if self.on_change:
                self.on_change(self.value)
    
    def draw(self, surface):
        """Draw the slider."""
        # Background track
        track_rect = pygame.Rect(self.x, self.y + 6, self.width, 8)
        pygame.draw.rect(surface, (40, 40, 60), track_rect, border_radius=4)
        pygame.draw.rect(surface, (80, 80, 100), track_rect, width=1, border_radius=4)
        
        # Filled portion
        fill_width = self.width * self.value
        fill_rect = pygame.Rect(self.x, self.y + 6, fill_width, 8)
        pygame.draw.rect(surface, NEON_CYAN, fill_rect, border_radius=4)
        
        # Slider knob
        knob_x = self.x + fill_width
        pygame.draw.circle(surface, NEON_CYAN, (int(knob_x), self.y + 10), 8)
        pygame.draw.circle(surface, WHITE, (int(knob_x), self.y + 10), 8, width=1)
        
        # Label and value
        label_text = self.font.render(f"{self.label}: {int(self.value * 100)}%", True, WHITE)
        surface.blit(label_text, (self.x - 150, self.y - 2))


class SettingsMenu:
    """Settings menu with volume controls."""
    
    SETTINGS_FILE = Path(__file__).parent.parent / "settings.json"
    
    def __init__(self, sw, sh):
        self.sw = sw
        self.sh = sh
        self.visible = False
        self.font_title = pygame.font.SysFont("consolas", 20, bold=True)
        self.font_small = pygame.font.SysFont("consolas", 14)
        
        # Panel dimensions
        self.panel_width = 300
        self.panel_height = 280
        self.panel_x = sw - self.panel_width - 20
        self.panel_y = 20
        
        # Load saved settings
        saved_settings = self._load_settings()
        
        # Sliders with callbacks to update actual volume
        slider_x = self.panel_x + 20
        slider_y = self.panel_y + 60
        slider_width = self.panel_width - 40
        
        self.sliders = {
            "master": VolumeSlider(slider_x, slider_y, slider_width, "Master", 
                                  saved_settings.get("master", 1.0), self._on_master_change),
            "effects": VolumeSlider(slider_x, slider_y + 50, slider_width, "Effects", 
                                   saved_settings.get("effects", 1.0), self._on_effects_change),
            "music": VolumeSlider(slider_x, slider_y + 100, slider_width, "Music", 
                                 saved_settings.get("music", 0.5), self._on_music_change),
        }
        
        # Apply loaded settings
        for slider in self.sliders.values():
            slider._update_value(slider.x + slider.width * slider.value)
        
        # Close button area
        self.close_rect = pygame.Rect(self.panel_x + self.panel_width - 30, self.panel_y + 5, 25, 25)
    
    def _load_settings(self):
        """Load settings from file."""
        try:
            if self.SETTINGS_FILE.exists():
                with open(self.SETTINGS_FILE, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def _save_settings(self):
        """Save settings to file."""
        try:
            settings = {
                "master": self.sliders["master"].value,
                "effects": self.sliders["effects"].value,
                "music": self.sliders["music"].value,
            }
            with open(self.SETTINGS_FILE, 'w') as f:
                json.dump(settings, f)
        except Exception:
            pass
    
    def _on_master_change(self, value):
        """Called when master volume changes."""
        import pygame
        # Set volume on all active channels
        for i in range(pygame.mixer.get_num_channels()):
            pygame.mixer.Channel(i).set_volume(value)
        # Also set music volume
        pygame.mixer.music.set_volume(value)
    
    def _on_effects_change(self, value):
        """Called when effects volume changes."""
        import pygame
        # Set volume on sound effect channels (0-7)
        for i in range(8):
            pygame.mixer.Channel(i).set_volume(value)
    
    def _on_music_change(self, value):
        """Called when music volume changes."""
        import pygame
        # Set volume on music channel (8)
        pygame.mixer.Channel(8).set_volume(value)
        pygame.mixer.music.set_volume(value)
    
    def toggle(self):
        """Toggle settings menu visibility."""
        self.visible = not self.visible
        if not self.visible:
            # Save settings when closing
            self._save_settings()
    
    def handle_event(self, event):
        """Handle input events."""
        if not self.visible:
            return
        
        # Check close button
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.close_rect.collidepoint(event.pos):
                self.visible = False
                return
        
        # Handle slider events
        for slider in self.sliders.values():
            slider.handle_event(event)
    
    def get_volumes(self):
        """Get current volume settings."""
        return {
            "master": self.sliders["master"].value,
            "effects": self.sliders["effects"].value,
            "music": self.sliders["music"].value,
        }
    
    def draw(self, surface, game_time):
        """Draw the settings menu."""
        if not self.visible:
            return
        
        # Semi-transparent background panel
        panel = pygame.Surface((self.panel_width, self.panel_height), pygame.SRCALPHA)
        panel.fill((15, 10, 30, 240))
        surface.blit(panel, (self.panel_x, self.panel_y))
        
        # Border
        pygame.draw.rect(surface, NEON_CYAN, (self.panel_x, self.panel_y, self.panel_width, self.panel_height), width=2, border_radius=8)
        
        # Title
        title = self.font_title.render("SETTINGS", True, NEON_CYAN)
        surface.blit(title, (self.panel_x + 20, self.panel_y + 10))
        
        # Close button (X)
        close_color = NEON_ORANGE if self.close_rect.collidepoint(pygame.mouse.get_pos()) else NEON_CYAN
        pygame.draw.line(surface, close_color, (self.close_rect.left + 5, self.close_rect.top + 5), 
                        (self.close_rect.right - 5, self.close_rect.bottom - 5), 2)
        pygame.draw.line(surface, close_color, (self.close_rect.right - 5, self.close_rect.top + 5), 
                        (self.close_rect.left + 5, self.close_rect.bottom - 5), 2)
        
        # Draw sliders
        for slider in self.sliders.values():
            slider.draw(surface)
        
        # Info text
        info = self.font_small.render("Drag sliders to adjust", True, (160, 140, 180))
        surface.blit(info, (self.panel_x + 20, self.panel_y + self.panel_height - 30))
