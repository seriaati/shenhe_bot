import typing

import aiohttp
import asyncpg
import discord

from apps.genshin import get_character_fanarts
from apps.text_map import text_map
from models import CustomInteraction, DefaultEmbed, UserCustomImage


async def get_user_custom_image_options(
    character_id: int,
    pool: asyncpg.Pool,
    user_id: int,
    locale: typing.Union[discord.Locale, str],
) -> typing.List[discord.SelectOption]:
    c_fanarts = await get_character_fanarts(str(character_id))

    rows = await pool.fetch(
        """
        SELECT
            nickname, image_url, current
        FROM
            custom_image
        WHERE
            user_id = $1 AND character_id = $2
        """,
        user_id,
        character_id,
    )
    options: typing.List[discord.SelectOption] = [
        discord.SelectOption(
            label=text_map.get(124, locale), value="default", default=bool(not rows)
        )
    ]
    current_image_url = None
    for row in rows:
        if row["current"]:
            current_image_url = row["image_url"]
        if row["image_url"] in c_fanarts:
            continue
        options.append(
            discord.SelectOption(
                label=row["nickname"][:100],
                description=row["image_url"][:100],
                value=row["image_url"],
                default=row["current"],
            )
        )

    index = 1
    for url in c_fanarts:
        if any(option.value == url for option in options):
            continue
        label = f"{text_map.get(748, locale)} ({index})"
        options.append(
            discord.SelectOption(
                label=label,
                description=url,
                value=url,
                default=current_image_url == url,
            )
        )
        index += 1

    return options


async def get_user_custom_image_embed(
    i: CustomInteraction,
    locale: discord.Locale | str,
    character_id: str,
    custom_image: typing.Optional[UserCustomImage] = None,
    from_settings: bool = True,
) -> discord.Embed:
    embed = DefaultEmbed(
        description=text_map.get(412, locale) if not from_settings else ""
    )
    embed.set_author(
        name=text_map.get(59, locale).format(
            character_name=text_map.get_character_name(character_id, locale)
        ),
        icon_url=i.user.display_avatar.url,
    )
    if custom_image is not None:
        embed.add_field(
            name=f"{text_map.get(277, locale)}: {custom_image.nickname}",
            value=custom_image.url,
        )
        embed.set_image(url=custom_image.url)
    if custom_image is not None and not (
        await validate_image_url(custom_image.url, i.client.session)
    ):
        embed.set_image(url=None)
        embed.set_footer(text=text_map.get(274, locale))
    return embed


async def validate_image_url(url: str, session: aiohttp.ClientSession) -> bool:
    if "jpg" not in url and "png" not in url and "jpeg" not in url:
        return False
    try:
        async with session.get(url=url) as response:
            return response.status == 200
    except aiohttp.InvalidURL:
        return False


async def change_user_custom_image(
    user_id: int, character_id: int, image_url: str, pool: asyncpg.Pool
) -> None:
    await pool.execute(
        """
        UPDATE
            custom_image
        SET
            current = false
        WHERE
            user_id = $1 AND character_id = $2
        """,
        user_id,
        character_id,
    )
    result = await pool.execute(
        """
        UPDATE
            custom_image
        SET
            current = true
        WHERE
            user_id = $1 AND character_id = $2 AND image_url = $3
        """,
        user_id,
        character_id,
        image_url,
    )
    if result == "UPDATE 0" and image_url != "default":
        await pool.execute(
            """
            INSERT INTO
                custom_image (user_id, character_id, image_url, nickname, from_shenhe)
            VALUES
                ($1, $2, $3, $4, true)
            """,
            user_id,
            character_id,
            image_url,
            image_url.split("/")[-1],
        )


async def get_user_custom_image(
    user_id: int, character_id: int, pool: asyncpg.Pool
) -> typing.Optional[UserCustomImage]:
    image: typing.Optional[asyncpg.Record] = await pool.fetchrow(
        """
        SELECT
            user_id, character_id, image_url, nickname, from_shenhe
        FROM
            custom_image
        WHERE
            user_id = $1 AND character_id = $2 AND current = true
        """,
        user_id,
        character_id,
    )
    if image is None:
        return None

    from_shenhe = image["from_shenhe"]
    if from_shenhe is None:
        fanarts = await get_character_fanarts(str(character_id))
        if image["image_url"] in fanarts:
            from_shenhe = True
            await pool.execute(
                """
                UPDATE
                    custom_image
                SET
                    from_shenhe = true
                WHERE
                    user_id = $1 AND character_id = $2 AND image_url = $3
                """,
                user_id,
                character_id,
                image["image_url"],
            )
        else:
            from_shenhe = False

    return UserCustomImage(
        user_id=image["user_id"],
        character_id=image["character_id"],
        url=image["image_url"],
        nickname=image["nickname"],
        from_shenhe=from_shenhe,
    )


async def add_user_custom_image(
    user_id: int,
    character_id: int,
    image_url: str,
    nickname: str,
    pool: asyncpg.Pool,
) -> None:
    await pool.execute(
        """
            UPDATE
                custom_image
            SET
                current = false
            WHERE
                user_id = $1 AND character_id = $2
            """,
        user_id,
        character_id,
    )
    await pool.execute(
        """
        INSERT INTO
            custom_image (user_id, character_id, image_url, nickname, current)
        VALUES
            ($1, $2, $3, $4, true)
        """,
        user_id,
        character_id,
        image_url,
        nickname,
    )


async def remove_user_custom_image(
    user_id: int, image_url: str, character_id: int, pool: asyncpg.Pool
) -> None:
    await pool.execute(
        """
        DELETE FROM
            custom_image
        WHERE
            user_id = $1 AND image_url = $2 AND character_id = $3
        """,
        user_id,
        image_url,
        character_id,
    )
    image: typing.Optional[asyncpg.Record] = await pool.fetchrow(
        """
        SELECT
            user_id, character_id, image_url, nickname
        FROM
            custom_image
        WHERE
            user_id = $1 AND character_id = $2
        LIMIT 1
        """,
        user_id,
        character_id,
    )
    if image is not None:
        await pool.execute(
            """
            UPDATE
                custom_image
            SET
                current = true
            WHERE
                user_id = $1 AND character_id = $2 AND image_url = $3
            """,
            user_id,
            character_id,
            image["image_url"],
        )
