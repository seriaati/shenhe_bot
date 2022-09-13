import asyncio
from typing import List

import aiosqlite
from apps.genshin.utils import get_uid_region
import config
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from debug import DefaultModal, DefaultView
from discord import ButtonStyle, Interaction, Locale, SelectOption, TextStyle
from discord.errors import InteractionResponded
from discord.ui import Button, Select, TextInput
from utility.utils import default_embed, error_embed
from enkanetwork import EnkaNetworkAPI, UIDNotFounded
from apps.genshin.genshin_app import GenshinApp


class View(DefaultView):
    def __init__(self, locale: Locale | str, select_options: List[SelectOption]):
        super().__init__(timeout=config.long_timeout)
        self.locale = locale
        self.select_options = select_options
        self.add_item(AddAccount(locale))
        self.add_item(RemoveAccount(locale, True if not select_options else False))
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
    view.clear_items()
    view.add_item(GOBack())
    view.add_item(AddUID(locale))
    view.add_item(AddCookie(locale))
    embed = default_embed(message=text_map.get(563, locale)).set_author(
        name=text_map.get(562, locale), icon_url=i.user.display_avatar.url
    )
    await i.response.edit_message(embed=embed, view=view)


class AddUID(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(
            emoji="<:uid_add:1018777895663063040>",
            label=text_map.get(564, locale),
            style=ButtonStyle.blurple,
        )

    async def callback(self, i: Interaction):
        await i.response.send_modal(AddUIDModal(self.view.locale))


class AddUIDModal(DefaultModal):
    uid = TextInput(label="UID", placeholder="Put your UID here")

    def __init__(self, locale: Locale | str) -> None:
        super().__init__(title=text_map.get(564, locale), timeout=config.mid_timeout)
        self.locale = locale
        self.uid.placeholder = text_map.get(566, locale)

    async def on_submit(self, i: Interaction) -> None:
        view = View(self.locale, [])
        view.clear_items()
        view.add_item(GOBack())
        view.add_item(AddUID(self.locale))
        view.add_item(AddCookie(self.locale))
        for item in view.children:
            item.disabled = True
        await i.response.edit_message(
            embed=default_embed(message=text_map.get(578, self.locale)).set_author(
                name=text_map.get(576, self.locale), icon_url=i.user.display_avatar.url
            ),
            view=view,
        )

        try:
            if not self.uid.value.isdigit():
                raise ValueError
            if int(self.uid.value[0]) not in [0, 1, 2, 5, 6, 7, 8, 9]:
                raise ValueError
            if len(self.uid.value) != 9:
                raise ValueError
            async with EnkaNetworkAPI() as enka:
                try:
                    await enka.fetch_user(self.uid.value)
                except UIDNotFounded:
                    raise ValueError
        except ValueError:
            return await i.edit_original_response(
                embed=error_embed()
                .set_author(
                    name=f"{text_map.get(286, self.locale)}: {self.uid.value}",
                    icon_url=i.user.display_avatar.url,
                )
                .set_footer(text=text_map.get(567, self.locale)),
            )

        c: aiosqlite.Cursor = await i.client.db.cursor()
        await c.execute(
            "INSERT INTO user_accounts (uid, user_id) VALUES (?, ?) ON CONFLICT (uid, user_id) DO NOTHING",
            (self.uid.value, i.user.id),
        )
        await i.client.db.commit()

        await i.edit_original_response(
            embed=default_embed(message=self.uid.value).set_author(
                name=text_map.get(568, self.locale),
                icon_url=i.user.display_avatar.url,
            )
        )
        await asyncio.sleep(2)
        await return_accounts(i)


class AddCookie(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(
            emoji="<:cookie_add:1018776813922693120>",
            label=text_map.get(565, locale),
            style=ButtonStyle.blurple,
        )

    async def callback(self, i: Interaction):
        await add_cookie_callback(self.view, i)


async def add_cookie_callback(view: View, i: Interaction):
    locale = view.locale
    embed = default_embed(
        text_map.get(137, locale),
        text_map.get(138, locale),
    )
    embed.set_image(url="https://i.imgur.com/OQ8arx0.gif")
    code_msg = f"```script:d=document.cookie; c=d.includes('account_id') || alert('{text_map.get(139, locale)}'); c && document.write(d)```"
    code_embed = default_embed(message=code_msg)
    view.clear_items()
    view.add_item(GOBack(2))
    view.add_item(SubmitCookie(locale))
    await i.response.edit_message(embeds=[embed, code_embed], view=view)


class SubmitCookie(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(
            emoji="<:submit_cookie:1019068169882718258>",
            label=text_map.get(413, locale),
            style=ButtonStyle.blurple,
        )

    async def callback(self, i: Interaction):
        await i.response.send_modal(SubmitCookieModal(self.view.locale))


class SubmitCookieModal(DefaultModal):
    cookie = TextInput(label="Cookie", style=TextStyle.long)

    def __init__(self, locale: Locale | str) -> None:
        super().__init__(
            title="CookieModal", timeout=config.mid_timeout, custom_id="cookie_modal"
        )
        self.locale = locale
        self.title = text_map.get(132, locale)
        self.cookie.placeholder = text_map.get(133, locale)

    async def on_submit(self, i: Interaction) -> None:
        view = View(self.locale, [])
        view.clear_items()
        view.add_item(GOBack())
        view.add_item(AddUID(self.locale))
        view.add_item(AddCookie(self.locale))
        for item in view.children:
            item.disabled = True
        await i.response.edit_message(
            embed=default_embed(message=text_map.get(578, self.locale)).set_author(
                name=text_map.get(577, self.locale), icon_url=i.user.display_avatar.url
            ),
            view=view,
        )
        genshin_app = GenshinApp(i.client.db, i.client)
        result, success = await genshin_app.set_cookie(
            i.user.id, self.cookie.value, i.locale
        )

        if not success:
            result.set_footer(text=text_map.get(567, self.locale))
            return await i.edit_original_response(embed=result)
        if isinstance(result, list):  # 有多個帳號
            view = View(self.locale, [])
            view.clear_items()
            view.add_item(UIDSelect(self.locale, result, self.cookie.value))
            view.add_item(GOBack(3))
            embed = default_embed().set_author(
                name=text_map.get(570, self.locale), icon_url=i.user.display_avatar.url
            )
            await i.edit_original_response(embed=embed, view=view)
            view.message = await i.original_response()
        else:  # 一個帳號而已
            await i.edit_original_response(embed=result)
            await asyncio.sleep(2)
            await return_accounts(i)


class UIDSelect(Select):
    def __init__(
        self, locale: Locale | str, select_options: list[SelectOption], cookie: str
    ) -> None:
        super().__init__(
            placeholder=text_map.get(136, locale),
            options=select_options,
        )
        self.cookie = cookie

    async def callback(self, i: Interaction):
        await i.response.defer()
        genshin_app = GenshinApp(i.client.db, i.client)
        result = (
            await genshin_app.set_cookie(
                i.user.id, self.cookie, i.locale, int(self.values[0])
            )
        )[0]
        for item in self.view.children:
            item.disabled = True
        await i.edit_original_response(embed=result, view=self.view)
        await asyncio.sleep(2)
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
    ):
        disabled = False
        self.remove_account = remove_account
        if not select_options:
            select_options = [SelectOption(label="None", value="None")]
            disabled = True
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
        else:
            await c.execute(
                "UPDATE user_accounts SET current = 0 WHERE user_id = ?", (i.user.id,)
            )
            await c.execute(
                "UPDATE user_accounts SET current = 1 WHERE uid = ? AND user_id = ?",
                (self.values[0], i.user.id),
            )
            for item in self.view.children:
                item.disabled = True
            await i.response.edit_message(
                embed=default_embed().set_author(
                    name=f"{text_map.get(569, self.view.locale)}: {self.values[0]}",
                    icon_url=i.user.display_avatar.url,
                ),
                view=self.view,
            )
        await asyncio.sleep(2)
        await return_accounts(i)
        await i.client.db.commit()


class GOBack(Button):
    def __init__(self, layer: int = 1):
        super().__init__(emoji="<:left:982588994778972171>")
        self.layer = layer

    async def callback(self, i: Interaction):
        if self.layer == 2:
            await add_account_callback(self.view, i)
        elif self.layer == 3:
            await add_cookie_callback(self.view, i)
        else:
            await return_accounts(i)


async def return_accounts(i: Interaction):
    user_locale = await get_user_locale(i.user.id, i.client.db)
    c: aiosqlite.Cursor = await i.client.db.cursor()
    await c.execute(
        "SELECT uid, ltuid, current FROM user_accounts WHERE user_id = ?", (i.user.id,)
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
            await i.response.send_message(
                embed=embed,
                view=view,
                ephemeral=True,
            )
        except InteractionResponded:
            await i.edit_original_response(embed=embed, view=view)
        return
    account_str = ""
    current_account = False
    for account in accounts:
        emoji = (
            "<:cookie_add:1018776813922693120>"
            if account[1] is not None
            else "<:number:1018838745614667817>"
        )
        if account[2] == 1:
            current_account = True
            account_str += f"**• {account[0]} | {text_map.get(get_uid_region(account[0]), i.locale, user_locale)} | {emoji}**\n"
        else:
            account_str += f"• {account[0]} | {text_map.get(get_uid_region(account[0]), i.locale, user_locale)} | {emoji}\n"
        select_options.append(
            SelectOption(
                label=f"{account[0]} | {text_map.get(get_uid_region(account[0]), i.locale, user_locale)}",
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
        await i.response.send_message(embed=embed, view=view, ephemeral=True)
    except InteractionResponded:
        await i.edit_original_response(embed=embed, view=view)
    view.message = await i.original_response()
    view.author = i.user
