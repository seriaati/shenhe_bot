import json
from typing import Dict, List, Optional, Union

import aiofiles

import aiohttp
import asyncpg
import discord
from discord import ui

import asset
import config
from ambr.client import AmbrTopAPI
from apps.genshin.custom_model import UserCustomImage, CustomInteraction
from apps.genshin.utils import get_character_emoji
from apps.text_map.convert_locale import to_ambr_top
from apps.text_map.text_map_app import text_map
from data.game.elements import get_element_emoji, get_element_list
from base_ui import BaseModal, BaseView
from utility.utils import DefaultEmbed, ErrorEmbed


class View(BaseView):
    def __init__(self, locale: discord.Locale | str):
        super().__init__(timeout=config.mid_timeout)

        elements = get_element_list()
        for index, element in enumerate(elements):
            self.add_item(
                ElementButton(get_element_emoji(element), element, index // 4)
            )
        self.locale = locale


class ElementButton(ui.Button):
    def __init__(self, emoji: str, element: str, row: int):
        super().__init__(emoji=emoji, row=row)
        self.element = element

    async def callback(self, i: CustomInteraction):
        self.view: View
        await element_button_callback(i, self.view, self.element)


class GoBack(ui.Button):
    def __init__(self):
        super().__init__(emoji=asset.back_emoji)

    async def callback(self, i: CustomInteraction):
        self.view: View
        self.view.clear_items()
        elements = get_element_list()
        for index, element in enumerate(elements):
            self.view.add_item(
                ElementButton(get_element_emoji(element), element, index // 4)
            )
        await i.response.edit_message(view=self.view)


class GoBackCharacter(ui.Button):
    def __init__(self, element: str):
        super().__init__(emoji=asset.back_emoji)
        self.element = element

    async def callback(self, i: CustomInteraction):
        self.view: View
        await element_button_callback(i, self.view, self.element)


async def element_button_callback(i: CustomInteraction, view: View, element: str):
    ambr = AmbrTopAPI(i.client.session, to_ambr_top(view.locale))
    characters = await ambr.get_character()
    if not isinstance(characters, List):
        raise TypeError("characters is not a list")
    options = []
    for character in characters:
        if character.element == element:
            character_id = character.id.split("-")[0]
            image_options = await get_user_custom_image_options(
                int(character_id), i.client.pool, i.user.id, view.locale
            )
            options.append(
                discord.SelectOption(
                    label=character.name,
                    description=text_map.get(532, view.locale).format(
                        num=len(image_options)
                    ),
                    value=str(character_id),
                    emoji=get_character_emoji(character.id),
                )
            )
    view.clear_items()
    view.add_item(CharacterSelect(view.locale, options, element))
    view.add_item(GoBack())
    embed = DefaultEmbed(description=text_map.get(276, view.locale))
    embed.set_author(
        name=text_map.get(62, view.locale), icon_url=i.user.display_avatar.url
    )
    await i.response.edit_message(view=view, embed=embed)


class AddImage(ui.Button):
    def __init__(
        self,
        locale: discord.Locale | str,
        character_id: int,
        element: str,
        disabled: bool,
    ):
        super().__init__(
            label=text_map.get(413, locale),
            style=discord.ButtonStyle.green,
            disabled=disabled,
        )
        self.character_id = character_id
        self.element = element

    async def callback(self, i: CustomInteraction):
        self.view: View
        await i.response.send_modal(
            AddImageModal(self.view.locale, self.character_id, self.view, self.element)
        )


class AddImageModal(BaseModal):
    nickname = ui.TextInput(
        label="Nickname",
        placeholder="Type a nickname for the custom image",
        max_length=25,
    )
    url = ui.TextInput(
        label="Image URL", placeholder="https://i.imgur.com/8lO5xNk.jpg", max_length=100
    )

    def __init__(
        self, locale: discord.Locale | str, character_id: int, view: View, element: str
    ):
        super().__init__(timeout=config.long_timeout, title=text_map.get(413, locale))
        self.nickname.placeholder = text_map.get(45, locale)
        self.nickname.label = text_map.get(601, locale)
        self.url.label = text_map.get(60, locale)
        self.character_id = character_id
        self.view = view
        self.element = element

    async def on_submit(self, i: CustomInteraction) -> None:
        check = await validate_image_url(self.url.value, i.client.session)
        if not check:
            return await i.response.send_message(
                embed=ErrorEmbed(
                    description=text_map.get(568, self.view.locale)
                ).set_author(
                    name=text_map.get(274, self.view.locale),
                    icon_url=i.user.display_avatar.url,
                ),
                ephemeral=True,
            )
        await add_user_custom_image(
            i.user.id,
            self.character_id,
            self.url.value,
            self.nickname.value,
            i.client.pool,
        )

        await return_custom_image_interaction(
            self.view, i, self.character_id, self.element
        )


class RemoveImage(ui.Button):
    def __init__(
        self,
        locale: discord.Locale | str,
        character_id: int,
        disabled: bool,
        element: str,
    ):
        super().__init__(
            label=text_map.get(61, locale),
            style=discord.ButtonStyle.red,
            disabled=disabled,
        )
        self.character_id = character_id
        self.element = element

    async def callback(self, i: CustomInteraction):
        self.view: View

        custom_image = await get_user_custom_image(
            i.user.id, self.character_id, i.client.pool
        )
        if custom_image is None:
            raise AssertionError

        await remove_user_custom_image(
            i.user.id, custom_image.url, custom_image.character_id, i.client.pool
        )
        await return_custom_image_interaction(
            self.view, i, self.character_id, self.element
        )


class ImageSelect(ui.Select):
    def __init__(
        self,
        locale: discord.Locale | str,
        options: List[discord.SelectOption],
        character_id: int,
        element: str,
    ):
        super().__init__(
            placeholder=text_map.get(562, locale),
            options=options
            if options
            else [discord.SelectOption(label="none", value="none")],
            disabled=not options,
        )
        self.character_id = character_id
        self.element = element

    async def callback(self, i: CustomInteraction):
        self.view: View

        await change_user_custom_image(
            i.user.id, self.character_id, self.values[0], i.client.pool
        )
        await return_custom_image_interaction(
            self.view, i, self.character_id, self.element
        )


class CharacterSelect(ui.Select):
    def __init__(
        self,
        locale: discord.Locale | str,
        options: List[discord.SelectOption],
        element: str,
    ):
        super().__init__(placeholder=text_map.get(157, locale), options=options)
        self.element = element

    async def callback(self, i: CustomInteraction):
        self.view: View
        await return_custom_image_interaction(
            self.view, i, int(self.values[0].split("-")[0]), self.element
        )


async def return_custom_image_interaction(
    view: View, i: CustomInteraction, character_id: int, element: str
):
    try:
        await i.response.defer()
    except discord.InteractionResponded:
        pass

    view.clear_items()
    view.add_item(GoBackCharacter(element))

    options = await get_user_custom_image_options(
        character_id, i.client.pool, i.user.id, view.locale
    )
    disabled = len(options) == 25
    view.add_item(AddImage(view.locale, character_id, element, disabled))

    disabled = bool(not options)
    view.add_item(RemoveImage(view.locale, character_id, disabled, element))
    view.add_item(ImageSelect(view.locale, options, character_id, element))

    custom_image = await get_user_custom_image(i.user.id, character_id, i.client.pool)
    embed = await get_user_custom_image_embed(
        i, view.locale, str(character_id), custom_image
    )
    view.message = await i.edit_original_response(embed=embed, view=view)
    view.author = i.user


async def get_user_custom_image_options(
    character_id: int,
    pool: asyncpg.Pool,
    user_id: int,
    locale: Union[discord.Locale, str],
) -> List[discord.SelectOption]:
    options: List[discord.SelectOption] = [
        discord.SelectOption(label=text_map.get(124, locale), value="default")
    ]
    async with aiofiles.open("data/draw/genshin_fanart.json", "r") as f:
        fanarts: Dict[str, List[str]] = json.loads(await f.read())
    c_fanarts = fanarts.get(str(character_id), [])

    rows = await pool.fetch(
        """
        SELECT
            nickname, image_url
        FROM
            custom_image
        WHERE
            user_id = $1 AND character_id = $2
        """,
        user_id,
        character_id,
    )
    for row in rows:
        if row["image_url"] in c_fanarts:
            continue
        options.append(
            discord.SelectOption(
                label=row["nickname"][:100],
                description=row["image_url"][:100],
                value=row["image_url"],
            )
        )

    index = 1
    for url in c_fanarts:
        if any(option.value == url for option in options):
            continue
        label = f"{text_map.get(748, locale)} ({index})"
        options.append(discord.SelectOption(label=label, description=url, value=url))
        index += 1

    return options


async def get_user_custom_image_embed(
    i: CustomInteraction,
    locale: discord.Locale | str,
    character_id: str,
    custom_image: Optional[UserCustomImage] = None,
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
        async with session.get(url) as response:
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
                custom_image (user_id, character_id, image_url, nickname)
            VALUES
                ($1, $2, $3, $4)
            """,
            user_id,
            character_id,
            image_url,
            image_url.split("/")[-1],
        )


async def get_user_custom_image(
    user_id: int, character_id: int, pool: asyncpg.Pool
) -> Optional[UserCustomImage]:
    image: Optional[asyncpg.Record] = await pool.fetchrow(
        """
        SELECT
            user_id, character_id, image_url, nickname
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
    return UserCustomImage(
        user_id=image["user_id"],
        character_id=image["character_id"],
        url=image["image_url"],
        nickname=image["nickname"],
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
    await pool.execute(
        """
        UPDATE
            custom_image
        SET
            current = true
        WHERE
            user_id = $1 AND character_id = $2
        LIMIT 1
        """,
        user_id,
        character_id,
    )
