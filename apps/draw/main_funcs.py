import asyncio
import functools
import io
from typing import Dict, List, Optional, Tuple

import asyncpg
import discord
import enkanetwork as enka
import genshin
import matplotlib.pyplot as plt

import apps.draw.draw_funcs as funcs
import dev.models as models
from ambr import Material
from apps.db.json import read_json, write_json
from apps.db.tables.abyss_board import AbyssBoardEntry
from apps.wish.models import RecentWish, WishData
from utils import calculate_time, compress_image_util, download_images, extract_urls


@calculate_time
async def draw_abyss_one_page(
    draw_input: models.DrawInput,
    user_stats: genshin.models.PartialGenshinUserStats,
    abyss_data: genshin.models.SpiralAbyss,
    user_characters: List[genshin.models.Character],
) -> io.BytesIO:
    urls = extract_urls(user_characters)
    await download_images(urls, draw_input.session)
    func = functools.partial(
        funcs.abyss.one_page,
        user_stats,
        abyss_data,
        draw_input.locale,
        draw_input.dark_mode,
        user_characters,
    )
    return await draw_input.loop.run_in_executor(None, func)


@calculate_time
async def draw_single_strike_leaderboard(
    draw_input: models.DrawInput,
    user_uid: int,
    users: List[models.BoardUser[AbyssBoardEntry]],
) -> io.BytesIO:
    urls = [u.entry.character.icon for u in users]
    await download_images(urls, draw_input.session)
    func = functools.partial(
        funcs.abyss.strike_board,
        draw_input.locale,
        draw_input.dark_mode,
        users,
        user_uid,
    )
    return await draw_input.loop.run_in_executor(None, func)


@calculate_time
async def draw_run_leaderboard(
    draw_input: models.DrawInput,
    user_uid: int,
    users: List[models.BoardUser[AbyssBoardEntry]],
) -> io.BytesIO:
    urls = [u.entry.icon for u in users]
    await download_images(urls, draw_input.session)
    func = functools.partial(
        funcs.abyss.full_clear_board,
        draw_input.locale,
        draw_input.dark_mode,
        users,
        user_uid,
    )
    return await draw_input.loop.run_in_executor(None, func)


@calculate_time
async def draw_farm_domain_card(
    draw_input: models.DrawInput,
    farm_data: List[models.FarmData],
) -> io.BytesIO:
    urls: List[str] = []
    domains = [data.domain for data in farm_data]
    rewards = [reward for domain in domains for reward in domain.rewards]
    urls.extend(extract_urls(rewards))

    items = [f.characters for f in farm_data] + [f.weapons for f in farm_data]
    items = [item for sublist in items for item in sublist]
    urls.extend(extract_urls(items))
    await download_images(urls, draw_input.session)

    func = functools.partial(
        funcs.farm.draw_domain_card, farm_data, draw_input.locale, draw_input.dark_mode
    )
    return await draw_input.loop.run_in_executor(None, func)


@calculate_time
async def draw_profile_card_v1(
    draw_input: models.DrawInput,
    character: enka.model.CharacterInfo,
    custom_image_url: Optional[str] = None,
) -> Optional[io.BytesIO]:
    urls: List[str] = []
    for e in character.equipments:
        if e.detail.icon is None:
            continue
        urls.append(e.detail.icon.url)
    if custom_image_url is not None:
        urls.append(custom_image_url)
    await download_images(urls, draw_input.session)
    func = functools.partial(
        funcs.profile.character_card,
        character,
        draw_input.locale,
        draw_input.dark_mode,
        custom_image_url,
    )
    return await draw_input.loop.run_in_executor(None, func)


@calculate_time
async def draw_stats_card(
    draw_input: models.DrawInput,
    namecard: enka.model.assets.NamecardAsset,
    user_stats: genshin.models.Stats,
    pfp: discord.Asset,
    character_num: int,
) -> io.BytesIO:
    urls = [namecard.banner.url, pfp.url]
    await download_images(urls, draw_input.session)
    func = functools.partial(
        funcs.stats.stats_card,
        user_stats,
        namecard,
        pfp,
        character_num,
        draw_input.dark_mode,
    )
    return await draw_input.loop.run_in_executor(None, func)


