import asyncio
from typing import List

import aiosqlite
from discord import ButtonStyle, Interaction, Locale, SelectOption
from discord.errors import InteractionResponded
from discord.ui import Button, Select, TextInput

import config
from apps.genshin.utils import get_uid_region
from apps.text_map.convert_locale import to_hutao_login_lang
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from UI_base_models import BaseModal, BaseView
from utility.utils import default_embed


class View(BaseView):
    def __init__(self, locale: Locale | str, select_options: List[SelectOption]):
        super().__init__(timeout=config.long_timeout)
        self.locale = locale
        self.select_options = select_options
        self.add_item(AddAccount(locale))
        self.add_item(RemoveAccount(locale, True if not select_options else False))
        self.add_item(ChangeNickname(locale, select_options))
        self.add_item(SwitchAccount(locale, select_options))


class AddAccount(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(
            emoji="<:person_add:1018764808251768832>",
            label=text_map.get(556, locale),
            style=ButtonStyle.blurple,
        )

    async def callback(self, i: Interaction):
        await add_account_callback(self.view, i)


async def add_account_callback(view: View, i: Interaction):
    view: View
    locale = view.locale
    await i.response.defer()
    view.clear_items()
    view.add_item(GOBack())
    view.add_item(GenerateLink(locale))
    embed = default_embed(message=text_map.get(563, locale)).set_author(
        name=text_map.get(556, locale), icon_url=i.user.display_avatar.url
    )
    await i.edit_original_response(embed=embed, view=view)


class GenerateLink(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(
            emoji="<:song_link:1021667672225763419>",
            label=text_map.get(401, locale),
            style=ButtonStyle.blurple,
        )

    async def callback(self, i: Interaction):
        self.view: View
        locale = self.view.locale
        embed = default_embed().set_author(
            name=text_map.get(402, locale), icon_url="https://i.imgur.com/V76M9Wa.gif"
        )
        self.disabled = True
        await i.response.edit_message(embed=embed, view=self.view)
        url, token = i.client.gateway.generate_login_url(
            user_id=str(i.user.id),
            guild_id=str(i.guild_id),
            channel_id=str(i.channel_id),
            language=to_hutao_login_lang(locale),
        )
        embed = default_embed().set_author(
            name=text_map.get(400, locale), icon_url=i.user.display_avatar.url
        )
        await asyncio.sleep(1)
        self.view.clear_items()
        self.view.add_item(GOBack(layer=2, blurple=True))
        self.view.add_item(Button(label=text_map.get(670, locale), url=url))
        message = await i.edit_original_response(embed=embed, view=self.view)
        i.client.tokenStore[token] = {
            "message": message,
            "locale": self.view.locale,
            "interaction": i,
            "author": i.user,
        }


class ChangeNickname(Button):
    def __init__(self, locale: Locale | str, select_options: List[SelectOption]):
        disabled = True if not select_options else False
        super().__init__(
            emoji="<:edit:1020096204924784700>",
            label=text_map.get(600, locale),
            disabled=disabled,
        )

    async def callback(self, i: Interaction):
        self.view: View
        self.view.clear_items()
        self.view.add_item(
            SwitchAccount(
                self.view.locale, self.view.select_options, change_nickname=True
            )
        )
        self.view.add_item(GOBack())
        embed = default_embed().set_author(
            name=text_map.get(602, self.view.locale), icon_url=i.user.display_avatar.url
        )
        await i.response.edit_message(embed=embed, view=self.view)


class NicknameModal(BaseModal):
    name = TextInput(label="Nickname", placeholder="Nickname", max_length=15)

    def __init__(self, locale: Locale | str, uid: str) -> None:
        super().__init__(title=text_map.get(600, locale), timeout=config.mid_timeout)
        self.locale = locale
        self.uid = uid
        self.name.label = text_map.get(601, locale)
        self.name.placeholder = text_map.get(601, locale).lower()

    async def on_submit(self, i: Interaction):
        c: aiosqlite.Cursor = await i.client.db.cursor()
        await c.execute(
            "UPDATE user_accounts SET nickname = ? WHERE uid = ? AND user_id = ?",
            (self.name.value, self.uid, i.user.id),
        )
        await i.client.db.commit()
        await return_accounts(i)


class RemoveAccount(Button):
    def __init__(self, locale: Locale | str, disabled: bool):
        super().__init__(
            emoji="<:person_remove:1018765604842377256>",
            label=text_map.get(557, locale),
            disabled=disabled,
            style=ButtonStyle.red,
        )

    async def callback(self, i: Interaction):
        self.view: View
        locale = self.view.locale
        self.view.clear_items()
        account_select = SwitchAccount(locale, self.view.select_options, True)
        account_select.placeholder = text_map.get(136, locale)
        self.view.add_item(account_select)
        self.view.add_item(GOBack())
        embed = default_embed().set_author(
            name=text_map.get(560, locale), icon_url=i.user.display_avatar.url
        )
        await i.response.edit_message(embed=embed, view=self.view)


class SwitchAccount(Select):
    def __init__(
        self,
        locale: Locale | str,
        select_options: List[SelectOption],
        remove_account: bool = False,
        change_nickname: bool = False,
    ):
        disabled = False
        if not select_options:
            select_options = [SelectOption(label="None", value="None")]
            disabled = True
        self.remove_account = remove_account
        self.change_nickname = change_nickname
        super().__init__(
            placeholder=text_map.get(559, locale),
            options=select_options,
            disabled=disabled,
            max_values=len(select_options) if self.remove_account else 1,
        )

    async def callback(self, i: Interaction):
        self.view: View
        c: aiosqlite.Cursor = await i.client.db.cursor()
        if self.remove_account:
            for uid in self.values:
                await c.execute(
                    "DELETE FROM user_accounts WHERE uid = ? AND user_id = ?",
                    (uid, i.user.id),
                )
            embed = default_embed().set_author(
                name=text_map.get(561, self.view.locale),
                icon_url=i.user.display_avatar.url,
            )
            for item in self.view.children:
                item.disabled = True
            await i.response.edit_message(embed=embed, view=self.view)
            await asyncio.sleep(2)
            await return_accounts(i)
        elif self.change_nickname:
            modal = NicknameModal(self.view.locale, self.values[0])
            await i.response.send_modal(modal)
        else:
            await c.execute(
                "UPDATE user_accounts SET current = 0 WHERE user_id = ?", (i.user.id,)
            )
            await c.execute(
                "UPDATE user_accounts SET current = 1 WHERE uid = ? AND user_id = ?",
                (self.values[0], i.user.id),
            )
            await return_accounts(i)
        await i.client.db.commit()


class GOBack(Button):
    def __init__(self, layer: int = 1, blurple: bool = False):
        super().__init__(
            emoji="<:left:982588994778972171>",
            style=ButtonStyle.blurple if blurple else ButtonStyle.gray,
        )
        self.layer = layer

    async def callback(self, i: Interaction):
        if self.layer == 2:
            await add_account_callback(self.view, i)
        else:
            await return_accounts(i)


async def return_accounts(i: Interaction):
    user_locale = await get_user_locale(i.user.id, i.client.db)
    c: aiosqlite.Cursor = await i.client.db.cursor()
    await c.execute(
        "SELECT uid, ltuid, current, nickname FROM user_accounts WHERE user_id = ?",
        (i.user.id,),
    )
    accounts = await c.fetchall()
    select_options = []
    view = View(user_locale or i.locale, select_options)
    if not accounts:
        embed = default_embed().set_author(
            name=text_map.get(545, i.locale, user_locale),
            icon_url=i.user.display_avatar.url,
        )
        try:
            await i.response.edit_message(
                embed=embed,
                view=view,
            )
            view.message = await i.original_response()
        except InteractionResponded:
            view.message = await i.edit_original_response(embed=embed, view=view)
        return
    account_str = ""
    current_account = False
    for account in accounts:
        emoji = (
            "<:cookie_add:1018776813922693120>"
            if account[1] is not None
            else "<:number:1018838745614667817>"
        )
        nickname = f"{account[3]} | " if account[3] is not None else ""
        if len(nickname) > 15:
            nickname = nickname[:15] + "..."
        if account[2] == 1:
            current_account = True
            account_str += f"• __**{nickname}{account[0]} | {text_map.get(get_uid_region(account[0]), i.locale, user_locale)} | {emoji}**__\n"
        else:
            account_str += f"• {nickname}{account[0]} | {text_map.get(get_uid_region(account[0]), i.locale, user_locale)} | {emoji}\n"
        select_options.append(
            SelectOption(
                label=f"{nickname}{account[0]} | {text_map.get(get_uid_region(account[0]), i.locale, user_locale)}",
                emoji=emoji,
                value=account[0],
            )
        )
    if not current_account:
        await c.execute(
            "UPDATE user_accounts SET current = 1 WHERE user_id = ? AND uid = ?",
            (i.user.id, accounts[0][0]),
        )
        await i.client.db.commit()
        return await return_accounts(i)
    embed = default_embed(message=account_str).set_author(
        name=text_map.get(555, i.locale, user_locale),
        icon_url=i.user.display_avatar.url,
    )
    view = View(user_locale or i.locale, select_options)
    try:
        await i.response.edit_message(embed=embed, view=view)
        view.message = await i.original_response()
    except InteractionResponded:
        view.message = await i.edit_original_response(embed=embed, view=view)
    view.author = i.user
