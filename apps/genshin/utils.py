import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Literal, Optional, Tuple
import aiohttp
import aiosqlite
import discord
import enkanetwork
import genshin
import yaml
from discord.utils import format_dt
from diskcache import FanoutCache
import sentry_sdk
from ambr.client import AmbrTopAPI
from ambr.models import Character, Domain, Weapon
from apps.genshin.custom_model import (CharacterBuild, EnkanetworkData,
                                       FightProp, ShenheBot, ShenheUser,
                                       WishInfo)
from apps.text_map.cond_text import cond_text
from apps.text_map.convert_locale import to_ambr_top, to_enka, to_genshin_py
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import (get_user_locale, get_weekday_name,
                                 translate_main_stat)
from data.game.artifact_map import artifact_map
from data.game.character_map import character_map
from data.game.fight_prop import fight_prop
from data.game.weapon_map import weapon_map
from utility.utils import (default_embed, divide_chunks, divide_dict,
                           error_embed, get_dt_now)


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
    character_id: str, element_builds_dict: dict, locale: discord.Locale | str
) -> List[CharacterBuild]:
    """Gets a character's builds

    Args:
        character_id (int): the id of the character
        element_builds_dict (dict): the dictionary of all characters of a given element, this is stored in data/builds
        locale (Locale): the discord locale
        user_locale (str): the user locale

    Returns:
        List[CharacterBuild]
    """
    character_name = text_map.get_character_name(character_id, "zh-TW")
    translated_character_name = text_map.get_character_name(character_id, locale)
    count = 1
    result = []

    for build in element_builds_dict[character_name]["builds"]:
        stat_str = ""
        for stat, value in build["stats"].items():
            stat_str += f"{cond_text.get_text(str(locale), 'build', stat)} ➜ {str(value).replace('任意', 'ANY')}\n"
        move_text = cond_text.get_text(
            str(locale), "build", f"{character_name}_{build['move']}"
        )
        weapon_id = text_map.get_id_from_name(build["weapon"])
        if weapon_id is None:
            raise ValueError(f"Unknown weapon {build['weapon']}")
        embed = default_embed(
            f"{translated_character_name} - {text_map.get(90, locale)}{count}",
            f"{text_map.get(91, locale)} • {get_weapon_emoji(weapon_id)} {text_map.get_weapon_name(weapon_id, locale)}\n"
            f"{text_map.get(92, locale)} • {cond_text.get_text(str(locale), 'build', build['artifacts'])}\n"
            f"{text_map.get(93, locale)} • {translate_main_stat(build['main_stats'], locale)}\n"
            f"{text_map.get(94, locale)} • {build['talents']}\n"
            f"{move_text} • {str(build['dmg']).replace('任意', 'ANY')}\n\n",
        )
        embed.add_field(name=text_map.get(95, locale), value=stat_str)
        count += 1
        embed.set_thumbnail(url=get_character_icon(str(character_id)))
        embed.set_footer(
            text=f"{text_map.get(96, locale)}: https://bbs.nga.cn/read.php?tid=25843014"
        )
        result.append(
            CharacterBuild(
                embed=embed,
                weapon=build["weapon"],
                artifact=build["artifacts"],
                is_thought=False,
            )
        )

    if "thoughts" in element_builds_dict[character_name]:
        count = 1
        embed = default_embed(text_map.get(97, locale))
        for _ in element_builds_dict[character_name]["thoughts"]:
            embed.add_field(
                name=f"#{count}",
                value=cond_text.get_text(
                    str(locale), "build", f"{character_name}_thoughts_{count-1}"
                ),
                inline=False,
            )
            count += 1
        embed.set_thumbnail(url=get_character_icon(str(character_id)))
        result.append(CharacterBuild(embed=embed, is_thought=True))

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


def get_fight_prop(id: str) -> FightProp:
    fight_prop_dict = fight_prop.get(
        id,
        {
            "name": "未知角色數據",
            "emoji": "",
            "substat": False,
            "text_map_hash": 700,
        },
    )
    return FightProp(**fight_prop_dict)


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


