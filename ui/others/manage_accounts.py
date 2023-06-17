from typing import List, Union

import discord
from discord import ui
from logingateway import HuTaoLoginAPI
from logingateway.exception import UserTokenNotFound
from apps.text_map.convert_locale import HUTAO_LOGIN_LANGS

import dev.asset as asset
import dev.config as config
from apps.db.tables.cookies import Cookie, Cookie, Cookie, Cookie
from apps.db.tables.hoyo_account import HoyoAccount, HoyoAccount, HoyoAccount, HoyoAccount
from apps.db.tables.user_settings import Settings, Settings, Settings, Settings
from apps.text_map import text_map, text_map, text_map, text_map
from dev.base_ui import BaseButton, BaseModal, BaseView
from dev.enum import GameType
from dev.models import DefaultEmbed, Inter, LoginInfo
from ui.others import acc_confirm
from utils import get_account_options


class View(BaseView):
    def __init__(self):
        super().__init__(timeout=config.long_timeout)

        self.lang: str
        self.accounts: List[HoyoAccount]
        self.author: Union[discord.User, discord.Member]

    async def _init(self, i: Inter):
        lang = await i.client.db.settings.get(i.user.id, Settings.LANG)
        self.lang = lang or str(i.locale)
        self.accounts = await i.client.db.users.get_all_of_user(i.user.id)

    async def start(self, i: Inter):
        await self._init(i)
        self.add_components()

        self.author = i.user
        embed = self.get_acc_embed()
        await i.response.send_message(embed=embed, view=self)
        self.message = await i.original_response()

    def add_components(self):
        self.clear_items()
        options = get_account_options(self.accounts)
        self.add_item(AddAccount(self.lang))
        self.add_item(RemoveAccount(self.lang, not self.accounts))
        self.add_item(ChangeNickname(self.lang, options))
        self.add_item(AccountSelect(self.lang, options))

    async def update(self, i: Inter, *, responded: bool = True):
        self.accounts = await i.client.db.users.get_all_of_user(i.user.id)
        embed = self.get_acc_embed()
        self.add_components()
        if responded:
            await i.edit_original_response(embed=embed, view=self)
        else:
            await i.response.edit_message(embed=embed, view=self)

    def get_acc_embed(self) -> DefaultEmbed:
        embed = DefaultEmbed()
        embed.set_title(780, self.lang, self.author)
        if not self.accounts:
            embed.description = text_map.get(545, self.lang)
        else:
            description = ""
            for account in self.accounts:
                if account.game is GameType.HSR:
                    game = text_map.get(770, self.lang)
                elif account.game is GameType.HONKAI:
                    game = text_map.get(771, self.lang)
                else:  # account.game is GameType.GENSHIN
                    game = text_map.get(313, self.lang)

                name = str(account.uid)
                if account.nickname:
                    name += f" ({account.nickname})"
                name += f" - {game}"

                if account.current:
                    name = f"__**{name}**__"
                description += f"• {name}\n"
            embed.description = description
        return embed


class AddAccount(ui.Button):
    def __init__(self, lang: str):
        super().__init__(
            emoji="<:person_add:1018764808251768832>",
            label=text_map.get(556, lang),
            style=discord.ButtonStyle.blurple,
        )
        self.view: View

    async def callback(self, i: Inter):
        lang = self.view.lang
        self.view.clear_items()
        self.view.add_item(GOBack())
        self.view.add_item(GenerateLink(lang))

        embed = DefaultEmbed(description=text_map.get(563, lang))
        embed.set_title(556, lang, i.user)
        await i.response.edit_message(embed=embed, view=self.view)


