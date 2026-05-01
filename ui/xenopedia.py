import pygame
from core.utils import draw_glow_rect, draw_glow_circle, pulse_value
from core.constants import *
from data.cells_data import CELLS
from data.races_data import RACES as RACE_DATA
from data.biomes_data import BIOMES

FEATURED_BUILDS = [
    {
        "name": "The Porcupine",
        "race": "Vorrkai",
        "desc": "All spike cells. Just ram everything. Simple and devastating.",
        "layout": {(0,0):"heart",(-1,0):"spike",(1,0):"spike",(0,-1):"spike",(0,1):"spike",(-1,1):"spike",(1,-1):"spike"},
        "tags": ["melee", "aggressive", "beginner"],
    },
    {
        "name": "Storm Caller",
        "race": "Lumenid",
        "desc": "Zapper + ability trigger chain. Electric burst spam. Fragile but lethal.",
        "layout": {(0,0):"heart",(-1,0):"zapper",(1,0):"zapper",(0,-1):"zapper",(0,1):"basic"},
        "tags": ["electric", "ability", "glass cannon"],
    },
    {
        "name": "The Parasite",
        "race": "Myrrhon",
        "desc": "Full symbiosis. Absorb everything you meet. Adapts to any situation.",
        "layout": {(0,0):"heart",(-1,0):"symbiont",(1,0):"symbiont",(0,-1):"basic",(0,1):"leech"},
        "tags": ["adaptive", "symbiosis", "advanced"],
    },
    {
        "name": "Void Phantom",
        "race": "Nullborn",
        "desc": "Phase through attacks, strike from the void. High skill ceiling.",
        "layout": {(0,0):"heart",(-1,0):"spike",(1,0):"thruster",(0,-1):"basic"},
        "tags": ["speed", "phase", "advanced"],
    },
    {
        "name": "Swarm King",
        "race": "Skrix",
        "desc": "Shed cells as minions, overwhelm with chaos. Never stop moving.",
        "layout": {(0,0):"heart",(-1,0):"basic",(1,0):"basic",(0,-1):"thruster",(0,1):"spike",(-1,1):"basic"},
        "tags": ["swarm", "aggressive", "chaotic"],
    },
    {
        "name": "Iron Fortress",
        "race": "Vorrkai",
        "desc": "3 shields + anchor core. Nearly unkillable. Slow but unstoppable.",
        "layout": {(0,0):"heart",(-1,0):"shield",(1,0):"shield",(0,-1):"shield",(0,1):"anchor",(-1,1):"basic",(1,-1):"spike"},
        "tags": ["tank", "defense", "beginner"],
    },
]