def get_uid_region_name(uid: int) -> int:
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


def get_uid_tz(uid: Optional[int]) -> Literal[0, -13, -7]:
    str_uid = str(uid)
    region_map = {
        "6": -13, # North America
        "7": -7, # Europe
    }
    return region_map.get(str_uid[0], 0)


async def get_shenhe_user(
    user_id: int,
    db: aiosqlite.Connection,
    bot: ShenheBot,
    locale: Optional[discord.Locale | str] = None,
    cookie: Optional[Dict[str, str | int]] = None,
    custom_uid: Optional[int] = None,
    daily_checkin: int = 1,
    author_locale: Optional[discord.Locale | str] = None,
) -> ShenheUser:
    discord_user = bot.get_user(user_id) or await bot.fetch_user(user_id)
    if not cookie:
        async with db.execute(
            "SELECT ltuid, ltoken, cookie_token, uid, china, current FROM user_accounts WHERE user_id = ?",
            (user_id,),
        ) as c:
            user_data = None
            async for row in c:
                if row[5] == 1:
                    user_data = row
                    break
                else:
                    user_data = row
        
        if user_data is None:
            sentry_sdk.capture_message(f"[Get Shenhe User]User {user_id} has no Shenhe Account")
            raise ValueError(f"User {user_id} has no Shenhe Account")

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
        client.uid = user_data[3]
        await c.close()
    else:
        client = genshin.Client()
        client.set_cookies(cookie)
    
    user_locale = await get_user_locale(user_id, db)
    final_locale = author_locale or user_locale or locale
    
    client.lang = to_genshin_py(str(final_locale)) or "en-us"
    client.default_game = genshin.Game.GENSHIN
    client.uid = custom_uid or client.uid
    
    china = True if str(client.uid)[0] in ["1", "2", "5"] else False
    if china:
        client.lang = "zh-cn"
        
    if client.uid is None:
        sentry_sdk.capture_message(f"[Get Shenhe User]User {user_id} has no UID")
        raise ValueError(f"User {user_id} has no UID")

    user_obj = ShenheUser(
        client=client,
        uid=client.uid,
        discord_user=discord_user,
        user_locale=str(final_locale),
        china=china,
        daily_checkin=True if daily_checkin == 1 else False,
    )
    return user_obj


async def get_uid(user_id: int, db: aiosqlite.Connection) -> Optional[int]:
    async with db.execute(
        "SELECT uid, current FROM user_accounts WHERE user_id = ?",
        (user_id,),
    ) as c:
        uid = None
        async for row in c:
            uid = row[0]
            if row[1] == 1:
                break
        return uid


class NoCharacterFound(Exception):
    pass


async def load_and_update_enka_cache(
    cache: enkanetwork.model.base.EnkaNetworkResponse,
    data: enkanetwork.model.base.EnkaNetworkResponse,
    uid: int,
    en: bool = False,
) -> enkanetwork.model.base.EnkaNetworkResponse:
    if data.characters is None:
        raise NoCharacterFound
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
    if not isinstance(character_upgrades, List) or not isinstance(
        weapon_upgrades, List
    ):
        raise ValueError("Invalid upgrade data")
    today_domains = []
    for domain in domains:
        if domain.weekday == weekday:
            today_domains.append(domain)
    for domain in today_domains:
        characters: Dict[str, Character] = {}
        for reward in domain.rewards:
            for upgrade in character_upgrades:
                if "10000005" in upgrade.character_id:
                    continue
                for item in upgrade.items:
                    if item.id == reward.id:
                        character = await ambr.get_character(upgrade.character_id)
                        if not isinstance(character, Character):
                            raise ValueError("Invalid character data")
                        characters[upgrade.character_id] = character
        weapons: Dict[int, Weapon] = {}
        for reward in domain.rewards:
            for upgrade in weapon_upgrades:
                for item in upgrade.items:
                    if item.id == reward.id:
                        weapon = await ambr.get_weapon(upgrade.weapon_id)
                        if not isinstance(weapon, Weapon):
                            raise ValueError("Invalid weapon data")
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
            discord.SelectOption(
                label=f"{get_domain_title(domain, locale)} {f'({current_len})' if current_len > 1 else ''}",
                value=index,
                emoji=get_city_emoji(domain.city.id),
                description=domain.rewards[0].name,
            )
        )
    return result, embeds, options


