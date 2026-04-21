import pygame

# Screen
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
WINDOW_TITLE, TARGET_FPS = "HEXCORE: ASCEND", 60

# Scene names
SCENE_MAIN_MENU, SCENE_CUSTOMIZE, SCENE_CODEX = "main_menu", "customize", "codex"
SCENE_GAME, SCENE_GAME_OVER, SCENE_HELP = "game", "game_over", "help"

# Data
DATA_DIR = "data"

# Colors
COLOR_BG = (10, 10, 15)
COLOR_TEXT = (240, 240, 240)
COLOR_TEXT_DIM = (140, 140, 150)
COLOR_ACCENT = (0, 200, 255)  # Teal accent
COLOR_ACCENT2 = (255, 100, 200)  # Pink accent
COLOR_DANGER = (255, 80, 80)
COLOR_SUCCESS = (100, 255, 150)
COLOR_WARNING = (255, 220, 100)
COLOR_BORDER = (50, 100, 150)  # Subtle blue border
COLOR_BG_PANEL = (20, 20, 30)
COLOR_GLOW = (0, 150, 200, 100)  # Semi-transparent glow
COLOR_SHADOW = (0, 0, 0, 50)

# Hex
HEX_RADIUS = 30
HEX_SIDES = 6

# World
WORLD_WIDTH, WORLD_HEIGHT = 3000, 3000

# Player stats
PLAYER_SPEED = 300.0
PLAYER_BASE_HP = 100.0
PLAYER_BASE_DEFENSE = 0.0
PLAYER_BASE_REGEN = 1.0

# Enemy stats
ENEMY_BASE_HP = 10.0
ENEMY_BASE_SPEED = 150.0
ENEMY_BASE_DMG = 5.0

# Game
SCORE_PER_KILL = 10
SCORE_PER_WAVE = 100
POWERUP_DROP_CHANCE = 0.25
ENEMY_SPAWN_RATE = 1.0

# Rarity colors
RARITY_COLORS = {
    "common": (200, 200, 200),
    "uncommon": (100, 255, 100),
    "rare": (100, 150, 255),
    "legendary": (255, 215, 0),
}

# ========================================================================
# HEX SKINS — 3 free + unlockable variants
# ========================================================================
HEX_SKINS = [
    {
        "id": "default",
        "name": "Default Hex",
        "fill": (0, 200, 255),
        "border": (0, 150, 200),
        "unlock_wave": 0,
        "description": "Your starting hex form. Classic and reliable.",
    },
    {
        "id": "crimson",
        "name": "Crimson Hex",
        "fill": (220, 50, 50),
        "border": (180, 30, 30),
        "unlock_wave": 0,
        "description": "A fierce red variant. Free skin!",
    },
    {
        "id": "void",
        "name": "Void Hex",
        "fill": (80, 20, 120),
        "border": (150, 50, 200),
        "unlock_wave": 0,
        "description": "Dark and mysterious. Free skin!",
    },
    {
        "id": "gold",
        "name": "Golden Hex",
        "fill": (255, 200, 0),
        "border": (200, 150, 0),
        "unlock_wave": 10,
        "achievement": "Reach Wave 10",
        "description": "Gleaming with power. Reach Wave 10!",
    },
    {
        "id": "emerald",
        "name": "Emerald Hex",
        "fill": (50, 200, 100),
        "border": (30, 150, 70),
        "unlock_wave": 25,
        "achievement": "Reach Wave 25",
        "description": "Forest green elegance. Reach Wave 25!",
    },
    {
        "id": "platinum",
        "name": "Platinum Hex",
        "fill": (200, 200, 220),
        "border": (150, 150, 180),
        "unlock_wave": 50,
        "achievement": "Reach Wave 50",
        "description": "The ultimate victory form. Beat the game!",
    },
]