import pygame
from core.utils import draw_glow_rect, draw_glow_circle, pulse_value
from core.constants import *

# Tutorial steps: each has a trigger condition, message, and optional highlight
TUTORIAL_STEPS = [
    {
        "id": "welcome",
        "title": "Welcome to EXODELTA",
        "lines": [
            "You are a microscopic organism on Planet Xenova.",
            "Your goal: grow powerful enough to defeat XENARCH,",
            "the ancient god-organism at the planet's core.",
            "",
            "Press SPACE or click NEXT to continue.",
        ],
        "trigger": "always",
        "highlight": None,
    },
    {
        "id": "movement",
        "title": "Movement",
        "lines": [
            "Use WASD (or arrow keys) to move your creature.",
            "Your mouse AIM rotates the creature — point it",
            "at enemies to face your spike/ability cells toward them.",
            "",
            "Your creature has physics weight and momentum.",
            "Heavier builds are harder to steer — plan accordingly.",
        ],
        "trigger": "always",
        "highlight": "wasd",
    },
    {
        "id": "genome",
        "title": "Genome & Biomass",
        "lines": [
            "Every cell has two costs:",
            "  GENOME SIZE — limits how many heavy cells you can use.",
            "  BIOMASS COST — limits total cells on your body.",
            "",
            "Offensive cells (Spike, Zapper, Acid) have HIGH genome cost.",
            "You can't just stack all attack cells — you need structure.",
        ],
        "trigger": "always",
        "highlight": "genome_bar",
    },
    {
        "id": "heart",
        "title": "Your Heart Cell",
        "lines": [
            "The Heart Cell is your lifeline.",
            "It stores most of your biomass (health).",
            "",
            "Keep it in the CENTER of your body,",
            "surrounded by structural or defense cells.",
            "If your heart dies, you die.",
        ],
        "trigger": "always",
        "highlight": "heart",
    },
    {
        "id": "combat",
        "title": "Combat",
        "lines": [
            "RAM enemies with your Spike cells to deal damage.",
            "Press SPACE to trigger active abilities",
            "(Zapper pulse, Explosive blast, Acid spray).",
            "",
            "Enemies also have cell bodies — hit their weak spots.",
            "Armored Brutes have shields. Aim for their back.",
        ],
        "trigger": "always",
        "highlight": None,
    },
    {
        "id": "cells_fall_off",
        "title": "Genome Integrity",
        "lines": [
            "Take too much damage and your cells start FALLING OFF.",
            "Your creature literally shrinks and weakens mid-fight.",
            "",
            "Retreat to a SAFE ZONE (glowing area) to regenerate.",
            "Lost cells can be replaced by picking up cell drops",
            "scattered around the world.",
        ],
        "trigger": "always",
        "highlight": "genome_bar",
    },
    {
        "id": "editor",
        "title": "Cell Editor",
        "lines": [
            "Press TAB at any time during gameplay to open the editor.",
            "Redesign your build on the fly.",
            "",
            "LMB to place cells, RMB to remove.",
            "The center cell is always your Heart — protect it.",
            "Watch your Genome and Biomass limits!",
        ],
        "trigger": "always",
        "highlight": None,
    },
    {
        "id": "synergies",
        "title": "Cell Synergies",
        "lines": [
            "Certain cell combinations unlock SYNERGIES:",
            "  3x Spike = FRENZY (passive AoE damage)",
            "  Zapper + Leech = VAMPIRIC SHOCK (heals on zap)",
            "  Thruster + Anchor = PULSE DASH (burst speed)",
            "  3x Shield = FORTRESS (40% damage reduction)",
            "",
            "Experiment — synergies are how you get powerful.",
        ],
        "trigger": "always",
        "highlight": None,
    },
    {
        "id": "keybind_abilities",
        "title": "Keybind Abilities",
        "lines": [
            "You have 4 powerful abilities on Q, E, R, F:",
            "  Q = DASH (quick burst of speed)",
            "  E = SHIELD BURST (damage reduction + knockback)",
            "  R = HEAL PULSE (restore health to all cells)",
            "  F = RAGE MODE (increased damage for 5 seconds)",
            "",
            "Watch the cooldown indicators at the bottom!",
        ],
        "trigger": "always",
        "highlight": None,
    },
    {
        "id": "map_system",
        "title": "World Map",
        "lines": [
            "Press M at any time to open the WORLD MAP.",
            "",
            "The world is vast — XENARCH is far away.",
            "Use the map to navigate and find your way.",
            "",
            "Safe zones, enemy nests, and cell caches are marked.",
            "Plan your journey carefully!",
        ],
        "trigger": "always",
        "highlight": None,
    },
    {
        "id": "beating_the_game",
        "title": "How to Beat the Game",
        "lines": [
            "Your ultimate goal: DEFEAT XENARCH.",
            "",
            "1. Explore the world and grow stronger",
            "2. Level up and unlock better cells",
            "3. Challenge MINI-BOSS DOMAINS for powerful buffs",
            "4. Find XENARCH's domain (marked on map)",
            "5. Enter the boss arena and claim victory!",
            "",
            "The journey is long — prepare well!",
        ],
        "trigger": "always",
        "highlight": None,
    },
    {
        "id": "miniboss_domains",
        "title": "Mini-Boss Domains",
        "lines": [
            "Scattered across the world are 3 MINI-BOSS DOMAINS.",
            "Each contains a powerful enemy and a unique reward:",
            "",
            "  • THE DEVOURER: +50% damage to all offensive cells",
            "  • THE ARCHITECT: +20 genome capacity",
            "  • THE SWARM QUEEN: +5 HP/sec passive regeneration",
            "",
            "These buffs are PERMANENT. Hunt them down!",
        ],
        "trigger": "always",
        "highlight": None,
    },
    {
        "id": "progression",
        "title": "Progression",
        "lines": [
            "Kill enemies to gain XP and level up.",
            "Leveling up increases your Genome and Biomass caps,",
            "letting you build bigger, more complex creatures.",
            "",
            "Defeat the zone BOSS to unlock the next biome.",
            "5 biomes stand between you and XENARCH.",
        ],
        "trigger": "always",
        "highlight": "xp_bar",
    },
    {
        "id": "races",
        "title": "Your Race",
        "lines": [
            "Each race has a unique PASSIVE and TRAIT.",
            "Vorrkai: cells are tougher, calcify when hit hard.",
            "Lumenid: electric cells hit harder, ability blinds.",
            "Skrix: lost cells spawn minions.",
            "Myrrhon: absorb enemy cell types.",
            "Nullborn: immune to biome effects, can phase.",
        ],
        "trigger": "always",
        "highlight": "race_badge",
    },
    {
        "id": "done",
        "title": "You're Ready",
        "lines": [
            "That's the basics covered.",
            "But let's do a quick COMBAT TUTORIAL",
            "so you know exactly how to fight.",
            "",
            "Press NEXT to continue, or SKIP to start playing.",
        ],
        "trigger": "always",
        "highlight": None,
    },
    # --- COMBAT BASICS TUTORIAL ---
    {
        "id": "combat_intro",
        "title": "Combat Basics: Overview",
        "lines": [
            "Combat in EXODELTA is all about POSITIONING.",
            "Your cells only deal damage when they TOUCH enemies.",
            "",
            "Spike cells = melee damage on collision",
            "Zapper/Acid/Explosive = abilities (press SPACE)",
        ],
        "trigger": "always",
        "highlight": None,
    },
    {
        "id": "combat_spike",
        "title": "Combat Basics: Spike Cells",
        "lines": [
            "Spike cells are your bread and butter.",
            "RAM enemies with your spikes to deal damage.",
            "",
            "Tip: Rotate your creature so spikes face the enemy.",
            "Your mouse aim controls which direction you face.",
        ],
        "trigger": "always",
        "highlight": None,
    },
    {
        "id": "combat_abilities",
        "title": "Combat Basics: Abilities",
        "lines": [
            "Press SPACE to trigger active abilities:",
            "  Zapper = electric pulse around you",
            "  Explosive = big blast (damages YOU too!)",
            "  Acid = spray that melts over time",
            "",
            "Abilities have cooldowns — use them wisely.",
        ],
        "trigger": "always",
        "highlight": None,
    },
    {
        "id": "combat_defense",
        "title": "Combat Basics: Defense",
        "lines": [
            "Shield cells absorb damage.",
            "Place them on the OUTSIDE of your build,",
            "facing the direction enemies attack from.",
            "",
            "Your Heart cell is in the CENTER — protect it!",
            "If your heart dies, you die.",
        ],
        "trigger": "always",
        "highlight": "heart",
    },
    {
        "id": "combat_positioning",
        "title": "Combat Basics: Positioning",
        "lines": [
            "Don't just charge in blindly.",
            "Circle around enemies, hit their weak spots.",
            "",
            "Armored Brutes have shields on front — hit their back.",
            "Hunters are fast — kite them and strike when they turn.",
            "Psychic Weavers attack from range — close the gap fast.",
        ],
        "trigger": "always",
        "highlight": None,
    },
    {
        "id": "combat_retreat",
        "title": "Combat Basics: Know When to Retreat",
        "lines": [
            "If you're losing cells, RETREAT to a SAFE ZONE.",
            "Safe zones heal you faster and enemies won't follow.",
            "",
            "Lost cells can be replaced by picking up cell drops.",
            "Don't fight to the death — live to fight another day.",
        ],
        "trigger": "always",
        "highlight": None,
    },
    {
        "id": "combat_done",
        "title": "Combat Tutorial Complete",
        "lines": [
            "You're ready to fight.",
            "",
            "Remember:",
            "  • Position your spikes toward enemies",
            "  • Use abilities at the right moment",
            "  • Protect your heart",
            "  • Retreat when needed",
            "",
            "Good luck out there.",
        ],
        "trigger": "always",
        "highlight": None,
    },
    {
        "id": "miniboss_offer",
        "title": "Mini Boss Challenge",
        "lines": [
            "Want to test your skills against a MINI BOSS?",
            "",
            "This is a tough enemy — cracked as hell.",
            "It'll push you to your limits.",
            "",
            "Press NEXT to fight the mini boss.",
            "Press SKIP to start the game normally.",
        ],
        "trigger": "always",
        "highlight": None,
        "is_miniboss_offer": True,
    },
]


