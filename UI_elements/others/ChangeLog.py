from typing import Any, List

import aiosqlite
from apps.text_map.text_map_app import text_map
from debug import DefaultView
from discord import Embed, Interaction, Locale
from discord.ui import Button
from utility.paginator import GeneralPaginator


class View(DefaultView):
    def __init__(self, db: aiosqlite.Connection, embeds: List[Embed], locale: Locale, user_locale: str | None):
        super().__init__(timeout=None)
        self.db = db
        self.embeds = embeds
        self.add_item(ChangeLogButton(locale, user_locale))


class ChangeLogButton(Button):
    def __init__(self, locale: Locale, user_locale: str | None):
        super().__init__(label=text_map.get(505, locale, user_locale), custom_id='change_log_button')

    async def callback(self, i: Interaction) -> Any:
        self.view: View
        discord = Button(
            label='discord', url='https://discord.gg/ryfamUykRw', row=2)
        github = Button(
            label='github', url='https://github.com/seriaati/shenhe_bot', row=2)
        await GeneralPaginator(i, self.view.embeds[1:], self.view.db, [discord, github]).start(ephemeral=True)
