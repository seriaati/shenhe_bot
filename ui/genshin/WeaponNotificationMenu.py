import asyncpg
from typing import Dict, List

from discord import Interaction, Locale, SelectOption
from discord.ui import Button, Select

import config
from ambr.client import AmbrTopAPI
from apps.genshin.utils import get_weapon_emoji
from apps.text_map import to_ambr_top
from apps.text_map import text_map
from data.game.weapon_types import get_weapon_type_emoji
from base_ui import BaseView
from ui.genshin import ReminderMenu
from utility import divide_chunks


class View(BaseView):
    def __init__(self, locale: Locale | str, weapon_types: Dict[str, str]):
        super().__init__(timeout=config.mid_timeout)
        self.locale = locale
        for weapon_type_id, weapon_type in weapon_types.items():
            self.add_item(
                WeaponTypeButton(
                    get_weapon_type_emoji(weapon_type_id),
                    weapon_type,
                    weapon_type_id,
                )
            )
        self.add_item(GOBackReminder())


class GOBackReminder(Button):
    def __init__(self):
        super().__init__(emoji="<:left:982588994778972171>", row=2)

    async def callback(self, i: Interaction):
        await ReminderMenu.return_weapon_notification(i, self.view)  # type: ignore


class GOBack(Button):
    def __init__(self):
        super().__init__(emoji="<:left:982588994778972171>", row=2)
        self.view: View

    async def callback(self, i: Interaction):
        self.view.clear_items()

        ambr = AmbrTopAPI(i.client.session, to_ambr_top(self.view.locale))  # type: ignore
        weapon_types = await ambr.get_weapon_types()

        for weapon_type_id, weapon_type in weapon_types.items():
            self.view.add_item(
                WeaponTypeButton(
                    get_weapon_type_emoji(weapon_type_id),
                    weapon_type,
                    weapon_type_id,
                )
            )
        self.view.add_item(GOBackReminder())
        await i.response.edit_message(view=self.view)


class WeaponTypeButton(Button):
    def __init__(self, emoji: str, label: str, weapon_type: str):
        super().__init__(emoji=emoji, label=label)
        self.weapon_type = weapon_type
        self.view: View

    async def callback(self, i: Interaction):
        pool: asyncpg.Pool = i.client.pool  # type: ignore

        weapon_list: List[str] = await pool.fetchval(
            "SELECT item_list FROM weapon_notification WHERE user_id = $1", i.user.id
        )

        ambr = AmbrTopAPI(i.client.session, to_ambr_top(self.view.locale))  # type: ignore
        weapons = await ambr.get_weapon()
        if not isinstance(weapons, list):
            raise AssertionError

        select_options = []
        for weapon in weapons:
            if weapon.type == self.weapon_type:
                description = (
                    text_map.get(638, self.view.locale)
                    if str(weapon.id) in weapon_list
                    else None
                )
                select_options.append(
                    SelectOption(
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
                    f"{text_map.get(180, self.view.locale)} ({count}~{count+len(options)-1})",
                )
            )
            count += len(options)
        await i.response.edit_message(view=self.view)


class WeaponSelect(Select):
    def __init__(self, options: List[SelectOption], placeholder: str):
        super().__init__(
            options=options, placeholder=placeholder, max_values=len(options)
        )
        self.view: View

    async def callback(self, i: Interaction):
        pool: asyncpg.Pool = i.client.pool  # type: ignore

        data_list = await pool.fetchval(
            "SELECT item_list FROM weapon_notification WHERE user_id = $1", i.user.id
        )
        weapon_list: List[str] = data_list
        for weapon_id in self.values:
            if weapon_id in weapon_list:
                weapon_list.remove(weapon_id)
            else:
                weapon_list.append(weapon_id)

        await pool.execute(
            "UPDATE weapon_notification SET item_list = $1 WHERE user_id = $2",
            weapon_list,
            i.user.id,
        )
        await i.response.edit_message(view=self.view)
        await ReminderMenu.return_weapon_notification(i, self.view)  # type: ignore
