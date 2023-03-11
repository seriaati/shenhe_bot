import json
import os
from typing import Dict


def load_text_maps() -> Dict[str, Dict[str, str]]:
    result: Dict[str, Dict[str, str]] = {}

    json_files = [
        j_file
        for j_file in os.listdir("GenshinData/TextMap")
        if j_file.endswith(".json")
    ]
    for json_file in json_files:
        with open(f"GenshinData/TextMap/{json_file}") as f:
            data: Dict[str, str] = json.load(f)
        result[json_file.split("TextMap")[-1].replace(".json", "")] = data

    return result
