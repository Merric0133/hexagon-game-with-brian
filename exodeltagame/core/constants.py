import pygame

# Screen
SCREEN_W, SCREEN_H = 1280, 720
FPS = 60
TITLE = "EXODELTA"

# Colors - Alien bioluminescent palette
BLACK       = (0, 0, 0)
DEEP_VOID   = (4, 2, 12)
VOID_PURPLE = (18, 8, 35)
NEON_CYAN   = (0, 255, 220)
NEON_PURPLE = (180, 0, 255)
NEON_GREEN  = (0, 255, 100)
NEON_ORANGE = (255, 120, 0)
NEON_PINK   = (255, 0, 150)
NEON_BLUE   = (0, 150, 255)
GOLD        = (255, 200, 50)
WHITE       = (255, 255, 255)
DARK_PANEL  = (10, 5, 25, 200)  # RGBA

# Biome color themes
BIOME_COLORS = {
    "membrane":   {"bg": (20, 8, 5),  "accent": (255, 80, 40),  "glow": (255, 120, 60)},
    "vein":       {"bg": (5, 15, 30), "accent": (0, 180, 255),  "glow": (0, 220, 255)},
    "cortex":     {"bg": (10, 5, 25), "accent": (160, 0, 255),  "glow": (200, 80, 255)},
    "void_stomach":{"bg":(2, 2, 8),   "accent": (0, 255, 120),  "glow": (0, 200, 100)},
    "titan_core": {"bg": (15, 0, 0),  "accent": (255, 50, 0),   "glow": (255, 150, 0)},
}

# Physics
PHYSICS_STEPS = 10
GRAVITY = (0, 0)  # Top-down, no gravity

# Cell grid
HEX_RADIUS = 18
HEX_GAP = 2

# Player
BASE_GENOME_SIZE = 6
BASE_BIOMASS = 100
XP_PER_LEVEL = [0, 100, 250, 500, 900, 1500, 2400, 3700, 5500, 8000]

# Races
RACES = ["Vorrkai", "Lumenid", "Skrix", "Myrrhon", "Nullborn"]

# Game states
STATE_MAIN_MENU    = "main_menu"
STATE_STRAIN_SELECT= "strain_select"
STATE_RACE_SELECT  = "race_select"
STATE_EDITOR       = "editor"
STATE_GAME         = "game"
STATE_XENOPEDIA    = "xenopedia"
STATE_ACHIEVEMENTS = "achievements"
STATE_PAUSED       = "paused"
STATE_GAME_OVER    = "game_over"
STATE_VICTORY      = "victory"

# Layers (draw order)
LAYER_BG      = 0
LAYER_TERRAIN = 1
LAYER_ENTITY  = 2
LAYER_PLAYER  = 3
LAYER_FX      = 4
LAYER_UI      = 5
