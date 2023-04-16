import asyncio
import typing

import aiohttp
import discord
import sentry_sdk
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from apps.db.tables import CustomImage
from apps.text_map import text_map
from dev.models import DefaultEmbed, Inter
from utils import get_character_fanarts


async def get_user_custom_image_options(
    character_id: int,
    engine: AsyncEngine,
    user_id: int,
    locale: typing.Union[discord.Locale, str],
) -> typing.List[discord.SelectOption]:
    """
    Given a character_id, AsyncEngine, user_id, and locale, returns a list of discord.SelectOption objects that
    represent the custom image options available to the user for the character.

    Args:
        character_id (int): The ID of the character.
        engine (AsyncEngine): AsyncEngine instance for making asynchronous SQLAlchemy queries.
        user_id (int): The ID of the user.
        locale (Union[discord.Locale, str]): A discord.Locale object or a string representing the locale.

    Returns:
        List[discord.SelectOption]: A list of discord.SelectOption objects.
    """
    c_fanarts = await get_character_fanarts(str(character_id))

    async with AsyncSession(engine) as s:
        statement = (
            select(CustomImage)
            .where(CustomImage.user_id == user_id)
            .where(CustomImage.character_id == character_id)
        )
        print(await s.stream(statement))
        async for row in await s.stream(statement):
            print(row)
            print(CustomImage.from_orm(row))
        rows = [CustomImage.from_orm(row) async for row in await s.stream(statement)]

    options = [
        discord.SelectOption(
            label=text_map.get(124, locale), value="default", default=bool(not rows)
        )
    ]
    current_image_url = None
    for row in rows:
        if row.current:
            current_image_url = row.image_url
        if row.image_url in c_fanarts:
            continue
        if any(option.value == row.image_url for option in options):
            continue

        options.append(
            discord.SelectOption(
                label=row.nickname[:100],
                description=row.image_url[:100],
                value=row.image_url[:100],
                default=row.current,
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
    i: Inter,
    locale: discord.Locale | str,
    character_id: str,
    image: typing.Optional[CustomImage] = None,
    from_settings: bool = True,
) -> discord.Embed:
    """
    Returns a Discord Embed object containing information about a user's custom image.

    Args:
        i (Inter): The Inter object representing the interaction context.
        locale (discord.Locale | str): The locale to use when formatting text.
        character_id (str): The ID of the character the custom image belongs to.
        image (typing.Optional[CustomImage]): The CustomImage object containing the custom image information.
        from_settings (bool): Whether the embed is being generated from the user's settings or not.

    Returns:
        discord.Embed: The Discord Embed object containing information about the user's custom image.
    """
    embed = DefaultEmbed(
        description=text_map.get(412, locale) if not from_settings else ""
    )
    embed.set_author(
        name=text_map.get(59, locale).format(
            character_name=text_map.get_character_name(character_id, locale)
        ),
        icon_url=i.user.display_avatar.url,
    )
    if image is not None:
        embed.add_field(
            name=f"{text_map.get(277, locale)}: {image.nickname}",
            value=image.image_url,
        )
        embed.set_image(url=image.image_url)
    if image is not None and not (
        await validate_image_url(image.image_url, i.client.session)
    ):
        embed.set_image(url=None)
        embed.set_footer(text=text_map.get(274, locale))
    return embed


async def validate_image_url(url: str, session: aiohttp.ClientSession) -> bool:
    """
    Validates whether the given URL points to a valid image by checking the URL's file extension and making an
    HTTP request to the URL.

    Args:
        url (str): The URL to validate.
        session (aiohttp.ClientSession): The aiohttp ClientSession object used to make the HTTP request.

    Returns:
        bool: True if the URL points to a valid image, False otherwise.
    """
    image_extensions = ("jpg", "png", "jpeg", "gif", "webp")
    if not any(url.endswith(ext) for ext in image_extensions):
        return False

    try:
        async with session.get(url=url) as response:
            return response.status == 200
    except (aiohttp.InvalidURL, aiohttp.ClientConnectorError, asyncio.TimeoutError):
        return False
    except Exception as e:  # skipcq: PYL-W0703
        sentry_sdk.capture_exception(e)
        return False


async def change_user_custom_image(
    user_id: int, character_id: int, image_url: str, engine: AsyncEngine
) -> None:
    """
    Updates the custom image for a user and character in the database with the given image URL.

    Args:
        user_id (int): The ID of the user whose custom image will be updated.
        character_id (int): The ID of the character whose custom image will be updated.
        image_url (str): The URL of the new custom image.
        engine (AsyncEngine): The SQLAlchemy AsyncEngine object used to connect to the database.

    Returns:
        None
    """
    async with AsyncSession(engine) as s, s.begin():
        statement = select(CustomImage).where(
            CustomImage.user_id == user_id and CustomImage.character_id == character_id
        )

        found = False
        async for row in await s.stream(statement):
            row = CustomImage.from_orm(row)
            if row.image_url == image_url:
                row.current = True
                found = True
            else:
                row.current = False
            s.add(row)

        if not found and image_url != "default":
            s.add(
                CustomImage(
                    user_id=user_id,
                    character_id=character_id,
                    image_url=image_url,
                    nickname=image_url.split("/")[-1],
                    current=True,
                    from_shenhe=True,
                )
            )
        await s.commit()


async def get_user_custom_image(
    user_id: int, character_id: int, engine: AsyncEngine
) -> typing.Optional[CustomImage]:
    """Retrieve the custom image for a user's character from the database, and returns the CustomImage object.

    Args:
        user_id (int): The ID of the user whose custom image to retrieve.
        character_id (int): The ID of the character for whom the custom image was created.
        engine (AsyncEngine): The SQLAlchemy AsyncEngine instance used to connect to the database.

    Returns:
        Optional[CustomImage]: The CustomImage object representing the retrieved image, or None if no image is found.
    """
    async with AsyncSession(engine) as s, s.begin():
        statement = select(CustomImage).where(
            CustomImage.user_id == user_id
            and CustomImage.character_id == character_id
            and CustomImage.current == True
        )
        result = await s.execute(statement)
        image = CustomImage.from_orm(result.scalars().first())
        if image.from_shenhe is None:
            fanarts = await get_character_fanarts(str(character_id))
            if image.image_url in fanarts:
                image.from_shenhe = True
            else:
                image.from_shenhe = False
            s.add(image)
            await s.commit()
        return image


async def add_user_custom_image(
    user_id: int,
    character_id: int,
    image_url: str,
    nickname: str,
    engine: AsyncEngine,
) -> None:
    """Add a custom image for a user's character to the database.

    Args:
        user_id (int): The ID of the user who created the custom image.
        character_id (int): The ID of the character for whom the custom image was created.
        image_url (str): The URL of the image to add.
        nickname (str): The nickname for the custom image.
        engine (AsyncEngine): The SQLAlchemy AsyncEngine instance used to connect to the database.

    Returns:
        None.
    """
    async with AsyncSession(engine) as s:
        async with s.begin():
            statement = select(CustomImage).where(
                CustomImage.user_id == user_id
                and CustomImage.character_id == character_id
            )
            async for row in await s.stream(statement):
                row = CustomImage.from_orm(row)
                row.current = False
                s.add(row)
        async with s.begin():
            s.add(
                CustomImage(
                    user_id=user_id,
                    character_id=character_id,
                    image_url=image_url,
                    nickname=nickname,
                    current=True,
                )
            )
        await s.commit()


async def remove_user_custom_image(
    user_id: int, image_url: str, character_id: int, engine: AsyncEngine
) -> None:
    """Remove a custom image for a user's character from the database.

    Args:
        user_id (int): The ID of the user who created the custom image.
        image_url (str): The URL of the image to remove.
        character_id (int): The ID of the character for whom the custom image was created.
        engine (AsyncEngine): The SQLAlchemy AsyncEngine instance used to connect to the database.

    Returns:
        None.
    """
    async with AsyncSession(engine) as s:
        async with s.begin():
            statement = select(CustomImage).where(
                CustomImage.user_id == user_id
                and CustomImage.image_url == image_url
                and CustomImage.character_id == character_id
            )
            async for row in await s.stream(statement):
                row = CustomImage.from_orm(row)
                await s.delete(row)
        async with s.begin():
            statement = select(CustomImage).where(
                CustomImage.user_id == user_id
                and CustomImage.character_id == character_id
            )
            image = CustomImage.from_orm((await s.execute(statement)).scalars().first())
            image.current = True
            s.add(image)
        await s.commit()
