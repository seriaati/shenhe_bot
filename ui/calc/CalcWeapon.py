import typing

import discord
from discord import ui

import dev.asset as asset
import dev.config as config
import dev.models as models
from ambr import AmbrTopAPI, Material, WeaponDetail
from apps.db import get_user_theme
from apps.draw import main_funcs
from apps.draw.utility import image_gen_transition
from apps.genshin import get_weapon_emoji, level_to_ascension_phase
from apps.text_map import text_map, to_ambr_top
from data.game.weapon_exp import get_weapon_exp_table
from data.game.weapon_types import get_weapon_type_emoji
from dev.base_ui import BaseModal, BaseView
from dev.exceptions import InvalidAscensionInput, InvalidWeaponCalcInput
from ui.calc.AddToTodo import AddButton
from utility import divide_chunks


class View(BaseView):
    def __init__(
        self, locale: discord.Locale | str, weapon_types: typing.Dict[str, str]
    ):
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


class WeaponTypeButton(ui.Button):
    def __init__(self, emoji: str, label: str, weapon_type: str, row: int):
        super().__init__(emoji=emoji, label=label, row=row)
        self.weapon_type = weapon_type
        self.view: View

    async def callback(self, i: models.Inter):
        ambr = AmbrTopAPI(i.client.session, to_ambr_top(self.view.locale))
        weapons = await ambr.get_weapon()
        if not isinstance(weapons, typing.List):
            raise TypeError("weapons is not a list")
        options = []
        for weapon in weapons:
            if weapon.type == self.weapon_type:
                options.append(
                    discord.SelectOption(
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


class WeaponSelect(ui.Select):
    def __init__(
        self,
        locale: discord.Locale | str,
        options: typing.List[discord.SelectOption],
        range_: str,
    ):
        super().__init__(
            placeholder=text_map.get(180, locale) + range_, options=options
        )
        self.view: View

    async def callback(self, i: models.Inter) -> typing.Any:
        await i.response.send_modal(LevelModal(self.values[0], self.view.locale))


class LevelModal(BaseModal):
    current = ui.TextInput(
        label="current_level", default="1", min_length=1, max_length=2
    )
    current_ascension = ui.TextInput(
        label="current_ascension", default="0", min_length=1, max_length=1
    )
    target = ui.TextInput(
        label="target_level", default="90", min_length=1, max_length=2
    )
    target_ascension = ui.TextInput(
        label="target_ascension", min_length=1, max_length=1, default="6"
    )

    def __init__(self, weapon_id: str, locale: discord.Locale | str) -> None:
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

    async def on_submit(self, i: models.Inter) -> None:
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
                embed=models.ErrorEmbed(
                    description=text_map.get(187, locale)
                ).set_author(
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
            if current_ascension not in (t_ascension, t_ascension - 1):
                raise InvalidAscensionInput

            t_ascension = level_to_ascension_phase(target)
            if target_ascension not in (t_ascension, t_ascension - 1):
                raise InvalidAscensionInput

            if current_ascension > target_ascension:
                raise InvalidAscensionInput

            if current < 1:
                raise InvalidWeaponCalcInput
            if current > target:
                raise InvalidWeaponCalcInput

        except InvalidWeaponCalcInput:
            embed = models.ErrorEmbed(
                description=text_map.get(172, locale).format(a=a, b=b)
            )
            embed.set_author(
                name=text_map.get(190, locale), icon_url=i.user.display_avatar.url
            )
            return await i.followup.send(
                embed=embed,
                ephemeral=True,
            )
        except InvalidAscensionInput:
            embed = models.ErrorEmbed(description=text_map.get(730, locale))
            embed.set_author(
                name=text_map.get(190, locale), icon_url=i.user.display_avatar.url
            )
            return await i.followup.send(embed=embed, ephemeral=True)

        view = None
        if i.message is not None:
            view = View.from_message(i.message)
        if view is None:
            await i.edit_original_response(
                embed=models.DefaultEmbed().set_author(
                    name=text_map.get(644, self.locale), icon_url=asset.loader
                ),
                view=None,
            )
        else:
            await image_gen_transition(i, view, self.locale)

        todo_list = models.TodoList()

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
                embed=models.DefaultEmbed().set_author(
                    name=text_map.get(197, self.locale),
                    icon_url=i.user.display_avatar.url,
                )
            )
            return

        fp = await main_funcs.draw_material_card(
            models.DrawInput(
                loop=i.client.loop,
                session=i.client.session,
                locale=self.locale,
                dark_mode=await get_user_theme(i.user.id, i.client.pool),
            ),
            all_materials,
            "",
            False,
        )
        fp.seek(0)

        embed = models.DefaultEmbed()
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
        view.add_item(AddButton(items, self.locale))
        view.author = i.user

        await i.edit_original_response(
            embed=embed, attachments=[discord.File(fp, "materials.jpeg")], view=view
        )
        view.message = await i.original_response()
