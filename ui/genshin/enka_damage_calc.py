import random
from typing import Any, Dict, List

import aiohttp
import discord
import PIL
from discord import ui, utils
from pyppeteer import browser

import dev.asset as asset
import dev.config as config
import yelan.damage_calculator as damage_calc
from apps.db.custom_image import get_user_custom_image
from apps.db.tables.user_settings import Settings
from apps.draw import main_funcs
from apps.genshin import get_browser
from apps.text_map import text_map
from dev.base_ui import BaseView, EnkaView
from dev.exceptions import CardNotReady, NoCharacterFound
from dev.models import DrawInput, ErrorEmbed, Inter
from utils import divide_chunks, get_character_fanarts
from yelan.data.GO_modes import HIT_MODE_TEXTS


class View(BaseView):
    def __init__(
        self,
        enka_view: EnkaView,
        lang: discord.Locale | str,
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
            enka_view.en_data,
            enka_view.character_id,
            lang,
            "critHit",
            enka_view.member,
            get_browser(browsers, str(lang)),
        )

        # producing select options
        reaction_mode_options = [
            discord.SelectOption(label=text_map.get(331, lang), value="none")
        ]
        element = str(self.calculator.current_character.element.name)
        if element == "Cryo" or self.calculator.infusion_aura == "cryo":
            reaction_mode_options.append(
                discord.SelectOption(label=text_map.get(332, lang), value="melt")
            )
        elif (
            element == "Pyro"
            or self.calculator.infusion_aura == "pyro"
            or element == "Anemo"
        ):
            reaction_mode_options.append(
                discord.SelectOption(label=text_map.get(333, lang), value="vaporize")
            )
            reaction_mode_options.append(
                discord.SelectOption(label=text_map.get(332, lang), value="melt")
            )
        elif element == "Hydro":
            reaction_mode_options.append(
                discord.SelectOption(label=text_map.get(333, lang), value="vaporize")
            )
        elif element == "Dendro":
            reaction_mode_options.append(
                discord.SelectOption(label=text_map.get(525, lang), value="spread")
            )
        elif element in ("Electro", "Anemo"):
            reaction_mode_options.append(
                discord.SelectOption(label=text_map.get(526, lang), value="aggravate")
            )

        teammate_options: List[discord.SelectOption] = []
        for option in self.enka_view.character_options:
            if option.value == str(self.enka_view.character_id):
                continue
            teammate_options.append(
                discord.SelectOption(
                    label=option.label, value=option.value, emoji=option.emoji
                )
            )

        # adding items
        for hit_mode, text_hash in HIT_MODE_TEXTS.items():
            self.add_item(HitModeButton(hit_mode, text_map.get(text_hash, lang)))
        self.add_item(
            ReactionModeSelect(reaction_mode_options, text_map.get(337, lang))
        )
        options = [
            discord.SelectOption(label=text_map.get(338, lang), value="none"),
            discord.SelectOption(
                label=text_map.get(339, lang),
                description=text_map.get(341, lang),
                value="pyro",
            ),
            discord.SelectOption(
                label=text_map.get(340, lang),
                description=text_map.get(342, lang),
                value="cryo",
            ),
            discord.SelectOption(
                label=text_map.get(360, lang),
                description=text_map.get(357, lang),
                value="hydro",
            ),
        ]
        self.add_item(InfusionAuraSelect(options, text_map.get(343, lang)))
        if teammate_options:
            self.add_item(TeamSelectButton(teammate_options, text_map.get(344, lang)))
        self.add_item(GoBack())
        self.add_item(RunCalc(text_map.get(502, lang)))


class GoBack(ui.Button):
    def __init__(self):
        super().__init__(emoji=asset.back_emoji, row=4)
        self.view: View

    async def callback(self, i: Inter):
        if isinstance(self.view, EnkaView):
            view = self.view
        else:
            view = self.view.enka_view
        await go_back_callback(i, view)


