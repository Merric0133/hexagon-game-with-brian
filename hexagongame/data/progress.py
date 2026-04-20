import json
import os
from constants import DATA_DIR

PROGRESS_FILE = os.path.join(DATA_DIR, "progress.json")
HIGHSCORES_FILE = os.path.join(DATA_DIR, "highscores.json")

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    return {"highest_wave": 0, "unlocked_skins": ["default"], "selected_skin": "default"}

def save_progress(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(PROGRESS_FILE, "w") as f:
        json.dump(data, f)

def get_selected_skin():
    return load_progress().get("selected_skin", "default")

def set_selected_skin(skin_id):
    data = load_progress()
    data["selected_skin"] = skin_id
    save_progress(data)

def record_wave(wave_num):
    data = load_progress()
    data["highest_wave"] = max(data.get("highest_wave", 0), wave_num)
    save_progress(data)

def load_highscores():
    if os.path.exists(HIGHSCORES_FILE):
        with open(HIGHSCORES_FILE, "r") as f:
            return json.load(f)
    return []

def save_highscore(name, wave, score):
    scores = load_highscores()
    scores.append({"name": name, "wave": wave, "score": score})
    scores.sort(key=lambda x: x["score"], reverse=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(HIGHSCORES_FILE, "w") as f:
        json.dump(scores[:10], f)