def get_domain_title(domain: Domain, locale: discord.Locale | str) -> str:
    if "Forgery" in text_map.get_domain_name(domain.id, "en-US"):
        return f"{domain.city.name} - {text_map.get(91, locale)}"
    else:
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
    elif wl == 4:
        return 44000
    elif wl == 5:
        return 52000
    else:
        return 60000


async def get_wish_history_embed(
    i: discord.Interaction,
    query: str,
    member: Optional[discord.User | discord.Member] = None,
) -> List[discord.Embed]:
    member = member or i.user
    user_locale = await get_user_locale(i.user.id, i.client.db)
    async with i.client.db.execute(
        f"SELECT wish_rarity, wish_time, item_id, pity_pull FROM wish_history WHERE {query} user_id = ? AND uid = ? ORDER BY wish_id DESC",
        (member.id, await get_uid(member.id, i.client.db)),
    ) as cursor:
        wish_history = await cursor.fetchall()

    if not wish_history:
        embed = error_embed(message=text_map.get(75, i.locale, user_locale)).set_author(
            name=text_map.get(648, i.locale, user_locale),
            icon_url=member.display_avatar.url,
        )
        return [embed]
    else:
        user_wish = []

        for _, tpl in enumerate(wish_history):
            user_wish.append(
                format_wish_str(
                    {
                        "item_rarity": tpl[0],
                        "time": tpl[1],
                        "item_id": tpl[2],
                        "pity_pull": tpl[3],
                    },
                    user_locale or i.locale,
                )
            )

        user_wish = list(divide_chunks(user_wish, 20))
        embeds = []
        for small_segment in user_wish:
            embed_str = ""
            for wish_str in small_segment:
                embed_str += f"{wish_str}\n"
            embed = default_embed(message=embed_str)
            embed.set_author(
                name=text_map.get(369, i.locale, user_locale),
                icon_url=member.display_avatar.url,
            )
            embeds.append(embed)

        return embeds


async def get_wish_info_embed(
    i: discord.Interaction,
    locale: str,
    wish_info: WishInfo,
    import_command: bool = False,
    linked: bool = False,
) -> discord.Embed:
    embed = default_embed(
        message=text_map.get(673 if import_command else 690, locale).format(
            a=wish_info.total
        )
    ).set_author(
        name=text_map.get(474 if import_command else 691, locale),
        icon_url=i.user.display_avatar.url,
    )
    embed.add_field(
        name="UID",
        value=text_map.get(674, locale)
        if not linked
        else (await get_uid(i.user.id, i.client.db)),
        inline=False,
    )
    newest_wish = wish_info.newest_wish
    oldest_wish = wish_info.oldest_wish
    embed.add_field(
        name=text_map.get(675, locale),
        value=format_wish_str(
            {
                "time": newest_wish.time,
                "item_rarity": newest_wish.rarity,
                "item_id": text_map.get_id_from_name(newest_wish.name),
            },
            locale,
        ),
        inline=False,
    )
    embed.add_field(
        name=text_map.get(676, locale),
        value=format_wish_str(
            {
                "time": oldest_wish.time,
                "item_rarity": oldest_wish.rarity,
                "item_id": text_map.get_id_from_name(oldest_wish.name),
            },
            locale,
        ),
        inline=False,
    )

    embed.add_field(
        name=text_map.get(645, locale),
        value=wish_info.character_banner_num,
        inline=False,
    )
    embed.add_field(
        name=text_map.get(646, locale), value=wish_info.weapon_banner_num, inline=False
    )
    embed.add_field(
        name=text_map.get(655, locale),
        value=wish_info.permanent_banner_num,
        inline=False,
    )
    embed.add_field(
        name=text_map.get(647, locale), value=wish_info.novice_banner_num, inline=False
    )

    return embed


