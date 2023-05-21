from typing import Dict, List, Union

import aiohttp
import discord
from discord import ui

from apps.db.tables.user_account import UserAccount, convert_game_type
from apps.db.tables.user_settings import Settings
from apps.text_map import text_map
from dev.asset import gift_open_outline, peko_yahoo
from dev.base_ui import (BaseGameSelector, BaseModal, BaseView,
                         get_error_handle_embed)
from dev.config import mid_timeout
from dev.enum import GameType
from dev.models import DefaultEmbed, ErrorEmbed, Inter


class View(BaseView):
    def __init__(self):
        super().__init__(timeout=mid_timeout)

        self.lang: str
        self.game: GameType
        self.user: UserAccount

    async def init(self, i: Inter):
        lang = await i.client.db.settings.get(i.user.id, Settings.LANG)
        self.lang = lang or str(i.locale)
        self.game = await i.client.db.settings.get(i.user.id, Settings.DEFAULT_GAME)
        self.user = await i.client.db.users.get(i.user.id)

    async def start(self, i: Inter):
        await i.response.defer()
        await self.init(i)

        codes = await i.client.db.codes.get_all()
        self.add_components(codes)
        embed = self._make_start_embed(i.user)

        self.author = i.user
        await i.followup.send(embed=embed, view=self)
        self.message = await i.original_response()

    def add_components(self, codes: List[str]) -> None:
        self.clear_items()
        self.add_item(RedeemCode(text_map.get(776, self.lang)))
        self.add_item(CodeSelector(codes, text_map.get(774, self.lang)))
        self.add_item(GameSelector(self.lang, self.game))

    def _make_start_embed(
        self, user: Union[discord.User, discord.Member]
    ) -> DefaultEmbed:
        embed = DefaultEmbed(text_map.get(776, self.lang), text_map.get(777, self.lang))
        embed.set_user_footer(user, self.user.uid)
        return embed

    async def redeem_code(
        self, code: str, user: Union[discord.User, discord.Member]
    ) -> discord.Embed:
        client = self.user.client
        uid = self.user.uid if self.game is GameType.GENSHIN else self.user.hsr_uid
        try:
            await client.redeem_code(code, uid, game=convert_game_type(self.game))
        except Exception as e:  # skipcq: PYL-W0703
            embed = get_error_handle_embed(user, e, self.lang)
        else:
            embed = DefaultEmbed(
                text_map.get(109, self.lang),
            )
        if embed.description is None:
            embed.description = ""
        embed.description += f"\n\n{text_map.get(108, self.lang)}: **{code}**"
        return embed

    async def redeem_response(self, i: Inter, code: str) -> None:
        embed = await self.redeem_code(code, i.user)
        success = not isinstance(embed, ErrorEmbed)
        view = View()
        if success:
            view.add_item(MeToo(text_map.get(132, self.lang), code))
        else:
            view.add_item(WebsiteRedeem(code, self.game, text_map.get(768, self.lang)))
        await i.followup.send(embed=embed, ephemeral=not success, view=view)
        view.message = await i.original_response()


class RedeemCode(ui.Button):
    def __init__(self, label: str):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label=label,
            emoji=gift_open_outline,
            row=0,
        )
        self.view: View

    async def callback(self, i: Inter):
        modal = CodeModal(self.view.lang)
        await i.response.send_modal(modal)
        await modal.wait()
        codes = (modal.code_1.value, modal.code_2.value, modal.code_3.value)
        for code in codes:
            if code:
                await self.view.redeem_response(i, code)


class CodeModal(BaseModal):
    code_1 = ui.TextInput(
        label="Code 1",
        placeholder="5A92W9JZBLCH",
        max_length=16,
        required=True,
    )
    code_2 = ui.TextInput(
        label="Code 2",
        placeholder="2SRKFQ2YSMVV",
        max_length=16,
        required=False,
    )
    code_3 = ui.TextInput(
        label="Code 3",
        placeholder="XT82F8JZS4TR",
        max_length=16,
        required=False,
    )

    def __init__(self, lang: str):
        super().__init__(
            title=text_map.get(776, lang),
            timeout=mid_timeout,
            custom_id="redeem_code_modal",
        )
        self.code_1.label = f"{text_map.get(108, lang)} 1"
        self.code_2.label = f"{text_map.get(108, lang)} 2"
        self.code_3.label = f"{text_map.get(108, lang)} 3"

    async def on_submit(self, i: Inter):
        await i.response.defer()
        self.stop()


class CodeSelector(ui.Select):
    def __init__(self, codes: List[str], placeholder: str):
        options = [discord.SelectOption(label=code, value=code) for code in codes]
        disabled = False
        if not options:
            options = [discord.SelectOption(label="No codes available", value="")]
            disabled = True
        super().__init__(
            options=options,
            placeholder=placeholder,
            disabled=disabled,
            row=1,
            custom_id="code_selector",
        )
        self.view: View

    async def callback(self, i: Inter):
        await i.response.defer()
        await self.view.redeem_response(i, self.values[0])


class GameSelector(BaseGameSelector):
    def __init__(self, lang: str, game: GameType):
        super().__init__(lang, game, row=2)
        self.view: View

    async def callback(self, i: Inter):
        await self.loading(i)
        self.view.game = GameType(self.values[0])
        if self.values[0] == GameType.GENSHIN.value:
            codes = await self.view.get_codes(i.client.session)
        else:
            codes = []
        self.view.add_components(codes)
        await i.edit_original_response(view=self.view)


class MeToo(ui.Button):
    def __init__(self, label: str, code: str):
        super().__init__(
            style=discord.ButtonStyle.gray,
            label=label,
            emoji=peko_yahoo,
            row=0,
        )

        self.view: View
        self.code = code

    async def callback(self, i: Inter):
        await i.response.defer()
        await self.view.init(i)
        await self.view.redeem_response(i, self.code)


class WebsiteRedeem(ui.Button):
    def __init__(self, code: str, game: GameType, label: str):
        if game is GameType.HSR:
            url = "https://hsr.hoyoverse.com/gift"
        else:
            url = "https://genshin.mihoyo.com/en/gift"

        super().__init__(label=label, url=f"{url}?code={code}")
