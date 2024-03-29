from typing import Dict, List, Optional

from discord import ButtonStyle, Embed, File, Locale, SelectOption
from discord.ui import Button, Select
from genshin.models import LineupPreview, LineupScenario

import dev.asset as asset
import dev.config as config
from ambr import Character
from apps.db.tables.user_settings import Settings
from apps.draw import main_funcs
from apps.text_map import text_map
from data.game.elements import get_element_emoji, get_element_list
from dev.base_ui import BaseView
from dev.models import DefaultEmbed, DrawInput, Inter
from utils import disable_view_items, get_character_emoji, image_gen_transition


class View(BaseView):
    def __init__(
        self,
        lang: Locale | str,
        options: List[SelectOption],
        scenario_dict: Dict[str, LineupScenario],
        ambr_characters: List[Character],
    ):
        super().__init__(timeout=config.long_timeout)

        self.characters: List[int] = []
        self.scenario: LineupScenario = list(scenario_dict.values())[0]

        self.lang = lang
        self.options = options
        self.scenario_dict = scenario_dict
        self.ambr_characters = ambr_characters
        self.lineup_selector: Optional[LineupSelector] = None

        self.add_item(SearchLineup(text_map.get(715, lang)))
        self.add_item(CharacterSelectButton(text_map.get(714, lang)))
        self.add_item(ScenarioSelector(text_map.get(140, lang), options, scenario_dict))


