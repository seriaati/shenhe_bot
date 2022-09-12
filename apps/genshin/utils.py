import os
from typing import Dict, List, Literal, Tuple, Union

from apps.text_map.text_map_app import text_map
from data.game.artifacts import artifacts_map
from data.game.characters import characters_map
from data.game.elements import elements
from data.game.fight_prop import fight_prop
from data.game.weapons import weapons_map
from discord import Embed, Locale, SelectOption
from dotenv import load_dotenv
from utility.utils import default_embed, parse_HTML
import aiosqlite

import genshin

load_dotenv()


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
    character_id: int, element_builds_dict: dict, locale: Locale, user_locale: str
) -> Tuple[List[Union[Embed, str, str]], bool]:
    """Gets a character's builds

    Args:
        character_id (int): the id of the character
        element_builds_dict (dict): the dictionary of all characters of a given element, this is stored in data/builds
        locale (Locale): the discord locale
        user_locale (str): the user locale

    Returns:
        Tuple[List[Embed], bool]: returns a list of lists of embeds, weapons, and artifacts of different builds + a boolean that indicates whether the character has artifact thoughts
    """
    character_name = text_map.get_character_name(character_id, "zh-TW", None)
    translated_character_name = text_map.get_character_name(
        character_id, locale, user_locale
    )
    count = 1
    has_thoughts = False
    result = []

    for build in element_builds_dict[character_name]["builds"]:
        statStr = ""
        for stat, value in build["stats"].items():
            statStr += f"{stat} ➜ {value}\n"
        embed = default_embed(
            f"{translated_character_name} - {text_map.get(90, locale, user_locale)}{count}",
            f"{text_map.get(91, locale, user_locale)} • {get_weapon(name=build['weapon'])['emoji']} {build['weapon']}\n"
            f"{text_map.get(92, locale, user_locale)} • {build['artifacts']}\n"
            f"{text_map.get(93, locale, user_locale)} • {build['main_stats']}\n"
            f"{text_map.get(94, locale, user_locale)} • {build['talents']}\n"
            f"{build['move']} • {build['dmg']}\n\n",
        )
        embed.add_field(name=text_map.get(95, locale, user_locale), value=statStr)
        count += 1
        embed.set_thumbnail(url=get_character(character_id)["icon"])
        embed.set_footer(
            text=f"[{text_map.get(96, locale, user_locale)}](https://bbs.nga.cn/read.php?tid=25843014)"
        )
        result.append([embed, build["weapon"], build["artifacts"]])

    if "thoughts" in element_builds_dict[character_name]:
        has_thoughts = True
        count = 1
        embed = default_embed(text_map.get(97, locale, user_locale))
        for thought in element_builds_dict[character_name]["thoughts"]:
            embed.add_field(name=f"#{count}", value=thought, inline=False)
            count += 1
        embed.set_thumbnail(url=get_character(character_id)["icon"])
        result.append([embed, text_map.get(97, locale, user_locale), ""])

    return result, has_thoughts


def get_character(id: int = "", name: str = "", eng: str = ""):
    for character_id, character_info in characters_map.items():
        if (
            str(id) == character_id
            or character_info["name"] == name
            or character_info["eng"] == eng
        ):
            return character_info
    return {
        "name": f"{id}{name}{eng}",
        "element": "Cryo",
        "rarity": 5,
        "icon": "https://icons.iconarchive.com/icons/paomedia/small-n-flat/1024/sign-error-icon.png",
        "emoji": "<:WARNING:992552271378386944>",
        "eng": "Unknown",
    }


def get_weapon(id: int = "", name: str = ""):
    for weapon_id, weapon_info in weapons_map.items():
        if weapon_id == str(id) or weapon_info["name"] == name:
            return weapon_info
    return {
        "name": f"{id}{name}",
        "emoji": "⚠️",
        "rarity": 5,
        "icon": "https://icons.iconarchive.com/icons/paomedia/small-n-flat/1024/sign-error-icon.png",
        "eng": "Unknown",
    }


def get_artifact(id: int = "", name: str = ""):
    for artifact_id, artifact_info in artifacts_map.items():
        if (
            artifact_id == str(id)
            or name in artifact_info["artifacts"]
            or name == artifact_info["name"]
        ):
            return artifact_info
    raise ValueError(f"Unknwon artifact {id}{name}")


def get_fight_prop(id: str = "", name: str = ""):
    for fight_prop_id, fight_prop_info in fight_prop.items():
        if fight_prop_id == str(id) or name == fight_prop_info["name"]:
            return fight_prop_info
    raise ValueError(f"Unknwon fight prop {id}{name}")


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


def get_uid_region(uid: int) -> int:
    uid = str(uid)
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
    return region_map.get(uid[0], 553)


