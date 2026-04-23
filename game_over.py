"""
game_over.py — Game-over / victory screen.
"""
import pygame
from scene_manager import BaseScene
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG, COLOR_TEXT,
    COLOR_ACCENT, COLOR_DANGER, COLOR_SUCCESS, COLOR_TEXT_DIM,
    SCENE_MAIN_MENU,
)
from ui import Button, generate_stars, draw_starfield, render_text_centered
from asset_manager import assets
from data.progress import load_progress


class GameOverScene(BaseScene):

    def __init__(self):
        super().__init__()
        self.stars  = generate_stars(200)
        self.t      = 0.0
        self.won    = False
        self.wave   = 0
        self.score  = 0
        self.kills  = 0

        bw, bh = 220, 48
        cx     = SCREEN_WIDTH // 2 - bw // 2
        self.btn_menu   = Button(cx, SCREEN_HEIGHT // 2 + 120, bw, bh,
                                  "MAIN MENU", color=(100, 120, 160))
        self.btn_replay = Button(cx, SCREEN_HEIGHT // 2 + 60,  bw, bh,
                                  "▶ PLAY AGAIN", color=COLOR_ACCENT)

    def on_enter(self, won=False, wave=0, score=0, kills=0, **kwargs):
        self.won   = won
        self.wave  = wave
        self.score = score
        self.kills = kills
        self.t     = 0.0

    def update(self, events: list, dt: float):
        from input_handler import input_handler
        input_handler.update(events, dt)
        self.t += dt

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.manager.switch(SCENE_MAIN_MENU)

        if self.btn_replay.update(input_handler, dt):
            self.manager.switch("build", wave_num=1, new_cells=[])
        if self.btn_menu.update(input_handler, dt):
            self.manager.switch(SCENE_MAIN_MENU)

    def draw(self, surface: pygame.Surface):
        surface.fill(COLOR_BG)
        draw_starfield(surface, self.t, 0, self.stars)

        title_col  = COLOR_SUCCESS if self.won else COLOR_DANGER
        title_text = "VICTORY!" if self.won else "HEXCORE DESTROYED"
        render_text_centered(surface, title_text, 56, title_col, SCREEN_HEIGHT // 2 - 110)

        font = assets.get_font("default", 22)
        lines = [
            ("Wave reached:  {}".format(self.wave), COLOR_TEXT),
            ("Score:         {}".format(self.score), COLOR_ACCENT),
            ("Kills:         {}".format(self.kills), (255, 150, 80)),
        ]
        progress = load_progress()
        hs = progress.get("high_score", 0)
        lines.append(("High score:    {}".format(hs), (255, 215, 0)))

        y = SCREEN_HEIGHT // 2 - 40
        for txt, col in lines:
            surf = font.render(txt, True, col)
            surface.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2, y))
            y += 34

        self.btn_replay.draw(surface)
        self.btn_menu.draw(surface)
