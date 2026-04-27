# Integration Guide - Step by Step

This guide will help you integrate all the new features into your existing HEXCORE: ASCEND game.

## 🔄 Migration Path

### Step 1: Update Constants (5 minutes)

The new `cell_types.py` replaces the cell definitions in `constants.py`. You need to:

1. **In constants.py**, remove or comment out:
   - The `CellType` enum
   - `CELL_TYPE_DEFS` dictionary
   - `get_cell_type_def()` function
   - `CELL_ICONS`, `CELL_COLORS`, `CELL_STAT_BONUS`
   - `CELL_CYCLE`
   - `STARTING_INVENTORY`

2. **Add to the top of constants.py**:
```python
# Import cell types from new module
from cell_types import (
    CellType, CELL_TYPE_DEFS, get_cell_type_def,
    CELL_CYCLE, STARTING_INVENTORY, CELLS_PER_WAVE, BONUS_CELL_WAVES
)
```

### Step 2: Update Player Class (15 minutes)

**File: player.py**

1. **Add imports at top**:
```python
from abilities import AbilityManager, BurstAbility, DashAbility
from cell_types import CellType, get_cell_type_def
from synergy_enhanced import SynergySystem
from meta_progression import meta
```

2. **In `__init__` method**, add:
```python
# Ability system
self.ability_manager = AbilityManager()
self._setup_abilities()

# Apply meta-progression bonuses
self._apply_meta_bonuses()
```

3. **Add new methods**:
```python
def _setup_abilities(self):
    """Setup abilities based on cells"""
    for cell in self.cells:
        cell_def = get_cell_type_def(cell)
        if "ability" in cell_def:
            ability_data = cell_def["ability"]
            if ability_data["type"] == "burst":
                self.ability_manager.add_ability(
                    BurstAbility(
                        damage=ability_data["damage"],
                        radius=ability_data["radius"],
                        cooldown=ability_data["cooldown"]
                    )
                )
            elif ability_data["type"] == "dash":
                self.ability_manager.add_ability(
                    DashAbility(
                        speed=ability_data["speed"],
                        duration=ability_data["duration"],
                        cooldown=ability_data["cooldown"]
                    )
                )

def _apply_meta_bonuses(self):
    """Apply permanent upgrades from meta-progression"""
    bonuses = meta.get_starting_bonuses()
    self.max_hp += bonuses["max_hp"]
    self.hp = self.max_hp
    self.speed += bonuses["speed"]
    self.contact_dmg += bonuses["contact_dmg"]
    self.defense += bonuses["defense"]
    self.regen += bonuses["regen"]

def try_activate_ability(self, ability_index: int, enemies):
    """Try to activate an ability"""
    return self.ability_manager.try_activate(ability_index, self, enemies)
```

4. **In `update` method**, add:
```python
# Update abilities
self.ability_manager.update(dt, self, [])  # Pass enemies list if available
```

5. **Replace synergy calculation** with:
```python
# In _recalculate_stats or wherever synergies are calculated
multipliers = SynergySystem.calculate_synergies(self.cells)
self.max_hp *= multipliers.get("max_hp", 1.0)
self.speed *= multipliers.get("speed", 1.0)
self.contact_dmg *= multipliers.get("contact_dmg", 1.0)
self.defense *= multipliers.get("defense", 1.0)
self.regen *= multipliers.get("regen", 1.0)
# ... etc for other stats
```

### Step 3: Update Game Scene (20 minutes)

**File: game_scene.py**

1. **Add imports**:
```python
from ui_enhanced import ModernHUD, FloatingTextManager, UITheme
from boss import should_spawn_boss, create_boss
from meta_progression import meta
```

2. **In `__init__` or `on_enter`**:
```python
# Replace old HUD with modern one
self.hud = ModernHUD(SCREEN_WIDTH, SCREEN_HEIGHT)
self.floating_text = FloatingTextManager()

# Boss tracking
self.current_boss = None
self.is_boss_wave = False
```

3. **In wave spawn logic**:
```python
def spawn_wave(self):
    # Check for boss wave
    if should_spawn_boss(self.current_wave):
        self.is_boss_wave = True
        self.current_boss = create_boss(
            self.current_wave, 
            WORLD_WIDTH, 
            WORLD_HEIGHT
        )
        self.enemies.append(self.current_boss)
    else:
        self.is_boss_wave = False
        # Normal enemy spawning...
```

