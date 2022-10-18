from datetime import datetime
from typing import Dict, List, Tuple, Union
import discord
import aiosqlite
import enkanetwork
from ambr.client import AmbrTopAPI
from ambr.models import Character, Domain, Weapon
from apps.genshin.custom_model import ShenheUser
from apps.text_map.convert_locale import to_ambr_top, to_genshin_py
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale, get_weekday_name, translate_main_stat
from apps.text_map.cond_text import cond_text
from data.game.artifact_map import artifact_map
from data.game.character_map import character_map
from data.game.elements import elements
from data.game.fight_prop import fight_prop
from data.game.weapon_map import weapon_map
from discord import Embed, Locale, SelectOption
from discord.ext import commands
from diskcache import FanoutCache
from utility.utils import default_embed, divide_dict, parse_HTML
import genshin


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
    locale = user_locale or locale
    character_name = text_map.get_character_name(character_id, "zh-TW", None)
    translated_character_name = text_map.get_character_name(character_id, locale)
    count = 1
    has_thoughts = False
    result = []

    for build in element_builds_dict[character_name]["builds"]:
        stat_str = ""
        for stat, value in build["stats"].items():
            stat_str += f"{cond_text.get_text(locale, 'build', stat)} ➜ {str(value).replace('任意', 'ANY')}\n"
        move_text = cond_text.get_text(
            locale, "build", f"{character_name}_{build['move']}"
        )
        weapon_id = text_map.get_weapon_id_with_name(build["weapon"])
        embed = default_embed(
            f"{translated_character_name} - {text_map.get(90, locale)}{count}",
            f"{text_map.get(91, locale)} • {get_weapon(name=build['weapon'])['emoji']} {text_map.get_weapon_name(weapon_id, locale)}\n"
            f"{text_map.get(92, locale)} • {cond_text.get_text(locale, 'build', build['artifacts'])}\n"
            f"{text_map.get(93, locale)} • {translate_main_stat(build['main_stats'], locale)}\n"
            f"{text_map.get(94, locale)} • {build['talents']}\n"
            f"{move_text}{'' if str(locale) in ['zh-TW', 'zh-CN'] else ' DMG'} • {str(build['dmg']).replace('任意', 'ANY')}\n\n",
        )
        embed.add_field(name=text_map.get(95, locale), value=stat_str)
        count += 1
        embed.set_thumbnail(url=get_character(character_id)["icon"])
        embed.set_footer(
            text=f"{text_map.get(96, locale)}: https://bbs.nga.cn/read.php?tid=25843014"
        )
        result.append([embed, build["weapon"], build["artifacts"]])

    if "thoughts" in element_builds_dict[character_name]:
        has_thoughts = True
        count = 1
        embed = default_embed(text_map.get(97, locale))
        for _ in element_builds_dict[character_name]["thoughts"]:
            embed.add_field(
                name=f"#{count}",
                value=cond_text.get_text(
                    locale, "build", f"{character_name}_thoughts_{count-1}"
                ),
                inline=False,
            )
            count += 1
        embed.set_thumbnail(url=get_character(character_id)["icon"])
        result.append([embed, text_map.get(97, locale), ""])

    return result, has_thoughts


def get_character(id: int = "", name: str = "", eng: str = ""):
    for character_id, character_info in character_map.items():
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
    for weapon_id, weapon_info in weapon_map.items():
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
    for artifact_id, artifact_info in artifact_map.items():
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
        f'{text_map.get(318, locale, user_locale)}: {avatar_data["fetter"]["constellation"]}\n'
        f'{text_map.get(319, locale, user_locale)}: {avatar_data["other"]["nameCard"]["name"] if "name" in avatar_data["other"]["nameCard"]else "???"}\n\n'
        f'*{avatar_data["fetter"]["detail"]}*\n',
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
    embed.set_image(
        url=f"https://api.ambr.top/assets/UI/generated/ascension/avatar/{avatar_id}.png"
    )
    for promoteLevel in avatar_data["upgrade"]["promote"][1:]:
        value = ""
        for item_id, item_count in promoteLevel["costItems"].items():
            value += f"{text_map.get_material_name(item_id, locale, user_locale)} x{item_count}\n"
        value += f'{text_map.get_material_name(202, locale, user_locale)} x{promoteLevel["coinCost"]}\n'
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
            embed.title = talent_info["name"]
            embed.description = parse_HTML(talent_info["description"])
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
                value += f'{text_map.get_material_name(202, locale, user_locale)} x{promote_info["coinCost"]}\n'
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
    for _, const_info in avatar_data["constellation"].items():
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


async def get_shenhe_user(
    user_id: int,
    db: aiosqlite.Connection,
    bot: commands.Bot,
    locale: Locale = None,
    cookie: Dict[str, str | int] = None,
    custom_uid: int = None,
    daily_checkin: int = 1,
) -> ShenheUser:
    discord_user = bot.get_user(user_id) or await bot.fetch_user(user_id)
    if not cookie:
        c: aiosqlite.Cursor = await db.cursor()
        await c.execute(
            "SELECT ltuid, ltoken, cookie_token, uid, china, current FROM user_accounts WHERE user_id = ?",
            (user_id,),
        )
        user_data = await c.fetchall()
        for _, tpl in enumerate(user_data):
            if tpl[5] == 1:
                user_data = tpl
                break
            else:
                user_data = tpl

        if user_data[0] is not None:
            client = genshin.Client()
            client.set_cookies(
                ltuid=user_data[0],
                ltoken=user_data[1],
                account_id=user_data[0],
                cookie_token=user_data[2],
            )
        else:
            client = bot.genshin_client
        uid = user_data[3]
        await c.close()
    else:
        client = genshin.Client()
        client.set_cookies(cookie)

    uid = custom_uid or uid
    user_locale = await get_user_locale(user_id, db)
    client.lang = to_genshin_py(user_locale or locale) or "en-us"
    client.default_game = genshin.Game.GENSHIN
    client.uid = uid
    china = True if str(uid)[0] in ["1", "2", "5"] else False
    if china:
        client.lang = "zh-cn"

    user_obj = ShenheUser(
        client=client,
        uid=uid,
        discord_user=discord_user,
        user_locale=user_locale,
        china=china,
        daily_checkin=True if daily_checkin == 1 else False,
    )
    return user_obj