def parse_character_wiki_embed(
    avatar: Dict, avatar_id: str, locale: Locale, user_locale: str | None
) -> Tuple[List[Embed], Embed, List[SelectOption]]:
    avatar_data = avatar["data"]
    embeds = []
    options = []
    embed = default_embed(
        f"{elements.get(avatar['data']['element'])} {avatar['data']['name']}"
    )
    embed.add_field(
        name=text_map.get(315, locale, user_locale),
        value=f'{text_map.get(316, locale, user_locale)}: {avatar_data["birthday"][0]}/{avatar_data["birthday"][1]}\n'
        f'{text_map.get(317, locale, user_locale)}: {avatar_data["fetter"]["title"]}\n'
        f'*{avatar_data["fetter"]["detail"]}*\n'
        f'{text_map.get(318, locale, user_locale)}: {avatar_data["fetter"]["constellation"]}\n'
        f'{text_map.get(319, locale, user_locale)}: {avatar_data["other"]["nameCard"]["name"] if "name" in avatar_data["other"]["nameCard"]else "???"}\n',
    )
    embed.set_image(
        url=f'https://api.ambr.top/assets/UI/namecard/{avatar_data["other"]["nameCard"]["icon"].replace("Icon", "Pic")}_P.png'
    )
    embed.set_thumbnail(
        url=(f'https://api.ambr.top/assets/UI/{avatar_data["icon"]}.png')
    )
    embeds.append(embed)
    options.append(SelectOption(label=embed.fields[0].name, value=0))
    embed = default_embed().set_author(
        name=text_map.get(320, locale, user_locale),
        icon_url=(f'https://api.ambr.top/assets/UI/{avatar_data["icon"]}.png'),
    )
    for promoteLevel in avatar_data["upgrade"]["promote"][1:]:
        value = ""
        for item_id, item_count in promoteLevel["costItems"].items():
            value += f"{text_map.get_material_name(item_id, locale, user_locale)} x{item_count}\n"
        value += f'<:202:991561579218878515> x{promoteLevel["coinCost"]}\n'
        embed.add_field(
            name=f'{text_map.get(321, locale, user_locale)} lvl.{promoteLevel["unlockMaxLevel"]}',
            value=value,
            inline=True,
        )
    embeds.append(embed)
    options.append(SelectOption(label=text_map.get(320, locale, user_locale), value=1))
    for talent_id, talent_info in avatar_data["talent"].items():
        max = 3
        if avatar_id == "10000002" or avatar_id == "10000041":
            max = 4
        if int(talent_id) <= max:
            embed = default_embed().set_author(
                name=text_map.get(94, locale, user_locale),
                icon_url=(f'https://api.ambr.top/assets/UI/{avatar_data["icon"]}.png'),
            )
            embed.add_field(
                name=talent_info["name"],
                value=parse_HTML(talent_info["description"]),
                inline=False,
            )
            material_embed = default_embed().set_author(
                name=text_map.get(322, locale, user_locale),
                icon_url=(f'https://api.ambr.top/assets/UI/{avatar_data["icon"]}.png'),
            )
            for level, promote_info in talent_info["promote"].items():
                if level == "1" or int(level) > 10:
                    continue
                value = ""
                for item_id, item_count in promote_info["costItems"].items():
                    value += f"{text_map.get_material_name(item_id, locale, user_locale)} x{item_count}\n"
                value += f'<:202:991561579218878515> x{promote_info["coinCost"]}\n'
                material_embed.add_field(
                    name=f"{text_map.get(324, locale, user_locale)} lvl.{level}",
                    value=value,
                    inline=True,
                )
            embed.set_thumbnail(
                url=f'https://api.ambr.top/assets/UI/{talent_info["icon"]}.png'
            )
            embeds.append(embed)
        else:
            embed = default_embed().set_author(
                name=text_map.get(323, locale, user_locale),
                icon_url=(f'https://api.ambr.top/assets/UI/{avatar_data["icon"]}.png'),
            )
            embed.add_field(
                name=talent_info["name"],
                value=parse_HTML(talent_info["description"]),
                inline=False,
            )
            embed.set_thumbnail(
                url=f'https://api.ambr.top/assets/UI/{talent_info["icon"]}.png'
            )
            embeds.append(embed)
    options.append(SelectOption(label=text_map.get(94, locale, user_locale), value=2))
    options.append(
        SelectOption(
            label=text_map.get(323, locale, user_locale), value=5 if max == 3 else 6
        )
    )
    const_count = 1
    for const_id, const_info in avatar_data["constellation"].items():
        embed = default_embed().set_author(
            name=f"{text_map.get(318, locale, user_locale)} {const_count}",
            icon_url=(f'https://api.ambr.top/assets/UI/{avatar_data["icon"]}.png'),
        )
        embed.add_field(
            name=const_info["name"], value=parse_HTML(const_info["description"])
        )
        embed.set_thumbnail(
            url=f'https://api.ambr.top/assets/UI/{const_info["icon"]}.png'
        )
        embeds.append(embed)
        const_count += 1
    options.append(
        SelectOption(
            label=text_map.get(318, locale, user_locale), value=8 if max == 3 else 9
        )
    )
    return embeds, material_embed, options
