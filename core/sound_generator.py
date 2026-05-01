"""
Sound generation system for EXODELTA.
Generates all sound effects procedurally without external dependencies.
"""

import numpy as np
import wave
import os
from pathlib import Path

class SoundGenerator:
    """Generate sound effects for the game."""
    
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.sounds_dir = Path(__file__).parent.parent / "sounds"
        self.sounds_dir.mkdir(exist_ok=True)
    
    def _save_wav(self, filename, audio_data):
        """Save audio data as WAV file."""
        filepath = self.sounds_dir / filename
        
        # Normalize audio to 16-bit range
        audio_data = np.int16(audio_data / np.max(np.abs(audio_data)) * 32767)
        
        with wave.open(str(filepath), 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        print(f"✓ Generated: {filename}")
    
    def generate_dash_sound(self):
        """Whoosh sound for dash attack."""
        duration = 0.2
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # Frequency sweep from 800 to 1200 Hz
        freq_start, freq_end = 800, 1200
        freq = np.linspace(freq_start, freq_end, len(t))
        phase = 2 * np.pi * np.cumsum(freq) / self.sample_rate
        
        # Sine wave with envelope
        envelope = np.exp(-5 * t / duration)  # Decay
        audio = np.sin(phase) * envelope
        
        self._save_wav("dash.wav", audio)
    
    def generate_hit_sound(self):
        """Impact sound for collision/hit."""
        duration = 0.15
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # Frequency sweep down (impact effect)
        freq_start, freq_end = 400, 100
        freq = np.linspace(freq_start, freq_end, len(t))
        phase = 2 * np.pi * np.cumsum(freq) / self.sample_rate
        
        # Sine wave with quick decay
        envelope = np.exp(-8 * t / duration)
        audio = np.sin(phase) * envelope
        
        self._save_wav("hit.wav", audio)
    
    def generate_explosion_sound(self):
        """Explosion sound for explosive cell."""
        duration = 0.5
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # Low frequency rumble
        freq = 150
        phase = 2 * np.pi * freq * t
        
        # Add noise for crackle
        noise = np.random.normal(0, 0.3, len(t))
        
        # Envelope: quick attack, slow decay
        envelope = np.exp(-3 * t / duration)
        
        audio = (np.sin(phase) * 0.7 + noise * 0.3) * envelope
        
        self._save_wav("explosion.wav", audio)
    
    def generate_damage_sound(self):
        """Damage/hurt sound."""
        duration = 0.3
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # Two descending tones
        freq1 = 300
        freq2 = 150
        
        # First half: high tone
        t1 = t[:len(t)//2]
        phase1 = 2 * np.pi * freq1 * t1
        audio1 = np.sin(phase1)
        
        # Second half: low tone
        t2 = t[len(t)//2:]
        phase2 = 2 * np.pi * freq2 * t2
        audio2 = np.sin(phase2)
        
        # Combine with envelope
        envelope = np.exp(-4 * t / duration)
        audio = np.concatenate([audio1, audio2]) * envelope
        
        self._save_wav("damage.wav", audio)
    
    def generate_heal_sound(self):
        """Healing/positive sound."""
        duration = 0.4
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # Ascending tones (positive feeling)
        freq1 = 400
        freq2 = 600
        freq3 = 800
        
        # Three ascending notes
        third = len(t) // 3
        
        t1 = t[:third]
        phase1 = 2 * np.pi * freq1 * t1
        audio1 = np.sin(phase1)
        
        t2 = t[third:2*third]
        phase2 = 2 * np.pi * freq2 * t2
        audio2 = np.sin(phase2)
        
        t3 = t[2*third:]
        phase3 = 2 * np.pi * freq3 * t3
        audio3 = np.sin(phase3)
        
        # Envelope
        envelope = np.exp(-2 * t / duration)
        audio = np.concatenate([audio1, audio2, audio3]) * envelope
        
        self._save_wav("heal.wav", audio)
    
    def generate_levelup_sound(self):
        """Level up fanfare."""
        duration = 0.8
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # Ascending chord progression
        freqs = [262, 330, 392, 523]  # C, E, G, C (octave)
        
        audio = np.zeros(len(t))
        quarter = len(t) // 4
        
        for i, freq in enumerate(freqs):
            start = i * quarter
            end = (i + 1) * quarter
            t_seg = t[start:end]
            phase = 2 * np.pi * freq * t_seg
            audio[start:end] = np.sin(phase)
        
        # Envelope
        envelope = np.exp(-2 * t / duration)
        audio = audio * envelope
        
        self._save_wav("levelup.wav", audio)
    
    def generate_telegraph_sound(self):
        """Warning sound for enemy telegraph."""
        duration = 0.3
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # Pulsing tone
        freq = 600
        pulse_freq = 4  # 4 pulses per second
        
        phase = 2 * np.pi * freq * t
        pulse = np.sin(2 * np.pi * pulse_freq * t)
        pulse = (pulse + 1) / 2  # Convert to 0-1 range
        
        audio = np.sin(phase) * pulse
        
        self._save_wav("telegraph.wav", audio)
    
    def generate_shield_sound(self):
        """Shield activation sound."""
        duration = 0.25
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # Ascending sweep
        freq_start, freq_end = 600, 1000
        freq = np.linspace(freq_start, freq_end, len(t))
        phase = 2 * np.pi * np.cumsum(freq) / self.sample_rate
        
        # Envelope
        envelope = np.exp(-4 * t / duration)
        audio = np.sin(phase) * envelope
        
        self._save_wav("shield.wav", audio)
    
    def generate_rage_sound(self):
        """Rage mode activation sound."""
        duration = 0.4
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # Deep, aggressive tone
        freq = 100
        phase = 2 * np.pi * freq * t
        
        # Add harmonics
        audio = (np.sin(phase) * 0.6 + 
                np.sin(phase * 2) * 0.3 + 
                np.sin(phase * 3) * 0.1)
        
        # Envelope
        envelope = np.exp(-3 * t / duration)
        audio = audio * envelope
        
        self._save_wav("rage.wav", audio)
    
    def generate_projectile_sound(self):
        """Projectile fire sound."""
        duration = 0.15
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # Quick ascending tone
        freq_start, freq_end = 400, 800
        freq = np.linspace(freq_start, freq_end, len(t))
        phase = 2 * np.pi * np.cumsum(freq) / self.sample_rate
        
        # Sharp envelope
        envelope = np.exp(-10 * t / duration)
        audio = np.sin(phase) * envelope
        
        self._save_wav("projectile.wav", audio)
    
    def generate_menu_select_sound(self):
        """Menu selection sound."""
        duration = 0.1
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        freq = 800
        phase = 2 * np.pi * freq * t
        
        envelope = np.exp(-8 * t / duration)
        audio = np.sin(phase) * envelope
        
        self._save_wav("menu_select.wav", audio)
    
    def generate_menu_hover_sound(self):
        """Menu hover sound."""
        duration = 0.08
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        freq = 600
        phase = 2 * np.pi * freq * t
        
        envelope = np.exp(-10 * t / duration)
        audio = np.sin(phase) * envelope
        
        self._save_wav("menu_hover.wav", audio)
    
    def generate_victory_sound(self):
        """Victory fanfare."""
        duration = 1.0
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # Victory chord progression
        freqs = [262, 330, 392, 523, 659, 784]  # C major scale
        
        audio = np.zeros(len(t))
        segment_len = len(t) // len(freqs)
        
        for i, freq in enumerate(freqs):
            start = i * segment_len
            end = (i + 1) * segment_len if i < len(freqs) - 1 else len(t)
            t_seg = t[start:end]
            phase = 2 * np.pi * freq * t_seg
            audio[start:end] = np.sin(phase)
        
        # Envelope
        envelope = np.exp(-1.5 * t / duration)
        audio = audio * envelope
        
        self._save_wav("victory.wav", audio)
    
    def generate_defeat_sound(self):
        """Defeat/game over sound."""
        duration = 0.8
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # Descending tones
        freqs = [392, 330, 262, 196]  # G, E, C, G (lower)
        
        audio = np.zeros(len(t))
        segment_len = len(t) // len(freqs)
        
        for i, freq in enumerate(freqs):
            start = i * segment_len
            end = (i + 1) * segment_len if i < len(freqs) - 1 else len(t)
            t_seg = t[start:end]
            phase = 2 * np.pi * freq * t_seg
            audio[start:end] = np.sin(phase)
        
        # Envelope
        envelope = np.exp(-2 * t / duration)
        audio = audio * envelope
        
        self._save_wav("defeat.wav", audio)
    
    def generate_all_sounds(self):
        """Generate all sound effects."""
        print("\n🔊 Generating sound effects...\n")
        
        self.generate_dash_sound()
        self.generate_hit_sound()
        self.generate_explosion_sound()
        self.generate_damage_sound()
        self.generate_heal_sound()
        self.generate_levelup_sound()
        self.generate_telegraph_sound()
        self.generate_shield_sound()
        self.generate_rage_sound()
        self.generate_projectile_sound()
        self.generate_menu_select_sound()
        self.generate_menu_hover_sound()
        self.generate_victory_sound()
        self.generate_defeat_sound()
        
        print(f"\n✅ All sounds generated in: {self.sounds_dir}\n")


if __name__ == "__main__":
    generator = SoundGenerator()
    generator.generate_all_sounds()
