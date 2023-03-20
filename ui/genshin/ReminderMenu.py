import asyncpg
import discord
from discord import ui

import asset
import config
from ambr.client import AmbrTopAPI
from apps.genshin.checks import check_cookie_predicate
from apps.genshin.utils import get_character_emoji, get_uid, get_weapon_emoji
from apps.text_map.convert_locale import to_ambr_top
from apps.text_map.text_map_app import text_map
from exceptions import NumbersOnly
from base_ui import BaseModal, BaseView
from ui.genshin import TalentNotificationMenu, WeaponNotificationMenu
from utility.utils import DefaultEmbed, divide_chunks


class View(BaseView):
    def __init__(self, locale: discord.Locale | str):
        super().__init__(timeout=config.mid_timeout)
        self.locale = locale
        self.add_item(ResinNotification(locale))
        self.add_item(PotNotification(locale))
        self.add_item(PTNotification(text_map.get(704, locale)))
        self.add_item(TalentNotification(locale))
        self.add_item(WeaponNotification(locale))
        self.add_item(PrivacySettings(locale))


class ResinNotification(ui.Button):
    def __init__(self, locale: discord.Locale | str):
        super().__init__(emoji=asset.resin_emoji, label=text_map.get(582, locale))
        self.view: View

    async def callback(self, i: discord.Interaction):
        await check_cookie_predicate(i)
        await return_resin_notification(i, self.view)


class PotNotification(ui.Button):
    def __init__(self, locale: discord.Locale | str):
        super().__init__(
            emoji=asset.realm_currency_emoji, label=text_map.get(584, locale)
        )
        self.view: View

    async def callback(self, i: discord.Interaction):
        await check_cookie_predicate(i)
        await return_pot_notification(i, self.view)


class TalentNotification(ui.Button):
    def __init__(self, locale: discord.Locale | str):
        super().__init__(
            emoji=asset.talent_book_emoji, label=text_map.get(442, locale), row=2
        )
        self.view: View

    async def callback(self, i: discord.Interaction):
        await return_talent_notification(i, self.view)


class WeaponNotification(ui.Button):
    def __init__(self, locale: discord.Locale | str):
        super().__init__(
            emoji=asset.weapon_emoji, label=text_map.get(632, locale), row=2
        )
        self.view: View

    async def callback(self, i: discord.Interaction):
        await return_weapon_notification(i, self.view)


class PTNotification(ui.Button):
    def __init__(self, label: str):
        super().__init__(emoji=asset.pt_emoji, label=label)
        self.view: View

    async def callback(self, i: discord.Interaction):
        await check_cookie_predicate(i)
        await return_pt_notification(i, self.view)


class AddWeapon(ui.Button):
    def __init__(self, locale: discord.Locale | str):
        super().__init__(
            emoji=asset.add_emoji,
            label=text_map.get(634, locale),
            row=1,
            style=discord.ButtonStyle.green,
        )
        self.locale = locale

    async def callback(self, i: discord.Interaction):
        ambr = AmbrTopAPI(i.client.session, to_ambr_top(self.locale))  # type: ignore
        view = WeaponNotificationMenu.View(self.locale, await ambr.get_weapon_types())
        await i.response.edit_message(view=view)
        view.author = i.user
        view.message = await i.original_response()


class RemoveAllWeapon(ui.Button):
    def __init__(self, locale: discord.Locale | str):
        super().__init__(
            emoji=asset.remove_emoji,
            label=text_map.get(635, locale),
            row=1,
            style=discord.ButtonStyle.red,
        )
        self.view: View

    async def callback(self, i: discord.Interaction):
        pool: asyncpg.Pool = i.client.pool  # type: ignore
        await pool.execute(
            "UPDATE weapon_notification SET item_list = $1 WHERE user_id = $2",
            [],
            i.user.id,
        )
        await return_weapon_notification(i, self.view)


