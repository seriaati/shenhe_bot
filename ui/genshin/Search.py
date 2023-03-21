from typing import Dict, List

import discord
from discord import ui

import config
from apps.draw import main_funcs
from apps.text_map import text_map
from base_ui import BaseView
from models import CustomInteraction, DrawInput
from utility import divide_chunks


class View(BaseView):
    def __init__(
        self,
        embeds: List[discord.Embed],
        options: List[discord.SelectOption],
        placeholder: str,
        all_materials,
        locale: discord.Locale | str,
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


class QuickNavigation(ui.Select):
    def __init__(self, options: List[discord.SelectOption], placeholder: str):
        super().__init__(placeholder=placeholder, options=options)
        self.view: View

    async def callback(self, i: CustomInteraction):
        await i.response.defer()
        if self.values[0] == "1":
            fp = await main_funcs.draw_material_card(
                DrawInput(
                    loop=i.client.loop,
                    session=i.client.session,
                    locale=self.view.locale,
                    dark_mode=self.view.dark_mode,
                ),
                self.view.all_materials,
                text_map.get(320, self.view.locale),
            )
            fp.seek(0)
            file_ = discord.File(fp, filename="ascension.jpeg")
            await i.edit_original_response(
                embed=self.view.embeds[1], attachments=[file_]
            )
        else:
            await i.edit_original_response(
                embed=self.view.embeds[int(self.values[0])], attachments=[]
            )


class BookVolView(BaseView):
    def __init__(
        self,
        embeds: Dict[str, discord.Embed],
        options: List[discord.SelectOption],
        placeholder: str,
    ):
        super().__init__(timeout=config.long_timeout)
        divided_options = list(divide_chunks(options, 25))
        current = 1
        for div in divided_options:
            self.add_item(BookVolumeNav(div, f"{placeholder} ({current}~{len(div)})"))
            current += len(div)
        self.embeds = embeds


class BookVolumeNav(ui.Select):
    def __init__(self, options: List[discord.SelectOption], placeholder: str):
        super().__init__(placeholder=placeholder, options=options)
        self.view: BookVolView

    async def callback(self, i: CustomInteraction):
        await i.response.edit_message(embed=self.view.embeds[self.values[0]])
