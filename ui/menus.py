import pygame
import math
from core.utils import draw_glow_circle, draw_glow_rect, pulse_value, lerp_color, draw_hex
from core.constants import *
from data.races_data import RACES as RACE_DATA
from core.save_manager import load_all_slots, default_strain, NUM_SLOTS

class Button:
    def __init__(self, rect, text, color=NEON_CYAN, font=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.color = color
        self.hovered = False
        self.font = font or pygame.font.SysFont("consolas", 18, bold=True)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, surface, game_time):
        pulse = pulse_value(game_time, speed=1.5, lo=0.7, hi=1.0) if self.hovered else 0.7
        c = tuple(int(v * pulse) for v in self.color)
        alpha = 160 if self.hovered else 80
        panel = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        panel.fill((*VOID_PURPLE, alpha))
        surface.blit(panel, self.rect.topleft)
        border_color = c if self.hovered else tuple(v//2 for v in self.color)
        pygame.draw.rect(surface, border_color, self.rect, width=2, border_radius=6)
        if self.hovered:
            draw_glow_rect(surface, self.color, self.rect, alpha=40)
        txt = self.font.render(self.text, True, c)
        tx = self.rect.centerx - txt.get_width() // 2
        ty = self.rect.centery - txt.get_height() // 2
        surface.blit(txt, (tx, ty))


class MainMenu:
    def __init__(self, sw, sh):
        self.sw, self.sh = sw, sh
        self.font_title = pygame.font.SysFont("consolas", 64, bold=True)
        self.font_sub    = pygame.font.SysFont("consolas", 18)
        cx = sw // 2
        self.buttons = {
            "play":   Button((cx-120, sh//2-20, 240, 48), "ENTER XENOVA", NEON_CYAN),
            "xeno":   Button((cx-120, sh//2+50, 240, 48), "XENOPEDIA",    NEON_PURPLE),
            "achiev": Button((cx-120, sh//2+120, 240, 48), "ACHIEVEMENTS", NEON_GREEN),
            "quit":   Button((cx-120, sh//2+190, 240, 48), "QUIT",         NEON_ORANGE),
        }
        self.bg_orbs = [
            {"pos": (sw*r, sh*r2), "r": r3, "color": c, "phase": p, "spd": s}
            for r, r2, r3, c, p, s in [
                (0.1, 0.2, 60, NEON_CYAN,   0.0, 0.8),
                (0.8, 0.7, 80, NEON_PURPLE, 1.0, 0.6),
                (0.5, 0.9, 40, NEON_GREEN,  2.0, 1.2),
                (0.2, 0.8, 50, NEON_ORANGE, 0.5, 0.9),
                (0.9, 0.3, 70, NEON_PINK,   1.5, 0.7),
            ]
        ]

    def handle_event(self, event):
        for key, btn in self.buttons.items():
            if btn.handle_event(event):
                return key
        return None

    def draw(self, surface, game_time):
        surface.fill(DEEP_VOID)
        # Ambient orbs
        for orb in self.bg_orbs:
            pulse = pulse_value(game_time + orb["phase"], speed=orb["spd"], lo=0.3, hi=0.8)
            draw_glow_circle(surface, orb["color"], orb["pos"], int(orb["r"] * pulse), alpha=40, layers=3)

        # Title
        title_pulse = pulse_value(game_time, speed=0.8, lo=0.85, hi=1.0)
        title_color = lerp_color(NEON_CYAN, NEON_PURPLE, 0.5 + 0.5 * math.sin(game_time * 0.5))
        title = self.font_title.render("EXODELTA", True, title_color)
        title.set_alpha(int(255 * title_pulse))
        tx = self.sw // 2 - title.get_width() // 2
        draw_glow_circle(surface, title_color, (self.sw//2, self.sh//4), 80, alpha=30, layers=4)
        surface.blit(title, (tx, self.sh // 4 - 40))

        sub = self.font_sub.render("Planet Xenova awaits. Build. Evolve. Survive.", True, NEON_CYAN)
        sub.set_alpha(180)
        surface.blit(sub, (self.sw//2 - sub.get_width()//2, self.sh//4 + 40))

        for btn in self.buttons.values():
            btn.draw(surface, game_time)


class StrainSelectMenu:
    def __init__(self, sw, sh):
        self.sw, self.sh = sw, sh
        self.font_title = pygame.font.SysFont("consolas", 36, bold=True)
        self.font_med   = pygame.font.SysFont("consolas", 16)
        self.font_small = pygame.font.SysFont("consolas", 13)
        self.slots = load_all_slots()
        self.slot_rects = []
        self.back_btn = Button((30, sh-60, 120, 40), "BACK", NEON_ORANGE)
        self._build_slot_rects()

    def _build_slot_rects(self):
        self.slot_rects = []
        card_w, card_h = 200, 260
        total_w = NUM_SLOTS * card_w + (NUM_SLOTS - 1) * 20
        start_x = self.sw // 2 - total_w // 2
        y = self.sh // 2 - card_h // 2
        for i in range(NUM_SLOTS):
            x = start_x + i * (card_w + 20)
            self.slot_rects.append(pygame.Rect(x, y, card_w, card_h))

    def refresh(self):
        self.slots = load_all_slots()

    def handle_event(self, event):
        if self.back_btn.handle_event(event):
            return ("back", None)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self.slot_rects):
                if rect.collidepoint(event.pos):
                    return ("select", i)
        return None

    def draw(self, surface, game_time):
        surface.fill(DEEP_VOID)
        title = self.font_title.render("SELECT STRAIN", True, NEON_CYAN)
        surface.blit(title, (self.sw//2 - title.get_width()//2, 40))

        for i, rect in enumerate(self.slot_rects):
            slot = self.slots[i]
            self._draw_slot_card(surface, rect, i, slot, game_time)

        self.back_btn.draw(surface, game_time)

    def _draw_slot_card(self, surface, rect, index, slot, game_time):
        mx, my = pygame.mouse.get_pos()
        hovered = rect.collidepoint(mx, my)
        pulse = pulse_value(game_time + index, speed=1.2, lo=0.6, hi=1.0) if hovered else 0.6

        panel = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        panel.fill((12, 6, 28, 200))
        surface.blit(panel, rect.topleft)

        if slot:
            race = slot.get("race", "Vorrkai")
            rdata = RACE_DATA.get(race, {})
            color = rdata.get("glow", NEON_CYAN)
            border_c = tuple(int(v * pulse) for v in color)
            pygame.draw.rect(surface, border_c, rect, width=2, border_radius=8)
            if hovered:
                draw_glow_rect(surface, color, rect, alpha=30)

            # Race glow orb
            orb_pos = (rect.centerx, rect.y + 70)
            draw_glow_circle(surface, color, orb_pos, int(30 * pulse), alpha=60, layers=3)

            # Info
            name_txt = self.font_med.render(slot.get("name", f"Strain {index+1}"), True, WHITE)
            race_txt = self.font_small.render(race, True, color)
            lv_txt   = self.font_small.render(f"LV {slot.get('level', 1)}", True, NEON_GREEN)
            biome_txt= self.font_small.render(slot.get("current_biome","membrane").upper(), True, NEON_ORANGE)

            surface.blit(name_txt, (rect.centerx - name_txt.get_width()//2, rect.y + 110))
            surface.blit(race_txt, (rect.centerx - race_txt.get_width()//2, rect.y + 140))
            surface.blit(lv_txt,   (rect.centerx - lv_txt.get_width()//2,   rect.y + 152))
            surface.blit(biome_txt,(rect.centerx - biome_txt.get_width()//2 + 15, rect.y + 175))

            # Delete hint
            del_txt = self.font_small.render("[DEL to reset]", True, (100, 60, 60))
            surface.blit(del_txt, (rect.centerx - del_txt.get_width()//2, rect.bottom - 22))
        else:
            pygame.draw.rect(surface, (40, 20, 60), rect, width=2, border_radius=8)
            empty_txt = self.font_med.render("[ EMPTY ]", True, (80, 60, 100))
            new_txt   = self.font_small.render("Click to create", True, (60, 40, 80))
            surface.blit(empty_txt, (rect.centerx - empty_txt.get_width()//2, rect.centery - 16))
            surface.blit(new_txt,   (rect.centerx - new_txt.get_width()//2,   rect.centery + 8))

        # Slot number
        num_txt = self.font_small.render(f"#{index+1}", True, (80, 60, 100))
        surface.blit(num_txt, (rect.x + 8, rect.y + 8))


class RaceSelectMenu:
    def __init__(self, sw, sh):
        self.sw, self.sh = sw, sh
        self.font_title = pygame.font.SysFont("consolas", 32, bold=True)
        self.font_med   = pygame.font.SysFont("consolas", 15)
        self.font_small = pygame.font.SysFont("consolas", 12)
        self.selected = 0
        self.races = list(RACE_DATA.keys())
        self.back_btn    = Button((30, sh-60, 120, 40), "BACK", NEON_ORANGE)
        self.confirm_btn = Button((sw-180, sh-60, 140, 40), "CONFIRM", NEON_GREEN)
        self.race_rects  = []
        self._build_rects()

    def _build_rects(self):
        self.race_rects = []
        card_w, card_h = 200, 300
        total_w = len(self.races) * card_w + (len(self.races)-1) * 16
        sx = self.sw//2 - total_w//2
        y  = self.sh//2 - card_h//2 + 20
        for i in range(len(self.races)):
            self.race_rects.append(pygame.Rect(sx + i*(card_w+16), y, card_w, card_h))

    def handle_event(self, event):
        if self.back_btn.handle_event(event):
            return ("back", None)
        if self.confirm_btn.handle_event(event):
            return ("confirm", self.races[self.selected])
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self.race_rects):
                if rect.collidepoint(event.pos):
                    self.selected = i
        return None

    def draw(self, surface, game_time):
        surface.fill(DEEP_VOID)
        title = self.font_title.render("CHOOSE YOUR RACE", True, NEON_CYAN)
        surface.blit(title, (self.sw//2 - title.get_width()//2, 30))

        for i, (race_key, rect) in enumerate(zip(self.races, self.race_rects)):
            self._draw_race_card(surface, rect, race_key, i == self.selected, game_time, i)

        self.back_btn.draw(surface, game_time)
        self.confirm_btn.draw(surface, game_time)

    def _draw_race_card(self, surface, rect, race_key, selected, game_time, idx):
        rdata = RACE_DATA[race_key]
        color = rdata["glow"]
        pulse = pulse_value(game_time + idx, speed=1.5, lo=0.7, hi=1.0) if selected else 0.6
        border_c = tuple(int(v * pulse) for v in color)

        panel = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        alpha = 220 if selected else 140
        panel.fill((12, 6, 28, alpha))
        surface.blit(panel, rect.topleft)
        pygame.draw.rect(surface, border_c, rect, width=3 if selected else 1, border_radius=8)
        if selected:
            draw_glow_rect(surface, color, rect, alpha=50)

        # Draw race-specific creature shape preview
        self._draw_race_shape(surface, (rect.centerx, rect.y + 70), rdata, pulse, game_time)

        name_txt = self.font_med.render(rdata["display"], True, WHITE if selected else (160,140,180))
        sub_txt  = self.font_small.render(rdata["subtitle"], True, color)
        surface.blit(name_txt, (rect.centerx - name_txt.get_width()//2, rect.y + 110))
        surface.blit(sub_txt,  (rect.centerx - sub_txt.get_width()//2,  rect.y + 130))

        # Description (word wrap)
        desc = rdata["desc"]
        words = desc.split()
        lines, line = [], ""
        for w in words:
            test = line + w + " "
            if self.font_small.size(test)[0] > rect.w - 16:
                lines.append(line)
                line = w + " "
            else:
                line = test
        if line: lines.append(line)
        for j, ln in enumerate(lines[:4]):
            t = self.font_small.render(ln, True, (180, 160, 200))
            surface.blit(t, (rect.x + 8, rect.y + 158 + j * 14))

        # Movement style label
        move_label = self.font_small.render(f"Movement: {rdata.get('movement_style', 'default').replace('_', ' ').title()}", True, (140, 200, 255))
        surface.blit(move_label, (rect.x + 8, rect.bottom - 60))

        # Trait
        gim_label = self.font_small.render("TRAIT:", True, NEON_ORANGE)
        gim_txt   = self.font_small.render(rdata["trait"].upper(), True, NEON_ORANGE)
        surface.blit(gim_label, (rect.x + 8, rect.bottom - 44))
        surface.blit(gim_txt,   (rect.x + 8, rect.bottom - 28))

    def _draw_race_shape(self, surface, center, rdata, pulse, game_time):
        """Draw a visual representation of the race's body shape."""
        from core.utils import draw_hex
        shape = rdata.get("body_shape", "compact_round")
        color = rdata["color"]
        glow = rdata["glow"]
        
        # Glow
        draw_glow_circle(surface, glow, center, int(35 * pulse), alpha=70, layers=3)
        
        if shape == "compact_round":
            # Vorrkai: dense cluster
            for angle in [0, 60, 120, 180, 240, 300]:
                rad = math.radians(angle)
                x = center[0] + math.cos(rad) * 16
                y = center[1] + math.sin(rad) * 16
                draw_hex(surface, color, (int(x), int(y)), 8)
            draw_hex(surface, color, center, 10)
        
        elif shape == "diamond":
            # Lumenid: diamond
            draw_hex(surface, color, center, 10)
            draw_hex(surface, color, (center[0], center[1]-18), 7)
            draw_hex(surface, color, (center[0], center[1]+18), 7)
            draw_hex(surface, color, (center[0]-16, center[1]), 7)
            draw_hex(surface, color, (center[0]+16, center[1]), 7)
        
        elif shape == "branching":
            # Skrix: multiple tendrils
            draw_hex(surface, color, center, 9)
            for angle in [0, 120, 240]:
                rad = math.radians(angle)
                for i in range(1, 3):
                    x = center[0] + math.cos(rad) * i * 14
                    y = center[1] + math.sin(rad) * i * 14
                    draw_hex(surface, color, (int(x), int(y)), 6)
        
        elif shape == "blob":
            # Myrrhon: amorphous blob
            import random
            random.seed(42)  # consistent shape
            for _ in range(8):
                angle = random.uniform(0, math.pi * 2)
                dist = random.uniform(8, 22)
                x = center[0] + math.cos(angle) * dist
                y = center[1] + math.sin(angle) * dist
                draw_hex(surface, color, (int(x), int(y)), random.randint(6, 10))
            draw_hex(surface, color, center, 11)
        
        elif shape == "long_snake":
            # Nullborn: long thin snake
            for i in range(6):
                y = center[1] - 20 + i * 8
                size = 10 if i == 0 else 7
                draw_hex(surface, color, (center[0], int(y)), size)
