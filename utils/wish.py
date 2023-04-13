import typing

import discord

import dev.asset as asset
from apps.text_map import text_map
from apps.wish.models import WishHistory, WishInfo
from dev.models import DefaultEmbed, ErrorEmbed, Inter

from .db import get_user_lang
from .general import divide_chunks
from .genshin import get_character_emoji, get_uid, get_weapon_emoji


async def get_wish_history_embeds(
    i: Inter,
    query: str,
    member: typing.Optional[discord.User | discord.Member] = None,
) -> typing.List[discord.Embed]:
    member = member or i.user
    user_locale = await get_user_lang(i.user.id, i.client.pool)

    pool = i.client.pool
    rows = await pool.fetch(
        f"""
        SELECT *
        FROM wish_history
        WHERE {query} user_id = $1 AND uid = $2
        ORDER BY wish_id DESC
        """,
        member.id,
        await get_uid(member.id, pool),
    )
    histories = [WishHistory.from_row(row) for row in rows]

    if not histories:
        embed = ErrorEmbed(
            description=text_map.get(75, i.locale, user_locale)
        ).set_author(
            name=text_map.get(648, i.locale, user_locale),
            icon_url=member.display_avatar.url,
        )
        return [embed]
    user_wish: typing.List[str] = []
    for wish in histories:
        user_wish.append(
            format_wish_str(
                wish,
                user_locale or i.locale,
            )
        )

    div_wish: typing.List[typing.List[str]] = list(divide_chunks(user_wish, 20))

    embeds: typing.List[discord.Embed] = []
    for small_segment in div_wish:
        description = "\n".join(small_segment)
        embed = DefaultEmbed(description=description)
        embed.set_author(
            name=text_map.get(369, i.locale, user_locale),
            icon_url=member.display_avatar.url,
        )
        embeds.append(embed)

    return embeds


async def get_wish_info_embed(
    i: Inter,
    locale: str,
    wish_info: WishInfo,
    *,
    import_command: bool = False,
) -> discord.Embed:
    embed = DefaultEmbed(
        description=text_map.get(673 if import_command else 690, locale).format(
            a=wish_info.total
        )
    )
    embed.set_title(474 if import_command else 691, locale, i.user)

    uid = await get_uid(i.user.id, i.client.pool)
    linked = uid is not None
    embed.add_field(
        name="UID",
        value=text_map.get(674, locale) if not linked else str(uid),
        inline=False,
    )

    newest_wish = wish_info.newest_wish
    oldest_wish = wish_info.oldest_wish
    for index, wish in enumerate((newest_wish, oldest_wish)):
        embed.add_field(
            name=text_map.get(675 + index, locale),
            value=format_wish_str(
                wish,
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


def format_wish_str(wish: WishHistory, locale: discord.Locale | str) -> str:
    if wish.item_id is not None:
        emoji = get_character_emoji(str(wish.item_id)) or get_weapon_emoji(wish.item_id)
        name = text_map.get_character_name(
            str(wish.item_id), locale
        ) or text_map.get_weapon_name(int(wish.item_id), locale)
    else:
        emoji = ""
        name = wish.name

    if wish.rarity == 3:
        rarity_emoji = asset.three_star_emoji
    elif wish.rarity == 4:
        rarity_emoji = asset.four_star_emoji
    else:
        rarity_emoji = asset.five_star_emoji
        name = f"**{name}**"

    dt_str = discord.utils.format_dt(wish.time, "d")
    pity = f"__(#{wish.pity})__" if wish.pity else ""
    result_str = f"{wish.rarity} {rarity_emoji} - {emoji} {name} {pity} | {dt_str}"

    return result_str
