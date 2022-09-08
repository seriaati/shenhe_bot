import ast
from typing import Any

import aiohttp
import aiosqlite
from ambr.client import AmbrTopAPI
from apps.text_map.convert_locale import to_ambr_top
from apps.genshin.utils import get_character
from data.game.elements import convert_elements, elements
from debug import DefaultView
from discord import Interaction, Locale, User, SelectOption
from discord.ui import Button, Select
from apps.genshin.genshin_app import GenshinApp
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from utility.utils import default_embed, error_embed
import config


class View(DefaultView):
    def __init__(
        self,
        author: User,
        locale: Locale,
        user_locale: str,
        db: aiosqlite.Connection,
        genshin_app: GenshinApp,
        session: aiohttp.ClientSession,
    ):
        super().__init__(timeout=config.short_timeout)
        self.author = author
        self.locale = locale
        self.user_locale = user_locale
        self.db = db
        self.genshin_app = genshin_app
        self.session = session

        element_names = list(convert_elements.values())
        element_emojis = list(elements.values())
        for index in range(0, 7):
            self.add_item(
                ElementButton(element_names[index], element_emojis[index], index // 4)
            )


class ElementButton(Button):
    def __init__(self, element: str, element_emoji: str, row: int):
        super().__init__(emoji=element_emoji, row=row)
        self.element = element

    async def callback(self, i: Interaction) -> Any:
        self.view: View
        user_locale = await get_user_locale(i.user.id, self.view.db)

        embed = default_embed(message=text_map.get(156, i.locale, user_locale))
        embed.set_author(
            name=text_map.get(157, i.locale, user_locale), icon_url=i.user.display_avatar.url
        )
        value = await self.view.genshin_app.get_user_talent_notification_enabled_str(
            i.user.id, i.locale
        )
        embed.add_field(name=text_map.get(159, i.locale, user_locale), value=value)

        c = await self.view.db.cursor()
        await c.execute(
            "SELECT talent_notif_chara_list FROM genshin_accounts WHERE user_id = ?",
            (i.user.id,),
        )
        user_character_list: list = ast.literal_eval((await c.fetchone())[0])

        options = []
        locale = to_ambr_top(user_locale or i.locale)
        client = AmbrTopAPI(i.client.session, locale)
        characters = await client.get_character()
        for character in characters:
            if character.element == self.element:
                description = (
                    text_map.get(161, i.locale, user_locale)
                    if character.id in user_character_list
                    else None
                )
                options.append(
                    SelectOption(
                        label=character.name,
                        emoji=get_character(character.id)['emoji'],
                        value=character.id,
                        description=description
                    )
                )

        # choose your character(s)
        placeholder = text_map.get(157, i.locale, user_locale)

        self.view.clear_items()
        self.view.add_item(GoBack())
        self.view.add_item(CharacterSelect(options, placeholder))
        await i.response.edit_message(embed=embed, view=self.view)


class GoBack(Button):
    def __init__(self):
        super().__init__(emoji="<:left:982588994778972171>", row=2)

    async def callback(self, i: Interaction):
        user_locale = await get_user_locale(i.user.id, self.view.db)
        self.view: View
        self.view.clear_items()

        element_names = list(convert_elements.values())
        element_emojis = list(elements.values())
        for index in range(0, 7):
            self.view.add_item(
                ElementButton(element_names[index], element_emojis[index], index // 4)
            )
        embed = default_embed(message=text_map.get(156, i.locale, user_locale))
        embed.set_author(
            name=text_map.get(157, i.locale, user_locale), icon_url=i.user.display_avatar.url
        )
        value = await self.view.genshin_app.get_user_talent_notification_enabled_str(
            i.user.id, i.locale
        )
        embed.add_field(name=text_map.get(159, i.locale, user_locale), value=value)
        await i.response.edit_message(embed=embed, view=self.view)


class CharacterSelect(Select):
    def __init__(self, options: list[SelectOption], placeholder: str):
        super().__init__(
            options=options, placeholder=placeholder, max_values=len(options)
        )

    async def callback(self, i: Interaction) -> Any:
        self.view: View
        c = await self.view.db.cursor()
        user_locale = await get_user_locale(i.user.id, self.view.db)

        await c.execute(
            "SELECT talent_notif_chara_list FROM genshin_accounts WHERE user_id = ?",
            (i.user.id,),
        )
        user_character_list: list = ast.literal_eval((await c.fetchone())[0])
        for character_id in self.values:
            if character_id in user_character_list:
                user_character_list.remove(character_id)
            else:
                user_character_list.append(character_id)
        await c.execute(
            "UPDATE genshin_accounts SET talent_notif_toggle = 1, talent_notif_chara_list = ? WHERE user_id = ?",
            (str(user_character_list), i.user.id),
        )
        await self.view.db.commit()

        embed = default_embed(message=text_map.get(156, i.locale, user_locale))
        embed.set_author(
            name=text_map.get(157, i.locale, user_locale), icon_url=i.user.display_avatar.url
        )
        value = await self.view.genshin_app.get_user_talent_notification_enabled_str(
            i.user.id, i.locale
        )
        embed.add_field(name=text_map.get(159, i.locale, user_locale), value=value)

        await c.execute(
            "SELECT talent_notif_chara_list FROM genshin_accounts WHERE user_id = ?",
            (i.user.id,),
        )
        user_character_list: list = ast.literal_eval((await c.fetchone())[0])
        for option in self.options:
            if option.value in user_character_list:
                option.description = text_map.get(161, i.locale, user_locale)
            else:
                option.description = None

        await i.response.edit_message(embed=embed, view=self.view)
