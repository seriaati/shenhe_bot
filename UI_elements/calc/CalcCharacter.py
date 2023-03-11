from typing import List
from apps.draw.utility import image_gen_transition
from apps.enka_api_docs.get_data import get_character_skill_order
from data.game.upgrade_exp import get_exp_table
from exceptions import InvalidWeaponCalcInput

from discord import ButtonStyle, File, Interaction, Locale, SelectOption, utils
from discord.ui import Button, Select, TextInput
from apps.draw import main_funcs
import asset
import config
from ambr.client import AmbrTopAPI
from ambr.models import Character, CharacterDetail, CharacterTalentType, Material
from apps.genshin.checks import check_cookie_predicate
from apps.genshin.custom_model import DrawInput, InitLevels, TodoList
from apps.genshin.utils import (
    get_character_emoji,
    get_character_suggested_talent_levels,
    get_shenhe_account,
    get_uid,
    level_to_ascension_phase,
)
from apps.text_map.convert_locale import to_ambr_top
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from data.game.elements import get_element_color, get_element_emoji, get_element_list
from UI_base_models import BaseModal, BaseView
from UI_elements.calc import AddToTodo
from utility.utils import DefaultEmbed, get_user_appearance_mode


class View(BaseView):
    def __init__(self):
        super().__init__(timeout=config.short_timeout)
        elements = get_element_list()
        for index, element in enumerate(elements):
            self.add_item(
                ElementButton(element, get_element_emoji(element), index // 4)
            )


class ElementButton(Button):
    def __init__(self, element: str, emoji: str, row: int):
        super().__init__(emoji=emoji, row=row)
        self.element = element

    async def callback(self, i: Interaction):
        self.view: View
        locale = await get_user_locale(i.user.id, i.client.pool) or i.locale
        ambr = AmbrTopAPI(i.client.session, to_ambr_top(locale))
        characters = await ambr.get_character()
        if not isinstance(characters, List):
            raise TypeError("characters is not a list")
        options: List[SelectOption] = []
        for character in characters:
            if character.element == self.element:
                options.append(
                    SelectOption(
                        label=character.name,
                        value=character.id,
                        emoji=get_character_emoji(character.id),
                    )
                )
        self.view.clear_items()
        self.view.add_item(CharacterSelect(options, text_map.get(157, locale)))
        await i.response.edit_message(view=self.view)


class CharacterSelect(Select):
    def __init__(self, options: List[SelectOption], placeholder: str):
        super().__init__(options=options, placeholder=placeholder)

    async def callback(self, i: Interaction):
        self.view: View
        locale = await get_user_locale(i.user.id, i.client.pool) or i.locale
        embed = DefaultEmbed().set_author(
            name=text_map.get(608, locale), icon_url=asset.loader
        )
        await i.response.edit_message(embed=embed, view=None)

        # character level, a/q/e level, ascention level
        init_levels = InitLevels()

        # get genshin calculator levels or enka talent levels
        try:
            await check_cookie_predicate(i)
        except Exception:
            pass
        else:
            character_id = int(self.values[0].split("-")[0])
            shenhe_user = await get_shenhe_account(i.user.id, i.client)

            calculator_characters = await shenhe_user.client.get_calculator_characters(
                sync=True
            )
            calculator_character = utils.get(calculator_characters, id=character_id)

            if calculator_character:
                init_levels.level = calculator_character.level

            try:
                character = await shenhe_user.client.get_character_details(character_id)
            except Exception:
                pass
            else:
                skill_order = await get_character_skill_order(str(character_id))

                if skill_order:
                    skill_a = utils.get(character.talents, id=skill_order[0])
                    init_levels.a_level = skill_a.level if skill_a else None
                    skill_e = utils.get(character.talents, id=skill_order[1])
                    init_levels.e_level = skill_e.level if skill_e else None
                    skill_q = utils.get(character.talents, id=skill_order[2])
                    init_levels.q_level = skill_q.level if skill_q else None

        # change None levels in init_levels to 1
        for key, value in init_levels.dict().items():
            if value is None:
                if key == "ascension_phase":
                    setattr(
                        init_levels,
                        key,
                        level_to_ascension_phase(init_levels.level or 1),
                    )
                else:
                    setattr(init_levels, key, 1)

        modal = InitLevelModal(self.values[0], locale, init_levels)
        self.view.clear_items()
        self.view.add_item(SpawnInitModal(locale, modal))
        await i.edit_original_response(embed=None, view=self.view)


class SpawnTargetLevelModal(Button):
    def __init__(
        self,
        locale: Locale | str,
        character_id: str,
        init_levels: List[int],
        suggested_levels: List[int],
    ):
        super().__init__(label=text_map.get(17, locale), style=ButtonStyle.blurple)
        self.locale = locale
        self.character_id = character_id
        self.init_levels = init_levels
        self.suggested_levels = suggested_levels

    async def callback(self, i: Interaction):
        await i.response.send_modal(
            TargetLevelModal(
                self.character_id, self.locale, self.init_levels, self.suggested_levels
            )
        )


class InitLevelModal(BaseModal):
    init = TextInput(
        label="level_init",
        default="1",
        min_length=1,
        max_length=2,
    )

    ascension_phase = TextInput(
        label="ascension_phase",
        min_length=1,
        max_length=1,
    )

    a = TextInput(
        label="attack_init",
        default="1",
        min_length=1,
        max_length=2,
    )

    e = TextInput(
        label="skill_init",
        default="1",
        min_length=1,
        max_length=2,
    )

    q = TextInput(
        label="burst_init",
        default="1",
        min_length=1,
        max_length=2,
    )

    def __init__(
        self, character_id: str, locale: Locale | str, init_levels: InitLevels
    ) -> None:
        super().__init__(
            title=text_map.get(181, locale),
            timeout=config.mid_timeout,
        )
        level_type = text_map.get(168, locale)

        self.init.label = text_map.get(169, locale).format(level_type=level_type)
        self.init.placeholder = text_map.get(170, locale).format(a=1)

        self.ascension_phase.label = text_map.get(720, locale)
        self.ascension_phase.placeholder = text_map.get(170, locale).format(a=4)

        self.a.label = text_map.get(171, locale).format(level_type=level_type)
        self.a.placeholder = text_map.get(170, locale).format(a=9)

        self.e.label = text_map.get(173, locale).format(level_type=level_type)
        self.e.placeholder = text_map.get(170, locale).format(a=8)

        self.q.label = text_map.get(174, locale).format(level_type=level_type)
        self.q.placeholder = text_map.get(170, locale).format(a=10)

        # fill in defaults
        for index, level in enumerate(init_levels.dict().values()):
            if index == 0:
                self.init.default = str(level)
            elif index == 1:
                self.a.default = str(level)
            elif index == 2:
                self.e.default = str(level)
            elif index == 3:
                self.q.default = str(level)
            elif index == 4:
                self.ascension_phase.default = str(level)

        self.character_id = character_id
        self.locale = locale

    async def on_submit(self, i: Interaction):
        await i.response.defer()
        # validate input
        try:
            await validate_level_input(
                self.init.value,
                self.a.value,
                self.e.value,
                self.q.value,
                self.ascension_phase.value,
                i,
                self.locale,
            )
        except InvalidWeaponCalcInput:
            return

        suggested_levlels = await get_character_suggested_talent_levels(
            self.character_id, i.client.session
        )
        view = View()
        view.author = i.user
        view.clear_items()
        view.add_item(
            SpawnTargetLevelModal(
                self.locale,
                self.character_id,
                [
                    int(self.init.value),
                    int(self.a.value),
                    int(self.e.value),
                    int(self.q.value),
                    int(self.ascension_phase.value),
                ],
                suggested_levlels,
            )
        )
        embed = DefaultEmbed()
        embed.set_author(
            name=text_map.get(18, self.locale), icon_url=i.user.display_avatar.url
        )
        await i.edit_original_response(embed=embed, view=view)
        view.message = await i.original_response()


class SpawnInitModal(Button):
    def __init__(self, locale: Locale | str, modal: InitLevelModal):
        super().__init__(label=text_map.get(17, locale), style=ButtonStyle.blurple)
        self.modal = modal

    async def callback(self, i: Interaction):
        await i.response.send_modal(self.modal)


class TargetLevelModal(BaseModal):
    target = TextInput(
        label="level_target",
        min_length=1,
        max_length=2,
    )

    ascension_target = TextInput(
        label="ascension_target",
        min_length=1,
        max_length=1,
    )

    a = TextInput(
        label="attack_target",
        min_length=1,
        max_length=2,
    )

    e = TextInput(
        label="skill_target",
        min_length=1,
        max_length=2,
    )

    q = TextInput(
        label="burst_target",
        min_length=1,
        max_length=2,
    )

    def __init__(
        self,
        character_id: str,
        locale: Locale | str,
        init_levels: List[int],
        suggested_levels: List[int],
    ) -> None:
        super().__init__(
            title=text_map.get(181, locale),
            timeout=config.mid_timeout,
        )
        level_type = text_map.get(182, locale)

        self.target.label = text_map.get(169, locale).format(level_type=level_type)
        self.target.placeholder = text_map.get(170, locale).format(a=90)
        self.target.default = str(init_levels[0])

        self.ascension_target.label = text_map.get(721, locale)
        self.ascension_target.placeholder = text_map.get(170, locale).format(a=4)
        self.ascension_target.default = str(init_levels[4])

        self.a.label = text_map.get(171, locale).format(level_type=level_type)
        self.a.placeholder = text_map.get(170, locale).format(a=9)
        self.a.default = (
            str(init_levels[1])
            if init_levels[1] > suggested_levels[0]
            else str(suggested_levels[0])
        )

        self.e.label = text_map.get(173, locale).format(level_type=level_type)
        self.e.placeholder = text_map.get(170, locale).format(a=4)
        self.e.default = (
            str(init_levels[2])
            if init_levels[2] > suggested_levels[1]
            else str(suggested_levels[1])
        )

        self.q.label = text_map.get(174, locale).format(level_type=level_type)
        self.q.placeholder = text_map.get(170, locale).format(a=10)
        self.q.default = (
            str(init_levels[3])
            if init_levels[3] > suggested_levels[2]
            else str(suggested_levels[2])
        )

        self.character_id = character_id
        self.init_levels = init_levels
        self.locale = locale

    async def on_submit(self, i: Interaction) -> None:
        await i.response.defer()
        # validate input
        try:
            await validate_level_input(
                self.target.value,
                self.a.value,
                self.e.value,
                self.q.value,
                self.ascension_target.value,
                i,
                self.locale,
            )
        except InvalidWeaponCalcInput:
            return

        view = None
        if i.message is not None:
            view = View.from_message(i.message)
        if view is None:
            await i.edit_original_response(
                embed=DefaultEmbed().set_author(
                    name=text_map.get(644, self.locale), icon_url=asset.loader
                ),
                view=None,
            )
        else:
            await image_gen_transition(i, view, self.locale)

        target = int(self.target.value)
        ascension = int(self.ascension_target.value)
        a = int(self.a.value)
        e = int(self.e.value)
        q = int(self.q.value)

        init = self.init_levels[0]
        init_a = self.init_levels[1]
        init_e = self.init_levels[2]
        init_q = self.init_levels[3]
        init_ascension = self.init_levels[4]

        ambr = AmbrTopAPI(i.client.session, to_ambr_top(self.locale))
        character = await ambr.get_character_detail(self.character_id)
        if not isinstance(character, CharacterDetail):
            raise TypeError("character is not a Character")

        todo_list = TodoList()

        # ascension items
        for asc in character.upgrade.ascensions:
            if init_ascension < asc.ascension_level <= ascension:
                if asc.cost_items is not None:
                    for item in asc.cost_items:
                        todo_list.add_item({int(item[0].id): item[1]})
                if asc.mora_cost is not None:
                    todo_list.add_item({202: asc.mora_cost})

        # talent upgrade items
        normal_attack = character.talents[0]
        elemental_skill = character.talents[1]
        elemental_burst = [
            t
            for t in character.talents
            if t.type is CharacterTalentType.ELEMENTAL_BURST
        ][0]

        talents = [
            normal_attack.upgrades,
            elemental_skill.upgrades,
            elemental_burst.upgrades,
        ]

        for index, talent in enumerate(talents):
            if talent is not None:
                if index == 0:
                    t_init = init_a
                    t_target = a
                elif index == 1:
                    t_init = init_e
                    t_target = e
                else:  # index == 2
                    t_init = init_q
                    t_target = q
                for t in talent:
                    if t_init < t.level <= t_target:
                        if t.cost_items is not None:
                            for item in t.cost_items:
                                todo_list.add_item({int(item[0].id): item[1]})
                        if t.mora_cost is not None:
                            todo_list.add_item({202: t.mora_cost})

        # level up items
        exp_table = get_exp_table()
        init_cumulative = 0
        target_cumulative = 0
        for key, value in exp_table.items():
            if key < init:
                init_cumulative += value["next_level"]
            if key < target:
                target_cumulative += value["next_level"]
        total_exp = target_cumulative - init_cumulative

        # hero
        hero_num = total_exp // 20000
        todo_list.add_item({104003: hero_num})
        todo_list.add_item({202: hero_num * 4000})

        # adventurer
        adv_num = (total_exp - 20000 * hero_num) // 5000
        todo_list.add_item({104002: adv_num})
        todo_list.add_item({202: adv_num * 1000})

        # wanderer
        wand_num = (total_exp - 20000 * hero_num - 5000 * adv_num) // 1000
        todo_list.add_item({104001: wand_num})
        todo_list.add_item({202: wand_num * 200})

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
                embed=DefaultEmbed().set_author(
                    name=text_map.get(197, self.locale),
                    icon_url=i.user.display_avatar.url,
                )
            )
            return

        character = await ambr.get_character(self.character_id)
        if not isinstance(character, Character):
            raise TypeError("character is not a Character")
        fp = await main_funcs.draw_material_card(
            DrawInput(
                loop=i.client.loop,
                session=i.client.session,
                locale=self.locale,
                dark_mode=await get_user_appearance_mode(i.user.id, i.client.pool),
            ),
            all_materials,
            "",
            background_color=get_element_color(character.element),
            draw_title=False,
        )
        fp.seek(0)
        embed = DefaultEmbed()
        embed.add_field(
            name=text_map.get(192, self.locale),
            value=f"{text_map.get(183, self.locale)}: {init} ▸ {target}\n"
            f"{text_map.get(722, self.locale)}: {init_ascension} ▸ {ascension}\n"
            f"{normal_attack.name}: {init_a} ▸ {a}\n"
            f"{elemental_skill.name}: {init_e} ▸ {e}\n"
            f"{elemental_burst.name}: {init_q} ▸ {q}",
        )
        embed.set_author(icon_url=character.icon, name=character.name)
        embed.set_image(url="attachment://materials.jpeg")
        view = View()
        view.clear_items()
        view.add_item(AddToTodo.AddToTodo(items, self.locale))
        view.author = i.user
        await i.edit_original_response(
            embed=embed, attachments=[File(fp, "materials.jpeg")], view=view
        )
        view.message = await i.original_response()


