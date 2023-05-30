import discord
from discord import ui

import dev.asset as asset
import dev.config as config
from apps.db.tables.user_settings import Settings
from apps.text_map import text_map
from dev.base_ui import BaseView, GoBackButton
from dev.models import DefaultEmbed, Inter, OriginalInfo


class View(BaseView):
    def __init__(
        self, lang: discord.Locale | str, current: bool, original_info: OriginalInfo
    ):
        super().__init__(timeout=config.mid_timeout)
        self.add_item(NotificationButton(lang, True, current))
        self.add_item(NotificationButton(lang, False, current))

        self.original_info = original_info


class NotificationButton(ui.Button):
    def __init__(self, lang: discord.Locale | str, toggle: bool, current: bool):
        super().__init__(
            emoji=asset.bell_outline if toggle else asset.bell_off_outline,
            label=text_map.get(99 if toggle else 100, lang),
            style=discord.ButtonStyle.primary
            if current == toggle
            else discord.ButtonStyle.secondary,
        )
        self.toggle = toggle
        self.lang = lang
        self.view: View

    async def callback(self, i: Inter):
        await i.client.pool.execute(
            "UPDATE user_settings SET notification = $1 WHERE user_id = $2",
            self.toggle,
            i.user.id,
        )
        if self.view.original_info is None:
            raise AssertionError
        await return_view(i, self.lang, self.view.original_info)


async def return_view(
    i: Inter, lang: discord.Locale | str, original_info: OriginalInfo
):
    notif = await i.client.db.settings.get(i.user.id, Settings.NOTIFICATION)
    view = View(lang, notif, original_info)
    view.add_item(GoBackButton(original_info))
    embed = DefaultEmbed(description=text_map.get(138, lang))
    embed.set_author(name=text_map.get(137, lang), icon_url=i.user.display_avatar.url)
    await i.response.edit_message(embed=embed, view=view)
    view.author = i.user
    view.message = await i.original_response()