class GenerateLink(ui.Button):
    def __init__(self, lang: str):
        super().__init__(
            emoji="<:song_link:1021667672225763419>",
            label=text_map.get(401, lang),
            style=discord.ButtonStyle.blurple,
        )
        self.view: View

    async def callback(self, i: Inter):
        lang = self.view.lang

        gateway: HuTaoLoginAPI = i.client.gateway
        url, token = gateway.generate_login_url(
            user_id=str(i.user.id),
            guild_id=str(i.guild_id),
            channel_id=str(i.channel_id),
            language=HUTAO_LOGIN_LANGS.get(lang, "en"),
        )

        embed = DefaultEmbed(description=text_map.get(728, lang))
        embed.set_title(400, lang, i.user)
        embed.set_image(url="https://i.imgur.com/EJtdwoq.png")

        self.view.clear_items()
        self.view.add_item(GOBack())
        self.view.add_item(ui.Button(label=text_map.get(670, lang), url=url))
        self.view.add_item(NextStep(str(i.user.id), token, text_map.get(781, lang)))

        await i.response.edit_message(embed=embed, view=self.view)
        message = await i.original_response()

        i.client.token_store[token] = LoginInfo(message, self.view.lang, i.user)


class NextStep(BaseButton):
    def __init__(self, user_id: str, token: str, label: str):
        super().__init__(
            style=discord.ButtonStyle.blurple,
            label=label,
            emoji=asset.right_emoji,
        )
        self.user_id = user_id
        self.token = token
        self.view: View

    async def callback(self, i: Inter):
        await self.loading(i)
        api = i.client.gateway.api

        try:
            result = await api.resend_token(
                user_id=self.user_id,
                token=self.token,
                show_token=True,
                is_register_event=True,
            )
        except UserTokenNotFound:
            i.client.token_store.pop(self.token, "")
        else:
            if result:
                ltuid = int(result.ltuid)
                cookie = Cookie(
                    ltuid=ltuid, ltoken=result.ltoken, cookie_token=result.cookie_token
                )
                await i.client.db.cookies.insert(cookie)

                view = acc_confirm.View()
                return await view.start(i, ltuid)

        # Return into account manager page
        await self.restore(i)
        embed = self.view.get_acc_embed()
        self.view.add_components()
        await i.edit_original_response(embed=embed, view=self.view)


class ChangeNickname(ui.Button):
    def __init__(self, lang: str, select_options: List[discord.SelectOption]):
        disabled = bool(not select_options)
        super().__init__(
            emoji=asset.edit_emoji,
            label=text_map.get(600, lang),
            disabled=disabled,
        )
        self.view: View

    async def callback(self, i: Inter):
        modal = NicknameModal(self.view.lang)
        await i.response.send_modal(modal)
        await modal.wait()

        uid = await i.client.db.users.get_uid(i.user.id)
        await i.client.db.users.update(i.user.id, uid, nickname=modal.name.value)

        await self.view.update(i)


class NicknameModal(BaseModal):
    name = ui.TextInput(label="NICKNAME", max_length=15)

    def __init__(self, lang: str) -> None:
        super().__init__(title=text_map.get(600, lang), timeout=config.mid_timeout)
        self.name.label = text_map.get(601, lang)

    async def on_submit(self, i: Inter):
        await i.response.defer()
        self.stop()


class RemoveAccount(ui.Button):
    def __init__(self, lang: str, disabled: bool):
        super().__init__(
            emoji="<:person_remove:1018765604842377256>",
            label=text_map.get(557, lang),
            disabled=disabled,
            style=discord.ButtonStyle.red,
        )
        self.view: View

    async def callback(self, i: Inter):
        uid = await i.client.db.users.get_uid(i.user.id)
        await i.client.db.users.delete(i.user.id, uid)

        await self.view.update(i, responded=False)


class AccountSelect(ui.Select):
    def __init__(
        self,
        lang: str,
        options: List[discord.SelectOption],
    ):
        super().__init__(
            placeholder=text_map.get(559, lang),
            options=options or [discord.SelectOption(label="NONE", value="NONE")],
            disabled=not options,
            max_values=1,
        )
        self.view: View

    async def callback(self, i: Inter):
        await i.client.db.users.set_current(i.user.id, int(self.values[0]))
        await self.view.update(i, responded=False)


class GOBack(ui.Button):
    def __init__(self):
        super().__init__(
            emoji=asset.back_emoji,
        )
        self.view: View

    async def callback(self, i: Inter):
        await self.view.update(i, responded=False)
