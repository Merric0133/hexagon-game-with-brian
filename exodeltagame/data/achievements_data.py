ACHIEVEMENTS = {
    # Progression
    "first_contact": {
        "name": "First Contact",
        "desc": "Defeat your first enemy.",
        "icon_color": (0, 255, 180),
        "condition": "enemies_killed >= 1",
        "secret": False,
    },
    "critical_mass": {
        "name": "Critical Mass",
        "desc": "Reach 10 cells on your body.",
        "icon_color": (0, 200, 255),
        "condition": "cell_count >= 10",
        "secret": False,
    },
    "titan_rising": {
        "name": "Titan Rising",
        "desc": "Grow to 5x your starting size.",
        "icon_color": (255, 180, 0),
        "condition": "scale >= 5",
        "secret": False,
    },
    "world_ender": {
        "name": "World Ender",
        "desc": "Defeat XENARCH.",
        "icon_color": (255, 50, 0),
        "condition": "xenarch_defeated",
        "secret": False,
    },
    # Build creativity
    "synergist": {
        "name": "Synergist",
        "desc": "Trigger your first cell synergy.",
        "icon_color": (180, 0, 255),
        "condition": "synergies_triggered >= 1",
        "secret": False,
    },
    "mad_scientist": {
        "name": "Mad Scientist",
        "desc": "Have 3 different synergies active at once.",
        "icon_color": (255, 0, 180),
        "condition": "active_synergies >= 3",
        "secret": False,
    },
    "the_absorber": {
        "name": "The Absorber",
        "desc": "Absorb 5 different enemy types (Myrrhon).",
        "icon_color": (160, 60, 255),
        "condition": "absorbed_types >= 5",
        "secret": False,
    },
    "architect": {
        "name": "Architect",
        "desc": "Save a build in all 5 strain slots.",
        "icon_color": (0, 255, 100),
        "condition": "filled_slots >= 5",
        "secret": False,
    },
    # Combat
    "untouchable": {
        "name": "Untouchable",
        "desc": "Defeat a boss without losing a single cell.",
        "icon_color": (255, 220, 0),
        "condition": "boss_no_cell_loss",
        "secret": True,
    },
    "fission_reactor": {
        "name": "Fission Reactor",
        "desc": "Shed 50 cells total as Skrix.",
        "icon_color": (80, 255, 40),
        "condition": "skrix_shed >= 50",
        "secret": False,
    },
    "void_walker": {
        "name": "Void Walker",
        "desc": "Phase through 100 attacks as Nullborn.",
        "icon_color": (120, 60, 200),
        "condition": "nullborn_phases >= 100",
        "secret": False,
    },
    # Exploration
    "deep_diver": {
        "name": "Deep Diver",
        "desc": "Reach The Void Stomach.",
        "icon_color": (0, 180, 120),
        "condition": "biome_reached == void_stomach",
        "secret": False,
    },
    "cartographer": {
        "name": "Cartographer",
        "desc": "Fully explore 3 biomes.",
        "icon_color": (0, 220, 200),
        "condition": "biomes_explored >= 3",
        "secret": False,
    },
    "mimic_slayer": {
        "name": "Mimic Slayer",
        "desc": "Defeat a Mimic that copied your exact build.",
        "icon_color": (255, 100, 200),
        "condition": "mimic_killed",
        "secret": True,
    },
}
