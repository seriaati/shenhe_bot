from typing import Dict, List, Optional, Tuple
from apps.draw.utility import image_gen_transition
from apps.genshin.custom_model import DrawInput
from apps.text_map.convert_locale import to_genshin_py
from utility.utils import DefaultEmbed, get_user_appearance_mode
from apps.draw import main_funcs
import yaml
import genshin
from discord import Embed, Interaction, SelectOption, File, Locale
from discord.ui import Button, Select
import asset
import config
from apps.genshin.utils import get_character_builds, get_character_emoji
from apps.text_map.cond_text import cond_text
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from data.game.elements import get_element_emoji, get_element_list
from UI_base_models import BaseView


class View(BaseView):
    def __init__(self):
        super().__init__(timeout=config.long_timeout)

        elements = get_element_list()
        for index, element in enumerate(elements):
            self.add_item(
                ElementButton(element, get_element_emoji(element), index // 4)
            )


class ElementButton(Button):
    def __init__(self, element: str, element_emoji: str, row: int):
        super().__init__(emoji=element_emoji, row=row)
        self.element = element

    async def callback(self, i: Interaction):
        self.view: View
        await element_button_callback(i, self.element, self.view)


class ShowThoughts(Button):
    def __init__(self, embed: Embed):
        super().__init__(emoji="💭", row=1)
        self.embed = embed

    async def callback(self, i: Interaction):
        await i.response.edit_message(embed=self.embed)


class CharacterSelect(Select):
    def __init__(
        self, options: List[SelectOption], placeholder: str, builds: Dict, element: str
    ):
        super().__init__(options=options, placeholder=placeholder)
        self.builds = builds
        self.element = element

    async def callback(self, i: Interaction):
        self.view: View
        locale = await get_user_locale(i.user.id, i.client.pool) or i.locale
        builds = get_character_builds(self.values[0], self.builds, locale)
        embeds = []
        options = []
        for index, build in enumerate(builds):
            if build.weapon is None:
                continue

            embeds.append(build.embed)
            weapon_id = text_map.get_id_from_name(build.weapon)
            if weapon_id is None:
                continue

            options.append(
                SelectOption(
                    label=f"{text_map.get(162, locale)} {index+1}",
                    description=f"{text_map.get_weapon_name(weapon_id, locale)} | {cond_text.get_text(str(locale), 'build', build.artifact)}",
                    value=str(index),
                )
            )
        placeholder = text_map.get(163, locale)
        self.view.clear_items()
        self.view.add_item(BuildSelect(options, placeholder, embeds))
        self.view.add_item(GoBack("character", self.element))
        self.view.add_item(
            Button(
                label=text_map.get(96, locale),
                url="https://bbs.nga.cn/read.php?tid=25843014",
                row=1,
            )
        )
        thoughts_embed = [b.embed for b in builds if b.is_thought]
        if thoughts_embed:
            self.view.add_item(ShowThoughts(thoughts_embed[0]))
        self.view.add_item(TeamButton(int(self.values[0])))
        await i.response.edit_message(embed=embeds[0], view=self.view)


class BuildSelect(Select):
    def __init__(
        self, options: List[SelectOption], placeholder: str, build_embeds: List[Embed]
    ):
        super().__init__(options=options, placeholder=placeholder, row=0)
        self.build_embeds = build_embeds

    async def callback(self, i: Interaction):
        await i.response.edit_message(embed=self.build_embeds[int(self.values[0])])


class TeamButton(Button):
    def __init__(self, character_id: int):
        super().__init__(emoji=asset.team_emoji)
        self.character_id = character_id

    async def callback(self, i: Interaction):
        self.view: View

        locale = await get_user_locale(i.user.id, i.client.pool) or i.locale
        dark_mode = await get_user_appearance_mode(i.user.id, i.client.pool)

        await image_gen_transition(i, self.view, locale)

        client: genshin.Client = i.client.genshin_client
        client.lang = to_genshin_py(locale)

        scenarios = await client.get_lineup_scenarios()
        scenarios_to_search = [
            scenarios.abyss.spire,
            scenarios.world,
            scenarios.world.domain_challenges,
            scenarios.world.battles,
        ]
        lineup_dict = {}
        select_options = []
        lineup = None
        
        for index, scenario in enumerate(scenarios_to_search):
            select_options.append(
                SelectOption(label=scenario.name, value=scenario.name)
            )
            lineup_dict[scenario.name] = (
                line_up:=await client.get_lineups(
                    characters=[self.character_id], limit=1, scenario=scenario, page_size=1
                )
            )[0]
            if index == 0:
                lineup = line_up[0]

        embeds, attachments = await get_embeds_for_lineup(
            i, locale, dark_mode, lineup, scenarios.abyss.spire.name, self.character_id
        )

        for item in self.view.children:
            item.disabled = False
        
        children_copy = self.view.children.copy()

        self.view.clear_items()

        self.view.add_item(
            TeamSelect(
                select_options,
                text_map.get(140, locale),
                lineup_dict,
                locale,
                dark_mode,
                self.character_id,
            )
        )
        self.view.add_item(GoBackOriginal(children_copy, i.message.embeds[0]))
        await i.edit_original_response(
            embeds=embeds, attachments=attachments, view=self.view
        )


class TeamSelect(Select):
    def __init__(
        self,
        options: List[SelectOption],
        placeholder: str,
        lineup_dict: Dict[str, genshin.models.LineupPreview],
        locale: Locale | str,
        dark_mode: bool,
        character_id: int,
    ):
        super().__init__(options=options, placeholder=placeholder, row=0)
        self.lineup_dict = lineup_dict
        self.locale = locale
        self.dark_mode = dark_mode
        self.character_id = character_id

    async def callback(self, i: Interaction):
        self.view: View
        await image_gen_transition(i, self.view, self.locale)

        embeds, attachments = await get_embeds_for_lineup(
            i,
            self.locale,
            self.dark_mode,
            self.lineup_dict[self.values[0]],
            self.values[0],
            self.character_id,
        )

        for item in self.view.children:
            item.disabled = False

        await i.edit_original_response(embeds=embeds, attachments=attachments, view=self.view)


async def get_embeds_for_lineup(
    i: Interaction,
    locale: Locale | str,
    dark_mode: bool,
    lineup: genshin.models.LineupPreview,
    scenario_name: str,
    character_id: int,
) -> Tuple[List[Embed], List[File]]:
    embeds = []
    attachments = []

    fp = await main_funcs.draw_lineup_card(
        DrawInput(
            loop=i.client.loop,
            session=i.client.session,
            locale=locale,
            dark_mode=dark_mode,
        ),
        lineup,
        character_id,
    )

    embed = DefaultEmbed(f"{text_map.get(139, locale)} | {scenario_name}")
    embed.set_footer(
        text=f"{text_map.get(496, locale)}: {lineup.author_nickname} (AR {lineup.author_level})",
        icon_url=lineup.author_icon,
    )
    embed.set_image(url="attachment://lineup.jpeg")
    fp.seek(0)
    attachments.append(File(fp, filename="lineup.jpeg"))
    embeds.append(embed)

    return embeds, attachments


class GoBackOriginal(Button):
    def __init__(self, items, embed: Embed):
        super().__init__(emoji=asset.back_emoji, row=2)
        self.items = items
        self.embed = embed

    async def callback(self, i: Interaction):
        self.view: View
        self.view.clear_items()
        for item in self.items:
            self.view.add_item(item)
        await i.response.edit_message(view=self.view, attachments=[], embed=self.embed)


class GoBack(Button):
    def __init__(self, place_to_go_back: str, element: Optional[str] = None):
        super().__init__(emoji=asset.back_emoji, row=2)
        self.place_to_go_back = place_to_go_back
        self.element = element

    async def callback(self, i: Interaction):
        self.view: View
        self.view.clear_items()
        if self.place_to_go_back == "element":
            elements = get_element_list()
            for index, element in enumerate(elements):
                self.view.add_item(
                    ElementButton(element, get_element_emoji(element), index // 4)
                )
            await i.response.edit_message(view=self.view)
        elif self.place_to_go_back == "character" and self.element is not None:
            await element_button_callback(i, self.element, self.view)


async def element_button_callback(i: Interaction, element: str, view: View):
    with open(f"data/builds/{element.lower()}.yaml", "r", encoding="utf-8") as f:
        builds = yaml.full_load(f)
    user_locale = await get_user_locale(i.user.id, i.client.pool)
    options = []
    placeholder = text_map.get(157, i.locale, user_locale)
    user_locale = await get_user_locale(i.user.id, i.client.pool)
    for character_name, character_builds in builds.items():
        character_id = text_map.get_id_from_name(character_name)
        localized_character_name = text_map.get_character_name(
            str(character_id), user_locale or i.locale
        )
        if localized_character_name is None:
            continue
        options.append(
            SelectOption(
                label=localized_character_name,
                emoji=get_character_emoji(str(character_id)),
                value=str(character_id),
                description=f'{len(character_builds["builds"])} {text_map.get(164, i.locale, user_locale)}',
            )
        )
    view.clear_items()
    view.add_item(CharacterSelect(options, placeholder, builds, element))
    view.add_item(GoBack("element"))
    await i.response.edit_message(embed=None, view=view)
    view.message = await i.original_response()
