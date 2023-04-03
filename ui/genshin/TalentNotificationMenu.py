from typing import Any, List

import asyncpg
from discord import Interaction, Locale, SelectOption
from discord.ui import Button, Select

import dev.asset as asset
import config
from ambr import AmbrTopAPI
from apps.genshin import get_character_emoji
from apps.text_map import text_map, to_ambr_top
from dev.base_ui import BaseView
from data.game.elements import convert_elements, elements
from ui.genshin import ReminderMenu


class View(BaseView):
    def __init__(self, locale: Locale | str):
        super().__init__(timeout=config.mid_timeout)
        self.locale = locale

        element_names = list(convert_elements.values())
        element_emojis = list(elements.values())
        for index in range(0, 7):
            self.add_item(
                ElementButton(element_names[index], element_emojis[index], index // 4)
            )
        self.add_item(GoBackTwo())


class GoBackTwo(Button):
    def __init__(self):
        super().__init__(emoji=asset.back_emoji, row=2)

    async def callback(self, i: Interaction):
        await ReminderMenu.return_talent_notification(i, self.view)  # type: ignore


class ElementButton(Button):
    def __init__(self, element: str, element_emoji: str, row: int):
        super().__init__(emoji=element_emoji, row=row)
        self.element = element

    async def callback(self, i: Interaction) -> Any:
        self.view: View
        pool: asyncpg.Pool = i.client.pool  # type: ignore
        character_list: List[str] = await pool.fetchval(
            "SELECT item_list FROM talent_notification WHERE user_id = $1", i.user.id
        )

        locale = self.view.locale
        ambr_locale = to_ambr_top(locale)
        client = AmbrTopAPI(i.client.session, ambr_locale)  # type: ignore
        characters = await client.get_character()
        if not isinstance(characters, list):
            raise AssertionError

        options: List[SelectOption] = []
        for character in characters:
            if character.element == self.element:
                description = (
                    text_map.get(161, locale)
                    if character.id in character_list
                    else None
                )
                options.append(
                    SelectOption(
                        label=character.name,
                        emoji=get_character_emoji(str(character.id)),
                        value=character.id,
                        description=description,
                    )
                )

        self.view.clear_items()
        self.view.add_item(GoBack())
        self.view.add_item(CharacterSelect(options, text_map.get(157, locale)))
        await i.response.edit_message(view=self.view)


class GoBack(Button):
    def __init__(self):
        super().__init__(emoji=asset.back_emoji, row=2)
        self.view: View

    async def callback(self, i: Interaction):
        self.view.clear_items()

        element_names = list(convert_elements.values())
        element_emojis = list(elements.values())
        for index in range(0, 7):
            self.view.add_item(
                ElementButton(element_names[index], element_emojis[index], index // 4)
            )
        self.view.add_item(GoBackTwo())
        await i.response.edit_message(view=self.view)


class CharacterSelect(Select):
    def __init__(self, options: list[SelectOption], placeholder: str):
        super().__init__(
            options=options, placeholder=placeholder, max_values=len(options)
        )
        self.view: View

    async def callback(self, i: Interaction) -> Any:
        pool: asyncpg.Pool = i.client.pool  # type: ignore
        data_list = await pool.fetchval(
            "SELECT item_list FROM talent_notification WHERE user_id = $1", i.user.id
        )
        character_list: List[str] = data_list
        for character_id in self.values:
            if character_id in character_list:
                character_list.remove(character_id)
            else:
                character_list.append(character_id)
        await pool.execute(
            "UPDATE talent_notification SET item_list = $1 WHERE user_id = $2",
            character_list,
            i.user.id,
        )

        await i.response.edit_message(view=self.view)
        await ReminderMenu.return_talent_notification(i, self.view)  # type: ignore
