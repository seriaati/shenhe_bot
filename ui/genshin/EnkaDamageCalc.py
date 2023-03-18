from typing import Any, Dict, List
import aiofiles
import json
import random

import aiohttp
import PIL
from discord import ButtonStyle, File, Locale, SelectOption, utils
from discord.ui import Button, Select
from pyppeteer import browser

import asset
import config
from apps.draw import main_funcs
from apps.genshin.browser import get_browser
from apps.genshin.custom_model import CustomInteraction, DrawInput, EnkaView
from apps.text_map.text_map_app import text_map
from base_ui import BaseView
from exceptions import NoCharacterFound
from ui.others.settings.CustomImage import get_user_custom_image
import utility.utils as utility_utils
import yelan.damage_calculator as damage_calc
from yelan.data.GO_modes import hit_mode_texts


class View(BaseView):
    def __init__(
        self,
        enka_view: EnkaView,
        locale: Locale | str,
        browsers: Dict[str, browser.Browser],
    ):
        super().__init__(timeout=config.long_timeout)

        # defining damage calculation variables
        self.enka_view = enka_view
        character_name = ""
        if enka_view.data.characters is None:
            raise NoCharacterFound
        for character in enka_view.data.characters:
            if str(character.id) == enka_view.character_id:
                character_name = character.name
                break

        self.calculator = damage_calc.DamageCalculator(
            character_name,
            enka_view.eng_data,
            enka_view.character_id,
            locale,
            "critHit",
            enka_view.member,
            get_browser(browsers, str(locale)),
        )

        # producing select options
        reaction_mode_options = [
            SelectOption(label=text_map.get(331, locale), value="none")
        ]
        element = str(self.calculator.current_character.element.name)
        if element == "Cryo" or self.calculator.infusion_aura == "cryo":
            reaction_mode_options.append(
                SelectOption(label=text_map.get(332, locale), value="melt")
            )
        elif (
            element == "Pyro"
            or self.calculator.infusion_aura == "pyro"
            or element == "Anemo"
        ):
            reaction_mode_options.append(
                SelectOption(label=text_map.get(333, locale), value="vaporize")
            )
            reaction_mode_options.append(
                SelectOption(label=text_map.get(332, locale), value="melt")
            )
        elif element == "Hydro":
            reaction_mode_options.append(
                SelectOption(label=text_map.get(333, locale), value="vaporize")
            )
        elif element == "Dendro":
            reaction_mode_options.append(
                SelectOption(label=text_map.get(525, locale), value="spread")
            )
        elif element in ("Electro", "Anemo"):
            reaction_mode_options.append(
                SelectOption(label=text_map.get(526, locale), value="aggravate")
            )

        teammate_options: List[SelectOption] = []
        for option in self.enka_view.character_options:
            if option.value == str(self.enka_view.character_id):
                continue
            teammate_options.append(
                SelectOption(label=option.label, value=option.value, emoji=option.emoji)
            )

        # adding items
        for hit_mode, text_hash in hit_mode_texts.items():
            self.add_item(HitModeButton(hit_mode, text_map.get(text_hash, locale)))
        self.add_item(
            ReactionModeSelect(reaction_mode_options, text_map.get(337, locale))
        )
        options = [
            SelectOption(label=text_map.get(338, locale), value="none"),
            SelectOption(
                label=text_map.get(339, locale),
                description=text_map.get(341, locale),
                value="pyro",
            ),
            SelectOption(
                label=text_map.get(340, locale),
                description=text_map.get(342, locale),
                value="cryo",
            ),
            SelectOption(
                label=text_map.get(360, locale),
                description=text_map.get(357, locale),
                value="hydro",
            ),
        ]
        self.add_item(InfusionAuraSelect(options, text_map.get(343, locale)))
        if teammate_options:
            self.add_item(TeamSelectButton(teammate_options, text_map.get(344, locale)))
        self.add_item(GoBack())
        self.add_item(RunCalc(text_map.get(502, locale)))


class GoBack(Button):
    def __init__(self):
        super().__init__(emoji=asset.back_emoji, row=4)

    async def callback(self, i: CustomInteraction):
        self.view: View
        await go_back_callback(i, self.view.enka_view)


