from typing import List

from discord import ButtonStyle, File, Interaction, Locale, SelectOption
from discord.ui import Button, Select, TextInput
from UI_elements.calc import AddToTodo
import asset
import config
from ambr.client import AmbrTopAPI
from ambr.models import Character, CharacterDetail, CharacterInfo, CharacterTalentType, Material
from apps.genshin.custom_model import TodoList
from apps.genshin.utils import (
    InvalidLevelInput,
    character_level_to_ascension_phase,
    get_character_emoji,
    validate_level_input,
)
from apps.text_map.convert_locale import to_ambr_top
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from data.game.elements import get_element_color, get_element_emoji, get_element_list
from UI_base_models import BaseModal, BaseView
from utility.utils import default_embed, get_user_appearance_mode
from yelan.draw import draw_big_material_card


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
        locale = await get_user_locale(i.user.id, i.client.db) or i.locale
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
        modal = InitLevelModal(
            self.values[0], await get_user_locale(i.user.id, i.client.db) or i.locale
        )
        await i.response.send_modal(modal)


class SpawnTargetLevelModal(Button):
    def __init__(self, locale: Locale | str, character_id: str, init_levels: List[int]):
        super().__init__(label=text_map.get(17, locale), style=ButtonStyle.blurple)
        self.locale = locale
        self.character_id = character_id
        self.init_levels = init_levels

    async def callback(self, i: Interaction):
        await i.response.send_modal(
            TargetLevelModal(self.character_id, self.locale, self.init_levels)
        )


class InitLevelModal(BaseModal):
    init = TextInput(
        label="level_init",
        placeholder="like: 90",
        default="1",
    )

    a = TextInput(
        label="attack_init",
        placeholder="like: 9",
        default="1",
    )

    e = TextInput(
        label="skill_init",
        placeholder="like: 4",
        default="1",
    )

    q = TextInput(
        label="burst_init",
        placeholder="like: 10",
        default="1",
    )

    def __init__(self, character_id: str, locale: Locale | str) -> None:
        super().__init__(
            title=text_map.get(181, locale),
            timeout=config.mid_timeout,
        )
        level_type = text_map.get(168, locale)
        self.init.label = text_map.get(169, locale).format(level_type=level_type)
        self.a.label = text_map.get(171, locale).format(level_type=level_type)
        self.e.label = text_map.get(173, locale).format(level_type=level_type)
        self.q.label = text_map.get(174, locale).format(level_type=level_type)
        self.character_id = character_id
        self.locale = locale

    async def on_submit(self, i: Interaction):
        # validate input
        try:
            await validate_level_input(
                self.init.value,
                self.a.value,
                self.e.value,
                self.q.value,
                i,
                self.locale,
            )
        except InvalidLevelInput:
            return

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
                ],
            )
        )
        await i.response.edit_message(
            view=view,
            embed=default_embed().set_author(
                name=text_map.get(18, self.locale), icon_url=i.user.display_avatar.url
            ),
        )
        view.message = await i.original_response()


class TargetLevelModal(BaseModal):
    target = TextInput(
        label="level_target",
        placeholder="like: 90",
    )

    a = TextInput(
        label="attack_target",
        placeholder="like: 9",
    )

    e = TextInput(
        label="skill_target",
        placeholder="like: 4",
    )

    q = TextInput(
        label="burst_target",
        placeholder="like: 10",
    )

    def __init__(
        self, character_id: str, locale: Locale | str, init_levels: List[int]
    ) -> None:
        super().__init__(
            title=text_map.get(181, locale),
            timeout=config.mid_timeout,
        )
        level_type = text_map.get(182, locale)
        self.target.label = text_map.get(169, locale).format(level_type=level_type)
        self.target.placeholder = text_map.get(170, locale).format(a=90)
        self.a.label = text_map.get(171, locale).format(level_type=level_type)
        self.a.placeholder = text_map.get(170, locale).format(a=9)
        self.e.label = text_map.get(173, locale).format(level_type=level_type)
        self.e.placeholder = text_map.get(170, locale).format(a=4)
        self.q.label = text_map.get(174, locale).format(level_type=level_type)
        self.q.placeholder = text_map.get(170, locale).format(a=10)
        self.character_id = character_id
        self.init_levels = init_levels
        self.locale = locale

    async def on_submit(self, i: Interaction) -> None:
        # validate input
        try:
            await validate_level_input(
                self.target.value,
                self.a.value,
                self.e.value,
                self.q.value,
                i,
                self.locale,
            )
        except InvalidLevelInput:
            return

        await i.response.edit_message(
            embed=default_embed().set_author(
                name=text_map.get(644, self.locale), icon_url=asset.loader
            ),view=None
        )

        target = int(self.target.value)
        a = int(self.a.value)
        e = int(self.e.value)
        q = int(self.q.value)
        init = self.init_levels[0]
        init_a = self.init_levels[1]
        init_e = self.init_levels[2]
        init_q = self.init_levels[3]

        ambr = AmbrTopAPI(i.client.session, to_ambr_top(self.locale))
        character = await ambr.get_character_detail(self.character_id)
        if not isinstance(character, CharacterDetail):
            raise TypeError("character is not a Character")

        todo_list = TodoList()

        # ascension items
        start = character_level_to_ascension_phase(init)
        end = character_level_to_ascension_phase(target)
        ascension_items = character.upgrade.ascentions[start:end]
        for asc in ascension_items:
            cost_items = asc.cost_items
            if cost_items is not None:
                for item in cost_items:
                    todo_list.add_item({int(item[0].id): item[1]})
            mora_cost = asc.mora_cost
            if mora_cost is not None:
                todo_list.add_item({202: mora_cost})

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
                    start = init_a
                    end = a
                elif index == 1:
                    start = init_e
                    end = e
                else:  # index == 2
                    start = init_q
                    end = q
                talent = talent[start : end - 1]
                for t in talent:
                    if t.cost_items is not None:
                        for item in t.cost_items:
                            todo_list.add_item({int(item[0].id): item[1]})
                    if t.mora_cost is not None:
                        todo_list.add_item({202: t.mora_cost})

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

        character = await ambr.get_character(self.character_id)
        if not isinstance(character, Character):
            raise TypeError("character is not a Character")
        fp = await draw_big_material_card(
            all_materials,
            f"{character.name}: {text_map.get(191, self.locale)}",
            get_element_color(character.element),
            i.client.session,
            await get_user_appearance_mode(i.user.id, i.client.db),
            self.locale,
        )
        fp.seek(0)
        embed = default_embed()
        embed.add_field(
            name=text_map.get(192, self.locale),
            value=f"{text_map.get(183, self.locale)}: {init} -> {target}\n"
            f"{normal_attack.name}: {init} ▸ {target}\n"
            f"{elemental_skill.name}: {init_e} ▸ {e}\n"
            f"{elemental_burst.name}: {init_q} ▸ {q}",
        )
        embed.set_author(url=character.icon, name=character.name)
        embed.set_image(url="attachment://materials.jpeg")
        view = View()
        view.clear_items()
        view.add_item(AddToTodo.AddToTodo(items, self.locale))
        view.author = i.user
        await i.edit_original_response(
            embed=embed, attachments=[File(fp, "materials.jpeg")], view=view
        )
        view.message = await i.original_response()
