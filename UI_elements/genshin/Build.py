from typing import Dict, List
import aiosqlite
import yaml
from apps.genshin.utils import get_character, get_character_builds
from apps.text_map.utils import get_user_locale
from debug import DefaultView
from discord import Embed, User, Interaction, SelectOption
from discord.ui import Button, Select
from apps.text_map.text_map_app import text_map
from data.game.elements import convert_elements, elements
import config


class View(DefaultView):
    def __init__(self, author: User, db: aiosqlite.Connection):
        super().__init__(timeout=config.long_timeout)
        self.author = author
        self.db = db

        element_names = list(convert_elements.values())
        element_emojis = list(elements.values())
        for index in range(0, 7):
            self.add_item(
                ElementButton(element_names[index], element_emojis[index], index // 4)
            )


class ElementButton(Button):
    def __init__(self, element: str, element_emoji: str, row: int):
        super().__init__(emoji=element_emoji, row=row)
        self.element = element

    async def callback(self, i: Interaction):
        await element_button_callback(i, self.element, self.view)


class CharacterSelect(Select):
    def __init__(
        self, options: List[SelectOption], placeholder: str, builds: Dict, element: str
    ):
        super().__init__(options=options, placeholder=placeholder)
        self.builds = builds
        self.element = element

    async def callback(self, i: Interaction):
        self.view: View
        user_locale = await get_user_locale(i.user.id, self.view.db)
        builds, has_thoughts = get_character_builds(
            self.values[0], self.builds, i.locale, user_locale
        )
        embeds = []
        options = []
        for index, build in enumerate(builds):
            embeds.append(build[0])
            if has_thoughts and index + 1 == len(builds):
                options.append(SelectOption(label=f"{build[1]}", value=index))
            else:
                options.append(
                    SelectOption(
                        label=f"{text_map.get(162, i.locale, user_locale)} {index+1} | {build[1]} {build[2]}",
                        value=index,
                    )
                )
        placeholder = text_map.get(163, i.locale, user_locale)
        self.view.clear_items()
        self.view.add_item(BuildSelect(options, placeholder, embeds))
        self.view.add_item(GoBack("character", self.element))
        await i.response.edit_message(embed=embeds[0], view=self.view)


class BuildSelect(Select):
    def __init__(
        self, options: List[SelectOption], placeholder: str, build_embeds: List[Embed]
    ):
        super().__init__(options=options, placeholder=placeholder)
        self.build_embeds = build_embeds

    async def callback(self, i: Interaction):
        await i.response.edit_message(embed=self.build_embeds[int(self.values[0])])


class GoBack(Button):
    def __init__(self, place_to_go_back: str, element: str = None):
        super().__init__(emoji="<:left:982588994778972171>")
        self.place_to_go_back = place_to_go_back
        self.element = element

    async def callback(self, i: Interaction):
        self.view: View
        self.view.clear_items()
        if self.place_to_go_back == "element":
            element_names = list(convert_elements.values())
            element_emojis = list(elements.values())
            for index in range(0, 7):
                self.view.add_item(
                    ElementButton(
                        element_names[index], element_emojis[index], index // 4
                    )
                )
            await i.response.edit_message(view=self.view)
        elif self.place_to_go_back == "character":
            await element_button_callback(i, self.element, self.view)


async def element_button_callback(i: Interaction, element: str, view: View):
    with open(f"data/builds/{element.lower()}.yaml", "r", encoding="utf-8") as f:
        builds = yaml.full_load(f)
    user_locale = await get_user_locale(i.user.id, view.db)
    options = []
    placeholder = text_map.get(157, i.locale, user_locale)
    user_locale = await get_user_locale(i.user.id, view.db)
    for character_name, character_builds in builds.items():
        character_id = text_map.get_character_id_with_name(character_name)
        localized_character_name = text_map.get_character_name(
            character_id, i.locale, user_locale
        )
        options.append(
            SelectOption(
                label=localized_character_name,
                emoji=get_character(character_id)["emoji"],
                value=character_id,
                description=f'{len(character_builds["builds"])} {text_map.get(164, i.locale, user_locale)}',
            )
        )
    view.clear_items()
    view.add_item(CharacterSelect(options, placeholder, builds, element))
    view.add_item(GoBack("element"))
    await i.response.edit_message(embed=None, view=view)
    view.message = await i.original_response()
