from typing import Any, Dict, List
from apps.genshin.custom_model import DrawInput
from apps.draw import main_funcs
from apps.text_map.text_map_app import text_map

import genshin
from discord import File, Interaction, Locale, SelectOption, Member, User, Embed
from discord.ui import Select
import asset
import config
from base_ui import BaseView
from utility.utils import DefaultEmbed, get_user_appearance_mode


class View(BaseView):
    def __init__(
        self,
        locale: Locale | str,
        characters: List[genshin.models.Character],
        options: List[SelectOption],
        member: Member | User,
        embeds: Dict[str, Embed],
    ):
        super().__init__(timeout=config.mid_timeout)
        self.add_item(ElementSelect(options, text_map.get(142, locale)))
        self.locale = locale
        self.characters = characters
        self.member = member
        self.embeds = embeds


class ElementSelect(Select):
    def __init__(self, options: List[SelectOption], placeholder: str):
        super().__init__(placeholder=placeholder, options=options)
        self.view: View

    async def callback(self, i: Interaction) -> Any:
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
                dark_mode=await get_user_appearance_mode(i.user.id, i.client.pool),
            ),
            self.view.characters,
            self.values[0],
        )
        fp.seek(0)
        file = File(fp, filename="characters.jpeg")

        await i.edit_original_response(
            embed=self.view.embeds[self.values[0]], attachments=[file]
        )
