"""
data/progress.py — Persists player progress, inventory, and skin choice.
"""
import json
import os
from constants import CellType, STARTING_INVENTORY

SAVE_FILE = os.path.join("data", "progress.json")


# ── Serialisation helpers ─────────────────────────────────────────────────────

def _inv_to_json(inv: dict) -> dict:
    """CellType keys → string keys for JSON."""
    return {ct.name: count for ct, count in inv.items()}

def _inv_from_json(raw: dict) -> dict:
    """String keys → CellType keys."""
    result = {}
    for name, count in raw.items():
        try:
            result[CellType[name]] = count
        except KeyError:
            pass
    return result


# ── Load / save ───────────────────────────────────────────────────────────────

def _default_progress() -> dict:
    return {
        "highest_wave":    0,
        "high_score":      0,
        "selected_skin":   "default",
        "inventory":       _inv_to_json(STARTING_INVENTORY),
        "equipped":        [],   # list of CellType names, length == HEX_SIDES
        "honeycomb_body":  [],   # list[{"q": int, "r": int, "type": str}]
    }

def load_progress() -> dict:
    if not os.path.exists(SAVE_FILE):
        return _default_progress()
    try:
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)
        # Back-fill any missing keys
        defaults = _default_progress()
        for k, v in defaults.items():
            data.setdefault(k, v)
        return data
    except Exception:
        return _default_progress()

def save_progress(data: dict):
    os.makedirs(os.path.dirname(SAVE_FILE), exist_ok=True)
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


# ── Convenience accessors ─────────────────────────────────────────────────────

def get_selected_skin() -> str:
    return load_progress().get("selected_skin", "default")

def set_selected_skin(skin_id: str):
    p = load_progress()
    p["selected_skin"] = skin_id
    save_progress(p)

def record_wave(wave: int):
    p = load_progress()
    if wave > p.get("highest_wave", 0):
        p["highest_wave"] = wave
    save_progress(p)

def save_highscore(score: int):
    p = load_progress()
    if score > p.get("high_score", 0):
        p["high_score"] = score
    save_progress(p)

def get_inventory() -> dict:
    """Returns {CellType: count} dict."""
    p = load_progress()
    raw = p.get("inventory", _inv_to_json(STARTING_INVENTORY))
    result = _inv_from_json(raw)
    # Ensure all cell types present
    for ct in CellType:
        if ct != CellType.EMPTY:
            result.setdefault(ct, 0)
    return result

def save_inventory(inv: dict):
    p = load_progress()
    p["inventory"] = _inv_to_json(inv)
    save_progress(p)

def add_to_inventory(cell_type: CellType, count: int = 1):
    inv = get_inventory()
    inv[cell_type] = inv.get(cell_type, 0) + count
    save_inventory(inv)

def get_equipped_layout() -> list:
    """Returns list of CellType (length HEX_SIDES), EMPTY for blank slots."""
    from constants import HEX_SIDES
    p = load_progress()
    raw = p.get("equipped", [])
    layout = []
    for name in raw:
        try:
            layout.append(CellType[name])
        except KeyError:
            layout.append(CellType.EMPTY)
    # Pad to HEX_SIDES
    while len(layout) < HEX_SIDES:
        layout.append(CellType.EMPTY)
    return layout[:HEX_SIDES]

def save_equipped_layout(layout: list):
    """layout = list of CellType, length HEX_SIDES."""
    p = load_progress()
    p["equipped"] = [ct.name for ct in layout]
    save_progress(p)


def get_honeycomb_body() -> list[dict]:
    """
    Returns list of {"q": int, "r": int, "type": CellType} entries.
    Falls back to legacy 6-slot equipped layout if no honeycomb data exists.
    """
    p = load_progress()
    raw = p.get("honeycomb_body", [])
    body = []
    for item in raw:
        try:
            q = int(item["q"])
            r = int(item["r"])
            ct = CellType[item["type"]]
            if ct != CellType.EMPTY:
                body.append({"q": q, "r": r, "type": ct})
        except Exception:
            continue
    if body:
        return body

    # Legacy fallback: map 6-slot ring around core into axial coordinates.
    ring = [(1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)]
    layout = get_equipped_layout()
    converted = []
    for i, ct in enumerate(layout):
        if ct != CellType.EMPTY:
            q, r = ring[i]
            converted.append({"q": q, "r": r, "type": ct})
    return converted


def save_honeycomb_body(body: list[dict]):
    """
    Save a honeycomb layout.
    Input entries should be {"q": int, "r": int, "type": CellType}.
    """
    p = load_progress()
    packed = []
    for item in body:
        ct = item.get("type")
        if ct is None or ct == CellType.EMPTY:
            continue
        packed.append({
            "q": int(item["q"]),
            "r": int(item["r"]),
            "type": ct.name if isinstance(ct, CellType) else str(ct),
        })
    p["honeycomb_body"] = packed
    save_progress(p)