def format_wish_str(wish_data: Dict, locale: discord.Locale | str):
    wish_time = datetime.strptime(wish_data["time"], "%Y/%m/%d %H:%M:%S")
    item_emoji = get_weapon_emoji(int(wish_data["item_id"])) or get_character_emoji(
        str(wish_data["item_id"])
    )
    pity_pull = f"#{wish_data['pity_pull']}" if "pity_pull" in wish_data else ""
    return f"{format_dt(wish_time, 'd')} {item_emoji} **{text_map.get_character_name(wish_data['item_id'], locale) or text_map.get_weapon_name(wish_data['item_id'], locale)}** ({wish_data['item_rarity']} ✦) {pity_pull}"


def get_account_options(
    accounts: List[Tuple], locale: str
) -> List[discord.SelectOption]:
    options = []
    for account in accounts:
        emoji = (
            "<:cookie_add:1018776813922693120>"
            if account[1] is not None
            else "<:number:1018838745614667817>"
        )
        nickname = f"{account[3]} | " if account[3] is not None else ""
        if len(nickname) > 15:
            nickname = nickname[:15] + "..."
        options.append(
            discord.SelectOption(
                label=f"{nickname}{account[0]} | {text_map.get(get_uid_region_name(account[0]), locale)}",
                emoji=emoji,
                value=account[0],
            )
        )
    return options


def level_to_ascension_phase(level: int) -> int:
    if level <= 20:
        return 0
    elif level <= 40:
        return 1
    elif level <= 50:
        return 2
    elif level <= 60:
        return 3
    elif level <= 70:
        return 4
    elif level <= 80:
        return 5
    elif level <= 90:
        return 6
    else:
        raise ValueError("Level is too high")


class InvalidLevelInput(Exception):
    pass


async def validate_level_input(
    target: str,
    a: str,
    e: str,
    q: str,
    i: discord.Interaction,
    locale: discord.Locale | str,
):
    try:
        int_target = int(target)
        int_a = int(a)
        int_e = int(e)
        int_q = int(q)
    except ValueError:
        await i.followup.send(
            embed=error_embed(message=text_map.get(187, locale)).set_author(
                name=text_map.get(190, locale), icon_url=i.user.display_avatar.url
            ),
            ephemeral=True,
        )
        raise InvalidLevelInput
    if int_target < 1 or int_target > 90:
        await i.followup.send(
            embed=error_embed(
                message=text_map.get(172, locale).format(a=1, b=90)
            ).set_author(
                name=text_map.get(190, locale), icon_url=i.user.display_avatar.url
            ),
            ephemeral=True,
        )
        raise InvalidLevelInput
    if int_a < 1 or int_a > 15 or int_e < 1 or int_e > 15 or int_q < 1 or int_q > 15:
        await i.followup.send(
            embed=error_embed(
                message=text_map.get(172, locale).format(a=1, b=15)
            ).set_author(
                name=text_map.get(190, locale), icon_url=i.user.display_avatar.url
            ),
            ephemeral=True,
        )
        raise InvalidLevelInput


async def get_character_suggested_talent_levels(
    character_id: str, session: aiohttp.ClientSession
) -> List[int]:
    chinese_character_name = text_map.get_character_name(character_id, "zh-TW")
    ambr = AmbrTopAPI(session)
    character = await ambr.get_character(character_id)
    if not isinstance(character, Character):
        return [1, 1, 1]
    with open(f"data/builds/{character.element.lower()}.yaml") as f:
        builds = yaml.safe_load(f)
    character_build = builds.get(chinese_character_name)
    if character_build is None:
        return [1, 1, 1]
    talents = builds[chinese_character_name]["builds"][0]["talents"]  # 2/2/2
    talents = talents.split("/")
    return [int(talent) for talent in talents]


