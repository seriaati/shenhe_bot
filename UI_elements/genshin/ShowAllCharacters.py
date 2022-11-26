from typing import Any, List

import genshin
from discord import File, Interaction, Locale, SelectOption, Member, User
from discord.ui import Select
from ambr.client import AmbrTopAPI

import asset
import config
from apps.text_map.text_map_app import text_map
from UI_base_models import BaseView
from utility.utils import default_embed, get_user_appearance_mode
from yelan.draw import draw_big_character_card


class View(BaseView):
    def __init__(
        self,
        locale: Locale | str,
        characters: List[genshin.models.Character],
        options: List[SelectOption],
        member: Member | User,
    ):
        super().__init__(timeout=config.mid_timeout)
        self.add_item(ElementSelect(options, text_map.get(142, locale)))
        self.locale = locale
        self.characters = characters
        self.member = member


class ElementSelect(Select):
    def __init__(self, options: List[SelectOption], placeholder: str):
        super().__init__(placeholder=placeholder, options=options)

    async def callback(self, i: Interaction) -> Any:
        self.view: View
        locale = self.view.locale
        await i.response.edit_message(
            embed=default_embed().set_author(
                name=text_map.get(644, self.view.locale), icon_url=asset.loader
            ),
            attachments=[],
        )
        fp = await draw_big_character_card(
            self.view.characters,
            i.client.session,  
            await get_user_appearance_mode(i.user.id, i.client.db),  
            self.view.locale,
            self.values[0],
        )
        fp.seek(0)
        file = File(fp, filename="characters.jpeg")
        ambr = AmbrTopAPI(i.client.session)  
        ambr_characters = await ambr.get_character(include_beta=False)
        if not isinstance(ambr_characters, List):
            raise TypeError("ambr_characters is not a list")
        characters = [c for c in self.view.characters if c.element == self.values[0]]
        all_characters = [c for c in ambr_characters if c.element == self.values[0]]
        embed = default_embed(
            message=f"{text_map.get(576, locale).format(current=len(characters), total=len(all_characters))}\n"
            f"{text_map.get(577, locale).format(current=len([c for c in characters if c.friendship == 10]), total=len(all_characters))}"
        )
        embed.set_author(
            name=text_map.get(196, locale),
            icon_url=self.view.member.display_avatar.url,
        )
        embed.set_image(url="attachment://characters.jpeg")
        await i.edit_original_response(embed=embed, attachments=[file])
