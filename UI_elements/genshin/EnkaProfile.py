from typing import Any, List

from discord import (
    ButtonStyle,
    Embed,
    Interaction,
    Locale,
    Member,
    SelectOption,
    User,
)
from discord.ui import Button, Select
from enkanetwork import EnkaNetworkResponse
from apps.genshin.custom_model import EnkaView

import asset
import config
from apps.text_map.text_map_app import text_map
from UI_base_models import BaseView
from UI_elements.genshin import EnkaDamageCalculator
from utility.utils import default_embed, divide_chunks
from yelan.damage_calculator import return_damage


class View(BaseView):
    def __init__(
        self,
        overview_embed: Embed,
        character_options: List[SelectOption],
        data: EnkaNetworkResponse,
        eng_data: EnkaNetworkResponse,
        member: User | Member,
        locale: Locale | str,
    ):
        super().__init__(timeout=config.mid_timeout)
        self.overview_embed = overview_embed
        self.character_options = character_options
        self.character_id: str = ""
        self.data = data
        self.eng_data = eng_data
        self.member = member
        self.locale = locale

        self.add_item(CalculateDamageButton(text_map.get(348, locale)))
        self.add_item(InfoButton())

        options = list(divide_chunks(self.character_options, 25))
        count = 1
        for option in options:
            character_num = len([o for o in option if o.value != 0])
            self.add_item(
                PageSelect(
                    option,
                    text_map.get(157, locale) + f" ({count}~{count+character_num-1})",
                )
            )
            count += character_num
        self.children[0].disabled = True


class InfoButton(Button):
    def __init__(self):
        super().__init__(style=ButtonStyle.secondary, emoji=asset.info_emoji)

    async def callback(self, i: Interaction):
        self.view: View
        await i.response.send_message(
            embed=default_embed(message=text_map.get(399, self.view.locale)),
            ephemeral=True,
        )


class PageSelect(Select):
    def __init__(self, character_options: list[SelectOption], plceholder: str):
        super().__init__(placeholder=plceholder, options=character_options)

    async def callback(self, i: Interaction) -> Any:
        self.view: EnkaView
        self.view.character_id = self.values[0]
        await EnkaDamageCalculator.go_back_callback(i, self.view)


class CalculateDamageButton(Button):
    def __init__(self, label: str):
        super().__init__(style=ButtonStyle.blurple, label=label, disabled=True)

    async def callback(self, i: Interaction) -> Any:
        self.view: EnkaView
        view = EnkaDamageCalculator.View(self.view, self.view.locale)
        view.author = i.user
        await return_damage(i, view)
        view.message = await i.original_response()
