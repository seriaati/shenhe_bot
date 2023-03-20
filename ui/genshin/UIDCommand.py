from base_ui import BaseView
from discord import Locale, Interaction, ButtonStyle
import config
from discord.ui import Button, Button
from apps.text_map.text_map_app import text_map


class View(BaseView):
    def __init__(self, locale: Locale | str, uid: int):
        super().__init__(timeout=config.short_timeout)
        self.locale = locale
        self.uid = uid

        self.add_item(CopyUID(text_map.get(726, locale)))


class CopyUID(Button):
    def __init__(self, label: str):
        super().__init__(label=label, style=ButtonStyle.green)

    async def callback(self, i: Interaction):
        self.view: View
        await i.response.send_message(content=str(self.view.uid), ephemeral=True)
