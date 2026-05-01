# Sound System - Complete Implementation

## Overview
EXODELTA now has a complete procedurally-generated sound system with 14 unique sound effects for all major game events.

## Generated Sound Effects

### Combat Sounds
| Sound | File | Trigger | Volume |
|-------|------|---------|--------|
| **Dash** | dash.wav | Q key dash attack | 0.7 |
| **Hit** | hit.wav | Collision/projectile hit | 0.5-0.7 |
| **Explosion** | explosion.wav | Explosive cell activation | 0.9 |
| **Damage** | damage.wav | Player takes damage | 0.6 |
| **Projectile** | projectile.wav | Projectile fired | 0.5 |

### Ability Sounds
| Sound | File | Trigger | Volume |
|-------|------|---------|--------|
| **Shield** | shield.wav | Shield Burst (E) | 0.8 |
| **Heal** | heal.wav | Heal Pulse (R) | 0.7 |
| **Rage** | rage.wav | Rage Mode (F) | 0.8 |
| **Telegraph** | telegraph.wav | Enemy about to attack | 0.6 |

### Game State Sounds
| Sound | File | Trigger | Volume |
|-------|------|---------|--------|
| **Level Up** | levelup.wav | Player levels up | 0.8 |
| **Victory** | victory.wav | All pillars activated | 0.9 |
| **Defeat** | defeat.wav | Player dies | 0.8 |
| **Menu Select** | menu_select.wav | Menu button click | 0.7 |
| **Menu Hover** | menu_hover.wav | Menu hover | 0.6 |

## Sound Generation Details

### Technology
- **Library**: NumPy for audio synthesis
- **Format**: WAV (44.1 kHz, 16-bit mono)
- **Method**: Procedural generation (no external audio files needed)
- **Location**: `sounds/` directory

### Sound Characteristics

**Dash Sound**
- Frequency sweep: 800 → 1200 Hz
- Duration: 0.2 seconds
- Effect: Whoosh/movement sound
- Envelope: Exponential decay

**Hit Sound**
- Frequency sweep: 400 → 100 Hz (downward)
- Duration: 0.15 seconds
- Effect: Impact/collision
- Envelope: Quick decay

**Explosion Sound**
- Base frequency: 150 Hz
- Duration: 0.5 seconds
- Effect: Low rumble + noise crackle
- Envelope: Slow decay

**Damage Sound**
- Two-tone: 300 Hz → 150 Hz
- Duration: 0.3 seconds
- Effect: Descending tones (negative)
- Envelope: Exponential decay

**Heal Sound**
- Three ascending tones: 400 → 600 → 800 Hz
- Duration: 0.4 seconds
- Effect: Positive/ascending feeling
- Envelope: Smooth decay

**Level Up Sound**
- Chord progression: C-E-G-C (262-330-392-523 Hz)
- Duration: 0.8 seconds
- Effect: Fanfare/celebration
- Envelope: Smooth decay

**Victory Sound**
- Scale progression: C-E-G-C-E-G (262-659 Hz)
- Duration: 1.0 seconds
- Effect: Triumphant fanfare
- Envelope: Smooth decay

**Defeat Sound**
- Descending tones: G-E-C-G (392-196 Hz)
- Duration: 0.8 seconds
- Effect: Sad/descending feeling
- Envelope: Smooth decay

## Integration Points

### Sound Manager
Located in `core/sound_manager.py`:
- Initializes pygame mixer
- Loads all WAV files
- Provides global `play_sound()` function
- Handles volume control

### Sound Generator
Located in `core/sound_generator.py`:
- Generates all WAV files procedurally
- Uses NumPy for audio synthesis
- Saves to `sounds/` directory
- Can be re-run anytime

### Game Integration
Sounds are triggered in `core/game.py`:
- Combat events (hit, damage, dash)
- Ability usage (heal, shield, rage)
- Game state changes (levelup, victory, defeat)
- Projectile events (fire, hit)

## How to Generate Sounds