@calculate_time
async def draw_profile_overview_card(
    draw_input: models.DrawInput,
    data: enka.model.base.EnkaNetworkResponse,
) -> Tuple[io.BytesIO, io.BytesIO]:
    if data.characters is None:
        raise ValueError("No characters found")
    if data.player is None:
        raise ValueError("No player found")

    urls = [c.image.icon.url for c in data.characters if c.image is not None]
    if data.player.namecard.banner is not None:
        urls.append(data.player.namecard.banner.url)
    if data.player.avatar is not None and data.player.avatar.icon is not None:
        urls.append(data.player.avatar.icon.url)
    for c in data.characters:
        for t in c.skills:
            if t.icon is not None:
                urls.append(t.icon.url)
    await download_images(urls, draw_input.session)
    func = functools.partial(
        funcs.profile.overview_and_characters,
        data,
        draw_input.dark_mode,
        draw_input.locale,
    )
    return await draw_input.loop.run_in_executor(None, func)


@calculate_time
async def draw_realtime_card(
    draw_input: models.DrawInput,
    note: genshin.models.Notes,
) -> io.BytesIO:
    urls = [e.character.icon for e in note.expeditions]
    await download_images(urls, draw_input.session)
    func = functools.partial(
        funcs.check.card, note, draw_input.locale, draw_input.dark_mode
    )
    return await draw_input.loop.run_in_executor(None, func)


@calculate_time
async def draw_wish_overview_card(
    draw_input: models.DrawInput,
    wish_data: WishData,
) -> io.BytesIO:
    urls = [w.icon for w in wish_data.recents if w.icon is not None]
    await download_images(urls, draw_input.session)
    func = functools.partial(
        funcs.wish.wish_overview,
        draw_input.locale,
        wish_data,
        draw_input.dark_mode,
    )
    return await draw_input.loop.run_in_executor(None, func)


@calculate_time
async def draw_wish_recents_card(
    draw_input: models.DrawInput,
    wish_recents: List[RecentWish],
) -> io.BytesIO:
    urls = [w.icon for w in wish_recents if w.icon is not None]
    await download_images(urls, draw_input.session)
    func = functools.partial(
        funcs.wish.draw_wish_recents_card,
        draw_input.locale,
        wish_recents,
        draw_input.dark_mode,
    )
    return await draw_input.loop.run_in_executor(None, func)


@calculate_time
async def draw_area_card(
    draw_input: models.DrawInput, explorations: List[genshin.models.Exploration]
) -> io.BytesIO:
    func = functools.partial(funcs.stats.area_card, explorations, draw_input.dark_mode)
    return await draw_input.loop.run_in_executor(None, func)


