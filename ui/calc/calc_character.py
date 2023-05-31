from typing import List

import attr
import discord
from discord import ui, utils

import ambr.models as ambr_models
import dev.asset as asset
import dev.config as config
import dev.models as models
from ambr import AmbrTopAPI
from apps.db.tables.user_settings import Settings
from apps.draw import main_funcs
from apps.enka.api_docs import get_character_skill_order
from apps.text_map import text_map, to_ambr_top
from data.game.elements import get_element_color, get_element_emoji, get_element_list
from data.game.upgrade_exp import get_exp_table
from dev.base_ui import BaseModal, BaseView
from dev.exceptions import InvalidWeaponCalcInput
from ui.calc.add_to_todo import AddButton
from utils import (
    get_character_emoji,
    get_character_suggested_talent_levels,
    image_gen_transition,
    level_to_ascension_phase,
)


class View(BaseView):
    def __init__(self):
        super().__init__(timeout=config.short_timeout)
        elements = get_element_list()
        for index, element in enumerate(elements):
            self.add_item(
                ElementButton(element, get_element_emoji(element), index // 4)
            )


class ElementButton(ui.Button):
    def __init__(self, element: str, emoji: str, row: int):
        super().__init__(emoji=emoji, row=row)

        self.view: View
        self.element = element

    async def callback(self, i: models.Inter):
        lang = await i.client.db.settings.get(i.user.id, Settings.LANG) or str(i.locale)
        ambr = AmbrTopAPI(i.client.session, to_ambr_top(lang))
        characters = await ambr.get_character()
        if not isinstance(characters, List):
            raise TypeError("characters is not a list")
        options: List[discord.SelectOption] = []
        for character in characters:
            if character.element == self.element:
                options.append(
                    discord.SelectOption(
                        label=character.name,
                        value=character.id,
                        emoji=get_character_emoji(character.id),
                    )
                )
        self.view.clear_items()
        self.view.add_item(CharacterSelect(options, text_map.get(157, lang)))
        await i.response.edit_message(view=self.view)


class CharacterSelect(ui.Select):
    def __init__(self, options: List[discord.SelectOption], placeholder: str):
        super().__init__(options=options, placeholder=placeholder)
        self.view: View

    async def callback(self, i: models.Inter):
        lang = await i.client.db.settings.get(i.user.id, Settings.LANG) or str(i.locale)
        embed = models.DefaultEmbed().set_author(
            name=text_map.get(608, lang), icon_url=asset.loader
        )
        await i.response.edit_message(embed=embed, view=None)

        # character level, a/q/e level, ascention level
        init_levels = models.InitLevels()

        character_id = int(self.values[0].split("-")[0])
        user = await i.client.db.users.get(i.user.id)
        client = await user.client

        calculator_characters = await client.get_calculator_characters(sync=True)
        calculator_character = utils.get(calculator_characters, id=character_id)

        if calculator_character:
            init_levels.level = calculator_character.level

        try:
            character = await client.get_character_details(character_id)
        except Exception:  # skipcq: PYL-W0703
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
        for key, value in attr.asdict(init_levels).items():
            if value is None:
                if key == "ascension_phase":
                    setattr(
                        init_levels,
                        key,
                        level_to_ascension_phase(init_levels.level or 1),
                    )
                else:
                    setattr(init_levels, key, 1)

        modal = InitLevelModal(self.values[0], lang, init_levels)
        self.view.clear_items()
        self.view.add_item(SpawnInitModal(lang, modal))
        await i.edit_original_response(embed=None, view=self.view)


class SpawnTargetLevelModal(ui.Button):
    def __init__(
        self,
        lang: str,
        character_id: str,
        init_levels: List[int],
        suggested_levels: List[int],
    ):
        super().__init__(
            label=text_map.get(17, lang), style=discord.ButtonStyle.blurple
        )
        self.lang = lang
        self.character_id = character_id
        self.init_levels = init_levels
        self.suggested_levels = suggested_levels

    async def callback(self, i: models.Inter):
        await i.response.send_modal(
            TargetLevelModal(
                self.character_id, self.lang, self.init_levels, self.suggested_levels
            )
        )


class InitLevelModal(BaseModal):
    init = ui.TextInput(
        label="level_init",
        default="1",
        min_length=1,
        max_length=2,
    )

    ascension_phase = ui.TextInput(
        label="ascension_phase",
        min_length=1,
        max_length=1,
    )

    a = ui.TextInput(
        label="attack_init",
        default="1",
        min_length=1,
        max_length=2,
    )

    e = ui.TextInput(
        label="skill_init",
        default="1",
        min_length=1,
        max_length=2,
    )

    q = ui.TextInput(
        label="burst_init",
        default="1",
        min_length=1,
        max_length=2,
    )

    def __init__(
        self,
        character_id: str,
        lang: str,
        init_levels: models.InitLevels,
    ) -> None:
        super().__init__(
            title=text_map.get(181, lang),
            timeout=config.mid_timeout,
        )
        level_type = text_map.get(168, lang)

        self.init.label = text_map.get(169, lang).format(level_type=level_type)
        self.init.placeholder = text_map.get(170, lang).format(a=1)

        self.ascension_phase.label = text_map.get(720, lang)
        self.ascension_phase.placeholder = text_map.get(170, lang).format(a=4)

        self.a.label = text_map.get(171, lang).format(level_type=level_type)
        self.a.placeholder = text_map.get(170, lang).format(a=9)

        self.e.label = text_map.get(173, lang).format(level_type=level_type)
        self.e.placeholder = text_map.get(170, lang).format(a=8)

        self.q.label = text_map.get(174, lang).format(level_type=level_type)
        self.q.placeholder = text_map.get(170, lang).format(a=10)

        # fill in defaults
        self.init.default = str(init_levels.level)
        self.a.default = str(init_levels.a_level)
        self.e.default = str(init_levels.e_level)
        self.q.default = str(init_levels.q_level)
        self.ascension_phase.default = str(init_levels.ascension_phase)

        self.character_id = character_id
        self.lang = lang

    async def on_submit(self, i: models.Inter):
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
                self.lang,
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
                self.lang,
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
        embed = models.DefaultEmbed()
        embed.set_author(
            name=text_map.get(18, self.lang), icon_url=i.user.display_avatar.url
        )
        await i.edit_original_response(embed=embed, view=view)
        view.message = await i.original_response()


class SpawnInitModal(ui.Button):
    def __init__(self, lang: str, modal: InitLevelModal):
        super().__init__(
            label=text_map.get(17, lang), style=discord.ButtonStyle.blurple
        )
        self.modal = modal

    async def callback(self, i: models.Inter):
        await i.response.send_modal(self.modal)


class TargetLevelModal(BaseModal):
    target = ui.TextInput(
        label="level_target",
        min_length=1,
        max_length=2,
    )

    ascension_target = ui.TextInput(
        label="ascension_target",
        min_length=1,
        max_length=1,
    )

    a = ui.TextInput(
        label="attack_target",
        min_length=1,
        max_length=2,
    )

    e = ui.TextInput(
        label="skill_target",
        min_length=1,
        max_length=2,
    )

    q = ui.TextInput(
        label="burst_target",
        min_length=1,
        max_length=2,
    )

    def __init__(
        self,
        character_id: str,
        lang: str,
        init_levels: List[int],
        suggested_levels: List[int],
    ) -> None:
        super().__init__(
            title=text_map.get(181, lang),
            timeout=config.mid_timeout,
        )
        level_type = text_map.get(182, lang)

        self.target.label = text_map.get(169, lang).format(level_type=level_type)
        self.target.placeholder = text_map.get(170, lang).format(a=90)
        self.target.default = str(init_levels[0])

        self.ascension_target.label = text_map.get(721, lang)
        self.ascension_target.placeholder = text_map.get(170, lang).format(a=4)
        self.ascension_target.default = str(init_levels[4])

        self.a.label = text_map.get(171, lang).format(level_type=level_type)
        self.a.placeholder = text_map.get(170, lang).format(a=9)
        self.a.default = (
            str(init_levels[1])
            if init_levels[1] > suggested_levels[0]
            else str(suggested_levels[0])
        )

        self.e.label = text_map.get(173, lang).format(level_type=level_type)
        self.e.placeholder = text_map.get(170, lang).format(a=4)
        self.e.default = (
            str(init_levels[2])
            if init_levels[2] > suggested_levels[1]
            else str(suggested_levels[1])
        )

        self.q.label = text_map.get(174, lang).format(level_type=level_type)
        self.q.placeholder = text_map.get(170, lang).format(a=10)
        self.q.default = (
            str(init_levels[3])
            if init_levels[3] > suggested_levels[2]
            else str(suggested_levels[2])
        )

        self.character_id = character_id
        self.init_levels = init_levels
        self.lang = lang

    async def on_submit(self, i: models.Inter) -> None:
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
                self.lang,
            )
        except InvalidWeaponCalcInput:
            return

        view = None
        if i.message is not None:
            view = View.from_message(i.message)
        if view is None:
            await i.edit_original_response(
                embed=models.DefaultEmbed().set_author(
                    name=text_map.get(644, self.lang), icon_url=asset.loader
                ),
                view=None,
            )
        else:
            await image_gen_transition(i, view, self.lang)

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

        ambr = AmbrTopAPI(i.client.session, to_ambr_top(self.lang))
        character = await ambr.get_character_detail(self.character_id)
        if not isinstance(character, ambr_models.CharacterDetail):
            raise TypeError("character is not a ambr_models.Character")

        todo_list = models.TodoList()

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
            if t.type is ambr_models.CharacterTalentType.ELEMENTAL_BURST
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
            if not isinstance(material, ambr_models.Material):
                raise TypeError("material is not a ambr_models.Material")
            all_materials.append((material, value))

        if not all_materials:
            await i.edit_original_response(
                embed=models.DefaultEmbed().set_author(
                    name=text_map.get(197, self.lang),
                    icon_url=i.user.display_avatar.url,
                )
            )
            return

        character = await ambr.get_character(self.character_id)
        if not isinstance(character, ambr_models.Character):
            raise TypeError("character is not a ambr_models.Character")

        dark_mode = await i.client.db.settings.get(i.user.id, Settings.DARK_MODE)
        fp = await main_funcs.draw_material_card(
            models.DrawInput(
                loop=i.client.loop,
                session=i.client.session,
                lang=self.lang,
                dark_mode=dark_mode,
            ),
            all_materials,
            "",
            background_color=get_element_color(character.element),
            draw_title=False,
        )
        fp.seek(0)
        embed = models.DefaultEmbed()
        embed.add_field(
            name=text_map.get(192, self.lang),
            value=f"{text_map.get(183, self.lang)}: {init} ▸ {target}\n"
            f"{text_map.get(722, self.lang)}: {init_ascension} ▸ {ascension}\n"
            f"{normal_attack.name}: {init_a} ▸ {a}\n"
            f"{elemental_skill.name}: {init_e} ▸ {e}\n"
            f"{elemental_burst.name}: {init_q} ▸ {q}",
        )
        embed.set_author(icon_url=character.icon, name=character.name)
        embed.set_image(url="attachment://materials.jpeg")
        view = View()
        view.clear_items()
        view.add_item(AddButton(items, self.lang))
        view.author = i.user
        await i.edit_original_response(
            embed=embed, attachments=[discord.File(fp, "materials.jpeg")], view=view
        )
        view.message = await i.original_response()


