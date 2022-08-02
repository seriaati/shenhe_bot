from discord.ui import Modal , TextInput
from discord import Locale, Interaction
from utility.apps.text_map.TextMap import text_map

class Modal(Modal):
    resin_threshold = TextInput(
        label='樹脂閥值', placeholder='例如: 140 (不得大於 160)')
    max_notif = TextInput(label='最大提醒值', placeholder='例如: 5')

    def __init__(self, locale: Locale, user_locale: str):
        super().__init__(title=text_map.get(151, locale, user_locale))
        self.resin_threshold.label = text_map.get(152, locale, user_locale)
        self.resin_threshold.placeholder = text_map.get(
            153, locale, user_locale)
        self.max_notif.label = text_map.get(154, locale, user_locale)
        self.max_notif.placeholder = text_map.get(155, locale, user_locale)

    async def on_submit(self, interaction: Interaction) -> None:
        await interaction.response.defer()
        self.stop()