class CharacterSelectButton(Button):
    def __init__(self, label: str):
        super().__init__(style=ButtonStyle.primary, label=label, emoji=asset.user_emoji)
        self.view: View

    async def callback(self, i: Inter):
        self.view.clear_items()

        elements = get_element_list()
        for index, element in enumerate(elements):
            self.view.add_item(
                ElementButton(element, get_element_emoji(element), index // 4)
            )

        await i.response.edit_message(view=self.view)


class ElementButton(Button):
    def __init__(self, element: str, emoji: str, row: int):
        super().__init__(emoji=emoji, row=row)
        self.element = element
        self.view: View

    async def callback(self, i: Inter):
        await i.response.defer()
        self.view.clear_items()

        options = []
        for character in self.view.ambr_characters:
            if character.element == self.element:
                options.append(
                    SelectOption(
                        label=character.name,
                        value=character.id,
                        emoji=get_character_emoji(character.id),
                    )
                )

        self.view.add_item(
            CharacterSelector(
                text_map.get(714, self.view.lang), options, self.view.characters
            )
        )
        await i.edit_original_response(view=self.view)


class CharacterSelector(Select):
    def __init__(
        self,
        placeholder: str,
        options: List[SelectOption],
        current_characters: List[int],
    ):
        super().__init__(
            placeholder=placeholder,
            options=options,
            max_values=4 - len(current_characters),
        )
        self.view: View

    async def callback(self, i: Inter):
        self.view.clear_items()
        self.view.characters += [int(o.split("-")[0]) for o in self.values]

        self.view.add_item(SearchLineup(text_map.get(715, self.view.lang)))
        if len(self.view.characters) == 4:
            self.view.add_item(
                ClearCharacter(
                    text_map.get(716, self.view.lang), self.view.children.copy()
                )
            )
        else:
            self.view.add_item(CharacterSelectButton(text_map.get(714, self.view.lang)))
        self.view.add_item(
            ScenarioSelector(
                text_map.get(140, self.view.lang),
                self.view.options,
                self.view.scenario_dict,
            )
        )
        self.view.add_item(self.view.lineup_selector)  # type: ignore

        if i.message is not None:
            embed = i.message.embeds[0]
            fields = embed.fields.copy()
            embed.clear_fields()
            embed = update_search_status(self.view, embed)
            for field in fields:
                embed.add_field(name=field.name, value=field.value)

            await i.response.edit_message(embed=embed, view=self.view)


class ClearCharacter(Button):
    def __init__(self, label: str, items):
        super().__init__(style=ButtonStyle.danger, label=label, emoji=asset.clear_emoji)

        self.items = items
        self.view: View

    async def callback(self, i: Inter):
        self.view.characters = []

        self.view.remove_item(self)
        self.view.add_item(CharacterSelectButton(text_map.get(714, self.view.lang)))

        if i.message is not None:
            embed = update_search_status(self.view, i.message.embeds[0])
            await i.response.edit_message(embed=embed, view=self.view)


class ScenarioSelector(Select):
    def __init__(
        self,
        placeholder: str,
        options: List[SelectOption],
        scenario_dict: Dict[str, LineupScenario],
    ):
        super().__init__(placeholder=placeholder, options=options)
        self.scenario_dict = scenario_dict
        self.view: View

    async def callback(self, i: Inter):
        self.view.scenario = self.scenario_dict[self.values[0]]

        if i.message is not None:
            embed = i.message.embeds[0]
            fields = embed.fields.copy()
            embed.clear_fields()
            embed = update_search_status(self.view, embed)
            for field in fields:
                embed.add_field(name=field.name, value=field.value)

            await i.response.edit_message(embed=embed)


class SearchLineup(Button):
    def __init__(self, label: str):
        super().__init__(style=ButtonStyle.green, label=label, emoji=asset.search_emoji)
        self.view: View

    async def callback(self, i: Inter):
        await search_lineup(i, self.view)


class LineupSelector(Select):
    def __init__(
        self,
        placeholder: str,
        options: List[SelectOption],
        lineup_dict: Dict[str, LineupPreview],
        character_id: int,
        embed: Embed,
    ):
        super().__init__(placeholder=placeholder, options=options)
        self.lineup_dict = lineup_dict
        self.character_id = character_id
        self.embed = embed
        self.view: View

    async def callback(self, i: Inter):
        await image_gen_transition(i, self.view, self.view.lang)

        lineup = self.lineup_dict[self.values[0]]
        user = await i.client.db.users.get(i.user.id)
        client = await user.client
        lineup_detail = await client.get_lineup_details(lineup)

        embed = DefaultEmbed(lineup_detail.title, lineup_detail.description)
        embed.set_footer(
            text=f"{text_map.get(496, self.view.lang)}: {lineup.author_nickname} (AR {lineup.author_level})",
            icon_url=lineup.author_icon,
        )
        embed.set_image(url="attachment://lineup.png")

        fp = await main_funcs.draw_lineup_card(
            DrawInput(
                loop=i.client.loop,
                session=i.client.session,
                lang=self.view.lang,
                dark_mode=await i.client.db.settings.get(i.user.id, Settings.DARK_MODE),
            ),
            lineup,
            self.character_id,
        )
        fp.seek(0)

        disable_view_items(self.view)
        items = self.view.children.copy()
        self.view.clear_items()
        self.view.add_item(GoBack(self.embed, items))

        await i.edit_original_response(
            embed=embed, attachments=[File(fp, filename="lineup.png")], view=self.view
        )


class GoBack(Button):
    def __init__(self, embed: Embed, items):
        super().__init__(emoji=asset.back_emoji)
        self.embed = embed
        self.items = items
        self.view: View

    async def callback(self, i: Inter):
        self.view.clear_items()
        for item in self.items:
            self.view.add_item(item)

        await i.response.edit_message(view=self.view, embed=self.embed, attachments=[])


def update_search_status(view: View, embed: Embed) -> Embed:
    lang = view.lang
    query_str = ""
    if view.characters:
        query_str += text_map.get(712, lang) + ": "
        for c in view.characters:
            emoji = get_character_emoji(str(c))
            if emoji:
                query_str += f"{emoji} "
    if view.scenario is not None:
        query_str += text_map.get(713, lang) + ": "
        query_str += view.scenario.name

    if query_str:
        embed.description = query_str

    return embed


async def search_lineup(i: Inter, view: View):
    await i.response.defer()

    lang = view.lang

    embed = DefaultEmbed()
    embed.set_author(name=text_map.get(709, lang), icon_url=i.user.display_avatar.url)
    embed = update_search_status(view, embed)

    user = await i.client.db.users.get(i.user.id)
    client = await user.client
    lineups = await client.get_lineups(
        scenario=view.scenario, characters=view.characters, limit=12, page_size=1
    )

    lineup_dict: Dict[str, LineupPreview] = {}
    options: List[SelectOption] = []

    for index, lineup in enumerate(lineups):
        # find the characters that matches the searched characters
        match_characters = lineup.characters[0]
        for characters in lineup.characters:
            for character in characters:
                if character.id in view.characters:
                    match_characters = characters

        lineup_dict[lineup.id] = lineup
        options.append(
            SelectOption(
                label=f"#{index+1}",
                description=" | ".join([c.name for c in match_characters]),
                value=lineup.id,
                emoji=get_character_emoji(str(match_characters[0].id)),
            )
        )

        lineup_str = "\n".join(
            [
                f"{get_character_emoji(str(c.id))} **{c.name.split(' ')[1 if len(c.name.split(' '))==2 else 0]}** | {c.role}"
                for c in match_characters
            ]
        )
        embed.add_field(name=f"#{index+1}", value=lineup_str)

    for item in view.children:
        if isinstance(item, LineupSelector):
            view.remove_item(item)

    view.add_item(
        lineup_selector := LineupSelector(
            text_map.get(711, lang), options, lineup_dict, 0, embed
        )
    )
    view.lineup_selector = lineup_selector

    await i.edit_original_response(embed=embed, view=view)
