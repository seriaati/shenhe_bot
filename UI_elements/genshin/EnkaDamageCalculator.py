from typing import Any, List

import config
from yelan.draw import draw_character_card
from yelan.damage_calculator import DamageCalculator, return_damage
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from yelan.data.GO_modes import hit_mode_texts
from UI_base_models import BaseView
from discord import ButtonStyle, File, Interaction, Locale, SelectOption
from discord.ui import Button, Select
from utility.utils import default_embed, get_user_appearance_mode


class View(BaseView):
    def __init__(self, enka_view, locale: Locale, user_locale: str | None):
        super().__init__(timeout=config.long_timeout)
        # defining damage calculation variables
        self.enka_view = enka_view
        self.author = self.enka_view.author
        character_name = ""
        for character in enka_view.data.characters:
            if str(character.id) == enka_view.character_id:
                character_name = character.name
                break
        self.calculator = DamageCalculator(
            character_name,
            enka_view.eng_data,
            enka_view.browser,
            enka_view.character_id,
            user_locale or locale,
            "critHit",
            enka_view.author,
        )

        # producing select options
        reactionMode_options = [
            SelectOption(label=text_map.get(331, locale, user_locale), value="none")
        ]
        element = str(self.calculator.current_character.element.name)
        if element == "Cryo" or self.calculator.infusion_aura == "cryo":
            reactionMode_options.append(
                SelectOption(label=text_map.get(332, locale, user_locale), value="melt")
            )
        elif (
            element == "Pyro"
            or self.calculator.infusion_aura == "pyro"
            or element == "Anemo"
        ):
            reactionMode_options.append(
                SelectOption(
                    label=text_map.get(333, locale, user_locale), value="vaporize"
                )
            )
            reactionMode_options.append(
                SelectOption(label=text_map.get(332, locale, user_locale), value="melt")
            )
        elif element == "Hydro":
            reactionMode_options.append(
                SelectOption(
                    label=text_map.get(333, locale, user_locale), value="vaporize"
                )
            )
        elif element == "Dendro":
            reactionMode_options.append(
                SelectOption(
                    label=text_map.get(525, locale, user_locale), value="spread"
                )
            )
        elif element == "Electro" or element == "Anemo":
            reactionMode_options.append(
                SelectOption(
                    label=text_map.get(526, locale, user_locale), value="aggravate"
                )
            )

        teammate_options = []
        option: SelectOption
        for option in self.enka_view.character_options:
            if str(option.value) == str(self.enka_view.character_id):
                continue
            teammate_options.append(
                SelectOption(label=option.label, value=option.value, emoji=option.emoji)
            )
        del teammate_options[0]

        # adding items
        self.add_item(GoBack())
        for hit_mode, hash in hit_mode_texts.items():
            self.add_item(
                HitModeButton(hit_mode, text_map.get(hash, locale, user_locale))
            )
        self.add_item(
            ReactionModeSelect(
                reactionMode_options, text_map.get(337, locale, user_locale)
            )
        )
        options = [
            SelectOption(label=text_map.get(338, locale, user_locale), value="none"),
            SelectOption(
                label=text_map.get(339, locale, user_locale),
                description=text_map.get(341, locale, user_locale),
                value="pyro",
            ),
            SelectOption(
                label=text_map.get(340, locale, user_locale),
                description=text_map.get(342, locale, user_locale),
                value="cryo",
            ),
        ]
        self.add_item(
            InfusionAuraSelect(options, text_map.get(343, locale, user_locale))
        )
        if len(teammate_options) >= 1:
            self.add_item(
                TeamSelect(teammate_options, text_map.get(344, locale, user_locale))
            )


class GoBack(Button):
    def __init__(self):
        super().__init__(emoji="<:left:982588994778972171>")

    async def callback(self, i: Interaction):
        await i.response.defer()
        self.view: View
        enka_view = self.view.enka_view
        user_locale = await get_user_locale(i.user.id, enka_view.db)
        card = i.client.enka_card_cache.get(
            f"{enka_view.member.id} - {enka_view.character_id}"
        )
        if card is None:
            [character] = [
                c for c in enka_view.characters if c.id == int(enka_view.character_id)
            ]
            dark_mode = await get_user_appearance_mode(i.user.id, i.client.db)
            card = await draw_character_card(
                character, user_locale or i.locale, i.client.session, dark_mode
            )
            i.client.enka_card_cache[
                f"{enka_view.member.id} - {enka_view.character_id}"
            ] = card

        is_card = False if card is None else True
        artifact_disabled = True if is_card else False

        enka_view.children[0].disabled = artifact_disabled

        if is_card:
            embed = default_embed()
            embed.set_image(url=f"attachment://card.jpeg")
            embed.set_author(
                name=enka_view.author.display_name,
                icon_url=enka_view.author.display_avatar.url,
            )
            card.seek(0)
            file = File(card, "card.jpeg")
            await i.edit_original_response(
                embed=embed, view=enka_view, attachments=[file]
            )
        else:
            embed = enka_view.embeds[enka_view.character_id]
            embed.set_author(
                name=enka_view.author.display_name,
                icon_url=enka_view.author.display_avatar.url,
            )
            await i.edit_original_response(embed=embed, view=enka_view, attachments=[])


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
