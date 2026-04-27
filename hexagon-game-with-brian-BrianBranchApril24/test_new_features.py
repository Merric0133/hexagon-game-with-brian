"""
test_new_features.py — Quick test script for new features
Run this to verify all new systems work before full integration
"""

def test_cell_types():
    """Test the expanded cell type system"""
    print("\n=== Testing Cell Types ===")
    from cell_types import CellType, get_cell_type_def, get_unlocked_cells
    
    # Test all cell types
    for cell_type in CellType:
        cell_def = get_cell_type_def(cell_type)
        icon = cell_def['icon'] if cell_def['icon'] else ' '
        print(f"{icon} {cell_def['name']:12} - {cell_def['description']}")
    
    # Test unlocks
    print(f"\nUnlocked at wave 0: {len(get_unlocked_cells(0))} cells")
    print(f"Unlocked at wave 10: {len(get_unlocked_cells(10))} cells")
    print(f"Unlocked at wave 25: {len(get_unlocked_cells(25))} cells")
    
    print("✅ Cell types working!")


def test_abilities():
    """Test the ability system"""
    print("\n=== Testing Abilities ===")
    from abilities import BurstAbility, DashAbility, AbilityManager
    
    # Create abilities
    burst = BurstAbility(damage=40, radius=150, cooldown=8.0)
    dash = DashAbility(speed=800, duration=0.3, cooldown=5.0)
    
    print(f"Burst ability: {burst.damage} damage, {burst.radius}px radius")
    print(f"Dash ability: {dash.speed} speed, {dash.duration}s duration")
    print(f"Burst ready: {burst.can_use()}")
    print(f"Dash ready: {dash.can_use()}")
    
    # Test ability manager
    manager = AbilityManager()
    manager.add_ability(burst)
    manager.add_ability(dash)
    
    print(f"Abilities in manager: {len(manager.abilities)}")
    states = manager.get_ability_states()
    print(f"Ability states: {states}")
    
    print("✅ Abilities working!")


def test_synergies():
    """Test the enhanced synergy system"""
    print("\n=== Testing Synergies ===")
    from cell_types import CellType
    from synergy_enhanced import SynergySystem
    
    # Test different builds
    builds = {
        "Tank": [CellType.HEART, CellType.HEART, CellType.SHIELD, 
                 CellType.SHIELD, CellType.REGEN, CellType.REGEN],
        "Glass Cannon": [CellType.DAMAGE, CellType.DAMAGE, CellType.DAMAGE,
                        CellType.LEECH, CellType.CRYSTAL, CellType.MOVE],
        "Speed Demon": [CellType.MOVE, CellType.MOVE, CellType.MOVE,
                       CellType.DASH, CellType.VOID, CellType.BURST],
    }
    
    for build_name, cells in builds.items():
        print(f"\n{build_name} Build:")
        synergies = SynergySystem.get_active_synergies(cells)
        for icon, name, value in synergies:
            print(f"  {icon} {name}: +{int(value * 100)}%")
        
        multipliers = SynergySystem.calculate_synergies(cells)
        print(f"  Total HP mult: {multipliers['max_hp']:.2f}x")
        print(f"  Total Speed mult: {multipliers['speed']:.2f}x")
        print(f"  Total Damage mult: {multipliers['contact_dmg']:.2f}x")
    
    print("\n✅ Synergies working!")


def test_boss():
    """Test the boss system"""
    print("\n=== Testing Boss System ===")
    from boss import should_spawn_boss, create_boss
    
    # Test boss spawn logic
    for wave in [5, 10, 15, 20, 25, 30]:
        should_spawn = should_spawn_boss(wave)
        print(f"Wave {wave}: Boss = {should_spawn}")
    
    # Create a test boss
    boss = create_boss(wave=10, world_width=4600, world_height=4600)
    print(f"\nBoss created:")
    print(f"  HP: {boss.hp}/{boss.max_hp}")
    print(f"  Speed: {boss.speed}")
    print(f"  Damage: {boss.damage}")
    print(f"  Phase: {boss.phase}")
    print(f"  Radius: {boss.radius}px")
    
    # Test phase transitions
    boss.hp = boss.max_hp * 0.5  # Trigger phase 2
    boss.update(0.1, 2300, 2300, (4600, 4600))
    print(f"  After damage: Phase {boss.phase}")
    
    print("✅ Boss system working!")


def test_meta_progression():
    """Test the meta-progression system"""
    print("\n=== Testing Meta-Progression ===")
    from meta_progression import meta
    
    print(f"Total runs: {meta.total_runs}")
    print(f"Highest wave: {meta.highest_wave}")
    print(f"Best score: {meta.best_score}")
    print(f"Total kills: {meta.total_kills}")
    print(f"Essence: {meta.essence}")
    
    # Test unlocked cells
    from cell_types import CellType
    print(f"\nUnlocked cells: {len(meta.unlocked_cells)}")
    for cell in [CellType.HEART, CellType.BURST, CellType.VOID]:
        unlocked = meta.is_cell_unlocked(cell)
        print(f"  {cell.name}: {unlocked}")
    
    # Test upgrade info
    print("\nUpgrade Info:")
    for upgrade in ["starting_hp", "xp_gain", "cell_rewards"]:
        info = meta.get_upgrade_info(upgrade)
        print(f"  {info['name']}: Level {info['level']}, Cost {info['cost']}")
    
    # Test starting bonuses
    bonuses = meta.get_starting_bonuses()
    print(f"\nStarting Bonuses:")
    print(f"  HP: +{bonuses['max_hp']}")
    print(f"  Speed: +{bonuses['speed']}")
    print(f"  Damage: +{bonuses['contact_dmg']}")
    print(f"  XP Mult: {bonuses['xp_mult']:.2f}x")
    
    print("✅ Meta-progression working!")


def test_ui():
    """Test the enhanced UI system"""
    print("\n=== Testing Enhanced UI ===")
    import pygame
    from ui_enhanced import ModernHUD, FloatingTextManager, UITheme
    
    # Initialize pygame (minimal)
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    
    # Create HUD
    hud = ModernHUD(800, 600)
    print("ModernHUD created")
    
    # Create floating text manager
    floating_text = FloatingTextManager()
    floating_text.add(400, 300, "+50 XP", UITheme.GOLD, 24, 1.0)
    floating_text.add(420, 280, "+10", UITheme.SUCCESS, 20, 0.8)
    print(f"Floating texts: {len(floating_text.texts)}")
    
    # Update
    floating_text.update(0.1)
    print(f"After update: {len(floating_text.texts)} texts")
    
    pygame.quit()
    print("✅ UI system working!")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("HEXCORE: ASCEND - New Features Test Suite")
    print("=" * 60)
    
    try:
        test_cell_types()
        test_abilities()
        test_synergies()
        test_boss()
        test_meta_progression()
        test_ui()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nYou're ready to integrate the new features!")
        print("See INTEGRATION_GUIDE.md for step-by-step instructions.")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
