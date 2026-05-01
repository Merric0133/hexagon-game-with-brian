import pygame
import math
from core.utils import draw_hex, draw_glow_circle, pulse_value
from data.cells_data import CELLS

class Cell:
    def __init__(self, cell_type, hex_col, hex_row, owner=None):
        self.cell_type = cell_type
        self.data = CELLS.get(cell_type, CELLS["basic"]).copy()
        self.hex_col = hex_col
        self.hex_row = hex_row
        self.owner = owner  # reference to creature
        self.hp = self.data["hp"]
        self.max_hp = self.data["hp"]
        self.alive = True
        self.world_pos = (0.0, 0.0)  # set by creature each frame
        self.pulse_t = 0.0
        # Mutation bonus (applied at pickup)
        self.mutation_bonus = {}  # e.g. {"damage": 1.2}
        self.ability_cooldown = 0.0

    def apply_race_modifiers(self, race_data):
        if race_data.get("passive") == "cell_hp_bonus":
            bonus = race_data["passive_value"]
            self.max_hp = int(self.max_hp * (1 + bonus))
            self.hp = self.max_hp
        if race_data.get("passive") == "absorbed_cell_bonus" and self.cell_type == "symbiont":
            bonus = race_data["passive_value"]
            if "damage" in self.data:
                self.data["damage"] = int(self.data["damage"] * (1 + bonus))

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
        return not self.alive  # returns True if cell died

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def update(self, dt, game_time):
        self.pulse_t = game_time
        if self.ability_cooldown > 0:
            self.ability_cooldown -= dt

    def draw(self, surface, screen_pos, zoom=1.0, game_time=0.0):
        r = max(6, int(self.data["radius"] * zoom))
        color = self.data["color"]
        glow_color = self.data["glow"]

        # Pulse scale
        pulse = pulse_value(game_time, speed=1.8, lo=0.92, hi=1.0)
        draw_r = max(4, int(r * pulse))

        # HP-based dimming
        hp_ratio = self.hp / self.max_hp
        dimmed = tuple(int(c * (0.4 + 0.6 * hp_ratio)) for c in color)

        # Glow
        draw_glow_circle(surface, glow_color, screen_pos, draw_r, alpha=50, layers=2)

        # Hex body
        draw_hex(surface, dimmed, screen_pos, draw_r)
        draw_hex(surface, glow_color, screen_pos, draw_r, width=1)

        # HP bar (small, above cell)
        if hp_ratio < 1.0 and zoom > 0.5:
            bar_w = draw_r * 2
            bar_h = max(2, int(3 * zoom))
            bar_x = screen_pos[0] - draw_r
            bar_y = screen_pos[1] - draw_r - bar_h - 2
            pygame.draw.rect(surface, (60, 20, 20), (bar_x, bar_y, bar_w, bar_h))
            pygame.draw.rect(surface, (0, 255, 100), (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))
