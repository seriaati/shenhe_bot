from typing import Any, Dict, List

from discord import File, Interaction, Locale, SelectOption
from discord.ui import Button, Select, TextInput

import asset
import config
from ambr.client import AmbrTopAPI
from ambr.models import Material, Weapon, WeaponDetail
from apps.genshin.custom_model import TodoList
from apps.genshin.utils import get_weapon_emoji, level_to_ascension_phase
from apps.text_map.convert_locale import to_ambr_top
from apps.text_map.text_map_app import text_map
from data.game.weapon_types import get_weapon_type_emoji
from UI_base_models import BaseModal, BaseView
from UI_elements.calc import AddToTodo
from utility.utils import (
    default_embed,
    divide_chunks,
    error_embed,
    get_user_appearance_mode,
)
from yelan.draw import draw_big_material_card


class View(BaseView):
    def __init__(self, locale: Locale | str, weapon_types: Dict[str, str]):
        super().__init__(timeout=config.short_timeout)
        self.locale = locale
        for weapon_type_id, weapon_type in weapon_types.items():
            self.add_item(
                WeaponTypeButton(
                    get_weapon_type_emoji(weapon_type_id), weapon_type, weapon_type_id
                )
            )


class WeaponTypeButton(Button):
    def __init__(self, emoji: str, label: str, weapon_type: str):
        super().__init__(emoji=emoji, label=label)
        self.weapon_type = weapon_type

    async def callback(self, i: Interaction):
        self.view: View
        ambr = AmbrTopAPI(i.client.session, to_ambr_top(self.view.locale))
        weapons = await ambr.get_weapon()
        if not isinstance(weapons, List):
            raise TypeError("weapons is not a list")
        options = []
        for weapon in weapons:
            if weapon.type == self.weapon_type:
                options.append(
                    SelectOption(
                        label=weapon.name,
                        value=str(weapon.id),
                        emoji=get_weapon_emoji(weapon.id),
                    )
                )
        options = list(divide_chunks(options, 25))
        self.view.clear_items()
        count = 1
        for option in options:
            self.view.add_item(WeaponSelect(self.view.locale, option, f" ({count}~{count+len(option)-1})"))
            count += len(option)
        await i.response.edit_message(view=self.view)


class WeaponSelect(Select):
    def __init__(self, locale: Locale | str, options: List[SelectOption], range: str):
        super().__init__(placeholder=text_map.get(180, locale)+range, options=options)

    async def callback(self, i: Interaction) -> Any:
        self.view: View
        await i.response.send_modal(LevelModal(self.values[0], self.view.locale))


class LevelModal(BaseModal):
    current = TextInput(label="current_level", default="1", min_length=1, max_length=2)
    target = TextInput(
        label="target_level", placeholder="like: 90", min_length=1, max_length=2
    )

    def __init__(self, weapon_id: str, locale: Locale | str) -> None:
        super().__init__(
            title=text_map.get(181, locale),
            timeout=config.mid_timeout,
        )
        self.current.label = text_map.get(185, locale).format(
            level_type=text_map.get(168, locale)
        )
        self.target.label = text_map.get(185, locale).format(
            level_type=text_map.get(182, locale)
        )
        self.target.placeholder = text_map.get(170, locale).format(a=90)
        self.weapon_id = weapon_id
        self.locale = locale

    async def on_submit(self, i: Interaction) -> None:
        await i.response.defer()
        locale = self.locale

        # validate input
        try:
            current = int(self.current.value)
            target = int(self.target.value)
        except ValueError:
            await i.followup.send(
                embed=error_embed(message=text_map.get(187, locale)).set_author(
                    name=text_map.get(190, locale), icon_url=i.user.display_avatar.url
                ),
                ephemeral=True,
            )
            return

        if current < 1 or current > 90 or target < 1 or target > 90:
            await i.followup.send(
                embed=error_embed(
                    message=text_map.get(172, locale).format(a=1, b=90)
                ).set_author(
                    name=text_map.get(190, locale), icon_url=i.user.display_avatar.url
                ),
                ephemeral=True,
            )
            return

        await i.edit_original_response(
            embed=default_embed().set_author(
                name=text_map.get(644, self.locale), icon_url=asset.loader
            ),
            view=None,
        )

        ambr = AmbrTopAPI(i.client.session, to_ambr_top(self.locale))
        weapon = await ambr.get_weapon_detail(int(self.weapon_id))
        if not isinstance(weapon, WeaponDetail):
            raise TypeError("weapon is not a WeaponDetail")

        todo_list = TodoList()

        # ascension materials
        init_phase = level_to_ascension_phase(current)
        target_phase = level_to_ascension_phase(target)
        all_materials = []
        weapon_ascensions = weapon.upgrade.ascensions[init_phase:target_phase]
        for ascension in weapon_ascensions:
            cost_items = ascension.cost_items
            if cost_items is not None:
                for item in cost_items:
                    todo_list.add_item({int(item[0].id): item[1]})
            mora_cost = ascension.mora_cost
            if mora_cost is not None:
                todo_list.add_item({202: mora_cost})

        items = todo_list.return_list()
        items = dict(sorted(items.items(), key=lambda x: x[0], reverse=True))
        all_materials = []

        for key, value in items.items():
            material = await ambr.get_material(key)
            if not isinstance(material, Material):
                raise TypeError("material is not a Material")
            all_materials.append((material, value))

        if not all_materials:
            await i.edit_original_response(
                embed=default_embed().set_author(
                    name=text_map.get(197, self.locale),
                    icon_url=i.user.display_avatar.url,
                )
            )
            return

        weapon = await ambr.get_weapon(int(self.weapon_id))
        if not isinstance(weapon, Weapon):
            raise TypeError("weapon is not a Weapon")
        fp = await draw_big_material_card(
            all_materials,
            f"{weapon.name}: {text_map.get(191, self.locale)}",
            "#C5EDFF",
            i.client.session,
            await get_user_appearance_mode(i.user.id, i.client.db),
            self.locale,
        )
        fp.seek(0)
        embed = default_embed()
        embed.add_field(
            name=text_map.get(192, self.locale),
            value=f"{text_map.get(183, self.locale)}: {current} ▸ {target}\n",
        )
        embed.set_author(url=weapon.icon, name=weapon.name)
        embed.set_image(url="attachment://materials.jpeg")
        view = BaseView(timeout=config.mid_timeout)
        view.clear_items()
        view.add_item(AddToTodo.AddToTodo(items, self.locale))
        view.author = i.user
        await i.edit_original_response(
            embed=embed, attachments=[File(fp, "materials.jpeg")], view=view
        )
        view.message = await i.original_response()
