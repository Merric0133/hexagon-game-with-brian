# Cell definitions based on Primordialis balancing research:
# - Genome size is the HARD CAP on offensive cells (spike=12, zapper=12, explosive=9, acid=16)
# - Biomass cost limits total cells on body (heart=25, offensive=5-12, structural=1-3)
# - Heart cell is mandatory anchor — high cost, high storage
# - Structural cells are cheap and enable offensive cells to function
# - You NEED structural cells to survive — pure offense = fragile, dies fast

CELLS = {
    "basic": {
        "name": "Basic Cell",
        "desc": "Cheap filler. Connects your body together. No special purpose.",
        "cost": 1, "genome": 0, "hp": 20,
        "color": (80, 180, 120), "glow": (0, 255, 100),
        "category": "structural", "ability": None,
        "mass": 1.0, "radius": 18,
    },
    "heart": {
        "name": "Heart Cell",
        "desc": "Stores most of your biomass. Protect it at all costs — losing it is fatal.",
        "cost": 25, "genome": 0, "hp": 100,
        "color": (160, 40, 60), "glow": (200, 60, 80),
        "category": "structural", "ability": None,
        "mass": 2.0, "radius": 18,
        "note": "Always required. Cannot be removed from center.",
    },
    # Race-specific hearts
    "heart_vorrkai": {
        "name": "Vorrkai Heart",
        "desc": "Armored heart. 30% more HP. Tanky and resilient.",
        "cost": 25, "genome": 0, "hp": 130,
        "color": (200, 60, 20), "glow": (255, 100, 40),
        "category": "structural", "ability": None,
        "mass": 2.2, "radius": 18,
        "note": "Vorrkai exclusive.",
    },
    "heart_lumenid": {
        "name": "Lumenid Heart",
        "desc": "Luminous heart. Radiates energy. Boosts ability damage.",
        "cost": 25, "genome": 0, "hp": 85,
        "color": (100, 200, 255), "glow": (150, 220, 255),
        "category": "structural", "ability": None,
        "mass": 1.8, "radius": 18,
        "note": "Lumenid exclusive.",
    },
    "heart_skrix": {
        "name": "Skrix Heart",
        "desc": "Volatile heart. Sheds cells to spawn minions.",
        "cost": 25, "genome": 0, "hp": 75,
        "color": (100, 220, 60), "glow": (150, 255, 100),
        "category": "structural", "ability": None,
        "mass": 1.6, "radius": 18,
        "note": "Skrix exclusive.",
    },
    "heart_myrrhon": {
        "name": "Myrrhon Heart",
        "desc": "Adaptive heart. Absorbs enemy cells for bonuses.",
        "cost": 25, "genome": 0, "hp": 100,
        "color": (180, 80, 255), "glow": (220, 140, 255),
        "category": "structural", "ability": None,
        "mass": 2.0, "radius": 18,
        "note": "Myrrhon exclusive.",
    },
    "heart_nullborn": {
        "name": "Nullborn Heart",
        "desc": "Void heart. Phases through attacks.",
        "cost": 25, "genome": 0, "hp": 90,
        "color": (60, 20, 100), "glow": (150, 80, 220),
        "category": "structural", "ability": None,
        "mass": 1.9, "radius": 18,
        "note": "Nullborn exclusive.",
    },
    "hard": {
        "name": "Hard Cell",
        "desc": "Rigid and tough. High drag but great protection for inner cells.",
        "cost": 3, "genome": 4, "hp": 55,
        "color": (100, 120, 160), "glow": (140, 170, 220),
        "category": "structural", "ability": None,
        "mass": 2.0, "radius": 18,
    },
    "speedy": {
        "name": "Speedy Cell",
        "desc": "Moves fast. Costs genome but gives a real speed boost.",
        "cost": 3, "genome": 4, "hp": 20,
        "color": (0, 200, 180), "glow": (0, 255, 220),
        "category": "structural", "ability": None,
        "mass": 0.7, "radius": 18, "speed_bonus": 1.4,
    },
    "seeker": {
        "name": "Seeker Cell",
        "desc": "Attracted to your cursor. Improves steering precision.",
        "cost": 5, "genome": 1, "hp": 15,
        "color": (0, 220, 255), "glow": (0, 255, 255),
        "category": "structural", "ability": None,
        "mass": 0.5, "radius": 18,
    },
    "vascular": {
        "name": "Vascular Cell",
        "desc": "High biomass storage. Acts as a secondary health pool.",
        "cost": 5, "genome": 2, "hp": 50,
        "color": (200, 60, 100), "glow": (255, 80, 130),
        "category": "structural", "ability": None,
        "mass": 1.2, "radius": 18,
    },
    # --- OFFENSIVE (high genome cost — can't spam these) ---
    "spike": {
        "name": "Spike Cell",
        "desc": "Deals damage on collision. Ram enemies with it. Heavy and slow.",
        "cost": 5, "genome": 12, "hp": 25,
        "color": (200, 160, 0), "glow": (255, 220, 0),
        "category": "offense", "ability": None,
        "mass": 2.5, "radius": 18, "damage": 22,
        "note": "High genome cost — you can only fit 1-2 per build early on.",
    },
    "zapper": {
        "name": "Zapper Cell",
        "desc": "Releases an electric pulse on SPACE. Needs structural cells to survive.",
        "cost": 7, "genome": 12, "hp": 18,
        "color": (100, 0, 255), "glow": (180, 80, 255),
        "category": "offense", "ability": "zap",
        "mass": 1.0, "radius": 18, "damage": 28, "zap_range": 130,
        "note": "Fragile. Wrap in basic/hard cells or it dies instantly.",
    },
    "explosive": {
        "name": "Explosive Cell",
        "desc": "Explodes on SPACE or on death. Damages YOU if too close.",
        "cost": 5, "genome": 9, "hp": 15,
        "color": (255, 60, 0), "glow": (255, 120, 0),
        "category": "offense", "ability": "explode",
        "mass": 1.0, "radius": 18, "damage": 65, "blast_radius": 160,
        "note": "Self-damage risk. Place on outer edge, not near heart.",
    },
    "acid": {
        "name": "Acid Cell",
        "desc": "Spews acid on SPACE. Melts enemy cells over time. Very high genome cost.",
        "cost": 12, "genome": 16, "hp": 18,
        "color": (120, 255, 0), "glow": (180, 255, 0),
        "category": "offense", "ability": "acid_spray",
        "mass": 1.0, "radius": 18, "damage": 10, "dot_duration": 3.5,
        "note": "Most expensive cell. One per build max early game.",
    },
    "leech": {
        "name": "Leech Cell",
        "desc": "Heals you proportional to damage dealt. Needs offense cells to work.",
        "cost": 6, "genome": 4, "hp": 20,
        "color": (180, 0, 120), "glow": (255, 0, 180),
        "category": "offense", "ability": None,
        "mass": 1.0, "radius": 18, "heal_ratio": 0.3,
        "note": "Useless alone. Pair with spike or zapper.",
    },
    # --- DEFENSIVE ---
    "shield": {
        "name": "Shield Cell",
        "desc": "Absorbs damage. Tough outer armor. Slows you slightly.",
        "cost": 4, "genome": 1, "hp": 65,
        "color": (40, 100, 220), "glow": (80, 160, 255),
        "category": "defense", "ability": None,
        "mass": 2.5, "radius": 18,
    },
    "anchor": {
        "name": "Anchor Cell",
        "desc": "Extremely heavy. Hard to push around. Slows movement significantly.",
        "cost": 8, "genome": 6, "hp": 50,
        "color": (60, 60, 80), "glow": (100, 100, 140),
        "category": "defense", "ability": None,
        "mass": 8.0, "radius": 18,
        "note": "Pairs with thruster for Pulse Dash synergy.",
    },
    "bouncer": {
        "name": "Bouncer Cell",
        "desc": "Reflects knockback back at enemies. Satisfying to use.",
        "cost": 5, "genome": 2, "hp": 35,
        "color": (0, 200, 200), "glow": (0, 255, 255),
        "category": "defense", "ability": None,
        "mass": 1.5, "radius": 18, "reflect_mult": 1.8,
    },
    # --- UTILITY ---
    "thruster": {
        "name": "Thruster Cell",
        "desc": "Boosts speed in the direction it faces. Pairs with anchor for Pulse Dash.",
        "cost": 3, "genome": 1, "hp": 20,
        "color": (255, 100, 0), "glow": (255, 160, 0),
        "category": "utility", "ability": "boost",
        "mass": 0.8, "radius": 18, "boost_force": 500,
    },
    # --- SPECIAL ---
    "symbiont": {
        "name": "Symbiont Cell",
        "desc": "Absorbed from a defeated enemy. Carries their unique ability.",
        "cost": 0, "genome": 3, "hp": 30,
        "color": (200, 100, 255), "glow": (220, 150, 255),
        "category": "special", "ability": "symbiont_passive",
        "mass": 1.2, "radius": 18,
    },
}

