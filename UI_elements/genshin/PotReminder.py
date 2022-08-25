import discord
from apps.text_map.text_map_app import text_map
from debug import DefaultModal


class Modal(DefaultModal):
    threshold = discord.ui.TextInput(label="寶錢閥值")
    max_notif = discord.ui.TextInput(label="最大提醒值")

    def __init__(self, locale: discord.Locale, user_locale: str):
        super().__init__(title=text_map.get(515, locale, user_locale))
        self.threshold.label = text_map.get(516, locale, user_locale)
        self.max_notif.label = text_map.get(154, locale, user_locale)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        self.stop()
