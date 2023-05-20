from typing import List, Union

import discord
from discord import ui

import dev.asset as asset
import dev.config as config
from ambr import AmbrTopAPI
from apps.db.main import Database
from apps.db.tables.notes_notif import NotifTable
from apps.db.tables.talent_notif import WTNotifTable
from apps.db.tables.user_account import UserAccount
from apps.db.tables.user_settings import Settings
from apps.text_map import text_map, to_ambr_top
from data.game.elements import convert_elements, elements
from data.game.weapon_types import get_weapon_type_emoji
from dev.base_ui import BaseModal, BaseView
from dev.enum import NotifType
from dev.exceptions import InvalidInput, NumbersOnly
from dev.models import DefaultEmbed, Inter
from utils import divide_chunks, get_character_emoji, get_weapon_emoji


class View(BaseView):
    def __init__(self) -> None:
        super().__init__(timeout=config.mid_timeout)
        self.lang: str
        self.user: UserAccount
        self.notif_type: NotifType
        self.uid: int
        self.author: Union[discord.User, discord.Member]

    async def _init(self, i: Inter) -> None:
        """Initialize view attributes"""
        lang = await i.client.db.settings.get(i.user.id, Settings.LANG)
        self.lang = lang or str(i.locale)
        self.user = await i.client.db.users.get(i.user.id)
        self.uid = self.user.uid
        self.author = i.user

    def make_start_embed(self) -> discord.Embed:
        embed = DefaultEmbed(description=text_map.get(592, self.lang))
        embed.set_author(
            name=text_map.get(593, self.lang), icon_url=self.author.display_avatar.url
        )
        return embed

    async def start(self, i: Inter) -> None:
        """Start view"""
        await self._init(i)
        self._add_items()
        embed = self.make_start_embed()

        await i.response.send_message(embed=embed, view=self)
        self.message = await i.original_response()

    def _add_items(self) -> None:
        """Add items to view"""
        self.clear_items()
        self.add_item(ResinNotification(text_map.get(582, self.lang)))
        self.add_item(PotNotification(text_map.get(584, self.lang)))
        self.add_item(PTNotification(text_map.get(704, self.lang)))
        self.add_item(TalentNotification(text_map.get(442, self.lang)))
        self.add_item(WeaponNotification(text_map.get(632, self.lang)))
        self.add_item(PrivacySettings(text_map.get(585, self.lang)))

    async def change_toggle(self, i: Inter, t: bool) -> None:
        db = i.client.db

        if self.notif_type is NotifType.RESIN:
            await db.notifs.resin.update(i.user.id, self.uid, toggle=t)
        elif self.notif_type is NotifType.POT:
            await db.notifs.pot.update(i.user.id, self.uid, toggle=t)
        elif self.notif_type is NotifType.PT:
            await db.notifs.pt.update(i.user.id, self.uid, toggle=t)
        elif self.notif_type is NotifType.TALENT:
            await db.notifs.talent.update(i.user.id, toggle=t)
        elif self.notif_type is NotifType.WEAPON:
            await db.notifs.weapon.update(i.user.id, toggle=t)

        on_button: NotificationON = self.get_item("notification_on")
        on_button.style = discord.ButtonStyle.blurple if t else discord.ButtonStyle.gray
        off_button: NotificationOFF = self.get_item("notification_off")
        off_button.style = (
            discord.ButtonStyle.gray if t else discord.ButtonStyle.blurple
        )

        await i.response.edit_message(view=self)

    def _add_toggles(self, toggle: bool) -> None:
        self.clear_items()
        self.add_item(NotificationON(text_map.get(99, self.lang), toggle))
        self.add_item(NotificationOFF(text_map.get(100, self.lang), toggle))

    async def resin_notif(self, i: Inter, *, responded: bool = False) -> None:
        # Set the notification type to resin
        self.notif_type = NotifType.RESIN

        # Get the database for resin notifications and insert the user's ID and the UID of the current reminder menu
        db = i.client.db.notifs.resin
        await db.insert(i.user.id, self.uid)

        # Get the user's data from the database
        user = await db.get(i.user.id, self.uid)

        # Create a string with the user's toggle, threshold, and max values
        value = f"""
        {text_map.get(302, self.lang)}: {user.threshold}
        {text_map.get(103, self.lang)}: {user.max}
        """

        # Create an embed for the notification
        embed = DefaultEmbed(description=text_map.get(586, self.lang))
        embed.add_field(name=text_map.get(591, self.lang), value=value)
        embed.set_author(
            name=text_map.get(582, self.lang), icon_url=i.user.display_avatar.url
        )

        # Add the toggles to the view
        self.add_item(ChangeSettings(text_map.get(594, self.lang)))
        self._add_toggles(user.toggle)
        self.add_item(GOBack())

        # Edit the response message with the embed and the current view
        if not responded:
            await i.response.edit_message(embed=embed, view=self)
        else:
            await i.edit_original_response(embed=embed, view=self)

    async def pot_notif(self, i: Inter, *, responded: bool = False) -> None:
        self.notif_type = NotifType.POT

        db = i.client.db.notifs.pot
        await db.insert(i.user.id, self.uid)
        user = await db.get(i.user.id, self.uid)

        value = f"""
        {text_map.get(302, self.lang)}: {user.threshold}
        {text_map.get(103, self.lang)}: {user.max}
        """
        embed = DefaultEmbed(description=text_map.get(639, self.lang))
        embed.set_author(
            name=text_map.get(584, self.lang), icon_url=i.user.display_avatar.url
        )
        embed.add_field(name=text_map.get(591, self.lang), value=value)

        self.add_item(ChangeSettings(text_map.get(594, self.lang)))
        self._add_toggles(user.toggle)
        self.add_item(GOBack())

        if not responded:
            await i.response.edit_message(embed=embed, view=self)
        else:
            await i.edit_original_response(embed=embed, view=self)

    async def pt_notif(self, i: Inter, *, responded: bool = False) -> None:
        self.notif_type = NotifType.PT

        db = i.client.db.notifs.pt
        await db.insert(i.user.id, self.uid)
        user = await db.get(i.user.id, self.uid)

        value = f"""
        {text_map.get(103, self.lang)}: {user.max}
        """
        embed = DefaultEmbed(description=text_map.get(512, self.lang))
        embed.add_field(name=text_map.get(591, self.lang), value=value)
        embed.set_author(
            name=text_map.get(704, self.lang), icon_url=i.user.display_avatar.url
        )

        self.add_item(ChangeSettings(text_map.get(594, self.lang)))
        self._add_toggles(user.toggle)
        self.add_item(GOBack())

        if not responded:
            await i.response.edit_message(embed=embed, view=self)
        else:
            await i.edit_original_response(embed=embed, view=self)

    async def weapon_notif(self, i: Inter) -> None:
        # Set the notification type to weapon
        self.notif_type = NotifType.WEAPON

        # Get the database for weapon notifications and insert the user's ID
        db = i.client.db.notifs.weapon
        await db.insert(i.user.id)

        # Get the user's data from the database
        user = await db.get(i.user.id)

        # Create an embed for the notification
        embed = DefaultEmbed(description=text_map.get(590, self.lang))
        embed.set_author(
            name=text_map.get(442, self.lang), icon_url=i.user.display_avatar.url
        )

        # If the user has no items, add a message to the embed
        if not user.item_list:
            value = text_map.get(637, self.lang)
            embed.add_field(name=text_map.get(636, self.lang), value=value)
        else:
            # If the user has items, add them to the embed
            values = []
            for weapon in user.item_list:
                values.append(
                    f"{get_weapon_emoji(int(weapon))} {text_map.get_weapon_name(int(weapon), self.lang)}\n"
                )
            values = list(divide_chunks(values, 20))
            for index, value in enumerate(values):
                embed.add_field(
                    name=text_map.get(636, self.lang) + f" (#{index+1})",
                    value="".join(value),
                )

        self._add_toggles(user.toggle)
        self.add_item(AddWeapon(self.lang))
        self.add_item(RemoveAllWeapon(self.lang))
        self.add_item(GOBack())

        # Edit the response message with the embed and the current view
        await i.response.edit_message(embed=embed, view=self)

    async def talent_notif(self, i: Inter) -> None:
        # Set the notification type to talent
        self.notif_type = NotifType.TALENT

        # Get the database for talent notifications and insert the user's ID
        db = i.client.db.notifs.talent
        await db.insert(i.user.id)

        # Get the user's data from the database
        user = await db.get(i.user.id)

        # Create an embed for the notification
        embed = DefaultEmbed(description=text_map.get(633, self.lang))
        embed.set_author(
            name=text_map.get(632, self.lang), icon_url=i.user.display_avatar.url
        )

        # If the user has no items, add a message to the embed
        if not user.item_list:
            value = text_map.get(158, self.lang)
            embed.add_field(name=text_map.get(159, self.lang), value=value)
        else:
            # If the user has items, add them to the embed
            values = []
            for character in user.item_list:
                values.append(
                    f"{get_character_emoji(character)} {text_map.get_character_name(character, self.lang)}\n"
                )
            values = list(divide_chunks(values, 20))
            for index, value in enumerate(values):
                embed.add_field(
                    name=text_map.get(159, self.lang) + f" (#{index+1})",
                    value="".join(value),
                )

        self._add_toggles(user.toggle)
        self.add_item(AddCharacter(self.lang))
        self.add_item(RemoveAllCharacter(self.lang))
        self.add_item(GOBack())

        # Edit the response message with the embed and the current view
        await i.response.edit_message(embed=embed, view=self)


