import asyncio
import json
import typing
import uuid

import aiofiles
import aiohttp
import genshin

import dev.asset as asset
import dev.models as models
from apps.text_map import AMBR_LANGS
from data.game.elements import convert_element
from utils import get_element_name

# abyss.json


def add_abyss_entry(
    result: typing.Dict[str, typing.Any],
    account: models.ShenheAccount,
    abyss: genshin.models.SpiralAbyss,
    characters: typing.List[genshin.models.Character],
) -> None:
    result["size"] += 1

    data_id = str(uuid.uuid4())
    abyss_dict = {
        "id": data_id,
        "floors": [],
    }
    user_dict = {
        "_id": data_id,
        "uid": account.uid,
        "avatars": [],
    }

    floors = [f for f in abyss.floors if f.floor >= 11]
    for floor in floors:
        floor_dict = {"floor": floor.floor, "chambers": []}

        for chamber in floor.chambers:
            chamber_list = []
            for battle in chamber.battles:
                chamber_list.append([c.id for c in battle.characters])
            floor_dict["chambers"].append(chamber_list)
        abyss_dict["floors"].append(floor_dict)

    for character in characters:
        character_dict = {
            "id": character.id,
            "name": character.name,
            "element": character.element,
            "level": character.level,
            "cons": character.constellation,
            "weapon": character.weapon.name,
            "artifacts": [a.set.name for a in character.artifacts],
        }
        user_dict["avatars"].append(character_dict)

    abyss_dict["user"] = user_dict
    result["data"].append(abyss_dict)


# text maps


async def update_thing_text_map(thing: str, session: aiohttp.ClientSession) -> None:
    update_dict: typing.Dict[str, typing.Dict[str, str]] = {}
    for discord_lang, lang in AMBR_LANGS.items():
        async with session.get(f"https://api.ambr.top/v2/{lang}/{thing}") as r:
            data = await r.json()
        for item_id, item_data in data["data"]["items"].items():
            if item_id not in update_dict:
                update_dict[item_id] = {}

            if thing == "avatar" and any(
                str(t_id) in str(item_id) for t_id in asset.traveler_ids
            ):
                update_dict[item_id][lang] = (
                    item_data["name"]
                    + f" ({get_element_name(convert_element(item_data['element']), discord_lang)})"
                    + f" ({'♂️' if '10000005' in item_id else '♀️'})"
                )
            else:
                update_dict[item_id][lang] = item_data["name"]
    if thing == "avatar":
        update_dict["10000007"] = asset.lumine_name_dict
        update_dict["10000005"] = asset.aether_name_dict
    async with aiofiles.open(f"text_maps/{thing}.json", "w+", encoding="utf-8") as f:
        await f.write(json.dumps(update_dict, indent=4, ensure_ascii=False))


async def update_dungeon_text_map(session: aiohttp.ClientSession) -> None:
    update_dict = {}
    for lang in list(AMBR_LANGS.values()):
        async with session.get(f"https://api.ambr.top/v2/{lang}/dailyDungeon") as r:
            data = await r.json()
        for _, domains in data["data"].items():
            for _, domain_info in domains.items():
                if str(domain_info["id"]) not in update_dict:
                    update_dict[str(domain_info["id"])] = {}
                update_dict[str(domain_info["id"])][lang] = domain_info["name"]
    async with aiofiles.open(
        "text_maps/dailyDungeon.json", "w+", encoding="utf-8"
    ) as f:
        await f.write(json.dumps(update_dict, indent=4, ensure_ascii=False))


async def update_item_text_map(things_to_update) -> None:
    huge_text_map: typing.Dict[str, str] = {}
    for thing in things_to_update:
        async with aiofiles.open(f"text_maps/{thing}.json", "r", encoding="utf-8") as f:
            text_map_: typing.Dict[str, typing.Dict[str, str]] = json.loads(
                await f.read()
            )
        for item_id, item_info in text_map_.items():
            for name in item_info.values():
                if name in huge_text_map:
                    continue

                if "10000005" in item_id:
                    huge_text_map[name] = "10000005"
                elif "10000007" in item_id:
                    huge_text_map[name] = "10000007"
                else:
                    huge_text_map[name] = item_id
    async with aiofiles.open("text_maps/item_name.json", "w+", encoding="utf-8") as f:
        await f.write(json.dumps(huge_text_map, indent=4, ensure_ascii=False))


async def retry_task_five_times(task, *args, **kwargs) -> typing.Any:
    exception = None
    for _ in range(5):
        try:
            return await task(*args, **kwargs)
        except Exception as e:
            exception = e
            await asyncio.sleep(60)
    if exception is not None:
        raise exception
