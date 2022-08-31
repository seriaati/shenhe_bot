from io import BytesIO
from typing import Any, List

from apps.genshin.damage_calculator import DamageCalculator, return_damage
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from data.game.GO_modes import hit_modes
from debug import DefaultView
from discord import ButtonStyle, Embed, File, Interaction, Locale, SelectOption
from discord.ui import Button, Select
from utility.utils import default_embed, error_embed
import config


class View(DefaultView):
    def __init__(self, enka_view, locale: Locale, user_locale: str | None):
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
        elif element == "Pyro" or self.calculator.infusion_aura == "pyro" or element == 'Anemo':
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
        elif element == "Electro" or element == 'Anemo':
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
        for index in range(0, 3):
            self.add_item(
                HitModeButton(index, text_map.get(334 + index, locale, user_locale))
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

    async def interaction_check(self, i: Interaction) -> bool:
        self.view: View
        user_locale = await get_user_locale(i.user.id, self.enka_view.db)
        if i.user.id != self.enka_view.author.id:
            await i.response.send_message(
                embed=error_embed().set_author(
                    name=text_map.get(143, i.locale, user_locale),
                    icon_url=i.user.display_avatar.url,
                ),
                ephemeral=True,
            )
        return i.user.id == self.enka_view.author.id


class GoBack(Button):
    def __init__(self):
        super().__init__(emoji="<:left:982588994778972171>")

    async def callback(self, i: Interaction):
        self.view: View
        for item in self.view.enka_view.children:
            item.disabled = False
        if not isinstance(
            self.view.enka_view.embeds[self.view.enka_view.character_id], Embed
        ):
            self.view.enka_view.children[0].disabled = True
            embed = default_embed()
            embed.set_image(url=f"attachment://card.jpeg")
            fp: BytesIO = self.view.enka_view.embeds[self.view.enka_view.character_id]
            fp.seek(0)
            file = File(fp, "card.jpeg")
            await i.response.edit_message(
                embed=embed, view=self.view.enka_view, attachments=[file]
            )
        else:
            embed = self.view.enka_view.embeds[self.view.enka_view.character_id]
            await i.response.edit_message(
                embed=embed, view=self.view.enka_view, attachments=[]
            )


class HitModeButton(Button):
    def __init__(self, index: int, label: str):
        super().__init__(style=ButtonStyle.blurple, label=label)
        self.index = index

    async def callback(self, i: Interaction) -> Any:
        self.view: View
        self.view.calculator.hit_mode = (list(hit_modes.keys()))[self.index]
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
