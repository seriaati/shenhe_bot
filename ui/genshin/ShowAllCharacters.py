from typing import Any, Dict, List

import discord
import genshin
from discord import ui

import asset
import config
from apps.db import get_user_theme
from apps.draw import main_funcs
from apps.text_map import text_map
from base_ui import BaseView
from models import CustomInteraction, DrawInput
from utility import DefaultEmbed


class View(BaseView):
    def __init__(
        self,
        locale: discord.Locale | str,
        characters: List[genshin.models.Character],
        options: List[discord.SelectOption],
        member: discord.Member | discord.User,
        embeds: Dict[str, discord.Embed],
    ):
        super().__init__(timeout=config.mid_timeout)
        self.add_item(ElementSelect(options, text_map.get(142, locale)))
        self.locale = locale
        self.characters = characters
        self.member = member
        self.embeds = embeds


class ElementSelect(ui.Select):
    def __init__(self, options: List[discord.SelectOption], placeholder: str):
        super().__init__(placeholder=placeholder, options=options)
        self.view: View

    async def callback(self, i: CustomInteraction) -> Any:
        await i.response.edit_message(
            embed=DefaultEmbed().set_author(
                name=text_map.get(644, self.view.locale), icon_url=asset.loader
            ),
            attachments=[],
        )
        fp = await main_funcs.character_summary_card(
            DrawInput(
                loop=i.client.loop,
                session=i.client.session,
                locale=self.view.locale,
                dark_mode=await get_user_theme(i.user.id, i.client.pool),
            ),
            self.view.characters,
            self.values[0],
        )
        fp.seek(0)
        file_ = discord.File(fp, filename="characters.jpeg")

        await i.edit_original_response(
            embed=self.view.embeds[self.values[0]], attachments=[file_]
        )
