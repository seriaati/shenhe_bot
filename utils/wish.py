import typing

import discord

import dev.asset as asset
from apps.db.tables.user_settings import Settings
from apps.text_map import text_map
from apps.wish.models import WishHistory, WishInfo
from dev.models import DefaultEmbed, ErrorEmbed, Inter
from .general import divide_chunks
from .genshin import get_character_emoji, get_weapon_emoji


async def get_wish_history_embeds(
    i: Inter,
    query: str,
    member: typing.Optional[discord.User | discord.Member] = None,
) -> typing.List[discord.Embed]:
    member = member or i.user
    lang = await i.client.db.settings.get(i.user.id, Settings.LANG) or str(i.locale)
    uid = await i.client.db.users.get_uid(member.id)
    pool = i.client.pool
    rows = await pool.fetch(
        f"""
        SELECT *
        FROM wish_history
        WHERE {query} user_id = $1 AND uid = $2
        ORDER BY wish_id DESC
        """,
        member.id,
        uid,
    )
    histories = [WishHistory(**row) for row in rows]

    if not histories:
        embed = ErrorEmbed(description=text_map.get(75, lang)).set_author(
            name=text_map.get(648, lang),
            icon_url=member.display_avatar.url,
        )
        return [embed]
    user_wish: typing.List[str] = []
    for wish in histories:
        user_wish.append(format_wish_str(wish, lang))

    div_wish: typing.List[typing.List[str]] = list(divide_chunks(user_wish, 20))

    embeds: typing.List[discord.Embed] = []
    for small_segment in div_wish:
        description = "\n".join(small_segment)
        embed = DefaultEmbed(description=description)
        embed.set_author(
            name=text_map.get(369, lang),
            icon_url=member.display_avatar.url,
        )
        embeds.append(embed)

    return embeds


def get_wish_info_embed(
    user: typing.Union[discord.User, discord.Member],
    lang: str,
    wish_info: WishInfo,
    uid: int,
    linked: bool,
    *,
    import_command: bool = False,
) -> discord.Embed:
    embed = DefaultEmbed(
        description=text_map.get(673 if import_command else 690, lang).format(
            a=wish_info.total
        )
    )
    embed.set_title(474 if import_command else 691, lang, user)

    embed.add_field(
        name="UID",
        value=text_map.get(674, lang) if not linked else str(uid),
        inline=False,
    )

    newest_wish = wish_info.newest_wish
    oldest_wish = wish_info.oldest_wish
    for index, wish in enumerate((newest_wish, oldest_wish)):
        embed.add_field(
            name=text_map.get(675 + index, lang),
            value=format_wish_str(
                wish,
                lang,
            ),
            inline=False,
        )

    embed.add_field(
        name=text_map.get(645, lang),
        value=wish_info.character_banner_num,
        inline=False,
    )
    embed.add_field(
        name=text_map.get(646, lang), value=wish_info.weapon_banner_num, inline=False
    )
    embed.add_field(
        name=text_map.get(655, lang),
        value=wish_info.permanent_banner_num,
        inline=False,
    )
    embed.add_field(
        name=text_map.get(647, lang), value=wish_info.novice_banner_num, inline=False
    )

    return embed


def format_wish_str(wish: WishHistory, lang: discord.Locale | str) -> str:
    if wish.item_id is not None:
        emoji = get_character_emoji(str(wish.item_id)) or get_weapon_emoji(wish.item_id)
        name = text_map.get_character_name(
            str(wish.item_id), lang
        ) or text_map.get_weapon_name(int(wish.item_id), lang)
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
