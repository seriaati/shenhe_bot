from debug import DefaultView
from discord import Interaction, Locale, Member
from discord.ui import Button
from apps.text_map.text_map_app import text_map
from apps.genshin.genshin_app import GenshinApp
from utility.utils import error_embed
import config


class View(DefaultView):
    def __init__(self, author: Member, member: Member, genshin_app: GenshinApp, locale: Locale, user_locale: str):
        super().__init__(timeout=config.mid_timeout)
        self.author = author
        self.member = member
        self.genshin_app = genshin_app
        self.locale = locale
        self.user_locale = user_locale
        self.add_item(Primo(
            text_map.get(144, locale, user_locale)))
        self.add_item(Mora(
            text_map.get(145, locale, user_locale)))

    async def interaction_check(self, i: Interaction) -> bool:
        if i.user.id != self.author.id:
            await i.response.send_message(embed=error_embed().set_author(name=text_map.get(143, self.locale, self.user_locale), icon_url=i.user.avatar))
        return self.author.id == i.user.id


class Primo(Button):
    def __init__(self, label: str):
        super().__init__(label=label, emoji='<:PRIMO:1010048703312171099>')

    async def callback(self, i: Interaction):
        self.view: View
        result, success = await self.view.genshin_app.get_diary_logs(self.view.member.id, i.locale)
        if not success:
            await i.response.send_message(embed=result, ephemeral=True)
        result = result[0]
        await i.response.send_message(embed=result, ephemeral=True)


class Mora(Button):
    def __init__(self, label: str):
        super().__init__(label=label, emoji='<:MORA:1010048704901828638>')

    async def callback(self, i: Interaction):
        self.view: View
        result, success = await self.view.genshin_app.get_diary_logs(self.view.member.id, i.locale)
        if not success:
            await i.response.send_message(embed=result, ephemeral=True)
        result = result[1]
        await i.response.send_message(embed=result, ephemeral=True)