class ResinNotification(ui.Button):
    def __init__(self, label: str):
        super().__init__(emoji=asset.resin_emoji, label=label)
        self.view: View

    async def callback(self, i: Inter):
        await self.view.resin_notif(i)


class PotNotification(ui.Button):
    def __init__(self, label: str):
        super().__init__(emoji=asset.realm_currency_emoji, label=label)
        self.view: View

    async def callback(self, i: Inter):
        await self.view.pot_notif(i)


class TalentNotification(ui.Button):
    def __init__(self, label: str):
        super().__init__(emoji=asset.talent_book_emoji, label=label, row=2)
        self.view: View

    async def callback(self, i: Inter):
        await self.view.talent_notif(i)


class WeaponNotification(ui.Button):
    def __init__(self, label: str):
        super().__init__(emoji=asset.weapon_emoji, label=label, row=2)
        self.view: View

    async def callback(self, i: Inter):
        await self.view.weapon_notif(i)


class PTNotification(ui.Button):
    def __init__(self, label: str):
        super().__init__(emoji=asset.pt_emoji, label=label)
        self.view: View

    async def callback(self, i: Inter):
        await self.view.pt_notif(i)


class AddWeapon(ui.Button):
    def __init__(self, lang: str):
        super().__init__(
            emoji=asset.add_emoji,
            label=text_map.get(634, lang),
            row=1,
            style=discord.ButtonStyle.green,
        )
        self.lang = lang
        self.view: View

    async def callback(self, i: discord.Interaction):
        ambr = AmbrTopAPI(i.client.session, to_ambr_top(self.lang))  # type: ignore
        weapon_types = await ambr.get_weapon_types()

        self.view.clear_items()
        num = 1
        for weapon_type_id, weapon_type in weapon_types.items():
            self.view.add_item(
                WeaponTypeButton(
                    get_weapon_type_emoji(weapon_type_id),
                    weapon_type,
                    weapon_type_id,
                    num // 3,
                )
            )
            num += 1

        await i.response.edit_message(view=self.view)


