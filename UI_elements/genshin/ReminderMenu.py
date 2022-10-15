import ast
import asyncio
from apps.genshin.checks import check_cookie_predicate
from apps.genshin.utils import get_character, get_uid, get_weapon
from UI_base_models import BaseModal, BaseView
import config
from discord import Locale, Interaction, ButtonStyle, Embed
from discord.ui import Button, TextInput
from discord.errors import InteractionResponded, Forbidden, NotFound
from apps.text_map.text_map_app import text_map
from utility.utils import default_embed, error_embed
import aiosqlite
from UI_elements.genshin import TalentNotificationMenu, WeaponNotificationMenu


class View(BaseView):
    def __init__(self, locale: Locale | str):
        super().__init__(timeout=config.mid_timeout)
        self.locale = locale
        self.add_item(ResinNotification(locale))
        self.add_item(PotNotification(locale))
        self.add_item(TalentNotification(locale))
        self.add_item(WeaponNotification(locale))
        self.add_item(PrivacySettings(locale))


class ResinNotification(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(emoji="🌙", label=text_map.get(582, locale))

    async def callback(self, i: Interaction):
        check = await check_cookie_predicate(i, i.user)
        if not check:
            return
        await return_resin_notification(i, self.view)


async def return_resin_notification(i: Interaction, view: View):
    c: aiosqlite.Cursor = await i.client.db.cursor()
    await c.execute(
        "SELECT toggle, threshold, max FROM resin_notification WHERE user_id = ? AND uid = ?",
        (i.user.id, await get_uid(i.user.id, i.client.db)),
    )
    (toggle, threshold, max) = await c.fetchone()
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


class PotNotification(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(emoji="🫖", label=text_map.get(584, locale))

    async def callback(self, i: Interaction):
        check = await check_cookie_predicate(i, i.user)
        if not check:
            return
        await return_pot_notification(i, self.view)


async def return_pot_notification(i: Interaction, view: View):
    c: aiosqlite.Cursor = await i.client.db.cursor()
    await c.execute(
        "SELECT toggle, threshold, max FROM pot_notification WHERE user_id = ? AND uid = ?",
        (i.user.id, await get_uid(i.user.id, i.client.db)),
    )
    (toggle, threshold, max) = await c.fetchone()
    value = f"{text_map.get(101, view.locale)}: {text_map.get(99 if toggle == 1 else 100, view.locale)}\n"
    value += f"{text_map.get(302, view.locale)}: {threshold}\n"
    value += f"{text_map.get(103, view.locale)}: {max}"
    embed = default_embed(message=text_map.get(586, view.locale))
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


class TalentNotification(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(emoji="📘", label=text_map.get(442, locale), row=2)

    async def callback(self, i: Interaction):
        await return_talent_notification(i, self.view)


class WeaponNotification(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(emoji="🗡️", label=text_map.get(632, locale), row=2)

    async def callback(self, i: Interaction):
        await return_weapon_notification(i, self.view)


class AddWeapon(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(emoji="✏️", label=text_map.get(634, locale))
        self.locale = locale

    async def callback(self, i: Interaction):
        view = WeaponNotificationMenu.View(self.locale)
        await i.response.edit_message(view=view)
        view.author = i.user
        view.message = await i.original_response()


class RemoveAllWeapon(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(emoji="🗑️", label=text_map.get(635, locale))

    async def callback(self, i: Interaction):
        await i.client.db.execute(
            "UPDATE weapon_notification SET weapon_list = '[]' WHERE user_id = ?",
            (i.user.id,),
        )
        await i.client.db.commit()
        await return_weapon_notification(i, self.view)


async def return_weapon_notification(i: Interaction, view: View):
    async with i.client.db.execute(
        "SELECT toggle, weapon_list FROM weapon_notification WHERE user_id = ?",
        (i.user.id,),
    ) as c:
        toggle, weapon_list = await c.fetchone()
    weapon_list = ast.literal_eval(weapon_list)
    if not weapon_list:
        value = text_map.get(637, view.locale)
    else:
        value = ""
        for weapon in weapon_list:
            value += f'{get_weapon(weapon)["emoji"]} {text_map.get_weapon_name(weapon, view.locale)}\n'
    embed = default_embed(message=text_map.get(633, view.locale))
    embed.set_author(
        name=text_map.get(632, view.locale), icon_url=i.user.display_avatar.url
    )
    embed.add_field(name=text_map.get(636, view.locale), value=value)
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


async def return_talent_notification(i: Interaction, view: View):
    c: aiosqlite.Cursor = await i.client.db.cursor()
    await c.execute(
        "SELECT toggle, character_list FROM talent_notification WHERE user_id = ?",
        (i.user.id,),
    )
    toggle, character_list = await c.fetchone()
    character_list = ast.literal_eval(character_list)
    if not character_list:
        value = text_map.get(158, view.locale)
    else:
        value = ""
        for character in character_list:
            value += f'{get_character(character)["emoji"]} {text_map.get_character_name(character, view.locale)}\n'
    embed = default_embed(message=text_map.get(590, view.locale))
    embed.set_author(
        name=text_map.get(442, view.locale), icon_url=i.user.display_avatar.url
    )
    embed.add_field(name=text_map.get(159, view.locale), value=value)
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
        c: aiosqlite.Cursor = await i.client.db.cursor()
        await c.execute(
            "UPDATE talent_notification SET character_list = '[]' WHERE user_id = ?",
            (i.user.id,),
        )
        await i.client.db.commit()
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


class NotificationON(Button):
    def __init__(self, locale: Locale | str, table_name: str, current: bool):
        super().__init__(
            emoji="🔔",
            label=text_map.get(99, locale),
            style=ButtonStyle.blurple if current else ButtonStyle.gray,
        )
        self.table_name = table_name

    async def callback(self, i: Interaction):
        c: aiosqlite.Cursor = await i.client.db.cursor()
        if self.table_name == "talent_notification" or self.table_name == "weapon_notification":
            await c.execute(
                f"UPDATE {self.table_name} SET toggle = 1 WHERE user_id = ?",
                (i.user.id,),
            )
        else:
            await c.execute(
                f"UPDATE {self.table_name} SET toggle = 1 WHERE user_id = ? AND uid = ?",
                (i.user.id, await get_uid(i.user.id, i.client.db)),
            )
        await i.client.db.commit()
        if self.table_name == "resin_notification":
            await return_resin_notification(i, self.view)
        elif self.table_name == "pot_notification":
            await return_pot_notification(i, self.view)
        elif self.table_name == "talent_notification":
            await return_talent_notification(i, self.view)
        elif self.table_name == "weapon_notification":
            await return_weapon_notification(i, self.view)


class NotificationOFF(Button):
    def __init__(self, locale: Locale | str, table_name: str, current: bool):
        super().__init__(
            emoji="🔕",
            label=text_map.get(100, locale),
            style=ButtonStyle.blurple if current else ButtonStyle.gray,
        )
        self.table_name = table_name

    async def callback(self, i: Interaction):
        c: aiosqlite.Cursor = await i.client.db.cursor()
        if self.table_name == "talent_notification" or self.table_name == "weapon_notification":
            await c.execute(
                f"UPDATE {self.table_name} SET toggle = 0 WHERE user_id = ?",
                (i.user.id,),
            )
        else:
            await c.execute(
                f"UPDATE {self.table_name} SET toggle = 0 WHERE user_id = ? AND uid = ?",
                (i.user.id, await get_uid(i.user.id, i.client.db)),
            )
        await i.client.db.commit()
        if self.table_name == "resin_notification":
            await return_resin_notification(i, self.view)
        elif self.table_name == "pot_notification":
            await return_pot_notification(i, self.view)
        elif self.table_name == "talent_notification":
            await return_talent_notification(i, self.view)
        elif self.table_name == "weapon_notification":
            await return_weapon_notification(i, self.view)


class ChangeSettings(Button):
    def __init__(self, locale: Locale | str, table_name: str):
        super().__init__(emoji="⚙️", label=text_map.get(594, locale))
        self.locale = locale
        self.table_name = table_name

    async def callback(self, i: Interaction):
        c: aiosqlite.Cursor = await i.client.db.cursor()
        uid = await get_uid(i.user.id, i.client.db)
        try:
            if self.table_name == "resin_notification":
                modal = ResinModal(self.locale)
                await i.response.send_modal(modal)
                await modal.wait()
                threshold = modal.resin_threshold.value
                max = modal.max_notif.value
                if not threshold or not max:
                    pass
                else:
                    if not threshold.isdigit() or not max.isdigit():
                        raise ValueError
                    await c.execute(
                        "UPDATE resin_notification SET threshold = ?, max = ? WHERE user_id = ? AND uid = ?",
                        (threshold, max, i.user.id, uid),
                    )
                    await i.client.db.commit()
                await return_resin_notification(i, self.view)
            elif self.table_name == "pot_notification":
                modal = PotModal(self.locale)
                await i.response.send_modal(modal)
                await modal.wait()
                threshold = modal.threshold.value
                max = modal.max_notif.value
                if not threshold or not max:
                    pass
                else:
                    if not threshold.isdigit() or not max.isdigit():
                        raise ValueError
                    await c.execute(
                        "UPDATE pot_notification SET threshold = ?, max = ? WHERE user_id = ? AND uid = ?",
                        (modal.threshold.value, modal.max_notif.value, i.user.id, uid),
                    )
                await i.client.db.commit()
                await return_pot_notification(i, self.view)
            elif self.table_name == "talent_notification":
                await return_talent_notification(i, self.view)
        except ValueError:
            for children in self.view.children:
                children.disabled = True
            await i.edit_original_response(
                embed=error_embed().set_author(
                    name=text_map.get(187, self.locale),
                    icon_url=i.user.display_avatar.url,
                ),
                view=self.view,
            )
            await asyncio.sleep(2)
            await return_notification_menu(i, self.locale)


class GOBack(Button):
    def __init__(self):
        super().__init__(emoji="<:left:982588994778972171>", row=2)

    async def callback(self, i: Interaction):
        await return_notification_menu(i, self.view.locale)


async def return_notification_menu(
    i: Interaction, locale: Locale | str, send: bool = False
):
    c: aiosqlite.Cursor = await i.client.db.cursor()
    uid = await get_uid(i.user.id, i.client.db)
    await c.execute(
        "INSERT INTO resin_notification (user_id, uid) VALUES (?, ?) ON CONFLICT DO NOTHING",
        (i.user.id, uid),
    )
    await c.execute(
        "INSERT INTO pot_notification (user_id, uid) VALUES (?, ?) ON CONFLICT DO NOTHING",
        (i.user.id, uid),
    )
    await c.execute(
        "INSERT INTO talent_notification (user_id) VALUES (?) ON CONFLICT DO NOTHING",
        (i.user.id,),
    )
    await c.execute(
        "INSERT INTO weapon_notification (user_id) VALUES (?) ON CONFLICT DO NOTHING",
        (i.user.id,),
    )
    await i.client.db.commit()
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


class ResinModal(BaseModal):
    resin_threshold = TextInput(label="樹脂閥值", placeholder="例如: 140 (不得大於 160)")
    max_notif = TextInput(label="最大提醒值", placeholder="例如: 5")

    def __init__(self, locale: Locale | str):
        super().__init__(title=text_map.get(151, locale))
        self.resin_threshold.label = text_map.get(152, locale)
        self.resin_threshold.placeholder = text_map.get(153, locale)
        self.max_notif.label = text_map.get(103, locale)
        self.max_notif.placeholder = text_map.get(155, locale)

    async def on_submit(self, interaction: Interaction) -> None:
        await interaction.response.defer()
        self.stop()


class PotModal(BaseModal):
    threshold = TextInput(label="寶錢閥值")
    max_notif = TextInput(label="最大提醒值")

    def __init__(self, locale: Locale):
        super().__init__(title=text_map.get(515, locale))
        self.threshold.label = text_map.get(516, locale)
        self.max_notif.label = text_map.get(103, locale)

    async def on_submit(self, interaction: Interaction) -> None:
        await interaction.response.defer()
        self.stop()
