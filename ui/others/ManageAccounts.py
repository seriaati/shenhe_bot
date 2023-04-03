import asyncio
from typing import List

import asyncpg
import discord
from discord import ui
from logingateway import HuTaoLoginAPI
from logingateway.exception import UserTokenNotFound

import dev.asset as asset
import config
from apps.db import get_user_lang
from apps.genshin import get_account_select_options, get_uid_region_hash
from apps.text_map import text_map, to_hutao_login_lang
from dev.base_ui import BaseModal, BaseView
from cogs.login import register_user
from dev.models import CustomInteraction, DefaultEmbed, ShenheBot
from utility import log


class View(BaseView):
    def __init__(
        self, locale: discord.Locale | str, select_options: List[discord.SelectOption]
    ):
        super().__init__(timeout=config.long_timeout)
        self.locale = locale
        self.select_options = select_options
        self.add_item(AddAccount(locale))
        self.add_item(RemoveAccount(locale, bool(not select_options)))
        self.add_item(ChangeNickname(locale, select_options))
        self.add_item(SwitchAccount(locale, select_options))


class AddAccount(ui.Button):
    def __init__(self, locale: discord.Locale | str):
        super().__init__(
            emoji="<:person_add:1018764808251768832>",
            label=text_map.get(556, locale),
            style=discord.ButtonStyle.blurple,
        )
        self.view: View

    async def callback(self, i: CustomInteraction):
        await add_account_callback(self.view, i)


async def add_account_callback(view: View, i: CustomInteraction):
    locale = view.locale
    await i.response.defer()
    view.clear_items()
    view.add_item(GOBack())
    view.add_item(GenerateLink(locale))
    embed = DefaultEmbed(description=text_map.get(563, locale))
    embed.set_author(name=text_map.get(556, locale), icon_url=i.user.display_avatar.url)
    embed.set_image(url="https://i.imgur.com/r31nQMN.png")
    await i.edit_original_response(embed=embed, view=view)


class GenerateLink(ui.Button):
    def __init__(self, locale: discord.Locale | str):
        super().__init__(
            emoji="<:song_link:1021667672225763419>",
            label=text_map.get(401, locale),
            style=discord.ButtonStyle.blurple,
        )
        self.view: View

    async def callback(self, i: CustomInteraction):
        locale = self.view.locale

        embed = DefaultEmbed().set_author(
            name=text_map.get(402, locale), icon_url=asset.loader
        )
        self.disabled = True
        await i.response.edit_message(embed=embed, view=self.view)

        gateway: HuTaoLoginAPI = i.client.gateway  # type: ignore
        url, token = gateway.generate_login_url(
            user_id=str(i.user.id),
            guild_id=str(i.guild_id),
            channel_id=str(i.channel_id),
            language=to_hutao_login_lang(locale),
        )

        embed = DefaultEmbed(description=text_map.get(728, locale))
        embed.set_author(
            name=text_map.get(400, locale), icon_url=i.user.display_avatar.url
        )

        await asyncio.sleep(1)
        self.view.clear_items()
        self.view.add_item(GOBack(layer=2, blurple=True))
        self.view.add_item(ResendToken(str(i.user.id), token))
        self.view.add_item(ui.Button(label=text_map.get(670, locale), url=url))

        message = await i.edit_original_response(embed=embed, view=self.view)

        i.client.tokenStore[token] = {  # type: ignore
            "message": message,
            "locale": self.view.locale,
            "interaction": i,
            "author": i.user,
        }

        await i.client.reload_extension("cogs.login")  # type: ignore


class ResendToken(ui.Button):
    def __init__(self, user_id: str, token: str):
        super().__init__(emoji=asset.reload_emoji, style=discord.ButtonStyle.green)
        self.user_id = user_id
        self.token = token
        self.view: View

    async def callback(self, i: CustomInteraction):
        bot: ShenheBot = i.client  # type: ignore

        await i.response.defer()
        api = bot.gateway.api

        try:
            result = await api.resend_token(
                user_id=self.user_id,
                token=self.token,
                show_token=True,
                is_register_event=True,
            )
        except UserTokenNotFound:
            log.warning(
                f"User ID {self.user_id} was not found in database. (Token key: {self.token})"
            )
            bot.tokenStore.pop(self.token, "")
        else:
            if not result:
                raise AssertionError
            await register_user(result, int(result.uid), int(result.user_id), bot.pool)

            try:
                await i.edit_original_response(
                    embed=DefaultEmbed().set_author(
                        name=text_map.get(39, self.view.locale),
                        icon_url=i.user.display_avatar.url,
                    ),
                    view=None,
                )
            except discord.HTTPException:
                pass

            # Reload gateway
            return await bot.reload_extension("cogs.login")

        # Return into account manager page
        await return_accounts(i)


class ChangeNickname(ui.Button):
    def __init__(
        self, locale: discord.Locale | str, select_options: List[discord.SelectOption]
    ):
        disabled = bool(not select_options)
        super().__init__(
            emoji=asset.edit_emoji,
            label=text_map.get(600, locale),
            disabled=disabled,
        )
        self.view: View

    async def callback(self, i: CustomInteraction):
        self.view.clear_items()
        self.view.add_item(
            SwitchAccount(
                self.view.locale, self.view.select_options, change_nickname=True
            )
        )
        self.view.add_item(GOBack())
        embed = DefaultEmbed().set_author(
            name=text_map.get(602, self.view.locale), icon_url=i.user.display_avatar.url
        )
        await i.response.edit_message(embed=embed, view=self.view)


