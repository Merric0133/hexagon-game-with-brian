"""
cell.py — Cell dataclass representing a single hex slot on the player's body.
"""
from dataclasses import dataclass, field
from constants import CellType, HEX_DIRECTIONS


@dataclass
class Cell:
    slot: int                               # 0-5, which direction from core
    cell_type: CellType = CellType.EMPTY
    flash_timer: float = 0.0               # damage flash

    def offset(self):
        """Return (dx, dy) world offset from the core for this slot."""
        return HEX_DIRECTIONS[self.slot]

    def world_pos(self, core_pos):
        """Return world-space (x, y) for this cell."""
        ox, oy = self.offset()
        return (core_pos[0] + ox, core_pos[1] + oy)
