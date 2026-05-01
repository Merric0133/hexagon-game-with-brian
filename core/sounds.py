"""
Simple sound effects using pygame.mixer with multiple channels.
Loads MP3 files from the root directory on demand.
"""

import pygame
from pathlib import Path

# Sound file mappings
SOUND_FILES = {
    "dash": "dragon-studio-simple-whoosh-382724.mp3",
    "attack": "freesound_community-item-pickup-sound-100291.mp3",
    "damage": "freesound_community-glass-shatter-3-100155.mp3",
    "heal": "yodguard-healing-magic-4-378668.mp3",
    "rage": "freesound_community-angry-alien-96734.mp3",
    "shield": "freesound_community-shield-guard-6963.mp3",
    "explosion": "soundreality-explosion-fx-343683.mp3",
    "projectile": "dragon-studio-animalistic-grunt-463204.mp3",
    "hit": "lesiakower-minimalist-button-hover-sound-effect-399749.mp3",
    "levelup": "scratchonix-victory-chime-366449.mp3",
    "defeat": "freesound_community-failure-1-89170.mp3",
    "victory": "scratchonix-victory-chime-366449.mp3",
    "menu_hover": "lesiakower-minimalist-button-hover-sound-effect-399749.mp3",
    "menu_click": "creatorshome-digital-click-357350.mp3",
    "shatter": "freesound_community-glass-shatter-3-100155.mp3",
    "zap": "dragon-studio-lightning-strike-386161.mp3",
}

MUSIC_FILES = {
    "game_loop": "1-09. Mystique.mp3",
    "menu": "foggysunrise-glass-gardens-loop-371924.mp3",
    "xenarch": "2-23. The Almighty.mp3",
}

_root_dir = Path(__file__).parent.parent
_sound_cache = {}
_next_channel = 0
_music_channel = None


def _init_mixer():
    """Initialize mixer with enough channels."""
    try:
        # Set up 8 channels for sound effects + 1 for music
        pygame.mixer.set_num_channels(9)
    except:
        pass


def play_sound(sound_name, volume=1.0):
    """Play a sound effect by name."""
    global _next_channel
    
    if sound_name not in SOUND_FILES:
        return
    
    try:
        _init_mixer()
        
        # Load from cache or disk
        if sound_name not in _sound_cache:
            filepath = _root_dir / SOUND_FILES[sound_name]
            if not filepath.exists():
                return
            _sound_cache[sound_name] = pygame.mixer.Sound(str(filepath))
        
        sound = _sound_cache[sound_name]
        sound.set_volume(max(0, min(1, volume)))
        
        # Use channels 0-7 for sound effects (channel 8 is for music)
        channel = pygame.mixer.Channel(_next_channel % 8)
        channel.play(sound)
        _next_channel += 1
    except Exception:
        pass


def play_music(music_name, loops=-1, volume=0.7):
    """Play background music by name."""
    global _music_channel
    
    if music_name not in MUSIC_FILES:
        return
    
    try:
        _init_mixer()
        
        filepath = _root_dir / MUSIC_FILES[music_name]
        if not filepath.exists():
            return
        
        # Use channel 8 for music
        _music_channel = pygame.mixer.Channel(8)
        sound = pygame.mixer.Sound(str(filepath))
        sound.set_volume(max(0, min(1, volume)))
        _music_channel.play(sound, loops=loops)
    except Exception:
        pass


def stop_music():
    """Stop background music."""
    global _music_channel
    try:
        if _music_channel:
            _music_channel.stop()
            _music_channel = None
    except Exception:
        pass


def stop_all_sounds():
    """Stop all sounds."""
    try:
        pygame.mixer.stop()
    except Exception:
        pass
