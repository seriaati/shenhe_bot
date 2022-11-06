import ast
from typing import List
from UI_base_models import BaseView
from ambr.client import AmbrTopAPI
from apps.genshin.utils import get_weapon
from apps.text_map.convert_locale import to_ambr_top
import config
from discord.ui import Button, Select
from discord import SelectOption, Interaction, Locale
from data.game.weapon_types import weapon_emoji_map, weapon_text_map
from apps.text_map.text_map_app import text_map
from UI_elements.genshin import ReminderMenu
from utility.utils import divide_chunks


class View(BaseView):
    def __init__(self, locale: Locale | str):
        super().__init__(timeout=config.mid_timeout)
        self.locale = locale
        for weapon_type, emoji in weapon_emoji_map.items():
            self.add_item(
                WeaponTypeButton(
                    emoji,
                    text_map.get(weapon_text_map[weapon_type], locale).capitalize(),
                    weapon_type,
                )
            )
        self.add_item(GOBackReminder())


class GOBackReminder(Button):
    def __init__(self):
        super().__init__(emoji="<:left:982588994778972171>", row=2)

    async def callback(self, i: Interaction):
        await ReminderMenu.return_weapon_notification(i, self.view)


class GOBack(Button):
    def __init__(self):
        super().__init__(emoji="<:left:982588994778972171>", row=2)

    async def callback(self, i: Interaction):
        self.view: View
        self.view.clear_items()

        for weapon_type, emoji in weapon_emoji_map.items():
            self.view.add_item(
                WeaponTypeButton(
                    emoji,
                    text_map.get(weapon_text_map[weapon_type], self.view.locale),
                    weapon_type,
                )
            )
        self.view.add_item(GOBackReminder())
        await i.response.edit_message(view=self.view)


class WeaponTypeButton(Button):
    def __init__(self, emoji: str, label: str, weapon_type: str):
        super().__init__(emoji=emoji, label=label)
        self.weapon_type = weapon_type

    async def callback(self, i: Interaction):
        self.view: View
        async with i.client.db.execute(
            "SELECT weapon_list FROM weapon_notification WHERE user_id = ?",
            (i.user.id,),
        ) as c:
            weapon_list = await c.fetchone()
        weapon_list: List[str] = ast.literal_eval(weapon_list[0])
        select_options = []
        ambr = AmbrTopAPI(i.client.session)
        weapons = await ambr.get_weapon()
        weapon_types = await ambr.get_weapon_types()
        if not isinstance(weapons, List):
            raise TypeError("weapons is not a list")
        for weapon in weapons:
            if weapon_types.get(weapon.type) == self.weapon_type:
                description = (
                    text_map.get(638, self.view.locale)
                    if str(weapon.id) in weapon_list
                    else None
                )
                select_options.append(
                    SelectOption(
                        emoji=get_weapon(weapon.id)["emoji"],
                        label=text_map.get_weapon_name(weapon.id, self.view.locale),
                        value=weapon.id,
                        description=description,
                    )
                )
        self.view.clear_items()
        self.view.add_item(GOBack())
        select_options = list(divide_chunks(select_options, 25))
        count = 1
        for options in select_options:
            self.view.add_item(
                WeaponSelect(options, f"{text_map.get(180, self.view.locale)} ({count}~{count+len(options)-1})")
            )
            count += len(options)
        await i.response.edit_message(view=self.view)


class WeaponSelect(Select):
    def __init__(self, options: List[SelectOption], placeholder: str):
        super().__init__(options=options, placeholder=placeholder, max_values=len(options))

    async def callback(self, i: Interaction):
        self.view: View
        async with i.client.db.execute(
            "SELECT weapon_list FROM weapon_notification WHERE user_id = ?",
            (i.user.id,),
        ) as c:
            (weapon_list,) = await c.fetchone()
        weapon_list: List[str] = ast.literal_eval(weapon_list)
        for weapon_id in self.values:
            if weapon_id in weapon_list:
                weapon_list.remove(weapon_id)
            else:
                weapon_list.append(weapon_id)
        await i.client.db.execute(
            "UPDATE weapon_notification SET weapon_list = ? WHERE user_id = ?",
            (str(weapon_list), i.user.id),
        )
        await i.client.db.commit()
        await i.response.edit_message(view=self.view)
        await ReminderMenu.return_weapon_notification(i, self.view)
