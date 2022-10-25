from discord import ButtonStyle, Interaction, Locale
from discord.ui import Button

import config
from apps.text_map.text_map_app import text_map
from UI_base_models import BaseView


class View(BaseView):
    def __init__(
        self,
        locale: Locale,
        user_locale: str | None,
    ):
        super().__init__(timeout=config.short_timeout)
        self.up = None
        self.locale = locale
        self.user_locale = user_locale

        self.add_item(IsUP())
        self.add_item(IsStandard(locale, user_locale))


class IsUP(Button):
    def __init__(self):
        super().__init__(label="UP", style=ButtonStyle.blurple)

    async def callback(self, i: Interaction):
        await i.response.defer()
        self.view.up = True
        self.view.stop()


class IsStandard(Button):
    def __init__(self, locale: Locale, user_locale: str | None):
        super().__init__(label=text_map.get(387, locale, user_locale))

    async def callback(self, i: Interaction):
        await i.response.defer()
        self.view.up = False
        self.view.stop()