async def validate_level_input(
    level: str,
    a: str,
    e: str,
    q: str,
    ascension: str,
    i: Interaction,
    locale: Locale | str,
):
    embed = DefaultEmbed().set_author(
        name=text_map.get(190, locale), icon_url=i.user.display_avatar.url
    )
    try:
        int_level = int(level)
        int_a = int(a)
        int_e = int(e)
        int_q = int(q)
        int_ascension = int(ascension)
    except ValueError:
        embed.description = text_map.get(187, locale)
        await i.followup.send(
            embed=embed,
            ephemeral=True,
        )
        raise InvalidWeaponCalcInput

    if int_level < 1 or int_level > 90:
        embed.description = text_map.get(172, locale).format(a=1, b=90)
        await i.followup.send(
            embed=embed,
            ephemeral=True,
        )
        raise InvalidWeaponCalcInput

    if int_a < 1 or int_a > 15 or int_e < 1 or int_e > 15 or int_q < 1 or int_q > 15:
        embed.description = text_map.get(172, locale).format(a=1, b=15)
        await i.followup.send(
            embed=embed,
            ephemeral=True,
        )
        raise InvalidWeaponCalcInput

    theoretical_ascension = level_to_ascension_phase(int_level)
    if int_ascension not in (theoretical_ascension, theoretical_ascension - 1):
        embed.description = text_map.get(730, locale)
        await i.followup.send(
            embed=embed,
            ephemeral=True,
        )
        raise InvalidWeaponCalcInput
