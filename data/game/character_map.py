import json

try:
    with open("data/game/character_map.json", encoding="utf-8", mode="r") as f:
        character_map = json.load(f)
except FileNotFoundError:
    character_map = {}