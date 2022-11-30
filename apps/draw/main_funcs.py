import functools
import io
from typing import Dict, List, Optional, Tuple

import discord
import enkanetwork
import genshin

from ambr.models import Character, Domain, Material, Weapon
from apps.draw.draw_funcs import abyss, farm, profile, remind, stats
from apps.draw.utility import (
    calculate_time,
    download_images,
    extract_urls,
    get_l_character_data,
)
from apps.genshin.custom_model import DrawInput, LeaderboardResult


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
):
    urls = extract_urls(list(items.values()))
    await download_images(urls, input.session)
    func = functools.partial(farm.draw_domain_card, domain, input.locale, items)
    return await input.loop.run_in_executor(None, func)


@calculate_time
async def draw_character_card(
    input: DrawInput,
    character: enkanetwork.model.CharacterInfo,
    custom_image_url: Optional[str] = None,
):
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
):
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
):
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
):
    urls = [c.image.icon.url for c in data.characters]
    urls.append(data.player.namecard.banner.url)
    urls.append(data.player.avatar.icon.url)
    for c in data.characters:
        for t in c.skills:
            urls.append(t.icon.url)
    await download_images(urls, input.session)
    func = functools.partial(profile.overview_and_characters, data, input.dark_mode, input.locale)
    return await input.loop.run_in_executor(None, func)