class AddCharacter(ui.Button):
    def __init__(self, locale: discord.Locale | str):
        super().__init__(
            emoji=asset.add_emoji,
            label=text_map.get(598, locale),
            row=1,
            style=discord.ButtonStyle.green,
        )
        self.locale = locale

    async def callback(self, i: discord.Interaction):
        view = TalentNotificationMenu.View(self.locale)
        await i.response.edit_message(view=view)
        view.author = i.user
        view.message = await i.original_response()


class RemoveAllCharacter(ui.Button):
    def __init__(self, locale: discord.Locale | str):
        super().__init__(
            emoji=asset.remove_emoji,
            label=text_map.get(599, locale),
            row=1,
            style=discord.ButtonStyle.red,
        )
        self.view: View

    async def callback(self, i: discord.Interaction):
        pool: asyncpg.Pool = i.client.pool  # type: ignore
        await pool.execute(
            "UPDATE talent_notification SET item_list = $1 WHERE user_id = $2",
            [],
            i.user.id,
        )
        await return_talent_notification(i, self.view)


class PrivacySettings(ui.Button):
    def __init__(self, locale: discord.Locale | str):
        super().__init__(emoji="✉️", label=text_map.get(585, locale), row=2)
        self.locale = locale
        self.view: View

    async def callback(self, i: discord.Interaction):
        embed = DefaultEmbed(description=text_map.get(595, self.locale))
        embed.set_author(
            name=text_map.get(311, self.locale),
            icon_url=i.user.display_avatar.url,
        )
        embed.set_image(url="https://i.imgur.com/FIVzwXb.gif")

        self.view.clear_items()
        self.view.add_item(GOBack())
        self.view.add_item(TestItOut(self.locale, embed))
        await i.response.edit_message(embed=embed, view=self.view)


class TestItOut(ui.Button):
    def __init__(self, locale: discord.Locale | str, embed: discord.Embed):
        super().__init__(emoji="📨", label=text_map.get(596, locale))
        self.locale = locale
        self.embed = embed

    async def callback(self, i: discord.Interaction):
        await i.response.defer()
        try:
            await i.user.send("Hello There!\n哈囉!")
        except discord.Forbidden:
            embed = self.embed
            embed.author.name = text_map.get(597, self.locale)
            embed.color = 0xFC5165
            await i.edit_original_response(embed=embed)


class NotificationON(ui.Button):
    def __init__(self, locale: discord.Locale | str, table_name: str, current: bool):
        super().__init__(
            emoji=asset.bell_outline,
            label=text_map.get(99, locale),
            style=discord.ButtonStyle.blurple if current else discord.ButtonStyle.gray,
        )
        self.table_name = table_name
        self.view: View

    async def callback(self, i: discord.Interaction):
        await on_off_function(self.view, self.table_name, i, True)


class NotificationOFF(ui.Button):
    def __init__(self, locale: discord.Locale | str, table_name: str, current: bool):
        super().__init__(
            emoji=asset.bell_off_outline,
            label=text_map.get(100, locale),
            style=discord.ButtonStyle.blurple
            if not current
            else discord.ButtonStyle.gray,
        )
        self.table_name = table_name
        self.view: View

    async def callback(self, i: discord.Interaction):
        await on_off_function(self.view, self.table_name, i, False)


class ChangeSettings(ui.Button):
    def __init__(self, locale: discord.Locale | str, table_name: str):
        super().__init__(emoji=asset.settings_emoji, label=text_map.get(594, locale))
        self.locale = locale
        self.table_name = table_name

    async def callback(self, i: discord.Interaction):
        if self.table_name == "resin_notification":
            modal = ResinModal(self.locale)
        elif self.table_name == "pot_notification":
            modal = PotModal(self.locale)
        else:  # pt_notification
            modal = PTModal(self.locale)
        await i.response.send_modal(modal)


class GOBack(ui.Button):
    def __init__(self):
        super().__init__(emoji=asset.back_emoji, row=2)
        self.view: View

    async def callback(self, i: discord.Interaction):
        await return_notification_menu(i, self.view.locale)


