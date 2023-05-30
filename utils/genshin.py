import json
from calendar import monthrange
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiofiles
import aiohttp
import asyncpg
import discord
import genshin
import yaml
from discord import Locale
from discord.utils import get

import dev.asset as asset
import dev.enum as enum
import dev.models as models
from ambr import AmbrTopAPI, Character, Domain, Material, Weapon
from ambr.models import CharacterDetail
from apps.db.json import read_json, write_json
from apps.db.tables.hoyo_account import HoyoAccount
from apps.enka.api_docs import get_character_skill_order
from apps.text_map import cond_text, text_map, to_ambr_top
from data.game.artifact_map import artifact_map
from data.game.character_map import character_map
from data.game.fight_prop import fight_prop
from data.game.weapon_map import weapon_map

from .general import get_dt_now
from .text_map import get_city_name, translate_main_stat


def calculate_artifact_score(substats: dict):
    tier_four_val = {
        "FIGHT_PROP_HP": 1196,
        "FIGHT_PROP_HP_PERCENT": 5.8,
        "FIGHT_PROP_ATTACK": 76,
        "FIGHT_PROP_ATTACK_PERCENT": 5.8,
        "FIGHT_PROP_DEFENSE": 92,
        "FIGHT_PROP_DEFENSE_PERCENT": 7.3,
        "FIGHT_PROP_CHARGE_EFFICIENCY": 6.5,
        "FIGHT_PROP_ELEMENT_MASTERY": 23,
        "FIGHT_PROP_CRITICAL": 3.9,
        "FIGHT_PROP_CRITICAL_HURT": 7.8,
    }
    result = 0
    for sub, val in substats.items():
        result += val / tier_four_val.get(sub) * 11
    return result


def get_character_builds(
    character_id: str, element_builds_dict: dict, lang: discord.Locale | str
) -> List[models.CharacterBuild]:
    """Gets a character's builds

    Args:
        character_id (int): the id of the character
        element_builds_dict (dict): the dictionary of all characters of a given element, this is stored in data/builds
        lang (Locale): the discord lang
        user_locale (str): the user lang

    Returns:
        List[models.CharacterBuild]
    """
    character_name = text_map.get_character_name(character_id, "zh-TW")
    translated_character_name = text_map.get_character_name(character_id, lang)
    count = 1
    result = []

    for build in element_builds_dict[character_name]["builds"]:
        stat_str = ""
        for stat, value in build["stats"].items():
            stat_str += f"{cond_text.get_text(str(lang), 'build', stat)} ➜ {str(value).replace('任意', 'ANY')}\n"
        move_text = cond_text.get_text(
            str(lang), "build", f"{character_name}_{build['move']}"
        )
        weapon_id = text_map.get_id_from_name(build["weapon"])
        if weapon_id is None:
            raise ValueError(f"Unknown weapon {build['weapon']}")
        embed = models.DefaultEmbed(
            f"{translated_character_name} - {text_map.get(90, lang)}{count}",
            f"{text_map.get(91, lang)} • {get_weapon_emoji(weapon_id)} {text_map.get_weapon_name(weapon_id, lang)}\n"
            f"{text_map.get(92, lang)} • {cond_text.get_text(str(lang), 'build', build['artifacts'])}\n"
            f"{text_map.get(93, lang)} • {translate_main_stat(build['main_stats'], lang)}\n"
            f"{text_map.get(94, lang)} • {build['talents']}\n"
            f"{move_text} • {str(build['dmg']).replace('任意', 'ANY')}\n\n",
        )
        embed.add_field(name=text_map.get(95, lang), value=stat_str)
        count += 1
        embed.set_thumbnail(url=get_character_icon(str(character_id)))
        result.append(
            models.CharacterBuild(
                embed=embed,
                weapon=build["weapon"],
                artifact=build["artifacts"],
                is_thought=False,
            )
        )

    if "thoughts" in element_builds_dict[character_name]:
        count = 1
        embed = models.DefaultEmbed(text_map.get(97, lang))
        for _ in element_builds_dict[character_name]["thoughts"]:
            embed.add_field(
                name=f"#{count}",
                value=cond_text.get_text(
                    str(lang), "build", f"{character_name}_thoughts_{count-1}"
                ),
                inline=False,
            )
            count += 1
        embed.set_thumbnail(url=get_character_icon(str(character_id)))
        result.append(models.CharacterBuild(embed=embed, is_thought=True))

    return result


