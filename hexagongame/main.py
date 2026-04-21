import pygame
import sys
import os
from typing import Optional

# Ensure hexcore/ is on sys.path when running from the parent directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE, TARGET_FPS,
    SCENE_MAIN_MENU, SCENE_CUSTOMIZE, SCENE_CODEX,
    SCENE_GAME, SCENE_GAME_OVER, SCENE_HELP,
    DATA_DIR, HEX_SKINS,
)
from scene_manager import manager

# Import scene classes (registers their definitions)
from main_menu      import MainMenuScene
from game_scene     import GameScene
from game_over      import GameOverScene
from help_scene     import HelpScene
from customize_scene import CustomizeScene
from codex_scene    import CodexScene


def _make_icon() -> Optional[pygame.Surface]:
    """
    Attempt to generate a tiny hex icon for the window title bar.
    Returns None silently if anything goes wrong.
    """
    try:
        from hex_renderer import draw_hex
        icon = pygame.Surface((32, 32), pygame.SRCALPHA)
        draw_hex(icon, 16, 16, HEX_SKINS[0], pulse_t=0,
                 rotation=0, draw_sockets=False)
        return icon
    except Exception:
        return None


def main():
    # ------------------------------------------------------------------
    # Pygame initialisation
    # ------------------------------------------------------------------
    pygame.init()

    # Audio — fail gracefully if the system has no audio device
    pygame.mixer.pre_init(44100, -16, 2, 512)
    try:
        pygame.mixer.init()
    except pygame.error:
        print("[HexCore] Audio unavailable — continuing without sound.")

    # Create the display
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)

    # Optional window icon
    icon = _make_icon()
    if icon:
        pygame.display.set_icon(icon)

    # Ensure the data directory exists for save files
    os.makedirs(DATA_DIR, exist_ok=True)

    clock = pygame.time.Clock()

    # ------------------------------------------------------------------
    # Register all scenes
    # ------------------------------------------------------------------
    manager.register(SCENE_MAIN_MENU, MainMenuScene())
    manager.register(SCENE_GAME,      GameScene())
    manager.register(SCENE_GAME_OVER, GameOverScene())
    manager.register(SCENE_HELP,      HelpScene())
    manager.register(SCENE_CUSTOMIZE, CustomizeScene())
    manager.register(SCENE_CODEX,     CodexScene())

    # Start at the main menu
    manager.switch(SCENE_MAIN_MENU)

    # ------------------------------------------------------------------
    # Main game loop
    # ------------------------------------------------------------------
    running = True
    while running:
        # Delta-time in seconds; capped to prevent "spiral of death" on lag
        dt     = clock.tick(TARGET_FPS) / 1000.0
        dt     = min(dt, 0.05)

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        manager.update(events, dt)
        manager.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