class ResinModal(BaseModal):
    threshold = ui.TextInput(
        label="樹脂閥值", placeholder="例如: 140 (不得大於 160)", max_length=3
    )
    max_notif = ui.TextInput(label="最大提醒值", placeholder="例如: 5", max_length=3)

    def __init__(self, locale: discord.Locale | str):
        super().__init__(title=text_map.get(515, locale))
        self.threshold.label = text_map.get(152, locale)
        self.threshold.placeholder = text_map.get(170, locale).format(a=140)
        self.max_notif.label = text_map.get(103, locale)
        self.max_notif.placeholder = text_map.get(155, locale)

        self.locale = locale

    async def on_submit(self, i: discord.Interaction) -> None:
        await i.response.defer()
        if not self.threshold.value.isdigit() or not self.max_notif.value.isdigit():
            raise NumbersOnly

        await resin_pot_modal_on_submit(
            i,
            self.locale,
            int(self.threshold.value),
            int(self.max_notif.value),
            "resin_notification",
        )


class PotModal(BaseModal):
    threshold = ui.TextInput(label="寶錢閥值", max_length=5)
    max_notif = ui.TextInput(label="最大提醒值", max_length=3)

    def __init__(self, locale: discord.Locale | str):
        super().__init__(title=text_map.get(515, locale))
        self.threshold.label = text_map.get(516, locale)
        self.threshold.placeholder = text_map.get(170, locale).format(a=2000)
        self.max_notif.label = text_map.get(103, locale)
        self.max_notif.placeholder = text_map.get(155, locale)

        self.locale = locale

    async def on_submit(self, i: discord.Interaction) -> None:
        await i.response.defer()
        if not self.threshold.value.isdigit() or not self.max_notif.value.isdigit():
            raise NumbersOnly

        await resin_pot_modal_on_submit(
            i,
            self.locale,
            int(self.threshold.value),
            int(self.max_notif.value),
            "pot_notification",
        )


class PTModal(BaseModal):
    max_notif = ui.TextInput(label="最大提醒值", max_length=3)

    def __init__(self, locale: discord.Locale | str):
        super().__init__(title=text_map.get(515, locale))
        self.max_notif.label = text_map.get(103, locale)
        self.max_notif.placeholder = text_map.get(155, locale)

        self.locale = locale

    async def on_submit(self, i: discord.Interaction) -> None:
        await i.response.defer()
        if not self.max_notif.value.isdigit():
            raise NumbersOnly

        pool: asyncpg.pool.Pool = i.client.pool  # type: ignore
        await pool.execute(
            """
            UPDATE pt_notification
            SET max = $1
            WHERE user_id = $2 AND uid = $3
            """,
            int(self.max_notif.value),
            i.user.id,
            await get_uid(i.user.id, pool),
        )

        await return_pt_notification(i, View(self.locale))


# Functions
async def return_resin_notification(i: discord.Interaction, view: View):
    pool: asyncpg.pool.Pool = i.client.pool  # type: ignore
    uid = await get_uid(i.user.id, pool)

    await pool.execute(
        """
        INSERT INTO resin_notification (user_id, uid)
        VALUES ($1, $2)
        ON CONFLICT DO NOTHING
        """,
        i.user.id,
        uid,
    )
    row = await pool.fetchrow(
        """
        SELECT toggle, threshold, max
        FROM resin_notification
        WHERE user_id = $1 AND uid = $2
        """,
        i.user.id,
        uid,
    )

    value = f"""
    {text_map.get(101, view.locale)}: {text_map.get(99 if row['toggle'] else 100, view.locale)}
    {text_map.get(302, view.locale)}: {row['threshold']}
    {text_map.get(103, view.locale)}: {row['max']}
    """
    embed = DefaultEmbed(description=text_map.get(586, view.locale))
    embed.add_field(name=text_map.get(591, view.locale), value=value)
    embed.set_author(
        name=text_map.get(582, view.locale), icon_url=i.user.display_avatar.url
    )

    view.clear_items()
    view.add_item(GOBack())
    view.add_item(ChangeSettings(view.locale, "resin_notification"))
    view.add_item(NotificationON(view.locale, "resin_notification", row["toggle"]))
    view.add_item(NotificationOFF(view.locale, "resin_notification", row["toggle"]))

    try:
        await i.response.edit_message(embed=embed, view=view)
    except discord.InteractionResponded:
        await i.edit_original_response(embed=embed, view=view)


