from typing import Any

import aiosqlite
from apps.genshin.utils import get_character
from data.game.elements import elements
from debug import DefaultView
from discord import ButtonStyle, Embed, Interaction, Member, SelectOption
from discord.ui import Button, Select
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from utility.utils import error_embed
import config


class View(DefaultView):
    def __init__(self, data: dict, author: User, db: aiosqlite.Connection):
        super().__init__(timeout=config.short_timeout)
        self.author = author
        self.db = db
        for index in range(0, 7):
            self.add_item(ElementButton(data, index))
        self.avatar_id = None

    async def interaction_check(self, i: Interaction) -> bool:
        user_locale = await get_user_locale(i.user.id, self.db)
        if i.user.id != self.author.id:
            await i.response.send_message(embed=error_embed().set_author(name=text_map.get(143, i.locale, user_locale), icon_url=i.user.display_avatar.url), ephemeral=True)
        return i.user.id == self.author.id


class ElementButton(Button):
    def __init__(self, data: dict, index: int):
        super().__init__(
            emoji=(list(elements.values()))[index], row=index//4)
        self.index = index
        self.data = data

    async def callback(self, i: Interaction) -> Any:
        self.view: View
        user_locale = await get_user_locale(i.user.id, self.view.db)
        self.view.clear_items()
        self.view.add_item(CharacterSelect(
            self.data, list(elements.keys())[self.index], text_map.get(157, i.locale, user_locale)))
        await i.response.edit_message(view=self.view)


class CharacterSelect(Select):
    def __init__(self, data: dict, element: str, placeholder: str):
        options = []
        for avatar_id, avatar_info in data['data']['items'].items():
            if avatar_info['element'] == element:
                options.append(SelectOption(label=avatar_info['name'], emoji=get_character(
                    avatar_id)['emoji'], value=avatar_id))
        super().__init__(placeholder=placeholder, options=options)

    async def callback(self, i: Interaction):
        await i.response.defer()
        self.view.avatar_id = self.values[0]
        self.view.stop()


class ShowTalentMaterials(Button):
    def __init__(self, embed: Embed, label: str):
        super().__init__(label=label, style=ButtonStyle.green, row=2)
        self.embed = embed

    async def callback(self, i: Interaction):
        await i.response.send_message(embed=self.embed, ephemeral=True)


class QuickNavigation(Select):
    def __init__(self, options: list[SelectOption], placeholder: str):
        super().__init__(placeholder=placeholder, options=options)

    async def callback(self, i: Interaction):
        self.view.current_page = int(self.values[0])
        await self.view.update_children(i)
