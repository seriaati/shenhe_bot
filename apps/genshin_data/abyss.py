import json
from typing import Any, Dict, List, Tuple, Union
from apps.genshin_data.utility import get_text
from discord import Locale
from dateutil import parser
from utility.utils import get_dt_now, parse_HTML, time_in_range


def get_abyss_blessing(
    text_map: Dict[str, Dict[str, str]], locale: Union[Locale, str]
) -> Tuple[str, str]:
    with open("GenshinData/ExcelBinOutput/TowerScheduleExcelConfigData.json") as f:
        tower: List[Dict[str, Any]] = json.load(f)
    with open("GenshinData/ExcelBinOutput/DungeonLevelEntityConfigData.json") as f:
        dungeon: List[Dict[str, Any]] = json.load(f)

    current_tower = get_current_tower(tower)

    buff_id = current_tower["monthlyLevelConfigId"]
    buff_name = get_text(text_map, locale, current_tower["buffnameTextMapHash"])

    buff_desc = "Unknown"
    dungeon_configs = find_dungeon_configs(dungeon, buff_id)
    if dungeon_configs:
        buff_desc = parse_HTML(get_text(text_map, locale, dungeon_configs[0]["descTextMapHash"]))

    return buff_name, buff_desc


def get_ley_line_disorders(
    text_map: Dict[str, Dict[str, str]], locale: Union[Locale, str]
) -> Dict[int, List[str]]:
    with open("GenshinData/ExcelBinOutput/TowerScheduleExcelConfigData.json") as f:
        tower: List[Dict[str, Any]] = json.load(f)
    with open("GenshinData/ExcelBinOutput/TowerFloorExcelConfigData.json") as f:
        floor: List[Dict[str, Any]] = json.load(f)
    with open("GenshinData/ExcelBinOutput/DungeonLevelEntityConfigData.json") as f:
        dungeon: List[Dict[str, Any]] = json.load(f)

    current_tower = get_current_tower(tower)

    result: Dict[int, List[str]] = {}
    num = 1
    floor_ids: List[int] = (
        current_tower["entranceFloorId"] + current_tower["schedules"][0]["floorList"]
    )
    for floor_id in floor_ids:
        result[num] = ["Unknown"]
        floor_excel = find_tower_floor(floor, floor_id)
        if floor_excel:
            result[num] = []
            config_id = floor_excel["floorLevelConfigId"]
            dungeon_configs = find_dungeon_configs(dungeon, config_id)
            for dungeon_config in dungeon_configs:
                disorder_desc = parse_HTML(
                    get_text(text_map, locale, dungeon_config["descTextMapHash"])
                )
                if disorder_desc != "Unknown":
                    result[num].append(disorder_desc)
        num += 1

    return result


def get_current_tower(tower: List[Dict[str, Any]]) -> Dict[str, Any]:
    tower.reverse()
    current_tower = tower[-1]
    for t in tower:
        open_time = t["schedules"][0]["openTime"]
        open_time = parser.parse(open_time)
        close_time = t["closeTime"]
        close_time = parser.parse(close_time)
        if time_in_range(open_time, close_time, get_dt_now()):
            current_tower = t
            break

    return current_tower


def find_tower_floor(floor: List[Dict[str, Any]], floor_id: int) -> Dict[str, Any]:
    for f in floor:
        if f["floorId"] == floor_id:
            return f
    return {}


def find_dungeon_configs(
    dungeon: List[Dict[str, Any]], config_id: int
) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for d in dungeon:
        if d["id"] == config_id:
            result.append(d)
    return result