# --- BALANCING RULES enforced in the editor ---
MAX_GENOME = 40          # Starting genome cap (grows with level)
MAX_BIOMASS_COST = 60    # Starting biomass cap (grows with level)
MIN_HEART_CELLS = 1      # Must always have at least 1 heart
MAX_OFFENSE_RATIO = 0.6  # Offense cells can't exceed 60% of total cells

def get_genome_cap(level):
    """Genome cap scales with level — more options as you grow."""
    return MAX_GENOME + (level - 1) * 8

def get_biomass_cap(level):
    """Biomass cap scales with level."""
    return MAX_BIOMASS_COST + (level - 1) * 10

def validate_layout(layout, level=1):
    """
    Returns (is_valid, list_of_errors).
    Enforces balancing rules so players can't just dump all offense.
    """
    errors = []
    if not layout:
        errors.append("Build is empty.")
        return False, errors

    cell_types = list(layout.values())
    total_genome = sum(CELLS.get(ct, CELLS["basic"])["genome"] for ct in cell_types)
    total_cost   = sum(CELLS.get(ct, CELLS["basic"])["cost"]   for ct in cell_types)
    heart_count  = cell_types.count("heart")
    offense_count = sum(1 for ct in cell_types if CELLS.get(ct, {}).get("category") == "offense")
    total_count  = len(cell_types)

    genome_cap   = get_genome_cap(level)
    biomass_cap  = get_biomass_cap(level)

    if heart_count < MIN_HEART_CELLS:
        errors.append("Need at least 1 Heart Cell — it's your lifeline.")
    if total_genome > genome_cap:
        errors.append(f"Genome overloaded! {total_genome}/{genome_cap}. Remove heavy cells.")
    if total_cost > biomass_cap:
        errors.append(f"Biomass cost too high! {total_cost}/{biomass_cap}. Simplify your build.")
    if total_count > 1 and offense_count / total_count > MAX_OFFENSE_RATIO:
        errors.append(f"Too many offense cells ({offense_count}/{total_count}). Add structural/defense cells.")

    return len(errors) == 0, errors


# Synergy definitions
SYNERGIES = [
    {
        "name": "Frenzy",
        "desc": "3+ Spike cells: passive AoE vibration damage around you.",
        "effect": "frenzy_aoe",
        "min_count": 3,
        "cell_type": "spike",
        "required_cells": None,
    },
    {
        "name": "Vampiric Shock",
        "desc": "Zapper + Leech: electric hits restore biomass.",
        "effect": "vampiric_shock",
        "min_count": 1,
        "cell_type": None,
        "required_cells": {"zapper", "leech"},
    },
    {
        "name": "Pulse Dash",
        "desc": "Thruster + Anchor: charges up then bursts forward.",
        "effect": "pulse_dash",
        "min_count": 1,
        "cell_type": None,
        "required_cells": {"thruster", "anchor"},
    },
    {
        "name": "Fortress",
        "desc": "3+ Shield cells: all incoming damage reduced by 40%.",
        "effect": "fortress",
        "min_count": 3,
        "cell_type": "shield",
        "required_cells": None,
    },
    {
        "name": "Toxic Feast",
        "desc": "Acid + Leech: acid damage also heals you.",
        "effect": "toxic_feast",
        "min_count": 1,
        "cell_type": None,
        "required_cells": {"acid", "leech"},
    },
]