def get_character_emoji(id: str) -> str:
    return character_map.get(id, {}).get("emoji", "")


def get_weapon_emoji(id: int) -> str:
    return weapon_map.get(str(id), {}).get("emoji", "")


def get_character_icon(id: str) -> str:
    return character_map.get(id, {}).get("icon", "")


def get_artifact(id: Optional[int] = 0, name: str = ""):
    for artifact_id, artifact_info in artifact_map.items():
        if (
            artifact_id == str(id)
            or name in artifact_info["artifacts"]
            or name == artifact_info["name"]
        ):
            return artifact_info
    raise ValueError(f"Unknwon artifact {id}{name}")


def get_fight_prop(id: str) -> models.FightProp:
    fight_prop_dict = fight_prop.get(
        id,
        {
            "name": "未知角色數據",
            "emoji": "",
            "substat": False,
            "text_map_hash": 700,
        },
    )
    return models.FightProp(**fight_prop_dict)  # type: ignore


def get_area_emoji(exploration_id: int):
    emoji_dict = {
        1: "<:Emblem_Mondstadt:982449412938809354>",
        2: "<:Emblem_Liyue:982449411047165992>",
        3: "<:Emblem_Dragonspine:982449405883977749>",
        4: "<:Emblem_Inazuma:982449409117806674>",
        5: "<:Emblem_Enkanomiya:982449407469441045>",
        6: "<:Emblem_Chasm:982449404076249138>",
        7: "<:Emblem_Chasm:982449404076249138>",
        8: "<:SUMERU:1015877773899857941>",
    }

    emoji = emoji_dict.get(exploration_id)
    return emoji or ""


def get_city_emoji(city_id: int):
    emoji_dict = {
        1: "<:Emblem_Mondstadt:982449412938809354>",
        2: "<:Emblem_Liyue:982449411047165992>",
        3: "<:Emblem_Inazuma:982449409117806674>",
        4: "<:SUMERU:1015877773899857941>",
    }
    return emoji_dict.get(city_id)


def get_uid_region_hash(uid: int) -> int:
    str_uid = str(uid)
    region_map = {
        "9": 547,
        "1": 548,
        "2": 548,
        "5": 549,
        "6": 550,
        "7": 551,
        "8": 552,
        "0": 554,
    }
    return region_map.get(str_uid[0], 553)


def get_uid_tz(uid: Optional[int]) -> int:
    str_uid = str(uid)
    region_map: Dict[str, int] = {
        "6": -13,  # North America
        "7": -7,  # Europe
    }
    return region_map.get(str_uid[0], 0)


async def get_farm_data(
    lang: Locale | str, session: aiohttp.ClientSession, weekday: int
) -> List[models.FarmData]:
    result: List[models.FarmData] = []

    client = AmbrTopAPI(session, to_ambr_top(lang))
    domains = await client.get_domains()
    c_upgrades = await client.get_character_upgrade()
    w_upgrades = await client.get_weapon_upgrade()
    if not isinstance(c_upgrades, list):
        raise AssertionError
    if not isinstance(w_upgrades, list):
        raise AssertionError

    for domain in domains:
        if domain.weekday != weekday:
            continue
        farm_data = models.FarmData(domain=domain)
        if len([r for r in domain.rewards if len(str(r.id)) == 6]) == 4:
            for w_upgrade in w_upgrades:
                upgrade_items = [
                    (await client.get_material(item.id)) for item in w_upgrade.items
                ]
                if any(
                    item in domain.rewards
                    for item in upgrade_items
                    if isinstance(item, Material)
                ):
                    weapon = await client.get_weapon(w_upgrade.weapon_id)
                    if not isinstance(weapon, Weapon):
                        raise AssertionError
                    farm_data.weapons.append(weapon)
        else:
            for c_upgrade in c_upgrades:
                upgrade_items = [
                    (await client.get_material(item.id)) for item in c_upgrade.items
                ]
                if any(
                    item in domain.rewards
                    for item in upgrade_items
                    if isinstance(item, Material)
                ):
                    character = await client.get_character(c_upgrade.character_id)
                    if not isinstance(character, Character):
                        raise AssertionError
                    farm_data.characters.append(character)
        result.append(farm_data)

    return result


