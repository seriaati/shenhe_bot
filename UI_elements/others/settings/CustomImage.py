import discord
from UI_base_models import BaseModal, BaseView
from ambr.client import AmbrTopAPI

from apps.genshin.custom_model import UserCustomImage
from apps.genshin.utils import get_character_emoji
from apps.text_map.convert_locale import to_ambr_top
from data.game.elements import get_element_emoji, get_element_list
from utility.utils import default_embed
from apps.text_map.text_map_app import text_map
from typing import List, Optional
import aiosqlite
import config
import asset


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
            image_options = await get_user_custom_image_options(i, int(character_id))
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
    embed = default_embed(message=text_map.get(276, view.locale))
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
        label="Image URL", placeholder="https://i.imgur.com/8lO5xNk.jpg"
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
        await add_user_custom_image(
            i, self.url.value, self.character_id, self.nickname.value
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
        options = await get_user_custom_image_options(i, int(self.character_id))
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
        if self.delete:
            await remove_user_custom_image(i, self.values[0], self.character_id)
        else:
            await change_user_custom_image(i, self.values[0], self.character_id)
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
    view.clear_items()
    view.add_item(GoBackCharacter(element))
    options = await get_user_custom_image_options(i, character_id)
    disabled = True if len(options) == 25 else False
    view.add_item(AddImage(view.locale, character_id, element, disabled))
    disabled = True if not options else False
    view.add_item(RemoveImage(view.locale, character_id, disabled, element))
    view.add_item(ImageSelect(view.locale, options, False, character_id, element))
    custom_image = await get_user_custom_image(i.user.id, i.client.db, character_id)
    embed = get_user_custom_image_embed(i, view.locale, str(character_id), custom_image)
    await i.response.edit_message(embed=embed, view=view)


async def change_user_custom_image(
    i: discord.Interaction, url: str, character_id: int
) -> None:
    await i.client.db.execute(
        "UPDATE custom_image SET current = 0 WHERE user_id = ? AND character_id = ?",
        (i.user.id, character_id),
    )
    await i.client.db.execute(
        "UPDATE custom_image SET current = 1 WHERE user_id = ? AND character_id = ? AND image_url = ?",
        (i.user.id, character_id, url),
    )
    await i.client.db.commit()


async def add_user_custom_image(
    i: discord.Interaction, url: str, character_id: int, nickname: str
) -> None:
    await i.client.db.execute(
        "UPDATE custom_image SET current = 0 WHERE user_id = ? AND character_id = ?",
        (i.user.id, character_id),
    )
    await i.client.db.execute(
        "INSERT INTO custom_image VALUES (?, ?, ?, ?, 1) ON CONFLICT DO NOTHING",
        (i.user.id, character_id, url, nickname),
    )
    await i.client.db.commit()


async def remove_user_custom_image(
    i: discord.Interaction, url: str, character_id: int
) -> None:
    await i.client.db.execute(
        "DELETE FROM custom_image WHERE user_id = ? AND character_id = ? AND image_url = ?",
        (
            i.user.id,
            character_id,
            url,
        ),
    )
    await i.client.db.commit()


async def get_user_custom_image_options(
    i: discord.Interaction, character_id: int
) -> List[discord.SelectOption]:
    async with i.client.db.execute(
        "SELECT * FROM custom_image WHERE user_id = ? AND character_id = ?",
        (i.user.id, character_id),
    ) as cursor:
        rows = await cursor.fetchall()
    options = []
    for row in rows:
        options.append(
            discord.SelectOption(label=row[3], description=row[2], value=row[2])
        )
    return options


def get_user_custom_image_embed(
    i: discord.Interaction,
    locale: discord.Locale | str,
    character_id: str,
    custom_image: Optional[UserCustomImage] = None,
    from_settings: bool = True,
) -> discord.Embed:
    embed = default_embed(
        message=text_map.get(412, locale) if not from_settings else ""
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
    return embed


async def get_user_custom_image(
    user_id: int, db: aiosqlite.Connection, character_id: int
) -> Optional[UserCustomImage]:
    async with db.execute(
        "SELECT * FROM custom_image WHERE user_id = ? AND character_id = ? AND current = 1",
        (user_id, character_id),
    ) as cursor:
        image = await cursor.fetchone()
    if image is None:
        return None
    else:
        return UserCustomImage(
            user_id=image[0],
            character_id=image[1],
            url=image[2],
            nickname=image[3],
            current=image[4],
        )
