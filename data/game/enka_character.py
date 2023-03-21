import json
from typing import Any, Dict

with open("data/game/enka_character.json") as f:
    enka_characters: Dict[str, Any] = json.load(f)


def get_enka_characters():
    return enka_characters
