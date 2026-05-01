import json
import os

SAVE_DIR = "saves"
NUM_SLOTS = 5

def _path(slot):
    return os.path.join(SAVE_DIR, f"strain_{slot}.json")

def load_slot(slot):
    p = _path(slot)
    if not os.path.exists(p):
        return None
    with open(p, "r") as f:
        return json.load(f)

def save_slot(slot, data):
    os.makedirs(SAVE_DIR, exist_ok=True)
    with open(_path(slot), "w") as f:
        json.dump(data, f, indent=2)

def delete_slot(slot):
    p = _path(slot)
    if os.path.exists(p):
        os.remove(p)

def load_all_slots():
    return [load_slot(i) for i in range(NUM_SLOTS)]

def default_strain(slot_index, race_name):
    return {
        "slot": slot_index,
        "race": race_name,
        "name": f"Strain {slot_index + 1}",
        "level": 1,
        "xp": 0,
        "cells": ["heart", "basic", "basic", "basic"],  # starting layout
        "cell_layout": {},  # {hex_coord: cell_type}
        "unlocked_cells": ["basic", "heart", "seeker", "spike"],
        "current_biome": "membrane",
        "stats": {
            "enemies_killed": 0,
            "bosses_killed": 0,
            "cells_lost": 0,
            "absorbed_types": [],
            "biomes_explored": [],
            "skrix_shed": 0,
            "nullborn_phases": 0,
            "synergies_triggered": 0,
            "xenarch_defeated": False,
        },
        "achievements": [],
        "scale": 1.0,
    }

def load_global_achievements():
    p = os.path.join(SAVE_DIR, "achievements.json")
    if not os.path.exists(p):
        return {}
    with open(p, "r") as f:
        return json.load(f)

def save_global_achievements(data):
    os.makedirs(SAVE_DIR, exist_ok=True)
    with open(os.path.join(SAVE_DIR, "achievements.json"), "w") as f:
        json.dump(data, f, indent=2)
