import json
from typing import Any, Dict, List

from dev.enum import GenshinWikiCategory, HSRWikiCategory
from utils.general import open_json

ambr_maps: Dict[GenshinWikiCategory, Dict[str, Dict[str, str]]] = {}
for category in GenshinWikiCategory:
    ambr_maps[category] = open_json(f"data/genshin/text_maps/{category.value}.json")
item_name = open_json("text_maps/item_name.json")

LANGUAGES = (
    "ChineseSimplified",
    "ChineseTraditional",
    "English",
    "French",
    "German",
    "Indonesian",
    "Italian",
    "Japanese",
    "Korean",
    "Portuguese",
    "Russian",
    "Spanish",
    "Thai",
    "Turkish",
    "Vietnamese",
)

tcg_data: Dict[str, List[Dict[str, Any]]] = {}
for lang in LANGUAGES:
    try:
        with open(f"data/cards/card_data_{lang}.json", "r", encoding="utf-8") as f:
            tcg_data[lang] = json.loads(f.read())
    except FileNotFoundError:
        tcg_data[lang] = []

yatta_maps: Dict[HSRWikiCategory, Dict[str, Dict[str, str]]] = {}
for category in HSRWikiCategory:
    yatta_maps[category] = open_json(f"data/star_rail/text_maps/{category.value}.json")
