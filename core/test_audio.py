#!/usr/bin/env python3
"""Test audio system."""

import pygame
from pathlib import Path

# Initialize pygame
pygame.init()
pygame.mixer.init()

sounds_dir = Path(__file__).parent.parent / "sounds"
print(f"Sounds directory: {sounds_dir}")
print(f"Exists: {sounds_dir.exists()}")

if sounds_dir.exists():
    print("\nAudio files found:")
    for f in sorted(sounds_dir.glob("*")):
        print(f"  - {f.name}")
    
    # Try loading a sound
    print("\nTesting sound loading:")
    test_files = ["whiff.wav", "punch.wav", "sfx.wav", "house_lo.mp3", "secosmic_lo.wav"]
    
    for fname in test_files:
        fpath = sounds_dir / fname
        if fpath.exists():
            try:
                sound = pygame.mixer.Sound(str(fpath))
                print(f"  OK: {fname} ({sound.get_length():.2f}s)")
            except Exception as e:
                print(f"  FAIL: {fname} - {e}")
        else:
            print(f"  MISSING: {fname}")
    
    # Try loading music
    print("\nTesting music loading:")
    music_files = ["house_lo.mp3", "secosmic_lo.wav"]
    
    for fname in music_files:
        fpath = sounds_dir / fname
        if fpath.exists():
            try:
                pygame.mixer.music.load(str(fpath))
                print(f"  OK: {fname}")
            except Exception as e:
                print(f"  FAIL: {fname} - {e}")
        else:
            print(f"  MISSING: {fname}")
else:
    print("Sounds directory not found!")