async def return_pt_notification(i: discord.Interaction, view: View):
    pool: asyncpg.pool.Pool = i.client.pool  # type: ignore
    uid = await get_uid(i.user.id, pool)

    await pool.execute(
        """
        INSERT INTO pt_notification (user_id, uid)
        VALUES ($1, $2)
        ON CONFLICT DO NOTHING
        """,
        i.user.id,
        uid,
    )
    row = await pool.fetchrow(
        """
        SELECT toggle, max
        FROM pt_notification
        WHERE user_id = $1 AND uid = $2
        """,
        i.user.id,
        uid,
    )

    value = f"""
        {text_map.get(101, view.locale)}: {text_map.get(99 if row['toggle'] else 100, view.locale)}
        {text_map.get(103, view.locale)}: {row['max']}
    """
    embed = DefaultEmbed(description=text_map.get(512, view.locale))
    embed.add_field(name=text_map.get(591, view.locale), value=value)
    embed.set_author(
        name=text_map.get(704, view.locale), icon_url=i.user.display_avatar.url
    )

    view.clear_items()
    view.add_item(ChangeSettings(view.locale, "pt_notification"))
    view.add_item(GOBack())
    view.add_item(NotificationON(view.locale, "pt_notification", row["toggle"]))
    view.add_item(NotificationOFF(view.locale, "pt_notification", row["toggle"]))

    try:
        await i.response.edit_message(embed=embed, view=view)
    except discord.InteractionResponded:
        await i.edit_original_response(embed=embed, view=view)


async def return_pot_notification(i: discord.Interaction, view: View):
    pool: asyncpg.pool.Pool = i.client.pool  # type: ignore
    uid = await get_uid(i.user.id, pool)

    await pool.execute(
        """
        INSERT INTO pot_notification (user_id, uid)
        VALUES ($1, $2)
        ON CONFLICT DO NOTHING
        """,
        i.user.id,
        uid,
    )
    row = await pool.fetchrow(
        """
        SELECT toggle, threshold, max
        FROM pot_notification
        WHERE user_id = $1 AND uid = $2
        """,
        i.user.id,
        uid,
    )

    value = f"""
    {text_map.get(101, view.locale)}: {text_map.get(99 if row['toggle'] else 100, view.locale)}
    {text_map.get(302, view.locale)}: {row['threshold']}
    {text_map.get(103, view.locale)}: {row['max']}
    """
    embed = DefaultEmbed(description=text_map.get(639, view.locale))
    embed.set_author(
        name=text_map.get(584, view.locale), icon_url=i.user.display_avatar.url
    )
    embed.add_field(name=text_map.get(591, view.locale), value=value)

    view.clear_items()
    view.add_item(GOBack())
    view.add_item(ChangeSettings(view.locale, "pot_notification"))
    view.add_item(NotificationON(view.locale, "pot_notification", row["toggle"]))
    view.add_item(NotificationOFF(view.locale, "pot_notification", row["toggle"]))

    try:
        await i.response.edit_message(embed=embed, view=view)
    except discord.InteractionResponded:
        await i.edit_original_response(embed=embed, view=view)


