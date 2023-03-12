import json
from typing import Dict, List

with open("genshin-substat-lookup/rollTable.json", "r") as f:
    roll_table: Dict[str, Dict[str, Dict[str, List[List[float]]]]] = json.load(f)


def calculate_substat_roll(prop_id: str, value: float) -> int:
    for _, sub_stats in roll_table.items():
        for p_id, table in sub_stats.items():
            if p_id == prop_id:
                for sub_stat_value, possible_rolls in table.items():
                    if float(sub_stat_value.replace(", ", "")) == value:
                        for possible_roll in possible_rolls:
                            return len(possible_roll)

    return 0
