BIOMES = {
    "membrane": {
        "name": "The Membrane",
        "desc": "Soft glowing tissue. The surface layer of Xenova. Weak organisms dwell here.",
        "bg_color": (35, 15, 10),  # Warm reddish-brown
        "accent": (255, 80, 40),
        "glow": (255, 120, 60),
        "particle_color": (140, 70, 45),   # desaturated orange-red
        "enemy_types": ["drifter", "hunter"],
        "modifier": None,
        "boss": "membrane_boss",
        "level_range": (1, 3),
        "visual_theme": "organic_tissue",
        "ambient_particles": "floating_cells",
    },
    "vein": {
        "name": "The Vein Network",
        "desc": "Pulsing bioluminescent corridors. Faster enemies lurk in the fluid.",
        "bg_color": (5, 20, 45),  # Deep blue
        "accent": (0, 180, 255),
        "glow": (0, 220, 255),
        "particle_color": (40, 100, 130),  # desaturated blue
        "enemy_types": ["drifter", "hunter", "armored_brute"],
        "modifier": {"type": "speed_boost", "desc": "All creatures move 20% faster.", "value": 1.2},
        "boss": "vein_boss",
        "level_range": (3, 6),
        "visual_theme": "flowing_liquid",
        "ambient_particles": "bubbles",
    },
    "cortex": {
        "name": "The Cortex",
        "desc": "Crystalline alien brain matter. Enemies with psychic and electric abilities.",
        "bg_color": (15, 8, 35),  # Deep purple
        "accent": (160, 0, 255),
        "glow": (200, 80, 255),
        "particle_color": (90, 50, 120),   # desaturated purple
        "enemy_types": ["hunter", "armored_brute", "psychic_weaver", "hive_cluster"],
        "modifier": {"type": "electric_amp", "desc": "Electric cells deal 2x damage.", "value": 2.0},
        "boss": "cortex_boss",
        "level_range": (6, 9),
        "visual_theme": "crystalline",
        "ambient_particles": "sparks",
    },
    "void_stomach": {
        "name": "The Void Stomach",
        "desc": "Dark and acidic. Enemies dissolve your cells. No healing zones.",
        "bg_color": (8, 12, 5),  # Sickly green-black
        "accent": (0, 255, 120),
        "glow": (0, 200, 100),
        "particle_color": (30, 90, 55),    # desaturated green
        "enemy_types": ["armored_brute", "psychic_weaver", "hive_cluster", "mimic"],
        "modifier": {"type": "no_regen", "desc": "No passive healing. Acid damage over time.", "value": None},
        "boss": "void_boss",
        "level_range": (9, 12),
        "visual_theme": "acidic",
        "ambient_particles": "acid_drops",
    },
    "titan_core": {
        "name": "The Titan's Core",
        "desc": "The heart of XENARCH. Survive long enough to face the god-organism.",
        "bg_color": (25, 5, 5),  # Deep crimson
        "accent": (255, 50, 0),
        "glow": (255, 150, 0),
        "particle_color": (130, 55, 20),   # desaturated ember orange
        "enemy_types": ["hunter", "armored_brute", "mimic", "psychic_weaver"],
        "modifier": {"type": "all_damage_amp", "desc": "All damage increased by 50%.", "value": 1.5},
        "boss": "xenarch",
        "level_range": (12, 15),
        "visual_theme": "inferno",
        "ambient_particles": "embers",
    },
}