async def validate_level_input(
    level: str,
    a: str,
    e: str,
    q: str,
    ascension: str,
    i: models.Inter,
    lang: str,
):
    embed = models.DefaultEmbed().set_author(
        name=text_map.get(190, lang), icon_url=i.user.display_avatar.url
    )
    try:
        int_level = int(level)
        int_a = int(a)
        int_e = int(e)
        int_q = int(q)
        int_ascension = int(ascension)
    except ValueError:
        embed.description = text_map.get(187, lang)
        await i.followup.send(
            embed=embed,
            ephemeral=True,
        )
        raise InvalidWeaponCalcInput

    if int_level < 1 or int_level > 90:
        embed.description = text_map.get(172, lang).format(a=1, b=90)
        await i.followup.send(
            embed=embed,
            ephemeral=True,
        )
        raise InvalidWeaponCalcInput

    if int_a < 1 or int_a > 15 or int_e < 1 or int_e > 15 or int_q < 1 or int_q > 15:
        embed.description = text_map.get(172, lang).format(a=1, b=15)
        await i.followup.send(
            embed=embed,
            ephemeral=True,
        )
        raise InvalidWeaponCalcInput

    theoretical_ascension = level_to_ascension_phase(int_level)
    if int_ascension not in (theoretical_ascension, theoretical_ascension - 1):
        embed.description = text_map.get(730, lang)
        await i.followup.send(
            embed=embed,
            ephemeral=True,
        )
        raise InvalidWeaponCalcInput
