import ast
import asyncio
from typing import Optional

import asqlite
from discord import (ButtonStyle, Embed, Forbidden, Interaction,
                     InteractionResponded, Locale, NotFound)
from discord.ui import Button, TextInput

import asset
import config
from ambr.client import AmbrTopAPI
from apps.genshin.checks import check_cookie_predicate
from apps.genshin.utils import get_character_emoji, get_uid, get_weapon_emoji
from apps.text_map.convert_locale import to_ambr_top
from apps.text_map.text_map_app import text_map
from exceptions import DBError
from UI_base_models import BaseModal, BaseView
from UI_elements.genshin import TalentNotificationMenu, WeaponNotificationMenu
from utility.utils import default_embed, divide_chunks, error_embed, log


class View(BaseView):
    def __init__(self, locale: Locale | str):
        super().__init__(timeout=config.mid_timeout)
        self.locale = locale
        self.add_item(ResinNotification(locale))
        self.add_item(PotNotification(locale))
        self.add_item(PTNotification(text_map.get(704, locale)))
        self.add_item(TalentNotification(locale))
        self.add_item(WeaponNotification(locale))
        self.add_item(PrivacySettings(locale))


class ResinNotification(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(emoji="🌙", label=text_map.get(582, locale))

    async def callback(self, i: Interaction):
        self.view: View
        await check_cookie_predicate(i)
        await return_resin_notification(i, self.view)


class PotNotification(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(emoji="🫖", label=text_map.get(584, locale))

    async def callback(self, i: Interaction):
        self.view: View
        await check_cookie_predicate(i)
        await return_pot_notification(i, self.view)


class TalentNotification(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(emoji="📘", label=text_map.get(442, locale), row=2)

    async def callback(self, i: Interaction):
        self.view: View
        await return_talent_notification(i, self.view)


class WeaponNotification(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(emoji="🗡️", label=text_map.get(632, locale), row=2)

    async def callback(self, i: Interaction):
        self.view: View
        await return_weapon_notification(i, self.view)


class AddWeapon(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(emoji="✏️", label=text_map.get(634, locale))
        self.locale = locale

    async def callback(self, i: Interaction):
        ambr = AmbrTopAPI(i.client.session, to_ambr_top(self.locale))
        view = WeaponNotificationMenu.View(self.locale, await ambr.get_weapon_types())
        await i.response.edit_message(view=view)
        view.author = i.user
        view.message = await i.original_response()


class RemoveAllWeapon(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(emoji="🗑️", label=text_map.get(635, locale))

    async def callback(self, i: Interaction):
        self.view: View
        async with i.client.pool.acquire() as db:
            await db.execute(
                "UPDATE weapon_notification SET weapon_list = '[]' WHERE user_id = ?",
                (i.user.id,),
            )
            await db.commit()
        await return_weapon_notification(i, self.view)


class AddCharacter(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(emoji="✏️", label=text_map.get(598, locale))
        self.locale = locale

    async def callback(self, i: Interaction):
        view = TalentNotificationMenu.View(self.locale)
        await i.response.edit_message(view=view)
        view.author = i.user
        view.message = await i.original_response()


class RemoveAllCharacter(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(emoji="🗑️", label=text_map.get(599, locale))

    async def callback(self, i: Interaction):
        self.view: View
        async with i.client.pool.acquire() as db:
            await db.execute(
                "UPDATE talent_notification SET character_list = '[]' WHERE user_id = ?",
                (i.user.id,),
            )
            await db.commit()
        await return_talent_notification(i, self.view)


class PrivacySettings(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(emoji="✉️", label=text_map.get(585, locale), row=2)
        self.locale = locale

    async def callback(self, i: Interaction):
        self.view: View
        embed = default_embed(
            message=f"{text_map.get(595, self.locale)}\n"
            f"1. {text_map.get(308, self.locale)}\n"
            f"2. {text_map.get(309, self.locale)}\n"
            f"3. {text_map.get(310, self.locale)}"
        )
        embed.set_author(
            name=text_map.get(311, self.locale),
            icon_url=i.user.display_avatar.url,
        )
        embed.set_image(url="https://i.imgur.com/sYg4SpD.gif")
        self.view.clear_items()
        self.view.add_item(GOBack())
        self.view.add_item(TestItOut(self.locale, embed))
        await i.response.edit_message(embed=embed, view=self.view)


class TestItOut(Button):
    def __init__(self, locale: Locale | str, embed: Embed):
        super().__init__(emoji="📨", label=text_map.get(596, locale))
        self.locale = locale
        self.embed = embed

    async def callback(self, i: Interaction):
        await i.response.defer()
        try:
            await i.user.send("Hello There!\n哈囉!")
        except Forbidden:
            embed = self.embed
            embed.author.name = text_map.get(597, self.locale)
            embed.color = 0xFC5165
            await i.edit_original_response(embed=embed)


class PTNotification(Button):
    def __init__(self, label: str):
        super().__init__(emoji=asset.pt_emoji, label=label)

    async def callback(self, i: Interaction):
        self.view: View
        await check_cookie_predicate(i)
        await return_pt_notification(i, self.view)


class NotificationON(Button):
    def __init__(self, locale: Locale | str, table_name: str, current: bool):
        super().__init__(
            emoji="🔔",
            label=text_map.get(99, locale),
            style=ButtonStyle.blurple if current else ButtonStyle.gray,
        )
        self.table_name = table_name

    async def callback(self, i: Interaction):
        self.view: View
        await on_off_function(self.view, self.table_name, i, 1)


class NotificationOFF(Button):
    def __init__(self, locale: Locale | str, table_name: str, current: bool):
        super().__init__(
            emoji="🔕",
            label=text_map.get(100, locale),
            style=ButtonStyle.blurple if current else ButtonStyle.gray,
        )
        self.table_name = table_name

    async def callback(self, i: Interaction):
        self.view: View
        await on_off_function(self.view, self.table_name, i, 0)


async def on_off_function(view: View, table_name: str, i: Interaction, toggle: int):
    async with i.client.pool.acquire() as db:
        if table_name in ["talent_notification", "weapon_notification"]:
            await db.execute(
                f"UPDATE {table_name} SET toggle = {toggle} WHERE user_id = ?",
                (i.user.id,),
            )
        else:
            await db.execute(
                f"UPDATE {table_name} SET toggle = {toggle} WHERE user_id = ? AND uid = ?",
                (i.user.id, await get_uid(i.user.id, i.client.pool)),
            )

        await db.commit()

    if table_name == "resin_notification":
        await return_resin_notification(i, view)
    elif table_name == "pot_notification":
        await return_pot_notification(i, view)
    elif table_name == "talent_notification":
        await return_talent_notification(i, view)
    elif table_name == "weapon_notification":
        await return_weapon_notification(i, view)
    elif table_name == "pt_notification":
        await return_pt_notification(i, view)


class ChangeSettings(Button):
    def __init__(self, locale: Locale | str, table_name: str):
        super().__init__(emoji=asset.settings_emoji, label=text_map.get(594, locale))
        self.locale = locale
        self.table_name = table_name

    async def callback(self, i: Interaction):
        self.view: View
        uid = await get_uid(i.user.id, i.client.pool)
        async with i.client.pool.acquire() as db:
            try:
                if self.table_name == "resin_notification":
                    modal = ResinModal(self.locale)
                    await i.response.send_modal(modal)
                    await modal.wait()
                    threshold = modal.resin_threshold.value
                    max_notif = modal.max_notif.value
                    if not threshold or not max_notif:
                        pass
                    else:
                        if not threshold.isdigit() or not max_notif.isdigit():
                            raise ValueError
                        await db.execute(
                            "UPDATE resin_notification SET threshold = ?, max = ? WHERE user_id = ? AND uid = ?",
                            (threshold, max_notif, i.user.id, uid),
                        )
                    await return_resin_notification(i, self.view)
                elif self.table_name == "pot_notification":
                    modal = PotModal(self.locale)
                    await i.response.send_modal(modal)
                    await modal.wait()
                    threshold = modal.threshold.value
                    max_notif = modal.max_notif.value
                    if not threshold or not max_notif:
                        pass
                    else:
                        if not threshold.isdigit() or not max_notif.isdigit():
                            raise ValueError
                        await db.execute(
                            "UPDATE pot_notification SET threshold = ?, max = ? WHERE user_id = ? AND uid = ?",
                            (threshold, max_notif, i.user.id, uid),
                        )
                    await return_pot_notification(i, self.view)
                elif self.table_name == "pt_notification":
                    modal = PTModal(self.locale)
                    await i.response.send_modal(modal)
                    await modal.wait()
                    max_notif = modal.max_notif.value
                    if not max_notif:
                        pass
                    else:
                        if not max_notif.isdigit():
                            raise ValueError
                        await db.execute(
                            "UPDATE pt_notification SET max = ? WHERE user_id = ? AND uid = ?",
                            (max_notif, i.user.id, uid),
                        )
                    await return_pt_notification(i, self.view)
            except ValueError:
                children = [
                    item for item in self.view.children if isinstance(item, Button)
                ]
                for child in children:
                    child.disabled = True
                await i.edit_original_response(
                    embed=error_embed().set_author(
                        name=text_map.get(187, self.locale),
                        icon_url=i.user.display_avatar.url,
                    ),
                    view=self.view,
                )
                await asyncio.sleep(2)
                await return_notification_menu(i, self.locale)
            await db.commit()


class GOBack(Button):
    def __init__(self):
        super().__init__(emoji="<:left:982588994778972171>", row=2)

    async def callback(self, i: Interaction):
        self.view: View
        await return_notification_menu(i, self.view.locale)


class ResinModal(BaseModal):
    resin_threshold = TextInput(
        label="樹脂閥值", placeholder="例如: 140 (不得大於 160)", max_length=3
    )
    max_notif = TextInput(label="最大提醒值", placeholder="例如: 5", max_length=3)

    def __init__(self, locale: Locale | str):
        super().__init__(title=text_map.get(515, locale))
        self.resin_threshold.label = text_map.get(152, locale)
        self.resin_threshold.placeholder = text_map.get(170, locale).format(a=140)
        self.max_notif.label = text_map.get(103, locale)
        self.max_notif.placeholder = text_map.get(155, locale)

    async def on_submit(self, interaction: Interaction) -> None:
        await interaction.response.defer()
        self.stop()


class PotModal(BaseModal):
    threshold = TextInput(label="寶錢閥值", max_length=5)
    max_notif = TextInput(label="最大提醒值", max_length=3)

    def __init__(self, locale: Locale | str):
        super().__init__(title=text_map.get(515, locale))
        self.threshold.label = text_map.get(516, locale)
        self.threshold.placeholder = text_map.get(170, locale).format(a=2000)
        self.max_notif.label = text_map.get(103, locale)
        self.max_notif.placeholder = text_map.get(155, locale)

    async def on_submit(self, interaction: Interaction) -> None:
        await interaction.response.defer()
        self.stop()


class PTModal(BaseModal):
    max_notif = TextInput(label="最大提醒值", max_length=3)

    def __init__(self, locale: Locale | str):
        super().__init__(title=text_map.get(515, locale))
        self.max_notif.label = text_map.get(103, locale)
        self.max_notif.placeholder = text_map.get(155, locale)

    async def on_submit(self, interaction: Interaction) -> None:
        await interaction.response.defer()
        self.stop()


# Functions
async def return_resin_notification(i: Interaction, view: View):
    uid = await get_uid(i.user.id, i.client.pool)

    async with i.client.pool.acquire() as db:
        async with db.execute(
            "INSERT INTO resin_notification (user_id, uid) VALUES (?, ?) ON CONFLICT DO NOTHING",
            (i.user.id, uid),
        ) as c:
            await c.execute(
                "SELECT toggle, threshold, max FROM resin_notification WHERE user_id = ? AND uid = ?",
                (i.user.id, uid),
            )
            rows = await c.fetchone()
            if rows is not None:
                toggle, threshold, max = rows
            else:
                raise ValueError("No rows found")

        await db.commit()
    value = f"{text_map.get(101, view.locale)}: {text_map.get(99 if toggle == 1 else 100, view.locale)}\n"
    value += f"{text_map.get(302, view.locale)}: {threshold}\n"
    value += f"{text_map.get(103, view.locale)}: {max}"
    embed = default_embed(message=text_map.get(586, view.locale))
    embed.add_field(name=text_map.get(591, view.locale), value=value)
    embed.set_author(
        name=text_map.get(582, view.locale), icon_url=i.user.display_avatar.url
    )
    view.clear_items()
    view.add_item(GOBack())
    view.add_item(ChangeSettings(view.locale, "resin_notification"))
    view.add_item(
        NotificationON(
            view.locale, "resin_notification", True if toggle == 1 else False
        )
    )
    view.add_item(
        NotificationOFF(
            view.locale, "resin_notification", True if toggle == 0 else False
        )
    )
    try:
        await i.response.edit_message(embed=embed, view=view)
    except InteractionResponded:
        await i.edit_original_response(embed=embed, view=view)


async def return_pt_notification(i: Interaction, view: View):
    uid = await get_uid(i.user.id, i.client.pool)
    toggle, max_notif = await get_notification_status(
        i.user.id, uid, "pt_notification", "toggle, max", i
    )
    value = f"""
        {text_map.get(101, view.locale)}: {text_map.get(99 if toggle == 1 else 100, view.locale)}
        {text_map.get(103, view.locale)}: {max_notif}
    """
    embed = default_embed(message=text_map.get(512, view.locale))
    embed.add_field(name=text_map.get(591, view.locale), value=value)
    embed.set_author(
        name=text_map.get(704, view.locale), icon_url=i.user.display_avatar.url
    )
    view.clear_items()
    view.add_item(ChangeSettings(view.locale, "pt_notification"))
    view.add_item(GOBack())
    view.add_item(
        NotificationON(view.locale, "pt_notification", True if toggle == 1 else False)
    )
    view.add_item(
        NotificationOFF(view.locale, "pt_notification", True if toggle == 0 else False)
    )
    try:
        await i.response.edit_message(embed=embed, view=view)
    except InteractionResponded:
        await i.edit_original_response(embed=embed, view=view)


async def return_pot_notification(i: Interaction, view: View):
    uid = await get_uid(i.user.id, i.client.pool)
    toggle, threshold, max = await get_notification_status(
        i.user.id, uid, "pot_notification", "toggle, threshold, max", i
    )

    value = f"{text_map.get(101, view.locale)}: {text_map.get(99 if toggle == 1 else 100, view.locale)}\n"
    value += f"{text_map.get(302, view.locale)}: {threshold}\n"
    value += f"{text_map.get(103, view.locale)}: {max}"
    embed = default_embed(message=text_map.get(639, view.locale))
    embed.set_author(
        name=text_map.get(584, view.locale), icon_url=i.user.display_avatar.url
    )
    embed.add_field(name=text_map.get(591, view.locale), value=value)
    view.clear_items()
    view.add_item(GOBack())
    view.add_item(ChangeSettings(view.locale, "pot_notification"))
    view.add_item(
        NotificationON(view.locale, "pot_notification", True if toggle == 1 else False)
    )
    view.add_item(
        NotificationOFF(view.locale, "pot_notification", True if toggle == 0 else False)
    )
    try:
        await i.response.edit_message(embed=embed, view=view)
    except InteractionResponded:
        await i.edit_original_response(embed=embed, view=view)


async def return_talent_notification(i: Interaction, view: View):
    toggle, character_list = await get_notification_status(
        i.user.id, None, "talent_notification", "toggle, character_list", i
    )
    character_list = ast.literal_eval(character_list)

    embed = default_embed(message=text_map.get(590, view.locale))
    embed.set_author(
        name=text_map.get(442, view.locale), icon_url=i.user.display_avatar.url
    )
    if not character_list:
        value = text_map.get(158, view.locale)
        embed.add_field(name=text_map.get(159, view.locale), value=value)
    else:
        values = []
        for character in character_list:
            values.append(
                f"{get_character_emoji(character)} {text_map.get_character_name(character, view.locale)}\n"
            )
        values = list(divide_chunks(values, 20))
        for index, value in enumerate(values):
            embed.add_field(
                name=text_map.get(159, view.locale) + f" (#{index+1})",
                value="".join(value),
            )
    view.clear_items()
    view.add_item(GOBack())
    view.add_item(AddCharacter(view.locale))
    view.add_item(RemoveAllCharacter(view.locale))
    view.add_item(
        NotificationON(
            view.locale, "talent_notification", True if toggle == 1 else False
        )
    )
    view.add_item(
        NotificationOFF(
            view.locale, "talent_notification", True if toggle == 0 else False
        )
    )
    try:
        await i.response.edit_message(embed=embed, view=view)
    except InteractionResponded:
        await i.edit_original_response(embed=embed, view=view)


async def return_weapon_notification(i: Interaction, view: View):
    toggle, weapon_list = await get_notification_status(
        i.user.id, None, "weapon_notification", "toggle, weapon_list", i
    )
    weapon_list = ast.literal_eval(weapon_list)

    embed = default_embed(message=text_map.get(633, view.locale))
    embed.set_author(
        name=text_map.get(632, view.locale), icon_url=i.user.display_avatar.url
    )
    if not weapon_list:
        value = text_map.get(637, view.locale)
        embed.add_field(name=text_map.get(636, view.locale), value=value)
    else:
        values = []
        for weapon in weapon_list:
            values.append(
                f"{get_weapon_emoji(int(weapon))} {text_map.get_weapon_name(weapon, view.locale)}\n"
            )
        values = list(divide_chunks(values, 20))
        for index, value in enumerate(values):
            embed.add_field(
                name=text_map.get(636, view.locale) + f" (#{index+1})",
                value="".join(value),
            )
    view.clear_items()
    view.add_item(GOBack())
    view.add_item(AddWeapon(view.locale))
    view.add_item(RemoveAllWeapon(view.locale))
    view.add_item(
        NotificationON(
            view.locale, "weapon_notification", True if toggle == 1 else False
        )
    )
    view.add_item(
        NotificationOFF(
            view.locale, "weapon_notification", True if toggle == 0 else False
        )
    )
    try:
        await i.response.edit_message(embed=embed, view=view)
    except InteractionResponded:
        await i.edit_original_response(embed=embed, view=view)


async def return_notification_menu(
    i: Interaction, locale: Locale | str, send: bool = False
):
    embed = default_embed(message=text_map.get(592, locale))
    embed.set_author(name=text_map.get(593, locale), icon_url=i.user.display_avatar.url)

    view = View(locale)
    if send:
        await i.response.send_message(embed=embed, view=view)
    else:
        try:
            await i.response.edit_message(embed=embed, view=view)
        except InteractionResponded:
            await i.edit_original_response(embed=embed, view=view)
    view.author = i.user
    try:
        view.message = await i.original_response()
    except NotFound:
        pass


async def get_notification_status(
    user_id: int, uid: Optional[int], table_name: str, items: str, i: Interaction
):
    _data = (user_id, uid) if uid else (user_id,)
    insert_query = "(user_id, uid)" if uid else "(user_id)"
    select_query = "user_id = ? AND uid = ?" if uid else "user_id = ?"
    values_query = "(?, ?)" if uid else "(?)"

    async with i.client.pool.acquire() as db:
        async with db.execute(
            f"INSERT INTO {table_name} {insert_query} VALUES {values_query} ON CONFLICT DO NOTHING",
            _data,
        ) as c:
            await c.execute(
                f"SELECT {items} FROM {table_name} WHERE {select_query}",
                _data,
            )
            rows = await c.fetchone()
            if rows is None:
                log.warning(f"User {user_id} with uid {uid} not found in {table_name}")
                raise DBError(
                    f"User {user_id} with uid {uid} not found in {table_name}"
                )
        await db.commit()

    return rows