class NicknameModal(BaseModal):
    name = ui.TextInput(label="Nickname", placeholder="Nickname", max_length=15)

    def __init__(self, locale: discord.Locale | str, uid: str) -> None:
        super().__init__(title=text_map.get(600, locale), timeout=config.mid_timeout)
        self.locale = locale
        self.uid = uid
        self.name.label = text_map.get(601, locale)
        self.name.placeholder = text_map.get(601, locale).lower()

    async def on_submit(self, i: CustomInteraction):
        await i.client.pool.execute(
            "UPDATE user_accounts SET nickname = $1 WHERE uid = $2 AND user_id = $3",
            self.name.value,
            int(self.uid),
            i.user.id,
        )
        await return_accounts(i)


class RemoveAccount(ui.Button):
    def __init__(self, locale: discord.Locale | str, disabled: bool):
        super().__init__(
            emoji="<:person_remove:1018765604842377256>",
            label=text_map.get(557, locale),
            disabled=disabled,
            style=discord.ButtonStyle.red,
        )
        self.view: View

    async def callback(self, i: CustomInteraction):
        locale = self.view.locale
        self.view.clear_items()
        account_select = SwitchAccount(locale, self.view.select_options, True)
        account_select.placeholder = text_map.get(136, locale)
        self.view.add_item(account_select)
        self.view.add_item(GOBack())
        embed = DefaultEmbed().set_author(
            name=text_map.get(560, locale), icon_url=i.user.display_avatar.url
        )
        await i.response.edit_message(embed=embed, view=self.view)


class SwitchAccount(ui.Select):
    def __init__(
        self,
        locale: discord.Locale | str,
        select_options: List[discord.SelectOption],
        remove_account: bool = False,
        change_nickname: bool = False,
    ):
        disabled = False
        if not select_options:
            select_options = [discord.SelectOption(label="None", value="None")]
            disabled = True
        self.remove_account = remove_account
        self.change_nickname = change_nickname
        super().__init__(
            placeholder=text_map.get(559, locale),
            options=select_options,
            disabled=disabled,
            max_values=len(select_options) if self.remove_account else 1,
        )
        self.view: View

    async def callback(self, i: CustomInteraction):
        pool: asyncpg.pool.Pool = i.client.pool  # type: ignore

        if self.remove_account:
            for uid in self.values:
                await pool.execute(
                    "DELETE FROM user_accounts WHERE uid = $1 AND user_id = $2",
                    int(uid),
                    i.user.id,
                )
            embed = DefaultEmbed().set_author(
                name=text_map.get(561, self.view.locale),
                icon_url=i.user.display_avatar.url,
            )
            for item in self.view.children:
                if isinstance(item, (ui.Button, ui.Select)):
                    item.disabled = True
            await i.response.edit_message(embed=embed, view=self.view)
            await asyncio.sleep(1.5)
            await return_accounts(i)
        elif self.change_nickname:
            modal = NicknameModal(self.view.locale, self.values[0])
            await i.response.send_modal(modal)
        else:
            await pool.execute(
                "UPDATE user_accounts SET current = false WHERE user_id = $1",
                i.user.id,
            )
            await pool.execute(
                "UPDATE user_accounts SET current = true WHERE uid = $1 AND user_id = $2",
                int(self.values[0]),
                i.user.id,
            )
            await return_accounts(i)


class GOBack(ui.Button):
    def __init__(self, layer: int = 1, blurple: bool = False):
        super().__init__(
            emoji=asset.back_emoji,
            style=discord.ButtonStyle.blurple if blurple else discord.ButtonStyle.gray,
        )
        self.layer = layer
        self.view: View

    async def callback(self, i: CustomInteraction):
        if self.layer == 2:
            await add_account_callback(self.view, i)
        else:
            await return_accounts(i)


async def return_accounts(i: CustomInteraction):
    locale = await get_user_lang(i.user.id, i.client.pool) or i.locale
    accounts: List[asyncpg.Record] = await i.client.pool.fetch(
        "SELECT uid, ltuid, current, nickname FROM user_accounts WHERE user_id = $1",
        i.user.id,
    )

    if not accounts:
        view = View(locale, [])
        embed = DefaultEmbed().set_author(
            name=text_map.get(545, locale),
            icon_url=i.user.display_avatar.url,
        )
        try:
            await i.response.edit_message(
                embed=embed,
                view=view,
            )
            view.message = await i.original_response()
        except discord.InteractionResponded:
            view.message = await i.edit_original_response(embed=embed, view=view)
        return

    account_str = ""
    found_current = False
    for account in accounts:
        emoji = (
            "<:cookie_add:1018776813922693120> Cookie"
            if account["ltuid"]
            else "<:number:1018838745614667817> UID"
        )
        nickname = f"{account['nickname']} | " if account[3] is not None else ""
        if len(nickname) > 15:
            nickname = nickname[:15] + "..."
        if account["current"]:
            found_current = True
            account_str += f"• __**{nickname}{account['uid']} | {text_map.get(get_uid_region_hash(account[0]), locale)} | {text_map.get(569, locale)}: {emoji}**__\n"
        else:
            account_str += f"• {nickname}{account[0]} | {text_map.get(get_uid_region_hash(account[0]), locale)} | {text_map.get(569, locale)}: {emoji}\n"

    select_options = get_account_select_options(accounts, locale)
    if not found_current:
        await i.client.pool.execute(
            "UPDATE user_accounts SET current = true WHERE user_id = $1 AND uid = $2",
            i.user.id,
            accounts[0]["uid"],
        )
        return await return_accounts(i)

    embed = DefaultEmbed(description=account_str).set_author(
        name=text_map.get(555, locale),
        icon_url=i.user.display_avatar.url,
    )

    view = View(locale, select_options)
    try:
        await i.response.edit_message(embed=embed, view=view)
        view.message = await i.original_response()
    except discord.InteractionResponded:
        view.message = await i.edit_original_response(embed=embed, view=view)
    view.author = i.user
