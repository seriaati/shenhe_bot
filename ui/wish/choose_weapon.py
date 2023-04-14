from typing import Optional

from discord import ButtonStyle, Interaction, Locale
from discord.ui import Button

import dev.config as config
from apps.text_map import text_map
from dev.base_ui import BaseView


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
        self.view: View

    async def callback(self, i: Interaction):
        await i.response.defer()
        self.view.up = True
        self.view.stop()


class IsStandard(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(label=text_map.get(387, locale))
        self.view: View

    async def callback(self, i: Interaction):
        await i.response.defer()
        self.view.up = False
        self.view.stop()