import pygame
from enum import Enum, auto

# Screen
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
WINDOW_TITLE, TARGET_FPS = "HEXCORE: ASCEND", 60

# Scene names
SCENE_MAIN_MENU  = "main_menu"
SCENE_BUILD      = "build"       # NEW – between waves
SCENE_GAME       = "game"
SCENE_GAME_OVER  = "game_over"
SCENE_HELP       = "help"
SCENE_CUSTOMIZE  = "customize"

# Data directory
DATA_DIR = "data"

# ── Colors ───────────────────────────────────────────────────────────────────
COLOR_BG        = (10,  10,  15)
COLOR_TEXT      = (240, 240, 240)
COLOR_TEXT_DIM  = (140, 140, 150)
COLOR_ACCENT    = (0,   200, 255)
COLOR_ACCENT2   = (255, 100, 200)
COLOR_DANGER    = (255, 80,  80)
COLOR_SUCCESS   = (100, 255, 150)
COLOR_WARNING   = (255, 220, 100)
COLOR_BORDER    = (50,  100, 150)
COLOR_BG_PANEL  = (20,  20,  30)
COLOR_GLOW      = (0,   150, 200, 100)
COLOR_SHADOW    = (0,   0,   0,   50)

# ── Hex geometry ─────────────────────────────────────────────────────────────
HEX_RADIUS  = 30
HEX_SIDES   = 6
CELL_OFFSET = 64          # center-to-center distance between core and cell hex

# Flat-top neighbor directions for the 6 cell slots
HEX_DIRECTIONS = [
    ( CELL_OFFSET,                         0),                               # 0 right
    ( CELL_OFFSET * 0.5,  CELL_OFFSET * 0.866),                             # 1 lower-right
    (-CELL_OFFSET * 0.5,  CELL_OFFSET * 0.866),                             # 2 lower-left
    (-CELL_OFFSET,                         0),                               # 3 left
    (-CELL_OFFSET * 0.5, -CELL_OFFSET * 0.866),                             # 4 upper-left
    ( CELL_OFFSET * 0.5, -CELL_OFFSET * 0.866),                             # 5 upper-right
]

# ── World ─────────────────────────────────────────────────────────────────────
WORLD_WIDTH, WORLD_HEIGHT = 3000, 3000

# ── Player base stats ─────────────────────────────────────────────────────────
PLAYER_BASE_SPEED  = 280.0
PLAYER_BASE_HP     = 100.0
PLAYER_BASE_REGEN  = 0.5

# ── Cell-type mechanics ───────────────────────────────────────────────────────
class CellType(Enum):
    EMPTY  = auto()
    HEART  = auto()   # +20 max HP
    MOVE   = auto()   # +60 speed
    DAMAGE = auto()   # contact damage aura; also boosts projectile dmg
    SHIELD = auto()   # +10 defense / reduces incoming damage

CELL_ICONS = {
    CellType.EMPTY:  "",
    CellType.HEART:  "♥",
    CellType.MOVE:   "➤",
    CellType.DAMAGE: "✦",
    CellType.SHIELD: "⬡",
}

CELL_COLORS = {
    CellType.EMPTY:  (40,  45,  65),
    CellType.HEART:  (240, 80,  100),
    CellType.MOVE:   (80,  230, 160),
    CellType.DAMAGE: (255, 160, 60),
    CellType.SHIELD: (100, 160, 255),
}

# Stat bonuses per equipped cell
CELL_STAT_BONUS = {
    CellType.HEART:  {"max_hp":    20, "contact_dmg": 0,  "speed": 0,  "defense": 0},
    CellType.MOVE:   {"max_hp":    0,  "contact_dmg": 0,  "speed": 60, "defense": 0},
    CellType.DAMAGE: {"max_hp":    0,  "contact_dmg": 15, "speed": 0,  "defense": 0},
    CellType.SHIELD: {"max_hp":    0,  "contact_dmg": 0,  "speed": 0,  "defense": 8},
}

# Cycle order for left-click cycling in build phase
CELL_CYCLE = [CellType.HEART, CellType.MOVE, CellType.DAMAGE, CellType.SHIELD, CellType.EMPTY]

# ── Inventory: cells awarded per wave ────────────────────────────────────────
# After each wave the player gets this many new cells to add to their inventory.
CELLS_PER_WAVE = 2          # base cells rewarded each wave
BONUS_CELL_WAVES = [5, 10, 15, 20, 30, 40, 50]  # extra bonus cell on these waves

# Starting inventory (counts per type)
STARTING_INVENTORY = {
    CellType.HEART:  2,
    CellType.MOVE:   1,
    CellType.DAMAGE: 1,
    CellType.SHIELD: 0,
}

# ── Enemy stats ───────────────────────────────────────────────────────────────
ENEMY_BASE_HP    = 10.0
ENEMY_BASE_SPEED = 140.0
ENEMY_BASE_DMG   = 8.0

# ── Game rules ────────────────────────────────────────────────────────────────
MAX_WAVES           = 50
BASE_ENEMIES        = 5
SCORE_PER_KILL      = 10
SCORE_PER_WAVE      = 100
POWERUP_DROP_CHANCE = 0.2

# ── Rarity colors ─────────────────────────────────────────────────────────────
RARITY_COLORS = {
    "common":    (200, 200, 200),
    "uncommon":  (100, 255, 100),
    "rare":      (100, 150, 255),
    "legendary": (255, 215, 0),
}

# ── Hex skins ─────────────────────────────────────────────────────────────────
HEX_SKINS = [
    {"id": "default", "name": "Default Hex",  "fill": (0,   200, 255), "border": (0,   150, 200), "unlock_wave": 0,  "description": "Classic teal."},
    {"id": "crimson", "name": "Crimson Hex",  "fill": (220, 50,  50),  "border": (180, 30,  30),  "unlock_wave": 0,  "description": "Fierce red."},
    {"id": "void",    "name": "Void Hex",     "fill": (80,  20,  120), "border": (150, 50,  200), "unlock_wave": 0,  "description": "Dark & mysterious."},
    {"id": "gold",    "name": "Golden Hex",   "fill": (255, 200, 0),   "border": (200, 150, 0),   "unlock_wave": 10, "description": "Reach Wave 10!"},
    {"id": "emerald", "name": "Emerald Hex",  "fill": (50,  200, 100), "border": (30,  150, 70),  "unlock_wave": 25, "description": "Reach Wave 25!"},
    {"id": "platinum","name": "Platinum Hex", "fill": (200, 200, 220), "border": (150, 150, 180), "unlock_wave": 50, "description": "Beat the game!"},
]