def get_domain_title(domain: Domain, lang: discord.Locale | str) -> str:
    if "Forgery" in text_map.get_domain_name(domain.id, "en-US"):
        return (
            f"{get_city_name(domain.city.id, str(lang))} - {text_map.get(91, lang)}"
        )
    return f"{get_city_name(domain.city.id, str(lang))} - {text_map.get(105, lang).title()}"


def convert_ar_to_wl(ar: int) -> int:
    if 1 <= ar <= 19:
        return 0
    if 20 <= ar < 25:
        return 1
    if 25 <= ar < 29:
        return 2
    if 30 <= ar < 35:
        return 3
    if 35 <= ar < 39:
        return 4
    if 40 <= ar < 45:
        return 5
    if 45 <= ar < 50:
        return 6
    if 50 <= ar < 54:
        return 7
    return 8


def convert_wl_to_mora(wl: int) -> int:
    if wl == 0:
        return 12000
    if wl == 1:
        return 20000
    if wl == 2:
        return 28000
    if wl == 3:
        return 36000
    if wl == 4:
        return 44000
    if wl == 5:
        return 52000
    return 60000


def level_to_ascension_phase(level: int) -> int:
    if level < 20:
        return 0
    if level < 40:
        return 1
    if level < 50:
        return 2
    if level < 60:
        return 3
    if level < 70:
        return 4
    if level < 80:
        return 5
    if level <= 90:
        return 6
    raise ValueError("Level is too high")


async def get_character_suggested_talent_levels(
    character_id: str, session: aiohttp.ClientSession
) -> List[int]:
    chinese_character_name = text_map.get_character_name(character_id, "zh-TW")
    ambr = AmbrTopAPI(session)
    character = await ambr.get_character(character_id)
    if not isinstance(character, Character):
        return [1, 1, 1]
    with open(f"data/builds/{character.element.lower()}.yaml") as f:
        builds: Dict[str, Any] = yaml.safe_load(f)  # type: ignore
    character_build = builds.get(chinese_character_name)  # type: ignore
    if character_build is None:
        return [1, 1, 1]
    talents = builds[chinese_character_name]["builds"][0]["talents"]  # type: ignore
    talents = talents.split("/")
    return [int(talent) for talent in talents]


def get_current_abyss_season() -> int:
    """Get the current abyss season number based on the current datetime."""
    ref_season_num = 59
    ref_season_time = datetime(2022, 12, 1, 4, 0, 0)

    current_season_num = ref_season_num
    current_season_time = ref_season_time
    while current_season_time < get_dt_now():
        current_season_time += timedelta(days=1)
        if current_season_time.day in (1, 16):
            current_season_num += 1

    return current_season_num


def get_abyss_season_date_range(season: int) -> str:
    """Get the date range of a given season"""
    ref_season_num = 59
    ref_season_time = datetime(2022, 12, 1, 4, 0, 0)

    current_season_num = ref_season_num
    current_season_time = ref_season_time
    while current_season_num != season:
        current_season_time += timedelta(days=1)
        if current_season_time.day in (1, 16):
            current_season_num += 1

    season_start = current_season_time
    if current_season_time.day == 1:
        season_end = current_season_time.replace(day=15)
    else:
        season_end = current_season_time.replace(
            day=monthrange(current_season_time.year, current_season_time.month)[1]
        )

    return f"{season_start.strftime('%Y-%m-%d')} ~ {season_end.strftime('%Y-%m-%d')}"


