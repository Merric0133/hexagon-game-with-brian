"""
Sound manager for EXODELTA.
Handles loading and playing sound effects.
"""

import pygame
from pathlib import Path
import os

class SoundManager:
    """Manage game sound effects."""
    
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.sounds = {}
        self.music = None
        self.sounds_dir = Path(__file__).parent.parent / "sounds"
        self.current_music = None
        
        if self.enabled:
            try:
                pygame.mixer.init()
                self._load_sounds()
            except Exception as e:
                self.enabled = False
    
    def _load_sounds(self):
        """Load all sound files."""
        sound_files = {
            # Custom real sounds
            "dash": "whiff.wav",
            "rage": "punch.wav",
            "attack": "sfx.wav",
            "game_loop": "house_lo.mp3",
            "menu_music": "secosmic_lo.wav",
            
            # Fallback procedural sounds
            "hit": "hit.wav",
            "explosion": "boom.wav",
            "damage": "damage.wav",
            "heal": "heal.wav",
            "levelup": "levelup.wav",
            "telegraph": "telegraph.wav",
            "shield": "shield.wav",
            "projectile": "projectile.wav",
            "menu_select": "menu_select.wav",
            "menu_hover": "menu_hover.wav",
            "defeat": "defeat.wav",
        }
        
        for sound_name, sound_file in sound_files.items():
            filepath = self.sounds_dir / sound_file
            if filepath.exists():
                try:
                    self.sounds[sound_name] = pygame.mixer.Sound(str(filepath))
                except Exception as e:
                    pass  # Silently skip missing sounds
    
    def play(self, sound_name, volume=1.0):
        """Play a sound effect."""
        if not self.enabled or sound_name not in self.sounds:
            return
        
        try:
            sound = self.sounds[sound_name]
            sound.set_volume(max(0, min(1, volume)))
            sound.play()
        except Exception as e:
            pass
    
    def play_music(self, music_name, loops=-1, volume=0.7):
        """Play background music (loops indefinitely by default)."""
        if not self.enabled:
            return
        
        filepath = self.sounds_dir / music_name
        if not filepath.exists():
            return
        
        try:
            pygame.mixer.music.load(str(filepath))
            pygame.mixer.music.set_volume(max(0, min(1, volume)))
            pygame.mixer.music.play(loops)
            self.current_music = music_name
        except Exception as e:
            pass
    
    def stop_music(self):
        """Stop background music."""
        if self.enabled:
            pygame.mixer.music.stop()
            self.current_music = None
    
    def stop_all(self):
        """Stop all sounds."""
        if self.enabled:
            pygame.mixer.stop()
    
    def set_volume(self, volume):
        """Set master volume."""
        if self.enabled:
            pygame.mixer.set_volume(max(0, min(1, volume)))


# Global sound manager instance
_sound_manager = None

def init_sounds(enabled=True):
    """Initialize the global sound manager."""
    global _sound_manager
    _sound_manager = SoundManager(enabled)

def play_sound(sound_name, volume=1.0):
    """Play a sound effect globally."""
    if _sound_manager:
        _sound_manager.play(sound_name, volume)

def play_music(music_name, loops=-1, volume=0.7):
    """Play background music globally."""
    if _sound_manager:
        _sound_manager.play_music(music_name, loops, volume)

def stop_music():
    """Stop background music globally."""
    if _sound_manager:
        _sound_manager.stop_music()

def stop_all_sounds():
    """Stop all sounds globally."""
    if _sound_manager:
        _sound_manager.stop_all()

def set_master_volume(volume):
    """Set master volume globally."""
    if _sound_manager:
        _sound_manager.set_volume(volume)