4. **In `update` method**:
```python
# Update floating text
self.floating_text.update(dt)

# Handle ability inputs
keys = pygame.key.get_pressed()
if keys[pygame.K_1]:
    if self.player.try_activate_ability(0, self.enemies):
        # Ability activated!
        pass
if keys[pygame.K_2]:
    if self.player.try_activate_ability(1, self.enemies):
        pass
```

5. **In `draw` method**:
```python
# Draw modern HUD
self.hud.draw_hp_bar(screen, self.player.hp, self.player.max_hp, 20, 20)
self.hud.draw_xp_bar(screen, self.player.xp, self.player.xp_required, 
                     self.player.level, SCREEN_WIDTH - 320, 20)
self.hud.draw_wave_counter(screen, self.current_wave, MAX_WAVES, 
                           SCREEN_WIDTH // 2, 20)
self.hud.draw_score(screen, self.score, SCREEN_WIDTH - 20, 60)

# Draw ability bar
ability_states = self.player.ability_manager.get_ability_states()
self.hud.draw_ability_bar(screen, ability_states, 
                          SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80)

# Draw synergies
synergies = SynergySystem.get_active_synergies(self.player.cells)
self.hud.draw_synergy_panel(screen, synergies, 20, SCREEN_HEIGHT - 250)

# Draw boss health bar if boss wave
if self.is_boss_wave and self.current_boss and self.current_boss.alive:
    self.hud.draw_boss_health_bar(screen, "HEXLORD", 
                                  self.current_boss.hp, 
                                  self.current_boss.max_hp, 100)

# Draw floating text
self.floating_text.draw(screen, camera_x, camera_y)
```

6. **When enemy dies**:
```python
# Add floating text for kills
self.floating_text.add(enemy.x, enemy.y, "+10", UITheme.GOLD, 20, 0.8)
```

7. **On game over**:
```python
# Award essence and save progress
essence_earned = meta.complete_run(
    self.current_wave, 
    self.score, 
    self.total_kills
)
print(f"Earned {essence_earned} essence!")
```

### Step 4: Update Build Scene (15 minutes)

**File: build_scene.py**

1. **Add imports**:
```python
from cell_types import CellType, get_cell_type_def, CELL_CYCLE
from synergy_enhanced import SynergySystem
from meta_progression import meta
```

2. **Filter unlocked cells**:
```python
def get_available_cells(self):
    """Get cells that are unlocked"""
    return [cell for cell in CELL_CYCLE 
            if meta.is_cell_unlocked(cell)]
```

3. **Show synergy preview**:
```python
# When hovering over a cell placement
preview_cells = self.cells.copy()
preview_cells[slot_index] = new_cell_type
synergies = SynergySystem.get_active_synergies(preview_cells)
# Display synergies to show what would change
```

4. **Update cell cycling** to only cycle through unlocked cells:
```python
available_cells = self.get_available_cells()
current_index = available_cells.index(current_cell)
next_cell = available_cells[(current_index + 1) % len(available_cells)]
```

### Step 5: Add Upgrade Shop Scene (30 minutes)

**File: upgrade_shop.py** (NEW FILE)

```python
"""
upgrade_shop.py — Meta-progression upgrade shop
"""
import pygame
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG, COLOR_TEXT
from ui_enhanced import UITheme, ModernHUD
from meta_progression import meta

class UpgradeShopScene:
    def __init__(self):
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        
        self.upgrade_names = [
            "starting_hp", "starting_speed", "starting_damage",
            "starting_defense", "xp_gain", "cell_rewards",
            "powerup_chance", "regen_boost"
        ]
        
        self.selected_index = 0
    
    def on_enter(self, **kwargs):
        pass
    
    def update(self, events, dt):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    from scene_manager import manager
                    manager.switch("main_menu")
                elif event.key == pygame.K_UP:
                    self.selected_index = (self.selected_index - 1) % len(self.upgrade_names)
                elif event.key == pygame.K_DOWN:
                    self.selected_index = (self.selected_index + 1) % len(self.upgrade_names)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    upgrade_name = self.upgrade_names[self.selected_index]
                    if meta.purchase_upgrade(upgrade_name):
                        print(f"Purchased {upgrade_name}!")
    
    def draw(self, screen):
        screen.fill(COLOR_BG)
        
        # Title
        title = self.font_large.render("UPGRADE SHOP", True, UITheme.ACCENT)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 40))
        
        # Essence display
        essence_text = f"Essence: {meta.essence}"
        essence_surf = self.font_medium.render(essence_text, True, UITheme.GOLD)
        screen.blit(essence_surf, (SCREEN_WIDTH // 2 - essence_surf.get_width() // 2, 100))
        
        # Upgrades list
        y = 180
        for i, upgrade_name in enumerate(self.upgrade_names):
            info = meta.get_upgrade_info(upgrade_name)
            
            # Highlight selected
            if i == self.selected_index:
                pygame.draw.rect(screen, UITheme.ACCENT, 
                               (100, y - 5, SCREEN_WIDTH - 200, 60), 2)
            
            # Upgrade name and level
            name_text = f"{info['name']} (Lv {info['level']})"
            color = UITheme.TEXT if info['can_afford'] else UITheme.TEXT_DIM
            name_surf = self.font_medium.render(name_text, True, color)
            screen.blit(name_surf, (120, y))
            
            # Description
            desc_surf = self.font_small.render(info['description'], True, UITheme.TEXT_DIM)
            screen.blit(desc_surf, (120, y + 30))
            
            # Cost
            cost_text = f"Cost: {info['cost']} essence"
            cost_color = UITheme.SUCCESS if info['can_afford'] else UITheme.DANGER
            cost_surf = self.font_small.render(cost_text, True, cost_color)
            screen.blit(cost_surf, (SCREEN_WIDTH - 250, y + 15))
            
            y += 80
        
        # Instructions
        instructions = "↑↓: Select | ENTER: Purchase | ESC: Back"
        inst_surf = self.font_small.render(instructions, True, UITheme.TEXT_DIM)
        screen.blit(inst_surf, (SCREEN_WIDTH // 2 - inst_surf.get_width() // 2, 
                               SCREEN_HEIGHT - 40))
    
    def on_exit(self):
        pass
```

