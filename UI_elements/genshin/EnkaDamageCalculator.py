from typing import Any, List

from cachetools import TTLCache
from discord import ButtonStyle, File, Interaction, Locale, SelectOption
from discord.ui import Button, Select

import asset
import config
from apps.genshin.custom_model import EnkaView
from apps.text_map.text_map_app import text_map
from UI_base_models import BaseView
from utility.utils import default_embed, divide_chunks, get_user_appearance_mode
from yelan.damage_calculator import DamageCalculator, return_damage
from yelan.data.GO_modes import hit_mode_texts
from yelan.draw import draw_character_card


class View(BaseView):
    def __init__(self, enka_view: EnkaView, locale: Locale | str):
        super().__init__(timeout=config.long_timeout)

        # defining damage calculation variables
        self.enka_view = enka_view
        character_name = ""
        for character in enka_view.data.characters:
            if str(character.id) == enka_view.character_id:
                character_name = character.name
                break

        self.calculator = DamageCalculator(
            character_name,
            enka_view.eng_data,
            enka_view.character_id,
            locale,
            "critHit",
            enka_view.member,
        )

        # producing select options
        reactionMode_options = [
            SelectOption(label=text_map.get(331, locale), value="none")
        ]
        element = str(self.calculator.current_character.element.name)
        if element == "Cryo" or self.calculator.infusion_aura == "cryo":
            reactionMode_options.append(
                SelectOption(label=text_map.get(332, locale), value="melt")
            )
        elif (
            element == "Pyro"
            or self.calculator.infusion_aura == "pyro"
            or element == "Anemo"
        ):
            reactionMode_options.append(
                SelectOption(label=text_map.get(333, locale), value="vaporize")
            )
            reactionMode_options.append(
                SelectOption(label=text_map.get(332, locale), value="melt")
            )
        elif element == "Hydro":
            reactionMode_options.append(
                SelectOption(label=text_map.get(333, locale), value="vaporize")
            )
        elif element == "Dendro":
            reactionMode_options.append(
                SelectOption(label=text_map.get(525, locale), value="spread")
            )
        elif element == "Electro" or element == "Anemo":
            reactionMode_options.append(
                SelectOption(label=text_map.get(526, locale), value="aggravate")
            )

        teammate_options: List[SelectOption] = []
        for option in self.enka_view.character_options:
            if option.value == "0":
                continue
            if option.value == str(self.enka_view.character_id):
                continue
            teammate_options.append(
                SelectOption(label=option.label, value=option.value, emoji=option.emoji)
            )

        # adding items
        self.add_item(GoBack())
        for hit_mode, hash in hit_mode_texts.items():
            self.add_item(HitModeButton(hit_mode, text_map.get(hash, locale)))
        self.add_item(
            ReactionModeSelect(reactionMode_options, text_map.get(337, locale))
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
            divided = list(divide_chunks(teammate_options, 25))
            divided: List[List[SelectOption]]
            count = 1
            for teammate_options_chunk in divided:
                self.add_item(
                    TeamSelect(teammate_options_chunk, f"{text_map.get(344, locale)} ({count}~{count + len(teammate_options_chunk) - 1})")
                )
                count += len(teammate_options_chunk)


class GoBack(Button):
    def __init__(self):
        super().__init__(emoji="<:left:982588994778972171>")

    async def callback(self, i: Interaction):
        self.view: View
        await go_back_callback(i, self.view.enka_view)


async def go_back_callback(i: Interaction, enka_view: EnkaView):
    await i.response.edit_message(
        embed=default_embed().set_author(
            name=text_map.get(644, enka_view.locale),
            icon_url=asset.loader,
        ),
        view=None,
        attachments=[],
    )
    if enka_view.character_id == "0":
        return await i.edit_original_response(
            embed=enka_view.overview_embed, attachments=[]
        )
    card = i.client.enka_card_cache.get(
        f"{enka_view.member.id} - {enka_view.character_id}"
    )
    if card is None:
        character = [
            c for c in enka_view.data.characters if c.id == int(enka_view.character_id)
        ][0]
        dark_mode = await get_user_appearance_mode(i.user.id, i.client.db)
        card = await draw_character_card(
            character, enka_view.locale, i.client.session, dark_mode
        )
        cache: TTLCache = i.client.enka_card_cache
        cache[f"{enka_view.member.id} - {enka_view.character_id}"] = card
        if card is None:
            embed = default_embed().set_author(
                name=text_map.get(189, enka_view.locale),
                icon_url=i.user.display_avatar.url,
            )
            return await i.edit_original_response(embed=embed, attachments=[], view=enka_view)

    embed = default_embed()
    embed.set_image(url=f"attachment://card.jpeg")
    embed.set_author(
        name=enka_view.data.player.nickname,
        icon_url=enka_view.data.player.icon.url.url,
    )
    card.seek(0)
    file = File(card, "card.jpeg")
    enka_view.children[0].disabled = False
    await i.edit_original_response(embed=embed, attachments=[file], view=enka_view)


class HitModeButton(Button):
    def __init__(self, hit_mode: str, label: str):
        super().__init__(style=ButtonStyle.blurple, label=label)
        self.hit_mode = hit_mode

    async def callback(self, i: Interaction) -> Any:
        self.view: View
        self.view.calculator.hit_mode = self.hit_mode
        await return_damage(i, self.view)


class ReactionModeSelect(Select):
    def __init__(self, options: list[SelectOption], placeholder: str):
        super().__init__(placeholder=placeholder, options=options)

    async def callback(self, i: Interaction) -> Any:
        self.view: View
        self.view.calculator.reaction_mode = (
            "" if self.values[0] == "none" else self.values[0]
        )
        await return_damage(i, self.view)


class InfusionAuraSelect(Select):
    def __init__(self, options: List[SelectOption], placeholder: str):
        super().__init__(placeholder=placeholder, options=options)

    async def callback(self, i: Interaction) -> Any:
        self.view: View
        self.view.calculator.infusion_aura = (
            "" if self.values[0] == "none" else self.values[0]
        )
        await return_damage(i, self.view)


class TeamSelect(Select):
    def __init__(self, options: list[SelectOption], placeholder: str):
        super().__init__(
            placeholder=placeholder,
            options=options,
            max_values=3 if len(options) >= 3 else len(options),
        )

    async def callback(self, i: Interaction) -> Any:
        self.view: View
        self.view.calculator.team = self.values
        await return_damage(i, self.view)
