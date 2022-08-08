from apps.text_map.text_map_app import text_map
from debug import DefaultView
from discord import Interaction, Locale
from discord.ui import Button, button
from utility.utils import default_embed


class View(DefaultView):
    def __init__(self, locale: Locale, user_locale: str | None):
        super().__init__(timeout=None)
        self.locale = locale
        self.user_locale = user_locale

    @button(emoji='<:windows:1005600225156673566>')
    async def pc(self, interaction: Interaction, button: Button):
        embed = default_embed(
            text_map.get(357, self.locale, self.user_locale),
            text_map.get(358, self.locale, self.user_locale)
        )
        code_message = "iex ((New-Object System.Net.WebClient).DownloadString('https://gist.githubusercontent.com/MadeBaruna/1d75c1d37d19eca71591ec8a31178235/raw/41853f2b76dcb845cf8cb0c44174fb63459920f4/getlink_global.ps1'))"
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

    @button(emoji='<:playstation:1005601741338841148>')
    async def ps(self, interaction: Interaction, button: Button):
        embed = default_embed(
            text_map.get(363, self.locale, self.user_locale),
            text_map.get(364, self.locale, self.user_locale)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