def get_account_options(
    accounts: List[HoyoAccount],
) -> List[discord.SelectOption]:
    GAME_EMOJIS = {
        enum.GameType.GENSHIN: asset.genshin_emoji,
        enum.GameType.HSR: asset.hsr_emoji,
        enum.GameType.HONKAI: asset.honkai_emoji,
    }

    options: List[discord.SelectOption] = []
    for account in accounts:
        label = str(account.uid)
        if account.nickname:
            label += f" ({account.nickname[:80]})"
        options.append(
            discord.SelectOption(
                label=label,
                value=str(account.uid),
                emoji=GAME_EMOJIS[account.game],
            )
        )
    return options


async def get_character_fanarts(character_id: str) -> List[str]:
    """Get the fanart URLs of a character."""
    async with aiofiles.open("yelan/data/genshin_fanart.json", "r") as f:
        fanart: Dict[str, List[str]] = json.loads(await f.read())

    return fanart.get(character_id, [])


async def calc_e_q_boost(
    session: aiohttp.ClientSession, character_id: str
) -> enum.TalentBoost:
    client = AmbrTopAPI(session)
    detail = await client.get_character_detail(character_id)
    if not isinstance(detail, CharacterDetail):
        raise ValueError("Invalid character ID")
    c3 = detail.constellations[2]
    e_skill = detail.talents[1]
    if e_skill.name in c3.description:
        return enum.TalentBoost.BOOST_E
    return enum.TalentBoost.BOOST_Q


async def update_talents_json(
    characters: List[genshin.models.Character],
    client: genshin.Client,
    pool: asyncpg.Pool,
    uid: int,
    session: aiohttp.ClientSession,
):
    talents_: Dict[str, str] = {}
    boost_dict = await read_json(pool, "genshin/talent_boost.json")
    if boost_dict is None:
        boost_dict = {}
    try:
        await client._enable_calculator_sync()  # skipcq: PYL-W0212
    except genshin.GenshinException:
        pass

    for character in characters:
        try:
            details = await client.get_character_details(character.id)
        except genshin.GenshinException:
            break
        character_id = str(character.id)
        if character.id in asset.traveler_ids:
            character_id = f"{character.id}-{character.element.lower()}"

        if boost_dict is None or character_id not in boost_dict:
            boost = await calc_e_q_boost(session, character_id)
            if boost_dict is None:
                boost_dict = {}
            boost_dict[str(character_id)] = boost.value
            await write_json(pool, "genshin/talent_boost.json", boost_dict)
        boost = enum.TalentBoost(boost_dict[character_id])

        skill_order = await get_character_skill_order(str(character.id))
        a_skill = details.talents[0]
        e_skill = details.talents[1]
        q_skill = details.talents[-1]
        if skill_order:
            a_skill = get(details.talents, id=skill_order[0])
            e_skill = get(details.talents, id=skill_order[1])
            q_skill = get(details.talents, id=skill_order[2])
        if not a_skill or not e_skill or not q_skill:
            a_skill = details.talents[0]
            e_skill = details.talents[1]
            q_skill = details.talents[-1]

        if a_skill and e_skill and q_skill:
            a_skill = a_skill.level
            e_skill = e_skill.level
            q_skill = q_skill.level
            c3 = character.constellations[2]
            c5 = character.constellations[4]
            if boost is enum.TalentBoost.BOOST_E and c3.activated:
                e_skill += 3
            elif boost is enum.TalentBoost.BOOST_Q and c5.activated:
                q_skill += 3
            talents_[str(character.id)] = f"{a_skill}/{e_skill}/{q_skill}"

    talents_["last_updated"] = get_dt_now().strftime("%Y-%m-%d %H:%M:%S")
    await write_json(pool, f"talents/{uid}.json", talents_)
