import json

try:
    with open("data/game/artifact_map.json", encoding="utf-8", mode="r") as f:
        artifact_map = json.load(f)
except FileNotFoundError:
    artifact_map = {}
