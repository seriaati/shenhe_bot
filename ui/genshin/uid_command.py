from discord import ButtonStyle, Interaction, Locale
from discord.ui import Button

import dev.config as config
from apps.text_map import text_map
from dev.base_ui import BaseView


class View(BaseView):
    def __init__(self, lang: Locale | str, uid: int):
        super().__init__(timeout=config.short_timeout)
        self.lang = lang
        self.uid = uid

        self.add_item(CopyUID(text_map.get(726, lang)))


class CopyUID(Button):
    def __init__(self, label: str):
        super().__init__(label=label, style=ButtonStyle.green)
        self.view: View

    async def callback(self, i: Interaction):
        await i.response.send_message(content=str(self.view.uid), ephemeral=True)
