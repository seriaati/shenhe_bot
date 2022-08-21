from typing import Any, Dict

import aiosqlite
from apps.genshin.damage_calculator import return_damage
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from debug import DefaultView
from discord import (ButtonStyle, Embed, Interaction, Locale, Member,
                     SelectOption)
from discord.ui import Button, Select
from enkanetwork import EnkaNetworkResponse
from pyppeteer.browser import Browser
from UI_elements.genshin import EnkaDamageCalculator
from utility.utils import error_embed
import config


class View(DefaultView):
    def __init__(self, embeds: Dict[int, Embed], artifact_embeds: dict[int, Embed], character_options: list[SelectOption], data: EnkaNetworkResponse, browser: Browser, eng_data: EnkaNetworkResponse, author: Member, db: aiosqlite.Connection, locale: Locale, user_locale: str):
        super().__init__(timeout=config.mid_timeout)
        self.embeds = embeds
        self.artifact_embeds = artifact_embeds
        self.character_options = character_options
        self.character_id = None
        self.browser = browser
        self.author = author
        self.data = data
        self.eng_data = eng_data
        self.db = db
        self.add_item(ViewArtifacts(text_map.get(92, locale, user_locale)))
        self.add_item(CalculateDamageButton(text_map.get(348, locale, user_locale)))
        self.add_item(PageSelect(character_options, text_map.get(157, locale, user_locale)))
        self.children[0].disabled = True
        self.children[1].disabled = True

    async def interaction_check(self, i: Interaction) -> bool:
        user_locale = await get_user_locale(i.user.id, self.db)
        if self.author.id != i.user.id:
            await i.response.send_message(embed=error_embed().set_author(name=text_map.get(143, i.locale, user_locale), icon_url=i.user.avatar), ephemeral=True)
        return self.author.id == i.user.id

class PageSelect(Select):
    def __init__(self, character_options: list[SelectOption], plceholder: str):
        super().__init__(placeholder=plceholder, options=character_options)

    async def callback(self, i: Interaction) -> Any:
        disabled = True if self.values[0] == '0' else False
        self.view.children[0].disabled = disabled
        self.view.children[1].disabled = disabled
        self.view.character_id = self.values[0]
        await i.response.edit_message(embed=self.view.embeds[self.values[0]], view=self.view)

class ViewArtifacts(Button):
    def __init__(self, label: str):
        super().__init__(label=label, style=ButtonStyle.blurple)

    async def callback(self, i: Interaction) -> Any:
        self.disabled = True
        await i.response.edit_message(embed=self.view.artifact_embeds[self.view.character_id], view=self.view)

class CalculateDamageButton(Button):
    def __init__(self, label: str):
        super().__init__(style=ButtonStyle.blurple, label=label, disabled=True)

    async def callback(self, i: Interaction) -> Any:
        self.view: View
        view = EnkaDamageCalculator.View(self.view, i.locale, await get_user_locale(i.user.id, self.view.db))
        await return_damage(i, view)
        view.message = await i.original_response()
