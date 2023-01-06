from typing import Any, Dict, List
from apps.draw.utility import image_gen_transition
from data.game.weapon_exp import get_weapon_exp_table

from discord import File, Interaction, Locale, SelectOption
from discord.ui import Button, Select, TextInput

import asset
import config
from ambr.client import AmbrTopAPI
from ambr.models import Material, WeaponDetail
from apps.genshin.custom_model import DrawInput, TodoList
from apps.genshin.utils import get_weapon_emoji, level_to_ascension_phase
from apps.text_map.convert_locale import to_ambr_top
from apps.text_map.text_map_app import text_map
from data.game.weapon_types import get_weapon_type_emoji
from UI_base_models import BaseModal, BaseView
from UI_elements.calc import AddToTodo
from exceptions import InvalidAscensionInput, InvalidWeaponCalcInput
from utility.utils import (
    default_embed,
    divide_chunks,
    error_embed,
    get_user_appearance_mode,
)
from apps.draw import main_funcs


class View(BaseView):
    def __init__(self, locale: Locale | str, weapon_types: Dict[str, str]):
        super().__init__(timeout=config.short_timeout)
        self.locale = locale

        count = 1
        for weapon_type_id, weapon_type in weapon_types.items():
            self.add_item(
                WeaponTypeButton(
                    get_weapon_type_emoji(weapon_type_id),
                    weapon_type,
                    weapon_type_id,
                    count // 3,
                )
            )
            count += 1


class WeaponTypeButton(Button):
    def __init__(self, emoji: str, label: str, weapon_type: str, row: int):
        super().__init__(emoji=emoji, label=label, row=row)
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
            self.view.add_item(
                WeaponSelect(
                    self.view.locale, option, f" ({count}~{count+len(option)-1})"
                )
            )
            count += len(option)
        await i.response.edit_message(view=self.view)


class WeaponSelect(Select):
    def __init__(self, locale: Locale | str, options: List[SelectOption], range: str):
        super().__init__(placeholder=text_map.get(180, locale) + range, options=options)

    async def callback(self, i: Interaction) -> Any:
        self.view: View
        await i.response.send_modal(LevelModal(self.values[0], self.view.locale))