@calculate_time
async def draw_abyss_overview_card(
    draw_input: models.DrawInput,
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
    await download_images(urls, draw_input.session)
    func = functools.partial(
        funcs.abyss.abyss_overview,
        draw_input.locale,
        draw_input.dark_mode,
        abyss_data,
        user_data,
    )
    return await draw_input.loop.run_in_executor(None, func)


@calculate_time
async def draw_abyss_floor_card(
    draw_input: models.DrawInput,
    floor: genshin.models.Floor,
    characters: List[genshin.models.Character],
) -> io.BytesIO:
    urls = extract_urls(characters)
    await download_images(urls, draw_input.session)
    func = functools.partial(
        funcs.abyss.floor_card, draw_input.dark_mode, floor, characters
    )
    return await draw_input.loop.run_in_executor(None, func)


@calculate_time
async def draw_diary_card(
    draw_input: models.DrawInput,
    diary_data: genshin.models.Diary,
    mora_count: int,
    month: int,
) -> io.BytesIO:
    colors = (
        [
            "#617d9d",
            "#bf6d6a",
            "#bfa36d",
            "#887db4",
            "#8ead85",
            "#488f8e",
            "#b3adaa",
        ]
        if draw_input.dark_mode
        else [
            "#617d9d",
            "#ff8985",
            "#ffd789",
            "#b0a0ef",
            "#B8E4AC",
            "#54BAB9",
            "#EDE4E0",
        ]
    )

    y = [val.amount for val in diary_data.data.categories]
    plot = None
    if sum(y) != 0:
        _, ax = plt.subplots()
        ax.pie(
            y,
            colors=colors,
        )
        plot = io.BytesIO()
        plt.savefig(plot, bbox_inches=None, transparent=True, format="png")
        plt.clf()

    func = functools.partial(
        funcs.diary.card,
        diary_data,
        mora_count,
        draw_input.locale,
        month,
        draw_input.dark_mode,
        plot,
    )
    return await draw_input.loop.run_in_executor(None, func)


@calculate_time
async def draw_material_card(
    draw_input: models.DrawInput,
    materials: List[Tuple[Material, int | str]],
    title: str,
    draw_title: bool = True,
    background_color: Optional[str] = None,
) -> io.BytesIO:
    urls = extract_urls([m[0] for m in materials])
    await download_images(urls, draw_input.session)
    func = functools.partial(
        funcs.todo.material_card,
        materials,
        title,
        draw_input.dark_mode,
        draw_input.locale,
        draw_title,
        background_color,
    )
    return await draw_input.loop.run_in_executor(None, func)


@calculate_time
async def abyss_character_usage_card(
    draw_input: models.DrawInput,
    uc_list: List[models.UsageCharacter],
) -> models.CharacterUsageResult:
    urls = extract_urls([c.character for c in uc_list])
    await download_images(urls, draw_input.session)
    func = functools.partial(
        funcs.abyss.character_usage, uc_list, draw_input.dark_mode, draw_input.locale
    )
    return await draw_input.loop.run_in_executor(None, func)


@calculate_time
async def character_summary_card(
    draw_input: models.DrawInput,
    character_list: List[genshin.models.Character],
    talents: Dict[str, str],
    pool: asyncpg.Pool,
) -> io.BytesIO:
    urls = [c.weapon.icon for c in character_list]
    pc_icons = await read_json(pool, "genshin/pc_icons.json")

    if (
        not pc_icons
        or any(str(c.id) not in pc_icons for c in character_list)
        or any(not pc_icons[str(c.id)] for c in character_list)
    ):
        client = genshin.Client()
        fields = await client.get_lineup_fields()
        pc_icons = {
            str(character.id): character.pc_icon for character in fields.characters
        }
        await write_json(pool, "genshin/pc_icons.json", pc_icons)
    urls.extend([pc_icons[str(c.id)] for c in character_list])

    await download_images(urls, draw_input.session)
    func = functools.partial(
        funcs.characters.character_card,
        character_list,
        talents,
        pc_icons,
        draw_input.dark_mode,
    )
    return await draw_input.loop.run_in_executor(None, func)


@calculate_time
async def draw_lineup_card(
    draw_input: models.DrawInput,
    lineup_preview: genshin.models.LineupPreview,
    character_id: int,
) -> io.BytesIO:
    # download images
    urls = []
    for characters_ in lineup_preview.characters:
        for character in characters_:
            urls.append(character.pc_icon)
            urls.append(character.weapon.icon)
            urls += [a.icon for a in character.artifacts]
    await download_images(urls, draw_input.session)
    func = functools.partial(
        funcs.lineup.card,
        draw_input.dark_mode,
        draw_input.locale,
        lineup_preview,
        character_id,
    )
    return await draw_input.loop.run_in_executor(None, func)


@calculate_time
async def draw_artifact_card(
    draw_input: models.DrawInput,
    arts: List[enka.Equipments],
    character: enka.CharacterInfo,
) -> io.BytesIO:
    urls = [art.detail.icon.url for art in arts]
    urls.append(character.image.icon.url)
    await download_images(urls, draw_input.session)
    func = functools.partial(
        funcs.artifact.draw_artifact_image,
        character,
        arts,
        draw_input.locale,
        draw_input.dark_mode,
    )
    return await draw_input.loop.run_in_executor(None, func)


@calculate_time
async def draw_banner_card(
    draw_input: models.DrawInput, banner_urls: List[str]
) -> io.BytesIO:
    await download_images(banner_urls, draw_input.session)
    func = functools.partial(funcs.banners.card, banner_urls, draw_input.locale)
    return await draw_input.loop.run_in_executor(None, func)


@calculate_time
async def draw_profile_card_v2(
    draw_input: models.DrawInput,
    character: enka.model.CharacterInfo,
    image_url: str,
) -> io.BytesIO:
    weapon = character.equipments[-1]
    artifacts = [
        c for c in character.equipments if c.type is enka.EquipmentsType.ARTIFACT
    ]
    talents = character.skills
    consts = character.constellations

    # download images
    urls: List[str] = []
    urls.append(weapon.detail.icon.url)
    urls.extend([a.detail.icon.url for a in artifacts])
    urls.extend([t.icon.url for t in talents])
    urls.extend([c.icon.url for c in consts])
    urls.append(image_url)
    await download_images(urls, draw_input.session)

    func = functools.partial(
        funcs.profile.card_v2,
        draw_input.locale,
        draw_input.dark_mode,
        character,
        image_url,
    )
    return await draw_input.loop.run_in_executor(None, func)


@calculate_time
async def compress_image(loop: asyncio.AbstractEventLoop, fp: bytes) -> bytes:
    func = functools.partial(compress_image_util, fp)
    return await loop.run_in_executor(None, func)
