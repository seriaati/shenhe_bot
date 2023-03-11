from typing import List, Optional

import aiohttp
import asyncpg
import discord

import asset
import config
from ambr.client import AmbrTopAPI
from apps.genshin.custom_model import UserCustomImage
from apps.genshin.utils import get_character_emoji
from apps.text_map.convert_locale import to_ambr_top
from apps.text_map.text_map_app import text_map
from data.game.elements import get_element_emoji, get_element_list
from UI_base_models import BaseModal, BaseView
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


class ElementButton(discord.ui.Button):
    def __init__(self, emoji: str, element: str, row: int):
        super().__init__(emoji=emoji, row=row)
        self.element = element

    async def callback(self, i: discord.Interaction):
        self.view: View
        await element_button_callback(i, self.view, self.element)


class GoBack(discord.ui.Button):
    def __init__(self):
        super().__init__(emoji=asset.back_emoji)

    async def callback(self, i: discord.Interaction):
        self.view: View
        self.view.clear_items()
        elements = get_element_list()
        for index, element in enumerate(elements):
            self.view.add_item(
                ElementButton(get_element_emoji(element), element, index // 4)
            )
        await i.response.edit_message(view=self.view)


class GoBackCharacter(discord.ui.Button):
    def __init__(self, element: str):
        super().__init__(emoji=asset.back_emoji)
        self.element = element

    async def callback(self, i: discord.Interaction):
        self.view: View
        await element_button_callback(i, self.view, self.element)


async def element_button_callback(i: discord.Interaction, view: View, element: str):
    ambr = AmbrTopAPI(i.client.session, to_ambr_top(view.locale))
    characters = await ambr.get_character()
    if not isinstance(characters, List):
        raise TypeError("characters is not a list")
    options = []
    for character in characters:
        if character.element == element:
            character_id = character.id.split("-")[0]
            image_options = await get_user_custom_image_options(
                int(character_id), i.client.pool, i.user.id
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


class AddImage(discord.ui.Button):
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

    async def callback(self, i: discord.Interaction):
        self.view: View
        await i.response.send_modal(
            AddImageModal(self.view.locale, self.character_id, self.view, self.element)
        )


class AddImageModal(BaseModal):
    nickname = discord.ui.TextInput(
        label="Nickname",
        placeholder="Type a nickname for the custom image",
        max_length=25,
    )
    url = discord.ui.TextInput(
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

    async def on_submit(self, i: discord.Interaction) -> None:
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
        pool: asyncpg.pool.Pool = i.client.pool  # type: ignore
        await add_user_custom_image(
            i.user.id, self.character_id, self.url.value, self.nickname.value, pool
        )

        await return_custom_image_interaction(
            self.view, i, self.character_id, self.element
        )


class RemoveImage(discord.ui.Button):
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

    async def callback(self, i: discord.Interaction):
        self.view: View
        self.view.clear_items()
        options = await get_user_custom_image_options(
            int(self.character_id), i.client.pool, i.user.id
        )
        self.view.add_item(
            ImageSelect(
                self.view.locale, options, True, int(self.character_id), self.element
            )
        )
        self.view.add_item(GoBack())
        await i.response.edit_message(view=self.view)


class ImageSelect(discord.ui.Select):
    def __init__(
        self,
        locale: discord.Locale | str,
        options: List[discord.SelectOption],
        delete: bool,
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
        self.delete = delete
        self.character_id = character_id
        self.element = element

    async def callback(self, i: discord.Interaction):
        self.view: View
        pool: asyncpg.Pool = i.client.pool  # type: ignore

        if self.delete:
            await pool.execute(
                """
                DELETE FROM
                    custom_image
                WHERE
                    user_id = $1 AND character_id = $2 AND image_url = $3
                """,
                i.user.id,
                self.character_id,
                self.values[0],
            )
        else:
            await change_user_custom_image(
                i.user.id, self.character_id, self.values[0], pool
            )

        await return_custom_image_interaction(
            self.view, i, self.character_id, self.element
        )


class CharacterSelect(discord.ui.Select):
    def __init__(
        self,
        locale: discord.Locale | str,
        options: List[discord.SelectOption],
        element: str,
    ):
        super().__init__(placeholder=text_map.get(157, locale), options=options)
        self.element = element

    async def callback(self, i: discord.Interaction):
        self.view: View
        await return_custom_image_interaction(
            self.view, i, int(self.values[0].split("-")[0]), self.element
        )


async def return_custom_image_interaction(
    view: View, i: discord.Interaction, character_id: int, element: str
):
    try:
        await i.response.defer()
    except discord.InteractionResponded:
        pass

    view.clear_items()
    view.add_item(GoBackCharacter(element))

    options = await get_user_custom_image_options(
        character_id, i.client.pool, i.user.id
    )
    disabled = True if len(options) == 25 else False
    view.add_item(AddImage(view.locale, character_id, element, disabled))

    disabled = True if not options else False
    view.add_item(RemoveImage(view.locale, character_id, disabled, element))
    view.add_item(ImageSelect(view.locale, options, False, character_id, element))

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
) -> List[discord.SelectOption]:
    options: List[discord.SelectOption] = []
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
        options.append(
            discord.SelectOption(
                label=row["nickname"][:100],
                description=row["image_url"][:100],
                value=row["image_url"],
            )
        )

    return options


async def get_user_custom_image_embed(
    i: discord.Interaction,
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
            if response.status == 200:
                return True
            else:
                return False
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
        image_url,
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
