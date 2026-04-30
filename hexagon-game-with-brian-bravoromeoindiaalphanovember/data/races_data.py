RACES = {
    "Vorrkai": {
        "display": "Vorrkai",
        "subtitle": "The Armored Brutes",
        "desc": "Slow and tanky. Cells have 30% more HP. On heavy damage, outer cells temporarily calcify.",
        "color": (180, 40, 20),
        "glow": (255, 80, 40),
        "passive": "cell_hp_bonus",
        "passive_value": 0.30,
        "trait": "calcify",
        "trait_desc": "On taking 30%+ HP in one hit, outer cells harden for 3s (50% damage reduction).",
        "stat_mods": {"speed": -0.15, "mass": 1.3},
        "unlock_level": 0,
        # Movement style
        "movement_style": "heavy_tank",
        "body_shape": "compact_round",  # Round, dense cluster
        "default_layout": {
            (0,0): "heart", 
            (-1,0): "hard", (1,0): "hard",
            (0,-1): "hard", (0,1): "hard",
            (-1,-1): "basic", (1,-1): "basic",
            (-1,1): "basic", (1,1): "basic",
        },
        "damping": 0.75,  # High damping = slow stop
        "turn_speed": 6.0,
    },
    "Lumenid": {
        "display": "Lumenid",
        "subtitle": "The Light Weavers",
        "desc": "Fragile but powerful. Electric and energy cells deal 25% more damage. Ability triggers release a blinding flash.",
        "color": (180, 220, 255),
        "glow": (100, 200, 255),
        "passive": "energy_damage_bonus",
        "passive_value": 0.25,
        "trait": "photon_burst",
        "trait_desc": "Ability triggers release a flash that blinds nearby enemies for 1.5s.",
        "stat_mods": {"speed": 0.10, "hp_mult": 0.85},
        "unlock_level": 0,
        # Movement style
        "movement_style": "darting",
        "body_shape": "diamond",  # Diamond shape, quick turns
        "default_layout": {
            (0,0): "heart",
            (0,-1): "speedy", (0,1): "speedy",
            (-1,0): "basic", (1,0): "basic",
            (0,-2): "seeker",
        },
        "damping": 0.88,
        "turn_speed": 12.0,
    },
    "Skrix": {
        "display": "Skrix",
        "subtitle": "The Swarm Born",
        "desc": "Glass cannon. Lost cells spawn tiny minions. Can voluntarily shed cells to create distractions.",
        "color": (80, 200, 40),
        "glow": (120, 255, 60),
        "passive": "cell_shed_minion",
        "passive_value": 1,
        "trait": "fission",
        "trait_desc": "Press ability to voluntarily shed outer cells as minion distractions.",
        "stat_mods": {"speed": 0.20, "hp_mult": 0.75},
        "unlock_level": 1,
        # Movement style
        "movement_style": "erratic_swarm",
        "body_shape": "branching",  # Multiple tendrils
        "default_layout": {
            (0,0): "heart",
            (-1,0): "basic", (1,0): "basic",
            (-2,0): "basic", (2,0): "basic",
            (0,-1): "basic", (0,1): "basic",
        },
        "damping": 0.90,
        "turn_speed": 14.0,
    },
    "Myrrhon": {
        "display": "Myrrhon",
        "subtitle": "The Symbiotes",
        "desc": "Adaptive. Absorbed enemy cells gain +15% stats. Can assimilate one enemy cell type per zone.",
        "color": (160, 60, 255),
        "glow": (200, 120, 255),
        "passive": "absorbed_cell_bonus",
        "passive_value": 0.15,
        "trait": "assimilate",
        "trait_desc": "Defeat an enemy below 20% HP to absorb their cell type permanently.",
        "stat_mods": {"speed": 0.0, "hp_mult": 1.0},
        "unlock_level": 2,
        # Movement style
        "movement_style": "flowing",
        "body_shape": "blob",  # Amorphous, shifts shape
        "default_layout": {
            (0,0): "heart",
            (-1,0): "basic", (1,0): "basic",
            (0,-1): "basic", (0,1): "basic",
            (-1,-1): "seeker", (1,1): "seeker",
        },
        "damping": 0.85,
        "turn_speed": 9.0,
    },
    "Nullborn": {
        "display": "Nullborn",
        "subtitle": "The Voidwalkers",
        "desc": "Immune to biome negative modifiers. Brief intangibility on ability trigger.",
        "color": (30, 10, 60),
        "glow": (120, 60, 200),
        "passive": "biome_immunity",
        "passive_value": 1,
        "trait": "phase",
        "trait_desc": "Ability trigger makes you intangible for 0.8s. 6s cooldown.",
        "stat_mods": {"speed": 0.05, "hp_mult": 0.90},
        "unlock_level": 3,
        # Movement style
        "movement_style": "slithering_snake",
        "body_shape": "long_snake",  # Long thin snake
        "default_layout": {
            (0,0): "heart",
            (0,-1): "seeker", (0,-2): "speedy",
            (0,1): "basic", (0,2): "basic", (0,3): "basic",
        },
        "damping": 0.92,  # Very responsive
        "turn_speed": 16.0,
    },
}