async def go_back_callback(i: CustomInteraction, enka_view: EnkaView):
    enka_view.clear_items()
    for child in enka_view.original_children:
        enka_view.add_item(child)

    for child in enka_view.children:
        child.disabled = True  # type: ignore

    # await i.response.edit_message(
    #     # embed=utility_utils.DefaultEmbed()
    #     # .set_author(
    #     #     name=text_map.get(644, enka_view.locale),
    #     #     icon_url=asset.loader,
    #     # )
    #     # .set_image(url="https://i.imgur.com/AsxZdAu.gif"),
    #     embed=None,
    #     attachments=[],
    #     view=enka_view,
    # )
    await i.response.defer()

    for child in enka_view.children:
        child.disabled = False  # type: ignore

    if enka_view.data.characters is None:
        raise NoCharacterFound

    character = utils.get(enka_view.data.characters, id=int(enka_view.character_id))
    if not character:
        raise AssertionError

    dark_mode = await utility_utils.get_user_appearance_mode(i.user.id, i.client.pool)
    try:
        custom_image = await get_user_custom_image(
            i.user.id, int(enka_view.character_id), i.client.pool
        )
        if custom_image is None:
            async with aiofiles.open("data/draw/genshin_fanart.json", "r") as f:
                fanart: Dict[str, List[str]] = json.loads(await f.read())
            url = random.choice(fanart[str(enka_view.character_id)])
        else:
            url = custom_image.url

        card = await main_funcs.draw_profile_card_v2(
            DrawInput(
                loop=i.client.loop,
                session=i.client.session,
                locale=enka_view.locale,
                dark_mode=dark_mode,
            ),
            character,
            url,
        )
    except (aiohttp.InvalidURL, PIL.UnidentifiedImageError):
        return await i.edit_original_response(
            embed=utility_utils.ErrorEmbed().set_author(
                name=text_map.get(274, enka_view.locale),
                icon_url=i.user.display_avatar.url,
            ),
            attachments=[],
            view=enka_view,
        )
    if card is None:
        embed = utility_utils.DefaultEmbed().set_author(
            name=text_map.get(189, enka_view.locale),
            icon_url=i.user.display_avatar.url,
        )
        return await i.edit_original_response(
            embed=embed, attachments=[], view=enka_view
        )

    card.seek(0)
    file_ = File(card, "card.jpeg")
    await i.edit_original_response(embed=None, attachments=[file_], view=enka_view)


class HitModeButton(Button):
    def __init__(self, hit_mode: str, label: str):
        super().__init__(style=ButtonStyle.blurple, label=label)
        self.hit_mode = hit_mode

    async def callback(self, i: CustomInteraction) -> Any:
        self.view: View
        self.view.calculator.hit_mode = self.hit_mode
        await damage_calc.return_current_status(i, self.view)


class ReactionModeSelect(Select):
    def __init__(self, options: list[SelectOption], placeholder: str):
        super().__init__(
            placeholder=placeholder, options=options, custom_id="reaction_mode"
        )

    async def callback(self, i: CustomInteraction) -> Any:
        self.view: View
        self.view.calculator.reaction_mode = (
            "" if self.values[0] == "none" else self.values[0]
        )
        await damage_calc.return_current_status(i, self.view)


class InfusionAuraSelect(Select):
    def __init__(self, options: List[SelectOption], placeholder: str):
        super().__init__(
            placeholder=placeholder, options=options, custom_id="infusion_aura"
        )

    async def callback(self, i: CustomInteraction) -> Any:
        self.view: View
        self.view.calculator.infusion_aura = (
            "" if self.values[0] == "none" else self.values[0]
        )
        await damage_calc.return_current_status(i, self.view)


class TeamSelectView(BaseView):
    def __init__(self, prev_view: View):
        super().__init__(timeout=config.mid_timeout)
        self.prev_view = prev_view


class GoBackToCalc(Button):
    def __init__(self):
        super().__init__(emoji=asset.back_emoji, row=4)

    async def callback(self, i: CustomInteraction):
        self.view: TeamSelectView
        view = self.view.prev_view
        view.author = i.user
        await i.response.edit_message(view=view)
        await damage_calc.return_current_status(i, view, True)
        view.message = await i.original_response()


class TeamSelectButton(Button):
    def __init__(self, options: List[SelectOption], placeholder: str):
        super().__init__(
            style=ButtonStyle.blurple,
            label=placeholder,
            custom_id="team_select",
            emoji=asset.team_emoji,
        )
        self.options = options
        self.placeholder = placeholder

    async def callback(self, i: CustomInteraction):
        self.view: View
        view = TeamSelectView(self.view)
        view.add_item(GoBackToCalc())
        divided: List[List[SelectOption]] = list(
            utility_utils.divide_chunks(self.options, 25)
        )
        count = 1
        for chunk in divided:
            view.add_item(
                TeamSelect(
                    chunk,
                    f"{self.placeholder} ({count}~{count + len(chunk) - 1})",
                )
            )
            count += len(chunk)
        view.author = i.user
        await i.response.edit_message(view=view)
        view.message = await i.original_response()


class TeamSelect(Select):
    def __init__(self, options: list[SelectOption], placeholder: str):
        super().__init__(
            placeholder=placeholder,
            options=options,
            max_values=3 if len(options) >= 3 else len(options),
        )

    async def callback(self, i: CustomInteraction) -> Any:
        self.view: TeamSelectView
        self.view.prev_view.calculator.team = self.values
        await damage_calc.return_current_status(i, self.view.prev_view)


class RunCalc(Button):
    def __init__(self, label: str):
        super().__init__(
            style=ButtonStyle.green,
            label=label,
            row=4,
            custom_id="calculate",
            emoji=asset.play_emoji,
        )

    async def callback(self, i: CustomInteraction) -> Any:
        self.view: View
        await damage_calc.return_damage(i, self.view)