**Then in main.py**, register the scene:
```python
from upgrade_shop import UpgradeShopScene
manager.register("upgrade_shop", UpgradeShopScene())
```

### Step 6: Update Main Menu (10 minutes)

**File: main_menu.py**

Add a button to access the upgrade shop:

```python
# In button list
buttons = [
    # ... existing buttons ...
    {"text": "UPGRADES", "action": lambda: manager.switch("upgrade_shop")},
]
```

## ✅ Testing Checklist

After integration, test these features:

1. **Cell Types**
   - [ ] All 14 cell types appear in build phase
   - [ ] Only unlocked cells are available
   - [ ] Cell stats apply correctly
   - [ ] Cell colors/icons render properly

2. **Abilities**
   - [ ] Burst ability triggers with key 1
   - [ ] Dash ability triggers with key 2
   - [ ] Cooldowns work correctly
   - [ ] Ability bar shows cooldown progress
   - [ ] Dash provides invulnerability

3. **Bosses**
   - [ ] Boss spawns on wave 10
   - [ ] Boss has 3 phases
   - [ ] Boss health bar displays
   - [ ] Boss dies and drops rewards
   - [ ] Normal enemies don't spawn during boss wave

4. **Meta-Progression**
   - [ ] Essence is awarded after runs
   - [ ] Upgrades can be purchased
   - [ ] Upgrades apply to next run
   - [ ] Progress saves between sessions
   - [ ] Achievements unlock

5. **Synergies**
   - [ ] Synergies calculate correctly
   - [ ] Synergy panel displays active synergies
   - [ ] Synergy bonuses apply to stats
   - [ ] Build preview shows synergy changes

6. **UI**
   - [ ] HP bar animates smoothly
   - [ ] XP bar shows level progress
   - [ ] Wave counter displays correctly
   - [ ] Floating text appears for damage/score
   - [ ] Boss health bar appears during boss fights

## 🐛 Common Issues

### Issue: Import errors
**Solution**: Make sure all new files are in the same directory as main.py

### Issue: Cell types not showing
**Solution**: Check that meta.is_cell_unlocked() is being called

### Issue: Abilities not working
**Solution**: Verify that _setup_abilities() is called in player __init__

### Issue: Boss not spawning
**Solution**: Check that should_spawn_boss() returns True on wave 10

### Issue: Synergies not applying
**Solution**: Make sure SynergySystem.calculate_synergies() is called after cell changes

## 🚀 Quick Integration (Minimal Changes)

If you want to test quickly without full integration:

1. Just add the new files to your project
2. In main.py, add at the top:
```python
# Initialize meta-progression
from meta_progression import meta
print(f"Loaded meta-progression: {meta.highest_wave} highest wave")
```

3. Run the game - the new systems will be available but not yet connected

## 📞 Need Help?

If you encounter issues:
1. Check the console for error messages
2. Verify all imports are correct
3. Make sure file names match exactly
4. Test one system at a time

---

**Take your time with integration - test each step before moving to the next!** 🎮
