import json
from typing import Dict, List

with open("data/game/rollTable.json", "r") as f:
    roll_table: Dict[str, Dict[str, Dict[str, List[List[float]]]]] = json.load(f)


def calculate_substat_roll(prop_id: str, value: float, rarity: int) -> int:
    try:
        possible_rolls = roll_table[str(rarity)][prop_id][str(value)]
        return len(possible_rolls[0])
    except KeyError:
        return 0