class Tutorial:
    def __init__(self, sw, sh):
        self.sw, self.sh = sw, sh
        self.step = 0
        self.active = True
        self.font_title = pygame.font.SysFont("consolas", 22, bold=True)
        self.font_body  = pygame.font.SysFont("consolas", 15)
        self.font_small = pygame.font.SysFont("consolas", 12)
        self.dismissed  = False
        self.spawn_miniboss = False  # Flag for mini boss battle

        from ui.menus import Button
        self.next_btn = Button((sw//2 + 60, sh - 130, 110, 36), "NEXT  ▶", (255, 220, 0))
        self.skip_btn = Button((sw//2 - 180, sh - 130, 110, 36), "SKIP ALL", (255, 100, 60))

    @property
    def current(self):
        if self.step < len(TUTORIAL_STEPS):
            return TUTORIAL_STEPS[self.step]
        return None

    def advance(self):
        # Check if this is the miniboss offer step
        if self.current and self.current.get("is_miniboss_offer"):
            self.spawn_miniboss = True
        
        self.step += 1
        if self.step >= len(TUTORIAL_STEPS):
            self.dismissed = True
            self.active = False

    def skip(self):
        self.dismissed = True
        self.active = False

    def handle_event(self, event):
        if not self.active:
            return
        if self.next_btn.handle_event(event):
            self.advance()
        if self.skip_btn.handle_event(event):
            self.skip()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self.advance()

    def draw(self, surface, game_time):
        if not self.active or self.dismissed:
            return
        step = self.current
        if not step:
            return

        # Dim overlay
        overlay = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        # Panel — bright yellow/gold background for contrast
        panel_w, panel_h = 560, 280
        px = self.sw // 2 - panel_w // 2
        py = self.sh - panel_h - 20

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((245, 220, 120, 250))  # Bright gold/yellow background
        surface.blit(panel, (px, py))

        # Glowing border — brighter, more visible
        pulse = pulse_value(game_time, speed=1.2, lo=0.7, hi=1.0)
        border_c = tuple(int(v * pulse) for v in (255, 220, 0))  # Gold instead of cyan
        pygame.draw.rect(surface, border_c, (px, py, panel_w, panel_h), width=3, border_radius=8)
        draw_glow_rect(surface, (255, 220, 0), pygame.Rect(px, py, panel_w, panel_h), alpha=30)

        # Step counter — dark text
        counter = self.font_small.render(
            f"Step {self.step + 1} / {len(TUTORIAL_STEPS)}", True, (60, 50, 40))
        surface.blit(counter, (px + panel_w - counter.get_width() - 12, py + 10))

        # Title — black for contrast
        title = self.font_title.render(step["title"], True, (20, 20, 20))
        surface.blit(title, (px + 20, py + 14))

        # Divider — darker for visibility
        pygame.draw.line(surface, (100, 80, 40), (px + 16, py + 42), (px + panel_w - 16, py + 42), width=2)

        # Body lines — black text for better contrast on gold panel
        for i, line in enumerate(step["lines"]):
            c = (20, 20, 20) if not line.startswith("  ") else (40, 40, 40)
            if line == "":
                continue
            t = self.font_body.render(line, True, c)
            surface.blit(t, (px + 20, py + 52 + i * 20))

        # Progress dots — gold
        dot_y = py + panel_h - 18
        total = len(TUTORIAL_STEPS)
        dot_start = self.sw // 2 - (total * 14) // 2
        for i in range(total):
            c = (255, 220, 0) if i == self.step else (60, 50, 40)
            r = 5 if i == self.step else 3
            pygame.draw.circle(surface, c, (dot_start + i * 14, dot_y), r)

        self.next_btn.draw(surface, game_time)
        self.skip_btn.draw(surface, game_time)
