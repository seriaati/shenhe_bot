import json
import typing
import uuid

import aiohttp
import asyncpg
import genshin

import asset
import models
from apps.db import get_user_notif
from apps.text_map import AMBR_LANGS, get_element_name, text_map
from data.game.elements import convert_element
from utility import DefaultEmbed, ErrorEmbed, log, send_embed

# abyss.json


def add_abyss_entry(
    result: typing.Dict[str, typing.Any],
    account: models.ShenheAccount,
    abyss: genshin.models.SpiralAbyss,
    characters: typing.List[genshin.models.Character],
):
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


# daily check-in


async def handle_daily_reward_error(
    user: models.ShenheAccount, error_message: str, pool: asyncpg.Pool
):
    await pool.execute(
        """
        UPDATE user_accounts
        SET daily_checkin = false
        WHERE user_id = $1 AND uid = $2
        """,
        user.discord_user.id,
        user.uid,
    )

    embed = ErrorEmbed(
        description=f"""
            {error_message}

            {text_map.get(630, 'en-US', user.user_locale)}
            """
    )
    embed.set_author(
        name=text_map.get(500, "en-US", user.user_locale),
        icon_url=user.discord_user.display_avatar.url,
    )
    embed.set_footer(text=text_map.get(611, "en-US", user.user_locale))
    await send_embed(user.discord_user, embed)


async def daily_reward_success(
    success_count: int,
    user: models.ShenheAccount,
    reward: genshin.models.DailyReward,
    pool: asyncpg.Pool,
) -> int:
    log.info(f"[Schedule][Claim Reward] Claimed reward for {user}")
    if await get_user_notif(user.discord_user.id, pool):
        embed = DefaultEmbed(
            text_map.get(87, "en-US", user.user_locale),
            f"{reward.name} x{reward.amount}",
        )
        embed.set_thumbnail(url=reward.icon)
        embed.set_footer(text=text_map.get(211, "en-US", user.user_locale))

        await send_embed(user.discord_user, embed)

    success_count += 1
    return success_count


# text maps


async def update_thing_text_map(thing: str, session: aiohttp.ClientSession):
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
    with open(f"text_maps/{thing}.json", "w+", encoding="utf-8") as f:
        json.dump(update_dict, f, indent=4, ensure_ascii=False)


async def update_dungeon_text_map(session: aiohttp.ClientSession):
    update_dict = {}
    for lang in list(AMBR_LANGS.values()):
        async with session.get(f"https://api.ambr.top/v2/{lang}/dailyDungeon") as r:
            data = await r.json()
        for _, domains in data["data"].items():
            for _, domain_info in domains.items():
                if str(domain_info["id"]) not in update_dict:
                    update_dict[str(domain_info["id"])] = {}
                update_dict[str(domain_info["id"])][lang] = domain_info["name"]
    with open("text_maps/dailyDungeon.json", "w+", encoding="utf-8") as f:
        json.dump(update_dict, f, indent=4, ensure_ascii=False)


def update_item_text_map(things_to_update):
    huge_text_map = {}
    for thing in things_to_update:
        with open(f"text_maps/{thing}.json", "r", encoding="utf-8") as f:
            text_map_ = json.load(f)
        for item_id, item_info in text_map_.items():
            for name in item_info.values():
                if "10000005" in item_id:
                    huge_text_map[name] = "10000005"
                elif "10000007" in item_id:
                    huge_text_map[name] = "10000007"
                else:
                    huge_text_map[name] = item_id
    with open("text_maps/item_name.json", "w+", encoding="utf-8") as f:
        json.dump(huge_text_map, f, indent=4, ensure_ascii=False)