async def return_talent_notification(i: discord.Interaction, view: View):
    pool: asyncpg.pool.Pool = i.client.pool  # type: ignore

    await pool.execute(
        """
        INSERT INTO talent_notification (user_id, item_list)
        VALUES ($1, $2)
        ON CONFLICT DO NOTHING
        """,
        i.user.id,
        [],
    )
    row = await pool.fetchrow(
        """
        SELECT toggle, item_list
        FROM talent_notification
        WHERE user_id = $1
        """,
        i.user.id,
    )

    embed = DefaultEmbed(description=text_map.get(590, view.locale))
    embed.set_author(
        name=text_map.get(442, view.locale), icon_url=i.user.display_avatar.url
    )
    if not row["item_list"]:
        value = text_map.get(158, view.locale)
        embed.add_field(name=text_map.get(159, view.locale), value=value)
    else:
        values = []
        for character in row["item_list"]:
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
    view.add_item(NotificationON(view.locale, "talent_notification", row["toggle"]))
    view.add_item(NotificationOFF(view.locale, "talent_notification", row["toggle"]))

    try:
        await i.response.edit_message(embed=embed, view=view)
    except discord.InteractionResponded:
        await i.edit_original_response(embed=embed, view=view)


async def return_weapon_notification(i: discord.Interaction, view: View):
    pool: asyncpg.pool.Pool = i.client.pool  # type: ignore

    await pool.execute(
        """
        INSERT INTO weapon_notification (user_id, item_list)
        VALUES ($1, $2)
        ON CONFLICT DO NOTHING
        """,
        i.user.id,
        [],
    )
    row = await pool.fetchrow(
        """
        SELECT toggle, item_list
        FROM weapon_notification
        WHERE user_id = $1
        """,
        i.user.id,
    )

    embed = DefaultEmbed(description=text_map.get(633, view.locale))
    embed.set_author(
        name=text_map.get(632, view.locale), icon_url=i.user.display_avatar.url
    )
    if not row["item_list"]:
        value = text_map.get(637, view.locale)
        embed.add_field(name=text_map.get(636, view.locale), value=value)
    else:
        values = []
        for weapon in row["item_list"]:
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
    view.add_item(NotificationON(view.locale, "weapon_notification", row["toggle"]))
    view.add_item(NotificationOFF(view.locale, "weapon_notification", row["toggle"]))

    try:
        await i.response.edit_message(embed=embed, view=view)
    except discord.InteractionResponded:
        await i.edit_original_response(embed=embed, view=view)


async def return_notification_menu(
    i: discord.Interaction, locale: discord.Locale | str, send: bool = False
):
    embed = DefaultEmbed(description=text_map.get(592, locale))
    embed.set_author(name=text_map.get(593, locale), icon_url=i.user.display_avatar.url)

    view = View(locale)
    if send:
        await i.response.send_message(embed=embed, view=view)
        view.message = await i.original_response()
    else:
        try:
            await i.response.edit_message(embed=embed, view=view)
            view.message = await i.original_response()
        except discord.InteractionResponded:
            view.message = await i.edit_original_response(embed=embed, view=view)
    view.author = i.user


async def resin_pot_modal_on_submit(
    i: discord.Interaction,
    locale: discord.Locale | str,
    threshold: int,
    max_notif: int,
    table_name: str,
):
    pool: asyncpg.Pool = i.client.pool  # type: ignore
    uid = await get_uid(i.user.id, pool)

    await pool.execute(
        f"""
        UPDATE {table_name}
        SET threshold = $1, max = $2
        WHERE user_id = $3 AND uid = $4
        """,
        threshold,
        max_notif,
        i.user.id,
        uid,
    )
    if table_name == "resin_notification":
        await return_resin_notification(i, View(locale))
    elif table_name == "pot_notification":
        await return_pot_notification(i, View(locale))


async def on_off_function(
    view: View, table_name: str, i: discord.Interaction, toggle: bool
):
    pool: asyncpg.Pool = i.client.pool  # type: ignore
    if table_name in ["talent_notification", "weapon_notification"]:
        await pool.execute(
            f"UPDATE {table_name} SET toggle = $1 WHERE user_id = $2", toggle, i.user.id
        )
    else:
        await pool.execute(
            f"UPDATE {table_name} SET toggle = $1 WHERE user_id = $2 AND uid = $3",
            toggle,
            i.user.id,
            await get_uid(i.user.id, pool),
        )

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
