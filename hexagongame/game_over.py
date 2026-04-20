# =============================================================================
# scenes/game_over.py — Win / Lose screen with score summary and leaderboard
# =============================================================================

import pygame
import math
from scene_manager import BaseScene
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG, COLOR_TEXT, COLOR_ACCENT,
    COLOR_ACCENT2, COLOR_TEXT_DIM, COLOR_SUCCESS, COLOR_DANGER,
    COLOR_WARNING, SCENE_MAIN_MENU, SCENE_GAME, HEX_SKINS,
)
from ui import (
    Button, draw_panel, generate_stars, draw_starfield,
    render_text_centered,
)
from hex_renderer import draw_hex_preview
from asset_manager import assets
from data.progress import load_highscores, get_selected_skin


class GameOverScene(BaseScene):
    """
    Shown after the player wins or loses.

    Receives kwargs from Gameswitch():
        won   : bool  — True = victory, False = defeat
        wave  : int   — wave reached
        score : int   — final score
        kills : int   — total kills
    """

    def __init__(self):
        super().__init__()
        self.stars = generate_stars(200)
        self.t     = 0.0

        # Results (populated in on_enter)
        self.won   = False
        self.wave  = 1
        self.score = 0
        self.kills = 0

        self.highscores    = []
        self.skin_data     = HEX_SKINS[0]
        self._entry_rank   = -1   # index of this run in the leaderboard (-1 = not top10)

        # Buttons
        bw, bh = 210, 46
        cx = SCREEN_WIDTH // 2 - bw // 2

        self.btn_play_again = Button(cx, SCREEN_HEIGHT - 170, bw, bh,
                                     "▶  PLAY AGAIN", COLOR_ACCENT)
        self.btn_main_menu  = Button(cx, SCREEN_HEIGHT - 110, bw, bh,
                                     "⌂  MAIN MENU",  (100, 120, 180))

        # Hex animation
        self._hex_rot  = 0.0
        self._pulse_t  = 0.0

    # ---------------------------------------------------------------- Enter

    def on_enter(self, **kwargs):
        self.won   = kwargs.get("won",   False)
        self.wave  = kwargs.get("wave",  1)
        self.score = kwargs.get("score", 0)
        self.kills = kwargs.get("kills", 0)
        self.t     = 0.0
        self._hex_rot = 0.0
        self._pulse_t = 0.0

        self.highscores  = load_highscores()
        skin_id          = get_selected_skin()
        self.skin_data   = next(
            (s for s in HEX_SKINS if s["id"] == skin_id), HEX_SKINS[0]
        )

        # Find where this run placed in the leaderboard
        self._entry_rank = -1
        for i, entry in enumerate(self.highscores):
            if entry["score"] == self.score and entry["wave"] == self.wave:
                self._entry_rank = i
                break

    # --------------------------------------------------------------- Update

    def update(self, events: list, dt: float):
        self.t        += dt
        self._hex_rot += dt * 0.6
        self._pulse_t += dt

        from input_handler import input_handler
        input_handler.update(events)

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.manager.switch(SCENE_GAME)
                if event.key == pygame.K_ESCAPE:
                    self.manager.switch(SCENE_MAIN_MENU)

        if self.btn_play_again.update(input_handler, dt):
            self.manager.switch(SCENE_GAME)
        if self.btn_main_menu.update(input_handler, dt):
            self.manager.switch(SCENE_MAIN_MENU)

    # ----------------------------------------------------------------- Draw

    def draw(self, surface: pygame.Surface):
        surface.fill(COLOR_BG)
        draw_starfield(surface, self.t * 3, 0, self.stars)

        if self.won:
            self._draw_victory(surface)
        else:
            self._draw_defeat(surface)

        self._draw_stats(surface)
        self._draw_leaderboard(surface)

        self.btn_play_again.draw(surface)
        self.btn_main_menu.draw(surface)

    # ------------------------------------------ Win / Lose headers

    def _draw_victory(self, surface: pygame.Surface):
        # Pulsing golden hex
        skin = next(s for s in HEX_SKINS if s["id"] == "gold")
        draw_hex_preview(surface, SCREEN_WIDTH // 2, 90, skin,
                         radius=52, alpha=0.9)

        # Heading with shimmer
        shimmer = abs(math.sin(self.t * 2)) * 60
        col = (int(255), int(200 + shimmer * 0.5), int(shimmer))
        font = assets.get_font("default", 58)
        txt  = font.render("VICTORY!", True, col)
        surface.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2, 150))

        render_text_centered(surface, "You survived all 50 waves.",
                             20, COLOR_TEXT_DIM, 218)

    def _draw_defeat(self, surface: pygame.Surface):
        # Dim red hex
        draw_hex_preview(surface, SCREEN_WIDTH // 2, 90,
                         self.skin_data, radius=48, alpha=0.5)

        font = assets.get_font("default", 58)
        txt  = font.render("DEFEATED", True, COLOR_DANGER)
        surface.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2, 150))

        render_text_centered(surface,
                             f"You reached Wave {self.wave}.",
                             20, COLOR_TEXT_DIM, 218)

    # ------------------------------------------ Stats panel

    def _draw_stats(self, surface: pygame.Surface):
        panel_w = 280
        panel_h = 110
        px      = SCREEN_WIDTH // 2 - panel_w // 2
        py      = 250
        draw_panel(surface, pygame.Rect(px, py, panel_w, panel_h), title="RUN SUMMARY")

        font = assets.get_font("default", 18)
        font_s = assets.get_font("default", 15)
        items = [
            ("Wave Reached",  str(self.wave)),
            ("Score",         f"{self.score:,}"),
            ("Total Kills",   str(self.kills)),
        ]
        y = py + 36
        for label, value in items:
            lbl_surf = font_s.render(label, True, COLOR_TEXT_DIM)
            val_surf = font.render(value,  True, COLOR_ACCENT)
            surface.blit(lbl_surf, (px + 16, y))
            surface.blit(val_surf, (px + panel_w - val_surf.get_width() - 16, y))
            y += 26

        # New personal-best badge
        if self._entry_rank == 0:
            badge_font = assets.get_font("default", 15)
            badge = badge_font.render("★ NEW HIGH SCORE!", True, COLOR_WARNING)
            surface.blit(badge, (SCREEN_WIDTH // 2 - badge.get_width() // 2, py + panel_h + 6))

    # ------------------------------------------ Leaderboard

    def _draw_leaderboard(self, surface: pygame.Surface):
        if not self.highscores:
            return

        panel_w = 340
        panel_x = SCREEN_WIDTH // 2 - panel_w // 2
        panel_y = 420
        panel_h = min(len(self.highscores), 5) * 22 + 44
        draw_panel(surface,
                   pygame.Rect(panel_x, panel_y, panel_w, panel_h),
                   title="TOP SCORES")

        font_s = assets.get_font("default", 15)
        y = panel_y + 36

        for i, entry in enumerate(self.highscores[:5]):
            is_current = (i == self._entry_rank)
            rank_col   = COLOR_WARNING if is_current else COLOR_TEXT_DIM
            row_col    = COLOR_TEXT    if is_current else COLOR_TEXT_DIM

            rank = font_s.render(f"#{i+1}", True, rank_col)
            wave = font_s.render(f"Wave {entry['wave']}", True, row_col)
            sc   = font_s.render(f"{entry['score']:>8,}", True,
                                  COLOR_ACCENT if is_current else COLOR_TEXT_DIM)

            surface.blit(rank, (panel_x + 12, y))
            surface.blit(wave, (panel_x + 50, y))
            surface.blit(sc,   (panel_x + panel_w - sc.get_width() - 12, y))
            y += 22
