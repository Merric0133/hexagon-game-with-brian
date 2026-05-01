#!/usr/bin/env python3
"""
Generate all sound effects for EXODELTA.
Run this script to create all WAV files.
"""

from sound_generator import SoundGenerator

if __name__ == "__main__":
    generator = SoundGenerator()
    generator.generate_all_sounds()
