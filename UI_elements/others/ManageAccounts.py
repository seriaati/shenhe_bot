import asyncio
from typing import List

import aiosqlite
from apps.genshin.utils import get_uid_region
import config
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from debug import DefaultView
from discord import ButtonStyle, Interaction, Locale, SelectOption
from discord.errors import InteractionResponded
from discord.ui import Button, Select
from utility.utils import default_embed, error_embed


class View(DefaultView):
    def __init__(self, locale: Locale | str, select_options: List[SelectOption]):
        super().__init__(timeout=config.long_timeout)
        self.locale = locale
        self.select_options = select_options
        self.add_item(AddAccount(locale))
        self.add_item(RemoveAccount(locale, True if not select_options else False))
        self.add_item(RemoveAllAccounts(locale, True if not select_options else False))
        self.add_item(SwitchAccount(locale, select_options))


class AddAccount(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(
            emoji="<:person_add:1018764808251768832>",
            label=text_map.get(556, locale),
            style=ButtonStyle.blurple,
        )

    async def callback(self, i: Interaction):
        self.view: View
        locale = self.view.locale
        self.view.clear_items()
        self.view.add_item(GOBack())
        self.view.add_item(AddUID(locale))
        self.view.add_item(AddCookie(locale))
        embed = default_embed(message=text_map.get(563, locale)).set_author(
            name=text_map.get(562, locale), icon_url=i.user.display_avatar.url
        )
        await i.response.edit_message(embed=embed, view=self.view)


class AddUID(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(
            emoji="<:uid_add:1018777895663063040>",
            label=text_map.get(564, locale),
            style=ButtonStyle.blurple,
        )

    async def callback(self, i: Interaction):
        pass


class AddCookie(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(
            emoji="<:cookie_add:1018776813922693120>",
            label=text_map.get(565, locale),
            style=ButtonStyle.blurple,
        )

    async def callback(self, i: Interaction):
        pass


class RemoveAccount(Button):
    def __init__(self, locale: Locale | str, disabled: bool):
        super().__init__(
            emoji="<:person_remove:1018765604842377256>",
            label=text_map.get(557, locale),
            disabled=disabled,
        )

    async def callback(self, i: Interaction):
        self.view: View
        locale = self.view.locale
        self.view.clear_items()
        account_select = SwitchAccount(locale, self.view.select_options)
        account_select.placeholder = text_map.get(136, locale)
        account_select.remove_account = True
        self.view.add_item(account_select)
        self.view.add_item(GOBack())
        embed = default_embed().set_author(
            name=text_map.get(560, locale), icon_url=i.user.display_avatar.url
        )
        await i.response.edit_message(embed=embed, view=self.view)


class RemoveAllAccounts(Button):
    def __init__(self, locale: Locale | str, disabled: bool):
        super().__init__(label=text_map.get(558, locale), style=ButtonStyle.red, disabled=disabled)

    async def callback(self, i: Interaction):
        pass


class SwitchAccount(Select):
    def __init__(self, locale: Locale | str, select_options: List[SelectOption]):
        disabled = False
        if not select_options:
            select_options = [SelectOption(label="None", value="None")]
            disabled = True
        super().__init__(
            placeholder=text_map.get(559, locale),
            options=select_options,
            row=3,
            disabled=disabled,
        )

    async def callback(self, i: Interaction):
        c: aiosqlite.Cursor = await i.client.db.cursor()
        if hasattr(self, "remove_account"):
            await c.execute(
                "DELETE FROM user_accounts WHERE uid = ?", (self.values[0],)
            )
        else:
            await c.execute(
                "UPDATE user_accounts SET active = 0 WHERE user_id = ?", (i.user.id,)
            )
            await c.execute(
                "UPDATE user_accounts SET active = 1 WHERE uid = ?", (self.values[0],)
            )
        await i.client.db.commit()
        embed = default_embed().set_author(
            name=text_map.get(561, self.view.locale), icon_url=i.user.display_avatar.url
        )
        await i.response.edit_message(embed=embed, view=None)
        await asyncio.sleep(1)
        await return_accounts(i)


class GOBack(Button):
    def __init__(self):
        super().__init__(emoji="<:left:982588994778972171>")

    async def callback(self, i: Interaction):
        await return_accounts(i)


async def return_accounts(i: Interaction):
    user_locale = await get_user_locale(i.user.id, i.client.db)
    c: aiosqlite.Cursor = await i.client.db.cursor()
    await c.execute("SELECT uid FROM user_accounts WHERE user_id = ?", (i.user.id,))
    accounts = await c.fetchall()
    select_options = []
    view = View(user_locale or i.locale, select_options)
    if not accounts:
        embed = default_embed().set_author(
            name=text_map.get(545, i.locale, user_locale),
            icon_url=i.user.display_avatar.url,
        )
        try:
            await i.response.send_message(
                embed=embed,
                view=view,
                ephemeral=True,
            )
        except InteractionResponded:
            await i.edit_original_response(embed=embed, view=view)
        return
    account_str = ""
    for account in accounts:
        account_str += f"• {account[0]} | {text_map.get(get_uid_region(account[0]), i.locale, user_locale)}\n"
        select_options.append(
            SelectOption(
                label=f"{account[0]} | {text_map.get(get_uid_region(account[0]), i.locale, user_locale)}",
                value=account[0],
            )
        )
    embed = default_embed(message=account_str).set_author(
        name=text_map.get(555, i.locale, user_locale),
        icon_url=i.user.display_avatar.url,
    )
    view = View(user_locale or i.locale, select_options)
    try:
        await i.response.send_message(embed=embed, view=view, ephemeral=True)
    except InteractionResponded:
        await i.edit_original_response(embed=embed, view=view)
    view.message = await i.original_response()
    view.author = i.user
