import aiosqlite
from utility.apps.text_map.utils import get_user_locale
from debug import DefaultView
from discord import Member, Interaction, Locale, Embed, SelectOption
from discord.ui import Select
from utility.apps.text_map.TextMap import text_map
from utility.utils import error_embed
from typing import Any

class View(DefaultView):
    def __init__(self, author: Member, embeds: list[Embed], locale: Locale, user_locale: str, db: aiosqlite.Connection):
        super().__init__(timeout=None)
        self.author = author
        self.db = db 
        
        self.add_item(FloorSelect(
            embeds, locale, user_locale))

    async def interaction_check(self, i: Interaction) -> bool:
        user_locale = await get_user_locale(i.user.id, self.db)
        if self.author.id != i.user.id:
            await i.response.send_message(embed=error_embed().set_author(name=text_map.get(143, i.locale, user_locale), icon_url=i.user.avatar), ephemeral=True)
        return self.author.id == i.user.id

class FloorSelect(Select):
    def __init__(self, embeds: list[Embed], locale: Locale, user_locale: str):
        options = []
        for index in range(0, len(embeds)):
            options.append(SelectOption(
                label=f'{text_map.get(146, locale, user_locale)} {9+index} {text_map.get(147, locale, user_locale)}', value=index))
        super().__init__(placeholder=text_map.get(148, locale, user_locale), options=options)
        self.embeds = embeds

    async def callback(self, i: Interaction) -> Any:
        await i.response.edit_message(embed=self.embeds[int(self.values[0])])