class RemoveAllWeapon(ui.Button):
    def __init__(self, lang: str):
        super().__init__(
            emoji=asset.remove_emoji,
            label=text_map.get(635, lang),
            row=1,
            style=discord.ButtonStyle.red,
        )
        self.view: View

    async def callback(self, i: Inter):
        db = i.client.db.notifs.weapon
        await db.update(i.user.id, item_list=[])
        await self.view.weapon_notif(i)


class AddCharacter(ui.Button):
    def __init__(self, lang: str):
        super().__init__(
            emoji=asset.add_emoji,
            label=text_map.get(598, lang),
            row=1,
            style=discord.ButtonStyle.green,
        )
        self.lang = lang
        self.view: View

    async def callback(self, i: discord.Interaction):
        self.view.clear_items()
        element_names = list(convert_elements.values())
        element_emojis = list(elements.values())
        for index in range(0, 7):
            self.view.add_item(
                ElementButton(element_names[index], element_emojis[index], index // 4)
            )
        await i.response.edit_message(view=self.view)


class RemoveAllCharacter(ui.Button):
    def __init__(self, lang: str):
        super().__init__(
            emoji=asset.remove_emoji,
            label=text_map.get(599, lang),
            row=1,
            style=discord.ButtonStyle.red,
        )
        self.view: View

    async def callback(self, i: Inter):
        db = i.client.db.notifs.talent
        await db.update(i.user.id, item_list=[])
        await self.view.talent_notif(i)


class PrivacySettings(ui.Button):
    def __init__(self, label: str):
        super().__init__(emoji="✉️", label=label, row=2)
        self.view: View

    async def callback(self, i: discord.Interaction):
        lang = self.view.lang
        embed = DefaultEmbed(description=text_map.get(595, lang))
        embed.set_author(
            name=text_map.get(311, lang),
            icon_url=i.user.display_avatar.url,
        )
        embed.set_image(url="https://i.imgur.com/FIVzwXb.gif")

        self.view.clear_items()
        self.view.add_item(GOBack())
        self.view.add_item(TestItOut(lang, embed))
        await i.response.edit_message(embed=embed, view=self.view)


class TestItOut(ui.Button):
    def __init__(self, lang: str, embed: discord.Embed):
        super().__init__(emoji="📨", label=text_map.get(596, lang))
        self.lang = lang
        self.embed = embed

    async def callback(self, i: discord.Interaction):
        await i.response.defer()
        try:
            await i.user.send("Hello There!\n哈囉!")
        except discord.Forbidden:
            embed = self.embed
            embed.author.name = text_map.get(597, self.lang)
            embed.color = 0xFC5165
            await i.edit_original_response(embed=embed)


class NotificationON(ui.Button):
    def __init__(self, label: str, current_toggle: bool):
        super().__init__(
            emoji=asset.bell_outline,
            label=label,
            style=discord.ButtonStyle.blurple
            if current_toggle
            else discord.ButtonStyle.gray,
            custom_id="notification_on",
        )
        self.view: View

    async def callback(self, i: Inter):
        await self.view.change_toggle(i, True)


class NotificationOFF(ui.Button):
    def __init__(self, label: str, current_toggle: bool):
        super().__init__(
            emoji=asset.bell_off_outline,
            label=label,
            style=discord.ButtonStyle.blurple
            if not current_toggle
            else discord.ButtonStyle.gray,
            custom_id="notification_off",
        )
        self.view: View

    async def callback(self, i: Inter):
        await self.view.change_toggle(i, False)


class ChangeSettings(ui.Button):
    def __init__(self, label: str):
        super().__init__(emoji=asset.settings_emoji, label=label)
        self.view: View

    async def callback(self, i: Inter):
        notif_type = self.view.notif_type
        lang = self.view.lang

        if notif_type is NotifType.RESIN:
            modal = ResinModal(lang)
            await i.response.send_modal(modal)
            await modal.wait()
            t = modal.threshold.value
            m = modal.max_notif.value
            if t and m:
                if not t.isdigit() or not m.isdigit():
                    raise NumbersOnly
                if int(t) < 0 or int(t) > 160:
                    raise InvalidInput(0, 160)
                if int(m) < 0 or int(m) > 10:
                    raise InvalidInput(0, 10)
                db = i.client.db.notifs.resin
                await db.update(i.user.id, self.view.uid, threshold=int(t), max=int(m))
                await self.view.resin_notif(i, responded=True)

        elif notif_type is NotifType.POT:
            modal = PotModal(lang)
            await i.response.send_modal(modal)
            await modal.wait()
            t = modal.threshold.value
            m = modal.max_notif.value
            if t and m:
                if not t.isdigit() or not m.isdigit():
                    raise NumbersOnly
                if int(t) < 0 or int(t) > 99999:
                    raise InvalidInput(0, 99999)
                if int(m) < 0 or int(m) > 10:
                    raise InvalidInput(0, 10)
                db = i.client.db.notifs.pot
                await db.update(i.user.id, self.view.uid, threshold=int(t), max=int(m))
                await self.view.pot_notif(i, responded=True)

        elif notif_type is NotifType.PT:
            modal = PTModal(lang)
            await i.response.send_modal(modal)
            await modal.wait()
            m = modal.max_notif.value
            if m:
                if not m.isdigit():
                    raise NumbersOnly
                if int(m) < 0 or int(m) > 10:
                    raise InvalidInput(0, 10)
                db = i.client.db.notifs.pt
                await db.update(i.user.id, self.view.uid, max=int(m))
                await self.view.pt_notif(i, responded=True)


class GOBack(ui.Button):
    def __init__(self):
        super().__init__(emoji=asset.back_emoji, row=2)
        self.view: View

    async def callback(self, i: discord.Interaction):
        self.view._add_items()
        embed = self.view.make_start_embed()
        await i.response.edit_message(embed=embed, view=self.view)


class ResinModal(BaseModal):
    threshold = ui.TextInput(
        label="RESIN_THRESHOLD", placeholder="FOR_EXAMPLE: 140", max_length=3
    )
    max_notif = ui.TextInput(
        label="MAX_NOTIF", placeholder="FOR_EXAMPLE: 5", max_length=2
    )

    def __init__(self, lang: str):
        super().__init__(title=text_map.get(515, lang))
        self.threshold.label = text_map.get(152, lang)
        self.threshold.placeholder = text_map.get(170, lang).format(a=140)
        self.max_notif.label = text_map.get(103, lang)
        self.max_notif.placeholder = text_map.get(155, lang)

    async def on_submit(self, i: discord.Interaction) -> None:
        await i.response.defer()
        self.stop()


class PotModal(BaseModal):
    threshold = ui.TextInput(label="CURRENCY_THRESHOLD", max_length=5)
    max_notif = ui.TextInput(label="MAX_NOTIF", max_length=2)

    def __init__(self, lang: str):
        super().__init__(title=text_map.get(515, lang))
        self.threshold.label = text_map.get(302, lang)
        self.threshold.placeholder = text_map.get(170, lang).format(a=2000)
        self.max_notif.label = text_map.get(103, lang)
        self.max_notif.placeholder = text_map.get(155, lang)

    async def on_submit(self, i: discord.Interaction) -> None:
        await i.response.defer()
        self.stop()


class PTModal(BaseModal):
    max_notif = ui.TextInput(label="MAX_NOTIF", max_length=2)

    def __init__(self, lang: str):
        super().__init__(title=text_map.get(515, lang))
        self.max_notif.label = text_map.get(103, lang)
        self.max_notif.placeholder = text_map.get(155, lang)

    async def on_submit(self, i: discord.Interaction) -> None:
        await i.response.defer()
        self.stop()


class ElementButton(ui.Button):
    def __init__(self, element: str, emoji: str, row: int):
        super().__init__(emoji=emoji, row=row)
        self.element = element
        self.view: View

    async def callback(self, i: Inter):
        user = await i.client.db.notifs.talent.get(i.user.id)

        client = AmbrTopAPI(i.client.session, to_ambr_top(self.view.lang))
        characters = await client.get_character()
        if not isinstance(characters, list):
            raise AssertionError("Characters is not a list")

        options: List[discord.SelectOption] = []
        for character in characters:
            if character.element == self.element:
                description = (
                    text_map.get(161, self.view.lang)
                    if character.id in user.item_list
                    else None
                )
                options.append(
                    discord.SelectOption(
                        label=character.name,
                        emoji=get_character_emoji(str(character.id)),
                        value=character.id,
                        description=description,
                    )
                )

        self.view.clear_items()
        self.view.add_item(GOBack())
        self.view.add_item(
            CharacterSelect(options, text_map.get(157, self.view.lang), user.item_list)
        )
        await i.response.edit_message(view=self.view)


class CharacterSelect(ui.Select):
    def __init__(
        self,
        options: List[discord.SelectOption],
        placeholder: str,
        item_list: List[str],
    ):
        super().__init__(
            options=options, placeholder=placeholder, max_values=len(options)
        )
        self.view: View
        self.item_list = item_list

    async def callback(self, i: Inter):
        for character_id in self.values:
            if character_id in self.item_list:
                self.item_list.remove(character_id)
            else:
                self.item_list.append(character_id)
        await i.client.db.notifs.talent.update(i.user.id, item_list=self.item_list)

        await self.view.talent_notif(i)


class WeaponTypeButton(ui.Button):
    def __init__(self, emoji: str, label: str, weapon_type: str, row: int):
        super().__init__(emoji=emoji, label=label, row=row)
        self.weapon_type = weapon_type
        self.view: View

    async def callback(self, i: Inter):
        user = await i.client.db.notifs.weapon.get(i.user.id)

        ambr = AmbrTopAPI(i.client.session, to_ambr_top(self.view.lang))
        weapons = await ambr.get_weapon()
        if not isinstance(weapons, list):
            raise AssertionError("Expected list of weapons, got something else")

        select_options = []
        for weapon in weapons:
            if weapon.type == self.weapon_type:
                description = (
                    text_map.get(638, self.view.lang)
                    if str(weapon.id) in user.item_list
                    else None
                )
                select_options.append(
                    discord.SelectOption(
                        emoji=get_weapon_emoji(weapon.id),
                        label=weapon.name,
                        value=str(weapon.id),
                        description=description,
                    )
                )

        self.view.clear_items()
        self.view.add_item(GOBack())

        select_options = list(divide_chunks(select_options, 25))
        count = 1
        for options in select_options:
            self.view.add_item(
                WeaponSelect(
                    options,
                    f"{text_map.get(180, self.view.lang)} ({count}~{count+len(options)-1})",
                    user.item_list,
                )
            )
            count += len(options)
        await i.response.edit_message(view=self.view)


class WeaponSelect(ui.Select):
    def __init__(
        self,
        options: List[discord.SelectOption],
        placeholder: str,
        item_list: List[str],
    ):
        super().__init__(
            options=options, placeholder=placeholder, max_values=len(options)
        )

        self.item_list = item_list
        self.view: View

    async def callback(self, i: Inter):
        for weapon_id in self.values:
            if weapon_id in self.item_list:
                self.item_list.remove(weapon_id)
            else:
                self.item_list.append(weapon_id)

        await i.client.db.notifs.weapon.update(i.user.id, item_list=self.item_list)

        await self.view.weapon_notif(i)
