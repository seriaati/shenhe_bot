import json

try:
    with open("data/game/weapon_map.json", encoding="utf-8", mode="r") as f:
        weapon_map = json.load(f)
except FileNotFoundError:
    weapon_map = {}