### First Time Setup
```bash
# Install numpy
python -m pip install numpy

# Generate all sounds
python core/generate_sounds.py
```

### Output
```
🔊 Generating sound effects...

✓ Generated: dash.wav
✓ Generated: hit.wav
✓ Generated: explosion.wav
✓ Generated: damage.wav
✓ Generated: heal.wav
✓ Generated: levelup.wav
✓ Generated: telegraph.wav
✓ Generated: shield.wav
✓ Generated: rage.wav
✓ Generated: projectile.wav
✓ Generated: menu_select.wav
✓ Generated: menu_hover.wav
✓ Generated: victory.wav
✓ Generated: defeat.wav

✅ All sounds generated in: sounds/
```

## Sound Files Location
```
hexagon-game/
├── sounds/
│   ├── dash.wav
│   ├── hit.wav
│   ├── explosion.wav
│   ├── damage.wav
│   ├── heal.wav
│   ├── levelup.wav
│   ├── telegraph.wav
│   ├── shield.wav
│   ├── rage.wav
│   ├── projectile.wav
│   ├── menu_select.wav
│   ├── menu_hover.wav
│   ├── victory.wav
│   └── defeat.wav
```

## API Usage

### Playing Sounds
```python
from core.sound_manager import play_sound

# Play a sound at default volume
play_sound("dash")

# Play a sound at custom volume (0.0 - 1.0)
play_sound("hit", volume=0.7)
```

### Initializing Sound System
```python
from core.sound_manager import init_sounds

# Initialize sounds (done automatically in Game.__init__)
init_sounds(enabled=True)
```

### Stopping All Sounds
```python
from core.sound_manager import stop_all_sounds

stop_all_sounds()
```

### Master Volume Control
```python
from core.sound_manager import set_master_volume

set_master_volume(0.5)  # 50% volume
```

## Sound Design Philosophy

### Feedback
- Every action has audio feedback
- Helps player understand game state
- Reinforces visual effects

### Variety
- Different sounds for different events
- Prevents audio fatigue
- Creates immersive experience

### Balance
- Volumes carefully tuned
- No single sound dominates
- Layered effects work together

### Procedural Generation
- No external dependencies
- Lightweight (all sounds < 1MB total)
- Can be regenerated anytime
- Consistent across platforms

## Performance Impact

### File Sizes
- Total sound files: ~500 KB
- Average per sound: ~35 KB
- Negligible memory impact

### CPU Usage
- Sound playback: Minimal
- Handled by pygame mixer
- No performance degradation

### Latency
- Sounds play immediately
- No noticeable delay
- Responsive feedback

## Future Enhancements (Optional)

- **Music tracks** - Background music for different biomes
- **Ambient sounds** - Environmental audio
- **Voice lines** - Character dialogue
- **Sound settings** - In-game volume control
- **Sound effects library** - More varied sounds
- **3D audio** - Positional sound effects
- **Music transitions** - Dynamic music system

## Troubleshooting

### No Sound Playing
1. Check if `sounds/` directory exists
2. Verify WAV files are present
3. Run `python core/generate_sounds.py` to regenerate
4. Check pygame mixer initialization

### Sound Distortion
1. Reduce volume parameter (< 0.8)
2. Check system volume settings
3. Regenerate sounds

### Missing Sounds
1. Run sound generator: `python core/generate_sounds.py`
2. Verify all 14 WAV files exist
3. Check file permissions

## Files Modified/Created

### New Files
- `core/sound_generator.py` - Sound synthesis
- `core/sound_manager.py` - Sound playback
- `core/generate_sounds.py` - Generation script
- `sounds/` - Directory with all WAV files

### Modified Files
- `core/game.py` - Added sound triggers
- `core/constants.py` - (no changes needed)

## Summary

✅ **14 unique sound effects** generated procedurally
✅ **Integrated into all major game events**
✅ **Lightweight and performant**
✅ **Easy to customize and extend**
✅ **No external audio dependencies**
✅ **Consistent cross-platform audio**

The game now has complete audio feedback for all player actions and game events!
