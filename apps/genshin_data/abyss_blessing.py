import json
from typing import Any, Dict, List, Tuple, Union
from apps.text_map.convert_locale import to_enka
from discord import Locale
from utility.utils import parse_HTML

def get_abyss_blessing(text_map: Dict[str, Dict[str, str]], locale: Union[Locale, str]) -> Tuple[str, str]:
    with open("GenshinData/ExcelBinOutput/TowerScheduleExcelConfigData.json") as f:
        tower: List[Dict[str, Any]] = json.load(f)
    with open("GenshinData/ExcelBinOutput/DungeonLevelEntityConfigData.json") as f:
        dungeon: List[Dict[str, Any]] = json.load(f)
    
    lang = to_enka(locale).upper()
    
    last_buff = tower[-1]
    buff_id = last_buff["monthlyLevelConfigId"]
    buff_name = text_map[lang].get(str(last_buff["buffnameTextMapHash"]), "Unknown")
    
    buff_desc = "Unknown"
    for buff in dungeon:
        if buff["id"] == buff_id:
            buff_desc = parse_HTML(text_map[lang].get(str(buff["descTextMapHash"]), "Unknown"))
            break
    
    return buff_name, buff_desc