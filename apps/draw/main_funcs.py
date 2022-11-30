import functools
import io
from typing import Dict, List, Optional, Tuple

import discord
import enkanetwork
import genshin

from ambr.models import Character, Domain, Material, Weapon
from apps.draw.draw_funcs import (abyss, check, diary, farm, profile, remind,
                                  stats, wish, todo, characters)
from apps.draw.utility import (calculate_time, download_images, extract_urls,
                               get_l_character_data)
from apps.genshin.custom_model import CharacterUsageResult, DrawInput, LeaderboardResult, UsageCharacter, WishData


@calculate_time
async def draw_abyss_one_page(
    input: DrawInput,
    user_stats: genshin.models.PartialGenshinUserStats,
    abyss_data: genshin.models.SpiralAbyss,
    user_characters: List[genshin.models.Character],
) -> io.BytesIO:
    urls = extract_urls(user_characters)
    await download_images(urls, input.session)
    func = functools.partial(
        abyss.one_page,
        user_stats,
        abyss_data,
        input.locale,
        input.dark_mode,
        user_characters,
    )
    return await input.loop.run_in_executor(None, func)


@calculate_time
async def draw_single_strike_leaderboard(
    input: DrawInput,
    current_uid: int,
    data: List[Tuple],
) -> LeaderboardResult:
    characters = [get_l_character_data(d[1]) for d in data]
    urls = extract_urls(characters)
    await download_images(urls, input.session)
    func = functools.partial(
        abyss.strike_leaderboard, input.dark_mode, current_uid, data, input.locale
    )
    return await input.loop.run_in_executor(None, func)


@calculate_time
async def draw_farm_domain_card(
    input: DrawInput,
    domain: Domain,
    items: Dict[int, Character | Weapon],
) -> io.BytesIO:
    urls = extract_urls(list(items.values()))
    await download_images(urls, input.session)
    func = functools.partial(farm.draw_domain_card, domain, input.locale, items)
    return await input.loop.run_in_executor(None, func)


@calculate_time
async def draw_character_card(
    input: DrawInput,
    character: enkanetwork.model.CharacterInfo,
    custom_image_url: Optional[str] = None,
) -> Optional[io.BytesIO]:
    urls: List[str] = []
    for e in character.equipments:
        urls.append(e.detail.icon.url)
    if custom_image_url is not None:
        urls.append(custom_image_url)
    await download_images(urls, input.session)
    func = functools.partial(
        profile.character_card,
        character,
        input.locale,
        input.dark_mode,
        custom_image_url,
    )
    return await input.loop.run_in_executor(None, func)


@calculate_time
async def draw_stats_card(
    input: DrawInput,
    namecard: enkanetwork.Namecard,
    user_stats: genshin.models.Stats,
    pfp: discord.Asset,
    character_num: int,
) -> io.BytesIO:
    urls = [namecard.banner.url, pfp.url]
    await download_images(urls, input.session)
    func = functools.partial(
        stats.card, user_stats, namecard, pfp, character_num, input.dark_mode
    )
    return await input.loop.run_in_executor(None, func)


@calculate_time
async def draw_reminder_card(
    input: DrawInput,
    materials: List[Material],
    type: str,
) -> io.BytesIO:
    urls = extract_urls(materials)
    await download_images(urls, input.session)
    func = functools.partial(
        remind.card, materials, input.locale, input.dark_mode, type
    )
    return await input.loop.run_in_executor(None, func)


@calculate_time
async def draw_profile_card(
    input: DrawInput,
    data: enkanetwork.model.base.EnkaNetworkResponse,
) -> Tuple[io.BytesIO, io.BytesIO]:
    urls = [c.image.icon.url for c in data.characters]
    urls.append(data.player.namecard.banner.url)
    urls.append(data.player.avatar.icon.url)
    for c in data.characters:
        for t in c.skills:
            urls.append(t.icon.url)
    await download_images(urls, input.session)
    func = functools.partial(
        profile.overview_and_characters, data, input.dark_mode, input.locale
    )
    return await input.loop.run_in_executor(None, func)


