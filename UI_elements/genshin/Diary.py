from UI_base_models import BaseView
from discord import Interaction, Locale, User
from discord.ui import Button
from apps.text_map.text_map_app import text_map
from apps.genshin.genshin_app import GenshinApp
from utility.utils import error_embed
import config


class View(BaseView):
    def __init__(
        self,
        author: User,
        member: User,
        genshin_app: GenshinApp,
        locale: Locale,
        user_locale: str,
    ):
        super().__init__(timeout=config.mid_timeout)
        self.author = author
        self.member = member
        self.genshin_app = genshin_app
        self.locale = locale
        self.user_locale = user_locale
        self.add_item(Primo(text_map.get(70, locale, user_locale)))
        self.add_item(Mora(text_map.get(72, locale, user_locale)))


class Primo(Button):
    def __init__(self, label: str):
        super().__init__(label=label, emoji="<:PRIMO:1010048703312171099>")

    async def callback(self, i: Interaction):
        await i.response.defer(ephemeral=True)
        self.view: View
        result = await self.view.genshin_app.get_diary_logs(
            self.view.member.id, True, i.locale
        )
        await i.followup.send(embed=result, ephemeral=True)


class Mora(Button):
    def __init__(self, label: str):
        super().__init__(label=label, emoji="<:MORA:1010048704901828638>")

    async def callback(self, i: Interaction):
        await i.response.defer(ephemeral=True)
        self.view: View
        result = await self.view.genshin_app.get_diary_logs(
            self.view.member.id, False, i.locale
        )
        await i.followup.send(embed=result, ephemeral=True)