class Xenopedia:
    def __init__(self, sw, sh):
        self.sw, self.sh = sw, sh
        self.font_title = pygame.font.SysFont("consolas", 30, bold=True)
        self.font_med   = pygame.font.SysFont("consolas", 15)
        self.font_small = pygame.font.SysFont("consolas", 12)
        self.tab = "builds"  # "builds", "cells", "races", "biomes"
        self.tab_buttons = {}
        self.scroll = 0
        self._build_tabs()
        from ui.menus import Button
        self.back_btn = Button((30, sh-60, 120, 40), "BACK", NEON_ORANGE)

    def _build_tabs(self):
        from ui.menus import Button
        tabs = ["builds", "cells", "races", "biomes"]
        colors = [NEON_CYAN, NEON_PURPLE, NEON_GREEN, NEON_ORANGE]
        for i, (tab, color) in enumerate(zip(tabs, colors)):
            x = 160 + i * 160
            self.tab_buttons[tab] = Button((x, 60, 140, 36), tab.upper(), color)

    def handle_event(self, event):
        if self.back_btn.handle_event(event):
            return "back"
        for tab, btn in self.tab_buttons.items():
            if btn.handle_event(event):
                self.tab = tab
                self.scroll = 0
        if event.type == pygame.MOUSEWHEEL:
            self.scroll -= event.y * 30
            self.scroll = max(0, self.scroll)
        return None

    def draw(self, surface, game_time):
        surface.fill(DEEP_VOID)
        
        # Center the title
        title = self.font_title.render("XENOPEDIA", True, NEON_CYAN)
        surface.blit(title, (self.sw//2 - title.get_width()//2, 14))
        
        # Center the tab buttons
        total_tab_width = len(self.tab_buttons) * 160 - 20
        start_x = self.sw//2 - total_tab_width//2
        for i, (tab, btn) in enumerate(self.tab_buttons.items()):
            btn.rect.x = start_x + i * 160
            btn.draw(surface, game_time)
        
        self.back_btn.draw(surface, game_time)

        # Center the content area
        content_w = min(self.sw - 80, 1200)
        content_x = self.sw//2 - content_w//2
        content_rect = pygame.Rect(content_x, 110, content_w, self.sh - 180)
        clip = surface.get_clip()
        surface.set_clip(content_rect)

        if self.tab == "builds":
            self._draw_builds(surface, content_rect, game_time)
        elif self.tab == "cells":
            self._draw_cells(surface, content_rect, game_time)
        elif self.tab == "races":
            self._draw_races(surface, content_rect, game_time)
        elif self.tab == "biomes":
            self._draw_biomes(surface, content_rect, game_time)

        surface.set_clip(clip)

    def _draw_builds(self, surface, area, game_time):
        import math
        from core.utils import draw_hex
        card_w, card_h = 380, 200  # Increased height from 160 to 200
        cols = 3
        pad = 20  # Increased padding
        for i, build in enumerate(FEATURED_BUILDS):
            row, col = divmod(i, cols)
            x = area.x + col * (card_w + pad)
            y = area.y + row * (card_h + pad) - self.scroll
            if y + card_h < area.y or y > area.bottom:
                continue
            rect = pygame.Rect(x, y, card_w, card_h)
            rdata = RACE_DATA.get(build["race"], {})
            color = rdata.get("glow", NEON_CYAN)
            pulse = pulse_value(game_time + i, speed=1.2, lo=0.7, hi=1.0)

            panel = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            panel.fill((12, 6, 28, 200))
            surface.blit(panel, rect.topleft)
            pygame.draw.rect(surface, tuple(int(v*pulse) for v in color), rect, width=2, border_radius=6)

            name_t = self.font_med.render(build["name"], True, WHITE)
            race_t = self.font_small.render(f"Race: {build['race']}", True, color)
            surface.blit(name_t, (x+10, y+10))
            surface.blit(race_t, (x+10, y+30))

            # Mini layout preview - moved to top right
            preview_cx = x + card_w - 70
            preview_cy = y + 50
            for (hc, hr), ctype in build["layout"].items():
                cdata = CELLS.get(ctype, CELLS["basic"])
                px = preview_cx + hc * 14 + (hr % 2) * 7
                py = preview_cy + hr * 12
                draw_hex(surface, cdata["color"], (px, py), 6)

            # Description - word wrap with proper spacing
            desc_y = y + 55
            words = build["desc"].split()
            lines, line = [], ""
            max_width = card_w - 150  # Leave space for preview
            for w in words:
                test = line + w + " "
                if self.font_small.size(test)[0] > max_width:
                    if line:  # Only append if line has content
                        lines.append(line.strip())
                    line = w + " "
                else:
                    line = test
            if line.strip():
                lines.append(line.strip())
            
            # Draw description lines with proper spacing
            for j, ln in enumerate(lines[:4]):  # Show up to 4 lines
                t = self.font_small.render(ln, True, (200, 180, 220))
                surface.blit(t, (x+10, desc_y + j*16))

            # Tags at bottom
            tag_y = y + card_h - 28
            tx = x + 10
            for tag in build["tags"]:
                tag_t = self.font_small.render(f"[{tag}]", True, NEON_ORANGE)
                surface.blit(tag_t, (tx, tag_y))
                tx += tag_t.get_width() + 8

    def _draw_cells(self, surface, area, game_time):
        from core.utils import draw_hex
        card_w, card_h = 220, 140  # Increased height from 120 to 140
        cols = 5
        pad = 16  # Increased padding
        for i, (ctype, cdata) in enumerate(CELLS.items()):
            row, col = divmod(i, cols)
            x = area.x + col * (card_w + pad)
            y = area.y + row * (card_h + pad) - self.scroll
            if y + card_h < area.y or y > area.bottom:
                continue
            rect = pygame.Rect(x, y, card_w, card_h)
            panel = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            panel.fill((12, 6, 28, 200))
            surface.blit(panel, rect.topleft)
            pygame.draw.rect(surface, cdata["glow"], rect, width=2, border_radius=4)
            
            # Hex icon
            draw_hex(surface, cdata["color"], (x+24, y+30), 16)
            
            # Name
            name_t = self.font_small.render(cdata["name"], True, WHITE)
            surface.blit(name_t, (x+50, y+12))
            
            # Description - word wrap
            desc_words = cdata["desc"].split()
            desc_lines = []
            line = ""
            max_width = card_w - 60
            for w in desc_words:
                test = line + w + " "
                if self.font_small.size(test)[0] > max_width:
                    if line:
                        desc_lines.append(line.strip())
                    line = w + " "
                else:
                    line = test
            if line.strip():
                desc_lines.append(line.strip())
            
            # Draw description lines
            desc_y = y + 32
            for j, ln in enumerate(desc_lines[:3]):  # Show up to 3 lines
                desc_t = self.font_small.render(ln, True, (180, 160, 200))
                surface.blit(desc_t, (x+50, desc_y + j*14))
            
            # Stats at bottom
            cost_t = self.font_small.render(f"Cost: {cdata['cost']}", True, NEON_GREEN)
            hp_t = self.font_small.render(f"HP: {cdata['hp']}", True, NEON_CYAN)
            genome_t = self.font_small.render(f"Genome: {cdata['genome']}", True, NEON_ORANGE)
            
            surface.blit(cost_t, (x+8, y + card_h - 42))
            surface.blit(hp_t, (x+8, y + card_h - 28))
            surface.blit(genome_t, (x+8, y + card_h - 14))

    def _draw_races(self, surface, area, game_time):
        card_w, card_h = 380, 220  # Increased height from 180 to 220
        pad = 20  # Increased padding
        for i, (rkey, rdata) in enumerate(RACE_DATA.items()):
            x = area.x + (i % 2) * (card_w + pad)
            y = area.y + (i // 2) * (card_h + pad) - self.scroll
            if y + card_h < area.y or y > area.bottom:
                continue
            rect = pygame.Rect(x, y, card_w, card_h)
            color = rdata["glow"]
            panel = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            panel.fill((12, 6, 28, 200))
            surface.blit(panel, rect.topleft)
            pygame.draw.rect(surface, color, rect, width=2, border_radius=6)
            
            # Icon
            draw_glow_circle(surface, color, (x+35, y+35), 20, alpha=60, layers=2)
            
            # Name and subtitle - moved down a bit
            name_t = self.font_med.render(rdata["display"], True, WHITE)
            sub_t  = self.font_small.render(rdata["subtitle"], True, color)
            surface.blit(name_t, (x+70, y+20))  # Was y+15, now y+20
            surface.blit(sub_t,  (x+70, y+40))  # Was y+35, now y+40
            
            # Trait - word wrap, moved down
            trait_text = f"Trait: {rdata['trait_desc']}"
            trait_words = trait_text.split()
            trait_lines = []
            line = ""
            max_width = card_w - 20
            for w in trait_words:
                test = line + w + " "
                if self.font_small.size(test)[0] > max_width:
                    if line:
                        trait_lines.append(line.strip())
                    line = w + " "
                else:
                    line = test
            if line.strip():
                trait_lines.append(line.strip())
            
            trait_y = y + 72  # Was y+65, now y+72
            for j, ln in enumerate(trait_lines[:2]):  # Show up to 2 lines
                gim_t = self.font_small.render(ln, True, NEON_ORANGE)
                surface.blit(gim_t, (x+10, trait_y + j*16))
            
            # Description - word wrap, moved down
            desc_words = rdata["desc"].split()
            desc_lines = []
            line = ""
            for w in desc_words:
                test = line + w + " "
                if self.font_small.size(test)[0] > max_width:
                    if line:
                        desc_lines.append(line.strip())
                    line = w + " "
                else:
                    line = test
            if line.strip():
                desc_lines.append(line.strip())
            
            desc_y = trait_y + len(trait_lines) * 16 + 12  # Added +2 more spacing
            for j, ln in enumerate(desc_lines[:4]):  # Show up to 4 lines
                desc_t = self.font_small.render(ln, True, (200, 180, 220))
                surface.blit(desc_t, (x+10, desc_y + j*16))

    def _draw_biomes(self, surface, area, game_time):
        card_w, card_h = min(area.width - 20, 700), 140  # Increased height from 120 to 140
        pad = 18  # Increased padding
        for i, (bkey, bdata) in enumerate(BIOMES.items()):
            x = area.x + (area.width - card_w) // 2  # Center the cards
            y = area.y + i * (card_h + pad) - self.scroll
            if y + card_h < area.y or y > area.bottom:
                continue
            rect = pygame.Rect(x, y, card_w, card_h)
            color = bdata["accent"]
            panel = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            panel.fill((*bdata["bg_color"], 220))
            surface.blit(panel, rect.topleft)
            pygame.draw.rect(surface, color, rect, width=2, border_radius=6)
            
            # Icon
            draw_glow_circle(surface, bdata["glow"], (x+35, y+card_h//2), 22, alpha=60, layers=2)
            
            # Name - moved more right
            name_t = self.font_med.render(bdata["name"], True, WHITE)
            surface.blit(name_t, (x+80, y+15))
            
            # Description - word wrap, moved more right
            desc_words = bdata["desc"].split()
            desc_lines = []
            line = ""
            max_width = card_w - 90
            for w in desc_words:
                test = line + w + " "
                if self.font_small.size(test)[0] > max_width:
                    if line:
                        desc_lines.append(line.strip())
                    line = w + " "
                else:
                    line = test
            if line.strip():
                desc_lines.append(line.strip())
            
            desc_y = y + 40
            for j, ln in enumerate(desc_lines[:2]):  # Show up to 2 lines
                desc_t = self.font_small.render(ln, True, (200, 180, 220))
                surface.blit(desc_t, (x+80, desc_y + j*16))
            
            # Modifier - moved more right
            mod_y = desc_y + len(desc_lines[:2]) * 16 + 5
            if bdata.get("modifier"):
                mod_t = self.font_small.render(f"Modifier: {bdata['modifier']['desc']}", True, NEON_ORANGE)
                surface.blit(mod_t, (x+80, mod_y))
                mod_y += 18
            
            # Level range - moved more right
            lv_t = self.font_small.render(f"Levels {bdata['level_range'][0]}-{bdata['level_range'][1]}", True, NEON_GREEN)
            surface.blit(lv_t, (x+80, mod_y))
