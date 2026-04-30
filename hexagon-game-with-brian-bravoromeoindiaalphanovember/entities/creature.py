import pygame
import pymunk
import math
from core.utils import hex_to_pixel, draw_glow_circle, pulse_value, normalize, distance
from entities.cell import Cell
from data.cells_data import CELLS, SYNERGIES

HEX_RADIUS = 20
HEX_SPACING = HEX_RADIUS * 1.85

class Creature:
    """Base class for player and enemy creatures."""

    def __init__(self, space, pos, cell_layout, race_data=None):
        self.space = space
        self.pos = list(pos)
        self.vel = [0.0, 0.0]
        self.race_data = race_data or {}
        self.cell_layout = {}  # (col, row) -> Cell
        self.cells = []
        self.alive = True
        self.scale = 1.0
        self.game_time = 0.0
        self.active_synergies = set()
        self.status_effects = {}  # {"calcify": timer, "phase": timer, ...}

        # Physics body
        self.body = pymunk.Body(body_type=pymunk.Body.DYNAMIC)
        self.body.position = pos
        self.shapes = []
        self.space.add(self.body)

        self._build_from_layout(cell_layout)
        self._rebuild_physics()
        self._check_synergies()

    def _build_from_layout(self, layout):
        """layout: dict {(col,row) or 'col,row': cell_type_str} or list of cell_type_str."""
        self.cell_layout = {}
        self.cells = []
        if isinstance(layout, dict):
            for coord, ctype in layout.items():
                if isinstance(coord, str):
                    col, row = map(int, coord.split(","))
                else:
                    col, row = int(coord[0]), int(coord[1])
                self._add_cell(ctype, col, row)
        else:
            for i, ctype in enumerate(layout):
                self._add_cell(ctype, i - len(layout) // 2, 0)

    def _add_cell(self, cell_type, col, row):
        cell = Cell(cell_type, col, row, owner=self)
        if self.race_data:
            cell.apply_race_modifiers(self.race_data)
        self.cell_layout[(col, row)] = cell
        self.cells.append(cell)

    def _rebuild_physics(self):
        for s in self.shapes:
            if s in self.space.shapes:
                self.space.remove(s)
        self.shapes = []
        total_mass = 0
        for (col, row), cell in self.cell_layout.items():
            offset = hex_to_pixel(col, row, HEX_SPACING)
            r = max(4, int(HEX_RADIUS * self.scale * 0.85))
            shape = pymunk.Circle(self.body, r, offset=offset)
            shape.mass = cell.data["mass"]
            shape.elasticity = 0.4
            shape.friction = 0.5
            shape.collision_type = getattr(self, 'collision_type', 1)
            shape.filter = pymunk.ShapeFilter(group=id(self) % 65535)
            self.space.add(shape)
            self.shapes.append(shape)
            total_mass += cell.data["mass"]
        self.body.mass = max(0.1, total_mass)
        moment = pymunk.moment_for_circle(self.body.mass, 0, HEX_RADIUS * self.scale * 2)
        self.body.moment = moment

    def _check_synergies(self):
        self.active_synergies = set()
        cell_types = [c.cell_type for c in self.cells if c.alive]
        for syn in SYNERGIES:
            if syn.get("cell_type"):
                # Count-based synergy (e.g. 3x spike)
                count = cell_types.count(syn["cell_type"])
                if count >= syn["min_count"]:
                    self.active_synergies.add(syn["name"])
            elif syn.get("required_cells"):
                # Combo synergy (e.g. zapper + leech)
                if all(ct in cell_types for ct in syn["required_cells"]):
                    self.active_synergies.add(syn["name"])

    def get_total_biomass(self):
        return sum(c.hp for c in self.cells if c.alive)

    def get_max_biomass(self):
        return sum(c.max_hp for c in self.cells if c.alive)

    def get_center(self):
        return (self.body.position.x, self.body.position.y)

    def apply_force(self, fx, fy):
        self.body.apply_force_at_world_point((fx, fy), self.body.position)

    def update(self, dt, game_time):
        self.game_time = game_time
        self.pos = [self.body.position.x, self.body.position.y]

        # Update status effect timers
        for key in list(self.status_effects.keys()):
            self.status_effects[key] -= dt
            if self.status_effects[key] <= 0:
                del self.status_effects[key]

        # Update cells
        for cell in self.cells:
            if cell.alive:
                offset = hex_to_pixel(cell.hex_col, cell.hex_row, HEX_SPACING)
                angle = self.body.angle
                cos_a, sin_a = math.cos(angle), math.sin(angle)
                rx = offset[0] * cos_a - offset[1] * sin_a
                ry = offset[0] * sin_a + offset[1] * cos_a
                cell.world_pos = (self.pos[0] + rx, self.pos[1] + ry)
                cell.update(dt, game_time)

        # Remove dead cells
        dead = [c for c in self.cells if not c.alive]
        if dead:
            for c in dead:
                del self.cell_layout[(c.hex_col, c.hex_row)]
            self.cells = [c for c in self.cells if c.alive]
            self._rebuild_physics()
            self._check_synergies()
            self._on_cells_lost(dead)

        if not self.cells:
            self.alive = False

    def _on_cells_lost(self, lost_cells):
        pass  # Override in subclasses

    def take_damage(self, amount, source_pos=None):
        """Distribute damage to nearest cells."""
        if not self.cells:
            return
        if source_pos:
            # Hit nearest cell to source
            nearest = min(self.cells, key=lambda c: distance(c.world_pos, source_pos))
            nearest.take_damage(amount)
        else:
            # Spread to random outer cell
            import random
            target = random.choice(self.cells)
            target.take_damage(amount)

    def draw(self, surface, camera, game_time):
        for cell in self.cells:
            if cell.alive:
                sp = camera.world_to_screen(*cell.world_pos)
                cell.draw(surface, sp, camera.zoom, game_time)
