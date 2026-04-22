"""
main.py — Entry point for HEXCORE: ASCEND (Cell Build Edition)
"""
import pygame
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE, TARGET_FPS,
    SCENE_MAIN_MENU, DATA_DIR, HEX_SKINS,
)
from scene_manager import manager

from main_menu      import MainMenuScene
from build_scene    import BuildScene
from game_scene     import GameScene
from game_over      import GameOverScene
from help_scene     import HelpScene
from customize_scene import CustomizeScene


def _make_icon():
    try:
        from hex_renderer import draw_hex
        icon = pygame.Surface((32, 32), pygame.SRCALPHA)
        draw_hex(icon, 16, 16, HEX_SKINS[0])
        return icon
    except Exception:
        return None


def main():
    pygame.init()
    pygame.mixer.pre_init(44100, -16, 2, 512)
    try:
        pygame.mixer.init()
    except pygame.error:
        print("[HexCore] Audio unavailable — continuing without sound.")

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)

    icon = _make_icon()
    if icon:
        pygame.display.set_icon(icon)

    os.makedirs(DATA_DIR, exist_ok=True)

    clock = pygame.time.Clock()

    # Register scenes
    manager.register(SCENE_MAIN_MENU, MainMenuScene())
    manager.register("build",         BuildScene())
    manager.register("game",          GameScene())
    manager.register("game_over",     GameOverScene())
    manager.register("help",          HelpScene())
    manager.register("customize",     CustomizeScene())

    manager.switch(SCENE_MAIN_MENU)

    running = True
    while running:
        dt     = min(clock.tick(TARGET_FPS) / 1000.0, 0.05)
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