async def get_enka_data(
    i: discord.Interaction,
    locale: discord.Locale | str,
    uid: int,
    member: discord.Member | discord.User,
    respond_message: bool = True,
) -> Optional[EnkanetworkData]:
    """Get and return enka data from enka.network, will return None if there is an error

    Args:
        i (discord.Interaction): Interaction object
        locale (discord.Locale | str): discord locale
        uid (int): user's uid
        member (discord.Member | discord.User): discord member object

    Returns:
        Tuple[enkanetwork.EnkaNetworkResponse, enkanetwork.EnkaNetworkResponse]: First element is the user's data in user's locale, second one is the user's data in en-US
    """
    with FanoutCache("data/cache/enka_data_cache") as enka_cache:
        cache: enkanetwork.model.base.EnkaNetworkResponse = enka_cache.get(uid)
    with FanoutCache("data/cache/enka_eng_cache") as enka_cache:
        eng_cache: enkanetwork.model.base.EnkaNetworkResponse = enka_cache.get(uid)
    enka_locale = to_enka(locale)
    async with enkanetwork.EnkaNetworkAPI(enka_locale) as enka:
        try:
            data = await enka.fetch_user(uid)
            await enka.set_language(enkanetwork.Language.EN)
            eng_data = await enka.fetch_user(uid)
        except (
            enkanetwork.UIDNotFounded,
            asyncio.exceptions.TimeoutError,
            enkanetwork.EnkaServerError,
        ):
            if cache is None:
                if respond_message:
                    await i.followup.send(
                        embed=error_embed(message=text_map.get(519, locale)).set_author(
                            name=text_map.get(286, locale),
                            icon_url=member.display_avatar.url,
                        ),
                        ephemeral=True,
                    )
                return None
            else:
                data = cache
                eng_data = eng_cache
        except enkanetwork.VaildateUIDError:
            if respond_message:
                await i.followup.send(
                    embed=error_embed().set_author(
                        name=text_map.get(286, locale),
                        icon_url=member.display_avatar.url,
                    ),
                    ephemeral=True,
                )
                return None
            else:
                return None
    try:
        cache = await load_and_update_enka_cache(cache, data, uid)
        eng_cache = await load_and_update_enka_cache(eng_cache, eng_data, uid, en=True)
    except NoCharacterFound:
        embed = (
            default_embed(message=text_map.get(287, locale))
            .set_author(
                name=text_map.get(141, locale),
                icon_url=member.display_avatar.url,
            )
            .set_image(url="https://i.imgur.com/frMsGHO.gif")
        )
        if respond_message:
            await i.followup.send(embed=embed, ephemeral=True)
            return None
        else:
            return None
    return EnkanetworkData(
        data=data,
        eng_data=eng_data,
        cache=enkanetwork.model.base.EnkaNetworkResponse(
            playerInfo=cache.player, avatarInfoList=cache.characters
        ),
        eng_cache=enkanetwork.model.base.EnkaNetworkResponse(
            playerInfo=eng_cache.player, avatarInfoList=eng_cache.characters
        ),
    )

def get_current_abyss_season():
    start_season = 59
    start_seasson_dt = datetime(2022, 12, 1, 4, 0, 0)
    
    # calculate time difference
    now = get_dt_now()
    diff = now - start_seasson_dt
    
    # calculate season
    # 1 season = 16 days
    season = start_season + (diff.days // 15)
    
    return season

def get_abyss_season_date_range(season: int) -> str:
    """Get the date range of a given season"""
    
    season_num = 59
    season_start = datetime(2022, 12, 1, 4, 0, 0) + timedelta(days=15 * (season_num - season))
    season_end = season_start + timedelta(days=15)
    
    return f"{season_start.strftime('%Y-%m-%d')} ~ {season_end.strftime('%Y-%m-%d')}"