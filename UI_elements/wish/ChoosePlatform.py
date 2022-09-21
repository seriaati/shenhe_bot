from apps.text_map.text_map_app import text_map
from UI_base_models import BaseView
from discord import Interaction, Locale
from discord.ui import Button, button
from utility.utils import default_embed
import config


class View(BaseView):
    def __init__(self, locale: Locale, user_locale: str | None):
        super().__init__(timeout=config.short_timeout)
        self.locale = locale
        self.user_locale = user_locale

    @button(emoji='<:windows:1005600225156673566>')
    async def pc(self, interaction: Interaction, button: Button):
        embed = default_embed(
            text_map.get(357, self.locale, self.user_locale),
            text_map.get(358, self.locale, self.user_locale)
        )
        code_message = "iex(irm https://gist.githubusercontent.com/MadeBaruna/1d75c1d37d19eca71591ec8a31178235/raw/d40fa0fd74d85d692543c1621669f5f9375b5975/getlink.ps1)"
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.followup.send(content=f'```{code_message}```', ephemeral=True)

    @button(emoji='<:android:1005600221797032076>')
    async def android(self, interaction: Interaction, button: Button):
        embed = default_embed(
            text_map.get(359, self.locale, self.user_locale),
            text_map.get(360, self.locale, self.user_locale)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @button(emoji='<:applelogo:1005601193042653184>')
    async def ios(self, interaction: Interaction, button: Button):
        embed = default_embed(
            text_map.get(361, self.locale, self.user_locale),
            text_map.get(362, self.locale, self.user_locale)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)