async def get_uid(user_id: int, db: aiosqlite.Connection) -> int | None:
    c = await db.cursor()
    await c.execute(
        "SELECT uid, current FROM user_accounts WHERE user_id = ?",
        (user_id,),
    )
    uid = await c.fetchall()
    for _, tpl in enumerate(uid):
        uid = tpl[0]
        if tpl[1] == 1:
            break
    return uid


async def load_and_update_enka_cache(
    cache: enkanetwork.EnkaNetworkResponse,
    data: enkanetwork.EnkaNetworkResponse,
    uid: int,
    en: bool = False,
) -> enkanetwork.EnkaNetworkResponse:
    if data.characters is None:
        raise ValueError("No characters found in data")
    if cache is None or cache.characters is None:
        cache = data
    c_dict = {}
    d_dict = {}
    new_dict = {}
    for c in cache.characters:
        c_dict[c.id] = c
    for d in data.characters:
        d_dict[d.id] = d
    new_dict = c_dict | d_dict
    cache.characters = []
    for character in list(new_dict.values()):
        cache.characters.append(character)
    cache.player = data.player

    if en:
        cache_path = "data/cache/enka_eng_cache"
    else:
        cache_path = "data/cache/enka_data_cache"
    with FanoutCache(cache_path) as enka_cache:
        enka_cache[uid] = cache

    return cache


async def get_farm_data(i: discord.Interaction, weekday: int):
    result = []
    user_locale = await get_user_locale(i.user.id, i.client.db)
    locale = user_locale or i.locale
    ambr = AmbrTopAPI(i.client.session, to_ambr_top(locale))
    domains = await ambr.get_domain()
    character_upgrades = await ambr.get_character_upgrade()
    weapon_upgrades = await ambr.get_weapon_upgrade()
    today_domains = []
    for domain in domains:
        if domain.weekday == weekday:
            today_domains.append(domain)
    for domain in today_domains:
        characters: Dict[int, Character] = {}
        for reward in domain.rewards:
            for upgrade in character_upgrades:
                if '10000005' in upgrade.character_id:
                    continue
                for item in upgrade.items:
                    if item.id == reward.id:
                        characters[upgrade.character_id] = (
                            await ambr.get_character(str(upgrade.character_id))
                        )[0]
        weapons: Dict[int, Weapon] = {}
        for reward in domain.rewards:
            for upgrade in weapon_upgrades:
                for item in upgrade.items:
                    if item.id == reward.id:
                        [weapon] = await ambr.get_weapon(id=str(upgrade.weapon_id))
                        if not weapon.default_icon:
                            weapons[upgrade.weapon_id] = weapon
        # merge two dicts
        items = characters | weapons
        chunks = list(divide_dict(items, 12))
        for chunk in chunks:
            result.append({"domain": domain, "items": chunk})
    embeds = []
    options = []
    for index, items in enumerate(result):
        embed = default_embed(
            f"{get_weekday_name(weekday, i.locale, user_locale, full_name=True)} {text_map.get(250, i.locale, user_locale)}"
        )
        embed.set_image(url=f"attachment://farm.jpeg")
        embeds.append(embed)
        domain: Domain = items["domain"]
        current_len = 1
        for option in options:
            if get_domain_title(domain, locale) in option.label:
                options[
                    -1
                ].label = f"{get_domain_title(domain, locale)} ({current_len})"
                current_len += 1
        options.append(
            SelectOption(
                label=f"{get_domain_title(domain, locale)} {f'({current_len})' if current_len > 1 else ''}",
                value=index,
                emoji=get_city_emoji(domain.city.id),
                description=domain.rewards[0].name,
            )
        )
    return result, embeds, options


def get_domain_title(domain: Domain, locale: Locale | str):
    if "Forgery" in text_map.get_domain_name(domain.id, "en-US"):
        return f"{domain.city.name} - {text_map.get(91, locale)}"
    elif "Mastery" in text_map.get_domain_name(domain.id, "en-US"):
        return f"{domain.city.name} - {text_map.get(105, locale).title()}"

def convert_ar_to_wl(ar: int) -> int:
    if 1 <= ar <= 19:
        return 0
    elif 20 <= ar < 25:
        return 1
    elif 25 <= ar < 29:
        return 2
    elif 30 <= ar < 35:
        return 3
    elif 35 <= ar < 39:
        return 4
    elif 40 <= ar < 45:
        return 5
    elif 45 <= ar < 50:
        return 6
    elif 50 <= ar < 54:
        return 7
    else:
        return 8

def convert_wl_to_mora(wl: int) -> int:
    if wl == 0:
        return 12000
    elif wl == 1:
        return 20000
    elif wl == 2:
        return 28000
    elif wl == 3:
        return 36000
    elif wl ==4 :
        return 44000
    elif wl == 5:
        return 52000
    else:
        return 60000