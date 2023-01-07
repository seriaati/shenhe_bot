import json
from typing import Any, Dict, List, Tuple, Union

import aiofiles
from dateutil import parser
from discord import Locale

from apps.genshin.custom_model import AbyssChamber, AbyssFloor, AbyssHalf
from apps.genshin_data.utility import get_text
from utility.utils import get_dt_now, parse_HTML, time_in_range


async def get_abyss_blessing(
    text_map: Dict[str, Dict[str, str]], locale: Union[Locale, str]
) -> Tuple[str, str]:
    async with aiofiles.open(
        "GenshinData/ExcelBinOutput/TowerScheduleExcelConfigData.json"
    ) as f:
        tower: List[Dict[str, Any]] = json.loads(await f.read())
    async with aiofiles.open(
        "GenshinData/ExcelBinOutput/DungeonLevelEntityConfigData.json"
    ) as f:
        dungeon: List[Dict[str, Any]] = json.loads(await f.read())

    current_tower = get_current_tower(tower)

    buff_id = current_tower["monthlyLevelConfigId"]
    buff_name = get_text(text_map, locale, current_tower["buffnameTextMapHash"])

    buff_desc = "Unknown"
    dungeon_configs = find_dungeon_configs(dungeon, buff_id)
    if dungeon_configs:
        buff_desc = parse_HTML(
            get_text(text_map, locale, dungeon_configs[0]["descTextMapHash"])
        )

    return buff_name, buff_desc


async def get_ley_line_disorders(
    text_map: Dict[str, Dict[str, str]], locale: Union[Locale, str]
) -> Dict[int, List[str]]:
    async with aiofiles.open(
        "GenshinData/ExcelBinOutput/TowerScheduleExcelConfigData.json"
    ) as f:
        tower: List[Dict[str, Any]] = json.loads(await f.read())
    async with aiofiles.open(
        "GenshinData/ExcelBinOutput/TowerFloorExcelConfigData.json"
    ) as f:
        floor: List[Dict[str, Any]] = json.loads(await f.read())
    async with aiofiles.open(
        "GenshinData/ExcelBinOutput/DungeonLevelEntityConfigData.json"
    ) as f:
        dungeon: List[Dict[str, Any]] = json.loads(await f.read())

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


async def get_abyss_enemies(
    text_map: Dict[str, Dict[str, str]], locale: Union[Locale, str]
) -> List[AbyssFloor]:
    result: List[AbyssFloor] = []

    async with aiofiles.open(
        "GenshinData/ExcelBinOutput/TowerScheduleExcelConfigData.json"
    ) as f:
        tower_schedule: List[Dict[str, Any]] = json.loads(await f.read())
    async with aiofiles.open(
        "GenshinData/ExcelBinOutput/TowerFloorExcelConfigData.json"
    ) as f:
        tower_floor: List[Dict[str, Any]] = json.loads(await f.read())
    async with aiofiles.open(
        "GenshinData/ExcelBinOutput/TowerLevelExcelConfigData.json"
    ) as f:
        tower_level: List[Dict[str, Any]] = json.loads(await f.read())
    async with aiofiles.open(
        "GenshinData/ExcelBinOutput/MonsterDescribeExcelConfigData.json"
    ) as f:
        monster_describe: List[Dict[str, Any]] = json.loads(await f.read())

    current_tower = get_current_tower(tower_schedule)

    corridor = current_tower["entranceFloorId"]
    spire = current_tower["schedules"][0]["floorList"]

    for floor_id in corridor + spire:
        floor = find_tower_floor(tower_floor, floor_id)
        result.append(a_floor := AbyssFloor(num=floor["floorIndex"], chambers=[]))
        tower_levels = find_tower_levels(tower_level, floor["levelGroupId"])
        for t_level in tower_levels:
            a_floor.chambers.append(
                a_chamber := AbyssChamber(
                    num=t_level["levelIndex"],
                    enemy_level=t_level["monsterLevel"],
                    halfs=[],
                )
            )
            halfs: List[List[int]] = [
                t_level["firstMonsterList"],
                t_level["secondMonsterList"],
            ]
            for index, half in enumerate(halfs):
                a_chamber.halfs.append(a_half := AbyssHalf(num=index + 1, enemies=[]))
                for monster_id in half:
                    monster = find_monster_describe(monster_describe, monster_id)
                    if monster:
                        a_half.enemies.append(
                            get_text(text_map, locale, monster["nameTextMapHash"])
                        )

        result.append(a_floor)

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


def find_tower_levels(
    tower_level: List[Dict[str, Any]], level_grou_id: int
) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for t in tower_level:
        if t["levelGroupId"] == level_grou_id:
            result.append(t)
    return result


def find_monster_describe(
    monster_describe: List[Dict[str, Any]], monster_id: int
) -> Dict[str, Any]:
    for m in monster_describe:
        if m["id"] == monster_id:
            return m
    return {}