async def go_back_callback(i: Inter, enka_view: EnkaView):
    await i.response.defer()

    enka_view.clear_items()
    for child in enka_view.original_children:
        enka_view.add_item(child)
    for child in enka_view.children:
        if isinstance(child, ui.Button):
            child.disabled = False

    character = utils.get(enka_view.data.characters, id=int(enka_view.character_id))
    if not character:
        raise AssertionError

    dark_mode = dark_mode = await i.client.db.settings.get(
        i.user.id, Settings.DARK_MODE
    )
    version = await i.client.db.settings.get(i.user.id, Settings.PROFILE_VERSION)
    try:
        custom_image = await get_user_custom_image(
            i.user.id, int(enka_view.character_id), i.client.pool
        )
        if version == 2:
            if custom_image is None:
                urls = await get_character_fanarts(str(enka_view.character_id))
                if not urls:
                    raise CardNotReady
                url = random.choice(urls)
            else:
                url = custom_image.url

            card = await main_funcs.draw_profile_card_v2(
                DrawInput(
                    loop=i.client.loop,
                    session=i.client.session,
                    lang=enka_view.lang,
                    dark_mode=dark_mode,
                ),
                character,
                url,
            )
        else:
            card = await main_funcs.draw_profile_card_v1(
                DrawInput(
                    loop=i.client.loop,
                    session=i.client.session,
                    lang=enka_view.lang,
                    dark_mode=dark_mode,
                ),
                character,
                custom_image.url if custom_image else None,
            )
            if card is None:
                raise CardNotReady
    except (aiohttp.InvalidURL, PIL.UnidentifiedImageError):
        return await i.edit_original_response(
            embed=ErrorEmbed().set_author(
                name=text_map.get(274, enka_view.lang),
                icon_url=i.user.display_avatar.url,
            ),
            attachments=[],
            view=enka_view,
        )

    card.seek(0)
    file_ = discord.File(card, "card.png")
    await i.edit_original_response(embed=None, attachments=[file_], view=enka_view)


class HitModeButton(ui.Button):
    def __init__(self, hit_mode: str, label: str):
        super().__init__(style=discord.ButtonStyle.blurple, label=label)
        self.hit_mode = hit_mode
        self.view: View

    async def callback(self, i: Inter) -> Any:
        self.view.calculator.hit_mode = self.hit_mode
        await damage_calc.return_current_status(i, self.view)


class ReactionModeSelect(ui.Select):
    def __init__(self, options: list[discord.SelectOption], placeholder: str):
        super().__init__(
            placeholder=placeholder, options=options, custom_id="reaction_mode"
        )
        self.view: View

    async def callback(self, i: Inter) -> Any:
        self.view.calculator.reaction_mode = (
            "" if self.values[0] == "none" else self.values[0]
        )
        await damage_calc.return_current_status(i, self.view)


class InfusionAuraSelect(ui.Select):
    def __init__(self, options: List[discord.SelectOption], placeholder: str):
        super().__init__(
            placeholder=placeholder, options=options, custom_id="infusion_aura"
        )
        self.view: View

    async def callback(self, i: Inter) -> Any:
        self.view.calculator.infusion_aura = (
            "" if self.values[0] == "none" else self.values[0]
        )
        await damage_calc.return_current_status(i, self.view)


class TeamSelectView(BaseView):
    def __init__(self, prev_view: View):
        super().__init__(timeout=config.mid_timeout)
        self.prev_view = prev_view


class GoBackToCalc(ui.Button):
    def __init__(self):
        super().__init__(emoji=asset.back_emoji, row=4)
        self.view: TeamSelectView

    async def callback(self, i: Inter):
        view = self.view.prev_view
        view.author = i.user
        await i.response.edit_message(view=view)
        await damage_calc.return_current_status(i, view, True)
        view.message = await i.original_response()


class TeamSelectButton(ui.Button):
    def __init__(self, options: List[discord.SelectOption], placeholder: str):
        super().__init__(
            style=discord.ButtonStyle.blurple,
            label=placeholder,
            custom_id="team_select",
            emoji=asset.team_emoji,
        )
        self.options = options
        self.placeholder = placeholder
        self.view: View

    async def callback(self, i: Inter):
        view = TeamSelectView(self.view)
        view.add_item(GoBackToCalc())
        divided: List[List[discord.SelectOption]] = list(
            divide_chunks(self.options, 25)
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


class TeamSelect(ui.Select):
    def __init__(self, options: list[discord.SelectOption], placeholder: str):
        super().__init__(
            placeholder=placeholder,
            options=options,
            max_values=3 if len(options) >= 3 else len(options),
        )
        self.view: TeamSelectView

    async def callback(self, i: Inter) -> Any:
        self.view.prev_view.calculator.team = self.values
        await damage_calc.return_current_status(i, self.view.prev_view)


class RunCalc(ui.Button):
    def __init__(self, label: str):
        super().__init__(
            style=discord.ButtonStyle.green,
            label=label,
            row=4,
            custom_id="calculate",
            emoji=asset.play_emoji,
        )
        self.view: View

    async def callback(self, i: Inter) -> Any:
        await damage_calc.return_damage(i, self.view)