@calculate_time
async def draw_realtime_card(
    input: DrawInput,
    note: genshin.models.Notes,
) -> io.BytesIO:
    urls = [e.character.icon for e in note.expeditions]
    await download_images(urls, input.session)
    func = functools.partial(check.card, note, input.locale, input.dark_mode)
    return await input.loop.run_in_executor(None, func)


@calculate_time
async def draw_wish_overview_card(
    input: DrawInput,
    wish_data: WishData,
    pfp: str,
    user_name: str,
) -> io.BytesIO:
    urls = [pfp]
    for w in wish_data.recents:
        if w.icon is not None:
            urls.append(w.icon)
    await download_images(urls, input.session)
    func = functools.partial(
        wish.overview, input.locale, wish_data, pfp, user_name, input.dark_mode
    )
    return await input.loop.run_in_executor(None, func)


@calculate_time
async def draw_area_card(
    input: DrawInput, explorations: List[genshin.models.Exploration]
) -> io.BytesIO:
    func = functools.partial(stats.area, explorations, input.dark_mode)
    return await input.loop.run_in_executor(None, func)


@calculate_time
async def draw_abyss_overview_card(
    input: DrawInput,
    abyss_data: genshin.models.SpiralAbyss,
    user_data: genshin.models.PartialGenshinUserStats,
) -> io.BytesIO:
    characters = [
        abyss_data.ranks.most_bursts_used[0],
        abyss_data.ranks.most_skills_used[0],
        abyss_data.ranks.strongest_strike[0],
        abyss_data.ranks.most_kills[0],
        abyss_data.ranks.most_damage_taken[0],
        abyss_data.ranks.most_played[:4],
    ]
    urls = extract_urls(characters)
    await download_images(urls, input.session)
    func = functools.partial(
        abyss.overview, input.locale, input.dark_mode, abyss_data, user_data
    )
    return await input.loop.run_in_executor(None, func)


@calculate_time
async def draw_abyss_floor_card(
    input: DrawInput,
    floor: genshin.models.Floor,
    characters: List[genshin.models.Character],
) -> io.BytesIO:
    urls = extract_urls(characters)
    await download_images(urls, input.session)
    func = functools.partial(abyss.floor, input.dark_mode, floor, characters)
    return await input.loop.run_in_executor(None, func)

@calculate_time
async def draw_diary_card(
    input: DrawInput,
    diary_data: genshin.models.Diary,
    user_data: genshin.models.PartialGenshinUserStats,
    month: int,
) -> io.BytesIO:
    func = functools.partial(
        diary.card, diary_data, user_data, input.locale, month, input.dark_mode
    )
    return await input.loop.run_in_executor(None, func)

@calculate_time
async def draw_material_card(
    input: DrawInput,
    materials: List[Tuple[Material, int | str]],
    title: str,
    draw_title: bool = True,
    background_color: Optional[str] = None,
) -> io.BytesIO:
    urls = extract_urls([m[0] for m in materials])
    await download_images(urls, input.session)
    func = functools.partial(todo.material_card, materials, title, input.dark_mode, input.locale, draw_title, background_color)
    return await input.loop.run_in_executor(None, func)

@calculate_time
async def abyss_character_usage_card(
    input: DrawInput,
    uc_list: List[UsageCharacter],
) -> CharacterUsageResult:
    urls = extract_urls([c.character for c in uc_list])
    await download_images(urls, input.session)
    func = functools.partial(abyss.character_usage, uc_list, input.dark_mode)
    return await input.loop.run_in_executor(None, func)

@calculate_time
async def character_card(
    input: DrawInput,
    character_list: List[genshin.models.Character],
    element: str,
    custom_title: Optional[str] = None,
) -> io.BytesIO:
    urls = extract_urls(character_list)
    await download_images(urls, input.session)
    func = functools.partial(characters.card, character_list, input.dark_mode, input.locale, element, custom_title)
    return await input.loop.run_in_executor(None, func)