class LevelModal(BaseModal):
    current = TextInput(label="current_level", default="1", min_length=1, max_length=2)
    current_ascension = TextInput(
        label="current_ascension", default="0", min_length=1, max_length=1
    )
    target = TextInput(label="target_level", default="90", min_length=1, max_length=2)
    target_ascension = TextInput(
        label="target_ascension", min_length=1, max_length=1, default="6"
    )

    def __init__(self, weapon_id: str, locale: Locale | str) -> None:
        super().__init__(
            title=text_map.get(181, locale),
            timeout=config.mid_timeout,
        )

        self.current.label = text_map.get(185, locale).format(
            level_type=text_map.get(168, locale)
        )
        self.current.placeholder = text_map.get(170, locale).format(a=1)

        self.current_ascension.label = text_map.get(720, locale)
        self.current_ascension.placeholder = text_map.get(170, locale).format(a=0)

        self.target.label = text_map.get(185, locale).format(
            level_type=text_map.get(182, locale)
        )
        self.target.placeholder = text_map.get(170, locale).format(a=90)

        self.target_ascension.label = text_map.get(721, locale)
        self.target_ascension.placeholder = text_map.get(170, locale).format(a=6)

        self.weapon_id = weapon_id
        self.locale = locale

    async def on_submit(self, i: Interaction) -> None:
        await i.response.defer()
        locale = self.locale

        # validate input
        try:
            current = int(self.current.value)
            target = int(self.target.value)
            current_ascension = int(self.current_ascension.value)
            target_ascension = int(self.target_ascension.value)
        except ValueError:
            return await i.followup.send(
                embed=error_embed(message=text_map.get(187, locale)).set_author(
                    name=text_map.get(190, locale), icon_url=i.user.display_avatar.url
                ),
                ephemeral=True,
            )

        ambr = AmbrTopAPI(i.client.session, to_ambr_top(self.locale))
        weapon = await ambr.get_weapon_detail(int(self.weapon_id))
        if not isinstance(weapon, WeaponDetail):
            raise TypeError("weapon is not a WeaponDetail")

        a = 1
        if weapon.rarity in [1, 2]:
            b = 70
        else:
            b = 90

        try:
            if current > target:
                raise InvalidWeaponCalcInput

            if weapon.rarity in [1, 2]:
                if current > 70 or target > 70:
                    raise InvalidWeaponCalcInput
            else:
                if current > 90 or target > 90:
                    raise InvalidWeaponCalcInput

            t_ascension = level_to_ascension_phase(current)
            if (
                current_ascension != t_ascension
                and current_ascension != t_ascension - 1
            ):
                raise InvalidAscensionInput

            t_ascension = level_to_ascension_phase(target)
            if target_ascension != t_ascension and target_ascension != t_ascension - 1:
                raise InvalidAscensionInput

            if current_ascension > target_ascension:
                raise InvalidAscensionInput

            if current < 1:
                raise InvalidWeaponCalcInput
            if current > target:
                raise InvalidWeaponCalcInput

        except InvalidWeaponCalcInput:
            embed = error_embed(message=text_map.get(172, locale).format(a=a, b=b))
            embed.set_author(
                name=text_map.get(190, locale), icon_url=i.user.display_avatar.url
            )
            return await i.followup.send(
                embed=embed,
                ephemeral=True,
            )
        except InvalidAscensionInput:
            embed = error_embed(message=text_map.get(730, locale))
            embed.set_author(
                name=text_map.get(190, locale), icon_url=i.user.display_avatar.url
            )
            return await i.followup.send(embed=embed, ephemeral=True)

        view = None
        if i.message is not None:
            view = View.from_message(i.message)
        if view is None:
            await i.edit_original_response(
                embed=default_embed().set_author(
                    name=text_map.get(644, self.locale), icon_url=asset.loader
                ),
                view=None,
            )
        else:
            await image_gen_transition(i, view, self.locale)

        todo_list = TodoList()

        # ascension materials
        weapon_ascensions = weapon.upgrade.ascensions
        for asc in weapon_ascensions:
            if current_ascension < asc.ascension_level <= target_ascension:
                if asc.cost_items is not None:
                    for item in asc.cost_items:
                        todo_list.add_item({int(item[0].id): item[1]})

                mora_cost = asc.mora_cost
                if mora_cost is not None:
                    todo_list.add_item({202: mora_cost})

        # level up items
        exp_table = get_weapon_exp_table()
        init_cumulative = 0
        target_cumulative = 0
        exp_table = exp_table[weapon.rarity]
        for key, value in exp_table.items():
            if key < current:
                init_cumulative += value
            if key < target:
                target_cumulative += value
        total_exp = target_cumulative - init_cumulative

        # mystic
        mystic_num = total_exp // 10000
        todo_list.add_item({104013: mystic_num})

        # fine
        fine_num = (total_exp - 10000 * mystic_num) // 2000
        todo_list.add_item({104012: fine_num})

        # normal
        normal_num = (total_exp - 10000 * mystic_num - 2000 * fine_num) // 400
        todo_list.add_item({104011: normal_num})

        # mora
        todo_list.add_item({202: total_exp // 10})

        # sort items
        items = todo_list.return_list()
        items = dict(sorted(items.items(), key=lambda x: x[0], reverse=True))

        all_materials = []
        for key, value in items.items():
            material = await ambr.get_material(key)
            if isinstance(material, Material):
                all_materials.append((material, value))

        if not all_materials:
            await i.edit_original_response(
                embed=default_embed().set_author(
                    name=text_map.get(197, self.locale),
                    icon_url=i.user.display_avatar.url,
                )
            )
            return

        fp = await main_funcs.draw_material_card(
            DrawInput(
                loop=i.client.loop,
                session=i.client.session,
                locale=self.locale,
                dark_mode=await get_user_appearance_mode(i.user.id),
            ),
            all_materials,
            "",
            False,
        )
        fp.seek(0)

        embed = default_embed()
        embed.add_field(
            name=text_map.get(192, self.locale),
            value=f"""
                {text_map.get(200, self.locale)}: {current} ▸ {target}
                {text_map.get(722, self.locale)}: {current_ascension} ▸ {target_ascension}
            """,
        )
        embed.set_author(icon_url=weapon.icon, name=weapon.name)
        embed.set_image(url="attachment://materials.jpeg")

        view = BaseView(timeout=config.mid_timeout)
        view.add_item(AddToTodo.AddToTodo(items, self.locale))
        view.author = i.user

        await i.edit_original_response(
            embed=embed, attachments=[File(fp, "materials.jpeg")], view=view
        )
        view.message = await i.original_response()
