import traceback
from typing import Any

from debug import DebugView, DefaultView
from discord import Interaction, Locale, SelectOption, TextStyle
from discord.ui import Modal, Select, TextInput
from apps.genshin.genshin_app import GenshinApp
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from utility.utils import error_embed


class Modal(Modal):
    cookie = TextInput(
        label='Cookie',
        style=TextStyle.long,
        required=True
    )

    def __init__(self, genshin_app: GenshinApp, locale: Locale, user_locale: str) -> None:
        super().__init__(title='CookieModal', timeout=None, custom_id='cookie_modal')
        self.title = text_map.get(132, locale, user_locale)
        self.cookie.placeholder = text_map.get(
            133, locale, user_locale)
        self.locale = locale
        self.user_locale = user_locale
        self.genshin_app = genshin_app

    async def on_submit(self, i: Interaction) -> None:
        await i.response.defer(ephemeral=True)
        result, success = await self.genshin_app.set_cookie(i.user.id, self.cookie.value, i.locale)
        if not success:
            return await i.followup.send(embed=result, ephemeral=True)
        if isinstance(result, list):  # 有多個帳號
            await i.followup.send(view=View(self, result), ephemeral=True)
        else:  # 一個帳號而已
            await i.followup.send(embed=result, ephemeral=True)

    async def on_error(self, i: Interaction, error: Exception) -> None:
        user_locale = await get_user_locale(i.user.id, self.genshin_app.db)
        embed = error_embed(message=text_map.get(
            134, i.locale, user_locale))
        embed.set_author(name=text_map.get(
            135, i.locale, user_locale), icon_url=i.user.avatar)
        traceback_message = traceback.format_exc()
        view = DebugView(traceback_message)
        await i.followup.send(embed=embed, view=view)


class View(DefaultView):
    def __init__(self, cookie_modal: Modal, options: list[SelectOption]) -> None:
        super().__init__(timeout=None)
        self.cookie = cookie_modal.cookie
        self.genshin_app = cookie_modal.genshin_app
        self.locale = cookie_modal.locale
        self.user_locale = cookie_modal.user_locale
        self.add_item(UIDSelect(self, options))


class UIDSelect(Select):
    def __init__(self, uid_view: View, options: list[SelectOption]) -> None:
        super().__init__(placeholder=text_map.get(
            136, uid_view.locale, uid_view.user_locale), options=options)
        self.view: View

    async def callback(self, i: Interaction) -> Any:
        await i.response.defer()
        result, success = await self.view.genshin_app.set_cookie(
            i.user.id, self.view.cookie.value, i.locale, int(self.values[0]))
        await i.followup.send(embed=result, ephemeral=True)
