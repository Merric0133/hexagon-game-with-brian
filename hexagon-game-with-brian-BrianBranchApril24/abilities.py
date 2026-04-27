"""
abilities.py — Active ability system for cells
"""
import pygame
import math
from typing import List, Tuple, Optional, Dict, Any


class Ability:
    """Base class for active abilities"""
    def __init__(self, ability_type: str, cooldown: float, **kwargs):
        self.ability_type = ability_type
        self.max_cooldown = cooldown
        self.current_cooldown = 0.0
        self.is_active = False
        self.params = kwargs
    
    def update(self, dt: float):
        """Update cooldown"""
        if self.current_cooldown > 0:
            self.current_cooldown = max(0, self.current_cooldown - dt)
    
    def can_use(self) -> bool:
        """Check if ability is ready"""
        return self.current_cooldown <= 0 and not self.is_active
    
    def activate(self, player, enemies: List[Any]) -> Optional[Dict[str, Any]]:
        """Activate the ability. Returns effect data if any."""
        if not self.can_use():
            return None
        
        self.current_cooldown = self.max_cooldown
        self.is_active = True
        return self._execute(player, enemies)
    
    def _execute(self, player, enemies: List[Any]) -> Optional[Dict[str, Any]]:
        """Override in subclasses"""
        return None
    
    def get_cooldown_percent(self) -> float:
        """Get cooldown progress (0.0 = ready, 1.0 = just used)"""
        if self.max_cooldown <= 0:
            return 0.0
        return self.current_cooldown / self.max_cooldown


class BurstAbility(Ability):
    """AOE damage burst around player"""
    def __init__(self, damage: float = 40, radius: float = 150, cooldown: float = 8.0):
        super().__init__("burst", cooldown, damage=damage, radius=radius)
        self.damage = damage
        self.radius = radius
    
    def _execute(self, player, enemies: List[Any]) -> Dict[str, Any]:
        """Deal AOE damage to nearby enemies"""
        hit_enemies = []
        px, py = player.x, player.y
        
        for enemy in enemies:
            if not enemy.alive:
                continue
            dx = enemy.x - px
            dy = enemy.y - py
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist <= self.radius:
                enemy.take_damage(self.damage)
                hit_enemies.append(enemy)
        
        self.is_active = False
        return {
            "type": "burst",
            "x": px,
            "y": py,
            "radius": self.radius,
            "hits": len(hit_enemies),
        }


class DashAbility(Ability):
    """Quick dash with invulnerability"""
    def __init__(self, speed: float = 800, duration: float = 0.3, cooldown: float = 5.0):
        super().__init__("dash", cooldown, speed=speed, duration=duration)
        self.speed = speed
        self.duration = duration
        self.dash_timer = 0.0
        self.dash_dir = (0, 0)
    
    def update(self, dt: float):
        super().update(dt)
        if self.is_active:
            self.dash_timer -= dt
            if self.dash_timer <= 0:
                self.is_active = False
    
    def _execute(self, player, enemies: List[Any]) -> Dict[str, Any]:
        """Start dash in current movement direction"""
        # Get movement direction from player input
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        dy = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
        
        # Default to facing direction if no input
        if dx == 0 and dy == 0:
            dx, dy = 1, 0
        
        # Normalize
        length = math.sqrt(dx*dx + dy*dy)
        if length > 0:
            dx /= length
            dy /= length
        
        self.dash_dir = (dx, dy)
        self.dash_timer = self.duration
        
        # Make player invulnerable during dash
        player.invincible_time = self.duration
        
        return {
            "type": "dash",
            "direction": self.dash_dir,
            "speed": self.speed,
            "duration": self.duration,
        }
    
    def apply_dash_movement(self, player, dt: float):
        """Apply dash movement to player"""
        if self.is_active and self.dash_timer > 0:
            dx, dy = self.dash_dir
            player.x += dx * self.speed * dt
            player.y += dy * self.speed * dt


class AbilityManager:
    """Manages all active abilities for the player"""
    def __init__(self):
        self.abilities = []
        self.ability_effects = []
    
    def add_ability(self, ability: Ability):
        """Add an ability to the manager"""
        self.abilities.append(ability)
    
    def update(self, dt: float, player, enemies: List[Any]):
        """Update all abilities"""
        for ability in self.abilities:
            ability.update(dt)
            
            # Apply dash movement if active
            if isinstance(ability, DashAbility) and ability.is_active:
                ability.apply_dash_movement(player, dt)
        
        # Update visual effects
        self.ability_effects = [
            effect for effect in self.ability_effects
            if effect.get("timer", 0) > 0
        ]
        for effect in self.ability_effects:
            effect["timer"] = effect.get("timer", 0) - dt
    
    def try_activate(self, ability_index: int, player, enemies: List[Any]) -> bool:
        """Try to activate an ability by index"""
        if 0 <= ability_index < len(self.abilities):
            result = self.abilities[ability_index].activate(player, enemies)
            if result:
                # Add visual effect
                result["timer"] = 0.5  # Effect display duration
                self.ability_effects.append(result)
                return True
        return False
    
    def get_ability_states(self) -> List[Tuple[str, float, bool]]:
        """Get state of all abilities (type, cooldown_percent, can_use)"""
        return [
            (ability.ability_type, ability.get_cooldown_percent(), ability.can_use())
            for ability in self.abilities
        ]
    
    def clear(self):
        """Clear all abilities"""
        self.abilities.clear()
        self.ability_effects.clear()
