from typing import Dict, List

from discord import Embed, File, Interaction, Locale, SelectOption
from discord.ui import Select

import asset
import config
from apps.text_map.text_map_app import text_map
from data.game.elements import get_element_color
from UI_base_models import BaseView
from utility.utils import divide_chunks
from yelan.draw import draw_big_material_card


class View(BaseView):
    def __init__(
        self,
        embeds: List[Embed],
        options: List[SelectOption],
        placeholder: str,
        all_materials,
        locale: Locale | str,
        dark_mode: bool,
        character_element: str,
    ):
        super().__init__(timeout=config.long_timeout)
        self.add_item(QuickNavigation(options, placeholder))
        self.embeds = embeds
        self.all_materials = all_materials
        self.locale = locale
        self.dark_mode = dark_mode
        self.character_element = character_element


class QuickNavigation(Select):
    def __init__(self, options: List[SelectOption], placeholder: str):
        super().__init__(placeholder=placeholder, options=options)

    async def callback(self, i: Interaction):
        self.view: View
        await i.response.defer()
        if self.values[0] == "1":
            fp = await draw_big_material_card(
                self.view.all_materials,
                text_map.get(320, self.view.locale),
                asset.dark_theme_background
                if self.view.dark_mode
                else get_element_color(self.view.character_element),
                i.client.session,
                self.view.dark_mode,
                self.view.locale,
            )
            fp.seek(0)
            file = File(fp, filename="ascension.jpeg")
            await i.edit_original_response(
                embed=self.view.embeds[1], attachments=[file]
            )
        else:
            await i.edit_original_response(
                embed=self.view.embeds[int(self.values[0])], attachments=[]
            )


class BookVolView(BaseView):
    def __init__(
        self, embeds: Dict[str, Embed], options: List[SelectOption], placeholder: str
    ):
        super().__init__(timeout=config.long_timeout)
        divided_options = list(divide_chunks(options, 25))
        current = 1
        for div in divided_options:
            self.add_item(BookVolumeNav(div, f"{placeholder} ({current}~{len(div)})"))
            current += len(div)
        self.embeds = embeds


class BookVolumeNav(Select):
    def __init__(self, options: List[SelectOption], placeholder: str):
        super().__init__(placeholder=placeholder, options=options)

    async def callback(self, i: Interaction):
        self.view: BookVolView
        await i.response.edit_message(embed=self.view.embeds[self.values[0]])
