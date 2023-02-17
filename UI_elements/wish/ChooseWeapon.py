from typing import Optional
from discord import ButtonStyle, Interaction, Locale
from discord.ui import Button

import config
from apps.text_map.text_map_app import text_map
from UI_base_models import BaseView


class View(BaseView):
    def __init__(
        self,
        locale: Locale | str,
    ):
        super().__init__(timeout=config.short_timeout)
        self.up: Optional[bool] = None
        self.locale = locale

        self.add_item(IsUP())
        self.add_item(IsStandard(locale))


class IsUP(Button):
    def __init__(self):
        super().__init__(label="UP", style=ButtonStyle.blurple)

    async def callback(self, i: Interaction):
        self.view: View
        await i.response.defer()
        self.view.up = True
        self.view.stop()


class IsStandard(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(label=text_map.get(387, locale))

    async def callback(self, i: Interaction):
        self.view: View
        await i.response.defer()
        self.view.up = False
        self.view.stop()
