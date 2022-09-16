import ast
from typing import Any

import aiosqlite
import config
from ambr.client import AmbrTopAPI
from apps.genshin.utils import get_character
from apps.text_map.convert_locale import to_ambr_top
from apps.text_map.text_map_app import text_map
from data.game.elements import convert_elements, elements
from debug import DefaultView
from discord import Interaction, Locale, SelectOption
from discord.ui import Button, Select
from UI_elements.genshin import ReminderMenu


class View(DefaultView):
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
        super().__init__(emoji="<:left:982588994778972171>", row=2)
    
    async def callback(self, i: Interaction):
        await ReminderMenu.return_talent_notification(i, self.view)

class ElementButton(Button):
    def __init__(self, element: str, element_emoji: str, row: int):
        super().__init__(emoji=element_emoji, row=row)
        self.element = element

    async def callback(self, i: Interaction) -> Any:
        self.view: View
        c: aiosqlite.Cursor = await i.client.db.cursor()
        await c.execute(
            "SELECT character_list FROM talent_notification WHERE user_id = ?",
            (i.user.id,),
        )
        (character_list,) = await c.fetchone()
        character_list = ast.literal_eval(character_list)
        locale = self.view.locale
        options = []
        ambr_locale = to_ambr_top(locale)
        client = AmbrTopAPI(i.client.session, ambr_locale)
        characters = await client.get_character()
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
                        emoji=get_character(character.id)["emoji"],
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
        super().__init__(emoji="<:left:982588994778972171>", row=2)

    async def callback(self, i: Interaction):
        self.view: View
        self.view.clear_items()

        element_names = list(convert_elements.values())
        element_emojis = list(elements.values())
        for index in range(0, 7):
            self.view.add_item(
                ElementButton(element_names[index], element_emojis[index], index // 4)
            )
        await i.response.edit_message(view=self.view)


class CharacterSelect(Select):
    def __init__(self, options: list[SelectOption], placeholder: str):
        super().__init__(
            options=options, placeholder=placeholder, max_values=len(options)
        )

    async def callback(self, i: Interaction) -> Any:
        self.view: View
        c: aiosqlite.Cursor = await i.client.db.cursor()
        await c.execute(
            "SELECT character_list FROM talent_notification WHERE user_id = ?",
            (i.user.id,),
        )
        (character_list,) = await c.fetchone()
        character_list = ast.literal_eval(character_list)
        for character_id in self.values:
            if character_id in character_list:
                character_list.remove(character_id)
            else:
                character_list.append(character_id)
        await c.execute(
            "UPDATE talent_notification SET character_list = ? WHERE user_id = ?",
            (str(character_list), i.user.id),
        )
        await i.client.db.commit()
        await i.response.edit_message(view=self.view)
        await ReminderMenu.return_talent_notification(i, self.view)
