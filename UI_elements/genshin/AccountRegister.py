from typing import Any
from apps.text_map.utils import get_user_locale

import config
from apps.genshin.genshin_app import GenshinApp
from apps.text_map.text_map_app import text_map
from debug import DefaultModal, DefaultView
from discord import Interaction, Locale, SelectOption, TextStyle, ButtonStyle
from discord.ui import Modal, Select, TextInput, Button

from utility.utils import error_embed


class Modal(DefaultModal):
    cookie = TextInput(label="Cookie", style=TextStyle.long)

    def __init__(
        self,
        genshin_app: GenshinApp,
        locale: Locale,
        user_locale: str,
        bbs: bool = False,
    ) -> None:
        super().__init__(
            title="CookieModal", timeout=config.mid_timeout, custom_id="cookie_modal"
        )
        self.title = text_map.get(132, locale, user_locale)
        self.cookie.placeholder = text_map.get(133, locale, user_locale)
        self.locale = locale
        self.user_locale = user_locale
        self.genshin_app = genshin_app
        self.bbs = bbs
        self.bbs_uid = TextInput(label="UID")
        if bbs:
            self.add_item(self.bbs_uid)

    async def on_submit(self, i: Interaction) -> None:
        await i.response.defer(ephemeral=True)
        if self.bbs:
            if not self.bbs_uid.value.isnumeric():
                return await i.followup.send(
                    embed=error_embed(
                        message=text_map.get(187, i.locale, self.user_locale)
                    ).set_author(
                        name=text_map.get(190, i.locale, self.user_locale),
                        icon_url=i.user.display_avatar.url,
                    ),
                    ephemeral=True,
                )
            result, success = await self.genshin_app.set_cookie(
                i.user.id, self.cookie.value, i.locale, int(self.bbs_uid.value), True
            )
        else:
            result, success = await self.genshin_app.set_cookie(
                i.user.id, self.cookie.value, i.locale
            )
        if not success:
            return await i.followup.send(embed=result, ephemeral=True)
        if isinstance(result, list):  # 有多個帳號
            view = View(self, result)
            message = await i.followup.send(view=view, ephemeral=True)
            view.message = message
        else:  # 一個帳號而已
            await i.followup.send(embed=result, ephemeral=True)


class View(DefaultView):
    def __init__(self, cookie_modal: Modal, options: list[SelectOption]) -> None:
        super().__init__(timeout=config.short_timeout)
        self.cookie = cookie_modal.cookie
        self.genshin_app = cookie_modal.genshin_app
        self.locale = cookie_modal.locale
        self.user_locale = cookie_modal.user_locale
        self.add_item(UIDSelect(self, options))


class UIDSelect(Select):
    def __init__(self, uid_view: View, options: list[SelectOption]) -> None:
        super().__init__(
            placeholder=text_map.get(136, uid_view.locale, uid_view.user_locale),
            options=options,
        )
        self.view: View

    async def callback(self, i: Interaction) -> Any:
        await i.response.defer()
        result, success = await self.view.genshin_app.set_cookie(
            i.user.id, self.view.cookie.value, i.locale, int(self.values[0])
        )
        await i.followup.send(embed=result, ephemeral=True)


class BBSServerButton(Button):
    def __init__(self, label: str):
        super().__init__(label=label, style=ButtonStyle.blurple)

    async def callback(self, i: Interaction) -> Any:
        user_locale = await get_user_locale(
            i.user.id,
        )
        await i.response.send_modal(Modal(self.genshin_app, i.locale, user_locale))
