from discord import ButtonStyle, Interaction, Locale
from discord.ui import Button

import config
from apps.text_map.text_map_app import text_map
from base_ui import BaseView


class View(BaseView):
    def __init__(self, locale: Locale | str, uid: int):
        super().__init__(timeout=config.short_timeout)
        self.locale = locale
        self.uid = uid

        self.add_item(CopyUID(text_map.get(726, locale)))


class CopyUID(Button):
    def __init__(self, label: str):
        super().__init__(label=label, style=ButtonStyle.green)
        self.view: View

    async def callback(self, i: Interaction):
        await i.response.send_message(content=str(self.view.uid), ephemeral=True)
